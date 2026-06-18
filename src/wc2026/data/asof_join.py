"""
Point-in-time safe as-of join utilities.
"""
from __future__ import annotations
from datetime import datetime
import pandas as pd

def asof_records(
    df: pd.DataFrame,
    prediction_timestamp: datetime,
    observed_at_col: str = "observed_at",
    match_id: int | None = None,
    match_id_col: str = "match_id",
    team_id: int | None = None,
    team_id_col: str = "team_id",
    player_id: int | None = None,
    player_id_col: str = "player_id",
    max_staleness_seconds: int | None = None,
) -> pd.DataFrame:
    """
    Return rows where observed_at <= prediction_timestamp.
    Optionally filter by match_id, team_id, player_id.
    If max_staleness_seconds is set, also require observed_at >= prediction_timestamp - max_staleness_seconds.
    Never returns future rows.
    """
    if df.empty:
        return df
    df = df.copy()
    df[observed_at_col] = pd.to_datetime(df[observed_at_col], utc=True)
    ts = pd.Timestamp(prediction_timestamp)
    if ts.tzinfo is None:
        ts = ts.tz_localize("UTC")
    else:
        ts = ts.tz_convert("UTC")
    mask = df[observed_at_col] <= ts
    if max_staleness_seconds is not None:
        from datetime import timedelta
        stale_cutoff = ts - pd.Timedelta(seconds=max_staleness_seconds)
        mask = mask & (df[observed_at_col] >= stale_cutoff)
    if match_id is not None and match_id_col in df.columns:
        mask = mask & (df[match_id_col] == match_id)
    if team_id is not None and team_id_col in df.columns:
        mask = mask & (df[team_id_col] == team_id)
    if player_id is not None and player_id_col in df.columns:
        mask = mask & (df[player_id_col] == player_id)
    return df[mask].reset_index(drop=True)
