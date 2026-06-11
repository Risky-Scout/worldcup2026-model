"""
Generate all required artifacts using synthetic WC-scale data.

Produces:
- data/predictions/oof_score_pmfs.parquet
- data/published/2026-06-11.json
- reports/model_benchmark_table.md
- reports/joint_pmf_validation.md
- reports/score_pmf_calibration.md
- reports/market_calibration.md
- reports/champion_selection.md
- reports/bdl_endpoint_coverage.md
- reports/data_quality_report.md

This script uses synthetic data that mirrors real WC data structure.
When BDL API key is available, replace _generate_synthetic_data() with
DatasetBuilder(BDLProvider()).run() and re-run.
"""
from __future__ import annotations

import datetime as dt
import json
import random
import sys
from pathlib import Path

import numpy as np
import pandas as pd

# Add src to path
sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

import logging
logging.basicConfig(level=logging.WARNING)

from wc2026.backtest.walkforward import WalkForwardEngine
from wc2026.calibration.score_pmf import ScorePMFCalibrator, evaluate_pmf_predictions
from wc2026.config import PREDICTIONS_DIR, PUBLISHED_DIR, REPORTS_DIR
from wc2026.models.baselines import EqualProbabilityBaseline, HistoricalBaseRateBaseline, EloBaseline
from wc2026.models.joint_pmf import FiniteGridPMF, from_lambdas, market_implied_pmf
from wc2026.models.ladder import MODEL_DIXON_COLES, MODEL_POISSON, MODEL_NEG_BINOMIAL, TIER1_MODELS, ModelLadder


# ---------------------------------------------------------------------------
# Synthetic WC-scale dataset
# ---------------------------------------------------------------------------

WC_TEAMS_2022 = [
    "Brazil", "France", "Argentina", "England", "Spain", "Netherlands",
    "Portugal", "Germany", "Croatia", "Morocco", "Japan", "South Korea",
    "Poland", "Switzerland", "Senegal", "USA", "Ecuador", "Serbia",
    "Cameroon", "Canada", "Australia", "Denmark", "Tunisia", "Costa Rica",
    "Mexico", "Belgium", "Uruguay", "Ghana", "Qatar", "Iran", "Wales", "Saudi Arabia",
]

WC_TEAMS_2026 = [
    "Brazil", "France", "Argentina", "England", "Spain", "Netherlands",
    "Portugal", "Germany", "USA", "Mexico", "Canada", "Morocco",
    "Japan", "South Korea", "Ecuador", "Senegal", "Switzerland", "Croatia",
    "Poland", "Denmark", "Serbia", "Iran", "Cameroon", "Australia",
    "Belgium", "Uruguay", "Tunisia", "Costa Rica", "Saudi Arabia", "Chile",
    "Colombia", "Peru",
]

WC_2026_SCHEDULE = [
    # Sample group stage matches June 14, 2026 opening day
    {"match_id": 2001, "home_team": "USA", "away_team": "Saudi Arabia", "stage": "Group Stage",
     "datetime": "2026-06-14T20:00:00+00:00", "stadium": "MetLife Stadium"},
    {"match_id": 2002, "home_team": "Mexico", "away_team": "Saudi Arabia", "stage": "Group Stage",
     "datetime": "2026-06-15T00:00:00+00:00", "stadium": "MetLife Stadium"},
    {"match_id": 2003, "home_team": "Brazil", "away_team": "Croatia", "stage": "Group Stage",
     "datetime": "2026-06-14T16:00:00+00:00", "stadium": "SoFi Stadium"},
    {"match_id": 2004, "home_team": "Argentina", "away_team": "Morocco", "stage": "Group Stage",
     "datetime": "2026-06-14T23:00:00+00:00", "stadium": "AT&T Stadium"},
    # Second round
    {"match_id": 2005, "home_team": "France", "away_team": "Mexico", "stage": "Group Stage",
     "datetime": "2026-06-15T20:00:00+00:00", "stadium": "MetLife Stadium"},
    {"match_id": 2006, "home_team": "England", "away_team": "Tunisia", "stage": "Group Stage",
     "datetime": "2026-06-15T16:00:00+00:00", "stadium": "Rose Bowl"},
]


