"""
Live match PMF snapshot — polls BDL for live 2026 WC matches and runs
LivePMFPredictor on each. Writes wc-live.json to FTP every run.

Designed to run every 5 minutes during match hours via GitHub Actions
or any cron scheduler. On days with no live matches, writes an empty
wc-live.json with status "quiet" so the live page degrades gracefully.

Usage:
    python scripts/live_snapshot.py
    make live-snapshot
"""
from __future__ import annotations

import ftplib
import io
import json
import logging
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "src"))

try:
    from dotenv import load_dotenv
    load_dotenv(REPO_ROOT / ".env")
except ImportError:
    pass


logging.basicConfig(level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(name)s: %(message)s")
log = logging.getLogger("live_snapshot")

# BDL live status codes the API may return → how we treat them
# BDL WC API uses "scheduled"/"completed" (full words) in historical data.
# During live matches the exact code is unknown until a match is live;
# we handle both short codes (1h/2h/ht) and longer descriptions defensively.
LIVE_STATUS_CODES = {
    "1h", "2h", "ht", "et", "pso",
    "in_progress", "inprogress", "in progress", "live",
    "first half", "second half", "halftime", "half time",
    "1st half", "2nd half", "extra time", "extra_time",
    "penalty", "penalties", "pen", "ongoing", "active",
}

PREGAME_STATUS_CODES = {"ns", "not started", "scheduled", "tbd", "pre", "prematch"}

COMPLETED_STATUS_CODES = {
    "ft", "aet", "pen", "finished", "ended", "final",
    "full time", "pso_finished", "completed", "complete",
    "full_time", "after et", "after penalties",
}

FTP_DIR_SPACE = "/tools/odds-scanner/predictions/world cup"
FTP_DIR_HYPHEN = "/tools/odds-scanner/predictions/world-cup/live"
FTP_DIR_CANON = "/tools/odds-scanner/predictions/worldcup"   # canonical no-space path (same as wc-xray.json)
LIVE_FILE = "wc-live.json"


def _parse_bdl_dt(ko_str: str) -> "datetime":
    """Parse a BDL datetime string robustly.

    BDL returns millisecond timestamps like '2026-06-20T03:00:00.000Z' which
    Python 3.10's fromisoformat() rejects (it only handles 6-digit microseconds,
    not 3-digit milliseconds, and does not recognise the Z suffix).
    This helper strips the fractional-seconds component and normalises Z → +00:00.
    """
    import re as _re
    s = str(ko_str).strip()
    # Strip milliseconds (.000 or .000000) before timezone indicator
    s = _re.sub(r'\.\d+(?=[Z+\-]|$)', '', s)
    # Replace Z suffix with explicit UTC offset
    s = s.replace("Z", "+00:00")
    # If still no timezone info, assume UTC
    if "+" not in s[10:] and s[10:].count("-") == 0:
        s += "+00:00"
    return datetime.fromisoformat(s)

# Static jersey colors for World Cup teams (used by live-pitch.html via JSON output)
TEAM_COLORS: dict[str, str] = {
    "Argentina": "#75aadb", "France": "#002395", "Brazil": "#009c3b",
    "England": "#cf091e", "Germany": "#dddddd", "Spain": "#aa151b",
    "Portugal": "#006600", "Netherlands": "#ff6600", "USA": "#b22234",
    "Mexico": "#006847", "Morocco": "#c1272d", "Japan": "#bc002d",
    "Senegal": "#00853f", "Algeria": "#006233", "Norway": "#ef2b2d",
    "Austria": "#ed2939", "Iraq": "#007a3d", "Jordan": "#007a3d",
    "Croatia": "#ff0000", "Ghana": "#006b3f", "Panama": "#da121a",
    "DR Congo": "#007fff", "Ecuador": "#ffdd00", "Uruguay": "#5eb6e4",
    "Colombia": "#fcd116", "Chile": "#d52b1e", "Switzerland": "#ff0000",
    "Belgium": "#000000", "Denmark": "#c60c30", "Sweden": "#006aa7",
    "Canada": "#ff0000", "Costa Rica": "#002b7f", "Saudi Arabia": "#006c35",
    "South Korea": "#c60c30", "Australia": "#ffcd00", "Cameroon": "#007a5e",
    "Tunisia": "#e70013", "Nigeria": "#008751", "Ivory Coast": "#f77f00",
    "Serbia": "#c6363c", "Poland": "#dc143c", "Ukraine": "#005bbc",
    "Qatar": "#8d1b3d",
}

# Position → x-coordinate on home side of pitch (0–105)
_POS_X_HOME: dict[str, float] = {
    "GK": 3.0, "SW": 10.0, "CB": 15.0, "CD": 15.0, "RCB": 15.0, "LCB": 15.0,
    "RB": 20.0, "LB": 20.0, "WB": 22.0, "RWB": 22.0, "LWB": 22.0,
    "CDM": 32.0, "DM": 32.0, "CM": 40.0, "RM": 40.0, "LM": 40.0, "MF": 40.0,
    "CAM": 45.0, "AM": 45.0, "OM": 45.0,
    "RW": 50.0, "LW": 50.0, "W": 50.0, "SS": 48.0,
    "ST": 55.0, "CF": 55.0, "FW": 55.0, "F": 55.0,
}


def _map_pos_to_coords(position: str, is_home: bool, y_index: int, y_total: int) -> tuple[float, float]:
    """Map position abbreviation to (x, y) coordinates on the pitch (0–105, 0–68)."""
    pos = position.upper().strip()
    hx = _POS_X_HOME.get(pos, 35.0)
    x = hx if is_home else round(105.0 - hx, 1)
    y_margin = 7.0
    if y_total <= 1:
        y = 34.0
    else:
        y = y_margin + (y_index / (y_total - 1)) * (68.0 - 2 * y_margin)
    return round(x, 1), round(y, 1)


def _extract_team_stats(bdl_stats: list | None, home_name: str, away_name: str) -> dict:
    """Extract possession, shots, xG, corners, cards from BDL team_match_stats rows.

    BDL team_match_stats field names (from API spec):
      possession_pct, shots_total, shots_on_target, expected_goals,
      corners, yellow_cards, red_cards, is_home (boolean).
    """
    out: dict = {
        "home_possession": 50, "away_possession": 50,
        "home_shots": 0, "away_shots": 0,
        "home_shots_on_target": 0, "away_shots_on_target": 0,
        "home_xg": 0.0, "away_xg": 0.0,
        "home_corners": 0, "away_corners": 0,
        "home_yellow_cards": 0, "away_yellow_cards": 0,
        "home_red_cards": 0, "away_red_cards": 0,
    }
    if not bdl_stats:
        return out

    for row in bdl_stats:
        # BDL team_match_stats has a direct is_home boolean
        is_home_flag = row.get("is_home")
        if is_home_flag is not None:
            is_home = bool(is_home_flag)
        else:
            # Fallback: match by team name
            team_obj = row.get("team") or {}
            team_name = team_obj.get("name") or team_obj.get("full_name") or ""
            ha = str(row.get("home_away") or "").lower()
            is_home = (team_name == home_name) or (ha == "home")
        p = "home" if is_home else "away"

        def _int(*keys) -> int | None:
            for k in keys:
                v = row.get(k)
                if v is not None:
                    try:
                        return int(float(str(v)))
                    except Exception:
                        pass
            return None

        def _float(*keys) -> float | None:
            for k in keys:
                v = row.get(k)
                if v is not None:
                    try:
                        return float(str(v).replace("%", ""))
                    except Exception:
                        pass
            return None

        # BDL API canonical names first, legacy names as fallback
        poss = _float("possession_pct", "possession", "ball_possession")
        if poss is not None:
            out[f"{p}_possession"] = round(poss, 1)

        shots = _int("shots_total", "shots", "total_shots")
        if shots is not None:
            out[f"{p}_shots"] = shots

        sot = _int("shots_on_target", "shots_on_goal", "shots_on")
        if sot is not None:
            out[f"{p}_shots_on_target"] = sot

        xg = _float("expected_goals", "xg", "xG")
        if xg is not None:
            out[f"{p}_xg"] = round(xg, 3)

        corners = _int("corners", "corner_kicks")
        if corners is not None:
            out[f"{p}_corners"] = corners

        yellow = _int("yellow_cards", "yellowcards")
        if yellow is not None:
            out[f"{p}_yellow_cards"] = yellow

        red = _int("red_cards", "redcards")
        if red is not None:
            out[f"{p}_red_cards"] = red

    # Sync possession to sum to 100 when only one side was updated
    hp, ap = out["home_possession"], out["away_possession"]
    if hp != 50 and ap == 50:
        out["away_possession"] = round(100.0 - hp, 1)
    elif ap != 50 and hp == 50:
        out["home_possession"] = round(100.0 - ap, 1)

    return out


def _synthesize_shot_coords(xg: float, is_home: bool, shot_index: int) -> tuple[float, float]:
    """
    When BDL does not provide shot coordinates, synthesize realistic (x, y) from xG.
    xG correlates with distance to goal: higher xG = closer to goal.
    Home team attacks toward x=105; away team attacks toward x=0.
    A small deterministic offset per shot_index prevents duplicate IDs.
    """
    import math
    # Approximate: xG ~ 0.5 * exp(-0.15 * distance_to_goal_meters)
    # → distance = -ln(xG / 0.5) / 0.15, clamped to [4, 35]
    xg_clamped = max(0.005, min(xg, 0.85))
    dist = -math.log(xg_clamped / 0.5) / 0.15
    dist = max(4.0, min(dist, 35.0))

    # Horizontal spread angle — varies by index to separate markers
    angle_deg = (shot_index % 9 - 4) * 8.0  # -32° to +32° in 8° steps
    angle_rad = angle_deg * math.pi / 180.0

    # Distance from goal-line end
    dx = dist * math.cos(angle_rad)
    dy = dist * math.sin(angle_rad)

    if is_home:
        # Attacking toward x=105 (right goal)
        x = 105.0 - dx
        y = 34.0 + dy
    else:
        # Attacking toward x=0 (left goal)
        x = dx
        y = 34.0 - dy

    return round(max(0.5, min(x, 104.5)), 2), round(max(2.0, min(y, 66.0)), 2)


def _extract_shot_list(bdl_shots: list | None, home_name: str, away_name: str,
                        player_lookup: dict | None = None) -> list[dict]:
    """Build shots[] from BDL match_shots rows using the correct API field names.

    BDL match_shots fields (from API spec):
      id, match_id, player_id, team_id, is_home (bool),
      shot_type (goal|save|miss|block|post), situation, body_part, goal_type,
      xg, xgot,
      player_x (0-100), player_y (0-100),   ← NORMALIZED PITCH COORDS
      goal_mouth_x, goal_mouth_y,
      time_minute, added_time, time_seconds

    Coordinates are normalized 0-100; we convert to FIFA pitch metres (105×68).
    When coordinates are missing, synthesize from xG so the pitch is never blank.
    Each shot gets a unique shot_id to prevent frontend deduplication.
    """
    if not bdl_shots:
        return []

    shots = []
    for i, row in enumerate(bdl_shots):
        # is_home is a direct boolean in BDL match_shots
        is_home = bool(row.get("is_home", False))

        # Player name from lookup table (player_id → name) or inline player object
        player_id = row.get("player_id")
        player_name = ""
        jersey = ""
        if player_lookup and player_id and player_id in player_lookup:
            pl = player_lookup[player_id]
            player_name = pl.get("short_name") or pl.get("name") or ""
            jersey = str(pl.get("jersey_number") or "")
        else:
            player_obj = row.get("player") or {}
            player_name = player_obj.get("short_name") or player_obj.get("name") or ""
            jersey = str(player_obj.get("jersey_number") or "")

        # xG / xGoT
        xg_val = 0.0
        try:
            if row.get("xg") is not None:
                xg_val = float(row["xg"])
        except Exception:
            pass
        xgot_val = 0.0
        try:
            if row.get("xgot") is not None:
                xgot_val = float(row["xgot"])
        except Exception:
            pass

        # shot_type: goal | save | miss | block | post
        shot_type = str(row.get("shot_type") or "").lower()
        result_str = shot_type  # use shot_type as the result field
        on_target = shot_type in ("goal", "save")

        # Minute
        minute = int(row.get("time_minute") or 0)
        added = int(row.get("added_time") or 0)

        # Coordinates — BDL returns player_x / player_y normalized 0-100
        # Convert to FIFA pitch metres: x → 0-105, y → 0-68
        px = row.get("player_x")
        py = row.get("player_y")
        coords_missing = (px is None or py is None)

        if not coords_missing:
            try:
                px_f = float(px)
                py_f = float(py)
                # BDL uses attacking-perspective coordinates (verified empirically):
                #   player_x=0  → near the opponent's goal (where shots happen)
                #   player_x=100 → near the shooter's own end
                # In our SVG: home attacks RIGHT (toward x=105), away attacks LEFT (toward x=0).
                # y=0..100 maps linearly to pitch width 0..68 (no flip needed).
                if is_home:
                    # x=0 near right goal → pitch_x = 105 * (1 - player_x/100)
                    x = round((1.0 - px_f / 100.0) * 105.0, 2)
                else:
                    # Away attacks left: x=0 near left goal → pitch_x = 105 * player_x/100
                    x = round((px_f / 100.0) * 105.0, 2)
                y = round((py_f / 100.0) * 68.0, 2)
            except Exception:
                coords_missing = True

        if coords_missing:
            x, y = _synthesize_shot_coords(xg_val if xg_val > 0 else 0.05, is_home, i)

        shots.append({
            "shot_id": f"s{row.get('id', i)}_{('h' if is_home else 'a')}_{minute}{'+'+str(added) if added else ''}",
            "minute": minute,
            "added_time": added,
            "team": home_name if is_home else away_name,
            "is_home": is_home,
            "player_name": player_name,
            "player_jersey": jersey,
            "player_id": player_id,
            "x": max(0.5, min(x, 104.5)),
            "y": max(0.5, min(y, 67.5)),
            "xg": round(xg_val, 3),
            "xgot": round(xgot_val, 3),
            "on_target": on_target,
            "result": result_str,
            "shot_type": shot_type,
            "situation": str(row.get("situation") or ""),
            "body_part": str(row.get("body_part") or ""),
            "coords_synthesized": coords_missing,
        })

    return sorted(shots, key=lambda s: (s["minute"], s.get("added_time", 0)))


def _extract_goals_from_shots(bdl_shots: list | None, home_name: str, away_name: str) -> list[dict]:
    """Fallback: build events[] from shots that resulted in goals (used when match_events unavailable)."""
    if not bdl_shots:
        return []
    events = []
    for row in bdl_shots:
        result_str = str(row.get("result") or row.get("shot_result") or "").lower()
        if result_str != "goal":
            continue
        team_obj = row.get("team") or {}
        team_name = team_obj.get("name") or team_obj.get("full_name") or ""
        ha = str(row.get("home_away") or "").lower()
        is_home = (team_name == home_name) or (ha == "home")
        player = row.get("player") or {}
        player_name = player.get("display_name") or player.get("name") or ""
        jersey = str(player.get("jersey_number") or player.get("number") or "")
        minute = 0
        for k in ["minute", "clock_minute", "match_minute"]:
            if row.get(k) is not None:
                try:
                    minute = int(row[k]); break
                except Exception:
                    pass
        events.append({
            "minute": minute,
            "added_time": 0,
            "type": "goal",
            "incident_class": "regular",
            "team": home_name if is_home else away_name,
            "is_home": is_home,
            "player_name": player_name,
            "player_jersey": jersey,
            "description": f"{minute}' ⚽ {player_name or (home_name if is_home else away_name)}",
        })
    return sorted(events, key=lambda e: e["minute"])


def _extract_events_from_bdl(
    bdl_events: list | None,
    home_name: str,
    away_name: str,
    bdl_shots: list | None = None,
) -> list[dict]:
    """
    Build events[] from BDL match_events rows (goals, cards, substitutions).
    Falls back to _extract_goals_from_shots when bdl_events is empty/None.

    Included incident_types: goal, card, substitution.
    Skipped: period, injuryTime, penaltyShootout.
    Rescinded cards are skipped.
    """
    _SKIP_TYPES = {"period", "injurytime", "injury_time", "penaltyshootout", "penalty_shootout"}

    if not bdl_events:
        return _extract_goals_from_shots(bdl_shots, home_name, away_name)

    events: list[dict] = []
    for row in bdl_events:
        raw_type = str(row.get("incident_type") or "").strip()
        norm_type = raw_type.lower().replace(" ", "").replace("_", "")
        if norm_type in _SKIP_TYPES:
            continue
        if row.get("rescinded"):
            continue

        is_home = bool(row.get("is_home"))
        team_name = home_name if is_home else away_name

        player = row.get("player") or {}
        player_name = player.get("display_name") or player.get("name") or ""
        player_jersey = str(player.get("jersey_number") or player.get("number") or "")

        minute = int(row.get("time_minute") or row.get("minute") or 0)
        added = int(row.get("added_time") or 0)
        min_str = f"{minute}" + (f"+{added}" if added else "")

        incident_class = str(row.get("incident_class") or "").lower()

        if norm_type in ("goal", "penalty", "owngoal"):
            if incident_class == "penalty":
                desc = f"{min_str}' ⚽ {player_name} (pen)"
            elif incident_class == "owngoal":
                desc = f"{min_str}' ⚽ {player_name} (og)"
            else:
                desc = f"{min_str}' ⚽ {player_name}"

            assist = row.get("assist_player") or {}
            assist_name = assist.get("display_name") or assist.get("name") or ""

            events.append({
                "minute": minute,
                "added_time": added,
                "type": "goal",
                "incident_class": incident_class or "regular",
                "team": team_name,
                "is_home": is_home,
                "player_name": player_name,
                "player_jersey": player_jersey,
                "assist_player": assist_name,
                "home_score": row.get("home_score"),
                "away_score": row.get("away_score"),
                "description": desc,
            })

        elif norm_type == "card":
            if incident_class in ("yellowred", "yellow_red"):
                card_type = "red_card"
                emoji = "🟥"
            elif incident_class == "red":
                card_type = "red_card"
                emoji = "🟥"
            elif incident_class == "yellow":
                card_type = "yellow_card"
                emoji = "🟨"
            else:
                continue  # Unknown card class — skip

            events.append({
                "minute": minute,
                "added_time": added,
                "type": card_type,
                "incident_class": incident_class,
                "team": team_name,
                "is_home": is_home,
                "player_name": player_name,
                "player_jersey": player_jersey,
                "description": f"{min_str}' {emoji} {player_name}",
            })

        elif norm_type == "substitution":
            player_out = row.get("player_out") or {}
            player_in = row.get("player_in") or {}
            out_name = player_out.get("display_name") or player_out.get("name") or player_name
            in_name = player_in.get("display_name") or player_in.get("name") or ""

            events.append({
                "minute": minute,
                "added_time": added,
                "type": "substitution",
                "team": team_name,
                "is_home": is_home,
                "player_out_name": out_name,
                "player_in_name": in_name,
                "description": f"{min_str}' 🔄 {out_name} → {in_name}",
            })

    return sorted(events, key=lambda e: (e["minute"], e.get("added_time", 0)))


def _extract_player_stats(bdl_player_stats: list | None) -> list[dict]:
    """Build player_stats[] from BDL player_match_stats rows."""
    if not bdl_player_stats:
        return []

    stats: list[dict] = []
    for row in bdl_player_stats:
        player = row.get("player") or {}
        player_name = player.get("display_name") or player.get("name") or ""
        player_id = str(player.get("id") or row.get("player_id") or "")
        is_home = bool(row.get("is_home"))

        def _int(key: str, aliases: list[str] | None = None) -> int:
            for k in [key] + (aliases or []):
                v = row.get(k)
                if v is not None:
                    try:
                        return int(float(str(v)))
                    except Exception:
                        pass
            return 0

        def _float(key: str, aliases: list[str] | None = None) -> float:
            for k in [key] + (aliases or []):
                v = row.get(k)
                if v is not None:
                    try:
                        return round(float(str(v)), 3)
                    except Exception:
                        pass
            return 0.0

        stats.append({
            "player_id": player_id,
            "is_home": is_home,
            "player_name": player_name,
            "minutes_played": _int("minutes_played", ["minutes"]),
            "goals": _int("goals", ["goals_scored"]),
            "assists": _int("assists"),
            "shots_on_target": _int("shots_on_goal", ["shots_on_target"]),
            "expected_goals": _float("expected_goals", ["xg", "xG"]),
            "rating": _float("rating", ["match_rating"]),
            "touches": _int("touches", ["ball_touches"]),
            "tackles": _int("tackles", ["tackles_won"]),
        })

    return stats


def _load_lineup_for_match(
    mid: str, home: str, away: str, date: str
) -> tuple[list[dict], list[dict]]:
    """
    Load starting lineup from published data and map positions to pitch coordinates.
    Scans today ±2 days to handle pipeline timing variance.
    """
    from datetime import date as _date, timedelta
    base = _date.fromisoformat(date)

    for delta in range(-1, 3):
        d = (base + timedelta(days=delta)).isoformat()
        pub_path = REPO_ROOT / "data" / "published" / f"{d}.json"
        if not pub_path.exists():
            continue
        try:
            doc = json.loads(pub_path.read_text())
        except Exception:
            continue

        for m in doc.get("matches", []):
            m_id = str(m.get("match_id", ""))
            m_home = m.get("home_team", "")
            m_away = m.get("away_team", "")
            if m_id != mid and f"{m_home}|{m_away}" != f"{home}|{away}":
                continue

            raw_lineups = m.get("lineups") or m.get("lineup") or {}
            home_raw = raw_lineups.get("home") or raw_lineups.get(m_home) or []
            away_raw = raw_lineups.get("away") or raw_lineups.get(m_away) or []

            def build_lineup(players: list, is_home: bool) -> list[dict]:
                pos_groups: dict[str, list] = {}
                for p in players:
                    pos = str(p.get("position") or p.get("pos") or "CM").upper()
                    pos_groups.setdefault(pos, []).append(p)
                result: list[dict] = []
                for pos, group in pos_groups.items():
                    for i, p in enumerate(group):
                        x, y = _map_pos_to_coords(pos, is_home, i, len(group))
                        result.append({
                            "name": p.get("display_name") or p.get("name") or "",
                            "jersey_number": str(p.get("jersey_number") or p.get("number") or ""),
                            "position": pos,
                            "x": x,
                            "y": y,
                        })
                return result

            return build_lineup(home_raw, True), build_lineup(away_raw, False)

    return [], []


def _load_pregame_data(date: str) -> tuple[dict, dict]:
    """
    Load pregame expected goals and win probabilities from published JSON files.
    Scans today ±3 days so data is always available regardless of pipeline timing.

    Returns
    -------
    lambdas : dict keyed by match_id or "home|away" → (lh, la)
    probs   : dict keyed by match_id or "home|away" → {home_win_prob, draw_prob, away_win_prob}
    """
    from datetime import date as _date, timedelta
    lambdas: dict = {}
    probs: dict = {}
    base = _date.fromisoformat(date)
    # Scan ±3 days (oldest→newest so today wins for same match)
    for delta in range(-3, 4):
        d = (base + timedelta(days=delta)).isoformat()
        pub_path = REPO_ROOT / "data" / "published" / f"{d}.json"
        if not pub_path.exists():
            continue
        try:
            doc = json.loads(pub_path.read_text())
        except Exception as _parse_exc:
            log.warning("Skipping malformed published file %s: %s", pub_path.name, _parse_exc)
            continue
        for m in doc.get("matches", []):
            pred = m.get("prediction", {})
            lh = pred.get("expected_home_goals", 1.35)
            la = pred.get("expected_away_goals", 1.00)
            mid = str(m.get("match_id", ""))
            home = m.get("home_team", "")
            away = m.get("away_team", "")
            er = pred.get("edge_report", {})
            pregame_lh = er.get("pregame_lh", lh)
            pregame_la = er.get("pregame_la", la)
            dm = pred.get("derived_markets", {})
            hw = pred.get("home_win_prob") or dm.get("home_win") or 0.0
            dr = pred.get("draw_prob") or dm.get("draw") or 0.0
            aw = pred.get("away_win_prob") or dm.get("away_win") or 0.0
            entry_l = (pregame_lh, pregame_la)
            entry_p = {"home_win_prob": float(hw), "draw_prob": float(dr), "away_win_prob": float(aw)}
            for key in ([mid] if mid else []) + ([f"{home}|{away}"] if home and away else []):
                lambdas[key] = entry_l
                probs[key] = entry_p
        log.debug("Pregame data loaded: date=%s n=%d", d, len(doc.get("matches", [])))
    log.info("Pregame cache: %d entries (lambdas+probs) across ±3d", len(lambdas))
    return lambdas, probs


def _load_pregame_lambdas(date: str) -> dict[str, tuple[float, float]]:
    """Legacy wrapper — returns only the lambdas dict (callers that don't need probs)."""
    lambdas, _ = _load_pregame_data(date)
    return lambdas


def _fetch_live_matches() -> tuple[list[dict], list[dict], list[dict]]:
    """Fetch all 2026 WC matches from BDL and return live ones."""
    from wc2026.data.providers.bdl import BDLProvider
    provider = BDLProvider(snapshot=False)
    log.info("Fetching 2026 WC matches from BDL…")
    try:
        all_matches = provider.fetch_matches(seasons=[2026])
    except Exception as exc:
        log.error("BDL fetch failed: %s", exc)
        return [], []

    log.info("BDL fetch complete: %d total matches, sample_status=%s",
             len(all_matches), all_matches[0].get("status") if all_matches else None)

    now_utc = datetime.now(tz=timezone.utc)
    live, upcoming, finished = [], [], []
    for m in all_matches:
        raw_status = str(m.get("status", "") or "").lower().strip()
        clock_seconds = int(m.get("clock_seconds", 0) or 0)

        if raw_status in LIVE_STATUS_CODES:
            live.append(m)
        elif raw_status in COMPLETED_STATUS_CODES:
            finished.append(m)
        elif raw_status in PREGAME_STATUS_CODES:
            # Check if kickoff time has passed — BDL often lags 5-15 min before
            # changing status from "scheduled" to "in_progress".
            ko_str = m.get("datetime") or m.get("date_time_utc", "")
            try:
                ko_dt = _parse_bdl_dt(ko_str)
                mins_since_ko = (now_utc - ko_dt).total_seconds() / 60.0
            except Exception:
                mins_since_ko = -999.0
            if 3.0 <= mins_since_ko <= 105.0:
                # Kickoff passed 3–105 min ago and BDL still says scheduled → treat as live.
                # Upper bound of 105 min = 90 min regulation + ~15 min max injury time.
                # Beyond that the game is almost certainly over; BDL just hasn't updated.
                home_name = (m.get("home_team") or {}).get("name") or "?"
                away_name = (m.get("away_team") or {}).get("name") or "?"
                log.warning(
                    "BDL lag detected: '%s' still 'scheduled' %.1f min after kickoff — "
                    "treating as live (0-0 min=0): %s vs %s",
                    m.get("id"), mins_since_ko, home_name, away_name,
                )
                live.append(m)
            elif mins_since_ko > 105.0:
                # BDL still says 'scheduled' >105 min after kickoff — game is finished.
                home_name = (m.get("home_team") or {}).get("name") or "?"
                away_name = (m.get("away_team") or {}).get("name") or "?"
                log.warning(
                    "BDL lag: '%s' 'scheduled' %.1f min post-KO — treating as finished: %s vs %s",
                    m.get("id"), mins_since_ko, home_name, away_name,
                )
                finished.append(m)
            else:
                upcoming.append(m)
        elif clock_seconds > 60:
            # Clock is running but status string is unrecognized → treat as live
            home_name = (m.get("home_team") or {}).get("name") or (m.get("home_team") or {}).get("full_name", "?")
            away_name = (m.get("away_team") or {}).get("name") or (m.get("away_team") or {}).get("full_name", "?")
            log.warning("Unknown status '%s' clock=%ds — treating as live: %s vs %s",
                        raw_status, clock_seconds, home_name, away_name)
            live.append(m)
        else:
            log.debug("Unclassified match status '%s' (clock=%ds) — treating as upcoming",
                      raw_status, clock_seconds)
            upcoming.append(m)

    unique_statuses = list({str(m.get("status", "")).lower() for m in all_matches})
    log.info("Status distribution: live=%d upcoming=%d finished=%d unique=%s",
             len(live), len(upcoming), len(finished), unique_statuses)

    # Collect recently-finished matches (completed within last 3 hours) so the live
    # page can show "FT <score>" instead of disappearing to a quiet screen immediately.
    recently_finished = []
    for m in finished:
        ko_str = m.get("datetime") or m.get("date_time_utc", "")
        try:
            ko_dt = _parse_bdl_dt(ko_str)
            # A standard 90-min match + stoppage ends ~105 min after kickoff.
            # We show FT cards for up to 4 hours post-kickoff (generous buffer).
            mins_since_ko = (now_utc - ko_dt).total_seconds() / 60.0
            if 0 <= mins_since_ko <= 240:
                recently_finished.append(m)
        except Exception:
            pass

    log.info("BDL: %d total, %d live, %d upcoming, %d finished (%d recent)",
             len(all_matches), len(live), len(upcoming), len(finished), len(recently_finished))
    return live, upcoming, recently_finished


def _compute_live_edge(
    result,
    live_hw_odds: float | None,
    live_dr_odds: float | None,
    live_aw_odds: float | None,
    pregame_fallback: bool,
    home_team: str,
    away_team: str,
) -> dict:
    """
    3B–3E: Compute live betting edge using Shin devigging + Kelly criterion.

    Returns a dict with Shin-devigged probs, per-outcome edge, and value-bet flags.
    Handles missing/invalid odds gracefully.
    """
    import penaltyblog as pb
    from penaltyblog.implied.models import ImpliedMethod

    # Skip if odds not available
    if not (live_hw_odds and live_dr_odds and live_aw_odds):
        return {"market_margin": None, "shin_z": None, "pregame_fallback": pregame_fallback,
                "home": None, "draw": None, "away": None, "any_value_bet": False,
                "error": "no_odds"}

    try:
        # 3B — Devigging: try Shin first; fall back to MULTIPLICATIVE when Shin's
        # Brent-method solver fails on extreme or synthetic odds distributions.
        odds = [float(live_hw_odds), float(live_dr_odds), float(live_aw_odds)]
        # Guard against invalid odds (<= 1.0)
        if any(o <= 1.0 for o in odds):
            raise ValueError(f"Invalid odds: {odds}")
        try:
            implied = pb.implied.calculate_implied(odds, method=ImpliedMethod.SHIN)
            shin_z = implied.method_params.get("z") if implied.method_params else None
        except Exception as _shin_exc:
            log.debug("Shin devigging failed (%s); retrying with MULTIPLICATIVE", _shin_exc)
            implied = pb.implied.calculate_implied(odds, method=ImpliedMethod.MULTIPLICATIVE)
            shin_z = None
        market_margin = float(implied.margin)

        # 3C — Per-outcome edge using estimated probabilities from live model
        home_vb = pb.betting.identify_value_bet(
            bookmaker_odds=float(live_hw_odds),
            estimated_probability=float(result.home_win_prob),
            kelly_fraction=0.5,
            min_edge_threshold=0.03,
        )
        draw_vb = pb.betting.identify_value_bet(
            bookmaker_odds=float(live_dr_odds),
            estimated_probability=float(result.draw_prob),
            kelly_fraction=0.5,
            min_edge_threshold=0.03,
        )
        away_vb = pb.betting.identify_value_bet(
            bookmaker_odds=float(live_aw_odds),
            estimated_probability=float(result.away_win_prob),
            kelly_fraction=0.5,
            min_edge_threshold=0.03,
        )

        # 3D — Build live_edge dict
        live_edge = {
            "market_margin": round(market_margin, 4),
            "shin_z": round(float(shin_z), 5) if shin_z is not None else None,
            "pregame_fallback": pregame_fallback,
            "home": {
                "edge": round(float(home_vb.edge), 5),
                "is_value": bool(home_vb.is_value_bet),
                "ev": round(float(home_vb.expected_value), 5),
                "kelly_stake": round(float(home_vb.recommended_stake_fraction), 5),
            },
            "draw": {
                "edge": round(float(draw_vb.edge), 5),
                "is_value": bool(draw_vb.is_value_bet),
                "ev": round(float(draw_vb.expected_value), 5),
                "kelly_stake": round(float(draw_vb.recommended_stake_fraction), 5),
            },
            "away": {
                "edge": round(float(away_vb.edge), 5),
                "is_value": bool(away_vb.is_value_bet),
                "ev": round(float(away_vb.expected_value), 5),
                "kelly_stake": round(float(away_vb.recommended_stake_fraction), 5),
            },
            "any_value_bet": bool(home_vb.is_value_bet or draw_vb.is_value_bet or away_vb.is_value_bet),
        }

        # 3E — Log when live edge fires
        if live_edge["any_value_bet"]:
            minute = int(getattr(result, "regulation_minute", 0) or 0)
            log.info(
                "LIVE EDGE DETECTED: %s vs %s min=%d | margin=%.3f shin_z=%.4f",
                home_team, away_team, minute,
                market_margin, float(shin_z) if shin_z is not None else 0.0,
            )

        return live_edge

    except Exception as exc:
        log.debug("live_edge computation failed for %s vs %s: %s", home_team, away_team, exc)
        return {"market_margin": None, "shin_z": None, "pregame_fallback": pregame_fallback,
                "home": None, "draw": None, "away": None, "any_value_bet": False,
                "error": str(exc)}


def _build_live_market_implied(odds_rows: list[dict]) -> dict[str, float]:
    """Convert BDL odds rows for one match into market_implied_markets with no-vig probabilities.

    Uses SHIN devigging for 1X2, simple proportional no-vig for totals and BTTS.
    Returns {} when no usable odds rows are provided.
    """
    if not odds_rows:
        return {}

    from wc2026.markets.no_vig import strip_vig_1x2, strip_vig_total
    import statistics as _stats
    from collections import defaultdict

    result: dict[str, float] = {}

    # 1X2 moneyline
    ml_probs: list[list[float]] = []
    for row in odds_rows:
        h = row.get("moneyline_home_odds")
        d = row.get("moneyline_draw_odds")
        a = row.get("moneyline_away_odds")
        if all(v is not None for v in (h, d, a)):
            try:
                nv = strip_vig_1x2(int(h), int(d), int(a), method="shin")
                if nv.method != "naive_fallback":
                    ml_probs.append(nv.probabilities)
            except Exception:
                pass
    if ml_probs:
        result["home_win"] = round(_stats.mean(p[0] for p in ml_probs), 6)
        result["draw"]     = round(_stats.mean(p[1] for p in ml_probs), 6)
        result["away_win"] = round(_stats.mean(p[2] for p in ml_probs), 6)
        log.info("  Live 1X2: H=%.3f D=%.3f A=%.3f (%d vendors)",
                 result["home_win"], result["draw"], result["away_win"], len(ml_probs))

    # Totals (over/under X.5 goals)
    def _dec_to_amer(dec: float) -> int:
        if dec >= 2.0:
            return int((dec - 1) * 100)
        return int(-100 / (dec - 1))

    totals_by_line: dict[float, list[tuple[int, int]]] = defaultdict(list)
    for row in odds_rows:
        for mkt in row.get("markets", []):
            if mkt.get("type") != "total":
                continue
            if mkt.get("period") != "match" or mkt.get("scope") != "match":
                continue
            line = mkt.get("line_value")
            if line is None:
                continue
            try:
                line = float(line)
            except (TypeError, ValueError):
                continue
            if line not in {0.5, 1.5, 2.5, 3.5, 4.5, 5.5, 6.5}:
                continue
            over_dec = under_dec = None
            for outcome in mkt.get("outcomes", []):
                if outcome.get("type") == "over":
                    over_dec = outcome.get("decimal_odds")
                elif outcome.get("type") == "under":
                    under_dec = outcome.get("decimal_odds")
            if over_dec and under_dec:
                totals_by_line[line].append(
                    (_dec_to_amer(float(over_dec)), _dec_to_amer(float(under_dec)))
                )
    for line, pairs in sorted(totals_by_line.items()):
        over_probs, under_probs = [], []
        for ov_a, un_a in pairs:
            try:
                op, up = strip_vig_total(ov_a, un_a, method="shin")
                over_probs.append(op)
                under_probs.append(up)
            except Exception:
                pass
        if over_probs:
            line_key = str(line).replace(".", "_")
            result[f"over_{line_key}"]  = round(_stats.mean(over_probs), 6)
            result[f"under_{line_key}"] = round(_stats.mean(under_probs), 6)

    # BTTS
    btts_yes_dec: list[float] = []
    btts_no_dec:  list[float] = []
    for row in odds_rows:
        for mkt in row.get("markets", []):
            if mkt.get("type") != "both_teams_to_score":
                continue
            if mkt.get("period") != "match" or mkt.get("scope") != "both_teams":
                continue
            name = (mkt.get("name") or "").lower()
            if any(x in name for x in ["corner", "first half", "2nd", "combo", "/"]):
                continue
            outcomes = mkt.get("outcomes", [])
            if len(outcomes) != 2:
                continue
            for outcome in outcomes:
                otype = (outcome.get("type") or "").lower()
                dec = outcome.get("decimal_odds")
                if dec and float(dec) > 1.0:
                    if otype in ("yes", "true", "btts", "both_teams"):
                        btts_yes_dec.append(float(dec))
                    elif otype in ("no", "false"):
                        btts_no_dec.append(float(dec))
    if btts_yes_dec and btts_no_dec:
        raw_y, raw_n = 1 / _stats.mean(btts_yes_dec), 1 / _stats.mean(btts_no_dec)
        total = raw_y + raw_n
        result["btts_yes"] = round(raw_y / total, 6)
        result["btts_no"]  = round(raw_n / total, 6)

    return result


def run_live_snapshot() -> dict:
    """Main: fetch live matches, run PMF engine, return snapshot dict."""
    from wc2026.live.predictor import LivePMFPredictor
    from wc2026.live.state import MatchStatus

    now_utc = datetime.now(tz=timezone.utc)
    today_et = now_utc.astimezone(
        __import__("zoneinfo", fromlist=["ZoneInfo"]).ZoneInfo("America/New_York")
    ).date().isoformat()

    predictor = LivePMFPredictor(max_delta=7, max_goals=10)
    pregame_lambdas, pregame_probs = _load_pregame_data(today_et)

    try:
        live_matches, upcoming, recently_finished = _fetch_live_matches()
    except Exception as exc:
        log.error("Failed to fetch matches: %s", exc)
        live_matches, upcoming, recently_finished = [], [], []

    # Fetch live team stats + shots + events + player stats for all live matches in one batch each
    live_ids = [m.get("id") for m in live_matches if m.get("id")]
    live_team_stats: dict[str, list] = {}    # match_id → [team_match_stats rows]
    live_shots: dict[str, list] = {}         # match_id → [match_shots rows]
    live_events: dict[str, list] = {}        # match_id → [match_events rows]
    live_player_stats: dict[str, list] = {}  # match_id → [player_match_stats rows]
    live_odds: dict[str, list] = {}          # match_id → [odds rows]
    if live_ids:
        try:
            from wc2026.data.providers.bdl import BDLProvider
            _stats_provider = BDLProvider(snapshot=False)
            stats_rows = _stats_provider.fetch_team_stats(match_ids=live_ids)
            for row in stats_rows:
                key = str(row.get("match_id", ""))
                live_team_stats.setdefault(key, []).append(row)
            shots_rows = _stats_provider.fetch_shots(match_ids=live_ids)
            for row in shots_rows:
                key = str(row.get("match_id", ""))
                live_shots.setdefault(key, []).append(row)
            try:
                events_rows = _stats_provider.fetch_events(match_ids=live_ids)
                for row in events_rows:
                    key = str(row.get("match_id", ""))
                    live_events.setdefault(key, []).append(row)
                log.info("Live events fetched: %d event rows for %d matches",
                         len(events_rows), len(live_ids))
            except Exception as exc:
                log.warning("Could not fetch live match events: %s", exc)
            try:
                pstats_rows = _stats_provider.fetch_player_stats(match_ids=live_ids)
                for row in pstats_rows:
                    key = str(row.get("match_id", ""))
                    live_player_stats.setdefault(key, []).append(row)
                log.info("Live player stats fetched: %d player-stat rows for %d matches",
                         len(pstats_rows), len(live_ids))
            except Exception as exc:
                log.warning("Could not fetch live player stats: %s", exc)
            # Fetch current live odds for X-Ray market comparison
            try:
                odds_rows = _stats_provider.fetch_odds(match_ids=live_ids)
                for row in odds_rows:
                    key = str(row.get("match_id", ""))
                    live_odds.setdefault(key, []).append(row)
                log.info("Live odds fetched: %d rows for %d matches", len(odds_rows), len(live_ids))
            except Exception as exc:
                log.warning("Could not fetch live odds: %s", exc)
            log.info("Live stats fetched: %d team-stat rows, %d shot rows for %d matches",
                     len(stats_rows), len(shots_rows), len(live_ids))
        except Exception as exc:
            log.warning("Could not fetch live team stats/shots: %s", exc)

    # Fetch momentum for live matches
    live_momentum: "dict[str, Any]" = {}
    if live_ids:
        try:
            from wc2026.data.providers.bdl import BDLProvider as _BDLProviderMom
            import pandas as _pd_mom
            _mom_provider = _BDLProviderMom(snapshot=False)
            momentum_rows = _mom_provider.fetch_momentum(match_ids=live_ids)
            if momentum_rows:
                _mom_df = _pd_mom.DataFrame(momentum_rows)
                for _m_mid, _m_grp in _mom_df.groupby("match_id"):
                    live_momentum[str(_m_mid)] = _m_grp.reset_index(drop=True)
                log.info("Momentum fetched: %d rows for %d live matches",
                         len(momentum_rows), len(live_ids))
        except Exception as _mom_exc:
            log.debug("Momentum fetch failed: %s", _mom_exc)

    # Fetch avg positions for live matches (used for defensive block depth)
    live_avg_positions: dict[str, list] = {}  # match_id → [avg_position rows]
    if live_ids:
        try:
            from wc2026.data.providers.bdl import BDLProvider as _BDLProvider2
            _pos_provider = _BDLProvider2(snapshot=False)
            avg_pos_rows = _pos_provider.fetch_avg_positions(match_ids=live_ids)
            for row in avg_pos_rows:
                key = str(row.get("match_id", ""))
                live_avg_positions.setdefault(key, []).append(row)
            log.info("Avg positions fetched: %d rows for %d live matches",
                     len(avg_pos_rows), len(live_ids))
        except Exception as exc:
            log.warning("Could not fetch avg positions: %s", exc)

    results = []
    for bdl_m in live_matches:
        mid = str(bdl_m.get("id", ""))
        home = (bdl_m.get("home_team") or {}).get("name") or (bdl_m.get("home_team") or {}).get("full_name", "Home")
        away = (bdl_m.get("away_team") or {}).get("name") or (bdl_m.get("away_team") or {}).get("full_name", "Away")

        # Look up pregame lambdas
        lh, la = pregame_lambdas.get(mid, pregame_lambdas.get(f"{home}|{away}", (1.35, 1.00)))
        bdl_stats = live_team_stats.get(mid) or None
        bdl_shots = live_shots.get(mid) or None
        bdl_match_events = live_events.get(mid) or None
        bdl_pstats = live_player_stats.get(mid) or None
        bdl_avg_pos = live_avg_positions.get(mid) or None

        # 3A — Populate live odds: try BDL match data first; fall back to pregame
        _live_hw_odds = bdl_m.get("home_odds") or bdl_m.get("odds_home") or None
        _live_dr_odds = bdl_m.get("draw_odds") or bdl_m.get("odds_draw") or None
        _live_aw_odds = bdl_m.get("away_odds") or bdl_m.get("odds_away") or None
        _pregame_fallback = False
        if not (_live_hw_odds and _live_dr_odds and _live_aw_odds):
            # Fall back to pregame probs converted to decimal odds
            _pg = pregame_probs.get(mid) or pregame_probs.get(f"{home}|{away}") or {}
            _pg_hw = float(_pg.get("home_win_prob") or 0)
            _pg_dr = float(_pg.get("draw_prob") or 0)
            _pg_aw = float(_pg.get("away_win_prob") or 0)
            if _pg_hw > 0.01 and _pg_dr > 0.01 and _pg_aw > 0.01:
                # Convert to decimal odds (include a small synthetic margin of ~4%)
                _margin = 1.04
                _live_hw_odds = round(_margin / _pg_hw, 3)
                _live_dr_odds = round(_margin / _pg_dr, 3)
                _live_aw_odds = round(_margin / _pg_aw, 3)
                _pregame_fallback = True

        # Score enrichment: BDL docs say home_score/away_score are null only pre-kickoff;
        # in practice they may also lag during live play.  When home_score IS populated,
        # it is used directly (primary path).  When null, inject the running score from
        # the last goal event (each event carries cumulative home_score/away_score).
        _score_source = "bdl_match"
        if bdl_m.get("home_score") is None and bdl_match_events:
            goal_events_with_score = [
                e for e in bdl_match_events
                if str(e.get("incident_type", "")).lower() in ("goal", "penalty", "owngoal")
                and e.get("home_score") is not None
                and not e.get("rescinded")
            ]
            if goal_events_with_score:
                goal_events_with_score.sort(
                    key=lambda e: (int(e.get("time_minute") or 0), int(e.get("added_time") or 0))
                )
                _last_goal = goal_events_with_score[-1]
                bdl_m = dict(bdl_m)  # shallow copy — do not mutate the original
                bdl_m["home_score"] = _last_goal["home_score"]
                bdl_m["away_score"] = _last_goal["away_score"]
                _score_source = f"events(last_goal_min={_last_goal.get('time_minute')})"
                log.info("Score injected from events: %s vs %s  %d-%d (event id=%s, min=%s)",
                         home, away, bdl_m["home_score"], bdl_m["away_score"],
                         _last_goal.get("id"), _last_goal.get("time_minute"))
            else:
                _score_source = "events(no_goals_yet)"

        log.info("Processing live match: %s vs %s  status=%s clock=%s score=%s-%s "
                 "score_src=%s lambda_src=%s stats=%s",
                 home, away, bdl_m.get("status"), bdl_m.get("clock_display"),
                 bdl_m.get("home_score"), bdl_m.get("away_score"),
                 _score_source,
                 "published" if mid in pregame_lambdas else "fallback",
                 "yes" if bdl_stats else "none")

        try:
            result = predictor.predict_from_bdl(bdl_m, pregame_lh=lh, pregame_la=la,
                                                bdl_stats=bdl_stats, bdl_shots=bdl_shots,
                                                avg_positions=bdl_avg_pos,
                                                momentum_df=live_momentum.get(mid))
            if result:
                d = result.to_dict()
                d["pregame_lh"] = lh
                d["pregame_la"] = la
                d["bdl_status"] = bdl_m.get("status")
                # Forward BDL extra-time / penalty-shootout flags so the live page
                # can annotate the scoreline when a WC knockout match goes to AET/PSO.
                d["has_extra_time"] = bool(bdl_m.get("has_extra_time"))
                d["has_penalty_shootout"] = bool(bdl_m.get("has_penalty_shootout"))
                if bdl_m.get("has_penalty_shootout"):
                    d["home_score_penalties"] = int(bdl_m.get("home_score_penalties") or 0)
                    d["away_score_penalties"] = int(bdl_m.get("away_score_penalties") or 0)

                # 3B–3E — Compute live betting edge with Shin devigging
                live_edge = _compute_live_edge(
                    result, _live_hw_odds, _live_dr_odds, _live_aw_odds,
                    _pregame_fallback, home, away,
                )
                d["live_edge"] = live_edge

                # Build market_implied_markets from live BDL odds for the X-Ray page
                live_mim = _build_live_market_implied(live_odds.get(mid, []))
                if live_mim:
                    d["market_implied_markets"] = live_mim
                    log.info("Live market_implied_markets built: %d markets for match %s",
                             len(live_mim), mid)
                else:
                    log.warning("No live odds available for match %s — X-Ray will use pregame fallback", mid)

                # Pitch visualization enrichment — shots, events, player stats, lineup
                try:
                    match_stats = _extract_team_stats(bdl_stats, home, away)
                    # Build player_id → player dict for name lookup in shots
                    _player_lookup: dict = {}
                    for _ps in (bdl_pstats or []):
                        _pid = _ps.get("player_id")
                        _pobj = _ps.get("player") or {}
                        if _pid and _pobj:
                            _player_lookup[_pid] = _pobj
                    shots_list = _extract_shot_list(bdl_shots, home, away, _player_lookup)
                    events_list = _extract_events_from_bdl(
                        bdl_match_events, home, away, bdl_shots
                    )
                    player_stats_list = _extract_player_stats(bdl_pstats)
                    lineup_home, lineup_away = _load_lineup_for_match(mid, home, away, today_et)

                    # Fallback: if team-stats endpoint returned 0 shots but shots_list has
                    # data, count shots and xG directly from the shots list.
                    if match_stats["home_shots"] == 0 and match_stats["away_shots"] == 0 and shots_list:
                        match_stats["home_shots"] = sum(1 for s in shots_list if s["is_home"])
                        match_stats["away_shots"] = sum(1 for s in shots_list if not s["is_home"])
                        match_stats["home_shots_on_target"] = sum(1 for s in shots_list if s["is_home"] and s["on_target"])
                        match_stats["away_shots_on_target"] = sum(1 for s in shots_list if not s["is_home"] and s["on_target"])
                        match_stats["home_xg"] = round(sum(s["xg"] for s in shots_list if s["is_home"]), 3)
                        match_stats["away_xg"] = round(sum(s["xg"] for s in shots_list if not s["is_home"]), 3)

                    # Augment shots_list with goal events so every goal appears on the pitch.
                    # Goals from the events feed may not be in bdl_shots (BDL often omits
                    # home-team shots in live data). Synthesize a shot marker for each goal
                    # event that is not already represented in shots_list.
                    existing_goal_minutes = {
                        s["minute"] for s in shots_list
                        if s.get("result") == "goal" or (s["xgot"] > 0.5)
                    }
                    goal_shot_count = len(shots_list)
                    for ev in events_list:
                        if ev.get("type") != "goal":
                            continue
                        ev_min = ev.get("minute", 0)
                        ev_home = ev.get("is_home", False)
                        # Add a pitch marker for this goal if not already covered
                        if ev_min not in existing_goal_minutes:
                            gx, gy = _synthesize_shot_coords(0.45, ev_home, goal_shot_count)
                            shots_list.append({
                                "shot_id": f"g{goal_shot_count}_{('h' if ev_home else 'a')}_{ev_min}",
                                "minute": ev_min,
                                "team": home if ev_home else away,
                                "is_home": ev_home,
                                "player_name": ev.get("player_name", ""),
                                "player_jersey": ev.get("player_jersey", ""),
                                "x": gx,
                                "y": gy,
                                "xg": 0.45,
                                "xgot": 0.9,
                                "on_target": True,
                                "result": "goal",
                                "coords_synthesized": True,
                            })
                            existing_goal_minutes.add(ev_min)
                            goal_shot_count += 1

                    d.update({
                        "home_possession":      match_stats["home_possession"],
                        "away_possession":      match_stats["away_possession"],
                        "home_shots":           match_stats["home_shots"],
                        "away_shots":           match_stats["away_shots"],
                        "home_shots_on_target": match_stats["home_shots_on_target"],
                        "away_shots_on_target": match_stats["away_shots_on_target"],
                        "home_xg":              match_stats["home_xg"],
                        "away_xg":              match_stats["away_xg"],
                        "home_corners":         match_stats["home_corners"],
                        "away_corners":         match_stats["away_corners"],
                        "home_yellow_cards":    match_stats["home_yellow_cards"],
                        "away_yellow_cards":    match_stats["away_yellow_cards"],
                        "home_red_cards":       match_stats["home_red_cards"],
                        "away_red_cards":       match_stats["away_red_cards"],
                        "shots":                sorted(shots_list, key=lambda s: s["minute"]),
                        "events":               events_list,
                        "player_stats":         player_stats_list,
                        "lineup_home":          lineup_home,
                        "lineup_away":          lineup_away,
                        "home_color":           TEAM_COLORS.get(home, "#1a56db"),
                        "away_color":           TEAM_COLORS.get(away, "#e63946"),
                    })
                    log.debug(
                        "Pitch data: %d shots, %d events (%s), %d player stats, %d+%d lineup",
                        len(shots_list), len(events_list),
                        "bdl" if bdl_match_events else "shots-fallback",
                        len(player_stats_list),
                        len(lineup_home), len(lineup_away),
                    )
                except Exception as enrich_exc:
                    log.warning("Pitch enrichment failed for %s vs %s: %s", home, away, enrich_exc)

                results.append(d)
                log.info("  Live PMF OK: %s vs %s  min=%.0f score=%d-%d hw=%.3f dr=%.3f aw=%.3f",
                         home, away, result.regulation_minute,
                         result.current_home_goals, result.current_away_goals,
                         result.home_win_prob, result.draw_prob, result.away_win_prob)
        except Exception as exc:
            log.warning("LivePMF failed for %s vs %s: %s", home, away, exc)

    # Build upcoming section (pre-game matches today)
    upcoming_today = []
    for m in upcoming[:10]:
        ko_str = m.get("datetime") or m.get("date_time_utc", "")
        try:
            from zoneinfo import ZoneInfo as _ZoneInfo
            ko_dt = _parse_bdl_dt(ko_str)
            ko_et = ko_dt.astimezone(_ZoneInfo("America/New_York"))
            # strftime %-I (Linux) vs %#I (Windows); fall back to %I with lstrip
            try:
                ko_et_str = ko_et.strftime("%-I:%M %p ET")
            except ValueError:
                ko_et_str = ko_et.strftime("%I:%M %p ET").lstrip("0")
        except Exception:
            ko_et_str = str(ko_str)
        home = (m.get("home_team") or {}).get("name") or (m.get("home_team") or {}).get("full_name", "")
        away = (m.get("away_team") or {}).get("name") or (m.get("away_team") or {}).get("full_name", "")
        mid_str = str(m.get("id", ""))
        p = (pregame_probs.get(mid_str)
             or pregame_probs.get(f"{home}|{away}")
             or {"home_win_prob": 0.0, "draw_prob": 0.0, "away_win_prob": 0.0})
        upcoming_today.append({
            "match_id": mid_str,
            "home_team": home,
            "away_team": away,
            "kickoff_et": ko_et_str,
            "kickoff_utc": ko_str,
            "status": m.get("status", ""),
            "home_win_prob": round(p["home_win_prob"], 5),
            "draw_prob": round(p["draw_prob"], 5),
            "away_win_prob": round(p["away_win_prob"], 5),
        })

    # Build recently-completed section — matches finished within the last 3 hours.
    # Displayed on the live page with an "FT" badge so users see the final score
    # instead of the page going blank after the final whistle.
    recently_completed_out = []
    for m in recently_finished:
        ft_home = (m.get("home_team") or {}).get("name") or (m.get("home_team") or {}).get("full_name", "")
        ft_away = (m.get("away_team") or {}).get("name") or (m.get("away_team") or {}).get("full_name", "")
        h_score = int(m.get("home_score") or 0)
        a_score = int(m.get("away_score") or 0)
        has_et = bool(m.get("has_extra_time"))
        has_pso = bool(m.get("has_penalty_shootout"))
        pen_h = int(m.get("home_score_penalties") or 0) if has_pso else None
        pen_a = int(m.get("away_score_penalties") or 0) if has_pso else None
        mid_str = str(m.get("id", ""))
        pg = (pregame_probs.get(mid_str)
              or pregame_probs.get(f"{ft_home}|{ft_away}")
              or {})
        recently_completed_out.append({
            "match_id": mid_str,
            "home_team": ft_home,
            "away_team": ft_away,
            "current_home_goals": h_score,
            "current_away_goals": a_score,
            "current_score": f"{h_score}-{a_score}",
            "is_ft": True,
            "bdl_status": "completed",
            "has_extra_time": has_et,
            "has_penalty_shootout": has_pso,
            "home_score_penalties": pen_h,
            "away_score_penalties": pen_a,
            "home_color": TEAM_COLORS.get(ft_home, "#1a56db"),
            "away_color": TEAM_COLORS.get(ft_away, "#e63946"),
            "home_win_prob": round(float(pg.get("home_win_prob") or 0), 5),
            "draw_prob": round(float(pg.get("draw_prob") or 0), 5),
            "away_win_prob": round(float(pg.get("away_win_prob") or 0), 5),
        })
        pso_note = f" (pens {pen_h}-{pen_a})" if has_pso else (" (AET)" if has_et else "")
        log.info("FT match added to snapshot: %s %d-%d %s%s", ft_home, h_score, a_score, ft_away, pso_note)

    snapshot = {
        "generated_at": now_utc.isoformat(),
        "date": today_et,
        "status": "live" if results else ("quiet" if not live_matches else "error"),
        "n_live": len(results),
        "live_matches": results,
        "recently_completed": recently_completed_out,
        "upcoming_today": upcoming_today,
    }
    return snapshot


def _ensure_remote_dir_and_chmod(ftp: ftplib.FTP, path: str) -> None:
    parts = [p for p in path.split("/") if p]
    current = ""
    for part in parts:
        current += f"/{part}"
        try:
            ftp.cwd(current)
        except ftplib.error_perm:
            try:
                ftp.mkd(current)
            except ftplib.error_perm as e:
                if "exists" not in str(e).lower():
                    raise
    try:
        ftp.sendcmd(f"SITE CHMOD 2775 {path}")
    except Exception:
        pass


def upload_snapshot(snapshot: dict) -> None:
    host = os.environ.get("FTP_HOST", "").strip()
    user = os.environ.get("FTP_USER", "").strip()
    password = os.environ.get("FTP_PASS", "").strip()

    if not host or not user or not password:
        log.warning("FTP credentials not set — skipping upload")
        return

    payload = json.dumps(snapshot, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    log.info("Uploading wc-live.json (%d bytes, %d live matches)…",
             len(payload), snapshot.get("n_live", 0))

    with ftplib.FTP(host, timeout=30) as ftp:
        ftp.login(user, password)
        for remote_dir in [FTP_DIR_SPACE, FTP_DIR_HYPHEN, FTP_DIR_CANON]:
            _ensure_remote_dir_and_chmod(ftp, remote_dir)
            ftp.cwd(remote_dir)
            ftp.storbinary(f"STOR {LIVE_FILE}", io.BytesIO(payload))
            try:
                ftp.sendcmd(f"SITE CHMOD 775 {remote_dir}/{LIVE_FILE}")
            except Exception:
                pass
        log.info("✓ Uploaded wc-live.json to all three paths")

    log.info("FTP upload complete: %d bytes, %d live matches, status=%s",
             len(payload), snapshot.get("n_live", 0), snapshot.get("status"))


def write_health_status(ok: bool, message: str, extra: dict | None = None) -> None:
    """Write wc-health.json to FTP — pages poll this to show pipeline status."""
    host = os.environ.get("FTP_HOST", "").strip()
    user = os.environ.get("FTP_USER", "").strip()
    password = os.environ.get("FTP_PASS", "").strip()
    if not host:
        return

    health = {
        "ok": ok,
        "message": message,
        "updated_at": datetime.now(tz=timezone.utc).isoformat(),
        **(extra or {}),
    }
    payload = json.dumps(health, separators=(",", ":")).encode("utf-8")
    try:
        with ftplib.FTP(host, timeout=15) as ftp:
            ftp.login(user, password)
            for remote_dir in [FTP_DIR_SPACE, FTP_DIR_HYPHEN, FTP_DIR_CANON,
                                "/tools/odds-scanner/predictions/world-cup/pre-match"]:
                try:
                    ftp.cwd(remote_dir)
                    ftp.storbinary("STOR wc-health.json", io.BytesIO(payload))
                    try:
                        ftp.sendcmd(f"SITE CHMOD 775 {remote_dir}/wc-health.json")
                    except Exception:
                        pass
                except Exception:
                    pass
    except Exception as exc:
        log.warning("Health write failed: %s", exc)


def push_to_live_server(snapshot: dict) -> bool:
    """
    Push a computed snapshot to the local FastAPI live server via the
    /api/refresh-snapshot endpoint so WebSocket clients get instant updates.
    Falls back gracefully if the server is not running.
    """
    import urllib.request
    import urllib.error
    server_url = os.environ.get("LIVE_SERVER_URL", "http://127.0.0.1:8000")
    secret = os.environ.get("WEBHOOK_SECRET", "")
    try:
        payload = json.dumps(snapshot).encode("utf-8")
        req = urllib.request.Request(
            f"{server_url}/api/refresh-snapshot",
            data=payload,
            headers={
                "Content-Type": "application/json",
                "X-Internal-Token": secret,
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            result = json.loads(resp.read())
            log.info("Pushed to live server: ws_clients=%d", result.get("ws_clients", 0))
            return True
    except Exception as exc:
        log.debug("Live server push skipped (not running?): %s", exc)
        return False


def register_bdl_webhook(endpoint_url: str) -> dict:
    """
    Register a webhook endpoint with BDL for World Cup events.
    Requires BDL_API_KEY in environment.
    """
    import requests as _req
    api_key = os.environ.get("BDL_API_KEY", "")
    if not api_key:
        raise ValueError("BDL_API_KEY not set")

    # BDL webhook registration endpoint (check BDL docs for exact path)
    base_url = "https://api.balldontlie.io/fifa/v1"
    headers = {"Authorization": api_key, "Content-Type": "application/json"}

    # First check existing endpoints
    try:
        r = _req.get(f"{base_url}/webhooks", headers=headers, timeout=10)
        r.raise_for_status()
        existing = r.json()
        log.info("Existing webhooks: %s", existing)
    except Exception as exc:
        log.warning("Could not list existing webhooks: %s", exc)
        existing = {}

    # Register our endpoint
    payload = {
        "url": endpoint_url,
        "events": [
            "goal.scored",
            "match.started",
            "match.halftime",
            "match.ended",
            "match.status_changed",
        ],
        "description": "WC2026 Live PMF Engine",
    }
    r = _req.post(f"{base_url}/webhooks", json=payload, headers=headers, timeout=10)
    r.raise_for_status()
    result = r.json()
    log.info("Webhook registered: %s", result)
    return result


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser(description="WC2026 live match PMF snapshot")
    parser.add_argument("--health-only", action="store_true",
                        help="Only write a health-OK status file, skip live snapshot")
    parser.add_argument("--register-webhook", metavar="URL",
                        help="Register BDL webhook for this endpoint URL and exit")
    args = parser.parse_args()

    log.info("=== WC2026 Live Snapshot ===")
    t0 = time.time()

    if args.register_webhook:
        log.info("Registering BDL webhook endpoint: %s", args.register_webhook)
        try:
            result = register_bdl_webhook(args.register_webhook)
            print(json.dumps(result, indent=2))
        except Exception as exc:
            log.error("Webhook registration failed: %s", exc)
            sys.exit(1)
        return

    if args.health_only:
        write_health_status(True, "Daily pipeline completed successfully")
        log.info("Health status written.")
        return

    try:
        snapshot = run_live_snapshot()
    except Exception as exc:
        log.error("Snapshot computation failed: %s", exc)
        write_health_status(False, f"Live snapshot failed: {exc}")
        sys.exit(1)

    log.info("Snapshot: status=%s, %d live matches", snapshot["status"], snapshot["n_live"])

    # Write local file FIRST so the self-chain logic can read it even if FTP fails.
    live_dir = REPO_ROOT / "data" / "live"
    live_dir.mkdir(parents=True, exist_ok=True)
    (live_dir / "latest.json").write_text(json.dumps(snapshot, indent=2))

    # FTP upload — log and continue on failure; the chain must not die due to FTP issues.
    try:
        upload_snapshot(snapshot)
    except Exception as ftp_exc:
        log.error("FTP upload failed (chain continues): %s", ftp_exc)
        write_health_status(False, f"FTP upload failed: {ftp_exc}")

    # Push to live server for instant WebSocket broadcast
    push_to_live_server(snapshot)
    write_health_status(True, f"Live snapshot OK — {snapshot['n_live']} live matches",
                        {"n_live": snapshot["n_live"], "snapshot_status": snapshot["status"]})
    log.info("Done in %.1fs", time.time() - t0)


if __name__ == "__main__":
    main()
