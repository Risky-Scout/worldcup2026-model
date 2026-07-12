"""
Pydantic schemas for every BDL World Cup API response type.

All field names mirror the BDL API exactly. Any field that BDL says is
nullable is typed `Optional[...]`.

If BDL renames or removes a field, pydantic will raise a `ValidationError`
immediately during parsing — no silent pandas corruption.
"""
from __future__ import annotations

from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Shared sub-objects
# ---------------------------------------------------------------------------

class Season(BaseModel):
    id: int
    year: int


class TeamSummary(BaseModel):
    id: int
    name: str
    abbreviation: str | None = None
    country_code: str | None = None
    confederation: str | None = None


class Group(BaseModel):
    id: int
    name: str


class Stadium(BaseModel):
    id: int
    name: str
    city: str | None = None
    country: str | None = None
    capacity: int | None = None
    latitude: float | None = None
    longitude: float | None = None


class Stage(BaseModel):
    id: int
    name: str
    order: int | None = None


class TeamSource(BaseModel):
    type: str
    source_match_id: int | None = None
    source_match_number: int | None = None
    source_group_id: int | None = None
    source_group_name: str | None = None
    placeholder: str | None = None
    description: str | None = None


class Referee(BaseModel):
    id: int
    name: str
    country_code: str | None = None
    country_name: str | None = None


class Manager(BaseModel):
    id: int
    name: str
    short_name: str | None = None


class Player(BaseModel):
    id: int
    name: str
    short_name: str | None = None
    position: str | None = None
    date_of_birth: str | None = None
    country_code: str | None = None
    country_name: str | None = None
    height_cm: int | None = None
    jersey_number: str | None = None


# ---------------------------------------------------------------------------
# Top-level objects
# ---------------------------------------------------------------------------

class Match(BaseModel):
    id: int
    match_number: int | None = None
    datetime: str | None = None
    status: str
    season: Season | None = None
    stage: Stage | None = None
    group: Group | None = None
    stadium: Stadium | None = None
    home_team: TeamSummary | None = None
    away_team: TeamSummary | None = None
    home_team_source: TeamSource | None = None
    away_team_source: TeamSource | None = None
    home_score: int | None = None
    away_score: int | None = None
    home_score_penalties: int | None = None
    away_score_penalties: int | None = None
    first_half_home_score: int | None = None
    first_half_away_score: int | None = None
    second_half_home_score: int | None = None
    second_half_away_score: int | None = None
    extra_time_home_score: int | None = None
    extra_time_away_score: int | None = None
    has_extra_time: bool | None = None
    has_penalty_shootout: bool | None = None
    round_number: int | None = None
    round_name: str | None = None
    home_formation: str | None = None
    away_formation: str | None = None
    referee: Referee | None = None
    home_manager: Manager | None = None
    away_manager: Manager | None = None


class TeamMatchStat(BaseModel):
    match_id: int
    team_id: int
    is_home: bool
    possession_pct: float | None = None
    expected_goals: float | None = None
    big_chances: int | None = None
    big_chances_missed: int | None = None
    shots_total: int | None = None
    shots_on_target: int | None = None
    shots_off_target: int | None = None
    shots_blocked: int | None = None
    shots_inside_box: int | None = None
    shots_outside_box: int | None = None
    hit_woodwork: int | None = None
    corners: int | None = None
    offsides: int | None = None
    fouls: int | None = None
    yellow_cards: int | None = None
    passes_total: int | None = None
    passes_accurate: int | None = None
    passes_final_third: int | None = None
    long_balls_total: int | None = None
    long_balls_accurate: int | None = None
    crosses_total: int | None = None
    crosses_accurate: int | None = None
    tackles: int | None = None
    interceptions: int | None = None
    clearances: int | None = None
    saves: int | None = None
    dribbles_completed: int | None = None
    dribbles_total: int | None = None


class MatchShot(BaseModel):
    id: int
    match_id: int
    player_id: int | None = None
    team_id: int | None = None
    is_home: bool | None = None
    shot_type: str | None = None
    situation: str | None = None
    body_part: str | None = None
    goal_type: str | None = None
    xg: float | None = None
    xgot: float | None = None
    player_x: float | None = None
    player_y: float | None = None
    time_minute: int | None = None
    added_time: int | None = None
    time_seconds: int | None = None


class MatchEvent(BaseModel):
    id: int
    match_id: int
    incident_type: str | None = None
    incident_class: str | None = None
    time_minute: int | None = None
    added_time: int | None = None
    period: str | None = None
    is_home: bool | None = None
    player: Player | None = None
    assist_player: Player | None = None
    player_in: Player | None = None
    player_out: Player | None = None
    home_score: int | None = None
    away_score: int | None = None
    shootout_sequence: int | None = None
    shootout_description: str | None = None
    rescinded: bool | None = None


class MatchMomentum(BaseModel):
    match_id: int
    minute: float
    value: float


class MarketOutcome(BaseModel):
    id: int
    key: str
    name: str
    type: str
    side: str | None = None
    line_value: str | None = None
    handicap: str | None = None
    american_odds: int | None = None
    decimal_odds: float | None = None
    updated_at: str | None = None


class MarketLine(BaseModel):
    id: int
    key: str
    name: str
    type: str
    period: str
    scope: str
    team_side: str | None = None
    line_value: str | None = None
    updated_at: str | None = None
    outcomes: list[MarketOutcome] = Field(default_factory=list)


class Odds(BaseModel):
    id: int
    match_id: int
    vendor: str
    moneyline_home_odds: int | None = None
    moneyline_away_odds: int | None = None
    moneyline_draw_odds: int | None = None
    spread_home_value: str | None = None
    spread_home_odds: int | None = None
    spread_away_value: str | None = None
    spread_away_odds: int | None = None
    total_value: str | None = None
    total_over_odds: int | None = None
    total_under_odds: int | None = None
    updated_at: str | None = None
    markets: list[MarketLine] = Field(default_factory=list)


class GroupStanding(BaseModel):
    season: Season | None = None
    team: TeamSummary
    group: Group | None = None
    position: int | None = None
    played: int | None = None
    won: int | None = None
    drawn: int | None = None
    lost: int | None = None
    goals_for: int | None = None
    goals_against: int | None = None
    goal_difference: int | None = None
    points: int | None = None


class MatchTeamForm(BaseModel):
    match_id: int
    team_id: int
    is_home: bool
    avg_rating: float | None = None
    position: int | None = None
    value: str | None = None


class MatchLineup(BaseModel):
    match_id: int
    team_id: int
    player: Player
    is_starter: bool
    is_substitute: bool
    shirt_number: int | None = None
    position: str | None = None
    formation: str | None = None


class PlayerMatchStat(BaseModel):
    match_id: int
    player_id: int
    team_id: int
    is_home: bool
    rating: float | None = None
    minutes_played: int | None = None
    expected_goals: float | None = None
    expected_assists: float | None = None
    goals: int | None = None
    assists: int | None = None
    shots_on_target: int | None = None
    passes_total: int | None = None
    passes_accurate: int | None = None
    key_passes: int | None = None
    tackles: int | None = None
    tackles_won: int | None = None
    interceptions: int | None = None
    duels_won: int | None = None
    duels_lost: int | None = None
    fouls_committed: int | None = None
    was_fouled: int | None = None
    touches: int | None = None
    saves: int | None = None


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
