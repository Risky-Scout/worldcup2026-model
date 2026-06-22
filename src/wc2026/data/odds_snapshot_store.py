"""
Append-only odds snapshot store backed by partitioned Parquet.

Stores every fetched BDL odds row with a SHA-256 hash for deduplication.
Partitioned by season: data/odds_snapshots/season={season}/
"""
from __future__ import annotations

import hashlib
import json
import logging
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

log = logging.getLogger(__name__)

_DEFAULT_BASE_DIR = Path("data/odds_snapshots")

_SCHEMA = pa.schema([
    pa.field("match_id", pa.int64()),
    pa.field("vendor", pa.string()),
    pa.field("market_type", pa.string()),
    pa.field("period", pa.string()),
    pa.field("outcome", pa.string()),
    pa.field("side", pa.string()),
    pa.field("line", pa.string()),
    pa.field("decimal_odds", pa.float64()),
    pa.field("american_odds", pa.int64()),
    pa.field("source_updated_at", pa.timestamp("us", tz="UTC")),
    pa.field("observed_at", pa.timestamp("us", tz="UTC")),
    pa.field("kickoff_at", pa.timestamp("us", tz="UTC")),
    pa.field("seconds_to_kickoff", pa.float64()),
    pa.field("is_live", pa.bool_()),
    pa.field("is_suspended", pa.bool_()),
    pa.field("raw_payload_hash", pa.string()),
    pa.field("ingestion_run_id", pa.string()),
    pa.field("season", pa.int32()),
    pa.field("endpoint", pa.string()),
    pa.field("raw_source_path", pa.string()),
])


