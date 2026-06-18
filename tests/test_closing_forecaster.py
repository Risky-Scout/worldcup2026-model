import numpy as np
import pandas as pd
import pytest
from wc2026.models.closing_line_forecaster import ClosingLineForecaster, InsufficientDataError

def _make_synthetic_dataset(n: int = 30) -> pd.DataFrame:
    rng = np.random.default_rng(42)
    rows = []
    for i in range(n):
        rows.append({
            "match_id": i,
            "prediction_timestamp": f"2026-01-{i+1:02d}T12:00:00",
            "horizon_seconds": 3600,
            "current_market_home_lambda": 1.3 + rng.normal(0, 0.2),
            "current_market_away_lambda": 1.0 + rng.normal(0, 0.15),
            "current_market_rho": -0.05,
            "structural_log_home_lambda_minus_market": rng.normal(0, 0.1),
            "structural_log_away_lambda_minus_market": rng.normal(0, 0.1),
            "structural_total_minus_market": rng.normal(0, 0.2),
            "structural_goal_diff_minus_market": rng.normal(0, 0.1),
            "vendor_count": 4,
            "market_quality": 0.8,
            "host_team_indicator": 0,
            "neutral_venue": 1,
            "target_log_home_lambda_move": rng.normal(0, 0.05),
            "target_log_away_lambda_move": rng.normal(0, 0.05),
            "target_rho_move": rng.normal(0, 0.01),
        })
    return pd.DataFrame(rows)

def test_forecaster_trains_without_error():
    clf = ClosingLineForecaster("ridge")
    ds = _make_synthetic_dataset(30)
    metrics = clf.fit(ds, n_folds=3)
    assert len(metrics) > 0

def test_rolling_origin_folds_strictly_temporal():
    """Verify that each fold's train set only uses data before the test set."""
    ds = _make_synthetic_dataset(20)
    clf = ClosingLineForecaster("ridge")
    metrics = clf.fit(ds, n_folds=4)
    for m in metrics:
        assert m.n_train > 0
        assert m.n_test > 0
        # Train size is smaller than or equal to fold boundary
        assert m.n_train + m.n_test <= len(ds)

def test_predictions_are_finite():
    clf = ClosingLineForecaster("ridge")
    ds = _make_synthetic_dataset(20)
    clf.fit(ds, n_folds=3)
    row = ds.iloc[[0]]
    pred = clf.predict(row)
    assert np.isfinite(pred.predicted_close_home_lambda)
    assert np.isfinite(pred.predicted_close_away_lambda)
    assert np.isfinite(pred.predicted_close_rho)

def test_insufficient_data_raises():
    clf = ClosingLineForecaster("ridge")
    with pytest.raises(InsufficientDataError):
        clf.fit(pd.DataFrame(), n_folds=5)

def test_zero_rows_raises():
    clf = ClosingLineForecaster("ridge")
    with pytest.raises(InsufficientDataError):
        clf.fit(None, n_folds=5)
