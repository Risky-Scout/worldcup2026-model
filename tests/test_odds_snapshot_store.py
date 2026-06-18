import tempfile, datetime, pytest
from wc2026.data.odds_snapshot_store import OddsSnapshotStore

FAKE_ODDS = [{"match_id": 1, "vendor": "draftkings", "moneyline_home_odds": -150, "moneyline_draw_odds": 270, "moneyline_away_odds": 400, "total_value": "2.5", "total_over_odds": -110, "total_under_odds": -110, "updated_at": "2026-06-18T12:00:00Z", "markets": []}]

def make_store():
    d = tempfile.mkdtemp()
    return OddsSnapshotStore(base_dir=d)

def test_two_snapshots_retained():
    store = make_store()
    t1 = datetime.datetime(2026, 6, 18, 10, 0, tzinfo=datetime.timezone.utc)
    t2 = datetime.datetime(2026, 6, 18, 11, 0, tzinfo=datetime.timezone.utc)
    store.append_snapshot(FAKE_ODDS, observed_at=t1)
    store.append_snapshot(FAKE_ODDS, observed_at=t2)  # different observed_at → different hash context
    df = store.load_snapshots(match_id=1)
    assert len(df) >= 2  # both retained

def test_asof_returns_only_before_timestamp():
    store = make_store()
    t1 = datetime.datetime(2026, 6, 18, 10, 0, tzinfo=datetime.timezone.utc)
    t2 = datetime.datetime(2026, 6, 18, 11, 0, tzinfo=datetime.timezone.utc)
    store.append_snapshot(FAKE_ODDS, observed_at=t1)
    store.append_snapshot(FAKE_ODDS, observed_at=t2)
    df = store.asof_snapshot(1, prediction_timestamp=datetime.datetime(2026, 6, 18, 10, 30, tzinfo=datetime.timezone.utc))
    assert all(df["observed_at"] <= datetime.datetime(2026, 6, 18, 10, 30, tzinfo=datetime.timezone.utc))

def test_backfill_excluded_by_default():
    store = make_store()
    t1 = datetime.datetime(2026, 6, 18, 10, 0, tzinfo=datetime.timezone.utc)
    store.append_snapshot(FAKE_ODDS, observed_at=t1, ingestion_run_id="backfill")
    df = store.asof_snapshot(1, prediction_timestamp=t1 + datetime.timedelta(hours=1))
    assert len(df) == 0  # backfill excluded

def test_append_twice_no_overwrite():
    store = make_store()
    t1 = datetime.datetime(2026, 6, 18, 10, 0, tzinfo=datetime.timezone.utc)
    n1 = store.append_snapshot(FAKE_ODDS, observed_at=t1)
    n2 = store.append_snapshot(FAKE_ODDS, observed_at=t1)  # same observed_at → same hash → skip
    assert n2 == 0  # no duplicates inserted
