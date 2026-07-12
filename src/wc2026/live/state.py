"""
MatchState — live match snapshot.

All live prediction begins from a MatchState object.  This is the single
source of truth for what the model knows at any moment during a match.

Design principles
-----------------
- Immutable snapshots: each state update creates a new MatchState.
- Explicit clock representation: clock_seconds is canonical; clock_display
  is for human readability.
- Separate regulation vs extra-time scoring.
- No post-match data may appear before the match ends (leakage guard).
- Missing-data fields are None, not silently 0 or imputed.
"""
from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field
from enum import Enum


class MatchStatus(str, Enum):
    PREMATCH    = "prematch"
    FIRST_HALF  = "first_half"
    HALF_TIME   = "half_time"
    SECOND_HALF = "second_half"
    EXTRA_TIME_FIRST  = "extra_time_first"
    EXTRA_TIME_SECOND = "extra_time_second"
    PENALTIES   = "penalties"
    COMPLETED   = "completed"
    SUSPENDED   = "suspended"
    POSTPONED   = "postponed"


class EventType(str, Enum):
    GOAL          = "goal"
    OWN_GOAL      = "own_goal"
    YELLOW_CARD   = "yellow_card"
    RED_CARD      = "red_card"
    YELLOW_RED    = "yellow_red"
    SUBSTITUTION  = "substitution"
    PENALTY_MISS  = "penalty_miss"
    PENALTY_GOAL  = "penalty_goal"
    VAR_REVIEW    = "var_review"
    INJURY        = "injury"
    KICKOFF       = "kickoff"
    WHISTLE       = "whistle"


@dataclass(frozen=True)
class MatchEvent:
    """A single timestamped match event."""
    clock_seconds: int      # seconds into the half (0 = kickoff)
    clock_display: str      # e.g. "45+3", "67", "90+5"
    event_type: EventType
    team: str               # "home" | "away"
    player_id: int | None = None
    player_name: str | None = None
    detail: str | None = None    # e.g. "penalty", "VAR cancel", sub-in name


@dataclass
class TeamLiveStats:
    """Live team statistics at a given moment."""
    shots_total: int | None = None
    shots_on_target: int | None = None
    xg: float | None = None          # cumulative xG
    xgot: float | None = None        # xG on target
    big_chances: int | None = None
    corners: int | None = None
    possession_pct: float | None = None
    fouls: int | None = None
    offsides: int | None = None
    yellow_cards: int = 0
    red_cards: int = 0
    players_sent_off: int = 0           # effectively 10 if 1, etc.
    # Formation/shape proxies
    attack_momentum_score: float | None = None   # from BDL momentum feed


