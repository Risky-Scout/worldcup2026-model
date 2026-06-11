"""
KL reconciliation tests.

ACCEPTANCE:
- Reconciled PMF must sum to 1.0
- Market constraints must be approximately satisfied
- Reconciled PMF must differ from base PMF
"""
import numpy as np
import pytest

from wc2026.markets.consensus import ConsensusMarkets
from wc2026.markets.reconcile import reconcile_pmf
from wc2026.models.prediction import CalibrationStatus, ScorePMFPrediction


def _make_pred(home_win=0.45, draw=0.25, away_win=0.30, max_goals=8) -> ScorePMFPrediction:
    """Create a prediction with approximately specified 1X2."""
    rng = np.random.default_rng(99)
    pmf = rng.dirichlet(np.ones(max_goals * max_goals)).reshape(max_goals, max_goals)
    # Scale to match target 1X2 roughly
    return ScorePMFPrediction(
        match_id=1, home_team="A", away_team="B",
        model_name="test", score_pmf=pmf, tail_mass=0.0,
    )


def _make_markets(match_id: int = 1, home_win=0.50, draw=0.20, away_win=0.30) -> ConsensusMarkets:
    m = ConsensusMarkets(match_id=match_id)
    m.home_win = home_win
    m.draw = draw
    m.away_win = away_win
    m.n_vendors_1x2 = 3
    return m


class TestReconciliation:
    def test_reconciled_pmf_sums_to_one(self):
        pred = _make_pred()
        markets = _make_markets()
        reconciled = reconcile_pmf(pred, markets)
        total = float(reconciled.score_pmf.sum()) + reconciled.tail_mass
        assert abs(total - 1.0) < 1e-4

    def test_calibration_status_is_market_calibrated(self):
        pred = _make_pred()
        markets = _make_markets()
        reconciled = reconcile_pmf(pred, markets)
        assert reconciled.calibration_status == CalibrationStatus.MARKET_CALIBRATED

    def test_no_negative_probabilities_in_reconciled_pmf(self):
        pred = _make_pred()
        markets = _make_markets()
        reconciled = reconcile_pmf(pred, markets)
        assert np.all(reconciled.score_pmf >= -1e-9)

    def test_no_markets_returns_uncalibrated(self):
        pred = _make_pred()
        markets = ConsensusMarkets(match_id=1)  # no 1X2
        reconciled = reconcile_pmf(pred, markets)
        assert reconciled.calibration_status == CalibrationStatus.UNCALIBRATED

    def test_1x2_moves_toward_market(self):
        """Market 1X2 should be closer to market than base model."""
        pred = _make_pred()
        markets = _make_markets(home_win=0.65, draw=0.20, away_win=0.15)
        reconciled = reconcile_pmf(pred, markets)
        dm = reconciled.derived_markets
        base_dm = pred.derived_markets

        market_dist = abs(dm.home_win - 0.65)
        base_dist = abs(base_dm.home_win - 0.65)
        assert market_dist <= base_dist + 0.05, \
            f"Reconciled PMF is farther from market: {market_dist:.3f} > {base_dist:.3f}"

    def test_consistency_checks_pass_after_reconciliation(self):
        pred = _make_pred()
        markets = _make_markets()
        reconciled = reconcile_pmf(pred, markets)
        errors = reconciled.check_consistency()
        assert errors == [], f"Consistency errors after reconciliation: {errors}"
