"""
Player efficiency ratings in per-90-minute units.
All ratings are shrunk toward position and team priors.
Point-in-time safe: only use stats observed before prediction_timestamp.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

import pandas as pd


@dataclass
class PlayerEfficiencyRating:
    player_id: int
    player_name: str
    team_id: int
    primary_position: str | None

    minutes_basis: float
    overall_value_per90: float

    attack_value_per90: float
    xg_value_per90: float
    xa_value_per90: float
    shot_value_per90: float
    chance_creation_value_per90: float
    ball_progression_proxy_per90: float

    defense_value_per90: float
    duel_value_per90: float
    aerial_value_per90: float
    pressing_or_recovery_proxy_per90: float
    discipline_risk_per90: float

    goalkeeper_value_per90: float
    xgot_prevention_per90: float
    distribution_value_per90: float

    uncertainty: float
    shrinkage_weight: float
    data_sources: list[str] = field(default_factory=list)
    asof_timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict:
        return {
            "player_id": self.player_id,
            "player_name": self.player_name,
            "team_id": self.team_id,
            "primary_position": self.primary_position,
            "minutes_basis": self.minutes_basis,
            "overall_value_per90": self.overall_value_per90,
            "attack_value_per90": self.attack_value_per90,
            "xg_value_per90": self.xg_value_per90,
            "xa_value_per90": self.xa_value_per90,
            "goalkeeper_value_per90": self.goalkeeper_value_per90,
            "xgot_prevention_per90": self.xgot_prevention_per90,
            "uncertainty": self.uncertainty,
            "shrinkage_weight": self.shrinkage_weight,
            "data_sources": self.data_sources,
            "asof_timestamp": self.asof_timestamp.isoformat() if self.asof_timestamp else None,
        }


_POSITION_GROUPS = {
    "GK": "goalkeeper",
    "CB": "center_back",
    "RB": "fullback", "LB": "fullback", "RWB": "fullback", "LWB": "fullback",
    "CDM": "defensive_mid", "DM": "defensive_mid",
    "CM": "central_mid", "CAM": "attacking_mid", "AM": "attacking_mid",
    "RW": "winger", "LW": "winger", "RM": "winger", "LM": "winger",
    "ST": "striker", "CF": "striker", "SS": "striker",
}

_MIN_MINUTES = 90.0  # minimum for non-zero rating
_SHRINKAGE_BASE = 300.0  # pseudo-observation minutes for prior


def _per90(value: float, minutes: float) -> float:
    if minutes < 1:
        return 0.0
    return value * 90.0 / minutes


def _shrink(observed: float, minutes: float, prior: float = 0.0) -> tuple[float, float]:
    """James-Stein style shrinkage. Returns (shrunk_value, shrinkage_weight)."""
    w = minutes / (minutes + _SHRINKAGE_BASE)
    return w * observed + (1 - w) * prior, w


def build_player_ratings(
    player_match_stats_df: pd.DataFrame,
    match_shots_df: pd.DataFrame | None = None,
    prediction_timestamp: datetime | None = None,
    position_map: dict[int, str] | None = None,
) -> dict[int, PlayerEfficiencyRating]:
    """
    Build per-player ratings from BDL /player_match_stats and /match_shots.

    player_match_stats_df columns (from BDL):
      player_id, player_name (optional), team_id, minutes_played,
      expected_goals, expected_assists, goals, assists,
      shots_on_target, key_passes, big_chances_created, big_chances_missed,
      tackles, tackles_won, interceptions, clearances, blocked_shots,
      duels_won, duels_lost, aerial_duels_won, aerial_duels_lost,
      fouls_committed, saves, saves_inside_box, high_claims, punches,
      passes_total, passes_accurate, long_balls_total, long_balls_accurate,
      ball_recoveries, rating, observed_at (optional)

    Returns dict: player_id -> PlayerEfficiencyRating
    """
    df = player_match_stats_df.copy()
    if df.empty:
        return {}

    # Point-in-time filter
    if prediction_timestamp is not None and "observed_at" in df.columns:
        df["observed_at"] = pd.to_datetime(df["observed_at"], utc=True, errors="coerce")
        ts = pd.Timestamp(prediction_timestamp)
        if ts.tzinfo is None:
            ts = ts.tz_localize("UTC")
        else:
            ts = ts.tz_convert("UTC")
        df = df[df["observed_at"] <= ts]

    if df.empty:
        return {}

    def _safe(col: str) -> pd.Series:
        if col in df.columns:
            return pd.to_numeric(df[col], errors="coerce").fillna(0.0)
        return pd.Series(0.0, index=df.index)

    # Aggregate by player
    df["_mp"] = _safe("minutes_played")
    df["_xg"] = _safe("expected_goals")
    df["_xa"] = _safe("expected_assists")
    df["_sot"] = _safe("shots_on_target")
    df["_kp"] = _safe("key_passes")
    df["_bcc"] = _safe("big_chances_created")
    df["_bcm"] = _safe("big_chances_missed")
    df["_tck"] = _safe("tackles_won")
    df["_int"] = _safe("interceptions")
    df["_clr"] = _safe("clearances")
    df["_blk"] = _safe("blocked_shots")
    df["_dw"] = _safe("duels_won")
    df["_dl"] = _safe("duels_lost")
    df["_adw"] = _safe("aerial_duels_won")
    df["_adl"] = _safe("aerial_duels_lost")
    df["_foul"] = _safe("fouls_committed")
    df["_saves"] = _safe("saves")
    df["_sib"] = _safe("saves_inside_box")
    df["_hcl"] = _safe("high_claims")
    df["_br"] = _safe("ball_recoveries")
    df["_pa"] = _safe("passes_accurate")
    df["_pt"] = _safe("passes_total")
    df["_lba"] = _safe("long_balls_accurate")
    df["_lbt"] = _safe("long_balls_total")

    agg_cols = [c for c in df.columns if c.startswith("_")]
    player_id_col = "player_id"
    if player_id_col not in df.columns:
        return {}

    grp = df.groupby(player_id_col)[agg_cols].sum().reset_index()

    ratings = {}
    for _, row in grp.iterrows():
        pid = int(row[player_id_col])
        mp = float(row.get("_mp", 0.0))
        if mp < _MIN_MINUTES:
            mp = _MIN_MINUTES  # use minimum for shrinkage denominator

        pos_raw = (position_map or {}).get(pid)
        pos_group = _POSITION_GROUPS.get(str(pos_raw).upper(), "unknown") if pos_raw else "unknown"

        xg = float(row.get("_xg", 0.0))
        xa = float(row.get("_xa", 0.0))
        sot = float(row.get("_sot", 0.0))
        kp = float(row.get("_kp", 0.0))
        bcc = float(row.get("_bcc", 0.0))
        saves = float(row.get("_saves", 0.0))
        sib = float(row.get("_sib", 0.0))
        float(row.get("_hcl", 0.0))
        tck = float(row.get("_tck", 0.0))
        inter = float(row.get("_int", 0.0))
        clr = float(row.get("_clr", 0.0))
        float(row.get("_blk", 0.0))
        dw = float(row.get("_dw", 0.0))
        dl = float(row.get("_dl", 0.0))
        adw = float(row.get("_adw", 0.0))
        adl = float(row.get("_adl", 0.0))
        foul = float(row.get("_foul", 0.0))
        br = float(row.get("_br", 0.0))
        pa = float(row.get("_pa", 0.0))
        pt = float(row.get("_pt", 0.0))
        float(row.get("_lba", 0.0))
        float(row.get("_lbt", 0.0))

        # Attack components per90
        xg90_raw = _per90(xg, mp)
        xa90_raw = _per90(xa, mp)
        sot90_raw = _per90(sot, mp)
        kp90_raw = _per90(kp, mp)
        bcc90_raw = _per90(bcc, mp)

        # Defense components per90
        tck90_raw = _per90(tck, mp)
        int90_raw = _per90(inter, mp)
        clr90_raw = _per90(clr, mp)
        br90_raw = _per90(br, mp)
        duel_win_rate = dw / (dw + dl) if (dw + dl) > 0 else 0.5
        aerial_win_rate = adw / (adw + adl) if (adw + adl) > 0 else 0.5
        disc_risk_raw = _per90(foul, mp)

        # GK components per90
        saves90_raw = _per90(saves + sib, mp)
        dist_eff_raw = pa / pt if pt > 0 else 0.5

        # Shrink everything
        xg90, sw = _shrink(xg90_raw, mp)
        xa90, _ = _shrink(xa90_raw, mp)
        sot90, _ = _shrink(sot90_raw, mp)
        kp90, _ = _shrink(kp90_raw, mp)
        bcc90, _ = _shrink(bcc90_raw, mp)
        tck90, _ = _shrink(tck90_raw, mp)
        int90, _ = _shrink(int90_raw, mp)
        clr90, _ = _shrink(clr90_raw, mp)
        br90, _ = _shrink(br90_raw, mp)
        saves90, _ = _shrink(saves90_raw, mp)
        disc_risk, _ = _shrink(disc_risk_raw, mp)

        # Composite scores by position
        attack_v = xg90 * 2.0 + xa90 * 1.5 + bcc90 * 0.5 + sot90 * 0.3 + kp90 * 0.2
        defense_v = tck90 * 0.8 + int90 * 0.8 + clr90 * 0.3 + br90 * 0.4 + duel_win_rate * 0.5
        gk_v = saves90 * 0.8 + dist_eff_raw * 0.2 + aerial_win_rate * 0.2

        if pos_group == "goalkeeper":
            overall = gk_v
        elif pos_group in ("center_back", "fullback"):
            overall = defense_v * 0.7 + attack_v * 0.3
        elif pos_group == "defensive_mid":
            overall = defense_v * 0.6 + attack_v * 0.4
        elif pos_group in ("central_mid", "attacking_mid"):
            overall = attack_v * 0.6 + defense_v * 0.4
        elif pos_group == "winger":
            overall = attack_v * 0.75 + defense_v * 0.25
        elif pos_group == "striker":
            overall = attack_v * 0.85 + defense_v * 0.15
        else:
            overall = (attack_v + defense_v) / 2

        overall_shrunk, _ = _shrink(overall, mp)
        uncertainty = 1.0 - sw

        player_name = ""
        if "player_name" in df.columns:
            names = df[df[player_id_col] == pid]["player_name"]
            if len(names) > 0:
                player_name = str(names.iloc[0]) if pd.notna(names.iloc[0]) else ""

        team_id = 0
        if "team_id" in df.columns:
            tids = df[df[player_id_col] == pid]["team_id"]
            if len(tids) > 0:
                team_id = int(tids.iloc[0]) if pd.notna(tids.iloc[0]) else 0

        ratings[pid] = PlayerEfficiencyRating(
            player_id=pid,
            player_name=player_name,
            team_id=team_id,
            primary_position=pos_raw,
            minutes_basis=mp,
            overall_value_per90=float(overall_shrunk),
            attack_value_per90=float(attack_v),
            xg_value_per90=float(xg90),
            xa_value_per90=float(xa90),
            shot_value_per90=float(sot90),
            chance_creation_value_per90=float(bcc90),
            ball_progression_proxy_per90=float(kp90),
            defense_value_per90=float(defense_v),
            duel_value_per90=float(duel_win_rate),
            aerial_value_per90=float(aerial_win_rate),
            pressing_or_recovery_proxy_per90=float(br90),
            discipline_risk_per90=float(disc_risk),
            goalkeeper_value_per90=float(gk_v),
            xgot_prevention_per90=float(saves90),
            distribution_value_per90=float(dist_eff_raw),
            uncertainty=float(uncertainty),
            shrinkage_weight=float(sw),
            data_sources=["player_match_stats"],
        )

    return ratings
