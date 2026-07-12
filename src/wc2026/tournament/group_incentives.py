"""Group stage incentive adjustment at the PMF level.

NOTE: 2026 WC FORMAT — 12 groups of 4 teams.
  Top 2 from each group advance automatically (24 teams).
  Best 8 of 12 third-place teams also advance (8 teams).
  Total 32 teams enter the knockout bracket.

This module applies a heuristic rho/lambda adjustment based on group
incentive state. The adjustment is suppressed in PRESENTATION_SAFE_MODE
because the constants are not validated from historical evidence.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass

import numpy as np
import pandas as pd

log = logging.getLogger(__name__)

_DRAW_UTILITY_THRESHOLD = 0.15  # Net marginal value of draw vs win above which we adjust PMF
_RHO_DRAW_BOOST = 0.04           # How much to increase |rho| when draw incentive is high
_INTENSITY_REDUCTION = 0.95      # Multiply lambdas by this when rotation likely


@dataclass
class GroupIncentiveState:
    team: str
    p_qualify_if_win: float = 1.0
    p_qualify_if_draw: float = 0.5
    p_qualify_if_loss: float = 0.0
    p_win_group_if_win: float = 0.5
    p_win_group_if_draw: float = 0.1
    p_advance_as_third_if_draw: float = 0.3
    marginal_gd_value: float = 0.0
    already_qualified_prob: float = 0.0
    already_eliminated_prob: float = 0.0
    rotation_proxy: float = 0.0
    draw_utility: float = 0.0


def compute_group_incentives(
    team: str,
    group_standings: pd.DataFrame,
    remaining_fixtures: list,
    pmf_cache: dict | None = None,
) -> GroupIncentiveState:
    """Compute group incentive state for a team given current standings."""
    state = GroupIncentiveState(team=team)
    if group_standings is None or group_standings.empty:
        return state

    try:
        # Find team row
        team_rows = group_standings[group_standings["team"].str.lower() == team.lower()]
        if team_rows.empty:
            return state

        row = team_rows.iloc[0]
        pts = int(row.get("points", 0))
        int(row.get("played", 0))
        remaining_games = len([f for f in remaining_fixtures if team.lower() in [str(t).lower() for t in f]])

        # Simple heuristics for incentive state
        max_pts = pts + remaining_games * 3
        state.already_qualified_prob = 1.0 if pts >= 7 else (0.8 if pts >= 6 else 0.0)
        state.already_eliminated_prob = 1.0 if max_pts < 1 else 0.0
        state.rotation_proxy = min(state.already_qualified_prob * 0.6, 0.5)

        # Marginal value of a draw vs a win
        if pts <= 3 and remaining_games > 0:
            state.p_qualify_if_win = 0.85
            state.p_qualify_if_draw = 0.45
            state.p_qualify_if_loss = 0.15
            state.draw_utility = state.p_qualify_if_draw - state.p_qualify_if_loss
        elif pts >= 4:
            state.p_qualify_if_win = 0.98
            state.p_qualify_if_draw = 0.80
            state.p_qualify_if_loss = 0.40
            state.draw_utility = 0.0  # Already fairly safe

        # If already qualified, draw utility is near zero but rotation may reduce goals
        if state.already_qualified_prob > 0.8:
            state.draw_utility = -0.05  # Slight preference to win group

    except Exception as e:
        log.debug("compute_group_incentives failed for %s: %s", team, e)

    return state


def adjust_pmf_for_group_incentives(
    pmf: np.ndarray,
    home_state: GroupIncentiveState,
    away_state: GroupIncentiveState,
    rho: float,
    lh: float,
    la: float,
) -> tuple[np.ndarray, float, float, float]:
    """
    Adjust PMF for group stage incentives at the distribution level.
    Returns (adjusted_pmf, adjusted_lh, adjusted_la, adjusted_rho).

    Suppressed when PRESENTATION_SAFE_MODE or SUPPRESS_DRAW_BOOST is active,
    because the adjustment constants are not validated from historical evidence.
    """
    try:
        from wc2026.config import PRESENTATION_SAFE_MODE, SUPPRESS_DRAW_BOOST
        if PRESENTATION_SAFE_MODE or SUPPRESS_DRAW_BOOST:
            return pmf, lh, la, rho
    except ImportError:
        pass
    try:
        from penaltyblog.models import create_dixon_coles_grid
    except ImportError:
        return pmf, lh, la, rho

    adj_lh, adj_la, adj_rho = lh, la, rho

    # Both teams have high draw utility → increase rho (more draw correlation)
    combined_draw_utility = (home_state.draw_utility + away_state.draw_utility) / 2.0
    if combined_draw_utility > _DRAW_UTILITY_THRESHOLD:
        rho_adjustment = min(_RHO_DRAW_BOOST, 0.08)
        adj_rho = max(rho - rho_adjustment, -0.35)
        log.debug("Group incentive: increasing draw correlation, rho %s → %s", rho, adj_rho)

    # Rotation proxy reduces goal intensity
    combined_rotation = (home_state.rotation_proxy + away_state.rotation_proxy) / 2.0
    if combined_rotation > 0.3:
        intensity_mult = max(1.0 - combined_rotation * 0.15, _INTENSITY_REDUCTION)
        adj_lh = lh * intensity_mult
        adj_la = la * intensity_mult
        log.debug("Group incentive: rotation adjustment, lh %s → %s", lh, adj_lh)

    if adj_rho == rho and adj_lh == lh and adj_la == la:
        return pmf, lh, la, rho

    try:
        grid = create_dixon_coles_grid(adj_lh, adj_la, rho=adj_rho, max_goals=pmf.shape[0] - 1)
        adj_pmf = np.array(grid.grid, dtype=np.float64)
        adj_pmf = adj_pmf / adj_pmf.sum()
        return adj_pmf, adj_lh, adj_la, adj_rho
    except Exception as e:
        log.warning("Group incentive PMF adjustment failed: %s", e)
        return pmf, lh, la, rho
