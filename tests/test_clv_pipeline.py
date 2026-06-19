"""Tests for CLV pipeline."""
import pandas as pd
import numpy as np
import pytest
from datetime import datetime, timezone
from src.wc2026.evaluation.clv_pipeline import (
    compute_fair_clv, compute_quarter_line_clv,
    write_clv_by_market, write_clv_by_horizon,
    CLVRecord,
)


def test_fair_clv_positive_edge():
    # Decimal odds of 2.10 with closing fair prob 0.52 → edge
    clv = compute_fair_clv(2.10, 0.52)
    assert clv > 0
    assert abs(clv - (2.10 * 0.52 - 1.0)) < 1e-9


def test_fair_clv_no_edge():
    # Exactly fair bet (odds = 1/prob) → CLV ≈ 0
    prob = 0.45
    odds = 1.0 / prob
    clv = compute_fair_clv(odds, prob)
    assert abs(clv) < 1e-9


def test_quarter_line_clv():
    clv = compute_quarter_line_clv(
        bet_decimal_odds=1.95,
        closing_win_prob=0.50,
        closing_push_prob=0.10,
        closing_lose_prob=0.40,
    )
    assert isinstance(clv, float)
    # With reasonable probs: (0.5*0.5 + 0.5*0.1)*(0.95) - 0.5*0.40
    expected = (0.5 * 0.50 + 0.5 * 0.10) * (1.95 - 1) - 0.5 * 0.40
    assert abs(clv - expected) < 1e-9


def test_write_clv_by_market_empty():
    out = write_clv_by_market([])
    assert out.exists()


def test_write_clv_by_horizon_empty():
    out = write_clv_by_horizon([])
    assert out.exists()


def _make_records():
    return [
        CLVRecord(
            match_id=1, home_team="USA", away_team="Brazil",
            market_type="1x2", market_key="home", bet_side="home",
            bet_decimal_odds=2.1, closing_fair_probability=0.52,
            current_fair_probability=0.50, fair_clv=0.092,
            same_line_clv=0.05, horizon_hours=3.5,
            vendor="draftkings", prediction_timestamp="2026-06-13T12:00:00Z",
            closing_timestamp="2026-06-13T15:30:00Z", stage="Group Stage",
        ),
        CLVRecord(
            match_id=2, home_team="France", away_team="Germany",
            market_type="totals", market_key="over_2.5", bet_side="over",
            bet_decimal_odds=1.9, closing_fair_probability=0.48,
            current_fair_probability=0.45, fair_clv=-0.088,
            same_line_clv=-0.095, horizon_hours=26.0,
            vendor="fanduel", prediction_timestamp="2026-06-14T10:00:00Z",
            closing_timestamp="2026-06-15T12:00:00Z", stage="Group Stage",
        ),
    ]


def test_write_clv_by_market_with_data():
    records = _make_records()
    out = write_clv_by_market(records)
    assert out.exists()
    df = pd.read_csv(out)
    assert "market_type" in df.columns
    assert "mean_fair_clv" in df.columns
    assert len(df) == 2  # 1x2 and totals


def test_write_clv_by_horizon_with_data():
    records = _make_records()
    out = write_clv_by_horizon(records)
    assert out.exists()
    df = pd.read_csv(out)
    assert "horizon_bin" in df.columns
    assert len(df) >= 1


def test_clv_records_have_required_fields():
    r = _make_records()[0]
    assert hasattr(r, "fair_clv")
    assert hasattr(r, "closing_fair_probability")
    assert hasattr(r, "horizon_hours")
    assert hasattr(r, "vendor")
    assert hasattr(r, "stage")
