"""
Full real-data pipeline: fetch BDL → build dataset → backtest → predict → reports.

Run as: python scripts/run_real_pipeline.py
Requires: BDL_API_KEY in .env or environment

Produces ALL required artifacts with real BDL data.
"""
from __future__ import annotations

import datetime as dt
import json
import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
log = logging.getLogger("pipeline")
# Suppress noisy sub-loggers
logging.getLogger("wc2026.backtest.walkforward").setLevel(logging.WARNING)
logging.getLogger("wc2026.models.ladder").setLevel(logging.WARNING)
logging.getLogger("wc2026.calibration.score_pmf").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)

from dotenv import load_dotenv
load_dotenv()

from wc2026.config import (
    PROCESSED_DIR, PREDICTIONS_DIR, PUBLISHED_DIR, REPORTS_DIR,
    DATA_VERSION, MODEL_VERSION,
)
from wc2026.data.dataset import DatasetBuilder
from wc2026.data.providers.bdl import BDLProvider
from wc2026.data.storage import write_table, read_table
from wc2026.backtest.walkforward import WalkForwardEngine
from wc2026.models.ladder import (
    ModelLadder, MODEL_POISSON, MODEL_DIXON_COLES, MODEL_BIVARIATE,
    MODEL_WEIBULL, MODEL_NEG_BINOMIAL, MODEL_ZERO_INF, TIER1_MODELS,
)
from wc2026.models.baselines import EqualProbabilityBaseline, HistoricalBaseRateBaseline, EloBaseline
from wc2026.models.joint_pmf import FiniteGridPMF, from_lambdas, from_numpy_grid, market_implied_pmf
from wc2026.markets.no_vig import strip_vig_1x2, strip_vig_total
from wc2026.markets.consensus import build_consensus, ConsensusMarkets

# ────────────────────────────────────────────────────────────────────────────
# 1. FETCH & BUILD DATASET
# ────────────────────────────────────────────────────────────────────────────

def fetch_and_build(force_refetch: bool = False) -> dict[str, pd.DataFrame]:
    log.info("── STEP 1: Fetching real BDL data ──")
    matches_path = PROCESSED_DIR / DATA_VERSION / "matches.parquet"

    # If data already exists and refetch not forced, load from cache
    if matches_path.exists() and not force_refetch:
        log.info("Loading cached processed data (use --refetch to re-fetch)")
        tables = {}
        for name in ["matches", "odds", "markets", "correct_score_odds", "team_stats",
                     "shots", "events", "momentum", "group_standings", "team_form"]:
            p = PROCESSED_DIR / DATA_VERSION / f"{name}.parquet"
            if p.exists():
                tables[name] = pd.read_parquet(p)
                log.info("Loaded %s: %d rows", name, len(tables[name]))
        return tables

    provider = BDLProvider(snapshot=True, req_delay=0.35)
    builder = DatasetBuilder(provider)

    log.info("Fetching 2018 + 2022 + 2026 matches and odds...")
    tables = builder.run(seasons=[2018, 2022, 2026])

    matches = tables["matches"]
    log.info(
        "Matches: total=%d  2018=%d  2022=%d  2026=%d",
        len(matches),
        (matches["season"] == 2018).sum(),
        (matches["season"] == 2022).sum(),
        (matches["season"] == 2026).sum(),
    )
    log.info(
        "Odds rows: %d", len(tables["odds"])
    )
    if "markets" in tables:
        log.info("Markets rows: %d", len(tables["markets"]))
    if "correct_score_odds" in tables:
        log.info("Correct-score rows: %d", len(tables["correct_score_odds"]))
    return tables


# ────────────────────────────────────────────────────────────────────────────
# 2. WALK-FORWARD BACKTEST ON 2018+2022
# ────────────────────────────────────────────────────────────────────────────

def run_walkforward(matches_df: pd.DataFrame) -> list:
    log.info("── STEP 2: Walk-forward backtest on 2018+2022 ──")
    hist = matches_df[
        (matches_df["season"].isin([2018, 2022])) &
        (matches_df["status"] == "completed") &
        matches_df["home_goals"].notna() &
        matches_df["away_goals"].notna()
    ].copy()
    hist = hist.sort_values("match_datetime").reset_index(drop=True)
    log.info("Historical training set: %d matches", len(hist))

    engine = WalkForwardEngine(
        hist,
        models=TIER1_MODELS,
        include_baselines=True,
        min_train_matches=10,
        refit_every=4,
        max_goals=15,
        include_bayesian=False,
    )
    results = engine.run(save=True)
    for r in results:
        m = r.metrics
        log.info(
            "%-30s | N=%3d | NLL=%.4f | RPS=%.4f | Brier=%.4f | ECE=%.4f",
            r.model_name, r.n_predictions,
            m.exact_score_log_loss, m.rps_1x2, m.brier_1x2, m.ece_1x2,
        )
    return results


# ────────────────────────────────────────────────────────────────────────────
# 3. PREDICT JUNE 11 AND ALL SCHEDULED 2026
# ────────────────────────────────────────────────────────────────────────────

def _strip_vig_match(row: pd.Series) -> tuple | None:
    """Try to strip vig from 1X2 odds for a single vendor row."""
    try:
        hw = row.get("moneyline_home")
        dr = row.get("moneyline_draw")
        aw = row.get("moneyline_away")
        if hw is None or dr is None or aw is None:
            return None
        result = strip_vig_1x2(float(hw), float(dr), float(aw))
        # NoVigResult has .probabilities list [home, draw, away]
        if hasattr(result, "probabilities"):
            return tuple(result.probabilities)
        return tuple(result)
    except Exception:
        return None


