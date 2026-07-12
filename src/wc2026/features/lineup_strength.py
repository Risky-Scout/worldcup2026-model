"""
Lineup-based team strength adjustment in log-lambda units.

Produces three states: early_projected, late_projected, confirmed.
lineup_adjustment_log = sum_i P(start_i) * E(minutes_i)/90 * (player_value_i - replacement_value_i)

Does NOT use generic "striker out = -10%" rules.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

import numpy as np
import pandas as pd
from src.wc2026.features.player_strength import _POSITION_GROUPS, PlayerEfficiencyRating


def injury_impact_score(players: list[dict]) -> float:
    """
    Compute injury impact score from a list of player injury dicts.

    players: list of {avg_rating: float, status: 'OUT' | 'GTD' | 'AVAILABLE'}
      OUT  → full weight (1.0)
      GTD  → half weight (0.5)
    """
    score = 0.0
    for p in players:
        status = str(p.get("status", "")).upper()
        if status == "OUT":
            score += float(p.get("avg_rating", 7.0)) * 1.0
        elif status == "GTD":
            score += float(p.get("avg_rating", 7.0)) * 0.5
    return score


def compute_injury_lambda_factor(
    team_name: str,
    injuries_df: pd.DataFrame | None,
    rosters_df: pd.DataFrame | None = None,
) -> float:
    """
    Compute multiplicative injury penalty for a team's attack lambda.

    Formula:
      score = injury_impact_score(players)         # sum of rating × multiplier
      normalized = score / 10.0
      factor = max(0.80, 1.0 - normalized × 0.15)  # cap penalty at −20%

    Returns 1.0 when no injury data is available (neutral / pipeline-safe).
    """
    if injuries_df is None or (hasattr(injuries_df, "empty") and injuries_df.empty):
        return 1.0

    # Filter to this team
    if "team_name" in injuries_df.columns:
        team_inj = injuries_df[injuries_df["team_name"] == team_name]
    elif "team_id" in injuries_df.columns:
        # fall back to filtering impossible without team_id mapping
        team_inj = pd.DataFrame()
    else:
        team_inj = pd.DataFrame()

    if team_inj.empty:
        return 1.0

    players = []
    for _, row in team_inj.iterrows():
        status = str(row.get("status", "")).upper()
        if status not in ("OUT", "GTD"):
            continue

        avg_rating = 7.0
        if rosters_df is not None and not (hasattr(rosters_df, "empty") and rosters_df.empty):
            pid = row.get("player_id")
            if pid is not None and "player_id" in rosters_df.columns and "avg_rating" in rosters_df.columns:
                p_rows = rosters_df[rosters_df["player_id"] == pid]
                if not p_rows.empty:
                    avg_rating = float(p_rows["avg_rating"].dropna().mean() or 7.0)

        players.append({"avg_rating": avg_rating, "status": status})

    score = injury_impact_score(players)
    normalized = score / 10.0
    return max(0.80, 1.0 - normalized * 0.15)


@dataclass
class LineupStrengthState:
    match_id: int
    team_id: int
    state: str   # "early_projected" | "late_projected" | "confirmed"
    predicted_timestamp: datetime

    projected_starting_xi_strength: float
    confirmed_starting_xi_strength: float
    substitute_bench_strength: float
    goalkeeper_strength: float
    attacking_lineup_strength: float
    defensive_lineup_strength: float
    expected_minutes_weighted_strength: float
    replacement_gap: float
    lineup_surprise_score: float
    injury_absence_penalty: float
    gtd_uncertainty_penalty: float

    lineup_adjustment_log: float   # feeds directly into lambda formula


def compute_lineup_adjustment(
    team_id: int,
    match_id: int,
    lineups_df: pd.DataFrame,
    injuries_df: pd.DataFrame,
    player_ratings: dict[int, PlayerEfficiencyRating],
    prediction_timestamp: datetime,
) -> LineupStrengthState:
    """
    Compute lineup adjustment log for a team in a match.

    lineups_df: from /match_lineups, filtered to match_id and team_id
    injuries_df: from /player_injuries, filtered to team_id and observed_at <= ts
    player_ratings: output of build_player_ratings()
    """
    # Filter lineup to this team/match
    lineup = lineups_df[
        (lineups_df["match_id"] == match_id) & (lineups_df["team_id"] == team_id)
    ] if not lineups_df.empty else pd.DataFrame()

    # Determine state
    has_confirmed = not lineup.empty and "is_starter" in lineup.columns
    state = "confirmed" if has_confirmed else "early_projected"

    # Get starters
    if has_confirmed:
        starters = lineup[lineup["is_starter"]]["player_id"].tolist() if "is_starter" in lineup.columns else []
        subs = lineup[lineup.get("is_substitute", pd.Series(False, index=lineup.index))]["player_id"].tolist()
    else:
        starters = []
        subs = []

    # Team average replacement value
    all_team_values = [r.overall_value_per90 for r in player_ratings.values() if r.team_id == team_id]
    avg_team_value = float(np.mean(all_team_values)) if all_team_values else 0.0
    replacement_value = avg_team_value * 0.7   # replacement is 70% of team average

    # Compute lineup strength
    adj_log = 0.0
    attack_strength = 0.0
    defense_strength = 0.0
    gk_strength = 0.0
    total_value = 0.0
    n_starters = 0

    for pid in starters:
        r = player_ratings.get(int(pid))
        if r is None:
            continue
        n_starters += 1
        p_start = 1.0
        exp_mins = 75.0  # expected minutes for starter
        contribution = p_start * (exp_mins / 90.0) * (r.overall_value_per90 - replacement_value)
        adj_log += contribution * 0.05   # scale to log units
        total_value += r.overall_value_per90

        pos_group = _POSITION_GROUPS.get(str(r.primary_position or "").upper(), "unknown")
        if pos_group == "goalkeeper":
            gk_strength += r.goalkeeper_value_per90
        elif pos_group in ("striker", "winger", "attacking_mid"):
            attack_strength += r.attack_value_per90
        elif pos_group in ("center_back", "fullback", "defensive_mid"):
            defense_strength += r.defense_value_per90

    # Injury penalty
    injury_penalty = 0.0
    if not injuries_df.empty:
        injured = injuries_df[
            (injuries_df.get("team_id", pd.Series()) == team_id) &
            (injuries_df.get("status", pd.Series()).isin(["OUT", "out", "doubtful"]))
        ] if "team_id" in injuries_df.columns else pd.DataFrame()
        for _, row in injured.iterrows():
            pid = int(row.get("player_id", row.get("player", {}).get("id", 0) if isinstance(row.get("player"), dict) else 0))
            r = player_ratings.get(pid)
            if r is not None:
                injury_penalty += max(0.0, r.overall_value_per90 - replacement_value) * 0.03

    avg_starter_value = total_value / n_starters if n_starters > 0 else avg_team_value
    bench_value = float(np.mean([player_ratings[int(pid)].overall_value_per90 for pid in subs if int(pid) in player_ratings])) if subs else avg_team_value * 0.8
    replacement_gap = avg_starter_value - bench_value

    return LineupStrengthState(
        match_id=match_id,
        team_id=team_id,
        state=state,
        predicted_timestamp=prediction_timestamp,
        projected_starting_xi_strength=avg_starter_value,
        confirmed_starting_xi_strength=avg_starter_value if has_confirmed else 0.0,
        substitute_bench_strength=bench_value,
        goalkeeper_strength=gk_strength,
        attacking_lineup_strength=attack_strength,
        defensive_lineup_strength=defense_strength,
        expected_minutes_weighted_strength=avg_starter_value,
        replacement_gap=replacement_gap,
        lineup_surprise_score=0.0,   # placeholder
        injury_absence_penalty=injury_penalty,
        gtd_uncertainty_penalty=0.0,
        lineup_adjustment_log=adj_log - injury_penalty,
    )
