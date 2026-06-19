"""
Validation gate tests: every scheduled match gets a prediction.
These enforce the prediction coverage contract.
"""
import pytest
import math
from datetime import datetime
from src.wc2026.models.prediction_coverage import (
    build_match_prediction, ensure_prediction_coverage,
    FullMatchPrediction, WC_TOTAL_BASELINE,
)
from src.wc2026.ratings.team_margin import TeamMarginRating
from src.wc2026.ratings.fallback_prior import (
    build_fallback_egm, compute_uncertainty, confederation_prior_egm,
    SOURCE_TIER_ORDER,
)


# ── Helper fixtures ─────────────────────────────────────────────────────────

def _make_match(match_id=1, h_id=10, a_id=20, h_name="USA", a_name="Brazil",
                h_conf="CONCACAF", a_conf="CONMEBOL"):
    return {
        "match_id": match_id, "home_team_id": h_id, "away_team_id": a_id,
        "home_team_name": h_name, "away_team_name": a_name,
        "home_confederation": h_conf, "away_confederation": a_conf,
    }


def _make_rating(team_id, egm=0.0, conf=None, sources=None, uncertainty=0.2):
    return TeamMarginRating(
        team_id=team_id, team_name=f"Team{team_id}",
        abbreviation=None, confederation=conf,
        neutral_egm=egm, attack_log=egm/2, defense_log=-egm/2,
        pure_strength_egm=egm, market_strength_egm=egm,
        uncertainty_egm=uncertainty,
        sources_used=sources or ["pi_elo", "market_ability"],
    )


# ── Test 1: every scheduled match gets a prediction ────────────────────────

def test_every_scheduled_match_has_egm_prediction():
    matches = [_make_match(i, h_id=i*2, a_id=i*2+1) for i in range(1, 11)]
    ratings = {}  # no ratings available — should fall back
    preds = ensure_prediction_coverage(matches, ratings)
    assert len(preds) == 10, "Must produce one prediction per match"
    for p in preds:
        assert isinstance(p, FullMatchPrediction)
        assert p.match_id > 0
        assert isinstance(p.home_neutral_egm, float)
        assert isinstance(p.away_neutral_egm, float)
        assert isinstance(p.match_expected_goal_margin, float)


# ── Test 2: every prediction has valid lambdas ──────────────────────────────

def test_every_prediction_has_valid_lambdas():
    matches = [_make_match(i, h_id=i, a_id=i+100) for i in range(1, 20)]
    ratings = {i: _make_rating(i, egm=(i-10)*0.1) for i in range(1, 10)}
    preds = ensure_prediction_coverage(matches, ratings)
    for p in preds:
        assert p.lambda_home > 0, f"lambda_home must be positive, got {p.lambda_home}"
        assert p.lambda_away > 0, f"lambda_away must be positive, got {p.lambda_away}"
        assert not math.isnan(p.lambda_home)
        assert not math.isnan(p.lambda_away)
        assert not math.isinf(p.lambda_home)
        assert not math.isinf(p.lambda_away)


# ── Test 3: every prediction has a score PMF ───────────────────────────────

def test_every_prediction_has_score_pmf():
    matches = [_make_match()]
    ratings = {}
    preds = ensure_prediction_coverage(matches, ratings)
    for p in preds:
        assert p.score_pmf_available is True


# ── Test 4: missing inputs trigger fallback, not failure ────────────────────

def test_missing_inputs_trigger_fallback_not_failure():
    """Even with completely empty ratings and an exception-prone path, must return a prediction."""
    matches = [_make_match(999, h_id=9999, a_id=9998, h_conf=None, a_conf=None)]
    preds = ensure_prediction_coverage(matches, {})
    assert len(preds) == 1
    p = preds[0]
    assert p.lambda_home > 0
    assert p.lambda_away > 0
    # Global fallback: both EGMs ≈ 0
    assert abs(p.home_neutral_egm) <= 0.2
    assert abs(p.away_neutral_egm) <= 0.2
    assert "global_fallback" in p.sources_used or "confederation" in p.sources_used


# ── Test 5: uncertainty increases when sources are missing ─────────────────

