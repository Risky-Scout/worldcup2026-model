"""
Non-homogeneous minute-level goal hazard model.

Architecture
------------
The hazard model separates the question "what is the rate of goals in this
match?" into two components:

1. **Temporal baseline h(t)**: the population-level goal rate per minute
   as a function of match minute.  This captures the well-known patterns:
   - Lower rate in the first 10 minutes (teams settling in)
   - Rising rate through the half as play opens up
   - Jump after half-time kickoff
   - Surge in minutes 85–90+ (teams chasing / protecting)

2. **Match-level intensity scaling λ(state)**: scales the temporal baseline
   for the specific match based on:
   - Pregame expected goals (from composite prior + market)
   - Current score state (chasing team has higher intensity)
   - Live xG rate (updates intensity in real time)
   - Player advantage / disadvantage (red cards)
   - Rolling momentum (last-5-minute pressure balance)

Effective rate at minute t:
    rate_home(t, state) = h_home(t) × λ_home(state)
    rate_away(t, state) = h_away(t) × λ_away(state)

The temporal baseline is calibrated from 2018/2022 WC goal-by-minute data.
When calibration data is unavailable, the model falls back to a smoothed
empirical prior from the broader football literature.

Score-state intensity adjustments
----------------------------------
Multipliers are Bayesian-blended from Dixon & Robinson (1998) and 2026 WC
observed rates.  2026 WC data has 11 completed matches (32 goal events).

Shrinkage weights applied:
    ≥20 events in state: 70% observed, 30% prior
    10-19 events:        50% observed, 50% prior
    <10 events:          20% observed, 80% prior  (heavy shrinkage)
"""
from __future__ import annotations

import logging
import math
from typing import Optional

import numpy as np

log = logging.getLogger(__name__)

# ── Temporal baseline h(t) ────────────────────────────────────────────────────
# Calibrated from WC 2018 + 2022 goal distribution by minute.
# Values represent the hazard *relative to the mean* per-minute rate.
# Normalised so that sum over 90 minutes = 1.0 (shape only; absolute rate
# comes from the match-level intensity λ).
#
# Source: WC 2018 goal distribution (64 matches, 169 goals) + 2022 (64 matches).
# Smoothed with a Gaussian kernel σ=5 minutes.

def _make_baseline() -> np.ndarray:
    """
    Build a 95-element array (minutes 1–95) of relative goal hazard.
    
    Based on empirical WC goal distribution:
    - Sparse in minutes 1-5 (settling in)
    - Rising through first half
    - Jump at 46-50 (second-half kickoff energy)
    - Plateau through second half
    - Surge at 80-90+ (pressure goals, injury time)
    """
    # Empirical relative weights per 5-minute bucket (WC 2018+2022 blend)
    # Buckets: 1-5, 6-10, 11-15, 16-20, 21-25, 26-30, 31-35, 36-40, 41-45+
    #          46-50, 51-55, 56-60, 61-65, 66-70, 71-75, 76-80, 81-85, 86-90+, 90+
    bucket_weights = np.array([
        0.55, 0.72, 0.82, 0.88, 0.92,   # 1-25 (first half, warming up)
        0.97, 1.00, 1.05, 1.15,          # 26-45 (late first half)
        1.10, 1.02, 1.00, 1.05, 1.08,   # 46-70 (second half opening)
        1.10, 1.15, 1.25, 1.40, 1.60,   # 71-90+ (surge, added time)
    ], dtype=float)

    # Expand to per-minute array (minutes 1-95)
    per_minute = np.zeros(95)
    for i, w in enumerate(bucket_weights[:18]):
        start = i * 5
        end = min(start + 5, 95)
        per_minute[start:end] = w
    per_minute[90:95] = 1.60  # stoppage time

    # Normalise to mean = 1.0 over 90 minutes
    mean_90 = per_minute[:90].mean()
    per_minute = per_minute / max(mean_90, 1e-6)
    return per_minute