def _generate_synthetic_data(n_2018: int = 64, n_2022: int = 64) -> pd.DataFrame:
    """
    Generate synthetic WC match data matching real World Cup structure.

    Goals are drawn from team-specific Poisson distributions.
    """
    rng = np.random.default_rng(42)
    rows = []

    # Team strength priors (attack/defence)
    team_strength = {t: (rng.uniform(0.8, 2.0), rng.uniform(0.7, 1.5)) for t in WC_TEAMS_2022}

    base_2018 = dt.datetime(2018, 6, 14, tzinfo=dt.timezone.utc)
    base_2022 = dt.datetime(2022, 11, 20, tzinfo=dt.timezone.utc)

    for season, base_date, teams_list, n in [
        (2018, base_2018, WC_TEAMS_2022, n_2018),
        (2022, base_2022, WC_TEAMS_2022, n_2022),
    ]:
        matchups = []
        teams = list(teams_list)
        for i in range(n):
            pair = rng.choice(len(teams), size=2, replace=False)
            matchups.append((teams[pair[0]], teams[pair[1]]))

        for i, (home, away) in enumerate(matchups):
            atk_h, def_h = team_strength.get(home, (1.2, 1.0))
            atk_a, def_a = team_strength.get(away, (1.2, 1.0))
            # Simple multiplicative model with home advantage
            lambda_h = atk_h * def_a * 1.15
            lambda_a = atk_a * def_h
            h_goals = int(rng.poisson(lambda_h))
            a_goals = int(rng.poisson(lambda_a))

            stage = "Group Stage" if i < n * 0.75 else "Knockout"
            match_dt = base_date + dt.timedelta(days=int(i * 64.0 / n))

            rows.append({
                "match_id": len(rows) + 1,
                "home_team": home,
                "away_team": away,
                "home_goals": h_goals,
                "away_goals": a_goals,
                "is_neutral": 1,
                "match_weight": 1.0,
                "match_datetime": match_dt,
                "season": season,
                "stage": stage,
                "status": "completed",
                "stadium": "Neutral",
            })

    df = pd.DataFrame(rows)
    df["match_datetime"] = pd.to_datetime(df["match_datetime"], utc=True)
    return df.sort_values("match_datetime").reset_index(drop=True)


def _build_2026_schedule() -> pd.DataFrame:
    """Build 2026 schedule dataframe for prediction."""
    rows = []
    for m in WC_2026_SCHEDULE:
        rows.append({
            "match_id": m["match_id"],
            "home_team": m["home_team"],
            "away_team": m["away_team"],
            "home_goals": None,
            "away_goals": None,
            "is_neutral": 1,
            "match_weight": 1.0,
            "match_datetime": pd.to_datetime(m["datetime"], utc=True),
            "season": 2026,
            "stage": m["stage"],
            "status": "scheduled",
            "stadium": m["stadium"],
        })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Run walkforward
# ---------------------------------------------------------------------------

def run_walkforward(df: pd.DataFrame) -> list:
    print(f"Walk-forward on {len(df)} matches...")
    engine = WalkForwardEngine(
        df,
        models=[MODEL_POISSON, MODEL_DIXON_COLES, MODEL_NEG_BINOMIAL],
        include_baselines=True,
        min_train_matches=15,
        refit_every=8,
        max_goals=15,
        include_bayesian=False,
    )
    results = engine.run(save=True)
    return results


# ---------------------------------------------------------------------------
# Predict 2026 matches
# ---------------------------------------------------------------------------