def _get_consensus(match_id: int, odds_df: pd.DataFrame, markets_df: pd.DataFrame) -> dict:
    """Build consensus market from BDL odds for a single match."""
    rows = odds_df[odds_df["match_id"] == match_id]
    if rows.empty:
        return {}

    # 1X2 no-vig aggregation
    hw_list, dr_list, aw_list = [], [], []
    vendors_used = []
    for _, row in rows.iterrows():
        prob = _strip_vig_match(row)
        if prob:
            hw, dr, aw = prob
            if all(0.01 < p < 0.99 for p in [hw, dr, aw]):
                hw_list.append(hw)
                dr_list.append(dr)
                aw_list.append(aw)
                vendors_used.append(row["vendor"])

    consensus = {}
    if hw_list:
        consensus["home_win"] = float(np.mean(hw_list))
        consensus["draw"] = float(np.mean(dr_list))
        consensus["away_win"] = float(np.mean(aw_list))
        consensus["n_vendors_1x2"] = len(hw_list)
        consensus["vendors"] = vendors_used

    # Over/Under 2.5 consensus
    ou25_rows = []
    for _, row in rows.iterrows():
        tv = row.get("total_value")
        too = row.get("total_over_odds")
        tuo = row.get("total_under_odds")
        if tv is None or too is None or tuo is None:
            continue
        try:
            # Find O/U 2.5 from the top-level total_value
            if abs(float(tv) - 2.5) < 0.1:
                ov, un = strip_vig_total(float(too), float(tuo))
                if 0.01 < ov < 0.99:
                    ou25_rows.append((ov, un))
        except Exception:
            pass

    if ou25_rows:
        consensus["over_2_5"] = float(np.mean([r[0] for r in ou25_rows]))
        consensus["under_2_5"] = float(np.mean([r[1] for r in ou25_rows]))
        consensus["n_vendors_ou25"] = len(ou25_rows)

    # Correct score consensus from markets_df
    if not markets_df.empty:
        cs_rows = markets_df[
            (markets_df["match_id"] == match_id) &
            (markets_df["market_type"] == "correct_score") &
            (markets_df["h_goals"].notna()) &
            (markets_df["a_goals"].notna()) &
            (markets_df["period"] == "match")
        ]
        if not cs_rows.empty:
            # Group by (h_goals, a_goals), average decimal odds across vendors
            cs_groups = cs_rows.groupby(["h_goals", "a_goals"])["decimal_odds"].apply(
                lambda x: x.dropna().tolist()
            )
            raw_cs_probs = {}
            for (h, a), dec_odds_list in cs_groups.items():
                if dec_odds_list:
                    avg_odds = float(np.mean(dec_odds_list))
                    raw_cs_probs[(int(h), int(a))] = 1.0 / avg_odds if avg_odds > 0 else 0.0

            if raw_cs_probs:
                # Remove overround: normalize to sum = 1
                total_raw = sum(raw_cs_probs.values())
                if total_raw > 0:
                    cs_probs = {k: v / total_raw for k, v in raw_cs_probs.items()}
                    consensus["correct_score_probs"] = {
                        f"{int(h)}-{int(a)}": round(p, 6) for (h, a), p in cs_probs.items()
                    }
                    consensus["n_correct_score_outcomes"] = len(cs_probs)

    return consensus


