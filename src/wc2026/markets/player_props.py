"""
PlayerPropsMarket — model-implied player proposition probabilities.

For each upcoming match, builds model-based player prop probabilities and
compares them against BDL market odds to surface edge opportunities.

Supported prop types
--------------------
- anytime_goal     Player scores at least one goal
- shots_on_target  Player registers at least one shot on target
- shots            Player registers at least one total shot

Algorithm
---------
anytime_goal:
    model_prob = 1 - exp(-xg_rate_90 * (match_xg_total / team_xg_rate) * minutes_expected / 90)
    where xg_rate_90 = player's WC2026 xG per 90 minutes from roster/player_stats.

shots_on_target:
    model_prob = 1 - exp(-sot_rate_90 * minutes_expected / 90)

shots:
    model_prob = 1 - exp(-shot_rate_90 * minutes_expected / 90)

All rates are estimated from the player's tournament stats where available,
falling back to positional averages.
"""
from __future__ import annotations

import logging
import math

import pandas as pd

log = logging.getLogger(__name__)

_EPS = 1e-9

# ── Positional default rates (per 90 min) ─────────────────────────────────
# Used as fallback when player stats are unavailable.
# Sources: 2022 WC aggregate data.
_POS_XG_RATE: dict[str, float] = {
    "FW": 0.35, "CF": 0.38, "ST": 0.38, "SS": 0.28,
    "CAM": 0.18, "AM": 0.18, "OM": 0.18, "RW": 0.22, "LW": 0.22,
    "CM": 0.10, "RM": 0.10, "LM": 0.10, "MF": 0.12,
    "CDM": 0.06, "DM": 0.06, "CB": 0.04, "RB": 0.05, "LB": 0.05,
    "GK": 0.01,
}
_POS_SOT_RATE: dict[str, float] = {
    "FW": 1.20, "CF": 1.30, "ST": 1.30, "SS": 0.95,
    "CAM": 0.65, "AM": 0.65, "OM": 0.65, "RW": 0.80, "LW": 0.80,
    "CM": 0.40, "RM": 0.40, "LM": 0.40, "MF": 0.45,
    "CDM": 0.25, "DM": 0.25, "CB": 0.20, "RB": 0.22, "LB": 0.22,
    "GK": 0.05,
}
_POS_SHOT_RATE: dict[str, float] = {
    "FW": 2.80, "CF": 3.10, "ST": 3.10, "SS": 2.20,
    "CAM": 1.50, "AM": 1.50, "OM": 1.50, "RW": 1.80, "LW": 1.80,
    "CM": 0.90, "RM": 0.90, "LM": 0.90, "MF": 1.00,
    "CDM": 0.55, "DM": 0.55, "CB": 0.45, "RB": 0.55, "LB": 0.55,
    "GK": 0.08,
}


def _pos_key(position: str | None) -> str:
    """Normalize position string to a key in the rate dicts."""
    if not position:
        return "MF"
    pos = str(position).upper().strip()
    for k in _POS_XG_RATE:
        if k in pos:
            return k
    return "MF"


def _poisson_at_least_one(rate_per_90: float, minutes: float) -> float:
    """P(≥1 event) = 1 - exp(-lambda), where lambda = rate * minutes/90."""
    if rate_per_90 <= 0 or minutes <= 0:
        return 0.0
    lam = rate_per_90 * minutes / 90.0
    return float(1.0 - math.exp(-lam))


def _american_to_decimal(a: float) -> float:
    if a >= 100:
        return a / 100.0 + 1.0
    return 100.0 / abs(a) + 1.0


def _decimal_to_implied(dec: float) -> float:
    if dec <= 1.0:
        return 1.0
    return 1.0 / dec


