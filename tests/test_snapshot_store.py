import tempfile
from pathlib import Path
from datetime import datetime, timezone
from src.wc2026.data.snapshot_store import SnapshotStore


def test_append_and_load():
    with tempfile.TemporaryDirectory() as d:
        store = SnapshotStore("test/endpoint", base_dir=Path(d))
        n = store.append([{"match_id": 1, "value": 42}], season=2026)
        assert n == 1
        df = store.load(season=2026)
        assert len(df) == 1
        assert df["match_id"].iloc[0] == 1


def test_no_duplicate_hashes():
    with tempfile.TemporaryDirectory() as d:
        store = SnapshotStore("test/endpoint", base_dir=Path(d))
        store.append([{"match_id": 1, "value": 42}], season=2026)
        n2 = store.append([{"match_id": 1, "value": 42}], season=2026)
        assert n2 == 0  # deduplicated
        df = store.load(season=2026)
        assert len(df) == 1


def test_asof_filter():
    import time
    with tempfile.TemporaryDirectory() as d:
        store = SnapshotStore("test/endpoint", base_dir=Path(d))
        store.append([{"match_id": 1, "v": 1}], season=2026)
        ts_middle = datetime.now(timezone.utc)
        time.sleep(0.01)
        store.append([{"match_id": 1, "v": 2}], season=2026)
        df = store.load(season=2026, asof=ts_middle)
        assert len(df) == 1
        assert df["v"].iloc[0] == 1