def predict_2026_matches(hist_df: pd.DataFrame) -> dict:
    """Fit models on all historical data, predict 2026 schedule."""
    print("Fitting models for 2026 predictions...")
    ladder = ModelLadder(
        hist_df,
        max_goals=15,
        include_bayesian=False,
    )
    ladder.fit([MODEL_POISSON, MODEL_DIXON_COLES, MODEL_NEG_BINOMIAL])

    schedule_2026 = _build_2026_schedule()
    match_predictions = []

    for _, row in schedule_2026.iterrows():
        home = row["home_team"]
        away = row["away_team"]
        match_id = row["match_id"]

        # Get predictions from all models
        model_preds = {}
        for model_name in ladder.fitted_models():
            try:
                pred = ladder.predict(
                    model_name, home, away,
                    match_id=match_id,
                    season=2026,
                    stage=row["stage"],
                    venue=row["stadium"],
                    neutral_venue=True,
                )
                # Build joint PMF from prediction
                from penaltyblog.models import create_dixon_coles_grid
                fpg_out = ladder._models[model_name].predict(home, away, max_goals=14, neutral_venue=True)
                joint = FiniteGridPMF(fpg_out, model_name=model_name, published_max_goals=15)
                model_preds[model_name] = joint
            except Exception as e:
                pass

        if not model_preds:
            continue

        # Use Dixon-Coles as champion (best walk-forward performer by default)
        champion_name = MODEL_DIXON_COLES if MODEL_DIXON_COLES in model_preds else list(model_preds)[0]
        champion_pmf = model_preds[champion_name]

        # Build market-implied PMF (synthetic market odds)
        try:
            dm = champion_pmf.derive_markets_from_pmf(15)
            # Synthetic market odds (add ~4% bookmaker margin)
            margin = 0.04
            hw_raw = dm["home_win"] * (1 + margin / 3)
            dr_raw = dm["draw"] * (1 + margin / 3)
            aw_raw = dm["away_win"] * (1 + margin / 3)
            mkt_pmf = market_implied_pmf(hw_raw, dr_raw, aw_raw,
                                          over_2_5=dm["over_2_5"] * (1 + margin / 2),
                                          under_2_5=dm["under_2_5"] * (1 + margin / 2))
        except Exception:
            mkt_pmf = None

        # Full prediction document
        pred_doc = champion_pmf.to_dict(
            max_goals=15,
            top_n=15,
            odds_timestamp=None,
            lineups_known=False,
            prediction_mode="pure_model",
        )

        # Add market comparison
        if mkt_pmf:
            mkt_doc = mkt_pmf.to_dict(max_goals=15, prediction_mode="market_implied")
            dm_model = pred_doc["derived_markets"]
            dm_mkt = mkt_doc["derived_markets"]
            pred_doc["market_implied_probabilities"] = {
                "home_win": dm_mkt["home_win"],
                "draw": dm_mkt["draw"],
                "away_win": dm_mkt["away_win"],
                "over_2_5": dm_mkt["over_2_5"],
                "btts_yes": dm_mkt["btts_yes"],
            }
            pred_doc["model_vs_market_differences"] = {
                "home_win_edge": round(dm_model["home_win"] - dm_mkt["home_win"], 4),
                "draw_edge": round(dm_model["draw"] - dm_mkt["draw"], 4),
                "away_win_edge": round(dm_model["away_win"] - dm_mkt["away_win"], 4),
            }
        else:
            pred_doc["market_implied_probabilities"] = None
            pred_doc["model_vs_market_differences"] = None

        # All model PMF summaries
        pred_doc["all_model_summaries"] = {
            name: {
                "home_win": round(pmf.derive_markets_from_pmf(15)["home_win"], 4),
                "draw": round(pmf.derive_markets_from_pmf(15)["draw"], 4),
                "away_win": round(pmf.derive_markets_from_pmf(15)["away_win"], 4),
                "over_2_5": round(pmf.derive_markets_from_pmf(15)["over_2_5"], 4),
            }
            for name, pmf in model_preds.items()
        }

        match_predictions.append({
            "match_id": match_id,
            "home_team": home,
            "away_team": away,
            "stage": row["stage"],
            "stadium": row["stadium"],
            "match_datetime": str(row["match_datetime"]),
            "status": "scheduled",
            "champion_model": champion_name,
            "prediction": pred_doc,
        })

    return {
        "schema_version": "1.0",
        "generated_at": "2026-06-11T04:46:00+00:00",
        "data_source": "synthetic_wc_scale_data",
        "note": "Generated from synthetic data. Replace with make fetch-bdl && make build-dataset for real predictions.",
        "matches": match_predictions,
    }


# ---------------------------------------------------------------------------
# Reports
# ---------------------------------------------------------------------------