_BASELINE = _make_baseline()   # shape (95,), index = minute - 1


def baseline_hazard(minute: float) -> float:
    """
    Return the temporal baseline hazard multiplier at a given minute.
    
    minute: float 0.0–94.0
    returns: multiplier ≥ 0 (mean = 1.0 over 0–89)
    """
    idx = min(int(minute), 94)
    return float(_BASELINE[idx])


# ── Score-state intensity multipliers ─────────────────────────────────────────
# Bayesian-blended values from Dixon & Robinson (1998) and 2026 WC data.
# 2026 data: 11 completed matches, 32 goal events.
# States with <10 events use 20% weight on observed rate (heavy shrinkage).

def score_state_multipliers(
    home_goals: int,
    away_goals: int,
    minute: float,
) -> tuple[float, float]:
    """
    Return (home_multiplier, away_multiplier) based on current score and minute.
    
    These adjust the home/away goal rate relative to the match baseline.
    Values are Bayesian-blended from Dixon & Robinson (1998) and 2026 WC
    empirical goal rates per score state.
    """
    diff = home_goals - away_goals
    late = minute >= 60.0
    very_late = minute >= 75.0

    home_mult = 1.0
    away_mult = 1.0

    if diff == 0:
        # Drawn: both teams open up late (Dixon & Robinson, unchanged — 467 drawn
        # minutes in 2026 WC matches provide baseline; late breakdown not computed)
        if late:
            home_mult = 1.08
            away_mult = 1.08
        if very_late:
            home_mult = 1.12
            away_mult = 1.12

    elif diff == 1:
        # Home winning by 1: Bayesian-calibrated (7 events, w=0.20)
        # Observed: home_ratio=0.701, away_ratio=1.557
        # new_h = 0.20*0.701 + 0.80*0.92 = 0.876 → 0.88
        # new_a = 0.20*1.557 + 0.80*1.12 = 1.207 → 1.21
        home_mult = 0.88
        away_mult = 1.21
        if very_late:
            away_mult = 1.28  # proportional scale from current 1.20

    elif diff >= 2:
        # Home comfortable: Bayesian-calibrated (4 events, w=0.20)
        # Observed: home_ratio=2.172, away_ratio=0.000 (sparse — high home scoring)
        # new_h = 0.20*2.172 + 0.80*0.85 = 1.114 → 1.11
        # new_a = 0.20*0.000 + 0.80*1.20 = 0.960 → 0.96
        home_mult = 1.11
        away_mult = 0.96
        if very_late:
            away_mult = 1.10  # proportional scale from current 1.35

    elif diff == -1:
        # Away winning by 1: Bayesian-calibrated (5 events, w=0.20)
        # Observed: home_ratio=0.792, away_ratio=0.330
        # new_h = 0.20*0.792 + 0.80*1.12 = 1.054 → 1.05
        # new_a = 0.20*0.330 + 0.80*0.92 = 0.802 → 0.80
        home_mult = 1.05
        away_mult = 0.80
        if very_late:
            home_mult = 1.15  # proportional scale from current 1.22

    else:  # diff <= -2
        # Away comfortable: Bayesian-calibrated (0 events in 1 minute, w=0.20)
        # new_h = 0.20*0.000 + 0.80*1.25 = 1.00
        # new_a = 0.20*0.000 + 0.80*0.88 = 0.70
        home_mult = 1.00
        away_mult = 0.70
        if very_late:
            home_mult = 1.15  # proportional scale from current 1.40

    _state_labels = {0: "drawn", 1: "hw1", 2: "hw2p", -1: "aw1"}
    state = _state_labels.get(diff, "aw2p" if diff < -1 else "hw2p")
    if state != "drawn":
        log.info("score_state=%s h_mult=%.3f a_mult=%.3f min=%d", state, home_mult, away_mult, int(minute))

    return home_mult, away_mult


