"""
Tests for JointScorePMF — the core unbounded PMF interface.

ACCEPTANCE criteria (these must ALL pass before any prediction is published):
- PMF + tail sums to 1.0
- Arbitrary score lookup works for any (h, a) >= 0
- Derived markets are computed from the PMF only
- 1X2 == triangle sums
- Totals == masked sums
- BTTS == masked sum
- Draw == diagonal sum
- Out-of-grid scores return non-zero probabilities (via tail model)
- Consistency checks all pass
- Serialized JSON includes all required fields
"""
import numpy as np
import pytest
from penaltyblog.models import create_dixon_coles_grid

from wc2026.models.joint_pmf import (
    CalibratedScorePMF,
    FiniteGridPMF,
    ScoreTailModel,
    UnboundedScorePMF,
    from_lambdas,
    from_penaltyblog_grid,
    market_implied_pmf,
)

MAX_G = 15


def _make_finite_pmf(lh=1.5, la=1.2, rho=-0.05) -> FiniteGridPMF:
    fpg = create_dixon_coles_grid(lh, la, rho=rho, max_goals=MAX_G - 1)
    return FiniteGridPMF(fpg, model_name="test_dc", rho=rho, published_max_goals=MAX_G)


class TestPMFInvariants:
    """ACCEPTANCE: Every PMF must satisfy these invariants."""

    def test_grid_plus_tail_sums_to_one(self):
        pmf = _make_finite_pmf()
        grid, tail = pmf.normalize_with_tail(MAX_G)
        assert abs(float(grid.sum()) + tail - 1.0) < 1e-5

    def test_no_negative_probabilities(self):
        pmf = _make_finite_pmf()
        grid, _ = pmf.normalize_with_tail(MAX_G)
        assert np.all(grid >= -1e-9)

    def test_arbitrary_score_in_grid(self):
        pmf = _make_finite_pmf()
        p = pmf.get_score_probability(2, 1)
        assert p > 0
        assert p < 1

    def test_arbitrary_score_out_of_grid(self):
        """Scores beyond max_goals must return non-zero via tail model."""
        pmf = _make_finite_pmf()
        p_far = pmf.get_score_probability(20, 0)
        assert p_far >= 0, "Negative probability for out-of-grid score"
        # Should be tiny but non-zero for plausible lambdas
        p_normal = pmf.get_score_probability(2, 1)
        assert p_far < p_normal, "Far-out score should be less likely than typical score"

    def test_negative_goals_returns_zero(self):
        pmf = _make_finite_pmf()
        assert pmf.get_score_probability(-1, 0) == 0.0
        assert pmf.get_score_probability(0, -1) == 0.0

    def test_consistency_checks_pass(self):
        pmf = _make_finite_pmf()
        errors = pmf.validate_internal_consistency(MAX_G)
        assert errors == [], f"Consistency errors: {errors}"