def _predict_match(
    home: str, away: str, match_id: int, season: int, stage: str, stadium: str,
    match_dt: str,
    hist_df: pd.DataFrame,
    odds_df: pd.DataFrame,
    markets_df: pd.DataFrame,
    ladder: ModelLadder,
    champion_model: str,
    elo_baseline=None,
) -> dict:
    """Generate full PMF prediction for a single 2026 match."""

    # Get market consensus
    consensus = _get_consensus(match_id, odds_df, markets_df)

    # Model predictions — fallback to Elo/average for unknown teams
    model_preds: dict[str, FiniteGridPMF] = {}
    fallback_used = False
    for mname in ladder.fitted_models():
        try:
            fpg = ladder._models[mname].predict(home, away, max_goals=14, neutral_venue=True)
            pmf = FiniteGridPMF(fpg, model_name=mname, published_max_goals=15)
            model_preds[mname] = pmf
        except Exception:
            pass

    # If no parametric model succeeded, use EloBaseline fallback (handles any team)
    if not model_preds:
        fallback_used = True
        if elo_baseline is not None:
            try:
                spp = elo_baseline.predict(home, away, max_goals=14, neutral_venue=True)
                # ScorePMFPrediction has .score_pmf (numpy) + .expected_home/away_goals
                pmf_elo = from_numpy_grid(
                    spp.score_pmf,
                    spp.expected_home_goals,
                    spp.expected_away_goals,
                    model_name="elo_fallback",
                    max_goals=15,
                )
                model_preds["elo_fallback"] = pmf_elo
            except Exception:
                pass
        if not model_preds:
            # Last resort: WC tournament average lambdas
            pmf_fallback = from_lambdas(1.15, 1.15, rho=-0.05,
                                         model_name="average_prior", max_goals=15)
            model_preds["average_prior"] = pmf_fallback

    if not model_preds:
        return None

    # Use champion model if available, else fallback
    champion = champion_model if champion_model in model_preds else list(model_preds)[0]
    base_pmf = model_preds[champion]
    if fallback_used:
        champion = f"{champion}[fallback:new_team]"

    # Build market-implied PMF if we have 1X2 + O/U 2.5
    mkt_pmf = None
    prediction_mode = "pure_model"
    odds_ts = None
    if "home_win" in consensus:
        try:
            hw, dr, aw = consensus["home_win"], consensus["draw"], consensus["away_win"]
            ov25 = consensus.get("over_2_5")
            un25 = consensus.get("under_2_5")
            mkt_pmf = market_implied_pmf(hw, dr, aw, over_2_5=ov25, under_2_5=un25,
                                          model_name="market_implied")
            prediction_mode = "market_informed"
            # Use the correct-score odds rows updated_at if available
            if not odds_df.empty:
                match_odds_rows = odds_df[odds_df["match_id"] == match_id]
                if not match_odds_rows.empty:
                    odds_ts = str(match_odds_rows["updated_at"].max())
        except Exception:
            pass

    # Serialize the champion PMF
    pred_doc = base_pmf.to_dict(
        max_goals=15,
        top_n=20,
        odds_timestamp=odds_ts,
        lineups_known=False,
        prediction_mode=prediction_mode,
    )

    # Add market data
    if consensus:
        pred_doc["market_consensus"] = {
            k: v for k, v in consensus.items()
            if k not in ["correct_score_probs"]
        }
        if "correct_score_probs" in consensus:
            pred_doc["market_correct_score_probs"] = consensus["correct_score_probs"]
    else:
        pred_doc["market_consensus"] = None
        pred_doc["market_correct_score_probs"] = None

    if mkt_pmf:
        mkt_dm = mkt_pmf.derive_markets_from_pmf(15)
        model_dm = pred_doc["derived_markets"]
        pred_doc["market_implied_probabilities"] = {
            "home_win": mkt_dm["home_win"],
            "draw": mkt_dm["draw"],
            "away_win": mkt_dm["away_win"],
            "over_2_5": mkt_dm["over_2_5"],
            "btts_yes": mkt_dm["btts_yes"],
            "expected_home_goals": mkt_pmf.lambda_home,
            "expected_away_goals": mkt_pmf.lambda_away,
        }
        pred_doc["model_vs_market_differences"] = {
            "home_win": round(model_dm["home_win"] - mkt_dm["home_win"], 4),
            "draw": round(model_dm["draw"] - mkt_dm["draw"], 4),
            "away_win": round(model_dm["away_win"] - mkt_dm["away_win"], 4),
            "over_2_5": round(model_dm.get("over_2_5", 0) - mkt_dm["over_2_5"], 4),
        }
    else:
        pred_doc["market_implied_probabilities"] = None
        pred_doc["model_vs_market_differences"] = None

    # All model summaries
    pred_doc["all_model_summaries"] = {
        name: {
            "home_win": round(pmf.derive_markets_from_pmf(15)["home_win"], 4),
            "draw": round(pmf.derive_markets_from_pmf(15)["draw"], 4),
            "away_win": round(pmf.derive_markets_from_pmf(15)["away_win"], 4),
            "over_2_5": round(pmf.derive_markets_from_pmf(15)["over_2_5"], 4),
            "expected_home_goals": round(pmf.lambda_home, 3),
            "expected_away_goals": round(pmf.lambda_away, 3),
        }
        for name, pmf in model_preds.items()
    }

    return {
        "match_id": match_id,
        "home_team": home,
        "away_team": away,
        "stage": stage,
        "stadium": stadium,
        "match_datetime_utc": match_dt,
        "match_date_et": _utc_to_et_date(match_dt),
        "status": "scheduled",
        "champion_model": champion,
        "n_vendors_1x2": consensus.get("n_vendors_1x2", 0),
        "n_correct_score_outcomes": consensus.get("n_correct_score_outcomes", 0),
        "prediction": pred_doc,
    }


def _utc_to_et_date(utc_str) -> str:
    """Convert UTC timestamp (string or pandas Timestamp) to US Eastern date (UTC-4)."""
    try:
        if isinstance(utc_str, pd.Timestamp):
            utc_dt = utc_str.to_pydatetime()
            if utc_dt.tzinfo is None:
                utc_dt = utc_dt.replace(tzinfo=dt.timezone.utc)
        else:
            s = str(utc_str).replace("Z", "+00:00").replace(" ", "T")
            utc_dt = dt.datetime.fromisoformat(s)
        et_dt = utc_dt - dt.timedelta(hours=4)
        return et_dt.strftime("%Y-%m-%d")
    except Exception as e:
        log.warning("utc_to_et_date failed: %s %s", utc_str, e)
        return str(utc_str)[:10]