class OddsSnapshotStore:
    def __init__(self, base_dir=None):
        if base_dir is None:
            base_dir = _DEFAULT_BASE_DIR
        self._base_dir = Path(base_dir)
        self._base_dir.mkdir(parents=True, exist_ok=True)

    def append_snapshot(
        self,
        raw_payload: list[dict],
        observed_at: datetime,
        ingestion_run_id: str = "live",
        season: int = 2026,
        endpoint: str = "odds",
        raw_source_path: str = "",
    ) -> int:
        """Flatten BDL odds rows, deduplicate by hash, append new rows. Returns count appended."""
        if not raw_payload:
            return 0

        rows = self._flatten_payload(raw_payload, observed_at, ingestion_run_id, season, endpoint, raw_source_path)
        if not rows:
            return 0

        # Load existing hashes to deduplicate
        existing_hashes = self._load_existing_hashes(season)

        new_rows = [r for r in rows if r["raw_payload_hash"] not in existing_hashes]
        if not new_rows:
            return 0

        df_new = pd.DataFrame(new_rows)
        df_new = self._cast_types(df_new)

        out_dir = self._base_dir / f"season={season}"
        out_dir.mkdir(parents=True, exist_ok=True)

        table = pa.Table.from_pandas(df_new, preserve_index=False)
        # Write each batch as a timestamped file so repeated calls append
        ts = observed_at.strftime("%Y%m%dT%H%M%SZ") if hasattr(observed_at, "strftime") else "unknown"
        out_path = out_dir / f"{ts}_{ingestion_run_id}.parquet"
        # Handle duplicate filenames by adding a counter
        counter = 0
        while out_path.exists():
            counter += 1
            out_path = out_dir / f"{ts}_{ingestion_run_id}_{counter}.parquet"
        pq.write_table(table, out_path, compression="snappy")
        log.info("OddsSnapshotStore: appended %d rows → %s", len(new_rows), out_path)
        return len(new_rows)

    def load_snapshots(self, match_id=None, start=None, end=None) -> pd.DataFrame:
        """Load all parquet files from the store, optionally filtered."""
        frames = []
        for f in sorted(self._base_dir.glob("**/*.parquet")):
            try:
                df = pd.read_parquet(f)
                frames.append(df)
            except Exception as e:
                log.warning("Failed to read %s: %s", f, e)

        if not frames:
            return pd.DataFrame()

        df = pd.concat(frames, ignore_index=True)

        if "observed_at" in df.columns:
            df["observed_at"] = pd.to_datetime(df["observed_at"], utc=True, errors="coerce")

        if match_id is not None:
            df = df[df["match_id"] == int(match_id)]

        if start is not None:
            start_ts = pd.Timestamp(start, tz="UTC") if not hasattr(start, "tzinfo") else pd.Timestamp(start)
            df = df[df["observed_at"] >= start_ts]

        if end is not None:
            end_ts = pd.Timestamp(end, tz="UTC") if not hasattr(end, "tzinfo") else pd.Timestamp(end)
            df = df[df["observed_at"] <= end_ts]

        return df.reset_index(drop=True)

    def asof_snapshot(
        self,
        match_id: int,
        prediction_timestamp: datetime,
        max_staleness_hours: Optional[float] = None,
        exclude_backfill: bool = True,
    ) -> pd.DataFrame:
        """Return rows where observed_at <= prediction_timestamp."""
        df = self.load_snapshots(match_id=match_id)
        if df.empty:
            return df

        if "observed_at" not in df.columns:
            return pd.DataFrame()

        df["observed_at"] = pd.to_datetime(df["observed_at"], utc=True, errors="coerce")
        pred_ts = pd.Timestamp(prediction_timestamp, tz="UTC") if prediction_timestamp.tzinfo is None else pd.Timestamp(prediction_timestamp)

        df = df[df["observed_at"] <= pred_ts]

        if exclude_backfill and "ingestion_run_id" in df.columns:
            df = df[df["ingestion_run_id"] != "backfill"]

        if max_staleness_hours is not None and "source_updated_at" in df.columns:
            df["source_updated_at"] = pd.to_datetime(df["source_updated_at"], utc=True, errors="coerce")
            cutoff = pred_ts - pd.Timedelta(hours=max_staleness_hours)
            df = df[df["source_updated_at"] >= cutoff]

        return df.reset_index(drop=True)

    def closing_snapshot(self, match_id: int, close_before_minutes: int = 3) -> pd.DataFrame:
        """Return rows observed at or before kickoff minus close_before_minutes."""
        df = self.load_snapshots(match_id=match_id)
        if df.empty:
            return df

        if "kickoff_at" not in df.columns or "observed_at" not in df.columns:
            return pd.DataFrame()

        df["observed_at"] = pd.to_datetime(df["observed_at"], utc=True, errors="coerce")
        df["kickoff_at"] = pd.to_datetime(df["kickoff_at"], utc=True, errors="coerce")

        valid = df.dropna(subset=["kickoff_at"])
        if valid.empty:
            return pd.DataFrame()

        cutoff = valid["kickoff_at"] - pd.Timedelta(minutes=close_before_minutes)
        valid = valid[valid["observed_at"] <= cutoff]
        if valid.empty:
            return pd.DataFrame()

        # Return the latest observed batch for that match
        latest_obs = valid["observed_at"].max()
        result = valid[valid["observed_at"] == latest_obs]
        return result.reset_index(drop=True)

    # -----------------------------------------------------------------------
    # Private helpers
    # -----------------------------------------------------------------------

    def _flatten_payload(
        self,
        raw_payload: list[dict],
        observed_at: datetime,
        ingestion_run_id: str,
        season: int,
        endpoint: str,
        raw_source_path: str,
    ) -> list[dict]:
        """Flatten BDL odds rows into schema rows."""
        rows = []
        obs_ts = _ensure_utc(observed_at)

        for raw in raw_payload:
            match_id = raw.get("match_id")
            vendor = str(raw.get("vendor", "unknown"))
            updated_at_raw = raw.get("updated_at")
            source_updated_at = _parse_ts(updated_at_raw) or obs_ts

            # Kickoff from raw row (may not be present)
            kickoff_at = _parse_ts(raw.get("kickoff_at") or raw.get("kickoff"))
            seconds_to_kickoff = None
            if kickoff_at is not None:
                seconds_to_kickoff = (kickoff_at - obs_ts).total_seconds()

            # Top-level moneyline
            if raw.get("moneyline_home_odds") is not None:
                for outcome_name, outcome_key, side in [
                    ("home", "moneyline_home_odds", "home"),
                    ("draw", "moneyline_draw_odds", "draw"),
                    ("away", "moneyline_away_odds", "away"),
                ]:
                    amer = _safe_int(raw.get(outcome_key))
                    dec = _amer_to_dec(amer) if amer is not None else None
                    row = _make_row(
                        match_id=match_id, vendor=vendor,
                        market_type="moneyline", period="match",
                        outcome=outcome_name, side=side, line=None,
                        decimal_odds=dec, american_odds=amer,
                        source_updated_at=source_updated_at, observed_at=obs_ts,
                        kickoff_at=kickoff_at, seconds_to_kickoff=seconds_to_kickoff,
                        ingestion_run_id=ingestion_run_id, season=season,
                        endpoint=endpoint, raw_source_path=raw_source_path,
                    )
                    rows.append(row)

            # Top-level total
            if raw.get("total_value") is not None and raw.get("total_over_odds") is not None:
                total_val = str(raw.get("total_value", ""))
                for outcome_name, odds_key in [("over", "total_over_odds"), ("under", "total_under_odds")]:
                    amer = _safe_int(raw.get(odds_key))
                    dec = _amer_to_dec(amer) if amer is not None else None
                    row = _make_row(
                        match_id=match_id, vendor=vendor,
                        market_type="total", period="match",
                        outcome=outcome_name, side=None, line=total_val,
                        decimal_odds=dec, american_odds=amer,
                        source_updated_at=source_updated_at, observed_at=obs_ts,
                        kickoff_at=kickoff_at, seconds_to_kickoff=seconds_to_kickoff,
                        ingestion_run_id=ingestion_run_id, season=season,
                        endpoint=endpoint, raw_source_path=raw_source_path,
                    )
                    rows.append(row)

            # markets[] sub-array
            for mkt in raw.get("markets", []):
                mkt_type = str(mkt.get("type", ""))
                mkt_period = str(mkt.get("period", "match"))
                line_val = str(mkt.get("line_value", "")) if mkt.get("line_value") is not None else None
                for oc in mkt.get("outcomes", []):
                    oc_name = str(oc.get("name", ""))
                    oc_type = str(oc.get("type", ""))
                    amer = _safe_int(oc.get("american_odds"))
                    dec = oc.get("decimal_odds")
                    if dec is not None:
                        try:
                            dec = float(dec)
                        except (TypeError, ValueError):
                            dec = None
                    row = _make_row(
                        match_id=match_id, vendor=vendor,
                        market_type=mkt_type, period=mkt_period,
                        outcome=oc_name, side=oc_type, line=line_val,
                        decimal_odds=dec, american_odds=amer,
                        source_updated_at=source_updated_at, observed_at=obs_ts,
                        kickoff_at=kickoff_at, seconds_to_kickoff=seconds_to_kickoff,
                        ingestion_run_id=ingestion_run_id, season=season,
                        endpoint=endpoint, raw_source_path=raw_source_path,
                    )
                    rows.append(row)

        return rows

    def _load_existing_hashes(self, season: int) -> set:
        """Load all existing raw_payload_hash values for a season."""
        hashes = set()
        season_dir = self._base_dir / f"season={season}"
        if not season_dir.exists():
            return hashes
        for f in sorted(season_dir.glob("*.parquet")):
            try:
                # Use to_pylist() to get native Python strings, bypassing pandas
                # type-inference changes (e.g. StringDtype in pandas 2.3+).
                raw_list = pq.read_table(f, columns=["raw_payload_hash"]).column(0).to_pylist()
                hashes.update(h for h in raw_list if h is not None)
            except Exception as e:
                log.warning("Could not read hashes from %s: %s", f, e)
        return hashes

    def _cast_types(self, df: pd.DataFrame) -> pd.DataFrame:
        """Cast dataframe columns to match schema types."""
        if "match_id" in df.columns:
            df["match_id"] = pd.to_numeric(df["match_id"], errors="coerce").astype("Int64")
        if "american_odds" in df.columns:
            df["american_odds"] = pd.to_numeric(df["american_odds"], errors="coerce").astype("Int64")
        if "decimal_odds" in df.columns:
            df["decimal_odds"] = pd.to_numeric(df["decimal_odds"], errors="coerce")
        if "seconds_to_kickoff" in df.columns:
            df["seconds_to_kickoff"] = pd.to_numeric(df["seconds_to_kickoff"], errors="coerce")
        if "season" in df.columns:
            df["season"] = pd.to_numeric(df["season"], errors="coerce").astype("Int32")
        if "is_live" in df.columns:
            df["is_live"] = df["is_live"].astype(bool)
        if "is_suspended" in df.columns:
            df["is_suspended"] = df["is_suspended"].astype(bool)
        for ts_col in ["observed_at", "source_updated_at", "kickoff_at"]:
            if ts_col in df.columns:
                df[ts_col] = pd.to_datetime(df[ts_col], utc=True, errors="coerce")
        return df


