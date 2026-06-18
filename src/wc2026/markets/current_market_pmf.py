"""Current market PMF: build joint score PMF from BDL odds snapshot."""
from __future__ import annotations
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

import numpy as np
import pandas as pd

log = logging.getLogger(__name__)


@dataclass
class CurrentMarketPMF:
    pmf: np.ndarray
    home_lambda: float
    away_lambda: float
    rho: float
    dispersion_proxy: Optional[float]
    reconstruction_error: dict
    vendor_count: int
    market_quality: float
    staleness_flags: dict
    overround: dict
    de_vig_method: str
    observed_at: Optional[datetime]
    odds_as_of: Optional[datetime]
    implementation: str = "simple"  # "simple" or "full"


def _american_to_decimal(american: int) -> float:
    if american > 0:
        return american / 100.0 + 1.0
    else:
        return 100.0 / abs(american) + 1.0


def _shin_devig(probs: list[float]) -> list[float]:
    """Simple Shin iterative de-vig."""
    try:
        from penaltyblog.implied import calculate_implied
        odds_decimal = [1.0 / p if p > 0 else 999.0 for p in probs]
        result = calculate_implied(odds_decimal, method="shin")
        return list(result["implied_probabilities"])
    except Exception:
        # Fallback: proportional normalization
        total = sum(probs)
        return [p / total for p in probs] if total > 0 else probs


def build_market_pmf_simple(snapshot_df: pd.DataFrame) -> Optional[CurrentMarketPMF]:
    """Build PMF from 1X2 + O/U 2.5 only (Shin de-vig, goal_expectancy_extended)."""
    if snapshot_df is None or snapshot_df.empty:
        return None

    try:
        from penaltyblog.models import goal_expectancy_extended, create_dixon_coles_grid
    except ImportError:
        log.error("penaltyblog not available")
        return None

    # Filter to moneyline rows
    ml_rows = snapshot_df[snapshot_df["market_type"] == "moneyline"].copy() if "market_type" in snapshot_df.columns else pd.DataFrame()

    # Try to extract from top-level moneyline odds columns if market_type not set
    if ml_rows.empty and "moneyline_home_odds" in snapshot_df.columns:
        ml_rows = snapshot_df.dropna(subset=["moneyline_home_odds", "moneyline_draw_odds", "moneyline_away_odds"])

    if ml_rows.empty:
        return None

    vendors = ml_rows["vendor"].unique() if "vendor" in ml_rows.columns else ["unknown"]
    lambdas_h, lambdas_a, rhos = [], [], []
    overrounds = {}

    for vendor in vendors:
        vrows = ml_rows[ml_rows["vendor"] == vendor] if "vendor" in ml_rows.columns else ml_rows
        if vrows.empty:
            continue
        row = vrows.iloc[0]
        try:
            if "moneyline_home_odds" in row and pd.notna(row.get("moneyline_home_odds")):
                ho = _american_to_decimal(int(row["moneyline_home_odds"]))
                dr = _american_to_decimal(int(row["moneyline_draw_odds"]))
                aw = _american_to_decimal(int(row["moneyline_away_odds"]))
            elif "decimal_odds" in vrows.columns:
                outcomes = vrows.groupby("outcome")["decimal_odds"].mean()
                if not {"home", "draw", "away"}.issubset(set(outcomes.index)):
                    continue
                ho, dr, aw = outcomes["home"], outcomes["draw"], outcomes["away"]
            else:
                continue

            raw_probs = [1/ho, 1/dr, 1/aw]
            overround = sum(raw_probs) - 1.0
            overrounds[vendor] = {"moneyline": overround}
            hw, dw, aw_p = _shin_devig(raw_probs)

            # Try O/U 2.5
            over25 = under25 = None
            if "total_value" in row and str(row.get("total_value", "")) == "2.5":
                if pd.notna(row.get("total_over_odds")):
                    o_dec = _american_to_decimal(int(row["total_over_odds"]))
                    u_dec = _american_to_decimal(int(row["total_under_odds"]))
                    o_p, u_p = _shin_devig([1/o_dec, 1/u_dec])
                    over25, under25 = o_p, u_p

            try:
                if over25 is not None:
                    res = goal_expectancy_extended(hw, dw, aw_p, over25, under25)
                    if isinstance(res, dict):
                        lh = float(res.get("home_exp", res.get("x", [1.3])[0]))
                        la = float(res.get("away_exp", res.get("x", [1.0, 1.0])[1]))
                        rho = float(res.get("implied_rho", -0.05) or -0.05)
                    else:
                        # scipy OptimizeResult
                        lh, la = float(res.x[0]), float(res.x[1])
                        rho = float(res.x[2]) if len(res.x) > 2 else -0.05
                else:
                    from penaltyblog.models import goal_expectancy
                    res = goal_expectancy(hw, dw, aw_p)
                    if isinstance(res, dict):
                        lh = float(res.get("home_exp", 1.3))
                        la = float(res.get("away_exp", 1.0))
                    else:
                        lh = float(res.x[0])
                        la = float(res.x[1])
                    rho = -0.05
                lambdas_h.append(lh)
                lambdas_a.append(la)
                rhos.append(rho)
            except Exception as e:
                log.debug("goal_expectancy failed for vendor %s: %s", vendor, e)
        except Exception as e:
            log.debug("Vendor %s processing failed: %s", vendor, e)

    if not lambdas_h:
        return None

    avg_lh = float(np.mean(lambdas_h))
    avg_la = float(np.mean(lambdas_a))
    avg_rho = float(np.mean(rhos))

    try:
        grid = create_dixon_coles_grid(avg_lh, avg_la, rho=avg_rho, max_goals=14)
        pmf = np.array(grid.grid, dtype=np.float64)
        pmf = pmf / pmf.sum()
    except Exception:
        from scipy.stats import poisson
        pmf = np.zeros((15, 15))
        for h in range(15):
            for a in range(15):
                pmf[h, a] = poisson.pmf(h, avg_lh) * poisson.pmf(a, avg_la)
        pmf = pmf / pmf.sum()

    observed_at = None
    if "observed_at" in snapshot_df.columns:
        try:
            observed_at = pd.to_datetime(snapshot_df["observed_at"]).max()
            if hasattr(observed_at, 'to_pydatetime'):
                observed_at = observed_at.to_pydatetime()
        except Exception:
            pass

    return CurrentMarketPMF(
        pmf=pmf, home_lambda=avg_lh, away_lambda=avg_la, rho=avg_rho,
        dispersion_proxy=None, reconstruction_error={}, vendor_count=len(lambdas_h),
        market_quality=min(len(lambdas_h) / 6.0, 1.0),
        staleness_flags={}, overround=overrounds, de_vig_method="shin",
        observed_at=observed_at, odds_as_of=observed_at, implementation="simple",
    )