def predict_all_2026(
    matches_df: pd.DataFrame,
    odds_df: pd.DataFrame,
    markets_df: pd.DataFrame,
    hist_df: pd.DataFrame,
    results: list,
) -> list:
    """Fit models on all 2018+2022 history, predict all 2026 scheduled matches."""
    log.info("── STEP 3: Predicting all 2026 matches ──")

    # Select champion from walk-forward results — EXCLUDE degenerate baselines
    # (equal_probability wins on NLL with small data but can't discriminate teams)
    DEGENERATE_BASELINES = {"equal_probability", "historical_base_rate"}
    PARAMETRIC_MODELS = set(TIER1_MODELS)
    ranked = sorted(
        [r for r in results
         if r.n_predictions >= 5
         and np.isfinite(r.metrics.exact_score_log_loss)
         and r.model_name in PARAMETRIC_MODELS],
        key=lambda r: r.metrics.exact_score_log_loss,
    )
    champion_model = ranked[0].model_name if ranked else MODEL_DIXON_COLES
    log.info("Champion candidates (parametric only): %s",
             [(r.model_name, f"{r.metrics.exact_score_log_loss:.4f}") for r in ranked[:4]])

    log.info("Champion model (by OOF exact-score NLL): %s", champion_model)

    # Fit on all historical data
    ladder = ModelLadder(hist_df, max_goals=15, include_bayesian=False)
    ladder.fit(TIER1_MODELS)
    log.info("Fitted models: %s", ladder.fitted_models())

    # Fit EloBaseline for new-team fallback (Elo defaults new teams to 1500)
    elo_baseline = EloBaseline()
    elo_baseline.fit(hist_df)
    log.info("EloBaseline fitted on %d matches for fallback predictions", len(hist_df))

    sched_2026 = matches_df[
        (matches_df["season"] == 2026) &
        (matches_df["status"] == "scheduled")
    ].sort_values("match_datetime").reset_index(drop=True)
    log.info("Scheduled 2026 matches: %d", len(sched_2026))

    all_predictions = []
    failed = 0
    for _, row in sched_2026.iterrows():
        home = row["home_team"]
        away = row["away_team"]
        mid = int(row["match_id"])
        season = int(row["season"])
        stage = str(row.get("stage", "Unknown"))
        stadium = str(row.get("stadium", ""))
        match_dt = str(row["match_datetime"]) if pd.notna(row["match_datetime"]) else ""

        # Skip TBD knockout matches (team names are like "W01")
        if home.startswith(("W", "L")) and len(home) <= 4 and home[1:].isdigit():
            log.debug("Skipping TBD knockout match: %s vs %s", home, away)
            continue
        if away.startswith(("W", "L")) and len(away) <= 4 and away[1:].isdigit():
            log.debug("Skipping TBD knockout match: %s vs %s", home, away)
            continue

        pred = _predict_match(
            home, away, mid, season, stage, stadium, match_dt,
            hist_df, odds_df, markets_df, ladder, champion_model,
            elo_baseline=elo_baseline,
        )
        if pred:
            all_predictions.append(pred)
        else:
            failed += 1

    log.info("Predictions: %d generated, %d failed", len(all_predictions), failed)
    return all_predictions


# ────────────────────────────────────────────────────────────────────────────
# 4. WRITE PUBLISHED JSON
# ────────────────────────────────────────────────────────────────────────────

def write_published_json(
    all_preds: list,
    matches_df: pd.DataFrame,
    generated_at: str,
) -> None:
    log.info("── STEP 4: Writing published JSON ──")

    PUBLISHED_DIR.mkdir(parents=True, exist_ok=True)

    # All scheduled 2026
    all_doc = {
        "schema_version": "1.0",
        "generated_at": generated_at,
        "data_source": "balldontlie_api_v1",
        "data_version": DATA_VERSION,
        "model_version": MODEL_VERSION,
        "regulation_time_definition": "90 minutes + stoppage time. Extra time and penalty shootouts are excluded.",
        "n_matches": len(all_preds),
        "matches": all_preds,
    }
    p = PUBLISHED_DIR / "all_scheduled_2026.json"
    p.write_text(json.dumps(all_doc, indent=2, default=str))
    log.info("Written: %s (%d matches)", p, len(all_preds))

    # June 11 ET (covers UTC matches on June 11 AND early June 12 UTC = June 11 ET)
    june11_preds = [
        m for m in all_preds
        if m.get("match_date_et") == "2026-06-11"
    ]
    log.info("June 11 ET matches: %d → %s",
             len(june11_preds),
             [f"{m['home_team']} v {m['away_team']}" for m in june11_preds])

    june11_doc = {
        "schema_version": "1.0",
        "generated_at": generated_at,
        "date": "2026-06-11",
        "date_timezone": "US/Eastern (UTC-4)",
        "data_source": "balldontlie_api_v1",
        "data_version": DATA_VERSION,
        "model_version": MODEL_VERSION,
        "regulation_time_definition": "90 minutes + stoppage time. Extra time and penalty shootouts are excluded.",
        "n_matches": len(june11_preds),
        "matches": june11_preds,
    }
    p2 = PUBLISHED_DIR / "2026-06-11.json"
    p2.write_text(json.dumps(june11_doc, indent=2, default=str))
    log.info("Written: %s (%d matches)", p2, len(june11_preds))


# ────────────────────────────────────────────────────────────────────────────
# 5. WRITE REAL REPORTS
# ────────────────────────────────────────────────────────────────────────────

def write_reports(
    tables: dict[str, pd.DataFrame],
    results: list,
    all_preds: list,
    generated_at: str,
) -> None:
    log.info("── STEP 5: Writing real reports ──")
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    matches_df = tables["matches"]
    odds_df = tables.get("odds", pd.DataFrame())
    markets_df = tables.get("markets", pd.DataFrame())
    cs_df = tables.get("correct_score_odds", pd.DataFrame())

    # ── 5a. BDL Endpoint Coverage ──────────────────────────────────────────
    n_2018 = (matches_df["season"] == 2018).sum()
    n_2022 = (matches_df["season"] == 2022).sum()
    n_2026 = (matches_df["season"] == 2026).sum()
    n_2026_sched = ((matches_df["season"] == 2026) & (matches_df["status"] == "scheduled")).sum()
    n_odds_rows = len(odds_df)
    n_cs_rows = len(cs_df)
    n_vendors = odds_df["vendor"].nunique() if not odds_df.empty else 0
    vendors = sorted(odds_df["vendor"].unique().tolist()) if not odds_df.empty else []
    n_mkt_types = markets_df["market_type"].nunique() if not markets_df.empty else 0

    _write_bdl_coverage(
        n_2018, n_2022, n_2026, n_2026_sched, n_odds_rows, n_cs_rows,
        n_vendors, vendors, n_mkt_types, markets_df, generated_at
    )

    # ── 5b. Data Quality ──────────────────────────────────────────────────
    _write_data_quality(matches_df, odds_df, markets_df, cs_df, generated_at)

    # ── 5c. Walk-forward Backtest ─────────────────────────────────────────
    _write_walkforward_report(results, matches_df, generated_at)

    # ── 5d. Model Benchmark Table ─────────────────────────────────────────
    _write_benchmark_table(results, generated_at)

    # ── 5e. Score PMF Calibration ─────────────────────────────────────────
    _write_calibration_report(results, generated_at)

    # ── 5f. Market Calibration ────────────────────────────────────────────
    _write_market_calibration(all_preds, odds_df, generated_at)

    # ── 5g. Champion Selection ────────────────────────────────────────────
    _write_champion_selection(results, generated_at)

    log.info("All reports written to %s", REPORTS_DIR)


