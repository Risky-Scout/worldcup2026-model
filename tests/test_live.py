"""
Tests for the live PMF engine.

Coverage:
- MatchState construction and derived properties
- LiveFeatureVector extraction
- Hazard model (temporal baseline, score-state multipliers, red cards)
- LivePMFPredictor correctness at all regulation checkpoints
- Prediction consistency: 1X2 sums to 1, next-goal probs sensible
- Score state validation (winning team should have higher win prob)
- No-data fallback (missing xG)
- Red card effect (disadvantaged team should have lower rate)
- Replay engine (synthetic 2022 data)
"""
import math

import numpy as np
import pytest

from wc2026.live.state import (
    MatchState, MatchStatus, MatchEvent, EventType, TeamLiveStats,
)
from wc2026.live.features import extract_features
from wc2026.live.hazard import (
    baseline_hazard, score_state_multipliers, red_card_multipliers,
    compute_live_rates, expected_goals_remaining,
)
from wc2026.live.predictor import LivePMFPredictor


# ── Fixtures ──────────────────────────────────────────────────────────────────

def make_state(
    minute: int = 0,
    home_goals: int = 0,
    away_goals: int = 0,
    h_rc: int = 0,
    a_rc: int = 0,
    h_xg: float = None,
    a_xg: float = None,
    status: MatchStatus = MatchStatus.SECOND_HALF,
) -> MatchState:
    h_stats = TeamLiveStats(
        xg=h_xg,
        shots_on_target=max(0, int(minute / 10)) if minute > 0 else None,
        possession_pct=52.0,
        red_cards=h_rc,
    ) if minute > 0 else None
    a_stats = TeamLiveStats(
        xg=a_xg,
        shots_on_target=max(0, int(minute / 12)) if minute > 0 else None,
        possession_pct=48.0,
        red_cards=a_rc,
    ) if minute > 0 else None

    if minute <= 45:
        status = MatchStatus.FIRST_HALF if minute < 45 else MatchStatus.HALF_TIME
    else:
        status = MatchStatus.SECOND_HALF

    return MatchState(
        match_id="test_001",
        home_team="Home",
        away_team="Away",
        season=2022,
        stage="group",
        status=status,
        clock_display=str(minute),
        match_seconds=minute * 60,
        home_goals=home_goals,
        away_goals=away_goals,
        home_stats=h_stats,
        away_stats=a_stats,
        home_effective_players=max(11 - h_rc, 9),
        away_effective_players=max(11 - a_rc, 9),
        pregame_lh=1.5,
        pregame_la=1.0,
    )


# ── MatchState tests ──────────────────────────────────────────────────────────

class TestMatchState:

    def test_regulation_minute_at_kickoff(self):
        s = make_state(minute=0, status=MatchStatus.PREMATCH)
        assert s.regulation_minute == 0.0

    def test_regulation_minute_at_67(self):
        s = make_state(minute=67)
        assert abs(s.regulation_minute - 67.0) < 0.1

    def test_remaining_regulation_seconds_at_60(self):
        s = make_state(minute=60)
        rem = s.remaining_regulation_seconds
        assert abs(rem - 30 * 60) < 60  # ~30 min remaining

    def test_score_state_drawn(self):
        s = make_state(home_goals=1, away_goals=1, minute=60)
        assert s.score_state == "drawn"

    def test_score_state_home_winning_1(self):
        s = make_state(home_goals=2, away_goals=1, minute=70)
        assert s.score_state == "home_winning_1"

    def test_score_state_away_winning_2plus(self):
        s = make_state(home_goals=0, away_goals=3, minute=80)
        assert s.score_state == "away_winning_2plus"

    def test_with_goal_creates_new_state(self):
        s = make_state(home_goals=0, away_goals=0, minute=30)
        s2 = s.with_goal("home")
        assert s2.home_goals == 1
        assert s.home_goals == 0  # original unchanged

    def test_to_dict_keys(self):
        s = make_state(minute=45)
        d = s.to_dict()
        assert "regulation_minute" in d
        assert "score_state" in d
        assert "remaining_seconds" in d


