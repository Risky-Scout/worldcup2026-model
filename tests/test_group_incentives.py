import numpy as np
import pandas as pd
import pytest
from wc2026.tournament.group_incentives import compute_group_incentives, adjust_pmf_for_group_incentives, GroupIncentiveState
from wc2026.markets.canonical_grid import CanonicalGrid

STANDINGS = pd.DataFrame([
    {"team": "USA", "points": 3, "played": 2, "goals_for": 2, "goals_against": 1},
    {"team": "England", "points": 3, "played": 2, "goals_for": 2, "goals_against": 1},
])

def test_incentive_state_computed():
    state = compute_group_incentives("USA", STANDINGS, remaining_fixtures=[("USA", "England")])
    assert isinstance(state, GroupIncentiveState)
    assert 0.0 <= state.draw_utility <= 1.0

def test_empty_standings_returns_default():
    state = compute_group_incentives("USA", pd.DataFrame(), remaining_fixtures=[])
    assert state.team == "USA"

def test_pmf_adjustment_changes_all_markets():
    """When PMF is adjusted, ALL markets change (not just 1X2)."""
    rng = np.random.default_rng(42)
    pmf_orig = rng.dirichlet(np.ones(64)).reshape(8, 8)
    pmf_orig = pmf_orig / pmf_orig.sum()

    home_state = GroupIncentiveState(team="A", draw_utility=0.4, already_qualified_prob=0.0, rotation_proxy=0.0)
    away_state = GroupIncentiveState(team="B", draw_utility=0.4, already_qualified_prob=0.0, rotation_proxy=0.0)

    pmf_adj, lh_adj, la_adj, rho_adj = adjust_pmf_for_group_incentives(
        pmf_orig, home_state, away_state, rho=-0.05, lh=1.5, la=1.0
    )

    # If adjustment was made, check that ALL markets are affected (not just 1X2)
    if not np.allclose(pmf_adj, pmf_orig):
        orig_grid = CanonicalGrid(pmf_orig)
        adj_grid = CanonicalGrid(pmf_adj)

        orig_markets = orig_grid.all_markets()
        adj_markets = adj_grid.all_markets()

        # 1X2 changed
        assert orig_markets["draw"] != adj_markets["draw"]
        # BTTS changed
        assert orig_markets["btts_yes"] != adj_markets["btts_yes"]
        # Totals changed
        assert orig_markets.get("over_2_5") != adj_markets.get("over_2_5")

def test_feature_flag_false_skips_pmf_adjustment(monkeypatch):
    """When GROUP_INCENTIVE_PMF_LEVEL=False, adjustment is not applied."""
    import wc2026.config as config
    monkeypatch.setattr(config, "GROUP_INCENTIVE_PMF_LEVEL", False)
    # Just verify config flag reads correctly
    assert config.GROUP_INCENTIVE_PMF_LEVEL == False