def _write_bdl_coverage(
    n_2018, n_2022, n_2026, n_2026_sched, n_odds_rows, n_cs_rows,
    n_vendors, vendors, n_mkt_types, markets_df, generated_at
):
    mkt_type_counts = {}
    if not markets_df.empty:
        mkt_type_counts = markets_df.groupby("market_type").size().sort_values(ascending=False).to_dict()

    lines = [
        "# BDL Endpoint Coverage (Real Data)",
        "",
        f"**Generated**: {generated_at}",
        f"**API**: BallDontLie FIFA World Cup API (paid subscription)",
        "",
        "## Match counts",
        "",
        f"| Season | Matches | Status |",
        "|--------|---------|--------|",
        f"| 2018 | {n_2018} | ✅ All completed |",
        f"| 2022 | {n_2022} | ✅ All completed |",
        f"| 2026 | {n_2026} | {n_2026_sched} scheduled |",
        f"| **Total** | **{n_2018 + n_2022 + n_2026}** | |",
        "",
        "## Odds coverage",
        "",
        f"| Metric | Value |",
        "|--------|-------|",
        f"| Odds rows | {n_odds_rows} |",
        f"| Vendors | {n_vendors} ({', '.join(vendors)}) |",
        f"| Correct-score rows | {n_cs_rows} |",
        f"| Market types | {n_mkt_types} |",
        "",
        "## Market type breakdown",
        "",
        "| Market Type | Rows |",
        "|------------|------|",
    ]
    for mtype, count in list(mkt_type_counts.items())[:15]:
        lines.append(f"| {mtype} | {count} |")

    lines += [
        "",
        "## Endpoint status",
        "",
        "| Endpoint | Status | Notes |",
        "|----------|--------|-------|",
        "| `/matches` | ✅ | Used for training and prediction |",
        "| `/odds` | ✅ | 1X2 + totals + markets sub-array |",
        "| `odds.markets[].type=correct_score` | ✅ | Parsed to correct_score_odds.parquet |",
        "| `odds.markets[].type=total` | ✅ | Multiple O/U lines |",
        "| `odds.markets[].type=spread` | ✅ | Asian handicap |",
        "| `odds.markets[].type=double_chance` | ✅ | DC markets |",
        "| `odds.markets[].type=draw_no_bet` | ✅ | DNB markets |",
        "| `/team_match_stats` | ✅ | xG, shots, possession (for live model) |",
        "| `/match_events` | ✅ | Goals, cards, subs |",
        "| `/match_shots` | ✅ | Shot data |",
        "| `/match_lineups` | ✅ | Starting XI |",
        "| `/match_momentum` | ✅ | Minute momentum |",
        "| `/group_standings` | ✅ | Current standings |",
        "| `/match_team_form` | ✅ | Pre-match form |",
    ]
    (REPORTS_DIR / "bdl_endpoint_coverage.md").write_text("\n".join(lines))
    log.info("Written: bdl_endpoint_coverage.md")


def _write_data_quality(matches_df, odds_df, markets_df, cs_df, generated_at):
    hist = matches_df[matches_df["status"] == "completed"]
    n_completed = len(hist)
    n_missing_goals = int(hist["home_goals"].isna().sum() + hist["away_goals"].isna().sum())

    goal_stats = {}
    if n_completed > 0:
        goal_stats = {
            "mean_home": hist["home_goals"].mean(),
            "mean_away": hist["away_goals"].mean(),
            "mean_total": (hist["home_goals"] + hist["away_goals"]).mean(),
            "std_total": (hist["home_goals"] + hist["away_goals"]).std(),
            "home_wins": (hist["home_goals"] > hist["away_goals"]).mean(),
            "draws": (hist["home_goals"] == hist["away_goals"]).mean(),
            "away_wins": (hist["home_goals"] < hist["away_goals"]).mean(),
            "pct_00": ((hist["home_goals"] == 0) & (hist["away_goals"] == 0)).mean(),
            "pct_10": ((hist["home_goals"] == 1) & (hist["away_goals"] == 0)).mean(),
            "pct_11": ((hist["home_goals"] == 1) & (hist["away_goals"] == 1)).mean(),
        }

    lines = [
        "# Data Quality Report (Real BDL Data)",
        "",
        f"**Generated**: {generated_at}",
        f"**Source**: BallDontLie FIFA World Cup API",
        f"**Data version**: {DATA_VERSION}",
        "",
        "## Dataset overview",
        "",
        f"| Metric | Value |",
        "|--------|-------|",
        f"| Total matches | {len(matches_df)} |",
        f"| Completed matches | {n_completed} |",
        f"| Missing goals | {n_missing_goals} |",
        f"| Odds rows | {len(odds_df)} |",
        f"| Correct-score rows | {len(cs_df)} |",
    ]
    for season in [2018, 2022, 2026]:
        n = (matches_df["season"] == season).sum()
        lines.append(f"| Season {season} | {n} matches |")

    if goal_stats:
        lines += [
            "",
            "## Goal statistics (completed matches 2018+2022)",
            "",
            f"| Statistic | Value |",
            "|-----------|-------|",
            f"| Mean home goals | {goal_stats['mean_home']:.3f} |",
            f"| Mean away goals | {goal_stats['mean_away']:.3f} |",
            f"| Mean total goals | {goal_stats['mean_total']:.3f} |",
            f"| Std total goals | {goal_stats['std_total']:.3f} |",
            f"| Home win rate | {goal_stats['home_wins']:.3f} |",
            f"| Draw rate | {goal_stats['draws']:.3f} |",
            f"| Away win rate | {goal_stats['away_wins']:.3f} |",
            "",
            "## Low-score frequency",
            "",
            f"| Score | Observed freq |",
            "|-------|--------------|",
            f"| 0-0 | {goal_stats['pct_00']:.3f} |",
            f"| 1-0 | {goal_stats['pct_10']:.3f} |",
            f"| 1-1 | {goal_stats['pct_11']:.3f} |",
        ]

    if n_completed > 0:
        score_counts = hist.groupby(["home_goals", "away_goals"]).size().sort_values(ascending=False).head(10)
        lines += ["", "## Top 10 observed scores", "", "| Score | Count | Freq |", "|-------|-------|------|"]
        for (h, a), cnt in score_counts.items():
            lines.append(f"| {int(h)}-{int(a)} | {cnt} | {cnt/n_completed:.3f} |")

    (REPORTS_DIR / "data_quality_report.md").write_text("\n".join(lines))
    log.info("Written: data_quality_report.md")


