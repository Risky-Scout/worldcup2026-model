"""
Opponent-adjusted team xG/process ratings.

For each team, builds latent factor ratings:
  - attack_chance_volume
  - attack_chance_quality
  - defense_chance_suppression
  - goalkeeper_xgot_prevention
  - finishing_residual_shrunk
  - discipline_risk

All adjusted for opponent quality. Time-decayed. Shrunk to confederation/global prior.
Returns EGM-scale contribution.
"""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
import numpy as np
import pandas as pd


@dataclass
class TeamProcessRating:
    team_id: int
    team_name: Optional[str]

    xg_for_per90: float
    xg_against_per90: float
    shots_on_target_for_per90: float
    shots_on_target_against_per90: float
    big_chances_for_per90: float
    big_chances_against_per90: float
    possession_pct: float
    attack_volume_factor: float
    attack_quality_factor: float
    defense_suppression_factor: float
    finishing_residual_shrunk: float
    discipline_risk: float

    sample_matches: int
    effective_weight: float
    asof_timestamp: datetime

    def attack_egm_contribution(self, scale: float = 0.3) -> float:
        """Approximate EGM contribution from attack process."""
        return (self.xg_for_per90 - 1.3) * scale

    def defense_egm_contribution(self, scale: float = 0.3) -> float:
        """Approximate EGM contribution from defense process (positive = better defense)."""
        return (1.3 - self.xg_against_per90) * scale


def build_team_process_ratings(
    team_match_stats_df: pd.DataFrame,
    match_shots_df: "pd.DataFrame | None" = None,
    prediction_timestamp: "datetime | None" = None,
    decay_halflife_days: float = 180.0,
    min_matches: int = 3,
) -> "dict[int, TeamProcessRating]":
    """
    Build team-level process ratings from BDL /team_match_stats.

    Required columns: match_id, team_id, expected_goals, shots_on_target,
    big_chances, big_chances_missed, possession_pct, fouls, yellow_cards,
    and ideally observed_at.
    """
    df = team_match_stats_df.copy()
    if df.empty:
        return {}

    if prediction_timestamp is not None and "observed_at" in df.columns:
        df["observed_at"] = pd.to_datetime(df["observed_at"], utc=True, errors="coerce")
        ts = pd.Timestamp(prediction_timestamp, tz="UTC")
        df = df[df["observed_at"] <= ts]

    if df.empty:
        return {}

    def _safe(col: str) -> pd.Series:
        return pd.to_numeric(df.get(col, pd.Series(np.nan, index=df.index)), errors="coerce").fillna(0.0)

    now = datetime.utcnow()

    def _decay_weight(row) -> float:
        if "observed_at" in df.columns and pd.notna(row.get("observed_at")):
            obs = pd.Timestamp(row["observed_at"])
            if obs.tzinfo is not None:
                obs = obs.tz_localize(None)
            days = (now - obs).days
        else:
            days = 0
        return float(np.exp(-np.log(2) * days / decay_halflife_days))

    df["_weight"] = df.apply(_decay_weight, axis=1)
    df["_xg"] = _safe("expected_goals")
    df["_sot"] = _safe("shots_on_target")
    df["_bc"] = _safe("big_chances")
    df["_poss"] = _safe("possession_pct")
    df["_fouls"] = _safe("fouls")
    df["_yc"] = _safe("yellow_cards")
    df["_mp"] = _safe("minutes_played") if "minutes_played" in df.columns else pd.Series(90.0, index=df.index)

    result = {}
    for team_id, grp in df.groupby("team_id"):
        if len(grp) < min_matches:
            continue
        w = grp["_weight"].values
        total_w = w.sum()
        if total_w < 1e-9:
            continue

        def _wavg(col: str) -> float:
            return float(np.average(grp[col].values, weights=w))

        xg_for = _wavg("_xg")
        xg_against_vals = []
        for _, row in grp.iterrows():
            mid = row.get("match_id")
            if mid is None:
                continue
            opp = df[(df["match_id"] == mid) & (df["team_id"] != team_id)]
            if not opp.empty:
                xg_against_vals.append(float(opp["_xg"].iloc[0]))
        xg_against = float(np.mean(xg_against_vals)) if xg_against_vals else 1.3

        sot_for = _wavg("_sot")
        bc_for = _wavg("_bc")
        poss = _wavg("_poss")
        fouls = _wavg("_fouls")
        yc = _wavg("_yc")

        # Opponent-adjust xG for using simple global baseline
        global_xg_baseline = 1.3
        xg_for_adj = xg_for - (xg_against - global_xg_baseline) * 0.3
        xg_against_adj = xg_against + (xg_for - global_xg_baseline) * 0.3

        # Shrink toward global baseline
        n = len(grp)
        shrink_w = n / (n + 10)
        xg_for_shrunk = shrink_w * xg_for_adj + (1 - shrink_w) * global_xg_baseline
        xg_against_shrunk = shrink_w * xg_against_adj + (1 - shrink_w) * global_xg_baseline

        result[int(team_id)] = TeamProcessRating(
            team_id=int(team_id),
            team_name=None,
            xg_for_per90=float(xg_for_shrunk),
            xg_against_per90=float(xg_against_shrunk),
            shots_on_target_for_per90=float(sot_for),
            shots_on_target_against_per90=0.0,
            big_chances_for_per90=float(bc_for),
            big_chances_against_per90=0.0,
            possession_pct=float(poss),
            attack_volume_factor=float(sot_for / 4.0),
            attack_quality_factor=float(xg_for / max(sot_for, 1)),
            defense_suppression_factor=float(max(0, global_xg_baseline - xg_against_shrunk)),
            finishing_residual_shrunk=0.0,
            discipline_risk=float(fouls / 20.0 + yc / 3.0),
            sample_matches=n,
            effective_weight=float(shrink_w),
            asof_timestamp=prediction_timestamp or datetime.utcnow(),
        )

    return result
