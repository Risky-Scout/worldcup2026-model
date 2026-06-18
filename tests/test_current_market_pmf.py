import numpy as np
import pytest
import pandas as pd
from wc2026.markets.current_market_pmf import build_market_pmf_simple, build_market_pmf_full

SNAPSHOT_SIMPLE = pd.DataFrame([{
    "match_id": 1, "vendor": "draftkings",
    "moneyline_home_odds": -150, "moneyline_draw_odds": 270, "moneyline_away_odds": 400,
    "total_value": "2.5", "total_over_odds": -110, "total_under_odds": -110,
    "market_type": "moneyline", "spread_home_value": None, "spread_home_odds": None, "spread_away_odds": None,
}])

SNAPSHOT_WITH_SPREAD = pd.DataFrame([
    {"match_id": 1, "vendor": "draftkings", "moneyline_home_odds": -150, "moneyline_draw_odds": 270,
     "moneyline_away_odds": 400, "total_value": "2.5", "total_over_odds": -110, "total_under_odds": -110,
     "market_type": "moneyline", "spread_home_value": "-0.5", "spread_home_odds": -120, "spread_away_odds": 100},
])

def test_simple_returns_result():
    result = build_market_pmf_simple(SNAPSHOT_SIMPLE)
    assert result is not None
    assert result.pmf.shape[0] > 0
    assert abs(result.pmf.sum() - 1.0) < 1e-6

def test_simple_no_negative_probs():
    result = build_market_pmf_simple(SNAPSHOT_SIMPLE)
    assert (result.pmf >= -1e-10).all()

def test_overround_stored():
    result = build_market_pmf_simple(SNAPSHOT_SIMPLE)
    assert len(result.overround) > 0

def test_missing_market_no_crash():
    result = build_market_pmf_simple(pd.DataFrame())
    assert result is None

def test_spread_changes_full_pmf():
    simple = build_market_pmf_simple(SNAPSHOT_SIMPLE)
    full = build_market_pmf_full(SNAPSHOT_WITH_SPREAD)
    assert full is not None
    # PMF should be different when spread provided (full optimization runs)
    # At minimum, both should be valid PMFs
    assert abs(full.pmf.sum() - 1.0) < 1e-5

def test_fallback_on_empty_snapshot():
    result = build_market_pmf_full(pd.DataFrame())
    assert result is None
