"""Build closing-line dataset for closing-line forecaster training."""
from __future__ import annotations

import logging
from pathlib import Path

import numpy as np
import pandas as pd

log = logging.getLogger(__name__)

_DEFAULT_HORIZONS_SECONDS = [86400, 21600, 3600, 600]  # 24h, 6h, 1h, 10min
_MIN_ROWS_REQUIRED = 10


def build_closing_dataset(
    seasons: list[int] | None = None,
    horizons_seconds: list[int] | None = None,
    published_dir: str | Path | None = None,
    store=None,  # OddsSnapshotStore instance
) -> pd.DataFrame:
    """
    Build closing-line prediction dataset.

    Returns empty DataFrame (with correct columns) when no historical snapshots exist.
    Never uses latest odds as proxy for historical snapshots.
    """
    if seasons is None:
        seasons = [2026]
    if horizons_seconds is None:
        horizons_seconds = _DEFAULT_HORIZONS_SECONDS

    from wc2026.data.odds_snapshot_store import OddsSnapshotStore
    if store is None:
        store = OddsSnapshotStore()

    rows = []

    # Load completed matches from published JSON
    matches = _load_completed_matches(published_dir, seasons)
    if matches.empty:
        log.info("No completed matches found for seasons %s", seasons)
        return _empty_dataset()

    for _, match_row in matches.iterrows():
        match_id = int(match_row["match_id"])
        kickoff_at = pd.to_datetime(match_row.get("kickoff_at") or match_row.get("match_datetime_utc"))
        if pd.isna(kickoff_at):
            continue

        kickoff_at = kickoff_at.to_pydatetime()
        if kickoff_at.tzinfo is None:
            import datetime
            kickoff_at = kickoff_at.replace(tzinfo=datetime.timezone.utc)

        # Load closing snapshot
        closing_snap = store.closing_snapshot(match_id, close_before_minutes=3)
        if closing_snap.empty:
            log.info("INSUFFICIENT_HISTORY: No closing snapshot for match %d", match_id)
            continue

        from wc2026.markets.current_market_pmf import build_market_pmf_simple
        close_pmf_obj = build_market_pmf_simple(closing_snap)
        if close_pmf_obj is None:
            continue

        for horizon_s in horizons_seconds:
            import datetime as dt
            pred_ts = kickoff_at - dt.timedelta(seconds=horizon_s)
            snap = store.asof_snapshot(match_id, prediction_timestamp=pred_ts)

            if len(snap) < _MIN_ROWS_REQUIRED:
                log.debug("INSUFFICIENT_HISTORY: match %d at horizon %ds: only %d rows", match_id, horizon_s, len(snap))
                continue

            curr_pmf_obj = build_market_pmf_simple(snap)
            if curr_pmf_obj is None:
                continue

            # Compute target moves
            try:
                log_h_move = float(np.log(close_pmf_obj.home_lambda / curr_pmf_obj.home_lambda))
                log_a_move = float(np.log(close_pmf_obj.away_lambda / curr_pmf_obj.away_lambda))
                rho_move = close_pmf_obj.rho - curr_pmf_obj.rho
                total_move = (close_pmf_obj.home_lambda + close_pmf_obj.away_lambda) - (curr_pmf_obj.home_lambda + curr_pmf_obj.away_lambda)
                gd_move = (close_pmf_obj.home_lambda - close_pmf_obj.away_lambda) - (curr_pmf_obj.home_lambda - curr_pmf_obj.away_lambda)
            except (ZeroDivisionError, ValueError):
                continue

            # Structural features from published JSON
            struct_lh = float(match_row.get("structural_home_lambda") or curr_pmf_obj.home_lambda)
            struct_la = float(match_row.get("structural_away_lambda") or curr_pmf_obj.away_lambda)

            row = {
                "match_id": match_id,
                "prediction_timestamp": pred_ts.isoformat(),
                "horizon_seconds": horizon_s,
                "current_market_home_lambda": curr_pmf_obj.home_lambda,
                "current_market_away_lambda": curr_pmf_obj.away_lambda,
                "current_market_rho": curr_pmf_obj.rho,
                "current_market_total": curr_pmf_obj.home_lambda + curr_pmf_obj.away_lambda,
                "current_market_goal_diff": curr_pmf_obj.home_lambda - curr_pmf_obj.away_lambda,
                "close_market_home_lambda": close_pmf_obj.home_lambda,
                "close_market_away_lambda": close_pmf_obj.away_lambda,
                "close_market_rho": close_pmf_obj.rho,
                "close_market_total": close_pmf_obj.home_lambda + close_pmf_obj.away_lambda,
                "close_market_goal_diff": close_pmf_obj.home_lambda - close_pmf_obj.away_lambda,
                "target_log_home_lambda_move": log_h_move,
                "target_log_away_lambda_move": log_a_move,
                "target_rho_move": rho_move,
                "target_total_move": total_move,
                "target_goal_diff_move": gd_move,
                "structural_log_home_lambda_minus_market": float(np.log(max(struct_lh, 0.01) / max(curr_pmf_obj.home_lambda, 0.01))),
                "structural_log_away_lambda_minus_market": float(np.log(max(struct_la, 0.01) / max(curr_pmf_obj.away_lambda, 0.01))),
                "structural_total_minus_market": (struct_lh + struct_la) - (curr_pmf_obj.home_lambda + curr_pmf_obj.away_lambda),
                "structural_goal_diff_minus_market": (struct_lh - struct_la) - (curr_pmf_obj.home_lambda - curr_pmf_obj.away_lambda),
                "vendor_count": curr_pmf_obj.vendor_count,
                "market_quality": curr_pmf_obj.market_quality,
                "stage": str(match_row.get("stage", "")),
                "group": str(match_row.get("group", "")),
                "host_team_indicator": int(match_row.get("is_host", 0)),
                "neutral_venue": 1,
                "lineup_known": 0,
                "injury_snapshot_available": 0,
                "player_props_available": 0,
            }
            rows.append(row)

    if not rows:
        return _empty_dataset()
    return pd.DataFrame(rows)