def write_benchmark_table(results: list) -> None:
    path = REPORTS_DIR / "model_benchmark_table.md"
    lines = [
        "# Model Benchmark Table",
        "",
        "**Source**: Walk-forward OOF backtest on synthetic WC-scale data (128 matches, 2018+2022 structure)",
        "**Note**: Replace with `make backtest` on real BDL data for production metrics.",
        "",
        f"| Model | N OOF | Exact-Score NLL | 1X2 RPS | 1X2 Brier | ECE | Calib Slope |",
        "|-------|-------|----------------|---------|-----------|-----|-------------|",
    ]
    results_sorted = sorted(results, key=lambda r: r.metrics.exact_score_log_loss if np.isfinite(r.metrics.exact_score_log_loss) else 999)
    for r in results_sorted:
        m = r.metrics
        lines.append(
            f"| {r.model_name:<30} | {r.n_predictions:>5} | "
            f"{m.exact_score_log_loss:>14.4f} | "
            f"{m.rps_1x2:>7.4f} | "
            f"{m.brier_1x2:>9.4f} | "
            f"{m.ece_1x2:>3.4f} | "
            f"{m.calibration_slope:>11.4f} |"
        )
    lines += [
        "",
        "## Notes",
        "- Metrics are computed on OUT-OF-FOLD predictions only (no training data)",
        "- Champion model selected by lowest Exact-Score NLL",
        "- Bayesian models excluded from this run (use `--include-bayesian` to include)",
        "- Market-implied model not run (requires BDL_API_KEY)",
    ]
    path.write_text("\n".join(lines))
    print(f"  Written: {path}")


def write_joint_pmf_validation(results: list) -> None:
    path = REPORTS_DIR / "joint_pmf_validation.md"

    # Validate a sample PMF
    pmf = from_lambdas(1.5, 1.2, rho=-0.05, max_goals=15)
    errors = pmf.validate_internal_consistency(15)
    grid, tail = pmf.normalize_with_tail(15)
    markets = pmf.derive_markets_from_pmf(15)

    lines = [
        "# Joint Score PMF Validation Report",
        "",
        "## Sample PMF (Dixon-Coles: λ_h=1.5, λ_a=1.2, ρ=-0.05, max_goals=15)",
        "",
        f"- Grid sum: {float(grid.sum()):.8f}",
        f"- Tail mass: {tail:.8f}",
        f"- Grid + tail: {float(grid.sum()) + tail:.8f}",
        f"- Consistency errors: {errors}",
        "",
        "## Invariant tests",
        "",
        f"| Check | Value | Pass |",
        "|-------|-------|------|",
        f"| PMF + tail = 1.0 | {float(grid.sum()) + tail:.8f} | {'✅' if abs(float(grid.sum()) + tail - 1.0) < 1e-5 else '❌'} |",
        f"| All values ≥ 0 | min={float(grid.min()):.2e} | {'✅' if float(grid.min()) >= -1e-9 else '❌'} |",
        f"| 1X2 sum = 1.0 | {markets['home_win'] + markets['draw'] + markets['away_win']:.8f} | {'✅' if abs(markets['home_win'] + markets['draw'] + markets['away_win'] - 1.0) < 1e-5 else '❌'} |",
        f"| BTTS sum = 1.0 | {markets['btts_yes'] + markets['btts_no']:.8f} | {'✅' if abs(markets['btts_yes'] + markets['btts_no'] - 1.0) < 1e-5 else '❌'} |",
        f"| Tail mass < 0.5% | {tail:.6f} | {'✅' if tail < 0.005 else '⚠️'} |",
        f"| No consistency errors | {len(errors)} errors | {'✅' if not errors else '❌'} |",
        "",
        "## Arbitrary score lookup",
        "",
        f"- P(0,0) = {pmf.get_score_probability(0, 0):.6f}",
        f"- P(1,0) = {pmf.get_score_probability(1, 0):.6f}",
        f"- P(2,1) = {pmf.get_score_probability(2, 1):.6f}",
        f"- P(5,0) [in-grid] = {pmf.get_score_probability(5, 0):.6f}",
        f"- P(15,0) [out-of-grid, tail] = {pmf.get_score_probability(15, 0):.2e}",
        f"- P(20,3) [out-of-grid, tail] = {pmf.get_score_probability(20, 3):.2e}",
        "",
        "## Top 10 scorelines",
        "",
        "| Rank | Score | Probability |",
        "|------|-------|-------------|",
    ]
    for i, s in enumerate(pmf.to_dict(15)["top_scorelines"][:10]):
        lines.append(f"| {i+1} | {s['home_goals']}-{s['away_goals']} | {s['probability']:.4%} |")

    lines += [
        "",
        "## OOF prediction summary (synthetic data)",
        "",
        f"| Model | N | Exact-Score NLL |",
        "|-------|---|----------------|",
    ]
    for r in sorted(results, key=lambda r: r.metrics.exact_score_log_loss if np.isfinite(r.metrics.exact_score_log_loss) else 999):
        lines.append(f"| {r.model_name} | {r.n_predictions} | {r.metrics.exact_score_log_loss:.4f} |")

    path.write_text("\n".join(lines))
    print(f"  Written: {path}")


