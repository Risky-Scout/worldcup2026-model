"""
Generic immutable append-only snapshot store.
Every snapshot row gets: observed_at, ingestion_run_id, raw_payload_hash, endpoint, season.
Never overwrites historical rows.
"""
from __future__ import annotations
import hashlib, json, uuid
from datetime import datetime, timezone
from pathlib import Path
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

_BASE = Path("data/snapshots")

def _hash(payload: dict | list) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode()).hexdigest()

class SnapshotStore:
    """
    Generic store. Each endpoint has its own sub-directory.
    Rows are deduplicated by raw_payload_hash within (endpoint, season, match_id/team_id/player_id).
    """
    def __init__(self, endpoint: str, base_dir: Path = _BASE):
        self.endpoint = endpoint
        self.base_dir = base_dir / endpoint.replace("/", "_")
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def append(
        self,
        records: list[dict],
        season: int | None = None,
        run_id: str | None = None,
    ) -> int:
        """Append records; skip exact duplicates (same hash). Returns count written."""
        if not records:
            return 0
        run_id = run_id or str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        rows = []
        for rec in records:
            h = _hash(rec)
            row = dict(rec)
            row["observed_at"] = now
            row["ingestion_run_id"] = run_id
            row["raw_payload_hash"] = h
            row["endpoint"] = self.endpoint
            if season is not None:
                row.setdefault("season", season)
            rows.append(row)
        df = pd.DataFrame(rows)
        path = self.base_dir / f"season_{season or 'all'}.parquet"
        if path.exists():
            existing = pq.read_table(path).to_pandas()
            # deduplicate
            existing_hashes = set(existing["raw_payload_hash"].tolist())
            df = df[~df["raw_payload_hash"].isin(existing_hashes)]
            if df.empty:
                return 0
            combined = pd.concat([existing, df], ignore_index=True)
        else:
            combined = df
        pq.write_table(pa.Table.from_pandas(combined, preserve_index=False), path)
        return len(df)

    def load(
        self,
        season: int | None = None,
        asof: datetime | None = None,
    ) -> pd.DataFrame:
        """Load snapshots, optionally filtered to observed_at <= asof."""
        path = self.base_dir / f"season_{season or 'all'}.parquet"
        if not path.exists():
            return pd.DataFrame()
        df = pq.read_table(path).to_pandas()
        if asof is not None:
            df["observed_at"] = pd.to_datetime(df["observed_at"], utc=True)
            asof_ts = pd.Timestamp(asof)
            if asof_ts.tzinfo is None:
                asof_ts = asof_ts.tz_localize("UTC")
            else:
                asof_ts = asof_ts.tz_convert("UTC")
            df = df[df["observed_at"] <= asof_ts]
        return df