def _load_completed_matches(published_dir, seasons) -> pd.DataFrame:
    import json
    from pathlib import Path as P
    if published_dir is None:
        published_dir = P("data/published")
    published_dir = P(published_dir)
    if not published_dir.exists():
        return pd.DataFrame()

    rows = []
    for f in sorted(published_dir.glob("2026-*.json")):
        try:
            with open(f) as fh:
                doc = json.load(fh)
            for m in doc.get("matches", []):
                if m.get("status") == "completed":
                    rows.append({
                        "match_id": m["match_id"],
                        "match_datetime_utc": m.get("match_datetime_utc"),
                        "stage": m.get("stage", ""),
                        "group": m.get("group", ""),
                        "structural_home_lambda": m.get("home_prior", {}).get("final_attack_lambda"),
                        "structural_away_lambda": m.get("away_prior", {}).get("final_attack_lambda"),
                    })
        except Exception:
            pass
    return pd.DataFrame(rows)


def _empty_dataset() -> pd.DataFrame:
    cols = [
        "match_id", "prediction_timestamp", "horizon_seconds",
        "current_market_home_lambda", "current_market_away_lambda", "current_market_rho",
        "current_market_total", "current_market_goal_diff",
        "close_market_home_lambda", "close_market_away_lambda", "close_market_rho",
        "close_market_total", "close_market_goal_diff",
        "target_log_home_lambda_move", "target_log_away_lambda_move",
        "target_rho_move", "target_total_move", "target_goal_diff_move",
        "structural_log_home_lambda_minus_market", "structural_log_away_lambda_minus_market",
        "structural_total_minus_market", "structural_goal_diff_minus_market",
        "vendor_count", "market_quality", "stage", "group",
        "host_team_indicator", "neutral_venue", "lineup_known",
        "injury_snapshot_available", "player_props_available",
    ]
    return pd.DataFrame(columns=cols)
