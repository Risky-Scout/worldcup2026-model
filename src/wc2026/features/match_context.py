"""
Match context adjustments for the EGM formula.

Key: BDL `home_team` is administrative (not true home-field advantage).
True host effect comes from stadium.country == team country_code.
"""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from math import radians, cos, sin, asin, sqrt
from typing import Optional
import pandas as pd


HOST_COUNTRIES_2026 = {"USA", "CAN", "MEX", "US", "CA", "MX"}

# Rough stadium home locations (fallback if lat/lon missing)
_KNOWN_HOST_COUNTRY_CODES = HOST_COUNTRIES_2026


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371.0
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
    return 2 * R * asin(sqrt(a))


# Approximate team home locations (lat, lon) — top WC nations
_TEAM_HOME_COORDS: dict[str, tuple[float, float]] = {
    "USA": (38.0, -97.0), "CAN": (56.0, -96.0), "MEX": (23.6, -102.5),
    "BRA": (-14.2, -51.9), "ARG": (-38.4, -63.6), "FRA": (46.2, 2.2),
    "ENG": (52.4, -1.8), "GER": (51.2, 10.5), "ESP": (40.5, -3.7),
    "POR": (39.4, -8.2), "NED": (52.1, 5.3), "BEL": (50.5, 4.5),
    "ITA": (41.9, 12.6), "URU": (-32.5, -55.8), "COL": (4.6, -74.1),
    "CHI": (-35.7, -71.5), "ECU": (-1.8, -78.2), "PER": (-9.2, -75.0),
    "MAR": (31.8, -7.1), "SEN": (14.5, -14.5), "GHA": (7.9, -1.0),
    "CMR": (3.8, 11.5), "NGA": (9.1, 8.7), "CIV": (7.5, -5.5),
    "EGY": (26.8, 30.8), "ALG": (28.0, 1.7), "TUN": (33.9, 9.6),
    "JPN": (36.2, 138.3), "KOR": (35.9, 127.8), "SAU": (24.0, 45.0),
    "IRN": (32.4, 53.7), "AUS": (-25.3, 133.8),
}


@dataclass
class MatchContextAdjustmentFull:
    match_id: int
    home_team_id: int
    away_team_id: int
    prediction_timestamp: datetime

    # Venue/host
    actual_host_home: bool          # home team is from a host country
    actual_host_away: bool          # away team is from a host country
    neutral_match_flag: bool
    host_country_match_flag: bool

    # Log-lambda adjustments
    host_home_adj_log: float        # boost if home team plays in their own country
    host_away_adj_log: float        # boost if away team plays in their own country
    venue_home_adj_log: float       # generic venue (capacity, altitude proxy)
    venue_away_adj_log: float
    rest_travel_home_adj_log: float
    rest_travel_away_adj_log: float
    lineup_home_adj_log: float      # filled in later by lineup_strength
    lineup_away_adj_log: float
    injury_home_adj_log: float
    injury_away_adj_log: float
    incentive_home_adj_log: float   # group incentive, filled by group_incentives
    incentive_away_adj_log: float
    total_intensity_adj_log: float
    rho_adj: float

    # Group incentive features (for CLV model features)
    draw_utility: float
    rotation_probability_proxy: float
    goal_difference_utility: float

    # Stage
    stage_order: int
    knockout_flag: bool
    group_match_number: int

    def to_context_adjustment(self):
        """Convert to the simpler MatchContextAdjustment used in egm_to_lambdas."""
        from src.wc2026.models.egm_to_lambdas import MatchContextAdjustment
        return MatchContextAdjustment(
            match_id=self.match_id,
            home_team_id=self.home_team_id,
            away_team_id=self.away_team_id,
            prediction_timestamp=self.prediction_timestamp,
            venue_home_adj_log=self.venue_home_adj_log,
            venue_away_adj_log=self.venue_away_adj_log,
            host_home_adj_log=self.host_home_adj_log,
            host_away_adj_log=self.host_away_adj_log,
            rest_travel_home_adj_log=self.rest_travel_home_adj_log,
            rest_travel_away_adj_log=self.rest_travel_away_adj_log,
            lineup_home_adj_log=self.lineup_home_adj_log,
            lineup_away_adj_log=self.lineup_away_adj_log,
            injury_home_adj_log=self.injury_home_adj_log,
            injury_away_adj_log=self.injury_away_adj_log,
            incentive_home_adj_log=self.incentive_home_adj_log,
            incentive_away_adj_log=self.incentive_away_adj_log,
            total_intensity_adj_log=self.total_intensity_adj_log,
            rho_adj=self.rho_adj,
        )


