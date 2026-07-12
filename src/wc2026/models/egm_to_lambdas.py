"""
Convert TeamMarginRating + MatchContextAdjustment → (lambda_home, lambda_away).

This is the bridge between the EGM layer and the existing PMF machinery.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from math import exp

import numpy as np
from src.wc2026.ratings.team_margin import TeamMarginRating


@dataclass
class MatchContextAdjustment:
    match_id: int
    home_team_id: int
    away_team_id: int
    prediction_timestamp: datetime

    venue_home_adj_log: float = 0.0
    venue_away_adj_log: float = 0.0
    host_home_adj_log: float = 0.0   # actual host, not admin home_team
    host_away_adj_log: float = 0.0
    rest_travel_home_adj_log: float = 0.0
    rest_travel_away_adj_log: float = 0.0
    lineup_home_adj_log: float = 0.0
    lineup_away_adj_log: float = 0.0
    injury_home_adj_log: float = 0.0
    injury_away_adj_log: float = 0.0
    incentive_home_adj_log: float = 0.0
    incentive_away_adj_log: float = 0.0
    total_intensity_adj_log: float = 0.0
    rho_adj: float = 0.0


def margin_total_to_lambdas(
    margin: float,
    total: float,
) -> tuple[float, float]:
    """
    Convert (margin, total) into (lambda_home, lambda_away).

    margin = expected home goals - expected away goals  (team strength signal)
    total  = expected home goals + expected away goals  (tempo/market/tournament signal)

    This decouples margin strength from total-goal environment.
    The EGM layer should learn margin; the total anchor comes from:
      - the totals market (primary when available)
      - a tournament baseline (~2.65 for WC regulation time)
      - the structural total from attack/defense logs

    lambda_home = (total + margin) / 2
    lambda_away = (total - margin) / 2
    """
    min_l = 0.05
    # Clamp margin so neither lambda goes below min_l before splitting
    margin = float(np.clip(margin, -(total - 2 * min_l), total - 2 * min_l))
    home = (total + margin) / 2.0
    away = (total - margin) / 2.0
    return max(home, min_l), max(away, min_l)


def egm_with_total_anchor(
    home_egm: float,
    away_egm: float,
    total_goal_anchor: float,
) -> tuple[float, float]:
    """
    Compute lambdas from team EGM ratings anchored to a total-goal constraint.

    home_egm: neutral EGM for home team (positive = stronger than average)
    away_egm: neutral EGM for away team
    total_goal_anchor: total goals constraint (from market or tournament prior)

    The margin is the difference of EGMs.
    The total is provided externally (market-implied or tournament baseline).
    """
    margin = home_egm - away_egm
    return margin_total_to_lambdas(margin, total_goal_anchor)


def egm_components_to_lambdas(
    home_rating: TeamMarginRating,
    away_rating: TeamMarginRating,
    context: MatchContextAdjustment,
    base_goals: float = 1.45,
) -> tuple[float, float, dict]:
    """
    Returns (lambda_home, lambda_away, diagnostics_dict).

    Formula:
      lambda_home = base_goals * exp(
          attack_log_home - defense_log_away
          + venue_home_adj_log + host_home_adj_log
          + rest_travel_home_adj_log + lineup_home_adj_log
          + injury_home_adj_log + incentive_home_adj_log
          + 0.5 * total_intensity_adj_log
      )
      lambda_away = base_goals * exp(
          attack_log_away - defense_log_home
          + venue_away_adj_log + host_away_adj_log
          + rest_travel_away_adj_log + lineup_away_adj_log
          + injury_away_adj_log + incentive_away_adj_log
          + 0.5 * total_intensity_adj_log
      )

    IMPORTANT: 'home_team' in BDL API is administrative, not true home advantage.
    True host effect must come through host_home_adj_log, set separately.
    Do NOT add a generic league home-advantage offset.

    # NOTE: This function does not enforce a total-goal anchor.
    # For a calibrated total, use egm_with_total_anchor() instead,
    # which separates margin strength (from EGM) from total goals (from market/prior).
    """
    lh_log = (
        home_rating.attack_log - away_rating.defense_log
        + context.venue_home_adj_log + context.host_home_adj_log
        + context.rest_travel_home_adj_log + context.lineup_home_adj_log
        + context.injury_home_adj_log + context.incentive_home_adj_log
        + 0.5 * context.total_intensity_adj_log
    )
    la_log = (
        away_rating.attack_log - home_rating.defense_log
        + context.venue_away_adj_log + context.host_away_adj_log
        + context.rest_travel_away_adj_log + context.lineup_away_adj_log
        + context.injury_away_adj_log + context.incentive_away_adj_log
        + 0.5 * context.total_intensity_adj_log
    )
    lambda_home = base_goals * exp(lh_log)
    lambda_away = base_goals * exp(la_log)

    diagnostics = {
        "base_goals": base_goals,
        "lh_log": lh_log,
        "la_log": la_log,
        "home_attack_log": home_rating.attack_log,
        "home_defense_log": home_rating.defense_log,
        "away_attack_log": away_rating.attack_log,
        "away_defense_log": away_rating.defense_log,
        "match_expected_goal_margin": lambda_home - lambda_away,
    }
    return lambda_home, lambda_away, diagnostics
