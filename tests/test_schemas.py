"""
Tests for BDL data schemas — fail loudly if BDL changes a field.
"""
import pytest
from pydantic import ValidationError

from wc2026.data.schemas import Match, Odds, TeamMatchStat, parse_matches


class TestMatchSchema:
    def test_valid_match_parses(self):
        raw = {
            "id": 1001,
            "status": "completed",
            "home_team": {"id": 1, "name": "Brazil"},
            "away_team": {"id": 2, "name": "France"},
            "home_score": 2,
            "away_score": 1,
            "season": {"id": 1, "year": 2026},
            "has_extra_time": False,
            "has_penalty_shootout": False,
        }
        match = Match.model_validate(raw)
        assert match.id == 1001
        assert match.home_team.name == "Brazil"
        assert match.home_score == 2

    def test_missing_required_field_raises(self):
        raw = {"status": "completed"}  # missing 'id'
        with pytest.raises(ValidationError):
            Match.model_validate(raw)

    def test_nullable_fields_accept_none(self):
        raw = {"id": 1, "status": "scheduled"}
        match = Match.model_validate(raw)
        assert match.home_score is None
        assert match.away_score is None
        assert match.home_team is None


class TestOddsSchema:
    def test_valid_odds_parses(self):
        raw = {
            "id": 1,
            "match_id": 1001,
            "vendor": "fanduel",
            "moneyline_home_odds": -130,
            "moneyline_draw_odds": 260,
            "moneyline_away_odds": 340,
            "total_value": "2.5",
            "total_over_odds": 110,
            "total_under_odds": -140,
            "markets": [],
        }
        odds = Odds.model_validate(raw)
        assert odds.vendor == "fanduel"
        assert odds.moneyline_home_odds == -130

    def test_unknown_field_is_silently_ignored(self):
        raw = {
            "id": 1,
            "match_id": 1001,
            "vendor": "test",
            "UNKNOWN_NEW_FIELD": "surprise",
            "markets": [],
        }
        odds = Odds.model_validate(raw)
        assert odds.match_id == 1001


class TestMockProvider:
    def test_mock_matches_parse_successfully(self):
        from wc2026.data.providers.mock import MOCK_MATCHES
        matches = parse_matches(MOCK_MATCHES)
        assert len(matches) == len(MOCK_MATCHES)
        for m in matches:
            assert m.id > 0
            assert m.status in ("completed", "scheduled", "in_progress")
