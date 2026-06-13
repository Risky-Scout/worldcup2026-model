"""
CLV Weight Grid Search
======================
Determines the optimal market_weight for CompositeTeamPrior by evaluating
different blending configurations against all completed 2026 World Cup matches.

Metrics reported per config:
  - mean_log_loss     : average -log(p_correct_outcome) for 1X2 (lower = better)
  - mean_exact_ll     : average -log(p_exact_score) (lower = better)
  - rps_1x2           : Ranked Probability Score on 1X2 (lower = better)
  - mean_clv_bits     : average log2(model_p / closing_p) from stored records (higher = better)
  - beat_close_rate   : fraction of CLV records where model_p > closing_p (higher = better)
  - model_mkt_diverge : mean |model_p - market_p| on 1X2 (higher = more independent)

Because only a handful of 2026 matches have completed so far, the log-loss
results will be directional rather than statistically definitive. The script
notes this explicitly and defaults to 0% market weight (pure penaltyblog) if
differences are within noise.

Usage
-----
  python scripts/clv_weight_search.py
  python scripts/clv_weight_search.py --save          # save CSV even on thin data

Results saved to:  data/clv_weight_search_results.csv
"""
from __future__ import annotations

import argparse
import json
import logging
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

import numpy as np
import pandas as pd
from scipy.stats import poisson as scipy_poisson

logging.basicConfig(
    level=logging.WARNING,
    format="%(levelname)s %(name)s: %(message)s",
)
log = logging.getLogger("clv_weight_search")

_EPS = 1e-9

# ── Weight configurations to evaluate ────────────────────────────────────────

CONFIGS: list[dict] = [
    {"name": "pure_penaltyblog",  "market_weight": 0.00,
     "description": "0% market — fully independent prior (CLV-optimal by theory)"},
    {"name": "market_20",         "market_weight": 0.20,
     "description": "20% market — light signal"},
    {"name": "market_30",         "market_weight": 0.30,
     "description": "30% market — moderate signal"},
    {"name": "market_50",         "market_weight": 0.50,
     "description": "50% market — balanced"},
    {"name": "market_60_default", "market_weight": 0.60,
     "description": "60% market — previous code default"},
]

# ── Paths ─────────────────────────────────────────────────────────────────────

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
PROCESSED_DIR = DATA_DIR / "processed" / "v1"
CLV_RECORDS_PATH = DATA_DIR / "clv" / "2026" / "records.jsonl"
OUT_CSV = DATA_DIR / "clv_weight_search_results.csv"


# ── Helpers ───────────────────────────────────────────────────────────────────

def _am2dec(american: float) -> float:
    if american >= 100:
        return american / 100.0 + 1.0
    return 100.0 / abs(american) + 1.0


def _score_pmf(lam_h: float, lam_a: float, max_goals: int = 10) -> np.ndarray:
    """Independent Poisson PMF grid."""
    pmf = np.outer(
        scipy_poisson.pmf(range(max_goals), lam_h),
        scipy_poisson.pmf(range(max_goals), lam_a),
    )
    pmf = np.clip(pmf, 0, None)
    return pmf / pmf.sum()


def _pmf_to_1x2(pmf: np.ndarray) -> tuple[float, float, float]:
    n = pmf.shape[0]
    hw = sum(pmf[h, a] for h in range(n) for a in range(n) if h > a)
    dr = sum(pmf[h, a] for h in range(n) for a in range(n) if h == a)
    aw = sum(pmf[h, a] for h in range(n) for a in range(n) if h < a)
    return float(hw), float(dr), float(aw)


def _rps_1x2(pred: tuple[float, float, float], actual: str) -> float:
    """Ranked Probability Score for 1X2."""
    p = list(pred)  # [hw, dr, aw]
    outcomes = {"home_win": [1, 0, 0], "draw": [0, 1, 0], "away_win": [0, 0, 1]}
    o = outcomes[actual]
    cp = [sum(p[:i+1]) for i in range(3)]
    co = [sum(o[:i+1]) for i in range(3)]
    return float(sum((cp[i] - co[i]) ** 2 for i in range(3)) / 2)


def _load_clv_records() -> list[dict]:
    if not CLV_RECORDS_PATH.exists():
        return []
    records = []
    with open(CLV_RECORDS_PATH) as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    return records


