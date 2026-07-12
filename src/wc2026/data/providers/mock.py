"""
MockProvider — deterministic fixtures for unit tests.

Returns minimal valid records that pass schema validation.
No API calls made.
"""
from __future__ import annotations

from .base import DataProvider

MOCK_MATCHES = [
    {
        "id": 1001,
        "match_number": 1,
        "datetime": "2022-11-20T16:00:00.000Z",
        "status": "completed",
        "season": {"id": 2, "year": 2022},
        "stage": {"id": 1, "name": "Group Stage", "order": 1},
        "group": {"id": 1, "name": "Group A"},
        "stadium": {"id": 1, "name": "Al Bayt Stadium", "city": "Al Khor", "country": "QAT"},
        "home_team": {"id": 1, "name": "Qatar", "abbreviation": "QAT", "country_code": "QAT", "confederation": "AFC"},
        "away_team": {"id": 2, "name": "Ecuador", "abbreviation": "ECU", "country_code": "ECU", "confederation": "CONMEBOL"},
        "home_team_source": None,
        "away_team_source": None,
        "home_score": 0,
        "away_score": 2,
        "home_score_penalties": None,
        "away_score_penalties": None,
        "first_half_home_score": 0,
        "first_half_away_score": 2,
        "second_half_home_score": 0,
        "second_half_away_score": 0,
        "extra_time_home_score": None,
        "extra_time_away_score": None,
        "has_extra_time": False,
        "has_penalty_shootout": False,
        "round_number": 1,
        "round_name": None,
        "home_formation": "5-3-2",
        "away_formation": "4-4-2",
        "referee": None,
        "home_manager": None,
        "away_manager": None,
    },
    {
        "id": 1002,
        "match_number": 2,
        "datetime": "2022-11-21T13:00:00.000Z",
        "status": "completed",
        "season": {"id": 2, "year": 2022},
        "stage": {"id": 1, "name": "Group Stage", "order": 1},
        "group": {"id": 2, "name": "Group B"},
        "stadium": {"id": 2, "name": "Lusail Stadium", "city": "Lusail", "country": "QAT"},
        "home_team": {"id": 3, "name": "England", "abbreviation": "ENG", "country_code": "ENG", "confederation": "UEFA"},
        "away_team": {"id": 4, "name": "Iran", "abbreviation": "IRN", "country_code": "IRN", "confederation": "AFC"},
        "home_team_source": None,
        "away_team_source": None,
        "home_score": 6,
        "away_score": 2,
        "home_score_penalties": None,
        "away_score_penalties": None,
        "first_half_home_score": 3,
        "first_half_away_score": 0,
        "second_half_home_score": 3,
        "second_half_away_score": 2,
        "extra_time_home_score": None,
        "extra_time_away_score": None,
        "has_extra_time": False,
        "has_penalty_shootout": False,
        "round_number": 1,
        "round_name": None,
        "home_formation": "4-2-3-1",
        "away_formation": "4-5-1",
        "referee": None,
        "home_manager": None,
        "away_manager": None,
    },
]

MOCK_TEAM_STATS = [
    {
        "match_id": 1001,
        "team_id": 1,
        "is_home": True,
        "possession_pct": 38,
        "expected_goals": 0.4,
        "shots_total": 4,
        "shots_on_target": 1,
    },
    {
        "match_id": 1001,
        "team_id": 2,
        "is_home": False,
        "possession_pct": 62,
        "expected_goals": 1.8,
        "shots_total": 12,
        "shots_on_target": 6,
    },
    {
        "match_id": 1002,
        "team_id": 3,
        "is_home": True,
        "possession_pct": 59,
        "expected_goals": 3.2,
        "shots_total": 20,
        "shots_on_target": 11,
    },
    {
        "match_id": 1002,
        "team_id": 4,
        "is_home": False,
        "possession_pct": 41,
        "expected_goals": 1.1,
        "shots_total": 8,
        "shots_on_target": 4,
    },
]

MOCK_ODDS = [
    {
        "id": 1,
        "match_id": 1001,
        "vendor": "fanduel",
        "moneyline_home_odds": -130,
        "moneyline_away_odds": 340,
        "moneyline_draw_odds": 260,
        "spread_home_value": None,
        "spread_home_odds": None,
        "spread_away_value": None,
        "spread_away_odds": None,
        "total_value": "2.5",
        "total_over_odds": 110,
        "total_under_odds": -140,
        "updated_at": "2022-11-20T12:00:00.000Z",
        "markets": [],
    }
]


class MockProvider(DataProvider):
    """Returns deterministic fixtures. Safe for unit tests."""

    def fetch_matches(self, seasons: list[int]) -> list[dict]:
        return [m for m in MOCK_MATCHES if (m.get("season") or {}).get("year") in seasons]

    def fetch_odds(self, match_ids: list[int]) -> list[dict]:
        return [o for o in MOCK_ODDS if o["match_id"] in match_ids]

    def fetch_team_stats(self, match_ids: list[int]) -> list[dict]:
        return [s for s in MOCK_TEAM_STATS if s["match_id"] in match_ids]

    def fetch_player_stats(self, match_ids: list[int]) -> list[dict]:
        return []

    def fetch_events(self, match_ids: list[int]) -> list[dict]:
        return []

    def fetch_shots(self, match_ids: list[int]) -> list[dict]:
        return []

    def fetch_lineups(self, match_ids: list[int]) -> list[dict]:
        return []

    def fetch_momentum(self, match_ids: list[int]) -> list[dict]:
        return []

    def fetch_group_standings(self, seasons: list[int]) -> list[dict]:
        return []

    def fetch_team_form(self, match_ids: list[int]) -> list[dict]:
        return []
