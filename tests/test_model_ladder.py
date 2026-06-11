"""
Integration tests for the ModelLadder.

Uses MockProvider data — no BDL API calls.
These tests verify that all Tier 1 penaltyblog models can be fitted and
produce valid ScorePMFPrediction outputs.
"""
import numpy as np
import pandas as pd
import pytest

from wc2026.data.dataset import DatasetBuilder
from wc2026.data.providers.mock import MockProvider
from wc2026.models.ladder import (
    MODEL_BIVARIATE,
    MODEL_DIXON_COLES,
    MODEL_NEG_BINOMIAL,
    MODEL_POISSON,
    MODEL_WEIBULL,
    MODEL_ZERO_INF,
    ModelLadder,
)
from wc2026.models.prediction import ScorePMFPrediction


def _make_training_data() -> pd.DataFrame:
    """Build minimal training DataFrame from mock fixtures."""
    # Expand mock data to get a usable training set
    import datetime as dt

    rows = []
    teams = ["Brazil", "France", "Germany", "Argentina", "England", "Spain", "Netherlands", "Portugal"]
    base_date = dt.datetime(2022, 11, 20, tzinfo=dt.timezone.utc)
    scores = [(2, 1), (0, 0), (3, 2), (1, 1), (0, 2), (1, 0), (2, 0), (0, 1),
              (3, 0), (1, 2), (0, 0), (2, 2), (4, 1), (0, 3), (1, 1), (2, 1)]

    for i, (h, a) in enumerate(scores):
        home = teams[i % len(teams)]
        away = teams[(i + 1) % len(teams)]
        rows.append({
            "match_id": i + 1,
            "home_team": home,
            "away_team": away,
            "home_goals": h,
            "away_goals": a,
            "is_neutral": 1,
            "match_weight": 0.9 ** (len(scores) - i),
            "match_datetime": base_date + dt.timedelta(days=i),
            "season": 2022,
            "stage": "Group Stage",
            "status": "completed",
        })
    return pd.DataFrame(rows)


@pytest.fixture(scope="module")
def training_df() -> pd.DataFrame:
    return _make_training_data()


@pytest.fixture(scope="module")
def fitted_ladder(training_df) -> ModelLadder:
    ladder = ModelLadder(
        training_df,
        max_goals=10,
        include_bayesian=False,  # Skip slow Bayesian for unit tests
    )
    # Fit Tier 1 only for speed
    ladder.fit([MODEL_POISSON, MODEL_DIXON_COLES, MODEL_BIVARIATE])
    return ladder


class TestModelLadderFit:
    def test_fits_without_error(self, fitted_ladder):
        assert fitted_ladder.fitted

    def test_returns_fitted_models(self, fitted_ladder):
        models = fitted_ladder.fitted_models()
        assert MODEL_POISSON in models
        assert MODEL_DIXON_COLES in models

    def test_rejects_too_few_matches(self):
        tiny_df = _make_training_data().head(2)
        with pytest.raises(ValueError, match="at least 3"):
            ModelLadder(tiny_df).fit()


class TestModelPredictions:
    """ACCEPTANCE: Every model must produce a valid ScorePMFPrediction."""

    def test_prediction_is_correct_type(self, fitted_ladder):
        pred = fitted_ladder.predict(MODEL_DIXON_COLES, "Brazil", "France")
        assert isinstance(pred, ScorePMFPrediction)

    def test_pmf_sums_to_one(self, fitted_ladder):
        for model_name in fitted_ladder.fitted_models():
            pred = fitted_ladder.predict(model_name, "Brazil", "France")
            total = float(pred.score_pmf.sum()) + pred.tail_mass
            assert abs(total - 1.0) < 1e-4, f"{model_name}: PMF sums to {total}"

    def test_pmf_no_negative_values(self, fitted_ladder):
        for model_name in fitted_ladder.fitted_models():
            pred = fitted_ladder.predict(model_name, "Brazil", "France")
            assert np.all(pred.score_pmf >= 0), f"{model_name}: negative PMF values"

    def test_derived_markets_1x2_sums_to_one(self, fitted_ladder):
        for model_name in fitted_ladder.fitted_models():
            pred = fitted_ladder.predict(model_name, "Brazil", "France")
            dm = pred.derived_markets
            total = dm.home_win + dm.draw + dm.away_win
            assert abs(total - 1.0) < 1e-4, f"{model_name}: 1X2 sums to {total}"

    def test_consistency_check_passes(self, fitted_ladder):
        for model_name in fitted_ladder.fitted_models():
            pred = fitted_ladder.predict(model_name, "Brazil", "France")
            errors = pred.check_consistency()
            assert errors == [], f"{model_name}: {errors}"

    def test_predict_unknown_model_raises(self, fitted_ladder):
        with pytest.raises(ValueError, match="not fitted"):
            fitted_ladder.predict("nonexistent_model", "Brazil", "France")

    def test_predict_all_returns_dict(self, fitted_ladder):
        preds = fitted_ladder.predict_all("Brazil", "France")
        assert isinstance(preds, dict)
        assert len(preds) > 0
        for name, pred in preds.items():
            assert isinstance(pred, ScorePMFPrediction)


class TestBaselines:
    def test_equal_probability_baseline(self):
        from wc2026.models.baselines import EqualProbabilityBaseline
        bl = EqualProbabilityBaseline()
        pred = bl.predict("Brazil", "France")
        assert abs(pred.score_pmf.sum() + pred.tail_mass - 1.0) < 1e-5
        assert abs(pred.derived_markets.home_win - pred.derived_markets.away_win) < 0.01

    def test_historical_base_rate_baseline(self, training_df):
        from wc2026.models.baselines import HistoricalBaseRateBaseline
        bl = HistoricalBaseRateBaseline().fit(training_df)
        pred = bl.predict("Brazil", "France")
        assert abs(pred.score_pmf.sum() + pred.tail_mass - 1.0) < 1e-5

    def test_elo_baseline(self, training_df):
        from wc2026.models.baselines import EloBaseline
        bl = EloBaseline().fit(training_df)
        pred = bl.predict("Brazil", "France")
        assert abs(pred.score_pmf.sum() + pred.tail_mass - 1.0) < 1e-5