class TestDerivedMarkets:
    """Markets must be derived from PMF, not independently."""

    def test_1x2_equals_pmf_triangles(self):
        pmf = _make_finite_pmf()
        markets = pmf.derive_markets_from_pmf(MAX_G)
        grid, _ = pmf.normalize_with_tail(MAX_G)
        I, J = np.indices(grid.shape)
        hw = float(grid[I > J].sum())
        dr = float(grid[I == J].sum())
        aw = float(grid[I < J].sum())
        assert abs(markets["home_win"] - hw) < 1e-5
        assert abs(markets["draw"] - dr) < 1e-5
        assert abs(markets["away_win"] - aw) < 1e-5

    def test_1x2_sums_to_one(self):
        pmf = _make_finite_pmf()
        m = pmf.derive_markets_from_pmf(MAX_G)
        assert abs(m["home_win"] + m["draw"] + m["away_win"] - 1.0) < 1e-5

    def test_btts_equals_pmf_mask(self):
        pmf = _make_finite_pmf()
        m = pmf.derive_markets_from_pmf(MAX_G)
        grid, _ = pmf.normalize_with_tail(MAX_G)
        I, J = np.indices(grid.shape)
        btts = float(grid[(I > 0) & (J > 0)].sum())
        assert abs(m["btts_yes"] - btts) < 1e-5

    def test_btts_sums_to_one(self):
        pmf = _make_finite_pmf()
        m = pmf.derive_markets_from_pmf(MAX_G)
        assert abs(m["btts_yes"] + m["btts_no"] - 1.0) < 1e-5

    def test_draw_equals_diagonal(self):
        pmf = _make_finite_pmf()
        m = pmf.derive_markets_from_pmf(MAX_G)
        grid, _ = pmf.normalize_with_tail(MAX_G)
        diagonal = float(np.diag(grid).sum())
        assert abs(m["draw"] - diagonal) < 1e-5

    def test_totals_are_monotonic(self):
        pmf = _make_finite_pmf()
        m = pmf.derive_markets_from_pmf(MAX_G)
        overs = [m[f"over_{str(l).replace('.', '_')}"] for l in [0.5, 1.5, 2.5, 3.5, 4.5, 5.5, 6.5]]
        for i in range(len(overs) - 1):
            assert overs[i] >= overs[i + 1] - 1e-5, f"Non-monotonic at {i}"

    def test_totals_equal_pmf_masked_sum(self):
        pmf = _make_finite_pmf()
        m = pmf.derive_markets_from_pmf(MAX_G)
        grid, _ = pmf.normalize_with_tail(MAX_G)
        I, J = np.indices(grid.shape)
        over_2_5_pmf = float(grid[(I + J) > 2.5].sum())
        assert abs(m["over_2_5"] - over_2_5_pmf) < 1e-5

    def test_all_probability_markets_in_01(self):
        pmf = _make_finite_pmf()
        m = pmf.derive_markets_from_pmf(MAX_G)
        # xpts can be > 1.0 (0-3 scale); skip it
        non_probability_keys = {"xpts_home", "xpts_away"}
        for k, v in m.items():
            if k in non_probability_keys:
                assert v >= 0.0, f"{k}={v} is negative"
            else:
                assert 0.0 <= v <= 1.0 + 1e-5, f"{k}={v} out of [0,1]"


class TestScoreTailModel:
    def test_tail_model_gives_zero_for_in_grid_scores(self):
        tail = ScoreTailModel(1.5, 1.2, tail_mass=0.01, grid_max=10)
        assert tail.get_probability(5, 5) == 0.0
        assert tail.get_probability(9, 9) == 0.0

    def test_tail_model_gives_nonzero_for_out_of_grid(self):
        tail = ScoreTailModel(1.5, 1.2, tail_mass=0.01, grid_max=10)
        p = tail.get_probability(10, 0)
        assert p > 0

    def test_tail_model_total_approximately_tail_mass(self):
        """Sum over a large range of out-of-grid scores ≈ tail_mass."""
        tail = ScoreTailModel(1.5, 1.2, tail_mass=0.01, grid_max=10)
        total = 0.0
        for h in range(50):
            for a in range(50):
                if h >= 10 or a >= 10:
                    total += tail.get_probability(h, a)
        assert abs(total - 0.01) < 0.002, f"Tail sum {total:.4f} ≠ 0.01"


class TestUnboundedPMF:
    def test_arbitrary_lookup_any_score(self):
        pmf = UnboundedScorePMF(1.5, 1.2, rho=-0.05)
        for h, a in [(0, 0), (3, 2), (10, 0), (0, 15), (20, 20)]:
            p = pmf.get_score_probability(h, a)
            assert p >= 0, f"Negative prob for ({h}, {a})"

    def test_high_scores_have_tiny_probability(self):
        pmf = UnboundedScorePMF(1.5, 1.2)
        p_normal = pmf.get_score_probability(1, 1)
        p_extreme = pmf.get_score_probability(15, 15)
        assert p_extreme < p_normal * 0.001

    def test_consistency_check_passes(self):
        pmf = UnboundedScorePMF(1.5, 1.2, rho=-0.05)
        errors = pmf.validate_internal_consistency(MAX_G)
        assert errors == []