def _make_row(
    match_id, vendor, market_type, period, outcome, side, line,
    decimal_odds, american_odds, source_updated_at, observed_at,
    kickoff_at, seconds_to_kickoff, ingestion_run_id, season, endpoint, raw_source_path,
) -> dict:
    """Build a single schema row with hash."""
    hash_input = json.dumps({
        "match_id": match_id, "vendor": vendor, "market_type": market_type,
        "period": period, "outcome": outcome, "side": side, "line": line,
        "decimal_odds": decimal_odds, "american_odds": american_odds,
        "observed_at": observed_at.isoformat() if observed_at is not None else None,
    }, sort_keys=True)
    raw_payload_hash = hashlib.sha256(hash_input.encode()).hexdigest()

    return {
        "match_id": match_id,
        "vendor": vendor,
        "market_type": market_type,
        "period": period,
        "outcome": outcome,
        "side": side,
        "line": line,
        "decimal_odds": decimal_odds,
        "american_odds": american_odds,
        "source_updated_at": source_updated_at,
        "observed_at": observed_at,
        "kickoff_at": kickoff_at,
        "seconds_to_kickoff": seconds_to_kickoff,
        "is_live": False,
        "is_suspended": False,
        "raw_payload_hash": raw_payload_hash,
        "ingestion_run_id": ingestion_run_id,
        "season": season,
        "endpoint": endpoint,
        "raw_source_path": raw_source_path,
    }


def _ensure_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def _parse_ts(raw) -> Optional[datetime]:
    if raw is None:
        return None
    try:
        if isinstance(raw, datetime):
            return _ensure_utc(raw)
        s = str(raw).strip().replace("Z", "+00:00")
        dt = datetime.fromisoformat(s)
        return _ensure_utc(dt)
    except Exception:
        return None


def _safe_int(v) -> Optional[int]:
    if v is None:
        return None
    try:
        return int(v)
    except (TypeError, ValueError):
        return None


def _amer_to_dec(american: int) -> float:
    if american > 0:
        return american / 100.0 + 1.0
    else:
        return 100.0 / abs(american) + 1.0
