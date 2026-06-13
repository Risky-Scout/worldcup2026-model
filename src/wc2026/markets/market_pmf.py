"""
Market-implied PMF construction using penaltyblog.models.goal_expectancy_extended.

Flow
----
1. Strip vig from BDL 1X2 odds (penaltyblog.implied, 7 methods)
2. Strip vig from BDL totals odds (over/under 2.5)
3. Call penaltyblog.models.goal_expectancy_extended(1X2 + totals) to infer (mu_h, mu_a, rho)
4. Call create_dixon_coles_grid(mu_h, mu_a, rho) → FootballProbabilityGrid
5. Wrap in FiniteGridPMF → same type as all model PMFs

This is the "gold standard" market-implied PMF because:
- goal_expectancy_extended simultaneously fits 1X2 + O/U → better rho estimate
- The result satisfies the same invariants as any model PMF
- No separate market object; market PMF is just another JointScorePMF
"""
from __future__ import annotations

import logging
from typing import Optional

import numpy as np
from penaltyblog.models import create_dixon_coles_grid, goal_expectancy_extended

from wc2026.config import PMF_MAX_GOALS
from wc2026.markets.consensus import ConsensusMarkets
from wc2026.markets.no_vig import strip_vig_1x2, strip_vig_total
from wc2026.models.joint_pmf import FiniteGridPMF

log = logging.getLogger(__name__)
_EPS = 1e-9


def build_market_pmf(
    markets: ConsensusMarkets,
    max_goals: int = PMF_MAX_GOALS,
    method: str = "multiplicative",
) -> Optional[FiniteGridPMF]:
    """
    Build a market-implied PMF from BDL consensus market probabilities.

    Uses penaltyblog.models.goal_expectancy_extended to solve for
    (lambda_home, lambda_away, rho) simultaneously from 1X2 + over2.5.

    Returns None if no valid market data is available.

    Parameters
    ----------
    markets : ConsensusMarkets
        Output from markets.consensus.build_consensus()
    max_goals : int
        Grid size for the returned PMF.
    method : str
        No-vig method used (for metadata only).
    """
    if not markets.has_1x2:
        log.debug("No 1X2 market data for match %s", markets.match_id)
        return None

    hw = markets.home_win
    dr = markets.draw
    aw = markets.away_win

    # Get over/under 2.5 if available
    over25: Optional[float] = None
    under25: Optional[float] = None
    for line_str in ["2.5", "2.0"]:
        if line_str in markets.totals:
            over25, under25 = markets.totals[line_str]
            break

    try:
        if over25 is not None and under25 is not None:
            result = goal_expectancy_extended(
                hw, dr, aw, over25, under25,
                remove_overround=True,
                max_goals=max_goals,
                objective="cross_entropy",
            )
            mu_h = result["home_exp"]
            mu_a = result["away_exp"]
            rho = result.get("implied_rho", 0.0)
            log.debug(
                "Market PMF (match %s): mu_h=%.3f mu_a=%.3f rho=%.3f success=%s",
                markets.match_id, mu_h, mu_a, rho, result["success"],
            )
        else:
            from penaltyblog.models import goal_expectancy
            result = goal_expectancy(hw, dr, aw, dc_adj=True, remove_overround=True,
                                     max_goals=max_goals, objective="cross_entropy")
            mu_h = result["home_exp"]
            mu_a = result["away_exp"]
            rho = 0.0

        # Clamp rho to valid bounds
        rho_min = max(-1.0 / mu_h, -1.0 / mu_a)
        rho_max = min(1.0, 1.0 / (mu_h * mu_a))
        rho = float(np.clip(rho, rho_min + _EPS, rho_max - _EPS))

        fpg = create_dixon_coles_grid(
            max(mu_h, 0.1), max(mu_a, 0.1),
            rho=rho,
            max_goals=max_goals - 1,
        )
        pmf = FiniteGridPMF(
            fpg,
            model_name=f"market_implied[{method},n={markets.n_vendors_1x2}]",
            rho=rho,
            published_max_goals=max_goals,
        )
        log.info(
            "Built market PMF for match %s: hw=%.3f dr=%.3f aw=%.3f mu_h=%.3f mu_a=%.3f",
            markets.match_id, hw, dr, aw, mu_h, mu_a,
        )
        return pmf

    except Exception as exc:
        log.warning("Failed to build market PMF for match %s: %s", markets.match_id, exc)
        return None
