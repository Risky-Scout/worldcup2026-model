"""
Tests for ShadowEGMRunner.
"""
import json
import tempfile
from pathlib import Path
from datetime import datetime, timezone
import pandas as pd
import pytest

from src.wc2026.models.shadow_egm_runner import ShadowMatchPrediction


def _minimal_pred():
    return ShadowMatchPrediction(
        match_id=1001,
        home_team="USA",
        away_team="Brazil",
        prediction_timestamp=datetime.now(timezone.utc).isoformat(),
        home_neutral_egm=0.1,
        away_neutral_egm=0.5,
        home_pure_strength_egm=0.1,
        away_pure_strength_egm=0.5,
        home_market_strength_egm=0.15,
        away_market_strength_egm=0.45,
        match_expected_goal_margin=-0.4,
        egm_lambda_home=1.1,
        egm_lambda_away=1.5,
        live_lambda_home=1.05,
        live_lambda_away=1.45,
    )


def test_shadow_pred_to_dict_has_team_strength():
    pred = _minimal_pred()
    d = pred.to_dict()
    assert "team_strength" in d
    assert "home_neutral_egm" in d["team_strength"]
    assert "match_expected_goal_margin" in d["team_strength"]


def test_shadow_pred_to_dict_has_shadow_model():
    pred = _minimal_pred()
    d = pred.to_dict()
    assert "shadow_model" in d
    assert d["shadow_model"]["live_lambda_home"] == 1.05


def test_team_strength_is_nested_not_flat():
    """team_strength must be a nested object, not a flat key overwrite."""
    pred = _minimal_pred()
    d = pred.to_dict()
    # Ensure top-level keys don't conflict with existing WoO schema
    assert "home_neutral_egm" not in d  # must be nested
    assert isinstance(d["team_strength"], dict)


def test_stacker_fallback_without_sklearn():
    """Stacker predict_pure should return a number even without fitted model."""
    from src.wc2026.models.team_margin_stacker import TeamMarginStacker
    s = TeamMarginStacker()
    result = s.predict_pure({"pi_egm": 0.3, "elo_egm": 0.1, "xg_attack_egm": 0.05,
                              "xg_defense_egm": 0.02, "player_egm": 0.0,
                              "futures_egm": 0.0, "venue_egm": 0.0})
    assert isinstance(result, float)


def test_no_generic_home_advantage_in_shadow():
    """Admin home_team listing must NOT give home advantage unless actual host."""
    from src.wc2026.ratings.team_margin import TeamMarginRating
    from src.wc2026.models.egm_to_lambdas import egm_components_to_lambdas, MatchContextAdjustment

    # Equal teams, no context adjustments
    home = TeamMarginRating.stub(1, "Brazil")
    away = TeamMarginRating.stub(2, "Argentina")
    ctx = MatchContextAdjustment(
        match_id=999, home_team_id=1, away_team_id=2,
        prediction_timestamp=datetime.now(timezone.utc),
        # All adjustments = 0
    )
    lh, la, _ = egm_components_to_lambdas(home, away, ctx, base_goals=1.3)
    assert abs(lh - la) < 0.01, "Equal teams with no context adjustments must yield symmetric lambdas"


def test_shadow_does_not_write_to_public_paths():
    """Shadow outputs must go to shadow dirs, not public prediction dirs."""
    from src.wc2026.models.shadow_egm_runner import SHADOW_DIR, TEAM_MARGIN_DIR
    public_paths = ["data/published", "docs/", "data/predictions/2026"]
    for p in public_paths:
        assert p not in str(SHADOW_DIR), f"Shadow dir must not be in {p}"
        assert p not in str(TEAM_MARGIN_DIR), f"Shadow dir must not be in {p}"
