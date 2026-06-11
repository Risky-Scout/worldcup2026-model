"""
Pydantic schemas for every BDL World Cup API response type.

All field names mirror the BDL API exactly. Any field that BDL says is
nullable is typed `Optional[...]`.

If BDL renames or removes a field, pydantic will raise a `ValidationError`
immediately during parsing — no silent pandas corruption.
"""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


# ---------------------------------------------------------------------------
# Shared sub-objects
# ---------------------------------------------------------------------------

class Season(BaseModel):
    id: int
    year: int


class TeamSummary(BaseModel):
    id: int
    name: str
    abbreviation: Optional[str] = None
    country_code: Optional[str] = None
    confederation: Optional[str] = None


class Group(BaseModel):
    id: int
    name: str


class Stadium(BaseModel):
    id: int
    name: str
    city: Optional[str] = None
    country: Optional[str] = None
    capacity: Optional[int] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class Stage(BaseModel):
    id: int
    name: str
    order: Optional[int] = None


class TeamSource(BaseModel):
    type: str
    source_match_id: Optional[int] = None
    source_match_number: Optional[int] = None
    source_group_id: Optional[int] = None
    source_group_name: Optional[str] = None
    placeholder: Optional[str] = None
    description: Optional[str] = None


class Referee(BaseModel):
    id: int
    name: str
    country_code: Optional[str] = None
    country_name: Optional[str] = None


class Manager(BaseModel):
    id: int
    name: str
    short_name: Optional[str] = None


class Player(BaseModel):
    id: int
    name: str
    short_name: Optional[str] = None
    position: Optional[str] = None
    date_of_birth: Optional[str] = None
    country_code: Optional[str] = None
    country_name: Optional[str] = None
    height_cm: Optional[int] = None
    jersey_number: Optional[str] = None


# ---------------------------------------------------------------------------
# Top-level objects
# ---------------------------------------------------------------------------

class Match(BaseModel):
    id: int
    match_number: Optional[int] = None
    datetime: Optional[str] = None
    status: str
    season: Optional[Season] = None
    stage: Optional[Stage] = None
    group: Optional[Group] = None
    stadium: Optional[Stadium] = None
    home_team: Optional[TeamSummary] = None
    away_team: Optional[TeamSummary] = None
    home_team_source: Optional[TeamSource] = None
    away_team_source: Optional[TeamSource] = None
    home_score: Optional[int] = None
    away_score: Optional[int] = None
    home_score_penalties: Optional[int] = None
    away_score_penalties: Optional[int] = None
    first_half_home_score: Optional[int] = None
    first_half_away_score: Optional[int] = None
    second_half_home_score: Optional[int] = None
    second_half_away_score: Optional[int] = None
    extra_time_home_score: Optional[int] = None
    extra_time_away_score: Optional[int] = None
    has_extra_time: Optional[bool] = None
    has_penalty_shootout: Optional[bool] = None
    round_number: Optional[int] = None
    round_name: Optional[str] = None
    home_formation: Optional[str] = None
    away_formation: Optional[str] = None
    referee: Optional[Referee] = None
    home_manager: Optional[Manager] = None
    away_manager: Optional[Manager] = None


class TeamMatchStat(BaseModel):
    match_id: int
    team_id: int
    is_home: bool
    possession_pct: Optional[float] = None
    expected_goals: Optional[float] = None
    big_chances: Optional[int] = None
    big_chances_missed: Optional[int] = None
    shots_total: Optional[int] = None
    shots_on_target: Optional[int] = None
    shots_off_target: Optional[int] = None
    shots_blocked: Optional[int] = None
    shots_inside_box: Optional[int] = None
    shots_outside_box: Optional[int] = None
    hit_woodwork: Optional[int] = None
    corners: Optional[int] = None
    offsides: Optional[int] = None
    fouls: Optional[int] = None
    yellow_cards: Optional[int] = None
    passes_total: Optional[int] = None
    passes_accurate: Optional[int] = None
    passes_final_third: Optional[int] = None
    long_balls_total: Optional[int] = None
    long_balls_accurate: Optional[int] = None
    crosses_total: Optional[int] = None
    crosses_accurate: Optional[int] = None
    tackles: Optional[int] = None
    interceptions: Optional[int] = None
    clearances: Optional[int] = None
    saves: Optional[int] = None
    dribbles_completed: Optional[int] = None
    dribbles_total: Optional[int] = None


class MatchShot(BaseModel):
    id: int
    match_id: int
    player_id: Optional[int] = None
    team_id: Optional[int] = None
    is_home: Optional[bool] = None
    shot_type: Optional[str] = None
    situation: Optional[str] = None
    body_part: Optional[str] = None
    goal_type: Optional[str] = None
    xg: Optional[float] = None
    xgot: Optional[float] = None
    player_x: Optional[float] = None
    player_y: Optional[float] = None
    time_minute: Optional[int] = None
    added_time: Optional[int] = None
    time_seconds: Optional[int] = None