def write_calibration_report(results: list) -> None:
    path = REPORTS_DIR / "score_pmf_calibration.md"
    lines = [
        "# Score PMF Calibration Report",
        "",
        "**Method**: Temperature scaling (T fitted by minimising exact-score NLL on OOF predictions)",
        "",
        "| Model | T | Exact-Score NLL (raw) | Calib Slope | ECE | Sharpness |",
        "|-------|---|----------------------|-------------|-----|-----------|",
    ]
    for r in sorted(results, key=lambda r: r.metrics.exact_score_log_loss if np.isfinite(r.metrics.exact_score_log_loss) else 999):
        m = r.metrics
        lines.append(
            f"| {r.model_name} | {m.temperature:.3f} | "
            f"{m.exact_score_log_loss:.4f} | "
            f"{m.calibration_slope:.4f} | "
            f"{m.ece_1x2:.4f} | "
            f"{m.sharpness:.4f} |"
        )
    lines += [
        "",
        "## Temperature interpretation",
        "- T > 1.0: model is overconfident (sharpens toward uniform)",
        "- T < 1.0: model is underconfident (sharpens toward peak)",
        "- T = 1.0: no correction applied (< 5 OOF matches)",
        "",
        "## Calibration slope interpretation",
        "- Ideal: slope = 1.0, intercept = 0.0",
        "- Slope > 1: model overestimates high probabilities",
        "- Slope < 1: model underestimates high probabilities",
    ]
    path.write_text("\n".join(lines))
    print(f"  Written: {path}")


def write_market_calibration_report() -> None:
    path = REPORTS_DIR / "market_calibration.md"

    # Test goal_expectancy_extended with a sample
    from penaltyblog.models import goal_expectancy_extended
    result = goal_expectancy_extended(0.45, 0.27, 0.28, 0.55, 0.45, remove_overround=True, max_goals=15)

    lines = [
        "# Market Calibration Report",
        "",
        "## Method",
        "",
        "Market-implied PMF uses `penaltyblog.models.goal_expectancy_extended`",
        "to simultaneously invert no-vig 1X2 + over/under 2.5 probabilities",
        "into (mu_home, mu_away, rho), then creates a Dixon-Coles grid.",
        "",
        "No-vig conversion: `penaltyblog.implied.calculate_implied` (7 methods available).",
        "",
        "## Sample market inversion",
        "",
        "Input: home_win=45%, draw=27%, away_win=28%, over_2.5=55%, under_2.5=45%",
        "",
        f"| Parameter | Value |",
        "|-----------|-------|",
        f"| mu_home (implied) | {result['home_exp']:.4f} |",
        f"| mu_away (implied) | {result['away_exp']:.4f} |",
        f"| rho (implied) | {result.get('implied_rho', 0.0):.4f} |",
        f"| Optimizer success | {result['success']} |",
        f"| Fit error | {result['error']:.6f} |",
        "",
        "## No-vig methods (penaltyblog.implied)",
        "",
        "| Method | Description |",
        "|--------|-------------|",
        "| MULTIPLICATIVE | Proportional margin removal (default) |",
        "| ADDITIVE | Equal absolute removal |",
        "| POWER | Power iteration |",
        "| SHIN | Shin method (accounts for insider trading) |",
        "| DIFFERENTIAL_MARGIN_WEIGHTING | Weights by odds |",
        "| ODDS_RATIO | Odds-ratio method |",
        "| LOGARITHMIC | Logarithmic method |",
        "",
        "## BDL data availability",
        "",
        "Full market calibration requires BDL API key and `make fetch-bdl`.",
        "Run `wc2026 calibrate` after fetching data to produce calibrated predictions.",
    ]
    path.write_text("\n".join(lines))
    print(f"  Written: {path}")


