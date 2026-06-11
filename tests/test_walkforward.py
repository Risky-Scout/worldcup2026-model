"""
Walk-forward backtester tests.

ACCEPTANCE: No model can be called calibrated unless it has OOF predictions
produced by the WalkForwardEngine.
"""
import datetime as dt

import numpy as np
import pandas as pd
import pytest

from wc2026.backtest.walkforward import WalkForwardEngine, WalkForwardResult
from wc2026.models.ladder import MODEL_DIXON_COLES, MODEL_POISSON


def _make_large_df(n: int = 30) -> pd.DataFrame:
    """30 synthetic completed matches across 6 teams."""
    teams = ["TeamA", "TeamB", "TeamC", "TeamD", "TeamE", "TeamF"]
    rng = np.random.default_rng(42)
    base = dt.datetime(2022, 6, 1, tzinfo=dt.timezone.utc)
    rows = []
    for i in range(n):
        h, a = rng.choice(teams, size=2, replace=False)
        rows.append({
            "match_id": i + 1,
            "home_team": h,
            "away_team": a,
            "home_goals": int(rng.poisson(1.4)),
            "away_goals": int(rng.poisson(1.2)),
            "is_neutral": 1,
            "match_weight": 1.0,
            "match_datetime": base + dt.timedelta(days=i),
            "season": 2022,
            "stage": "Group Stage",
            "status": "completed",
        })
    return pd.DataFrame(rows)


@pytest.fixture(scope="module")
def large_df():
    return _make_large_df(30)


class TestWalkForwardEngine:

    def test_produces_results(self, large_df):
        engine = WalkForwardEngine(
            large_df,
            models=[MODEL_POISSON],
            include_baselines=False,
            min_train_matches=8,
            refit_every=5,
            include_bayesian=False,
        )
        results = engine.run(save=False)
        assert len(results) >= 1
        assert results[0].n_predictions > 0

    def test_no_future_leakage(self, large_df):
        """Training data for match i must only contain rows with index < i."""
        # We verify this by checking that n_train_matches grows monotonically
        engine = WalkForwardEngine(
            large_df,
            models=[MODEL_POISSON],
            include_baselines=False,
            min_train_matches=8,
            refit_every=100,  # refit only once
            include_bayesian=False,
        )
        results = engine.run(save=False)
        if results and not results[0].per_match.empty:
            train_counts = results[0].per_match["n_train_matches"].values
            assert all(train_counts[i] <= train_counts[i + 1] for i in range(len(train_counts) - 1)), \
                "Training data count decreased — possible leakage."

    def test_metrics_are_finite(self, large_df):
        engine = WalkForwardEngine(
            large_df,
            models=[MODEL_POISSON],
            include_baselines=True,
            min_train_matches=8,
            refit_every=5,
            include_bayesian=False,
        )
        results = engine.run(save=False)
        for r in results:
            m = r.metrics
            if r.n_predictions > 0:
                assert np.isfinite(m.rps_1x2), f"{r.model_name}: RPS is not finite"
                assert np.isfinite(m.exact_score_log_loss), f"{r.model_name}: ExactLL is not finite"

    def test_pmf_predictions_sum_to_one(self, large_df):
        """Each OOF prediction's PMF must sum to 1.0."""
        engine = WalkForwardEngine(
            large_df,
            models=[MODEL_POISSON],
            include_baselines=False,
            min_train_matches=8,
            refit_every=5,
            include_bayesian=False,
        )
        results = engine.run(save=False)
        if results:
            # OOF predictions are stored as objects in per_match (before parquet serialisation)
            # p_home + p_draw + p_away should sum to 1.0
            df = results[0].per_match
            if not df.empty:
                sums = df["p_home_win"] + df["p_draw"] + df["p_away_win"]
                assert all(abs(s - 1.0) < 1e-4 for s in sums), "OOF PMF-derived 1X2 does not sum to 1"