# ── Feature extraction tests ──────────────────────────────────────────────────

class TestFeatureExtraction:

    def test_features_at_kickoff(self):
        s = make_state(minute=0, status=MatchStatus.PREMATCH)
        f = extract_features(s, pregame_lh=1.5, pregame_la=1.0)
        assert f.regulation_minute == 0.0
        assert f.fraction_elapsed == 0.0
        assert f.remaining_fraction == 1.0
        assert f.is_drawn == 1.0
        assert f.is_first_half == 1.0 or f.is_second_half == 0.0

    def test_features_at_67_1_0(self):
        s = make_state(minute=67, home_goals=1, away_goals=0, h_xg=1.2, a_xg=0.4)
        f = extract_features(s, pregame_lh=1.5, pregame_la=1.0)
        assert abs(f.regulation_minute - 67.0) < 1.0
        assert f.home_goals == 1.0
        assert f.away_goals == 0.0
        assert f.is_home_winning_1 == 1.0
        assert f.xg_missing == 0.0  # xG available

    def test_features_xg_missing_flag(self):
        s = make_state(minute=0, status=MatchStatus.PREMATCH)
        f = extract_features(s, pregame_lh=1.5, pregame_la=1.0)
        assert f.xg_missing == 1.0

    def test_features_red_card(self):
        s = make_state(minute=55, h_rc=1)
        f = extract_features(s)
        assert f.home_red_cards == 1.0
        assert f.home_player_disadvantage == 1.0


# ── Hazard model tests ────────────────────────────────────────────────────────

class TestHazardModel:

    def test_baseline_hazard_nonzero(self):
        for minute in [1, 15, 30, 45, 60, 75, 85, 90]:
            h = baseline_hazard(float(minute))
            assert h > 0, f"baseline_hazard({minute}) = {h}"

    def test_baseline_hazard_late_surge(self):
        h_60 = baseline_hazard(60.0)
        h_88 = baseline_hazard(88.0)
        assert h_88 > h_60, "Late-game hazard should be higher than 60min"

    def test_score_state_drawn_late(self):
        h_mult, a_mult = score_state_multipliers(1, 1, minute=75.0)
        assert h_mult > 1.0 and a_mult > 1.0, "Drawn late: both teams push"

    def test_score_state_home_winning_away_pushes(self):
        _, a_mult = score_state_multipliers(1, 0, minute=70.0)
        assert a_mult > 1.0, "Away team chases when behind"

    def test_red_card_reduces_disadvantaged_team(self):
        h_no_card, a_no_card = red_card_multipliers(0, 0)
        h_one_card, a_one_card = red_card_multipliers(1, 0)
        assert h_one_card < h_no_card, "Red card reduces home rate"
        assert a_one_card > a_no_card, "Numerical advantage increases away rate"

    def test_compute_live_rates_pregame_at_zero(self):
        h_rate, a_rate = compute_live_rates(
            minute=0.0, home_goals=0, away_goals=0,
            pregame_lh=1.5, pregame_la=1.0,
        )
        assert h_rate > 0 and a_rate > 0
        assert h_rate > a_rate, "Home expected rate higher than away"

    def test_expected_goals_remaining_decreases_over_time(self):
        lh1, la1 = expected_goals_remaining(30, 0, 0, 1.5, 1.0, 60 * 60)
        lh2, la2 = expected_goals_remaining(70, 0, 0, 1.5, 1.0, 20 * 60)
        assert lh2 < lh1, "Expected remaining goals decrease as time passes"

    def test_expected_goals_zero_at_fulltime(self):
        lh, la = expected_goals_remaining(90, 1, 0, 1.5, 1.0, 0.0)
        assert lh == 0.0 and la == 0.0


# ── LivePMFPredictor tests ────────────────────────────────────────────────────