def test_uncertainty_increases_when_sources_are_missing():
    # Full data prediction
    full_pred = build_match_prediction(
        match_id=1, home_team="A", away_team="B",
        home_egm=0.3, away_egm=-0.1,
        total_anchor=WC_TOTAL_BASELINE,
        home_sources=["market_ability", "futures_ability", "pi_elo", "qualifying", "player_roster"],
        away_sources=["market_ability", "futures_ability", "pi_elo", "qualifying", "player_roster"],
        home_uncertainty=0.1, away_uncertainty=0.1,
    )
    # Fallback-only prediction
    fallback_pred = build_match_prediction(
        match_id=2, home_team="C", away_team="D",
        home_egm=0.0, away_egm=0.0,
        total_anchor=WC_TOTAL_BASELINE,
        home_sources=["global_fallback"],
        away_sources=["global_fallback"],
        home_uncertainty=1.0, away_uncertainty=1.0,
    )
    assert fallback_pred.uncertainty_level > full_pred.uncertainty_level, (
        f"Fallback ({fallback_pred.uncertainty_level:.2f}) must be more uncertain "
        f"than full-data ({full_pred.uncertainty_level:.2f})"
    )
    assert fallback_pred.uncertainty_level >= 0.9
    assert full_pred.uncertainty_level <= 0.3


# ── Test 6: win/draw/loss always sum to 1.0 ────────────────────────────────

def test_wdl_always_sums_to_one():
    for egm_diff in [-2.0, -0.5, 0.0, 0.5, 1.5, 3.0]:
        pred = build_match_prediction(
            match_id=1, home_team="A", away_team="B",
            home_egm=egm_diff/2, away_egm=-egm_diff/2,
            total_anchor=WC_TOTAL_BASELINE,
            home_sources=["pi_elo"], away_sources=["pi_elo"],
            home_uncertainty=0.3, away_uncertainty=0.3,
        )
        total = pred.p_home_win + pred.p_draw + pred.p_away_win
        assert abs(total - 1.0) < 1e-6, f"W+D+L = {total:.6f} for egm_diff={egm_diff}"


# ── Test 7: confederation priors are used for unknown teams ────────────────

def test_confederation_prior_used_for_unknown_teams():
    matches = [_make_match(1, h_id=9999, a_id=9998, h_conf="UEFA", a_conf="CAF")]
    preds = ensure_prediction_coverage(matches, {})
    p = preds[0]
    # UEFA team should get positive EGM, CAF should get negative EGM
    # (based on confederation priors)
    assert p.home_neutral_egm >= 0, f"UEFA prior should be ≥ 0, got {p.home_neutral_egm}"
    assert p.away_neutral_egm <= 0, f"CAF prior should be ≤ 0, got {p.away_neutral_egm}"


# ── Test 8: fallback hierarchy produces traceable sources ─────────────────

def test_fallback_produces_traceable_sources():
    egm, sources, uncertainty = build_fallback_egm(
        team_name="TestTeam", team_id=1, confederation="UEFA",
        component_egms={"pi_elo": 0.2, "market_ability": None, "futures_ability": None,
                        "qualifying": None, "player_roster": None},
    )
    assert "pi_elo" in sources
    assert len(sources) >= 1
    assert isinstance(uncertainty, float)
    assert 0.0 <= uncertainty <= 1.0


# ── Test 9: no prediction is None or raises ───────────────────────────────

def test_no_prediction_is_none_or_raises():
    """Stress test: 48 matches with partial/missing ratings."""
    matches = [_make_match(i, h_id=i, a_id=i+48) for i in range(1, 49)]
    # Only half have ratings
    ratings = {i: _make_rating(i, egm=(i % 10 - 5) * 0.1) for i in range(1, 25)}
    preds = ensure_prediction_coverage(matches, ratings)
    assert len(preds) == 48
    for p in preds:
        assert p is not None
        assert p.lambda_home > 0
        assert p.lambda_away > 0
        assert not math.isnan(p.lambda_home)


# ── Test 10: betting abstention ≠ prediction abstention ──────────────────

def test_betting_abstention_does_not_prevent_prediction():
    """
    Even a match where CLV model would abstain (uncertainty > 0.8)
    must still have a valid EGM prediction.
    """
    pred = build_match_prediction(
        match_id=1, home_team="A", away_team="B",
        home_egm=0.0, away_egm=0.0,
        total_anchor=WC_TOTAL_BASELINE,
        home_sources=["global_fallback"],
        away_sources=["global_fallback"],
        home_uncertainty=1.0, away_uncertainty=1.0,
    )
    # High uncertainty — CLV layer would abstain from bet recommendations
    assert pred.uncertainty_level > 0.8
    # But prediction exists and is valid
    assert pred.lambda_home > 0
    assert pred.lambda_away > 0
    assert abs(pred.p_home_win + pred.p_draw + pred.p_away_win - 1.0) < 1e-6