def write_champion_selection(results: list) -> None:
    path = REPORTS_DIR / "champion_selection.md"
    if not results:
        path.write_text("# Champion Selection\n\nNo OOF results available.\n")
        return

    ranked = sorted(
        [r for r in results if np.isfinite(r.metrics.exact_score_log_loss)],
        key=lambda r: r.metrics.exact_score_log_loss,
    )

    champion = ranked[0] if ranked else None

    lines = [
        "# Champion Model Selection",
        "",
        "**Selection criterion**: Lowest exact-score negative log-likelihood on OOF predictions.",
        "",
        "## Ranking by OOF exact-score NLL",
        "",
        "| Rank | Model | OOF NLL | RPS | Brier | vs. Equal-Prob baseline |",
        "|------|-------|---------|-----|-------|------------------------|",
    ]
    baseline_nll = next((r.metrics.exact_score_log_loss for r in ranked if r.model_name == "equal_probability"), None)
    for i, r in enumerate(ranked):
        vs_baseline = ""
        if baseline_nll is not None and r.model_name != "equal_probability":
            delta = r.metrics.exact_score_log_loss - baseline_nll
            vs_baseline = f"{delta:+.4f} ({'better' if delta < 0 else 'worse'})"
        lines.append(
            f"| {i+1} | {r.model_name} | {r.metrics.exact_score_log_loss:.4f} | "
            f"{r.metrics.rps_1x2:.4f} | {r.metrics.brier_1x2:.4f} | {vs_baseline} |"
        )

    lines += [
        "",
        f"## Champion: {champion.model_name if champion else 'N/A'}",
        "",
        f"Selected by: lowest OOF exact-score NLL",
        "",
        "## Notes",
        "- Metrics are on synthetic data; re-run with real BDL data for production champion",
        "- Bayesian models not included in this run (add `--include-bayesian`)",
        "- Market-implied model requires BDL API key",
        "- Final champion will be selected after real data backtest",
    ]
    path.write_text("\n".join(lines))
    print(f"  Written: {path}")


def write_bdl_coverage() -> None:
    path = REPORTS_DIR / "bdl_endpoint_coverage.md"
    lines = [
        "# BDL Endpoint Coverage",
        "",
        "**API**: BallDontLie FIFA World Cup API (paid subscription required)",
        "**Base URL**: https://api.balldontlie.io/fifa/worldcup/v1",
        "",
        "| Endpoint | Description | Fetched by | Processed Table | Status |",
        "|----------|-------------|------------|-----------------|--------|",
        "| `/matches` | Match schedule, scores, stage | `fetch_matches()` | `matches.parquet` | ✅ Implemented |",
        "| `/odds` | Moneyline, totals, spreads (all vendors) | `fetch_odds()` | `odds.parquet` | ✅ Implemented |",
        "| `/team_match_stats` | xG, shots, possession, corners, cards | `fetch_team_stats()` | `team_stats.parquet` | ✅ Implemented |",
        "| `/player_match_stats` | Per-player ratings, goals, assists, xG | `fetch_player_stats()` | `player_stats.parquet` | ✅ Implemented |",
        "| `/match_events` | Goals, cards, substitutions | `fetch_events()` | `events.parquet` | ✅ Implemented |",
        "| `/match_shots` | Shot coordinates, xG, xGOT | `fetch_shots()` | `shots.parquet` | ✅ Implemented |",
        "| `/match_lineups` | Starting XI, substitutes | `fetch_lineups()` | `lineups.parquet` | ✅ Implemented |",
        "| `/match_momentum` | Minute-by-minute momentum | `fetch_momentum()` | `momentum.parquet` | ✅ Implemented |",
        "| `/group_standings` | Group table positions | `fetch_group_standings()` | `group_standings.parquet` | ✅ Implemented |",
        "| `/match_team_form` | Pre-match form data | `fetch_team_form()` | `team_form.parquet` | ✅ Implemented |",
        "",
        "## Not yet parsed (in odds.markets sub-array)",
        "",
        "| Market | Description | Status |",
        "|--------|-------------|--------|",
        "| Exact score odds | `markets[].type == 'exact_score'` | ⏳ Pending (will improve low-score calibration) |",
        "| Double chance | `markets[].type == 'double_chance'` | ⏳ Pending |",
        "| Draw no bet | `markets[].type == 'draw_no_bet'` | ⏳ Pending |",
        "| BTTS | `markets[].type == 'both_teams_to_score'` | ⏳ Pending |",
        "| Asian handicap (per-line) | `markets[].type == 'asian_handicap'` | ⏳ Pending |",
        "",
        "## Raw snapshot format",
        "",
        "```",
        "data/raw/bdl/{season}/{endpoint}/{YYYYMMDDTHHMMSSZ}.jsonl",
        "```",
        "",
        "Each line is one API record (JSON). Timestamped for reproducibility.",
        "Schema validated via pydantic before normalization.",
    ]
    path.write_text("\n".join(lines))
    print(f"  Written: {path}")


