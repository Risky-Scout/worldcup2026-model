"""
Tests for no-vig conversion using penaltyblog.implied.

These validate that we are correctly stripping margin from American odds
and that the resulting probabilities sum to 1.0 (within tolerance).
"""
import pytest

from wc2026.markets.no_vig import (
    NoVigResult,
    american_to_decimal,
    strip_vig_1x2,
    strip_vig_total,
)


class TestAmericanToDecimal:
    def test_positive_american(self):
        assert abs(american_to_decimal(200) - 3.0) < 1e-6

    def test_negative_american(self):
        assert abs(american_to_decimal(-110) - 1.9091) < 1e-3

    def test_even_money(self):
        assert abs(american_to_decimal(100) - 2.0) < 1e-6


class TestStripVig1X2:
    """ACCEPTANCE: No-vig probabilities must sum to 1.0."""

    def test_1x2_probabilities_sum_to_one(self):
        result = strip_vig_1x2(-130, 260, 340, method="multiplicative")
        total = sum(result.probabilities)
        assert abs(total - 1.0) < 1e-5, f"Probs sum to {total}"

    def test_all_probabilities_positive(self):
        result = strip_vig_1x2(-150, 300, 350, method="multiplicative")
        for p in result.probabilities:
            assert p > 0

    def test_favourite_has_highest_probability(self):
        # Heavy favourite at -150 should have highest prob
        result = strip_vig_1x2(-150, 300, 350)
        assert result.home_win > result.draw
        assert result.home_win > result.away_win

    def test_returns_three_probabilities(self):
        result = strip_vig_1x2(-110, -110, 350)
        assert len(result.probabilities) == 3

    def test_margin_is_positive(self):
        result = strip_vig_1x2(-130, 260, 340)
        assert result.margin > 0

    @pytest.mark.parametrize("method", [
        "multiplicative", "additive", "power", "shin",
        "differential_margin_weighting", "odds_ratio", "logarithmic",
    ])
    def test_all_penaltyblog_methods_work(self, method):
        result = strip_vig_1x2(-130, 260, 340, method=method)
        total = sum(result.probabilities)
        assert abs(total - 1.0) < 1e-4, f"Method {method}: probs sum to {total}"
        assert all(p > 0 for p in result.probabilities)


class TestStripVigTotal:
    def test_total_probabilities_sum_to_one(self):
        over, under = strip_vig_total(-110, -110)
        assert abs(over + under - 1.0) < 1e-5

    def test_both_probabilities_positive(self):
        over, under = strip_vig_total(120, -150)
        assert over > 0
        assert under > 0

    def test_underdog_over_has_lower_probability(self):
        # over at +120 is the underdog; under at -150 is favoured
        over, under = strip_vig_total(120, -150)
        assert under > over