def _market_no_vig_1x2(odds_rows: pd.DataFrame) -> tuple[float, float, float] | None:
    """Average no-vig 1X2 from bookmaker moneyline rows."""
    hw_list, dr_list, aw_list = [], [], []
    for _, row in odds_rows.iterrows():
        try:
            hw_a = float(row["moneyline_home"])
            dr_a = float(row["moneyline_draw"])
            aw_a = float(row["moneyline_away"])
            p_hw = 1.0 / _am2dec(hw_a)
            p_dr = 1.0 / _am2dec(dr_a)
            p_aw = 1.0 / _am2dec(aw_a)
            tot = p_hw + p_dr + p_aw
            if tot < 0.5:
                continue
            hw_list.append(p_hw / tot)
            dr_list.append(p_dr / tot)
            aw_list.append(p_aw / tot)
        except Exception:
            continue
    if not hw_list:
        return None
    return float(np.mean(hw_list)), float(np.mean(dr_list)), float(np.mean(aw_list))


# ── Core evaluation ───────────────────────────────────────────────────────────

def evaluate_config(
    config: dict,
    matches_df: pd.DataFrame,
    odds_df: pd.DataFrame,
    completed_2026: pd.DataFrame,
) -> dict:
    """
    Evaluate a single weight configuration on all completed 2026 matches.

    Returns a dict of metrics.
    """
    from wc2026.ratings.composite import CompositeTeamPrior

    prior = CompositeTeamPrior(market_weight=config["market_weight"])
    prior.fit(matches_df, odds_df)

    log_losses = []
    exact_lls = []
    rps_scores = []
    divergences = []

    for _, mrow in completed_2026.iterrows():
        home = str(mrow["home_team"])
        away = str(mrow["away_team"])
        actual_h = int(mrow["home_goals"])
        actual_a = int(mrow["away_goals"])
        actual_outcome = (
            "home_win" if actual_h > actual_a else
            "draw" if actual_h == actual_a else
            "away_win"
        )

        hp = prior.get_prior(home)
        ap = prior.get_prior(away)

        # Multiplicative Poisson model (same as predict_match_from_composite)
        WC_AVG = 1.30
        lam_h = float(np.clip(hp.final_attack_lambda * ap.final_defense_lambda / WC_AVG, 0.3, 5.0))
        lam_a = float(np.clip(ap.final_attack_lambda * hp.final_defense_lambda / WC_AVG, 0.3, 5.0))

        pmf = _score_pmf(lam_h, lam_a)
        p_hw, p_dr, p_aw = _pmf_to_1x2(pmf)

        p_outcome = {"home_win": p_hw, "draw": p_dr, "away_win": p_aw}[actual_outcome]
        p_exact = float(pmf[min(actual_h, pmf.shape[0]-1), min(actual_a, pmf.shape[1]-1)])

        log_losses.append(-math.log(max(p_outcome, _EPS)))
        exact_lls.append(-math.log(max(p_exact, _EPS)))
        rps_scores.append(_rps_1x2((p_hw, p_dr, p_aw), actual_outcome))

        # Model vs market divergence
        match_odds = odds_df[odds_df["match_id"] == mrow["match_id"]]
        mkt = _market_no_vig_1x2(match_odds)
        if mkt is not None:
            div = (abs(p_hw - mkt[0]) + abs(p_dr - mkt[1]) + abs(p_aw - mkt[2])) / 3.0
            divergences.append(div)

    result = {
        "config": config["name"],
        "market_weight": config["market_weight"],
        "description": config["description"],
        "n_matches": len(log_losses),
        "mean_log_loss": round(float(np.mean(log_losses)), 4) if log_losses else None,
        "mean_exact_ll": round(float(np.mean(exact_lls)), 4) if exact_lls else None,
        "rps_1x2": round(float(np.mean(rps_scores)), 4) if rps_scores else None,
        "model_mkt_diverge": round(float(np.mean(divergences)), 4) if divergences else None,
    }
    return result


def evaluate_clv_records(configs: list[dict]) -> dict[str, dict]:
    """
    Extract CLV bits from stored records (model-independent — same for all configs
    since they were computed from model_prob at prediction time).
    Returns {config_name: {"mean_clv_bits": ..., "beat_close_rate": ...}}
    """
    records = _load_clv_records()
    clv_recs = [r for r in records if r.get("clv_bits") is not None]

    if not clv_recs:
        return {}

    mean_bits = round(float(np.mean([r["clv_bits"] for r in clv_recs])), 4)
    beat_close = sum(1 for r in clv_recs if r.get("clv_bits", -1) > 0)
    beat_close_rate = round(beat_close / len(clv_recs), 4) if clv_recs else None

    # CLV records are from the current (pre-change) model predictions, so they
    # apply to the prediction_mode used at the time. They are NOT per-weight-config.
    # We report them once as the current-model baseline.
    return {
        "n_with_clv": len(clv_recs),
        "mean_clv_bits": mean_bits,
        "beat_close_rate": beat_close_rate,
    }


