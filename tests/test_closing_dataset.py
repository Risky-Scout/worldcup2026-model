import datetime, pytest
import numpy as np
import pandas as pd
import tempfile
from wc2026.evaluation.closing_dataset import build_closing_dataset, _empty_dataset

def test_returns_empty_when_no_snapshots(tmp_path):
    """Returns empty DataFrame (not error) when no historical snapshots exist."""
    from wc2026.data.odds_snapshot_store import OddsSnapshotStore
    store = OddsSnapshotStore(base_dir=tmp_path / "snapshots")
    result = build_closing_dataset(
        seasons=[2026], store=store, published_dir=tmp_path / "published"
    )
    assert isinstance(result, pd.DataFrame)
    assert len(result) == 0

def test_empty_dataset_has_correct_columns():
    df = _empty_dataset()
    assert "match_id" in df.columns
    assert "target_log_home_lambda_move" in df.columns
    assert "horizon_seconds" in df.columns

def test_feature_timestamps_before_prediction(tmp_path):
    """Feature timestamps (current market odds) must be <= prediction_timestamp."""
    from wc2026.data.odds_snapshot_store import OddsSnapshotStore
    store = OddsSnapshotStore(base_dir=tmp_path / "snapshots")

    # Inject a snapshot at T-1h
    obs_t = datetime.datetime(2026, 6, 18, 11, 0, tzinfo=datetime.timezone.utc)
    kickoff_t = datetime.datetime(2026, 6, 18, 12, 0, tzinfo=datetime.timezone.utc)
    fake_odds = [{"match_id": 1, "vendor": "draftkings", "moneyline_home_odds": -150,
                  "moneyline_draw_odds": 270, "moneyline_away_odds": 400,
                  "total_value": "2.5", "total_over_odds": -110, "total_under_odds": -110,
                  "updated_at": obs_t.isoformat(), "markets": []}]
    store.append_snapshot(fake_odds, observed_at=obs_t)
    # Verify asof_snapshot respects timestamp
    snap = store.asof_snapshot(1, prediction_timestamp=obs_t - datetime.timedelta(hours=2))
    assert len(snap) == 0  # not returned before it was observed
