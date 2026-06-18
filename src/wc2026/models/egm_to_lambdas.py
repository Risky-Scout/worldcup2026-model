"""
Convert TeamMarginRating + MatchContextAdjustment → (lambda_home, lambda_away).

This is the bridge between the EGM layer and the existing PMF machinery.
"""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from math import exp
from typing import Optional

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


def egm_components_to_lambdas(
    home_rating: TeamMarginRating,
    away_rating: TeamMarginRating,
    context: MatchContextAdjustment,
    base_goals: float = 1.30,
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
