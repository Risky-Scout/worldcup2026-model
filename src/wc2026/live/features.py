"""
LiveFeatureVector — feature extraction for the live PMF model.

Features are derived from a MatchState and the pregame PMF.

Design
------
- All features are computed without future leakage.
- Missing stats produce imputed values with a missingness flag.
- Features are continuous scalars suitable for a linear hazard model.

Feature groups
--------------
Clock features
    regulation_minute, fraction_elapsed, remaining_fraction
    is_first_half, is_second_half, is_stoppage

Score-state features
    home_goals, away_goals, goal_diff, n_goals_scored
    is_drawn, is_home_winning_1, is_home_winning_2plus
    is_away_winning_1, is_away_winning_2plus

Strength features (from pregame)
    pregame_lh, pregame_la, pregame_home_win_prob
    pregame_over_2_5

Performance features (from live stats)
    home_xg_rate       xG per 90 min (from cumulative xG)
    away_xg_rate
    home_shots_rate    shots on target per 90 min
    away_shots_rate
    home_xg_momentum   recent xG accumulation rate (last 15 min proxy)
    away_xg_momentum
    xg_ratio           home_xg / (home_xg + away_xg + eps)
    possession_ratio   home possession / 100
    home_big_chances_rate
    away_big_chances_rate

Card/player features
    home_red_cards, away_red_cards
    home_player_disadvantage  (11 - home_effective_players)
    away_player_disadvantage

Missingness flags (0/1)
    xg_missing, shots_missing, possession_missing
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Optional

from .state import MatchState, TeamLiveStats

_EPS = 1e-6


@dataclass
class LiveFeatureVector:
    """
    Feature vector for the live hazard model.

    All values are floats; missing data is imputed and flagged.
    """
    # Clock
    regulation_minute: float        # 0 – 90
    fraction_elapsed: float         # 0 – 1
    remaining_fraction: float       # 1 – 0
    remaining_seconds: float
    is_first_half: float
    is_second_half: float
    is_stoppage: float              # 1 if in added time

    # Score state
    home_goals: float
    away_goals: float
    goal_diff: float                # home - away
    n_goals_scored: float
    is_drawn: float
    is_home_winning_1: float
    is_home_winning_2plus: float
    is_away_winning_1: float
    is_away_winning_2plus: float

    # Pregame strength
    pregame_lh: float               # pregame expected home goals
    pregame_la: float               # pregame expected away goals
    pregame_home_win_prob: float
    pregame_over_2_5: float         # pregame P(total > 2.5)

    # Live performance
    home_xg_rate: float             # xG per 90 min
    away_xg_rate: float
    home_shots_rate: float          # shots on target per 90 min
    away_shots_rate: float
    xg_ratio: float                 # home_xg / total_xg
    possession_ratio: float         # home possession / 100
    home_big_chances_rate: float
    away_big_chances_rate: float

    # Cards / players
    home_red_cards: float
    away_red_cards: float
    home_player_disadvantage: float  # 11 - effective
    away_player_disadvantage: float

    # Missingness flags
    xg_missing: float
    shots_missing: float
    possession_missing: float

    def to_dict(self) -> dict:
        return {k: round(float(v), 6) for k, v in self.__dict__.items()}


def extract_features(
    state: MatchState,
    pregame_lh: Optional[float] = None,
    pregame_la: Optional[float] = None,
    pregame_home_win: Optional[float] = None,
) -> LiveFeatureVector:
    """
    Extract a LiveFeatureVector from a MatchState.

    Parameters
    ----------
    state           Current match state
    pregame_lh      Pregame expected home goals (overrides state.pregame_lh)
    pregame_la      Pregame expected away goals
    pregame_home_win  Pregame home win probability
    """
    lh = pregame_lh or state.pregame_lh or 1.35
    la = pregame_la or state.pregame_la or 1.00
    hw = pregame_home_win or state.pregame_home_win_prob or 0.45

    # ── Clock features ────────────────────────────────────────────────────
    minute = float(state.regulation_minute)
    elapsed = min(minute / 90.0, 1.0)
    remaining = state.remaining_regulation_seconds
    remaining_frac = max(0.0, remaining / (90 * 60))
    is_fh = 1.0 if minute < 45.0 else 0.0
    is_sh = 1.0 if 45.0 <= minute < 90.0 else 0.0
    is_stop = 1.0 if minute >= 90.0 else 0.0

    # ── Score state ───────────────────────────────────────────────────────
    hg = float(state.home_goals)
    ag = float(state.away_goals)
    diff = hg - ag
    n_goals = hg + ag
    is_drawn = 1.0 if diff == 0 else 0.0
    is_hw1   = 1.0 if diff == 1 else 0.0
    is_hw2p  = 1.0 if diff >= 2 else 0.0
    is_aw1   = 1.0 if diff == -1 else 0.0
    is_aw2p  = 1.0 if diff <= -2 else 0.0

    # ── Pregame strength ──────────────────────────────────────────────────
    # Compute over_2.5 from independent Poisson
    from scipy.stats import poisson
    over_2_5 = float(1.0 - sum(
        poisson.pmf(h, lh) * poisson.pmf(a, la)
        for h in range(4) for a in range(4) if h + a <= 2
    ))

    # ── Live stats ────────────────────────────────────────────────────────
    time_factor = max(minute, 1.0) / 90.0  # normalise to per-90

    home_xg_rate = away_xg_rate = lh, la  # default: pregame rates
    xg_miss = 1.0
    if state.home_stats and state.away_stats:
        h_xg = state.home_stats.xg
        a_xg = state.away_stats.xg
        if h_xg is not None and a_xg is not None and minute > 0:
            home_xg_rate = h_xg / time_factor
            away_xg_rate = a_xg / time_factor
            xg_miss = 0.0
        else:
            home_xg_rate = lh
            away_xg_rate = la
    else:
        home_xg_rate = lh
        away_xg_rate = la

    # Shots
    shots_miss = 1.0
    h_shots = a_shots = 0.0
    if state.home_stats and state.away_stats:
        h_sot = state.home_stats.shots_on_target
        a_sot = state.away_stats.shots_on_target
        if h_sot is not None and a_sot is not None and minute > 0:
            h_shots = h_sot / time_factor
            a_shots = a_sot / time_factor
            shots_miss = 0.0

    # Possession
    poss_miss = 1.0
    poss_ratio = 0.5
    if state.home_stats:
        p = state.home_stats.possession_pct
        if p is not None:
            poss_ratio = float(p) / 100.0
            poss_miss = 0.0

    # Big chances
    h_bc = a_bc = 0.0
    if state.home_stats and state.away_stats:
        h_bc_raw = state.home_stats.big_chances
        a_bc_raw = state.away_stats.big_chances
        if h_bc_raw is not None and minute > 0:
            h_bc = float(h_bc_raw) / time_factor
        if a_bc_raw is not None and minute > 0:
            a_bc = float(a_bc_raw) / time_factor

    # xG ratio
    total_xg = float(home_xg_rate) + float(away_xg_rate) + _EPS
    xg_ratio = float(home_xg_rate) / total_xg

    # Cards
    h_rc = float(state.home_stats.red_cards if state.home_stats else 0)
    a_rc = float(state.away_stats.red_cards if state.away_stats else 0)
    h_disadv = float(11 - state.home_effective_players)
    a_disadv = float(11 - state.away_effective_players)

    return LiveFeatureVector(
        regulation_minute=minute,
        fraction_elapsed=elapsed,
        remaining_fraction=remaining_frac,
        remaining_seconds=float(remaining),
        is_first_half=is_fh,
        is_second_half=is_sh,
        is_stoppage=is_stop,
        home_goals=hg,
        away_goals=ag,
        goal_diff=diff,
        n_goals_scored=n_goals,
        is_drawn=is_drawn,
        is_home_winning_1=is_hw1,
        is_home_winning_2plus=is_hw2p,
        is_away_winning_1=is_aw1,
        is_away_winning_2plus=is_aw2p,
        pregame_lh=float(lh),
        pregame_la=float(la),
        pregame_home_win_prob=float(hw),
        pregame_over_2_5=float(over_2_5),
        home_xg_rate=float(home_xg_rate),
        away_xg_rate=float(away_xg_rate),
        home_shots_rate=float(h_shots),
        away_shots_rate=float(a_shots),
        xg_ratio=float(xg_ratio),
        possession_ratio=float(poss_ratio),
        home_big_chances_rate=float(h_bc),
        away_big_chances_rate=float(a_bc),
        home_red_cards=float(h_rc),
        away_red_cards=float(a_rc),
        home_player_disadvantage=float(h_disadv),
        away_player_disadvantage=float(a_disadv),
        xg_missing=float(xg_miss),
        shots_missing=float(shots_miss),
        possession_missing=float(poss_miss),
    )