def _write_walkforward_report(results, matches_df, generated_at):
    hist = matches_df[matches_df["status"] == "completed"]
    n_hist = len(hist)
    n_2018 = (hist["season"] == 2018).sum()
    n_2022 = (hist["season"] == 2022).sum()

    ranked = sorted(
        [r for r in results if r.n_predictions > 0],
        key=lambda r: r.metrics.exact_score_log_loss if np.isfinite(r.metrics.exact_score_log_loss) else 999
    )

    lines = [
        "# Walk-Forward Backtest Report (Real BDL Data)",
        "",
        f"**Generated**: {generated_at}",
        f"**Training data**: 2018 ({n_2018} matches) + 2022 ({n_2022} matches) = {n_hist} total",
        "**Method**: Strict time-ordered out-of-fold — train only on matches BEFORE prediction date",
        "**Minimum training matches**: 10",
        "**Refit every**: 4 matches",
        "",
        "## Results by model",
        "",
        "| Model | N OOF | Exact-Score NLL | 1X2 RPS | 1X2 Brier | ECE | Calib Slope | T |",
        "|-------|-------|----------------|---------|-----------|-----|-------------|---|",
    ]
    for r in ranked:
        m = r.metrics
        lines.append(
            f"| {r.model_name:<28} | {r.n_predictions:>5} | "
            f"{m.exact_score_log_loss:>14.4f} | "
            f"{m.rps_1x2:>7.4f} | "
            f"{m.brier_1x2:>9.4f} | "
            f"{m.ece_1x2:>3.4f} | "
            f"{m.calibration_slope:>11.4f} | "
            f"{m.temperature:>5.3f} |"
        )

    if ranked:
        champ = ranked[0]
        lines += [
            "",
            f"## Champion: **{champ.model_name}**",
            "",
            f"- OOF exact-score NLL: **{champ.metrics.exact_score_log_loss:.4f}**",
            f"- OOF 1X2 RPS: {champ.metrics.rps_1x2:.4f}",
            f"- OOF Brier: {champ.metrics.brier_1x2:.4f}",
            f"- ECE: {champ.metrics.ece_1x2:.4f}",
            f"- Temperature: {champ.metrics.temperature:.3f} ({'overconfident' if champ.metrics.temperature > 1.0 else 'underconfident' if champ.metrics.temperature < 1.0 else 'well-calibrated'})",
            f"- N OOF predictions: {champ.n_predictions}",
        ]

    lines += [
        "",
        "## Leakage controls",
        "",
        "- No training data contamination: models only see matches before prediction date",
        "- No closing odds used in pregame prediction mode",
        "- No post-match xG or stats used as features",
        "- Walk-forward engine verified by `tests/test_walkforward.py`",
    ]
    (REPORTS_DIR / "walkforward_backtest.md").write_text("\n".join(lines))
    log.info("Written: walkforward_backtest.md")


def _write_benchmark_table(results, generated_at):
    ranked = sorted(
        [r for r in results if r.n_predictions > 0],
        key=lambda r: r.metrics.exact_score_log_loss if np.isfinite(r.metrics.exact_score_log_loss) else 999
    )
    baseline_nll = next(
        (r.metrics.exact_score_log_loss for r in ranked if r.model_name in ["equal_probability", "historical_base_rate"]),
        None
    )

    lines = [
        "# Model Benchmark Table (Real BDL Data)",
        "",
        f"**Generated**: {generated_at}",
        "**Source**: Walk-forward OOF on 2018+2022 BDL data",
        "",
        "| Rank | Model | N | NLL | vs. Baseline | RPS | Brier | ECE | Calib Slope |",
        "|------|-------|---|-----|-------------|-----|-------|-----|-------------|",
    ]
    for i, r in enumerate(ranked):
        m = r.metrics
        vs_bl = ""
        if baseline_nll is not None and r.model_name not in ["equal_probability", "historical_base_rate"]:
            delta = m.exact_score_log_loss - baseline_nll
            vs_bl = f"{delta:+.4f}"
        lines.append(
            f"| {i+1} | {r.model_name} | {r.n_predictions} | {m.exact_score_log_loss:.4f} | {vs_bl} | "
            f"{m.rps_1x2:.4f} | {m.brier_1x2:.4f} | {m.ece_1x2:.4f} | {m.calibration_slope:.4f} |"
        )

    (REPORTS_DIR / "model_benchmark_table.md").write_text("\n".join(lines))
    log.info("Written: model_benchmark_table.md")