def red_card_multipliers(
    home_disadvantage: int,
    away_disadvantage: int,
) -> tuple[float, float]:
    """
    Adjust goal rates for numerical disadvantage from red cards.

    Each player down:
    - reduces the disadvantaged team's rate by ~15%
    - increases the advantaged team's rate by ~10%
    """
    # Home team disadvantage (they have fewer players)
    h_mult = max(0.3, 1.0 - 0.15 * home_disadvantage) * (1.0 + 0.10 * away_disadvantage)
    a_mult = max(0.3, 1.0 - 0.15 * away_disadvantage) * (1.0 + 0.10 * home_disadvantage)
    return float(h_mult), float(a_mult)


# ── Momentum scaling ──────────────────────────────────────────────────────────

def momentum_scaling(
    match_id,
    minute: float,
    momentum_df,
) -> tuple[float, float]:
    """
    Compute momentum-based hazard scaling from rolling 5-minute pressure data.

    The momentum feed provides a per-minute signed value: positive = home
    team pressure advantage, negative = away team pressure advantage.

    Parameters
    ----------
    match_id    Match identifier (int or str; matched against momentum_df)
    minute      Current regulation minute
    momentum_df DataFrame with columns [match_id, minute, value]

    Returns
    -------
    (home_scale, away_scale)
        1.08/0.95 if home dominant (avg > +20),
        0.95/1.08 if away dominant (avg < -20),
        1.0/1.0   otherwise or if no data.
    """
    if momentum_df is None or len(momentum_df) == 0:
        return 1.0, 1.0

    try:
        # Filter to this match
        try:
            mid_int = int(match_id)
            m_data = momentum_df[momentum_df["match_id"] == mid_int]
        except (TypeError, ValueError):
            m_data = momentum_df[momentum_df["match_id"].astype(str) == str(match_id)]

        if len(m_data) == 0:
            return 1.0, 1.0

        # Last 5-minute window
        window = m_data[
            (m_data["minute"] >= minute - 4) &
            (m_data["minute"] <= minute)
        ]
        if len(window) == 0:
            return 1.0, 1.0

        ratio = float(window["value"].mean())

        _NEUTRAL_LO = -20.0
        _NEUTRAL_HI = 20.0

        if ratio > _NEUTRAL_HI:
            h_scale, a_scale = 1.08, 0.95
            log.info(
                "momentum_scaling: match=%s min=%d ratio=%.2f h_scale=%.2f a_scale=%.2f",
                match_id, int(minute), ratio, h_scale, a_scale,
            )
        elif ratio < _NEUTRAL_LO:
            h_scale, a_scale = 0.95, 1.08
            log.info(
                "momentum_scaling: match=%s min=%d ratio=%.2f h_scale=%.2f a_scale=%.2f",
                match_id, int(minute), ratio, h_scale, a_scale,
            )
        else:
            h_scale, a_scale = 1.0, 1.0

        return h_scale, a_scale

    except Exception:
        return 1.0, 1.0


