import pandas as pd
import numpy as np
import pytest
from wc2026.evaluation.clv_report import compute_clv_report, _fair_clv_no_push, _fair_clv_quarter_line

def _make_clv_records(n=30, include_backfill=False, include_post_match=False):
    rows = []
    for i in range(n):
        rows.append({
            "match_id": i % 5,
            "market": "home_win",
            "closing_prob": 0.55,
            "model_fair_odds": 1.8,
            "closing_source": "live_api",
            "clv_raw": 0.8 * 0.55 - 1 + 1.8 * 0.55 - 1,
            "market_quality": 0.8,
        })
    if include_backfill:
        rows.append({
            "match_id": 99, "market": "home_win", "closing_prob": 0.5,
            "model_fair_odds": 2.0, "closing_source": "backfill_invalid",
            "clv_raw": 0.0, "market_quality": 0.5,
        })
    return pd.DataFrame(rows)

def test_backfill_excluded():
    df = _make_clv_records(25, include_backfill=True)
    report = compute_clv_report(df)
    # backfill record should not appear in results
    assert "backfill_invalid" not in str(report.get("excluded_reasons", ""))

def test_positive_clv_requires_valid_source():
    # Only backfill records → no valid data → empty or warning
    df = pd.DataFrame([{
        "match_id": 1, "market": "home_win", "closing_prob": 0.9,
        "model_fair_odds": 1.1, "closing_source": "backfill_invalid",
        "clv_raw": 5.0, "market_quality": 0.9,
    }])
    report = compute_clv_report(df)
    # Should return empty (all excluded) or show 0 valid bets
    if len(report) > 0:
        assert report.iloc[0]["n_bets"] == 0

def test_quarter_line_settlement():
    """AH +0.25 partial win: close_win_weight=0.5, close_lose_weight=0.0 → fair_clv correct."""
    # Bet at 2.0 decimal odds, closing PMF says 50% win (half-win at +0.25)
    clv = _fair_clv_quarter_line(bet_decimal_odds=2.0, close_win_weight=0.5, close_lose_weight=0.0)
    assert abs(clv - (0.5 * (2.0 - 1.0) - 0.0)) < 1e-10

def test_no_push_formula():
    clv = _fair_clv_no_push(bet_decimal_odds=2.0, closing_fair_prob=0.55)
    assert abs(clv - (2.0 * 0.55 - 1.0)) < 1e-10

def test_report_with_valid_records():
    df = _make_clv_records(25)
    report = compute_clv_report(df)
    assert len(report) > 0
    assert "mean_clv" in report.columns
    assert "ci_lower" in report.columns