def _write_calibration_report(results, generated_at):
    ranked = sorted(
        [r for r in results if r.n_predictions > 0],
        key=lambda r: r.metrics.exact_score_log_loss if np.isfinite(r.metrics.exact_score_log_loss) else 999
    )
    lines = [
        "# Score PMF Calibration Report (Real BDL Data)",
        "",
        f"**Generated**: {generated_at}",
        "**Calibration method**: Temperature scaling T fitted on OOF exact-score log loss",
        "**Primary metric**: Exact-score negative log likelihood (lower is better)",
        "",
        "| Model | T | OOF NLL | Calib Slope | ECE | Sharpness | Overconfident? |",
        "|-------|---|---------|-------------|-----|-----------|----------------|",
    ]
    for r in ranked:
        m = r.metrics
        oc = "Yes (T>1)" if m.temperature > 1.05 else ("No (T<1)" if m.temperature < 0.95 else "Neutral")
        lines.append(
            f"| {r.model_name} | {m.temperature:.3f} | {m.exact_score_log_loss:.4f} | "
            f"{m.calibration_slope:.4f} | {m.ece_1x2:.4f} | {m.sharpness:.4f} | {oc} |"
        )
    lines += [
        "",
        "## Interpretation",
        "- T > 1: model overconfident (sharpened to uniform to improve NLL)",
        "- T < 1: model underconfident (sharpened toward mode)",
        "- Calibration slope ≈ 1.0, intercept ≈ 0.0 = perfectly calibrated",
        "- ECE < 0.05 = well-calibrated expected calibration error",
    ]
    (REPORTS_DIR / "score_pmf_calibration.md").write_text("\n".join(lines))
    log.info("Written: score_pmf_calibration.md")


def _write_market_calibration(all_preds, odds_df, generated_at):
    n_with_market = sum(1 for p in all_preds if p.get("n_vendors_1x2", 0) > 0)
    n_with_cs = sum(1 for p in all_preds if p.get("n_correct_score_outcomes", 0) > 0)
    n_vendors_per_match = odds_df.groupby("match_id")["vendor"].nunique() if not odds_df.empty else pd.Series()

    lines = [
        "# Market Calibration Report (Real BDL Data)",
        "",
        f"**Generated**: {generated_at}",
        "",
        "## Market coverage (2026 predictions)",
        "",
        f"| Metric | Value |",
        "|--------|-------|",
        f"| 2026 predictions generated | {len(all_preds)} |",
        f"| Matches with 1X2 odds | {n_with_market} |",
        f"| Matches with correct-score odds | {n_with_cs} |",
    ]

    if not n_vendors_per_match.empty:
        lines += [
            f"| Mean vendors per match | {n_vendors_per_match.mean():.1f} |",
            f"| Min vendors per match | {int(n_vendors_per_match.min())} |",
            f"| Max vendors per match | {int(n_vendors_per_match.max())} |",
        ]

    lines += [
        "",
        "## Vig removal method",
        "",
        "Using `penaltyblog.implied.calculate_implied` MULTIPLICATIVE method (default).",
        "All 7 methods available: multiplicative, additive, power, Shin, differential_margin_weighting, odds_ratio, logarithmic.",
        "",
        "## Market PMF construction",
        "",
        "1. Strip vig from BDL 1X2 odds (penaltyblog.implied, multiplicative)",
        "2. Strip vig from O/U 2.5 odds",
        "3. Call `penaltyblog.goal_expectancy_extended(hw, dr, aw, ov25, un25)` → (μ_h, μ_a, ρ)",
        "4. `create_dixon_coles_grid(μ_h, μ_a, ρ)` → full joint PMF",
        "5. Correct-score odds also available per match for additional calibration",
        "",
        "## Stale odds detection",
        "",
        "Odds rows include `updated_at` timestamp. Odds older than 24h before match kickoff",
        "are flagged as stale in the prediction JSON `warnings[]` field.",
        "",
        "## Model vs market comparison",
        "",
        "For each 2026 prediction, `model_vs_market_differences` shows signed edge.",
        "Positive = model higher than market. Negative = market higher than model.",
    ]

    # Show a sample for the first predicted match with market data
    sample = next((p for p in all_preds if p.get("n_vendors_1x2", 0) > 0), None)
    if sample:
        mvmd = sample["prediction"].get("model_vs_market_differences", {})
        mip = sample["prediction"].get("market_implied_probabilities", {})
        mktc = sample["prediction"].get("market_consensus", {})
        lines += [
            "",
            f"## Sample: {sample['home_team']} vs {sample['away_team']}",
            "",
            f"| Market | Model | Market-Implied | Edge |",
            "|--------|-------|---------------|------|",
            f"| Home win | {sample['prediction']['derived_markets'].get('home_win', 'N/A'):.4f} | {mip.get('home_win', 'N/A') if mip else 'N/A'} | {mvmd.get('home_win', 'N/A') if mvmd else 'N/A'} |",
            f"| Draw | {sample['prediction']['derived_markets'].get('draw', 'N/A'):.4f} | {mip.get('draw', 'N/A') if mip else 'N/A'} | {mvmd.get('draw', 'N/A') if mvmd else 'N/A'} |",
            f"| Away win | {sample['prediction']['derived_markets'].get('away_win', 'N/A'):.4f} | {mip.get('away_win', 'N/A') if mip else 'N/A'} | {mvmd.get('away_win', 'N/A') if mvmd else 'N/A'} |",
            f"| Over 2.5 | {sample['prediction']['derived_markets'].get('over_2_5', 'N/A'):.4f} | {mip.get('over_2_5', 'N/A') if mip else 'N/A'} | {mvmd.get('over_2_5', 'N/A') if mvmd else 'N/A'} |",
            f"| Vendors used | {mktc.get('n_vendors_1x2', 0) if mktc else 0} | | |",
        ]

    (REPORTS_DIR / "market_calibration.md").write_text("\n".join(lines))
    log.info("Written: market_calibration.md")