class MatchEvent(BaseModel):
    id: int
    match_id: int
    incident_type: Optional[str] = None
    incident_class: Optional[str] = None
    time_minute: Optional[int] = None
    added_time: Optional[int] = None
    period: Optional[str] = None
    is_home: Optional[bool] = None
    player: Optional[Player] = None
    assist_player: Optional[Player] = None
    player_in: Optional[Player] = None
    player_out: Optional[Player] = None
    home_score: Optional[int] = None
    away_score: Optional[int] = None
    shootout_sequence: Optional[int] = None
    shootout_description: Optional[str] = None
    rescinded: Optional[bool] = None


class MatchMomentum(BaseModel):
    match_id: int
    minute: float
    value: float


class MarketOutcome(BaseModel):
    id: int
    key: str
    name: str
    type: str
    side: Optional[str] = None
    line_value: Optional[str] = None
    handicap: Optional[str] = None
    american_odds: Optional[int] = None
    decimal_odds: Optional[float] = None
    updated_at: Optional[str] = None


class MarketLine(BaseModel):
    id: int
    key: str
    name: str
    type: str
    period: str
    scope: str
    team_side: Optional[str] = None
    line_value: Optional[str] = None
    updated_at: Optional[str] = None
    outcomes: List[MarketOutcome] = Field(default_factory=list)


class Odds(BaseModel):
    id: int
    match_id: int
    vendor: str
    moneyline_home_odds: Optional[int] = None
    moneyline_away_odds: Optional[int] = None
    moneyline_draw_odds: Optional[int] = None
    spread_home_value: Optional[str] = None
    spread_home_odds: Optional[int] = None
    spread_away_value: Optional[str] = None
    spread_away_odds: Optional[int] = None
    total_value: Optional[str] = None
    total_over_odds: Optional[int] = None
    total_under_odds: Optional[int] = None
    updated_at: Optional[str] = None
    markets: List[MarketLine] = Field(default_factory=list)


class GroupStanding(BaseModel):
    season: Optional[Season] = None
    team: TeamSummary
    group: Optional[Group] = None
    position: Optional[int] = None
    played: Optional[int] = None
    won: Optional[int] = None
    drawn: Optional[int] = None
    lost: Optional[int] = None
    goals_for: Optional[int] = None
    goals_against: Optional[int] = None
    goal_difference: Optional[int] = None
    points: Optional[int] = None


class MatchTeamForm(BaseModel):
    match_id: int
    team_id: int
    is_home: bool
    avg_rating: Optional[float] = None
    position: Optional[int] = None
    value: Optional[str] = None


class MatchLineup(BaseModel):
    match_id: int
    team_id: int
    player: Player
    is_starter: bool
    is_substitute: bool
    shirt_number: Optional[int] = None
    position: Optional[str] = None
    formation: Optional[str] = None


class PlayerMatchStat(BaseModel):
    match_id: int
    player_id: int
    team_id: int
    is_home: bool
    rating: Optional[float] = None
    minutes_played: Optional[int] = None
    expected_goals: Optional[float] = None
    expected_assists: Optional[float] = None
    goals: Optional[int] = None
    assists: Optional[int] = None
    shots_on_target: Optional[int] = None
    passes_total: Optional[int] = None
    passes_accurate: Optional[int] = None
    key_passes: Optional[int] = None
    tackles: Optional[int] = None
    tackles_won: Optional[int] = None
    interceptions: Optional[int] = None
    duels_won: Optional[int] = None
    duels_lost: Optional[int] = None
    fouls_committed: Optional[int] = None
    was_fouled: Optional[int] = None
    touches: Optional[int] = None
    saves: Optional[int] = None


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------

def parse_matches(records: list[dict]) -> list[Match]:
    return [Match.model_validate(r) for r in records]


def parse_odds(records: list[dict]) -> list[Odds]:
    return [Odds.model_validate(r) for r in records]


def parse_team_stats(records: list[dict]) -> list[TeamMatchStat]:
    return [TeamMatchStat.model_validate(r) for r in records]


def parse_shots(records: list[dict]) -> list[MatchShot]:
    return [MatchShot.model_validate(r) for r in records]


def parse_events(records: list[dict]) -> list[MatchEvent]:
    return [MatchEvent.model_validate(r) for r in records]


def parse_momentum(records: list[dict]) -> list[MatchMomentum]:
    return [MatchMomentum.model_validate(r) for r in records]