class PlayerPropsMarket:
    """
    Model-implied player prop probabilities for a single match.

    Usage
    -----
    market = PlayerPropsMarket()
    props = market.build_props_from_prediction(
        match_prediction=pred,
        player_stats_df=player_stats_df,
        lineup_df=lineup_df,
        bdl_props=bdl_props_list,
    )
    # props: {prop_type: {player_name: {model_prob, market_odds, edge_pct}}}
    """

    DEFAULT_MINUTES = 80.0  # assumed minutes for a starter

    def build_props_from_prediction(
        self,
        match_prediction: dict,
        player_stats_df: pd.DataFrame | None = None,
        lineup_df: pd.DataFrame | None = None,
        bdl_props: list[dict] | None = None,
    ) -> dict[str, dict[str, dict]]:
        """
        Build model-implied props and compare to market.

        Parameters
        ----------
        match_prediction : dict
            Single match prediction dict (from wc-predictions.json).
        player_stats_df : pd.DataFrame, optional
            Player match stats from player_match_stats parquet.
        lineup_df : pd.DataFrame, optional
            Match lineups; used to determine starters and minutes.
        bdl_props : list[dict], optional
            Raw BDL player_props API response for this match.

        Returns
        -------
        dict: {prop_type: {player_name: {"model_prob", "market_odds", "edge_pct", ...}}}
        """
        home_team = match_prediction.get("home_team", "")
        away_team = match_prediction.get("away_team", "")
        pred = match_prediction.get("prediction", {})

        expected_home_xg = float(pred.get("expected_home_goals") or 1.3)
        expected_away_xg = float(pred.get("expected_away_goals") or 1.0)

        # ── Build player rate table ────────────────────────────────────────
        player_rates: dict[str, dict] = {}  # player_name → {xg_90, sot_90, shot_90, team, pos}

        if player_stats_df is not None and not player_stats_df.empty:
            for _, row in player_stats_df.iterrows():
                pname = str(row.get("player_name") or row.get("player_id") or "")
                team = str(row.get("team_name", ""))
                pos = str(row.get("position") or row.get("player_position") or "")
                mins = row.get("minutes_played")
                xg = row.get("expected_goals")
                sot = row.get("shots_on_goal") or row.get("shots_on_target")
                shots = row.get("shots") or row.get("total_shots")

                if not pname or mins is None:
                    continue
                try:
                    mins_f = float(mins)
                except (TypeError, ValueError):
                    continue
                if mins_f < 1:
                    continue

                rates: dict = {
                    "team": team,
                    "position": pos,
                    "total_minutes": mins_f,
                }
                if xg is not None:
                    try:
                        rates["xg_90"] = float(xg) / mins_f * 90.0
                    except (TypeError, ValueError, ZeroDivisionError):
                        pass
                if sot is not None:
                    try:
                        rates["sot_90"] = float(sot) / mins_f * 90.0
                    except (TypeError, ValueError, ZeroDivisionError):
                        pass
                if shots is not None:
                    try:
                        rates["shot_90"] = float(shots) / mins_f * 90.0
                    except (TypeError, ValueError, ZeroDivisionError):
                        pass

                # Merge / update
                if pname not in player_rates:
                    player_rates[pname] = rates
                else:
                    existing = player_rates[pname]
                    existing["total_minutes"] = existing.get("total_minutes", 0) + mins_f
                    for k in ["xg_90", "sot_90", "shot_90"]:
                        if k in rates:
                            if k in existing:
                                # Running average
                                w_old = existing["total_minutes"] - mins_f
                                w_new = mins_f
                                existing[k] = (existing[k] * w_old + rates[k] * w_new) / existing["total_minutes"]
                            else:
                                existing[k] = rates[k]

        # ── Build market odds lookup ───────────────────────────────────────
        # {(player_name_lower, prop_type): {model implied prob, american odds}}
        mkt_lookup: dict[tuple, dict] = {}
        if bdl_props:
            for p in bdl_props:
                pname = (
                    (p.get("player") or {}).get("name")
                    or (p.get("player") or {}).get("display_name")
                    or str(p.get("player_name", ""))
                ).strip()
                ptype = str(p.get("prop_type") or p.get("market_type") or "").lower()
                american = p.get("american_odds") or p.get("odds")
                if not pname or not ptype or american is None:
                    continue
                try:
                    mkt_implied = _decimal_to_implied(_american_to_decimal(float(american)))
                except (TypeError, ValueError):
                    continue
                key = (pname.lower(), ptype)
                if key not in mkt_lookup or mkt_lookup[key]["mkt_prob"] < mkt_implied:
                    mkt_lookup[key] = {
                        "american_odds": int(american),
                        "mkt_prob": mkt_implied,
                    }

        # ── Compute model props for each known player ─────────────────────
        output: dict[str, dict[str, dict]] = {
            "anytime_goal": {},
            "shots_on_target": {},
            "shots": {},
        }

        # Teams playing in this match
        _teams = {home_team.lower(), away_team.lower()}
        for pname, rates in player_rates.items():
            team = rates.get("team", "")
            if team.lower() not in _teams and home_team and away_team:
                continue
            pos = rates.get("position", "")
            pk = _pos_key(pos)
            is_home = team.lower() == home_team.lower()

            # Expected match xG for this player's team
            team_match_xg = expected_home_xg if is_home else expected_away_xg

            # Estimate player's share of team goals = (player_xg_90 / team_avg_xg_90) capped
            # We use positional defaults as fallback
            xg_rate_90 = rates.get("xg_90") or _POS_XG_RATE.get(pk, 0.10)
            sot_rate_90 = rates.get("sot_90") or _POS_SOT_RATE.get(pk, 0.40)
            shot_rate_90 = rates.get("shot_90") or _POS_SHOT_RATE.get(pk, 0.90)

            # Minutes expected: from lineup if available, else default
            minutes = self.DEFAULT_MINUTES

            # ── anytime_goal ─────────────────────────────────────────────
            # Scale player xG by actual match xG intensity vs WC average
            WC_AVG_TEAM_XG = 1.45
            xg_scale = team_match_xg / WC_AVG_TEAM_XG if WC_AVG_TEAM_XG > 0 else 1.0
            scaled_xg_rate = xg_rate_90 * xg_scale
            model_prob_goal = _poisson_at_least_one(scaled_xg_rate, minutes)

            # ── shots_on_target ───────────────────────────────────────────
            model_prob_sot = _poisson_at_least_one(sot_rate_90, minutes)

            # ── shots ─────────────────────────────────────────────────────
            model_prob_shots = _poisson_at_least_one(shot_rate_90, minutes)

            # ── Compare to market ──────────────────────────────────────────
            for prop_type, model_prob in [
                ("anytime_goal", model_prob_goal),
                ("shots_on_target", model_prob_sot),
                ("shots", model_prob_shots),
            ]:
                entry: dict = {
                    "model_prob": round(model_prob, 4),
                    "team": team,
                    "position": pos,
                }
                mkt = mkt_lookup.get((pname.lower(), prop_type))
                if mkt:
                    mkt_prob = mkt["mkt_prob"]
                    edge_pct = round((model_prob - mkt_prob) / max(mkt_prob, _EPS) * 100.0, 2)
                    entry["market_odds"] = mkt["american_odds"]
                    entry["market_prob"] = round(mkt_prob, 4)
                    entry["edge_pct"] = edge_pct
                    entry["value"] = edge_pct > 4.0

                output[prop_type][pname] = entry

        return output

    def top_value_props(
        self,
        props: dict[str, dict[str, dict]],
        top_k: int = 3,
    ) -> list[dict]:
        """
        Return the top_k value props across all prop types, sorted by edge.

        Parameters
        ----------
        props  Output from build_props_from_prediction.
        top_k  Number of top props to return.

        Returns
        -------
        list of dicts with keys: player_name, prop_type, model_prob, market_odds,
                                  edge_pct, value.
        """
        candidates = []
        for prop_type, players in props.items():
            for pname, entry in players.items():
                if entry.get("edge_pct") is not None:
                    candidates.append({
                        "player_name": pname,
                        "prop_type": prop_type,
                        "model_prob": entry.get("model_prob"),
                        "market_odds": entry.get("market_odds"),
                        "market_prob": entry.get("market_prob"),
                        "edge_pct": entry.get("edge_pct"),
                        "value": entry.get("value", False),
                        "team": entry.get("team"),
                    })
        # Sort by edge descending
        candidates.sort(key=lambda x: x.get("edge_pct", 0), reverse=True)
        return candidates[:top_k]