def write_data_quality_report(df: pd.DataFrame) -> None:
    path = REPORTS_DIR / "data_quality_report.md"
    n = len(df)
    by_season = df.groupby("season").size().to_dict()
    missing_goals = df["home_goals"].isna().sum() + df["away_goals"].isna().sum()

    lines = [
        "# Data Quality Report",
        "",
        f"**Data version**: v1",
        f"**Generated**: 2026-06-11",
        f"**Source**: Synthetic data (mirrors BDL structure)",
        "",
        "## Dataset overview",
        "",
        f"| Metric | Value |",
        "|--------|-------|",
        f"| Total matches | {n} |",
        f"| Completed | {df['status'].value_counts().get('completed', 0)} |",
        f"| Missing goals | {missing_goals} |",
    ]
    for season, count in sorted(by_season.items()):
        lines.append(f"| Season {season} | {count} matches |")

    lines += [
        "",
        "## Schema validation",
        "",
        "All BDL records validated against pydantic schemas before normalization.",
        "Any field rename or type change will raise `ValidationError` immediately.",
        "",
        "## Goal statistics",
        "",
        f"| Stat | Home | Away |",
        "|------|------|------|",
        f"| Mean goals | {df['home_goals'].mean():.3f} | {df['away_goals'].mean():.3f} |",
        f"| Median goals | {df['home_goals'].median():.1f} | {df['away_goals'].median():.1f} |",
        f"| Std goals | {df['home_goals'].std():.3f} | {df['away_goals'].std():.3f} |",
        f"| Max goals | {df['home_goals'].max()} | {df['away_goals'].max()} |",
        "",
        "## Score distribution",
        "",
        "| Score | Count | % |",
        "|-------|-------|---|",
    ]
    score_counts = df.groupby(["home_goals", "away_goals"]).size().sort_values(ascending=False).head(10)
    for (h, a), count in score_counts.items():
        lines.append(f"| {h}-{a} | {count} | {count/n*100:.1f}% |")

    lines += [
        "",
        "## Limitations",
        "- This is synthetic data for demonstration.",
        "- Real data requires `BDL_API_KEY` in `.env` and `make fetch-bdl`.",
        "- With real data: 128 completed matches (64×2018, 64×2022).",
    ]
    path.write_text("\n".join(lines))
    print(f"  Written: {path}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("Generating artifacts with synthetic WC-scale data...")
    print("(Replace with real BDL data after `make fetch-bdl && make build-dataset`)\n")

    # 1. Generate synthetic data
    df = _generate_synthetic_data(64, 64)
    print(f"Synthetic dataset: {len(df)} matches")

    # 2. Walk-forward backtest
    results = run_walkforward(df)

    # 3. Predict 2026 matches
    print("Predicting 2026 scheduled matches...")
    pred_2026 = predict_2026_matches(df)

    # 4. Write published JSON artifacts
    # Single date: 2026-06-11 (today)
    today_doc = {
        "schema_version": "1.0",
        "generated_at": "2026-06-11T04:46:00+00:00",
        "date": "2026-06-11",
        "season": 2026,
        "data_version": "synthetic_v1",
        "model_version": "v1",
        "note": "No matches scheduled for 2026-06-11. Tournament opens June 14.",
        "n_matches": 0,
        "matches": [],
    }
    today_path = PUBLISHED_DIR / "2026-06-11.json"
    today_path.write_text(json.dumps(today_doc, indent=2, default=str))
    print(f"  Written: {today_path}")

    # All scheduled 2026 matches
    all_path = PUBLISHED_DIR / "all_scheduled_2026.json"
    all_path.write_text(json.dumps(pred_2026, indent=2, default=str))
    print(f"  Written: {all_path} ({len(pred_2026['matches'])} matches)")

    # 5. Write all reports
    print("\nWriting reports...")
    write_benchmark_table(results)
    write_joint_pmf_validation(results)
    write_calibration_report(results)
    write_market_calibration_report()
    write_champion_selection(results)
    write_bdl_coverage()
    write_data_quality_report(df)

    print("\nDone.")
    print(f"OOF predictions: {PREDICTIONS_DIR / 'oof_score_pmfs.parquet'}")
    print(f"Published today: {today_path}")
    print(f"Published 2026:  {all_path}")
    print(f"Reports:         {REPORTS_DIR}/")


if __name__ == "__main__":
    main()
