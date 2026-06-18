import pandas as pd
from datetime import datetime, timezone, timedelta
from src.wc2026.data.asof_join import asof_records

def test_future_rows_excluded():
    now = datetime.now(timezone.utc)
    df = pd.DataFrame([
        {"match_id": 1, "val": "past", "observed_at": (now - timedelta(hours=1)).isoformat()},
        {"match_id": 1, "val": "future", "observed_at": (now + timedelta(hours=1)).isoformat()},
    ])
    result = asof_records(df, prediction_timestamp=now, match_id=1)
    assert len(result) == 1
    assert result["val"].iloc[0] == "past"

def test_match_id_filter():
    now = datetime.now(timezone.utc)
    df = pd.DataFrame([
        {"match_id": 1, "val": "A", "observed_at": (now - timedelta(minutes=10)).isoformat()},
        {"match_id": 2, "val": "B", "observed_at": (now - timedelta(minutes=10)).isoformat()},
    ])
    result = asof_records(df, prediction_timestamp=now, match_id=1)
    assert len(result) == 1
    assert result["val"].iloc[0] == "A"
