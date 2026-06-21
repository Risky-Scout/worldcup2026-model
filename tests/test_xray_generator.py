"""
Tests for Market X-Ray generator functions.
Imports core functions directly from scripts/generate_xray.py.
"""
import importlib.util
import sys
import math
from datetime import datetime, timezone, timedelta
from pathlib import Path

# ── Import generate_xray module by path ──────────────────────────────────────
REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT_PATH = REPO_ROOT / "scripts" / "generate_xray.py"

spec = importlib.util.spec_from_file_location("generate_xray", SCRIPT_PATH)
gx = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gx)


# ── Math helpers ─────────────────────────────────────────────────────────────

class TestAmericanToDecimal:
    def test_positive_odds(self):
        result = gx.american_to_decimal(100)
        assert abs(result - 2.0) < 1e-9

    def test_negative_odds(self):
        result = gx.american_to_decimal(-110)
        assert abs(result - (1 + 100/110)) < 1e-6, f"Got {result}"

    def test_plus_200(self):
        assert abs(gx.american_to_decimal(200) - 3.0) < 1e-9


class TestProbToAmerican:
    def test_favorite(self):
        # p=0.55 → -100*0.55/0.45 = -122.2 → -122
        result = gx.prob_to_american(0.55)
        assert result == -122, f"Expected -122, got {result}"

    def test_underdog(self):
        # p=0.40 → 100*0.60/0.40 = 150
        result = gx.prob_to_american(0.40)
        assert result == 150, f"Expected 150, got {result}"

    def test_even(self):
        result = gx.prob_to_american(0.5)
        assert result == -100

    def test_boundary_zero(self):
        assert gx.prob_to_american(0) == 0
        assert gx.prob_to_american(1) == 0


class TestDecimalToAmerican:
    def test_plus_100(self):
        assert gx.decimal_to_american(2.0) == 100

    def test_favorite(self):
        # decimal 1.909... → -100/(0.909) ≈ -110
        result = gx.decimal_to_american(1 + 100/110)
        assert result == -110, f"Expected -110, got {result}"


class TestCalculateEV:
    def test_positive_ev(self):
        # calculate_ev(0.55, 1.9) = 0.55*0.9*100 - 0.45*100 = 49.5 - 45.0 = 4.5
        result = gx.calculate_ev(0.55, 1.9)
        assert abs(result - 4.5) < 1e-6, f"Expected 4.5, got {result}"

    def test_negative_ev(self):
        # calculate_ev(0.40, 1.9) = 0.40*0.9*100 - 0.60*100 = 36 - 60 = -24
        result = gx.calculate_ev(0.40, 1.9)
        assert abs(result - (-24.0)) < 1e-6, f"Expected -24.0, got {result}"

    def test_break_even(self):
        # At fair price, EV ≈ 0; fair decimal for p=0.55 is 1/0.55 ≈ 1.818
        result = gx.calculate_ev(0.55, 1/0.55)
        assert abs(result) < 0.1, f"Expected ~0, got {result}"


class TestConfidenceGrade:
    def test_grade_A(self):
        assert gx.confidence_grade(5.5, "LOW") == "A"

    def test_grade_B_edge(self):
        assert gx.confidence_grade(3.5) == "B"

    def test_grade_C(self):
        assert gx.confidence_grade(2.0) == "C"

    def test_grade_D(self):
        assert gx.confidence_grade(0.5) == "D"

    def test_A_requires_low_uncertainty(self):
        assert gx.confidence_grade(6.0, "MEDIUM") == "B"


class TestPregameAction:
    def test_bet(self):
        assert gx.pregame_action(4.5) == "BET"

    def test_small_bet(self):
        assert gx.pregame_action(3.0) == "SMALL BET"

    def test_lean(self):
        assert gx.pregame_action(1.5) == "LEAN"

    def test_pass(self):
        assert gx.pregame_action(0.5) == "PASS"

    def test_do_not_chase(self):
        # Previous edge was 5.0, now dropped to 3.0 (dropped > 0.5)
        assert gx.pregame_action(3.0, prev_edge_pp=5.0) == "DO NOT CHASE"

    def test_no_chase_if_small_drop(self):
        # Drop of only 0.3 pp — not enough to trigger DO NOT CHASE
        assert gx.pregame_action(3.0, prev_edge_pp=3.3) == "SMALL BET"


