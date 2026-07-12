"""Fair CLV reporting with correct quarter-line settlement and cluster bootstrap."""
from __future__ import annotations

import logging
from dataclasses import dataclass

import numpy as np
import pandas as pd

log = logging.getLogger(__name__)

_MIN_VALID_RECORDS = 20
_EXCLUDED_SOURCES = {None, "backfill_invalid", ""}
_BOOTSTRAP_REPS = 1000


@dataclass
class CLVReportRow:
    group_key: tuple
    n_bets: int
    mean_clv: float
    median_clv: float
    std_error: float
    ci_lower: float
    ci_upper: float
    n_excluded: int
    excluded_reasons: dict


def _fair_clv_no_push(bet_decimal_odds: float, closing_fair_prob: float) -> float:
    """Fair CLV for no-push markets: EV - 1."""
    return bet_decimal_odds * closing_fair_prob - 1.0


def _fair_clv_quarter_line(
    bet_decimal_odds: float,
    close_win_weight: float,
    close_lose_weight: float,
) -> float:
    """Fair CLV for push/quarter-line markets (AH, totals)."""
    return close_win_weight * (bet_decimal_odds - 1.0) - close_lose_weight


def _cluster_bootstrap_ci(values: np.ndarray, match_ids: np.ndarray, n_reps: int = _BOOTSTRAP_REPS, alpha: float = 0.05) -> tuple[float, float]:
    """Bootstrap confidence interval clustered by match_id."""
    unique_matches = np.unique(match_ids)
    n_clusters = len(unique_matches)
    if n_clusters < 2:
        std = float(np.std(values)) / max(len(values) ** 0.5, 1)
        mean = float(np.mean(values))
        return mean - 1.96 * std, mean + 1.96 * std

    means = []
    rng = np.random.default_rng(42)
    for _ in range(n_reps):
        sampled = rng.choice(unique_matches, size=n_clusters, replace=True)
        mask = np.isin(match_ids, sampled)
        if mask.sum() > 0:
            means.append(float(np.mean(values[mask])))

    means = np.array(means)
    return float(np.percentile(means, alpha * 50)), float(np.percentile(means, 100 - alpha * 50))


def compute_clv_report(
    clv_records: pd.DataFrame,
    closing_snapshots: pd.DataFrame | None = None,
    canonical_markets: dict | None = None,
    group_by: list[str] | None = None,
) -> pd.DataFrame:
    """
    Compute fair CLV report.

    Args:
        clv_records: DataFrame from CLVStore (one row per market per match)
        closing_snapshots: Optional DataFrame from OddsSnapshotStore.closing_snapshot()
        canonical_markets: Optional pre-computed canonical grid outputs per match
        group_by: Columns to group by (default: ["market"])

    Returns:
        DataFrame with CLV statistics per group
    """
    if clv_records is None or clv_records.empty:
        log.warning("No CLV records provided")
        return pd.DataFrame()

    if group_by is None:
        group_by = ["market"]

    # Validate and filter records
    valid_mask = pd.Series(True, index=clv_records.index)
    excluded_counts = {}

    # Exclude invalid closing sources
    if "closing_source" in clv_records.columns:
        invalid_source = clv_records["closing_source"].isin(_EXCLUDED_SOURCES) | clv_records["closing_source"].isna()
        excluded_counts["invalid_closing_source"] = int(invalid_source.sum())
        valid_mask &= ~invalid_source

    # Exclude where observed_at > kickoff_at (post-match odds)
    if "closing_timestamp" in clv_records.columns and "match_datetime_utc" in clv_records.columns:
        try:
            ct = pd.to_datetime(clv_records["closing_timestamp"], utc=True)
            ko = pd.to_datetime(clv_records["match_datetime_utc"], utc=True)
            post_match = ct > ko
            excluded_counts["post_match_closing"] = int(post_match.sum())
            valid_mask &= ~post_match
        except Exception:
            pass

    valid_df = clv_records[valid_mask].copy()
    n_excluded = int((~valid_mask).sum())
    n_valid = int(valid_mask.sum())

    log.info("CLV report: %d valid records, %d excluded (%s)", n_valid, n_excluded, excluded_counts)

    if n_valid < _MIN_VALID_RECORDS:
        log.warning("Only %d valid records (min %d required). Report will be incomplete.", n_valid, _MIN_VALID_RECORDS)

    # Compute fair CLV per record
    if "clv_raw" in valid_df.columns:
        valid_df["fair_clv"] = valid_df["clv_raw"].astype(float)
    elif "closing_prob" in valid_df.columns and "model_fair_odds" in valid_df.columns:
        valid_df["fair_clv"] = valid_df.apply(
            lambda r: _fair_clv_no_push(
                float(r.get("model_fair_odds", 2.0)),
                float(r.get("closing_prob", 0.5))
            ), axis=1
        )
    else:
        log.warning("Cannot compute fair_clv: missing clv_raw or closing_prob/model_fair_odds")
        valid_df["fair_clv"] = 0.0

    # Add dimension bins
    if "market_quality" in valid_df.columns:
        valid_df["market_quality_bin"] = pd.cut(
            valid_df["market_quality"].fillna(0),
            bins=[0, 0.4, 0.7, 1.01],
            labels=["low", "medium", "high"],
        )

    # Group and compute statistics
    available_group_cols = [c for c in group_by if c in valid_df.columns]
    if not available_group_cols:
        available_group_cols = ["market"] if "market" in valid_df.columns else []
    if not available_group_cols:
        valid_df["_all"] = "all"
        available_group_cols = ["_all"]

    report_rows = []
    for group_key, group_df in valid_df.groupby(available_group_cols):
        if not isinstance(group_key, tuple):
            group_key = (group_key,)
        values = group_df["fair_clv"].dropna().values
        if len(values) < 1:
            continue
        match_ids = group_df["match_id"].values if "match_id" in group_df.columns else np.zeros(len(values))
        ci_lo, ci_hi = _cluster_bootstrap_ci(values, match_ids)
        n_clusters = len(np.unique(match_ids))
        se = (ci_hi - ci_lo) / (2 * 1.96) if ci_hi > ci_lo else 0.0
        report_rows.append({
            **dict(zip(available_group_cols, group_key)),
            "n_bets": len(values),
            "n_matches": n_clusters,
            "mean_clv": float(np.mean(values)),
            "median_clv": float(np.median(values)),
            "std_error": se,
            "ci_lower": ci_lo,
            "ci_upper": ci_hi,
            "n_excluded": n_excluded,
            "excluded_reasons": str(excluded_counts),
        })

    return pd.DataFrame(report_rows)
