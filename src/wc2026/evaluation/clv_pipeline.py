"""
CLV Pipeline orchestrator.

Reads:
  - immutable odds snapshots (OddsSnapshotStore)
  - live predictions with their timestamps
  - closing odds snapshots

Produces:
  - reports/clv/closing_line_forecast.csv
  - reports/clv/clv_by_market.csv
  - reports/clv/clv_by_horizon.csv
  - reports/live_shadow/production_diff.csv

Only runs when WC_USE_NEW_CLV_REPORTING=True (default True in config).
Does NOT alter any public WizardOfOdds output.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
import logging
import json
import pandas as pd
import numpy as np

log = logging.getLogger(__name__)

CLV_REPORT_DIR = Path("reports/clv")
SHADOW_REPORT_DIR = Path("reports/live_shadow")
TEAM_STRENGTH_REPORT_DIR = Path("reports/team_strength")

for _d in [CLV_REPORT_DIR, SHADOW_REPORT_DIR, TEAM_STRENGTH_REPORT_DIR]:
    _d.mkdir(parents=True, exist_ok=True)


@dataclass
class CLVRecord:
    match_id: int
    home_team: str
    away_team: str
    market_type: str
    market_key: str
    bet_side: str
    bet_decimal_odds: float
    closing_fair_probability: float
    current_fair_probability: float
    fair_clv: float
    same_line_clv: float
    horizon_hours: Optional[float]
    vendor: Optional[str]
    prediction_timestamp: str
    closing_timestamp: Optional[str]
    stage: Optional[str]
    notes: str = ""


def compute_fair_clv(bet_decimal_odds: float, closing_fair_prob: float) -> float:
    """
    Fair CLV for no-push markets:
      fair_clv = bet_decimal_odds * closing_fair_probability - 1
    """
    return bet_decimal_odds * closing_fair_prob - 1.0


def compute_quarter_line_clv(
    bet_decimal_odds: float,
    closing_win_prob: float,
    closing_push_prob: float,
    closing_lose_prob: float,
) -> float:
    """
    Fair CLV for quarter-line (half win / half push) markets:
      fair_clv = (0.5*win + 0.5*push) * (bet_decimal_odds - 1) - 0.5*lose

    Approximation used when exact quarter-line settlement probs are available.
    """
    return (
        (0.5 * closing_win_prob + 0.5 * closing_push_prob) * (bet_decimal_odds - 1)
        - 0.5 * closing_lose_prob
    )


def _clv_records_to_df(records: list[CLVRecord]) -> pd.DataFrame:
    if not records:
        return pd.DataFrame()
    return pd.DataFrame([vars(r) for r in records])


def write_clv_by_market(records: list[CLVRecord]) -> Path:
    """Slice CLV by market type and write CSV."""
    df = _clv_records_to_df(records)
    if df.empty:
        out = CLV_REPORT_DIR / "clv_by_market.csv"
        pd.DataFrame().to_csv(out, index=False)
        return out

    agg = df.groupby("market_type").agg(
        n_bets=("fair_clv", "count"),
        mean_fair_clv=("fair_clv", "mean"),
        median_fair_clv=("fair_clv", "median"),
        std_fair_clv=("fair_clv", "std"),
        positive_clv_pct=("fair_clv", lambda x: (x > 0).mean()),
    ).reset_index()
    out = CLV_REPORT_DIR / "clv_by_market.csv"
    agg.to_csv(out, index=False)
    return out


def write_clv_by_horizon(records: list[CLVRecord]) -> Path:
    """Slice CLV by prediction horizon and write CSV."""
    df = _clv_records_to_df(records)
    if df.empty or "horizon_hours" not in df.columns:
        out = CLV_REPORT_DIR / "clv_by_horizon.csv"
        pd.DataFrame().to_csv(out, index=False)
        return out

    df = df.dropna(subset=["horizon_hours"])
    df["horizon_bin"] = pd.cut(
        df["horizon_hours"],
        bins=[0, 1, 6, 24, 72, 168, float("inf")],
        labels=["<1h", "1-6h", "6-24h", "24-72h", "72h-1w", ">1w"],
        right=False,
    )
    agg = df.groupby("horizon_bin", observed=True).agg(
        n_bets=("fair_clv", "count"),
        mean_fair_clv=("fair_clv", "mean"),
        std_fair_clv=("fair_clv", "std"),
        positive_clv_pct=("fair_clv", lambda x: (x > 0).mean()),
    ).reset_index()
    out = CLV_REPORT_DIR / "clv_by_horizon.csv"
    agg.to_csv(out, index=False)
    return out


def write_closing_line_forecast_csv(predictions: list[dict]) -> Path:
    """Write closing-line forecast results to CSV."""
    df = pd.DataFrame(predictions) if predictions else pd.DataFrame()
    out = CLV_REPORT_DIR / "closing_line_forecast.csv"
    df.to_csv(out, index=False)
    return out


def write_production_diff_csv(diff_rows: list[dict]) -> Path:
    """Write live model vs shadow model comparison."""
    df = pd.DataFrame(diff_rows) if diff_rows else pd.DataFrame()
    out = SHADOW_REPORT_DIR / "production_diff.csv"
    df.to_csv(out, index=False)
    return out


def run_clv_pipeline(
    bet_records: list[dict],
    closing_snapshots: pd.DataFrame,
    prediction_timestamp: datetime,
    match_metadata: dict[int, dict] | None = None,
) -> dict:
    """
    Main CLV pipeline entry point.

    bet_records: list of dicts with keys:
      match_id, market_type, market_key, bet_side,
      bet_decimal_odds, current_fair_probability,
      prediction_timestamp, vendor, stage

    closing_snapshots: DataFrame from OddsSnapshotStore with closing odds.

    Returns dict with paths to written reports.
    """
    records = []

    for bet in bet_records:
        mid = int(bet.get("match_id", 0))

        # Find closing odds for this match/market
        if closing_snapshots.empty:
            continue

        match_close = (
            closing_snapshots[closing_snapshots["match_id"] == mid]
            if "match_id" in closing_snapshots.columns
            else pd.DataFrame()
        )
        if match_close.empty:
            continue

        market_type = str(bet.get("market_type", ""))
        bet_side = str(bet.get("bet_side", ""))

        close_fair_prob = _get_closing_fair_prob(match_close, market_type, bet_side)
        if close_fair_prob is None or close_fair_prob <= 0:
            continue

        bet_odds = float(bet.get("bet_decimal_odds", 2.0))
        fair_clv = compute_fair_clv(bet_odds, close_fair_prob)

        current_fair = float(bet.get("current_fair_probability", 0.5))
        same_line_clv = bet_odds * current_fair - 1.0

        pred_ts = str(bet.get("prediction_timestamp", prediction_timestamp.isoformat()))
        close_ts_vals = match_close.get("observed_at", pd.Series(dtype=object))
        close_ts = str(close_ts_vals.max()) if len(close_ts_vals) > 0 else None

        # Compute horizon
        horizon_hours = None
        if close_ts:
            try:
                pts = pd.Timestamp(pred_ts, tz="UTC")
                cts = pd.Timestamp(close_ts, tz="UTC")
                horizon_hours = float((cts - pts).total_seconds() / 3600)
            except Exception:
                pass

        metadata = (match_metadata or {}).get(mid, {})

        records.append(CLVRecord(
            match_id=mid,
            home_team=str(metadata.get("home_team", "")),
            away_team=str(metadata.get("away_team", "")),
            market_type=market_type,
            market_key=str(bet.get("market_key", "")),
            bet_side=bet_side,
            bet_decimal_odds=bet_odds,
            closing_fair_probability=close_fair_prob,
            current_fair_probability=current_fair,
            fair_clv=fair_clv,
            same_line_clv=same_line_clv,
            horizon_hours=horizon_hours,
            vendor=bet.get("vendor"),
            prediction_timestamp=pred_ts,
            closing_timestamp=close_ts,
            stage=metadata.get("stage"),
        ))

    out_paths = {}
    out_paths["clv_by_market"] = str(write_clv_by_market(records))
    out_paths["clv_by_horizon"] = str(write_clv_by_horizon(records))

    return {
        "n_records": len(records),
        "report_paths": out_paths,
        "records": [vars(r) for r in records],
    }


def _get_closing_fair_prob(
    match_close: pd.DataFrame,
    market_type: str,
    side: str,
) -> Optional[float]:
    """Extract closing fair probability for a specific market/side."""
    if market_type in ("moneyline", "1x2", "1X2"):
        home_odds_col = "moneyline_home_odds"
        draw_odds_col = "moneyline_draw_odds"
        away_odds_col = "moneyline_away_odds"

        latest = match_close.sort_values("observed_at").iloc[-1] if len(match_close) > 0 else None
        if latest is None:
            return None

        try:
            home_o = float(latest.get(home_odds_col, 0) or 0)
            draw_o = float(latest.get(draw_odds_col, 0) or 0)
            away_o = float(latest.get(away_odds_col, 0) or 0)
            if home_o <= 0 or draw_o <= 0 or away_o <= 0:
                return None
            raws = [1 / home_o, 1 / draw_o, 1 / away_o]
            total = sum(raws)
            probs = [r / total for r in raws]

            side_lower = side.lower()
            if "home" in side_lower:
                return probs[0]
            elif "draw" in side_lower:
                return probs[1]
            elif "away" in side_lower:
                return probs[2]
        except Exception:
            pass

    return None