class TestLiveAction:
    def test_bet(self):
        assert gx.live_action(6.5) == "BET"

    def test_small_bet(self):
        assert gx.live_action(5.0) == "SMALL BET"

    def test_lean(self):
        assert gx.live_action(3.0) == "LEAN"

    def test_pass(self):
        assert gx.live_action(1.0) == "PASS"

    def test_staleness_pmf_cap(self):
        # PMF older than 7 minutes → max action = WAIT
        action = gx.live_action(7.0, pmf_age_min=8.0)
        assert action == "WAIT", f"Expected WAIT (stale PMF), got {action}"

    def test_staleness_odds_cap(self):
        # Odds older than 90 seconds → WAIT
        action = gx.live_action(7.0, odds_age_sec=100.0)
        assert action == "WAIT", f"Expected WAIT (stale odds), got {action}"

    def test_do_not_chase_live(self):
        assert gx.live_action(3.0, prev_edge_pp=5.0) == "DO NOT CHASE"


class TestCLVSignals:
    def test_beat_close_null_when_no_closing_timestamp(self):
        """beat_close should be None when closing_timestamp is null."""
        clv_index = {
            ("42", "home_win"): {
                "match_id": "42",
                "market": "home_win",
                "model_prob": 0.55,
                "model_fair_odds": 1.818,
                "prediction_timestamp": "2026-06-20T10:00:00Z",
                "closing_timestamp": None,
                "closing_source": None,
            }
        }
        markets = [{
            "market_id": "home_win",
            "market_label": "Home Win (1X2)",
            "model_probability": 0.55,
            "model_fair_american": -122,
            "market_odds_american": -110,
            "market_no_vig_probability": 0.52,
            "edge_pp": 3.0,
            "ev_per_100": 4.5,
            "confidence": "B",
            "action": "SMALL BET",
            "trader_note": "...",
        }]
        signals = gx.build_clv_signals("42", markets, clv_index)
        assert len(signals) == 1
        assert signals[0]["beat_close"] is None
        assert signals[0]["closing_timestamp"] is None

    def test_signal_not_included_when_no_record(self):
        """No CLV signal if record doesn't exist."""
        signals = gx.build_clv_signals("99", [{"market_id": "draw", "market_label": "Draw"}], {})
        assert signals == []


class TestDerivedMarketConsistency:
    """Test that a simple mock PMF gives consistent 1X2 probabilities summing to 1."""

    def test_1x2_sums_to_one(self):
        # Create a tiny 5x5 PMF grid summing to 1.0
        grid = [[0.0] * 5 for _ in range(5)]
        # P(0-0)=0.12, P(1-0)=0.20, P(0-1)=0.15, P(1-1)=0.18, P(2-0)=0.10
        # P(0-2)=0.08, P(2-1)=0.07, P(1-2)=0.06, P(2-2)=0.04
        probs = {(0,0):0.12,(1,0):0.20,(0,1):0.15,(1,1):0.18,(2,0):0.10,
                 (0,2):0.08,(2,1):0.07,(1,2):0.06,(2,2):0.04}
        total = sum(probs.values())  # = 1.0
        for (h,a), p in probs.items():
            grid[h][a] = p

        # Derive 1X2 from the grid
        home_win = sum(grid[h][a] for h in range(5) for a in range(5) if h > a)
        draw     = sum(grid[h][a] for h in range(5) for a in range(5) if h == a)
        away_win = sum(grid[h][a] for h in range(5) for a in range(5) if a > h)

        assert abs(home_win + draw + away_win - 1.0) < 1e-6, \
            f"1X2 probs sum to {home_win + draw + away_win}, expected ~1.0"


class TestTraderNote:
    def test_bet_note_contains_key_phrases(self):
        note = gx.generate_trader_note(
            market_type="home_win",
            selection="Germany ML",
            model_prob=0.584,
            market_odds_american=-118,
            edge_pp=4.3,
            action="BET",
            ev_per_100=7.1,
            mode="pregame",
        )
        assert "Model fair:" in note
        assert "Edge:" in note
        assert "+4.3" in note
        assert "pregame" in note

    def test_do_not_chase_note(self):
        note = gx.generate_trader_note(
            market_type="over_2_5",
            selection="Over 2.5",
            model_prob=0.55,
            market_odds_american=-115,
            edge_pp=1.5,
            action="DO NOT CHASE",
            ev_per_100=None,
            mode="live",
        )
        assert "deteriorating" in note.lower() or "decreased" in note.lower()

    def test_pass_note(self):
        note = gx.generate_trader_note(
            market_type="draw",
            selection="Draw",
            model_prob=0.30,
            market_odds_american=None,
            edge_pp=0.3,
            action="PASS",
            ev_per_100=None,
            mode="pregame",
        )
        assert "No material edge" in note


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
