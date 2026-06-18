from src.wc2026.ratings.team_margin import TeamMarginRating
from datetime import datetime

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
    assert "stub" in r.sources_used

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
        prediction_timestamp=datetime.utcnow(),
    )
    lh, la, diag = egm_components_to_lambdas(home, away, ctx, base_goals=1.3)
    assert lh > 0 and la > 0
    assert abs(diag["match_expected_goal_margin"] - (lh - la)) < 1e-9
    # No generic home advantage: host_home_adj_log=0, venue=0, so no spurious home boost
    # For equal attack/defense, lambdas should be symmetric-ish