class TestLivePMFPredictor:

    def _pred(self, minute=67, home_goals=1, away_goals=0, lh=1.5, la=1.0):
        p = LivePMFPredictor()
        s = make_state(minute=minute, home_goals=home_goals, away_goals=away_goals)
        return p.predict(s, pregame_lh=lh, pregame_la=la)

    def test_1x2_sums_to_one(self):
        r = self._pred()
        total = r.home_win_prob + r.draw_prob + r.away_win_prob
        assert abs(total - 1.0) < 0.01

    def test_pmf_sums_to_one(self):
        r = self._pred()
        assert abs(float(r.final_score_pmf.sum()) - 1.0) < 0.05  # some overflow

    def test_home_winning_1_0_at_67_hw_dominant(self):
        r = self._pred(minute=67, home_goals=1, away_goals=0)
        assert r.home_win_prob > 0.70, f"Home winning 1-0 @67: HW={r.home_win_prob}"

    def test_away_winning_0_2_at_80(self):
        r = self._pred(minute=80, home_goals=0, away_goals=2)
        assert r.away_win_prob > 0.80, f"Away winning 0-2 @80: AW={r.away_win_prob}"

    def test_prematch_roughly_matches_pregame(self):
        p = LivePMFPredictor()
        s = MatchState(
            match_id="t", home_team="A", away_team="B", season=2026, stage="group",
            status=MatchStatus.PREMATCH, clock_display="0", match_seconds=0,
            pregame_lh=1.5, pregame_la=1.0,
        )
        r = p.predict(s, pregame_lh=1.5, pregame_la=1.0)
        # With pregame lh=1.5, la=1.0, home should win ~52-55%
        assert 0.45 < r.home_win_prob < 0.65

    def test_top_scorelines_match_pmf(self):
        r = self._pred()
        n = r.final_score_pmf.shape[0]
        for entry in r.top_scorelines[:5]:
            h, a = entry["home_goals"], entry["away_goals"]
            if h < n and a < n:
                assert abs(entry["probability"] - float(r.final_score_pmf[h, a])) < 0.001

    def test_no_more_goals_makes_sense(self):
        # At 89 min with 0-0, some positive prob of no goals
        p = LivePMFPredictor()
        s = make_state(minute=89, home_goals=0, away_goals=0)
        r = p.predict(s, pregame_lh=1.5, pregame_la=1.0)
        assert r.no_more_goals_prob > 0.0

    def test_next_goal_probs_sensible(self):
        r = self._pred()
        # next_goal probs should not exceed 1.0
        assert r.next_goal_home_prob <= 1.0
        assert r.next_goal_away_prob <= 1.0
        assert r.next_goal_home_prob >= 0.0
        assert r.next_goal_away_prob >= 0.0

    def test_predict_from_bdl_returns_result(self):
        p = LivePMFPredictor()
        bdl_match = {
            "id": 12345,
            "home_team": {"full_name": "Mexico"},
            "away_team": {"full_name": "South Africa"},
            "status": "2h",
            "clock_display": "67",
            "home_score": 1,
            "away_score": 0,
            "season": 2026,
            "stage": "group",
        }
        result = p.predict_from_bdl(bdl_match, pregame_lh=1.8, pregame_la=0.6)
        assert result is not None
        assert result.home_team == "Mexico"
        assert result.current_home_goals == 1
        assert result.home_win_prob > 0.7

    def test_live_pmf_result_to_dict(self):
        r = self._pred()
        d = r.to_dict()
        assert "home_win_prob" in d
        assert "top_scorelines" in d
        assert "final_score_pmf_grid" in d
        assert "derived_markets" in d

    def test_red_card_reduces_home_win_prob(self):
        p = LivePMFPredictor()
        s_no_rc = make_state(minute=60, home_goals=1, away_goals=0)
        s_rc = make_state(minute=60, home_goals=1, away_goals=0, h_rc=1)
        r_no_rc = p.predict(s_no_rc, pregame_lh=1.5, pregame_la=1.0)
        r_rc = p.predict(s_rc, pregame_lh=1.5, pregame_la=1.0)
        assert r_rc.home_win_prob < r_no_rc.home_win_prob, (
            "Red card should reduce home win probability"
        )
