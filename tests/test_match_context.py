from datetime import datetime
from src.wc2026.features.match_context import compute_match_context, HOST_COUNTRIES_2026

def test_usa_gets_host_boost():
    match = {"id": 1, "home_team": {"id": 1}, "away_team": {"id": 2},
             "stage": {"name": "Group Stage", "order": 1}, "round_number": 1}
    ctx = compute_match_context(
        match_row=match,
        home_team_country_code="USA",
        away_team_country_code="BRA",
        stadium_row={"latitude": 33.8, "longitude": -84.4, "capacity": 75000, "country": "United States"},
        home_standing=None, away_standing=None,
        home_match_dates=[], away_match_dates=[],
        prediction_timestamp=datetime.utcnow(),
    )
    assert ctx.actual_host_home is True
    assert ctx.actual_host_away is False
    assert ctx.host_home_adj_log > 0

def test_non_host_no_home_advantage():
    match = {"id": 2, "home_team": {"id": 3}, "away_team": {"id": 4},
             "stage": {"name": "Group Stage", "order": 1}, "round_number": 1}
    ctx = compute_match_context(
        match_row=match,
        home_team_country_code="BRA",
        away_team_country_code="ARG",
        stadium_row=None,
        home_standing=None, away_standing=None,
        home_match_dates=[], away_match_dates=[],
        prediction_timestamp=datetime.utcnow(),
    )
    # BRA is NOT a host in 2026 → no host boost from being listed as home_team
    assert ctx.host_home_adj_log == 0.0
    assert ctx.actual_host_home is False

def test_egm_lambdas_no_generic_home_advantage():
    """
    Ensure that for equal teams with no adjustments, lambda_home ≈ lambda_away.
    """
    from src.wc2026.ratings.team_margin import TeamMarginRating
    from src.wc2026.models.egm_to_lambdas import egm_components_to_lambdas, MatchContextAdjustment
    home = TeamMarginRating.stub(1, "A")
    away = TeamMarginRating.stub(2, "B")
    ctx = MatchContextAdjustment(match_id=1, home_team_id=1, away_team_id=2,
                                  prediction_timestamp=datetime.utcnow())
    lh, la, _ = egm_components_to_lambdas(home, away, ctx, base_goals=1.3)
    assert abs(lh - la) < 0.01, f"Expected symmetric lambdas, got {lh:.3f} vs {la:.3f}"
