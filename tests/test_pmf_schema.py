"""
Tests for ScorePMFPrediction — the core PMF schema.

These tests MUST pass for any model to be considered production-ready.
A failing test means a prediction cannot be published.
"""
import numpy as np
import pytest

from wc2026.models.prediction import (
    CalibrationStatus,
    DerivedMarkets,
    ScorePMFPrediction,
)

MAX_GOALS = 10


def _make_valid_pmf(max_goals: int = MAX_GOALS) -> np.ndarray:
    """Uniform PMF over a max_goals × max_goals grid."""
    pmf = np.ones((max_goals, max_goals), dtype=float)
    pmf /= pmf.sum()
    return pmf


def _make_prediction(**kwargs) -> ScorePMFPrediction:
    defaults = dict(
        match_id=1,
        home_team="Brazil",
        away_team="France",
        season=2026,
        stage="Group Stage",
        venue="MetLife Stadium",
        model_name="test_model",
        max_goals=MAX_GOALS,
        score_pmf=_make_valid_pmf(),
        tail_mass=0.0,
        expected_home_goals=1.4,
        expected_away_goals=1.2,
    )
    defaults.update(kwargs)
    return ScorePMFPrediction(**defaults)


class TestPMFConstraints:
    """ACCEPTANCE: Every PMF must satisfy these invariants."""

    def test_pmf_sums_to_one(self):
        pred = _make_prediction()
        total = float(pred.score_pmf.sum()) + pred.tail_mass
        assert abs(total - 1.0) < 1e-6, f"PMF sums to {total}, not 1.0"

    def test_pmf_no_negative_values(self):
        pred = _make_prediction()
        assert np.all(pred.score_pmf >= 0), "PMF contains negative probabilities"

    def test_pmf_is_2d(self):
        pred = _make_prediction()
        assert pred.score_pmf.ndim == 2

    def test_pmf_rejects_negative_input(self):
        bad_pmf = _make_valid_pmf()
        bad_pmf[0, 0] = -0.05
        with pytest.raises(ValueError, match="negative"):
            ScorePMFPrediction(
                match_id=1, home_team="A", away_team="B",
                model_name="bad", score_pmf=bad_pmf, tail_mass=0.0,
            )

    def test_pmf_rejects_bad_sum(self):
        bad_pmf = np.ones((MAX_GOALS, MAX_GOALS))  # sums to 100, not 1.0
        with pytest.raises(ValueError, match="sums to"):
            ScorePMFPrediction(
                match_id=1, home_team="A", away_team="B",
                model_name="bad", score_pmf=bad_pmf, tail_mass=0.0,
            )


class TestDerivedMarkets:
    """ACCEPTANCE: Derived markets must be consistent with the PMF."""

    def test_1x2_sums_to_one(self):
        pred = _make_prediction()
        dm = pred.derived_markets
        total = dm.home_win + dm.draw + dm.away_win
        assert abs(total - 1.0) < 1e-5, f"1X2 sums to {total}"

    def test_btts_sums_to_one(self):
        pred = _make_prediction()
        dm = pred.derived_markets
        assert abs(dm.btts_yes + dm.btts_no - 1.0) < 1e-5

    def test_totals_are_monotonic(self):
        pred = _make_prediction()
        dm = pred.derived_markets
        overs = [dm.over_0_5, dm.over_1_5, dm.over_2_5, dm.over_3_5,
                 dm.over_4_5, dm.over_5_5, dm.over_6_5]
        for i in range(len(overs) - 1):
            assert overs[i] >= overs[i + 1] - 1e-6, (
                f"Totals not monotonic: over_{i}_5={overs[i]:.4f} < over_{i+1}_5={overs[i+1]:.4f}"
            )

    def test_all_probabilities_in_range(self):
        pred = _make_prediction()
        dm = pred.derived_markets
        for attr, val in dm.__dict__.items():
            assert 0.0 <= val <= 1.0 + 1e-6, f"{attr}={val} out of [0,1]"

    def test_dc_1x_is_home_plus_draw(self):
        pred = _make_prediction()
        dm = pred.derived_markets
        expected = dm.home_win + dm.draw
        assert abs(dm.dc_1x - expected) < 1e-6

    def test_consistency_check_passes_for_valid_prediction(self):
        pred = _make_prediction()
        errors = pred.check_consistency()
        assert errors == [], f"Consistency errors: {errors}"


class TestMarketDerivation:
    """ACCEPTANCE: Markets must derive from PMF, not be computed independently."""

    def test_exact_score_sums_to_pmf(self):
        pred = _make_prediction()
        # Sum of all exact scores should equal pmf sum
        total = sum(
            pred.exact_score(h, a)
            for h in range(MAX_GOALS)
            for a in range(MAX_GOALS)
        )
        assert abs(total - float(pred.score_pmf.sum())) < 1e-5

    def test_top_scores_are_sorted_descending(self):
        pred = _make_prediction()
        scores = pred.top_scores(n=5)
        probs = [s["probability"] for s in scores]
        assert probs == sorted(probs, reverse=True)

    def test_home_win_matches_pmf_triangle(self):
        pred = _make_prediction()
        n = pred.score_pmf.shape[0]
        i, j = np.indices((n, n))
        expected = float(pred.score_pmf[i > j].sum())
        assert abs(pred.derived_markets.home_win - expected) < 1e-6


class TestCalibrationStatus:
    """Track calibration status correctly."""

    def test_default_status_is_uncalibrated(self):
        pred = _make_prediction()
        assert pred.calibration_status == CalibrationStatus.UNCALIBRATED

    def test_serialization_roundtrip(self):
        pred = _make_prediction()
        d = pred.to_dict()
        assert d["calibration_status"] == "uncalibrated"
        assert isinstance(d["score_pmf"], list)
        assert isinstance(d["derived_markets"], dict)
        assert len(d["top_scores"]) <= 15


class TestTailMass:
    """Tail mass warnings and PMF integrity."""

    def test_high_tail_mass_generates_warning(self):
        pmf = _make_valid_pmf()
        # Shrink the grid to put some mass in tail
        pmf = pmf * 0.97
        pred = ScorePMFPrediction(
            match_id=1, home_team="A", away_team="B",
            model_name="test", score_pmf=pmf, tail_mass=0.03,
        )
        assert any("tail" in w.lower() for w in pred.warnings), "Expected tail mass warning"

    def test_zero_tail_mass_no_warning(self):
        pred = _make_prediction(tail_mass=0.0)
        tail_warnings = [w for w in pred.warnings if "tail" in w.lower()]
        assert len(tail_warnings) == 0
