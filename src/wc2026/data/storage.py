"""
Raw BDL snapshot storage + versioned Parquet tables.

Raw layer
---------
Every API response is written to:
  data/raw/bdl/{season}/{endpoint}/{iso_timestamp}.jsonl

One record per line (JSONL format). Idempotent — existing snapshots are not
overwritten; a new timestamp file is created each time the endpoint is called.

Processed layer
---------------
Normalised Parquet tables are written to:
  data/processed/{data_version}/{table}.parquet

Overwritten each time `build_dataset` is called. The data_version string
(e.g. "v1") provides coarse versioning. Fine-grained reproducibility relies
on the raw snapshots.
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from wc2026.config import DATA_VERSION, PROCESSED_DIR, RAW_DIR, DATA_DIR

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Raw snapshot
# ---------------------------------------------------------------------------

def snapshot_raw(
    endpoint: str,
    season: int | str,
    records: list[dict],
) -> Path:
    """
    Write raw API records to a timestamped JSONL file.

    Returns the path of the written file.
    """
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_dir = RAW_DIR / str(season) / endpoint
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{ts}.jsonl"

    with open(out_path, "w", encoding="utf-8") as fh:
        for rec in records:
            fh.write(json.dumps(rec, default=str) + "\n")

    log.info("Snapshotted %d records → %s", len(records), out_path)
    return out_path


def load_latest_raw(endpoint: str, season: int | str) -> list[dict]:
    """Load the most recently created snapshot for an endpoint/season."""
    snap_dir = RAW_DIR / str(season) / endpoint
    if not snap_dir.exists():
        return []
    files = sorted(snap_dir.glob("*.jsonl"))
    if not files:
        return []
    latest = files[-1]
    records = []
    with open(latest, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    log.info("Loaded %d records from %s", len(records), latest)
    return records


# ---------------------------------------------------------------------------
# Processed Parquet tables
# ---------------------------------------------------------------------------

_PROCESSED_TABLES = [
    "matches",
    "odds",
    "events",
    "shots",
    "team_stats",
    "player_stats",
    "lineups",
    "momentum",
    "group_standings",
    "team_form",
]


def _table_path(table_name: str, version: str | None = None) -> Path:
    v = version or DATA_VERSION
    out = PROCESSED_DIR / v
    out.mkdir(parents=True, exist_ok=True)
    return out / f"{table_name}.parquet"


def write_table(table_name: str, df: pd.DataFrame, version: str | None = None) -> Path:
    """Write a Parquet table, overwriting any existing version."""
    path = _table_path(table_name, version)
    table = pa.Table.from_pandas(df, preserve_index=False)
    pq.write_table(table, path, compression="snappy")
    log.info("Wrote %s rows → %s", len(df), path)
    return path


def read_table(table_name: str, version: str | None = None) -> pd.DataFrame:
    """Read a Parquet table. Raises FileNotFoundError if missing."""
    path = _table_path(table_name, version)
    if not path.exists():
        raise FileNotFoundError(
            f"Processed table '{table_name}' (version={version or DATA_VERSION}) not found. "
            f"Run `make build-dataset` first."
        )
    return pd.read_parquet(path)


def table_exists(table_name: str, version: str | None = None) -> bool:
    return _table_path(table_name, version).exists()


def list_versions() -> list[str]:
    """List all processed data versions."""
    if not PROCESSED_DIR.exists():
        return []
    return sorted(d.name for d in PROCESSED_DIR.iterdir() if d.is_dir())


def write_table_append(table_name: str, df: pd.DataFrame, base_path: Path | None = None) -> Path:
    """Append rows to a partitioned Parquet dataset without overwriting."""
    path = base_path or (DATA_DIR / "processed" / "v1" / f"{table_name}.parquet")
    table = pa.Table.from_pandas(df, preserve_index=False)
    pq.write_to_dataset(table, root_path=str(path.parent), partition_cols=None)
    return path


_PMF_LAYERS_DIR = DATA_DIR / "predictions" / "pmf_layers"


def append_pmf_layer(layer_record: dict) -> None:
    """Append a single PMF layer record to the append-only Parquet store."""
    season = layer_record.get("season", 2026)
    out_dir = _PMF_LAYERS_DIR / str(season)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "pmf_layers.parquet"

    # Convert pmf array to bytes
    record = dict(layer_record)
    if isinstance(record.get("pmf_flat"), np.ndarray):
        record["pmf_flat"] = record["pmf_flat"].astype(np.float64).tobytes()

    df_new = pd.DataFrame([record])

    if out_path.exists():
        existing = pd.read_parquet(out_path)
        df_combined = pd.concat([existing, df_new], ignore_index=True)
    else:
        df_combined = df_new

    df_combined.to_parquet(out_path, index=False, compression="snappy")


def load_pmf_layers(season: int = 2026, match_id: int | None = None) -> pd.DataFrame:
    """Load PMF layers from store, optionally filtered by match_id."""
    out_path = _PMF_LAYERS_DIR / str(season) / "pmf_layers.parquet"
    if not out_path.exists():
        return pd.DataFrame()
    df = pd.read_parquet(out_path)
    if match_id is not None:
        df = df[df["match_id"] == match_id]
    return df