def build_market_pmf_full(snapshot_df: pd.DataFrame) -> Optional[CurrentMarketPMF]:
    """Full market surface PMF fit using SLSQP. Falls back to simple on failure."""
    if snapshot_df is None or snapshot_df.empty:
        return build_market_pmf_simple(snapshot_df)

    try:
        simple = build_market_pmf_simple(snapshot_df)
        if simple is None:
            return None

        # Check if spread/AH odds available
        has_spread = False
        if "market_type" in snapshot_df.columns:
            spread_rows = snapshot_df[snapshot_df["market_type"].isin(["spread", "asian_handicap"])]
            has_spread = len(spread_rows) > 0
        elif "spread_home_value" in snapshot_df.columns:
            has_spread = snapshot_df["spread_home_value"].notna().any()

        if not has_spread:
            # No spread data — simple is sufficient
            simple.implementation = "simple_no_spread"
            return simple

        from scipy.optimize import minimize
        from wc2026.markets.canonical_grid import CanonicalGrid

        # Build initial PMF from simple, then optimize to fit spread constraints
        init_pmf = simple.pmf.flatten()
        n = len(init_pmf)

        def kl_loss(pmf_flat):
            pmf_flat = np.abs(pmf_flat)
            pmf_sum = pmf_flat.sum()
            if pmf_sum < 1e-12:
                return 1e9
            pmf_flat = pmf_flat / pmf_sum
            pmf_2d = pmf_flat.reshape(simple.pmf.shape)
            grid = CanonicalGrid(pmf_2d)
            loss = 0.0
            # Add spread constraint terms (minimize distance to implied spread probability)
            if has_spread and "spread_home_value" in snapshot_df.columns:
                spread_rows = snapshot_df.dropna(subset=["spread_home_value", "spread_home_odds"])
                for _, srow in spread_rows.iterrows():
                    try:
                        line = float(srow["spread_home_value"])
                        h_dec = _american_to_decimal(int(srow["spread_home_odds"]))
                        a_dec = _american_to_decimal(int(srow["spread_away_odds"]))
                        mkt_h, mkt_a = _shin_devig([1/h_dec, 1/a_dec])
                        ah = grid.asian_handicap([line])
                        from wc2026.markets.canonical_grid import _fmt_ah_line
                        key = f"asian_handicap_home_{_fmt_ah_line(line)}"
                        if key in ah:
                            loss += (ah[key] - mkt_h) ** 2 * 10.0
                    except Exception:
                        pass
            return loss

        constraints = [{"type": "eq", "fun": lambda x: np.abs(x).sum() - 1.0}]
        bounds = [(0, None)] * n
        result = minimize(kl_loss, init_pmf, method="SLSQP", bounds=bounds, constraints=constraints,
                         options={"maxiter": 100, "ftol": 1e-6})

        if result.success:
            pmf_opt = np.abs(result.x).reshape(simple.pmf.shape)
            pmf_opt = pmf_opt / pmf_opt.sum()
            simple.pmf = pmf_opt
            simple.implementation = "full"
            simple.reconstruction_error["spread_residual"] = float(result.fun)
        else:
            log.warning("Full market PMF optimization failed: %s — using simple fallback", result.message)
            simple.implementation = "simple_fallback"

        return simple

    except Exception as e:
        log.warning("build_market_pmf_full failed: %s — using simple fallback", e)
        return build_market_pmf_simple(snapshot_df)