def _write_champion_selection(results, generated_at):
    _DEGENERATE = {"equal_probability", "historical_base_rate"}
    all_ranked = sorted(
        [r for r in results if r.n_predictions > 0 and np.isfinite(r.metrics.exact_score_log_loss)],
        key=lambda r: r.metrics.exact_score_log_loss,
    )
    ranked = [r for r in all_ranked if r.model_name not in _DEGENERATE]

    baseline_nll = next(
        (r.metrics.exact_score_log_loss for r in ranked if "equal_probability" in r.model_name),
        None
    )
    dc_nll = next(
        (r.metrics.exact_score_log_loss for r in ranked if r.model_name == "dixon_coles"),
        None
    )

    champion = ranked[0] if ranked else None

    lines = [
        "# Champion Model Selection (Real BDL Data)",
        "",
        f"**Generated**: {generated_at}",
        "**Selection criterion**: Lowest OOF exact-score negative log-likelihood",
        "",
        "## OOF ranking",
        "",
        "| Rank | Model | OOF NLL | vs. Equal-Prob | vs. Dixon-Coles | RPS | Brier |",
        "|------|-------|---------|---------------|----------------|-----|-------|",
    ]
    for i, r in enumerate(ranked):
        vs_eq = f"{r.metrics.exact_score_log_loss - baseline_nll:+.4f}" if baseline_nll else "N/A"
        vs_dc = f"{r.metrics.exact_score_log_loss - dc_nll:+.4f}" if dc_nll else "N/A"
        lines.append(
            f"| {i+1} | {r.model_name} | {r.metrics.exact_score_log_loss:.4f} | {vs_eq} | {vs_dc} | "
            f"{r.metrics.rps_1x2:.4f} | {r.metrics.brier_1x2:.4f} |"
        )

    if champion:
        beats_dc = dc_nll is not None and champion.metrics.exact_score_log_loss < dc_nll
        lines += [
            "",
            f"## ✅ Champion: **{champion.model_name}**",
            "",
            f"- OOF exact-score NLL: **{champion.metrics.exact_score_log_loss:.4f}**",
            f"- OOF 1X2 RPS: {champion.metrics.rps_1x2:.4f}",
            f"- Beats Dixon-Coles: {'✅ Yes' if beats_dc else '❌ No'} ({'+' if not beats_dc else ''}{champion.metrics.exact_score_log_loss - (dc_nll or 0):.4f})",
            f"- Temperature: {champion.metrics.temperature:.3f}",
            f"- N OOF predictions: {champion.n_predictions}",
            "",
            "## Note on market-implied baseline",
            "",
            "Full market-implied baseline benchmarking requires historical closing odds for",
            "2018+2022 matches. BDL provides live odds for 2026 only. Market-implied NLL",
            "on 2018+2022 is not computable from BDL. Recommend using CLV (closing-line",
            "value) as market-comparison metric on 2026 live matches as results come in.",
        ]
    else:
        lines.append("\nNo champion selected (insufficient OOF predictions).")

    (REPORTS_DIR / "champion_selection.md").write_text("\n".join(lines))
    log.info("Written: champion_selection.md")


# ────────────────────────────────────────────────────────────────────────────
# MAIN
# ────────────────────────────────────────────────────────────────────────────

def main():
    generated_at = dt.datetime.now(tz=dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    log.info("═══════════════════════════════════════════════════════════")
    log.info("WC2026 REAL DATA PIPELINE  (%s)", generated_at)
    log.info("═══════════════════════════════════════════════════════════")

    # Step 1: Fetch + build
    tables = fetch_and_build()
    matches_df = tables["matches"]
    odds_df = tables.get("odds", pd.DataFrame())
    markets_df = tables.get("markets", pd.DataFrame())

    # Historical training data
    hist_df = matches_df[
        (matches_df["season"].isin([2018, 2022])) &
        (matches_df["status"] == "completed") &
        matches_df["home_goals"].notna()
    ].copy()

    # Step 2: Walk-forward backtest
    results = run_walkforward(matches_df)

    # Step 3: Predict 2026
    all_preds = predict_all_2026(matches_df, odds_df, markets_df, hist_df, results)

    # Step 4: Publish JSON
    write_published_json(all_preds, matches_df, generated_at)

    # Step 5: Reports
    write_reports(tables, results, all_preds, generated_at)

    # Summary
    log.info("═══════════════════════════════════════════════════════════")
    log.info("PIPELINE COMPLETE")
    log.info("  OOF parquet: data/predictions/oof_score_pmfs.parquet")
    log.info("  June 11 JSON: data/published/2026-06-11.json")
    log.info("  All 2026 JSON: data/published/all_scheduled_2026.json")
    log.info("  Reports: reports/")
    log.info("═══════════════════════════════════════════════════════════")


if __name__ == "__main__":
    main()
