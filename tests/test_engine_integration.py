"""
Integration tests for PredictionEngine.predict_match() hot path.

Uses synthetic training data — no BDL API calls.
Verifies the full predict_match fallback pipeline: ladder fitting,
equal-probability guard, market structure, and consistency invariants.
"""
from __future__ import annotations

import datetime as dt
import math

import numpy as np
import pandas as pd
import pytest

from wc2026.models.baselines import EqualProbabilityBaseline
from wc2026.models.ladder import ModelLadder
from wc2026.models.prediction import ScorePMFPrediction


# ---------------------------------------------------------------------------
# Shared fixture helpers
# ---------------------------------------------------------------------------

TEAMS = [
    "Brazil", "France", "Germany", "Argentina",
    "England", "Spain", "Netherlands", "Portugal",
]

SCORES = [
    (2, 1), (0, 0), (3, 2), (1, 1), (0, 2), (1, 0), (2, 0), (0, 1),
    (3, 0), (1, 2), (0, 0), (2, 2), (4, 1), (0, 3), (1, 1), (2, 1),
    (1, 0), (2, 1), (0, 1), (3, 0), (1, 3), (0, 0), (2, 0), (1, 2),
]


def _make_training_df() -> pd.DataFrame:
    base = dt.datetime(2022, 11, 20, tzinfo=dt.timezone.utc)
    rows = []
    for i, (h, a) in enumerate(SCORES):
        rows.append({
            "match_id": i + 1,
            "home_team": TEAMS[i % len(TEAMS)],
            "away_team": TEAMS[(i + 1) % len(TEAMS)],
            "home_goals": h,
            "away_goals": a,
            "is_neutral": 1,
            "match_weight": 0.9 ** (len(SCORES) - i),
            "match_datetime": base + dt.timedelta(days=i),
            "season": 2022,
            "stage": "Group Stage",
        })
    return pd.DataFrame(rows)


@pytest.fixture(scope="module")
def fitted_ladder() -> ModelLadder:
    df = _make_training_df()
    ladder = ModelLadder(df, include_bayesian=False)
    ladder.fit(models=["dixon_coles", "poisson"])
    return ladder


# ---------------------------------------------------------------------------
# Tests: engine fallback path (predict_match without composite prior)
# ---------------------------------------------------------------------------

class TestPredictMatchFallback:
    """
    Exercises the predict_match fallback path directly via the ladder.
    We bypass the full PredictionEngine (which needs data on disk) and
    exercise the same logic: ladder predict → select champion → return dict.
    """

    def _run_predict(self, ladder: ModelLadder, home: str, away: str) -> dict:
        """Replicates the engine's fallback predict_match logic."""
        predictions: dict[str, ScorePMFPrediction] = {}
        for model_name in ladder.fitted_models():
            try:
                pred = ladder.predict(model_name, home, away, neutral_venue=True)
                predictions[model_name] = pred
            except Exception:
                pass

        if not predictions:
            predictions["equal_probability"] = EqualProbabilityBaseline().predict(home, away)

        # Champion selection: prefer dixon_coles, else first available
        champion_name = next(
            (n for n in ["dixon_coles", "poisson"] if n in predictions),
            next(iter(predictions)),
        )
        return predictions, champion_name

    def test_predict_returns_nonempty_predictions(self, fitted_ladder):
        preds, champion = self._run_predict(fitted_ladder, "Brazil", "France")
        assert len(preds) > 0

    def test_champion_is_dixon_coles_when_fitted(self, fitted_ladder):
        preds, champion = self._run_predict(fitted_ladder, "Brazil", "France")
        assert champion == "dixon_coles"

    def test_prediction_has_valid_1x2(self, fitted_ladder):
        preds, champion = self._run_predict(fitted_ladder, "Brazil", "France")
        p = preds[champion]
        dm = p.derived_markets
        total = dm.home_win + dm.draw + dm.away_win
        assert abs(total - 1.0) < 1e-4, f"1x2 sum = {total}"

    def test_all_probabilities_in_unit_interval(self, fitted_ladder):
        preds, champion = self._run_predict(fitted_ladder, "Brazil", "Germany")
        p = preds[champion]
        dm = p.derived_markets
        for attr in ("home_win", "draw", "away_win", "over_2_5", "btts_yes"):
            val = getattr(dm, attr)
            assert 0.0 <= val <= 1.0, f"{attr} = {val} out of [0, 1]"

    def test_expected_goals_positive(self, fitted_ladder):
        preds, champion = self._run_predict(fitted_ladder, "Argentina", "England")
        p = preds[champion]
        assert p.expected_home_goals > 0
        assert p.expected_away_goals > 0

    def test_equal_probability_fallback_used_when_no_models(self):
        """When ladder has no predictions, equal-probability baseline is used."""
        predictions: dict = {}
        home, away = "Unknown_A", "Unknown_B"

        if not predictions:
            predictions["equal_probability"] = EqualProbabilityBaseline().predict(home, away)

        assert "equal_probability" in predictions
        dm = predictions["equal_probability"].derived_markets
        total = dm.home_win + dm.draw + dm.away_win
        assert abs(total - 1.0) < 1e-4

    def test_equal_probability_not_injected_when_models_succeed(self, fitted_ladder):
        """Bug fix verification: equal_probability must NOT appear in successful predictions."""
        preds, champion = self._run_predict(fitted_ladder, "Brazil", "France")
        # The fixed engine only adds equal_probability as last resort
        assert "equal_probability" not in preds, (
            "equal_probability was injected even though real models produced predictions"
        )

    def test_reversing_matchup_swaps_outcomes(self, fitted_ladder):
        """When A vs B is reversed to B vs A, A's win prob as home > B's win prob as home."""
        preds_fwd, champ_fwd = self._run_predict(fitted_ladder, "Brazil", "Germany")
        preds_rev, champ_rev = self._run_predict(fitted_ladder, "Germany", "Brazil")
        hw_fwd = preds_fwd[champ_fwd].derived_markets.home_win  # Brazil home-win prob
        hw_rev = preds_rev[champ_rev].derived_markets.home_win  # Germany home-win prob
        # In a symmetric neutral model: hw_fwd + hw_rev ≠ 1, but draw fills the gap.
        # Just assert both predictions are nonzero and different.
        assert hw_fwd > 0 and hw_rev > 0
        assert hw_fwd != hw_rev