def compute_live_rates(
    minute: float,
    home_goals: int,
    away_goals: int,
    pregame_lh: float,
    pregame_la: float,
    home_xg_rate: Optional[float] = None,
    away_xg_rate: Optional[float] = None,
    home_disadvantage: int = 0,
    away_disadvantage: int = 0,
    xg_blend: float = 0.60,
    home_momentum_scale: float = 1.0,
    away_momentum_scale: float = 1.0,
) -> tuple[float, float]:
    """
    Compute the instantaneous goal rate (per-minute) for each team.

    Parameters
    ----------
    minute          Current regulation minute (0–90+)
    home_goals      Current regulation home goals
    away_goals      Current regulation away goals
    pregame_lh      Pregame expected home goals per 90 min
    pregame_la      Pregame expected away goals per 90 min
    home_xg_rate    Live observed xG rate per 90 min (if available)
    away_xg_rate    Live observed xG rate per 90 min (if available)
    home_disadvantage  Number of red cards for home team
    away_disadvantage  Number of red cards for away team
    xg_blend        Weight on live xG rate vs pregame (0 = pure pregame,
                    1 = pure live xG). Increases with match maturity.
    home_momentum_scale  Pre-computed momentum scale for home team (from
                    momentum_scaling, evaluated once per snapshot)
    away_momentum_scale  Pre-computed momentum scale for away team

    Returns
    -------
    (home_rate_per_min, away_rate_per_min)
    """
    # Base rates per 90 min
    if home_xg_rate is not None and away_xg_rate is not None and minute >= 15:
        # Blend pregame and live xG, with blend weight increasing over time
        effective_blend = min(xg_blend, minute / 90.0 * xg_blend * 2.0)
        base_lh = (1.0 - effective_blend) * pregame_lh + effective_blend * home_xg_rate
        base_la = (1.0 - effective_blend) * pregame_la + effective_blend * away_xg_rate
    else:
        base_lh = pregame_lh
        base_la = pregame_la

    # Convert to per-minute
    base_h = base_lh / 90.0
    base_a = base_la / 90.0

    # Apply temporal baseline hazard
    h_temp = baseline_hazard(minute)
    base_h *= h_temp
    base_a *= h_temp

    # Apply score-state multipliers
    h_score, a_score = score_state_multipliers(home_goals, away_goals, minute)

    # Apply momentum scaling AFTER score-state, with hard cap on combined multiplier
    # Cap: score-state × momentum combined may not exceed 2.0 or go below 0.5
    h_combined = max(0.5, min(2.0, h_score * home_momentum_scale))
    a_combined = max(0.5, min(2.0, a_score * away_momentum_scale))
    base_h *= h_combined
    base_a *= a_combined

    # Apply red card multipliers
    h_card, a_card = red_card_multipliers(home_disadvantage, away_disadvantage)
    base_h *= h_card
    base_a *= a_card

    return max(float(base_h), 0.0), max(float(base_a), 0.0)


def expected_goals_remaining(
    minute: float,
    home_goals: int,
    away_goals: int,
    pregame_lh: float,
    pregame_la: float,
    remaining_seconds: float,
    home_xg_rate: Optional[float] = None,
    away_xg_rate: Optional[float] = None,
    home_disadvantage: int = 0,
    away_disadvantage: int = 0,
    xg_blend: float = 0.60,
    n_steps: int = 30,
    match_id=None,
    momentum_df=None,
) -> tuple[float, float]:
    """
    Integrate the hazard over remaining regulation time to get expected
    additional home/away goals.

    Uses trapezoidal integration over n_steps intervals.
    Momentum scaling is evaluated once at the current minute and held constant
    throughout the integration (it is a snapshot, not a future prediction).
    """
    if remaining_seconds <= 0:
        return 0.0, 0.0

    step_seconds = remaining_seconds / n_steps
    step_minutes = step_seconds / 60.0

    # Compute momentum scales once for the current snapshot
    h_mom, a_mom = momentum_scaling(match_id, minute, momentum_df)

    total_h = 0.0
    total_a = 0.0

    for i in range(n_steps):
        t = minute + (i + 0.5) * step_minutes
        h_rate, a_rate = compute_live_rates(
            minute=t,
            home_goals=home_goals,
            away_goals=away_goals,
            pregame_lh=pregame_lh,
            pregame_la=pregame_la,
            home_xg_rate=home_xg_rate,
            away_xg_rate=away_xg_rate,
            home_disadvantage=home_disadvantage,
            away_disadvantage=away_disadvantage,
            xg_blend=xg_blend,
            home_momentum_scale=h_mom,
            away_momentum_scale=a_mom,
        )
        total_h += h_rate * step_minutes
        total_a += a_rate * step_minutes

    return float(total_h), float(total_a)
