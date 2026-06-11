"""
Calibration tests — temperature scaling on OOF predictions.

ACCEPTANCE:
- CalibrationMetrics must be computed on OOF predictions only.
- Temperature should be reported, even if T=1.0.
- All metrics must be finite and in valid ranges.
"""
import numpy as np
import pytest

from wc2026.calibration.score_pmf import (
    CalibrationMetrics,
    ScorePMFCalibrator,
    evaluate_pmf_predictions,
)
from wc2026.models.prediction import ScorePMFPrediction


def _make_test_predictions_and_actuals(n: int = 30):
    rng = np.random.default_rng(42)
    preds = []
    actuals = []
    for i in range(n):
        lam_h = rng.uniform(0.8, 2.0)
        lam_a = rng.uniform(0.8, 1.8)
        # Simple Poisson PMF
        from scipy.stats import poisson
        max_g = 10
        pmf = np.outer(
            poisson.pmf(np.arange(max_g), lam_h),
            poisson.pmf(np.arange(max_g), lam_a),
        )
        pmf /= pmf.sum()

        pred = ScorePMFPrediction(
            match_id=i,
            home_team="A",
            away_team="B",
            model_name="test",
            score_pmf=pmf,
            tail_mass=0.0,
            expected_home_goals=lam_h,
            expected_away_goals=lam_a,
        )
        preds.append(pred)
        actuals.append((int(rng.poisson(lam_h)), int(rng.poisson(lam_a))))
    return preds, actuals


class TestScorePMFCalibrator:
    def test_fits_temperature(self):
        preds, actuals = _make_test_predictions_and_actuals(30)
        cal = ScorePMFCalibrator()
        cal.fit(preds, actuals)
        assert 0.3 < cal.temperature < 3.0

    def test_transform_produces_valid_pmf(self):
        preds, actuals = _make_test_predictions_and_actuals(30)
        cal = ScorePMFCalibrator()
        cal.fit(preds, actuals)
        transformed = cal.transform(preds[0])
        total = float(transformed.score_pmf.sum()) + transformed.tail_mass
        assert abs(total - 1.0) < 1e-5

    def test_transform_without_fit_raises(self):
        preds, _ = _make_test_predictions_and_actuals(5)
        cal = ScorePMFCalibrator()
        with pytest.raises(RuntimeError, match="fit"):
            cal.transform(preds[0])

    def test_small_sample_defaults_to_temperature_one(self):
        preds, actuals = _make_test_predictions_and_actuals(3)
        cal = ScorePMFCalibrator()
        cal.fit(preds, actuals)
        assert cal.temperature == 1.0


class TestCalibrationMetrics:
    def test_all_metrics_are_finite(self):
        preds, actuals = _make_test_predictions_and_actuals(30)
        metrics = evaluate_pmf_predictions(preds, actuals, "test")
        assert np.isfinite(metrics.exact_score_log_loss)
        assert np.isfinite(metrics.rps_1x2)
        assert np.isfinite(metrics.brier_1x2)

    def test_rps_in_valid_range(self):
        preds, actuals = _make_test_predictions_and_actuals(30)
        metrics = evaluate_pmf_predictions(preds, actuals, "test")
        assert 0.0 <= metrics.rps_1x2 <= 1.0

    def test_brier_in_valid_range(self):
        preds, actuals = _make_test_predictions_and_actuals(30)
        metrics = evaluate_pmf_predictions(preds, actuals, "test")
        assert 0.0 <= metrics.brier_1x2 <= 2.0

    def test_exact_log_loss_positive(self):
        preds, actuals = _make_test_predictions_and_actuals(30)
        metrics = evaluate_pmf_predictions(preds, actuals, "test")
        assert metrics.exact_score_log_loss > 0

    def test_empty_input_returns_nan_metrics(self):
        metrics = evaluate_pmf_predictions([], [], "test")
        assert metrics.n_matches == 0
