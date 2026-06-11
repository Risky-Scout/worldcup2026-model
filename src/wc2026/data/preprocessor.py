"""
Transform raw BDL API responses into modelling-ready DataFrames.

Key outputs
-----------
build_match_dataframe()
    One row per completed match with: home_team, away_team, home_goals,
    away_goals, is_neutral, season, stage, match_weight (time-decay),
    and optional xG columns.

build_team_xg_features()
    Per-team aggregated xG / shots-on-target features for use as
    prior information when refining lambda estimates.
"""
from __future__ import annotations

import math
from datetime import datetime, timezone
from typing import List

import numpy as np
import pandas as pd

# Half-life for time-decay weights: matches played ~180 days ago
# receive approximately half the weight of a match played today.
WEIGHT_HALF_LIFE_DAYS: float = 180.0


def _decay_weight(match_date: str, reference_date: datetime | None = None) -> float:
    """Exponential time-decay weight centred on *reference_date* (default: today)."""
    ref = reference_date or datetime.now(timezone.utc)
    try:
        dt = datetime.fromisoformat(match_date.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return 1.0
    days_ago = (ref - dt).total_seconds() / 86400
    days_ago = max(days_ago, 0.0)
    return math.exp(-math.log(2) * days_ago / WEIGHT_HALF_LIFE_DAYS)


def build_match_dataframe(
    matches: list[dict],
    team_stats: list[dict] | None = None,
    shots: list[dict] | None = None,
    include_xg: bool = True,
    reference_date: datetime | None = None,
) -> pd.DataFrame:
    """
    Build the primary modelling DataFrame from raw BDL match objects.

    Parameters
    ----------
    matches : list[dict]
        Raw match objects from ``DataFetcher.completed_matches()``.
    team_stats : list[dict], optional
        Raw team_match_stats objects for xG enrichment.
    shots : list[dict], optional
        Raw match_shots objects for xG enrichment (alternative to team_stats).
    include_xg : bool
        If True and xG data is available, add ``home_xg`` / ``away_xg`` columns.
    reference_date : datetime, optional
        Reference point for time-decay. Defaults to now.

    Returns
    -------
    pd.DataFrame
        Columns: match_id, season, stage, home_team, away_team, home_goals,
        away_goals, is_neutral, match_date, match_weight,
        [home_xg, away_xg] (optional)
    """
    rows: List[dict] = []

    # Build per-match xG lookup from team_stats if provided
    xg_map: dict[tuple[int, bool], float] = {}
    if team_stats:
        for ts in team_stats:
            mid = ts.get("match_id")
            is_home = ts.get("is_home", False)
            xg = ts.get("expected_goals")
            if mid is not None and xg is not None:
                xg_map[(mid, bool(is_home))] = float(xg)

    # Build per-match xG lookup from shots if team_stats not available
    shots_xg_map: dict[tuple[int, bool], float] = {}
    if shots and not xg_map:
        for s in shots:
            mid = s.get("match_id")
            is_home = s.get("is_home", False)
            xg = s.get("xg")
            if mid is not None and xg is not None:
                key = (mid, bool(is_home))
                shots_xg_map[key] = shots_xg_map.get(key, 0.0) + float(xg)

    effective_xg = xg_map or shots_xg_map

    for m in matches:
        if m.get("status") != "completed":
            continue

        home_team = (m.get("home_team") or {}).get("name")
        away_team = (m.get("away_team") or {}).get("name")
        home_goals = m.get("home_score")
        away_goals = m.get("away_score")

        if any(v is None for v in (home_team, away_team, home_goals, away_goals)):
            continue

        season = (m.get("season") or {}).get("year")
        stage = (m.get("stage") or {}).get("name", "Unknown")
        match_date = m.get("datetime", "")
        mid = m.get("id")

        # All World Cup matches are at neutral venues from the perspective of
        # both nations (hosted in USA / Canada / Mexico). However we keep
        # a "home_team" flag because the nominally designated home side may
        # still benefit from crowd proximity in certain cities.
        # Set is_neutral=True for all knockout stage matches; group stage
        # matches retain a soft home advantage for the host nations.
        host_teams = {"United States", "USA", "Canada", "CAN", "Mexico", "MEX"}
        is_neutral = home_team not in host_teams

        weight = _decay_weight(match_date, reference_date)

        row: dict = {
            "match_id": mid,
            "season": season,
            "stage": stage,
            "home_team": home_team,
            "away_team": away_team,
            "home_goals": int(home_goals),
            "away_goals": int(away_goals),
            "is_neutral": int(is_neutral),
            "match_date": match_date,
            "match_weight": weight,
        }

        if include_xg and effective_xg:
            row["home_xg"] = effective_xg.get((mid, True), np.nan)
            row["away_xg"] = effective_xg.get((mid, False), np.nan)

        rows.append(row)

    df = pd.DataFrame(rows)
    if df.empty:
        return df

    df["match_date"] = pd.to_datetime(df["match_date"], utc=True, errors="coerce")
    df = df.sort_values("match_date").reset_index(drop=True)
    return df


def build_team_xg_features(
    team_stats: list[dict],
    matches: list[dict],
) -> pd.DataFrame:
    """
    Aggregate per-team xG and shot statistics across all matches.

    Returns a DataFrame indexed by ``team_name`` with columns:
    avg_xg_for, avg_xg_against, avg_shots_on_target_for,
    avg_shots_on_target_against, n_matches.
    """
    team_id_to_name: dict[int, str] = {}
    for m in matches:
        for side in ("home_team", "away_team"):
            t = m.get(side) or {}
            if t.get("id") and t.get("name"):
                team_id_to_name[t["id"]] = t["name"]

    records: list[dict] = []
    for ts in team_stats:
        team_id = ts.get("team_id")
        team_name = team_id_to_name.get(team_id, f"team_{team_id}")
        is_home = ts.get("is_home", False)
        mid = ts.get("match_id")

        # Find the match to get opponent xG
        records.append(
            {
                "team_name": team_name,
                "team_id": team_id,
                "match_id": mid,
                "is_home": is_home,
                "xg_for": ts.get("expected_goals") or np.nan,
                "shots_on_target_for": ts.get("shots_on_target") or np.nan,
            }
        )

    if not records:
        return pd.DataFrame()

    df = pd.DataFrame(records)

    # Pair home/away rows to get opponent stats
    home = df[df["is_home"]].rename(
        columns={"xg_for": "home_xg", "shots_on_target_for": "home_sot"}
    )[["match_id", "team_id", "team_name", "home_xg", "home_sot"]]
    away = df[~df["is_home"]].rename(
        columns={"xg_for": "away_xg", "shots_on_target_for": "away_sot"}
    )[["match_id", "team_id", "team_name", "away_xg", "away_sot"]]

    merged = home.merge(away, on="match_id", suffixes=("_home", "_away"))

    agg_home = (
        merged.groupby("team_name_home")
        .agg(
            xg_for=("home_xg", "mean"),
            xg_against=("away_xg", "mean"),
            sot_for=("home_sot", "mean"),
            sot_against=("away_sot", "mean"),
            n=("match_id", "count"),
        )
        .rename_axis("team_name")
    )
    agg_away = (
        merged.groupby("team_name_away")
        .agg(
            xg_for=("away_xg", "mean"),
            xg_against=("home_xg", "mean"),
            sot_for=("away_sot", "mean"),
            sot_against=("home_sot", "mean"),
            n=("match_id", "count"),
        )
        .rename_axis("team_name")
    )

    combined = pd.concat([agg_home, agg_away]).groupby("team_name").mean()
    return combined