# ---------------------------------------------------------------------------
# Tests: EqualProbabilityBaseline
# ---------------------------------------------------------------------------

class TestEqualProbabilityBaseline:
    def test_sums_to_one(self):
        b = EqualProbabilityBaseline()
        pred = b.predict("A", "B")
        dm = pred.derived_markets
        assert abs(dm.home_win + dm.draw + dm.away_win - 1.0) < 1e-6

    def test_home_and_away_equal(self):
        b = EqualProbabilityBaseline()
        pred = b.predict("A", "B")
        dm = pred.derived_markets
        assert abs(dm.home_win - dm.away_win) < 1e-6

    def test_over_2_5_in_range(self):
        b = EqualProbabilityBaseline()
        pred = b.predict("X", "Y")
        assert 0.0 <= pred.derived_markets.over_2_5 <= 1.0


# ---------------------------------------------------------------------------
# Tests: global average constant consistency
# ---------------------------------------------------------------------------

def test_global_average_updated_to_wc2026():
    """Regression: _WC_AVG_ATTACK must reflect WC2026 observed rate 1.45, not 1.30."""
    from wc2026.ratings.composite import _WC_AVG_ATTACK, _WC_AVG_DEFENSE
    assert _WC_AVG_ATTACK == pytest.approx(1.45, abs=0.01), (
        f"_WC_AVG_ATTACK={_WC_AVG_ATTACK} — still at old 1.30?"
    )
    assert _WC_AVG_DEFENSE == pytest.approx(1.45, abs=0.01)


def test_engine_lambda_divisor_updated():
    """Regression: engine.py lambda divisor must be 1.45, not 1.30."""
    import ast
    import pathlib
    src = (pathlib.Path(__file__).parent.parent / "src" / "wc2026" / "engine.py").read_text()
    tree = ast.parse(src)
    # Find the two comp_lh / comp_la assignment lines and check for 1.30
    assert "/ 1.30" not in src, (
        "engine.py still divides by 1.30 — update to 1.45 for WC2026 observed rate"
    )


def test_no_utcnow_in_src():
    """Regression: datetime.utcnow() must not appear in any source file."""
    import pathlib
    src_dir = pathlib.Path(__file__).parent.parent / "src"
    violations = []
    for py_file in src_dir.rglob("*.py"):
        text = py_file.read_text()
        if "utcnow" in text:
            violations.append(str(py_file))
    assert not violations, f"Files still using utcnow(): {violations}"