# ── Walk-forward baseline (NLL) ───────────────────────────────────────────────

def run_walkforward_baseline(matches_df: pd.DataFrame) -> dict | None:
    """
    Run WalkForwardEngine on 2018+2022 historical data to establish the baseline
    NLL/RPS for the pure penaltyblog models (independent of market weight).
    Returns metrics dict for the best model, or None if not enough data.
    """
    try:
        from wc2026.backtest.walkforward import WalkForwardEngine
    except ImportError:
        return None

    hist = matches_df[
        (matches_df["status"] == "completed") &
        matches_df["home_goals"].notna() &
        matches_df["away_goals"].notna() &
        matches_df["season"].isin([2018, 2022])
    ].copy()

    if len(hist) < 20:
        return None

    engine = WalkForwardEngine(
        hist,
        models=["dixon_coles"],
        include_baselines=False,
        min_train_matches=10,
        refit_every=5,
        include_bayesian=False,
    )
    results = engine.run(save=False)
    if not results:
        return None

    r = results[0]
    return {
        "model": r.model_name,
        "n_predictions": r.n_predictions,
        "rps_1x2": round(r.metrics.rps_1x2, 4),
        "brier_1x2": round(r.metrics.brier_1x2, 4),
        "exact_score_nll": round(r.metrics.exact_score_log_loss, 4),
    }


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="CLV weight grid search")
    parser.add_argument("--save", action="store_true", default=True,
                        help="Save results CSV (default: True)")
    parser.add_argument("--no-save", dest="save", action="store_false")
    parser.add_argument("--skip-walkforward", action="store_true",
                        help="Skip the 2018/2022 walk-forward baseline (faster)")
    args = parser.parse_args()

    print("=" * 70)
    print("CLV WEIGHT GRID SEARCH  —  World Cup 2026 Model")
    print("Run date: 2026-06-12  |  Branch: feature/clv-weight-optimization")
    print("=" * 70)

    # ── Load data ────────────────────────────────────────────────────────────
    matches_path = PROCESSED_DIR / "matches.parquet"
    odds_path = PROCESSED_DIR / "odds.parquet"

    if not matches_path.exists():
        print(f"\nERROR: {matches_path} not found. Run 'make build-dataset' first.")
        sys.exit(1)

    matches_df = pd.read_parquet(matches_path)
    odds_df = pd.read_parquet(odds_path) if odds_path.exists() else pd.DataFrame()

    completed_2026 = matches_df[
        (matches_df["season"] == 2026) &
        (matches_df["status"] == "completed") &
        matches_df["home_goals"].notna() &
        matches_df["away_goals"].notna()
    ].copy()

    print(f"\nData loaded:")
    print(f"  Total matches: {len(matches_df)}")
    print(f"  Completed 2026 matches: {len(completed_2026)}")
    print(f"  Odds rows available: {len(odds_df)}")

    if len(completed_2026) == 0:
        print("\nWARNING: No completed 2026 matches. Cannot evaluate configs on actual results.")
        print("Results will show model-market divergence only.")

    # ── Walk-forward baseline ────────────────────────────────────────────────
    if not args.skip_walkforward:
        print("\n" + "-" * 70)
        print("Walk-forward baseline (2018+2022, dixon_coles — independent of market weight):")
        wf = run_walkforward_baseline(matches_df)
        if wf:
            print(f"  Model        : {wf['model']}")
            print(f"  N predictions: {wf['n_predictions']}")
            print(f"  RPS (1X2)    : {wf['rps_1x2']}")
            print(f"  Brier (1X2)  : {wf['brier_1x2']}")
            print(f"  Exact NLL    : {wf['exact_score_nll']}")
            print("  (These metrics do not change with market_weight — the WalkForward")
            print("   uses ModelLadder fitted directly on historical data, not the prior.)")
        else:
            print("  Walk-forward baseline skipped (not enough historical data or import error).")

    # ── CLV record summary ───────────────────────────────────────────────────
    print("\n" + "-" * 70)
    print("Current CLV record summary (from data/clv/2026/records.jsonl):")
    clv_info = evaluate_clv_records(CONFIGS)
    if clv_info:
        print(f"  N records with CLV : {clv_info['n_with_clv']}")
        print(f"  Mean CLV bits      : {clv_info['mean_clv_bits']:+.4f}")
        print(f"  Beat-close rate    : {clv_info['beat_close_rate']:.1%}")
        print("  (CLV bits are computed at prediction time from the then-current model;")
        print("   they reflect the market_reconciled mode, not the raw prior.)")
    else:
        print("  No CLV records with closing line found.")

    # ── Per-config evaluation ────────────────────────────────────────────────
    print("\n" + "-" * 70)
    print("Per-config evaluation on completed 2026 matches:\n")

    rows = []
    for cfg in CONFIGS:
        r = evaluate_config(cfg, matches_df, odds_df, completed_2026)
        rows.append(r)

    if rows:
        df_results = pd.DataFrame(rows)

        # Pretty-print table
        print(f"{'Config':<24} {'MW':>5}  {'N':>3}  {'LogLoss':>8}  {'ExactLL':>8}  "
              f"{'RPS':>7}  {'MktDiv':>7}")
        print("-" * 72)
        for _, row in df_results.iterrows():
            ll = f"{row['mean_log_loss']:.4f}" if row['mean_log_loss'] is not None else "  —  "
            el = f"{row['mean_exact_ll']:.4f}" if row['mean_exact_ll'] is not None else "  —  "
            rp = f"{row['rps_1x2']:.4f}" if row['rps_1x2'] is not None else "  —  "
            md = f"{row['model_mkt_diverge']:.4f}" if row['model_mkt_diverge'] is not None else "  —  "
            print(f"{row['config']:<24} {row['market_weight']:>5.2f}  "
                  f"{row['n_matches']:>3}  {ll:>8}  {el:>8}  {rp:>7}  {md:>7}")

        print()

        # ── Winner selection ─────────────────────────────────────────────────
        valid = df_results[df_results["mean_log_loss"].notna()].copy()

        if len(valid) == 0 or len(completed_2026) < 5:
            winner_name = "pure_penaltyblog"
            winner_mw = 0.0
            reason = (
                f"INCONCLUSIVE: only {len(completed_2026)} completed match(es) — "
                "too few for reliable statistical comparison. "
                "Defaulting to 0% market weight (pure penaltyblog) as the "
                "theoretically correct choice for maximising CLV independence."
            )
        else:
            best_idx = valid["mean_log_loss"].idxmin()
            winner_name = valid.loc[best_idx, "config"]
            winner_mw = valid.loc[best_idx, "market_weight"]

            # Check if difference from pure_penaltyblog is meaningful (>0.01 nll units)
            pure_ll = valid[valid["config"] == "pure_penaltyblog"]["mean_log_loss"].values
            best_ll = valid.loc[best_idx, "mean_log_loss"]
            threshold = 0.01

            if len(pure_ll) > 0 and (pure_ll[0] - best_ll) < threshold:
                winner_name = "pure_penaltyblog"
                winner_mw = 0.0
                reason = (
                    f"INCONCLUSIVE: best config ({valid.loc[best_idx,'config']}, "
                    f"LL={best_ll:.4f}) is within {threshold:.3f} NLL of pure_penaltyblog "
                    f"(LL={pure_ll[0]:.4f}). Defaulting to 0% market weight."
                )
            else:
                reason = (
                    f"WINNER: {winner_name} (market_weight={winner_mw:.2f}) "
                    f"with mean_log_loss={best_ll:.4f}"
                )

        print("=" * 70)
        print("RECOMMENDATION")
        print("=" * 70)
        print(f"\n  Optimal market_weight: {winner_mw:.2f}  ({winner_name})")
        print(f"\n  Rationale: {reason}")
        print()
        print("  NOTE: With fewer than 5 matches completed, these results are")
        print("  directional only. Re-run this script after more group-stage")
        print("  matches complete (target: 2026-06-13 or 2026-06-14) to get a")
        print("  more reliable assessment.")
        print("=" * 70)

        # ── Save CSV ─────────────────────────────────────────────────────────
        if args.save:
            df_results["run_date"] = "2026-06-12"
            df_results["n_completed_matches"] = len(completed_2026)
            df_results["winner"] = winner_name
            df_results["recommended_weight"] = winner_mw
            OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
            df_results.to_csv(OUT_CSV, index=False)
            print(f"\nResults saved → {OUT_CSV}")

        return winner_mw

    return 0.0


if __name__ == "__main__":
    main()
