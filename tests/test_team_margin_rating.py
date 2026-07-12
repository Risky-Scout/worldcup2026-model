from src.wc2026.ratings.team_margin import TeamMarginRating
from datetime import datetime, timezone

def test_to_dict_has_all_fields():
    r = TeamMarginRating(
        team_id=1, team_name="Brazil", abbreviation="BRA", confederation="CONMEBOL",
        neutral_egm=0.5, attack_log=0.2, defense_log=0.1,
        pure_strength_egm=0.4, market_strength_egm=0.5,
    )
    d = r.to_dict()
    assert "neutral_egm" in d
    assert "attack_log" in d
    assert "pure_strength_egm" in d
    assert d["team_name"] == "Brazil"

def test_stub_is_zero():
    r = TeamMarginRating.stub(99, "Unknown")
    assert r.neutral_egm == 0.0
    assert r.pure_strength_egm == 0.0
    # No confederation supplied → global fallback (stub() now uses fallback hierarchy)
    assert "global_fallback" in r.sources_used or "stub" in r.sources_used

def test_egm_to_lambdas():
    from src.wc2026.models.egm_to_lambdas import egm_components_to_lambdas, MatchContextAdjustment
    home = TeamMarginRating(
        team_id=1, team_name="Brazil", abbreviation=None, confederation=None,
        neutral_egm=0.5, attack_log=0.3, defense_log=0.2,
        pure_strength_egm=0.5, market_strength_egm=0.5,
    )
    away = TeamMarginRating(
        team_id=2, team_name="Germany", abbreviation=None, confederation=None,
        neutral_egm=0.4, attack_log=0.25, defense_log=0.15,
        pure_strength_egm=0.4, market_strength_egm=0.4,
    )
    ctx = MatchContextAdjustment(
        match_id=100, home_team_id=1, away_team_id=2,
        prediction_timestamp=datetime.now(timezone.utc),
    )
    lh, la, diag = egm_components_to_lambdas(home, away, ctx, base_goals=1.3)
    assert lh > 0 and la > 0
    assert abs(diag["match_expected_goal_margin"] - (lh - la)) < 1e-9
    # No generic home advantage: host_home_adj_log=0, venue=0, so no spurious home boost
    # For equal attack/defense, lambdas should be symmetric-ish


# ── Total-goal anchor tests ──────────────────────────────────────────────

from src.wc2026.models.egm_to_lambdas import margin_total_to_lambdas, egm_with_total_anchor


def test_margin_total_to_lambdas_basic():
    lh, la = margin_total_to_lambdas(margin=0.70, total=2.65)
    assert abs(lh - 1.675) < 0.001
    assert abs(la - 0.975) < 0.001
    assert abs((lh + la) - 2.65) < 1e-9
    assert abs((lh - la) - 0.70) < 1e-9


def test_margin_total_preserves_total():
    """The total anchor must be preserved regardless of margin."""
    for margin in [-2.0, -0.5, 0.0, 0.5, 1.2, 2.5]:
        lh, la = margin_total_to_lambdas(margin=margin, total=2.65)
        assert abs((lh + la) - 2.65) < 0.01, f"Total not preserved for margin={margin}"


def test_margin_total_preserves_margin():
    """The margin must match home_egm - away_egm."""
    for margin in [-1.5, 0.0, 0.5, 1.0, 2.0]:
        lh, la = margin_total_to_lambdas(margin=margin, total=2.65)
        assert abs((lh - la) - margin) < 0.01, f"Margin not preserved: {lh-la} vs {margin}"


def test_egm_with_total_anchor_contract():
    """Contract test matching the specification."""
    lh, la = egm_with_total_anchor(
        home_egm=0.50,
        away_egm=-0.20,
        total_goal_anchor=2.65,
    )
    assert abs((lh + la) - 2.65) < 0.03
    assert abs((lh - la) - 0.70) < 0.03


def test_lambda_floor_no_negative():
    """Lambda can never be negative even with extreme margins."""
    lh, la = margin_total_to_lambdas(margin=5.0, total=2.65)
    assert lh >= 0.05
    assert la >= 0.05


def test_high_total_market_is_used_over_baseline():
    """If market total is 3.2, that should be used instead of 2.65 baseline."""
    lh_market, la_market = margin_total_to_lambdas(margin=0.5, total=3.2)
    lh_base, la_base = margin_total_to_lambdas(margin=0.5, total=2.65)
    assert lh_market + la_market > lh_base + la_base
    assert abs((lh_market + la_market) - 3.2) < 1e-9


def test_no_lambda_inflation_for_equal_strong_teams():
    """
    Two strong teams (both +0.5 EGM) should NOT produce an inflated total.
    With total anchor = 2.65, total must stay at 2.65.
    """
    lh, la = egm_with_total_anchor(home_egm=0.5, away_egm=0.5, total_goal_anchor=2.65)
    assert abs((lh + la) - 2.65) < 0.03
    assert abs(lh - la) < 0.01  # margin ≈ 0 for equal teams