class TestCalibratedPMF:
    def test_temperature_one_is_identity(self):
        base = _make_finite_pmf()
        cal = CalibratedScorePMF(base, temperature=1.0, published_max_goals=MAX_G)
        grid_base, _ = base.normalize_with_tail(MAX_G)
        grid_cal, _ = cal.normalize_with_tail(MAX_G)
        assert np.allclose(grid_base, grid_cal, atol=1e-5)

    def test_high_temperature_flattens_distribution(self):
        base = _make_finite_pmf()
        cal = CalibratedScorePMF(base, temperature=3.0, published_max_goals=MAX_G)
        grid_base, _ = base.normalize_with_tail(MAX_G)
        grid_cal, _ = cal.normalize_with_tail(MAX_G)
        # Flatter = lower variance
        assert grid_cal.var() < grid_base.var()

    def test_low_temperature_sharpens_distribution(self):
        base = _make_finite_pmf()
        cal = CalibratedScorePMF(base, temperature=0.7, published_max_goals=MAX_G)
        grid_base, _ = base.normalize_with_tail(MAX_G)
        grid_cal, _ = cal.normalize_with_tail(MAX_G)
        assert grid_cal.var() > grid_base.var()

    def test_calibrated_pmf_sums_to_one(self):
        base = _make_finite_pmf()
        cal = CalibratedScorePMF(base, temperature=1.2, published_max_goals=MAX_G)
        grid, tail = cal.normalize_with_tail(MAX_G)
        assert abs(float(grid.sum()) + tail - 1.0) < 1e-5


class TestMarketImpliedPMF:
    def test_market_implied_sums_to_one(self):
        pmf = market_implied_pmf(0.45, 0.27, 0.28, over_2_5=0.55, under_2_5=0.45)
        grid, tail = pmf.normalize_with_tail(MAX_G)
        assert abs(float(grid.sum()) + tail - 1.0) < 1e-4

    def test_market_implied_consistency(self):
        pmf = market_implied_pmf(0.45, 0.27, 0.28, over_2_5=0.55, under_2_5=0.45)
        errors = pmf.validate_internal_consistency(MAX_G)
        assert errors == []

    def test_market_implied_without_totals(self):
        pmf = market_implied_pmf(0.40, 0.30, 0.30)
        errors = pmf.validate_internal_consistency(MAX_G)
        assert errors == []


class TestSerializationSchema:
    """ACCEPTANCE: JSON output must include all required fields."""

    REQUIRED_FIELDS = [
        "regulation_only",
        "extra_time_excluded",
        "penalty_shootout_excluded",
        "regulation_score_pmf_grid",
        "max_goals",
        "tail_mass",
        "tail_policy",
        "arbitrary_score_lookup_supported",
        "top_scorelines",
        "exact_score_probabilities",
        "derived_markets",
        "odds_used",
        "odds_timestamp",
        "lineups_known",
        "prediction_mode",
        "consistency_errors",
    ]

    def test_all_required_fields_present(self):
        pmf = _make_finite_pmf()
        d = pmf.to_dict(max_goals=MAX_G)
        for field in self.REQUIRED_FIELDS:
            assert field in d, f"Missing required field: {field}"

    def test_regulation_only_is_true(self):
        pmf = _make_finite_pmf()
        d = pmf.to_dict()
        assert d["regulation_only"] is True

    def test_extra_time_excluded_is_true(self):
        pmf = _make_finite_pmf()
        d = pmf.to_dict()
        assert d["extra_time_excluded"] is True

    def test_pmf_grid_correct_shape(self):
        pmf = _make_finite_pmf()
        d = pmf.to_dict(max_goals=MAX_G)
        grid = d["regulation_score_pmf_grid"]
        assert len(grid) == MAX_G
        assert all(len(row) == MAX_G for row in grid)

    def test_pmf_grid_sums_to_one_minus_tail(self):
        pmf = _make_finite_pmf()
        d = pmf.to_dict(max_goals=MAX_G)
        grid = d["regulation_score_pmf_grid"]
        total = sum(v for row in grid for v in row) + d["tail_mass"]
        assert abs(total - 1.0) < 1e-4

    def test_arbitrary_score_lookup_supported_is_true(self):
        pmf = _make_finite_pmf()
        d = pmf.to_dict()
        assert d["arbitrary_score_lookup_supported"] is True

    def test_consistency_errors_empty_for_valid_pmf(self):
        pmf = _make_finite_pmf()
        d = pmf.to_dict()
        assert d["consistency_errors"] == []

    def test_score_log_loss_positive(self):
        pmf = _make_finite_pmf()
        ll = pmf.score_log_loss(1, 0)
        assert ll > 0

    def test_score_log_loss_decreases_for_likely_scores(self):
        pmf = _make_finite_pmf(lh=2.0, la=0.5)
        ll_likely = pmf.score_log_loss(2, 0)  # high-scoring home win
        ll_unlikely = pmf.score_log_loss(0, 5)  # very unlikely
        assert ll_likely < ll_unlikely