def compute_match_context(
    match_row: dict,
    home_team_country_code: str,
    away_team_country_code: str,
    stadium_row: Optional[dict],
    home_standing: Optional[dict],
    away_standing: Optional[dict],
    home_match_dates: list[str],
    away_match_dates: list[str],
    prediction_timestamp: datetime,
) -> MatchContextAdjustmentFull:
    """
    Compute match context adjustments.

    match_row: /matches row dict
    home/away_team_country_code: BDL country_code
    stadium_row: /stadiums row dict
    home/away_standing: /group_standings row dict
    home/away_match_dates: list of ISO datetime strings for recent matches
    """
    match_id = int(match_row.get("id", 0))
    home_team_id = int((match_row.get("home_team") or {}).get("id", 0))
    away_team_id = int((match_row.get("away_team") or {}).get("id", 0))

    stadium_country = ""
    if stadium_row:
        stadium_country = str(stadium_row.get("country", ""))

    # True host check (NOT just admin home_team field)
    h_code = str(home_team_country_code).upper()
    a_code = str(away_team_country_code).upper()
    actual_host_home = h_code in _KNOWN_HOST_COUNTRY_CODES
    actual_host_away = a_code in _KNOWN_HOST_COUNTRY_CODES

    # Host adjustment: ~+0.10 to +0.15 log-lambda for true host
    HOST_ADJ = 0.12
    host_home_adj_log = HOST_ADJ if actual_host_home else 0.0
    host_away_adj_log = HOST_ADJ if actual_host_away else 0.0

    # Venue adjustment (capacity proxy — larger crowds slightly help hosting team)
    venue_home_adj_log = 0.0
    venue_away_adj_log = 0.0
    if stadium_row:
        cap = float(stadium_row.get("capacity", 50000) or 50000)
        venue_adj = max(0.0, (cap - 50000) / 500000)  # small effect
        if actual_host_home:
            venue_home_adj_log += venue_adj
        if actual_host_away:
            venue_away_adj_log += venue_adj

    # Rest/travel
    def _rest_days(match_dates: list[str]) -> float:
        if len(match_dates) < 2:
            return 7.0
        dates_sorted = sorted(match_dates)[-2:]
        try:
            d1 = pd.Timestamp(dates_sorted[0])
            d2 = pd.Timestamp(dates_sorted[1])
            return float((d2 - d1).days)
        except Exception:
            return 7.0

    home_rest = _rest_days(home_match_dates)
    away_rest = _rest_days(away_match_dates)
    REST_SCALE = 0.01
    rest_home_adj = REST_SCALE * min(home_rest - 4, 3)
    rest_away_adj = REST_SCALE * min(away_rest - 4, 3)

    # Travel distance proxy
    travel_home_adj = 0.0
    travel_away_adj = 0.0
    if stadium_row and stadium_row.get("latitude") and stadium_row.get("longitude"):
        slat = float(stadium_row["latitude"])
        slon = float(stadium_row["longitude"])
        h_home = _TEAM_HOME_COORDS.get(h_code)
        a_home = _TEAM_HOME_COORDS.get(a_code)
        if h_home:
            h_dist = _haversine_km(h_home[0], h_home[1], slat, slon)
            travel_home_adj = -min(h_dist / 50000, 0.05)
        if a_home:
            a_dist = _haversine_km(a_home[0], a_home[1], slat, slon)
            travel_away_adj = -min(a_dist / 50000, 0.05)

    # Group incentive features
    draw_utility = 0.0
    rotation_proxy = 0.0
    gd_utility = 0.0
    if home_standing and away_standing:
        h_pts = int(home_standing.get("points", 0) or 0)
        a_pts = int(away_standing.get("points", 0) or 0)
        h_played = int(home_standing.get("played", 0) or 0)
        a_played = int(away_standing.get("played", 0) or 0)
        h_gd = int(home_standing.get("goal_difference", 0) or 0)
        a_gd = int(away_standing.get("goal_difference", 0) or 0)
        # If both teams are safe or eliminated, rotation more likely
        if h_played >= 2 and a_played >= 2:
            rotation_proxy = 0.3 if (h_pts >= 6 or a_pts >= 6) else 0.0
        draw_utility = 0.2 if abs(h_pts - a_pts) <= 1 else 0.0
        gd_utility = 0.1 if abs(h_gd - a_gd) <= 2 else 0.0

    # Stage
    stage_name = str((match_row.get("stage") or {}).get("name", ""))
    stage_order = int((match_row.get("stage") or {}).get("order", 0) or 0)
    knockout_flag = "knock" in stage_name.lower() or "round of" in stage_name.lower() or stage_order > 3
    group_match_number = int(match_row.get("round_number", 0) or 0)

    return MatchContextAdjustmentFull(
        match_id=match_id,
        home_team_id=home_team_id,
        away_team_id=away_team_id,
        prediction_timestamp=prediction_timestamp,
        actual_host_home=actual_host_home,
        actual_host_away=actual_host_away,
        neutral_match_flag=not actual_host_home and not actual_host_away,
        host_country_match_flag=actual_host_home or actual_host_away,
        host_home_adj_log=host_home_adj_log,
        host_away_adj_log=host_away_adj_log,
        venue_home_adj_log=venue_home_adj_log,
        venue_away_adj_log=venue_away_adj_log,
        rest_travel_home_adj_log=rest_home_adj + travel_home_adj,
        rest_travel_away_adj_log=rest_away_adj + travel_away_adj,
        lineup_home_adj_log=0.0,
        lineup_away_adj_log=0.0,
        injury_home_adj_log=0.0,
        injury_away_adj_log=0.0,
        incentive_home_adj_log=0.0,
        incentive_away_adj_log=0.0,
        total_intensity_adj_log=0.0,
        rho_adj=0.0,
        draw_utility=draw_utility,
        rotation_probability_proxy=rotation_proxy,
        goal_difference_utility=gd_utility,
        stage_order=stage_order,
        knockout_flag=knockout_flag,
        group_match_number=group_match_number,
    )