@dataclass
class MatchState:
    """
    Complete live match snapshot at a specific clock moment.

    Clock semantics
    ---------------
    clock_seconds   : seconds elapsed in the CURRENT half (regulation only).
                      0 at kickoff of each half.
    match_seconds   : total regulation seconds elapsed
                      (0-45*60 for first half, 45*60 - 90*60 for second half).
    added_time_1h   : stoppage added to first half (None if not yet announced)
    added_time_2h   : stoppage added to second half

    Score semantics
    ---------------
    home_goals, away_goals : regulation score only.
    Do not include extra-time or penalty goals.
    """
    # Identity
    match_id: str
    home_team: str
    away_team: str
    season: int
    stage: str                              # "group", "R16", "QF", "SF", "F"
    venue: str | None = None

    # Clock
    status: MatchStatus = MatchStatus.PREMATCH
    clock_seconds: int = 0                  # seconds in current half
    clock_display: str = "0"
    match_seconds: int = 0                  # total regulation seconds
    added_time_1h: int | None = None
    added_time_2h: int | None = None
    snapshot_time: dt.datetime | None = None  # wall-clock when snapshot taken

    # Regulation score
    home_goals: int = 0
    away_goals: int = 0

    # Extra-time score (not part of regulation PMF)
    home_goals_et: int = 0
    away_goals_et: int = 0

    # Penalty shootout (tracked separately)
    home_penalties: int = 0
    away_penalties: int = 0
    home_penalties_missed: int = 0
    away_penalties_missed: int = 0

    # Events (immutable tuple for hashability if needed)
    events: tuple[MatchEvent, ...] = field(default_factory=tuple)

    # Live stats
    home_stats: TeamLiveStats | None = None
    away_stats: TeamLiveStats | None = None

    # Lineup availability
    lineup_available: bool = False
    home_effective_players: int = 11       # decremented on red card
    away_effective_players: int = 11

    # Pre-match prior (from the pregame PMF engine)
    pregame_home_win_prob: float | None = None
    pregame_draw_prob: float | None = None
    pregame_away_win_prob: float | None = None
    pregame_lh: float | None = None    # pregame expected home goals
    pregame_la: float | None = None    # pregame expected away goals

    # Live odds snapshot (for CLV / live market comparison)
    live_home_win_odds: float | None = None  # decimal odds
    live_draw_odds: float | None = None
    live_away_win_odds: float | None = None
    live_odds_timestamp: dt.datetime | None = None

    # Data quality flags
    missing_data_warnings: tuple[str, ...] = field(default_factory=tuple)

    # ── Derived properties ────────────────────────────────────────────────

    @property
    def regulation_minute(self) -> float:
        """Canonical regulation minute (0.0 at kickoff, 90.0 at final whistle)."""
        return min(self.match_seconds / 60.0, 90.0)

    @property
    def remaining_regulation_seconds(self) -> float:
        """Expected regulation seconds remaining (including announced added time)."""
        if self.status in (MatchStatus.COMPLETED, MatchStatus.EXTRA_TIME_FIRST,
                           MatchStatus.EXTRA_TIME_SECOND, MatchStatus.PENALTIES):
            return 0.0
        base_remaining = max(0, 90 * 60 - self.match_seconds)
        stoppage = 0
        if self.status == MatchStatus.FIRST_HALF and self.added_time_1h:
            # Already past 45min — count announced added time
            over = max(0, self.match_seconds - 45 * 60)
            stoppage = max(0, (self.added_time_1h * 60) - over)
        elif self.status == MatchStatus.SECOND_HALF and self.added_time_2h:
            over = max(0, self.match_seconds - 90 * 60)
            stoppage = max(0, (self.added_time_2h * 60) - over)
        elif self.status == MatchStatus.SECOND_HALF and self.match_seconds >= 90 * 60:
            # Past 90 with no announcement: assume ~4 min average stoppage
            stoppage = max(0, 4 * 60 - (self.match_seconds - 90 * 60))
        return float(base_remaining + stoppage)

    @property
    def score_state(self) -> str:
        """Human-readable score state: e.g. 'home_winning_1', 'drawn', 'away_winning_2+'."""
        diff = self.home_goals - self.away_goals
        if diff == 0:
            return "drawn"
        if diff == 1:
            return "home_winning_1"
        if diff >= 2:
            return "home_winning_2plus"
        if diff == -1:
            return "away_winning_1"
        return "away_winning_2plus"

    @property
    def is_regulation(self) -> bool:
        return self.status in (
            MatchStatus.FIRST_HALF, MatchStatus.HALF_TIME, MatchStatus.SECOND_HALF
        )

    @property
    def n_goals_scored(self) -> int:
        return self.home_goals + self.away_goals

    @property
    def total_goal_events(self) -> int:
        return sum(1 for e in self.events if e.event_type in (EventType.GOAL, EventType.OWN_GOAL))

    def with_goal(self, team: str, event: MatchEvent | None = None) -> MatchState:
        """Return new MatchState with one additional regulation goal."""
        new_events = self.events + ((event,) if event else ())
        if team == "home":
            return MatchState(**{**self.__dict__,
                                 "home_goals": self.home_goals + 1,
                                 "events": new_events})
        return MatchState(**{**self.__dict__,
                             "away_goals": self.away_goals + 1,
                             "events": new_events})

    def to_dict(self) -> dict:
        return {
            "match_id": self.match_id,
            "home_team": self.home_team,
            "away_team": self.away_team,
            "status": self.status.value,
            "clock_display": self.clock_display,
            "regulation_minute": round(self.regulation_minute, 2),
            "match_seconds": self.match_seconds,
            "remaining_seconds": round(self.remaining_regulation_seconds, 1),
            "home_goals": self.home_goals,
            "away_goals": self.away_goals,
            "score_state": self.score_state,
            "home_effective_players": self.home_effective_players,
            "away_effective_players": self.away_effective_players,
            "n_events": len(self.events),
            "missing_data_warnings": list(self.missing_data_warnings),
        }
