"""
Pi Ratings match prediction engine.

For every scheduled 2026 World Cup match:
  1. Load Pi ratings (from completed match history)
  2. Load calibration state (rho, total_anchor)
  3. Compute lambdas from Pi composite ratings
  4. Build Dixon-Coles PMF grid (26x26)
  5. Derive all market probabilities
  6. Assemble a full audit trail showing every number at every step

Outputs:
  pi-ratings/predictions_YYYY-MM-DD.json   — machine-readable full output
  pi-ratings/summary_YYYY-MM-DD.html       — human-readable summary page

Usage:
    python pi-ratings/predict_matches.py
    python pi-ratings/predict_matches.py --parquet path/to/matches.parquet
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field, asdict
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Optional

_REPO_ROOT = Path(__file__).resolve().parent.parent
_PI_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_PI_DIR))

from pi_model import PiRatings, DixonColesPMF, MatchMarkets
from calibrate import CalibrationState, load as load_calibration, _FALLBACK_RHO, _FALLBACK_TOTAL


@dataclass
class PiMatchPrediction:
    match_id: int
    home_team: str
    away_team: str
    stage: str
    match_datetime: str

    # Step 1 — Pi ratings
    home_pi_home: float
    home_pi_away: float
    home_pi_composite: float
    away_pi_home: float
    away_pi_away: float
    away_pi_composite: float
    home_n_matches: int
    away_n_matches: int

    # Step 2 — Calibration
    rho: float
    total_anchor: float
    rho_source: str
    total_source: str
    calibration_n_matches: int

    # Step 3 — Lambdas
    margin: float
    lambda_home: float
    lambda_away: float

    # Step 4 — PMF summary
    expected_home_goals: float
    expected_away_goals: float
    pmf_grid_sum: float
    pmf_max_goals: int

    # Step 5 — Markets
    markets: dict = field(default_factory=dict)
    top_scorelines: list = field(default_factory=list)

    # Generated at
    generated_at: str = ""

    def to_dict(self) -> dict:
        return {
            "match_id": self.match_id,
            "home_team": self.home_team,
            "away_team": self.away_team,
            "stage": self.stage,
            "match_datetime": self.match_datetime,
            "generated_at": self.generated_at,
            "audit_trail": {
                "step1_pi_ratings": {
                    "home_pi_home":      round(self.home_pi_home, 4),
                    "home_pi_away":      round(self.home_pi_away, 4),
                    "home_pi_composite": round(self.home_pi_composite, 4),
                    "home_n_matches":    self.home_n_matches,
                    "away_pi_home":      round(self.away_pi_home, 4),
                    "away_pi_away":      round(self.away_pi_away, 4),
                    "away_pi_composite": round(self.away_pi_composite, 4),
                    "away_n_matches":    self.away_n_matches,
                    "formula": "composite = (home_rating + away_rating) / 2",
                },
                "step2_calibration": {
                    "rho":             self.rho,
                    "total_anchor":    self.total_anchor,
                    "rho_source":      self.rho_source,
                    "total_source":    self.total_source,
                    "n_matches_used":  self.calibration_n_matches,
                },
                "step3_lambdas": {
                    "margin":        round(self.margin, 4),
                    "lambda_home":   round(self.lambda_home, 4),
                    "lambda_away":   round(self.lambda_away, 4),
                    "formula": "margin = home_composite - away_composite; lambda_H = max(0.30, total_anchor/2 + margin/2); lambda_A = max(0.30, total_anchor/2 - margin/2)",
                },
                "step4_pmf": {
                    "grid_sum":     round(self.pmf_grid_sum, 6),
                    "max_goals":    self.pmf_max_goals,
                    "expected_home_goals": round(self.expected_home_goals, 4),
                    "expected_away_goals": round(self.expected_away_goals, 4),
                    "formula": "P(h,a) = tau(h,a,rho) * Poisson(h;lambda_H) * Poisson(a;lambda_A), normalised",
                },
                "step5_markets": self.markets,
            },
            "top_scorelines": self.top_scorelines,
            "markets": self.markets,
        }


def _is_tbd(name: str) -> bool:
    if not name or not isinstance(name, str):
        return True
    s = name.strip()
    if len(s) <= 4 and len(s) >= 2 and s[0] in "WL" and s[1:].isdigit():
        return True
    if len(s) == 2 and s[0].isdigit() and s[1].isalpha():
        return True
    return False


def build_ratings(matches_df) -> PiRatings:
    """Fit Pi ratings on all completed matches in chronological order."""
    completed = matches_df[
        (matches_df["status"] == "completed")
        & matches_df["home_goals"].notna()
        & matches_df["away_goals"].notna()
    ].copy()
    for col in ("match_datetime", "datetime", "date"):
        if col in completed.columns:
            completed = completed.sort_values(col)
            break
    model = PiRatings(alpha=0.15, beta=0.10)
    for _, row in completed.iterrows():
        home = str(row.get("home_team") or "")
        away = str(row.get("away_team") or "")
        hg = int(row["home_goals"])
        ag = int(row["away_goals"])
        dt = row.get("match_datetime") or row.get("datetime") or row.get("date")
        dt_str = str(dt)[:10] if dt is not None else None
        if home and away:
            model.update(home, away, hg, ag, match_date=dt_str)
    return model


def predict_match(
    match_id: int,
    home_team: str,
    away_team: str,
    stage: str,
    match_dt: str,
    ratings: PiRatings,
    cal: CalibrationState,
) -> PiMatchPrediction:
    """Run all 5 prediction steps for a single match."""
    h_rating = ratings.get_rating(home_team)
    a_rating = ratings.get_rating(away_team)

    margin = h_rating.composite - a_rating.composite
    lh = max(0.30, cal.total_anchor / 2 + margin / 2)
    la = max(0.30, cal.total_anchor / 2 - margin / 2)

    pmf = DixonColesPMF(lambda_home=lh, lambda_away=la, rho=cal.rho, max_goals=26)
    mkts = MatchMarkets(pmf)
    all_mkts = mkts.all_markets()
    top_scores = pmf.top_scorelines(n=20)

    grid_sum = sum(pmf.grid[h][a] for h in range(pmf.max_goals) for a in range(pmf.max_goals))

    return PiMatchPrediction(
        match_id=match_id,
        home_team=home_team,
        away_team=away_team,
        stage=stage,
        match_datetime=match_dt,
        home_pi_home=h_rating.home_rating,
        home_pi_away=h_rating.away_rating,
        home_pi_composite=h_rating.composite,
        away_pi_home=a_rating.home_rating,
        away_pi_away=a_rating.away_rating,
        away_pi_composite=a_rating.composite,
        home_n_matches=h_rating.n_matches,
        away_n_matches=a_rating.n_matches,
        rho=cal.rho,
        total_anchor=cal.total_anchor,
        rho_source=cal.rho_source,
        total_source=cal.total_source,
        calibration_n_matches=cal.n_matches_used,
        margin=margin,
        lambda_home=lh,
        lambda_away=la,
        expected_home_goals=pmf.expected_home_goals,
        expected_away_goals=pmf.expected_away_goals,
        pmf_grid_sum=grid_sum,
        pmf_max_goals=pmf.max_goals,
        markets=all_mkts,
        top_scorelines=top_scores,
        generated_at=datetime.now(timezone.utc).isoformat(),
    )


def run_predictions(matches_df, ratings: PiRatings, cal: CalibrationState) -> list[PiMatchPrediction]:
    """Predict all named scheduled 2026 matches."""
    sched = matches_df[
        (matches_df["season"] == 2026) &
        (matches_df["status"] == "scheduled")
    ].copy() if "season" in matches_df.columns else matches_df[
        matches_df["status"] == "scheduled"
    ].copy()

    for col in ("match_datetime", "datetime", "date"):
        if col in sched.columns:
            sched = sched.sort_values(col)
            break

    predictions = []
    for _, row in sched.iterrows():
        home = str(row.get("home_team") or "")
        away = str(row.get("away_team") or "")
        if _is_tbd(home) or _is_tbd(away):
            continue
        match_id = int(row.get("match_id", 0) or 0)
        stage = str(row.get("stage") or "")
        dt = row.get("match_datetime") or row.get("datetime") or row.get("date")
        match_dt = str(dt)[:16] if dt is not None else ""
        pred = predict_match(match_id, home, away, stage, match_dt, ratings, cal)
        predictions.append(pred)

    return predictions


def write_json(predictions: list[PiMatchPrediction], out_dir: Path) -> Path:
    today = date.today().isoformat()
    path = out_dir / f"predictions_{today}.json"
    payload = {
        "schema": "pi_ratings_predictions_v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "date": today,
        "n_matches": len(predictions),
        "matches": [p.to_dict() for p in predictions],
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path


def main():
    parser = argparse.ArgumentParser(description="Pi ratings match predictor")
    parser.add_argument("--parquet", default=str(_REPO_ROOT / "data" / "processed" / "v1" / "matches.parquet"))
    args = parser.parse_args()

    import pandas as pd
    parquet = Path(args.parquet)
    if not parquet.exists():
        raise SystemExit(f"Parquet not found: {parquet}")

    print("Loading match data...")
    df = pd.read_parquet(parquet)

    print("Building Pi ratings...")
    ratings = build_ratings(df)
    print(f"  {len(ratings.all_ratings())} teams rated")

    print("Loading calibration state...")
    cal = load_calibration()
    if cal is None:
        print("  No calibration_state.json found — using fallbacks")
        from calibrate import CalibrationState
        cal = CalibrationState(
            rho=_FALLBACK_RHO, total_anchor=_FALLBACK_TOTAL, n_matches_used=0,
            calibrated_at="fallback", log_likelihood=0.0, rmse_total_goals=0.0,
            rho_source="fallback", total_source="fallback",
        )
    print(f"  rho={cal.rho} ({cal.rho_source}), total_anchor={cal.total_anchor} ({cal.total_source})")

    print("Predicting scheduled matches...")
    predictions = run_predictions(df, ratings, cal)
    print(f"  {len(predictions)} match predictions generated")

    json_path = write_json(predictions, _PI_DIR)
    print(f"  JSON written: {json_path}")

    # Import and call summary writer
    from summary import write_summary
    html_path = write_summary(predictions, cal, _PI_DIR)
    print(f"  HTML written: {html_path}")

    # Print preview
    print("\n--- Prediction preview (first 5 matches) ---")
    for p in predictions[:5]:
        ml = p.markets
        print(f"  {p.match_datetime[:10]} | {p.home_team:20s} vs {p.away_team:20s} | "
              f"1X2: {ml.get('home_win',0):.4f}/{ml.get('draw',0):.4f}/{ml.get('away_win',0):.4f} | "
              f"λH={p.lambda_home:.3f} λA={p.lambda_away:.3f}")


if __name__ == "__main__":
    main()
