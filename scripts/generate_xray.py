"""
Wizard Sports Market X-Ray Generator
=====================================
Reads published prediction JSON + live snapshot + CLV records and produces
data/published/wc-xray.json — a trader-facing market edge table.

Usage:
    python scripts/generate_xray.py [--date 2026-06-20]
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "src"))

try:
    from dotenv import load_dotenv
    load_dotenv(REPO_ROOT / ".env")
except ImportError:
    pass

ET = ZoneInfo("America/New_York")

# ── Market label map ─────────────────────────────────────────────────────────
MARKET_LABELS: dict[str, str] = {
    "home_win": "Home Win (1X2)",
    "draw": "Draw (1X2)",
    "away_win": "Away Win (1X2)",
    "draw_no_bet_home": "DNB Home",
    "draw_no_bet_away": "DNB Away",
    "double_chance_1x": "Double Chance 1X",
    "double_chance_x2": "Double Chance X2",
    "double_chance_12": "Double Chance 12",
    "btts_yes": "BTTS Yes",
    "btts_no": "BTTS No",
    "clean_sheet_home": "Home Clean Sheet",
    "clean_sheet_away": "Away Clean Sheet",
    "over_0_5": "Total Over 0.5",
    "over_1_5": "Total Over 1.5",
    "over_2_5": "Total Over 2.5",
    "over_3_5": "Total Over 3.5",
    "over_4_5": "Total Over 4.5",
    "under_0_5": "Total Under 0.5",
    "under_1_5": "Total Under 1.5",
    "under_2_5": "Total Under 2.5",
    "under_3_5": "Total Under 3.5",
    "under_4_5": "Total Under 4.5",
    "home_over_0_5": "Home Team Over 0.5",
    "home_over_1_5": "Home Team Over 1.5",
    "home_over_2_5": "Home Team Over 2.5",
    "away_over_0_5": "Away Team Over 0.5",
    "away_over_1_5": "Away Team Over 1.5",
    "away_over_2_5": "Away Team Over 2.5",
    "asian_handicap_home_-2": "AH Home -2",
    "asian_handicap_home_-1_5": "AH Home -1.5",
    "asian_handicap_home_-1": "AH Home -1",
    "asian_handicap_home_-0_5": "AH Home -0.5",
    "asian_handicap_home_0": "AH Home 0 (Pick'em)",
    "asian_handicap_home_0_5": "AH Home +0.5",
    "asian_handicap_home_1": "AH Home +1",
    "asian_handicap_home_1_5": "AH Home +1.5",
    "asian_handicap_home_2": "AH Home +2",
    # underscore-neg variants used in actual JSON
    "asian_handicap_home_neg2": "AH Home -2",
    "asian_handicap_home_neg1_5": "AH Home -1.5",
    "asian_handicap_home_neg1": "AH Home -1",
    "asian_handicap_home_neg0_5": "AH Home -0.5",
    "asian_handicap_home_-0.5": "AH Home -0.5",
}

# ── Decided-market detection ─────────────────────────────────────────────────
def _is_market_decided(key: str, home_goals: int, away_goals: int) -> bool:
    """Return True when a market outcome is already settled by the current score.
    
    Over/under total goal lines are trivially resolved once enough goals have
    been scored; showing them as actionable creates fake edge from stale market
    prices.  Clean sheet and BTTS markets settle similarly.
    """
    total = home_goals + away_goals
    # Over N.5 goals: decided (TRUE) once total >= N+1
    over_map = {
        "over_0_5": 1, "over_1_5": 2, "over_2_5": 3,
        "over_3_5": 4, "over_4_5": 5,
    }
    if key in over_map and total >= over_map[key]:
        return True
    # Under N.5 goals: decided (FALSE/impossible) once total > N
    under_map = {
        "under_0_5": 1, "under_1_5": 2, "under_2_5": 3,
        "under_3_5": 4, "under_4_5": 5,
    }
    if key in under_map and total >= under_map[key]:
        return True
    # Home team total over lines
    home_over_map = {
        "home_over_0_5": 1, "home_over_1_5": 2, "home_over_2_5": 3,
    }
    if key in home_over_map and home_goals >= home_over_map[key]:
        return True
    # Away team total over lines
    away_over_map = {
        "away_over_0_5": 1, "away_over_1_5": 2, "away_over_2_5": 3,
    }
    if key in away_over_map and away_goals >= away_over_map[key]:
        return True
    # BTTS yes: decided once both teams have scored
    if key == "btts_yes" and home_goals > 0 and away_goals > 0:
        return True
    # BTTS no / clean sheets: decided impossible once both teams scored or one concedes
    if key == "btts_no" and home_goals > 0 and away_goals > 0:
        return True
    if key == "clean_sheet_home" and away_goals > 0:
        return True
    if key == "clean_sheet_away" and home_goals > 0:
        return True
    return False


# Total goals over/under line market keys — BDL does not update these live,
# so their prices remain at pre-game opening lines during in-play markets.
TOTAL_GOALS_LINES: frozenset[str] = frozenset({
    "over_0_5", "over_1_5", "over_2_5", "over_3_5", "over_4_5",
    "under_0_5", "under_1_5", "under_2_5", "under_3_5", "under_4_5",
})


# Markets to expose (canonical set + any value_flag edge markets)
CORE_MARKETS: set[str] = {
    "home_win", "draw", "away_win",
    "draw_no_bet_home", "draw_no_bet_away",
    "double_chance_1x", "double_chance_x2", "double_chance_12",
    "btts_yes", "btts_no",
    "clean_sheet_home", "clean_sheet_away",
    "over_0_5", "over_1_5", "over_2_5", "over_3_5", "over_4_5",
    "under_0_5", "under_1_5", "under_2_5", "under_3_5", "under_4_5",
    "home_over_0_5", "home_over_1_5", "home_over_2_5",
    "away_over_0_5", "away_over_1_5", "away_over_2_5",
    "asian_handicap_home_-2", "asian_handicap_home_-1_5", "asian_handicap_home_-1",
    "asian_handicap_home_-0_5", "asian_handicap_home_0",
    "asian_handicap_home_0_5", "asian_handicap_home_1",
    "asian_handicap_home_1_5", "asian_handicap_home_2",
    # underscore-neg variants as they appear in actual JSON
    "asian_handicap_home_neg2", "asian_handicap_home_neg1_5", "asian_handicap_home_neg1",
    "asian_handicap_home_neg0_5",
    "asian_handicap_home_-0.5",
}

# ── Team abbreviation map (FIFA standard) ────────────────────────────────────
TEAM_ABBR: dict[str, str] = {
    "Argentina": "ARG", "Australia": "AUS", "Austria": "AUT", "Belgium": "BEL",
    "Bolivia": "BOL", "Brazil": "BRA", "Cameroon": "CMR", "Canada": "CAN",
    "Chile": "CHI", "Colombia": "COL", "Costa Rica": "CRC", "Croatia": "CRO",
    "Cuba": "CUB", "Curaçao": "CUW", "Denmark": "DEN", "Ecuador": "ECU",
    "Egypt": "EGY", "England": "ENG", "France": "FRA", "Germany": "GER",
    "Ghana": "GHA", "Guatemala": "GUA", "Honduras": "HON", "Hungary": "HUN",
    "Indonesia": "IDN", "Iran": "IRN", "Iraq": "IRQ", "Israel": "ISR",
    "Italy": "ITA", "Ivory Coast": "CIV", "Jamaica": "JAM", "Japan": "JPN",
    "Jordan": "JOR", "Kenya": "KEN", "Mali": "MLI", "Mexico": "MEX",
    "Morocco": "MAR", "Netherlands": "NED", "New Zealand": "NZL",
    "Nigeria": "NGA", "Panama": "PAN", "Paraguay": "PAR", "Peru": "PER",
    "Portugal": "POR", "Qatar": "QAT", "Romania": "ROU", "Saudi Arabia": "KSA",
    "Senegal": "SEN", "Serbia": "SRB", "Slovenia": "SVN", "South Korea": "KOR",
    "Spain": "ESP", "Switzerland": "SUI", "Tanzania": "TAN", "Tunisia": "TUN",
    "Turkey": "TUR", "Ukraine": "UKR", "United States": "USA", "Uruguay": "URU",
    "Venezuela": "VEN",
}


def abbr(team: str) -> str:
    return TEAM_ABBR.get(team, team[:3].upper())


# ── Math helpers ─────────────────────────────────────────────────────────────
def american_to_decimal(american: float) -> float:
    if american > 0:
        return 1 + american / 100
    else:
        return 1 + 100 / abs(american)


def decimal_to_american(decimal: float) -> int:
    if decimal <= 1.0:
        return 0
    if decimal >= 2.0:
        return int(round((decimal - 1) * 100))
    else:
        return int(round(-100 / (decimal - 1)))


def prob_to_american(p: float) -> int:
    if p <= 0 or p >= 1:
        return 0
    if p >= 0.5:
        return int(round(-100 * p / (1 - p)))
    else:
        return int(round(100 * (1 - p) / p))


def calculate_ev(model_prob: float, market_decimal: float) -> float:
    return model_prob * (market_decimal - 1) * 100 - (1 - model_prob) * 100


def confidence_grade(edge_pp: float, match_uncertainty: str = "MEDIUM") -> str:
    if edge_pp >= 5.0 and match_uncertainty == "LOW":
        return "A"
    elif edge_pp >= 3.0:
        return "B"
    elif edge_pp >= 1.5:
        return "C"
    else:
        return "D"


def pregame_action(edge_pp: float, prev_edge_pp: float | None = None) -> str:
    if prev_edge_pp is not None and prev_edge_pp > edge_pp + 0.5:
        return "DO NOT CHASE"
    if edge_pp < 1.0:
        return "PASS"
    elif edge_pp < 2.5:
        return "LEAN"
    elif edge_pp < 4.0:
        return "SMALL BET"
    else:
        return "BET"


def live_action(
    edge_pp: float,
    prev_edge_pp: float | None = None,
    pmf_age_min: float = 0.0,
    odds_age_sec: float = 0.0,
    price_moved_against: bool = False,
    market_odds_stale: bool = False,
    regulation_minute: float | None = None,
) -> str:
    if market_odds_stale:
        return "WAIT"  # Cannot act when comparing live model to stale pregame odds

    if prev_edge_pp is not None and prev_edge_pp > edge_pp + 0.5:
        return "DO NOT CHASE"

    # Cap action in final minutes — probabilities become extreme and PMF clamping
    # creates artificial edge on essentially-decided outcomes.
    if regulation_minute is not None and regulation_minute >= 85:
        return "WAIT"

    # Staleness caps
    if pmf_age_min > 7 or odds_age_sec > 90:
        return "WAIT"

    if edge_pp < 2.0:
        return "PASS"
    elif edge_pp < 4.0:
        return "WAIT" if price_moved_against else "LEAN"
    elif edge_pp < 6.0:
        return "SMALL BET"
    else:
        return "BET"


def generate_trader_note(
    market_type: str,
    selection: str,
    model_prob: float,
    market_odds_american: int | None,
    edge_pp: float,
    action: str,
    ev_per_100: float | None,
    mode: str,
) -> str:
    fair_american = prob_to_american(model_prob)
    fair_str = f"+{fair_american}" if fair_american > 0 else str(fair_american)
    mkt_str = (
        (f"+{market_odds_american}" if market_odds_american > 0 else str(market_odds_american))
        if market_odds_american is not None
        else "N/A"
    )
    edge_str = f"+{edge_pp:.1f}" if edge_pp > 0 else f"{edge_pp:.1f}"
    ev_str = (
        (f"+{ev_per_100:.1f}" if ev_per_100 > 0 else str(round(ev_per_100, 1)))
        if ev_per_100 is not None
        else "N/A"
    )

    if action == "BET":
        return (
            f"Model fair: {fair_str}. Best market: {mkt_str}. "
            f"Edge: {edge_str} pp, EV: {ev_str}% per $100. "
            f"Edge clears the {mode} execution threshold."
        )
    elif action == "SMALL BET":
        return (
            f"Model fair: {fair_str}. Best market: {mkt_str}. "
            f"Edge: {edge_str} pp, EV: {ev_str}% per $100. "
            f"Edge clears threshold; reduced sizing recommended."
        )
    elif action == "LEAN":
        return (
            f"Model fair: {fair_str}. Best market: {mkt_str}. "
            f"Edge: {edge_str} pp. Positive edge, but below the {mode} execution threshold. "
            f"Monitor for a better price."
        )
    elif action == "WAIT":
        return (
            f"Model fair: {fair_str}. Best market: {mkt_str}. "
            f"Edge: {edge_str} pp. Price is close but not yet sufficient. Wait for improvement."
        )
    elif action == "DO NOT CHASE":
        return (
            f"Model fair: {fair_str}. Edge existed earlier but has decreased to {edge_str} pp. "
            f"Do not chase a deteriorating edge."
        )
    else:
        return f"Model fair: {fair_str}. No material edge on this market at current prices."


# ── Data loaders ─────────────────────────────────────────────────────────────
def load_published(date: str) -> list[dict]:
    pub_path = REPO_ROOT / "data" / "published" / f"{date}.json"
    if pub_path.exists():
        doc = json.loads(pub_path.read_text())
        return doc.get("matches", [])
    fallback = REPO_ROOT / "data" / "published" / "all_scheduled_2026.json"
    if fallback.exists():
        doc = json.loads(fallback.read_text())
        return [m for m in doc.get("matches", []) if m.get("match_date_et") == date]
    return []


def load_live() -> dict:
    """Returns live JSON or empty dict. Checks wc-live.json first, falls back to latest.json."""
    for p in ["data/live/wc-live.json", "data/live/latest.json"]:
        live_path = REPO_ROOT / p
        if live_path.exists():
            try:
                return json.loads(live_path.read_text())
            except Exception:
                continue
    return {}


def load_clv() -> dict[tuple, dict]:
    """Returns {(match_id, market): record} from CLV records."""
    clv_path = REPO_ROOT / "data" / "clv" / "2026" / "records.jsonl"
    index: dict[tuple, dict] = {}
    if not clv_path.exists():
        return index
    with open(clv_path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
                key = (str(rec.get("match_id", "")), str(rec.get("market", "")))
                index[key] = rec
            except Exception:
                pass
    return index


def load_snapshots(date: str) -> dict[tuple, list[dict]]:
    """Returns {(match_id, market_id): [snapshot rows]} sorted oldest-first."""
    snap_path = REPO_ROOT / "data" / "xray" / "snapshots" / f"{date}.jsonl"
    index: dict[tuple, list[dict]] = {}
    if not snap_path.exists():
        return index
    with open(snap_path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
                key = (str(row.get("match_id", "")), str(row.get("market_id", "")))
                index.setdefault(key, []).append(row)
            except Exception:
                pass
    return index


# ── Market processing ─────────────────────────────────────────────────────────
def build_markets(
    match_id: str,
    derived_markets: dict,
    market_implied_markets: dict,
    edge_report_edges: list[dict],
    mode: str,
    home_team: str,
    away_team: str,
    prev_snapshots: dict[tuple, list[dict]],
    pmf_age_min: float = 0.0,
    odds_age_sec: float = 0.0,
    match_uncertainty: str = "MEDIUM",
    warnings: list[str] | None = None,
    market_odds_stale: bool = False,
    regulation_minute: float | None = None,
    home_goals: int = 0,
    away_goals: int = 0,
) -> list[dict]:
    warnings = warnings or []
    has_warnings = any(w for w in warnings if w)

    # Build edge lookup by market key
    edge_lookup: dict[str, dict] = {}
    for e in edge_report_edges:
        edge_lookup[e["market"]] = e

    # Determine which markets to expose
    candidate_keys: set[str] = set()
    # Core markets present in both dm and mim
    for k in CORE_MARKETS:
        if k in derived_markets and k in market_implied_markets:
            candidate_keys.add(k)
    # Value-flagged edge markets
    for e in edge_report_edges:
        if e.get("value_flag"):
            k = e["market"]
            if k in derived_markets and k in market_implied_markets:
                candidate_keys.add(k)

    market_rows: list[dict] = []

    for key in sorted(candidate_keys):
        # Skip markets whose outcome is already settled by the current score.
        # These create fake edge from stale market prices (e.g. over 0.5 at 72%
        # when the score is already 1-0 — the line hasn't moved and the model
        # is trivially at 99.9%, manufacturing a phantom +28pp edge).
        if mode == "live" and _is_market_decided(key, home_goals, away_goals):
            continue

        model_prob = derived_markets.get(key)
        market_no_vig = market_implied_markets.get(key)

        if model_prob is None or market_no_vig is None:
            continue
        if not isinstance(model_prob, (int, float)) or not isinstance(market_no_vig, (int, float)):
            continue
        if math.isnan(model_prob) or math.isnan(market_no_vig):
            continue
        # Clamp instead of skip: late-game PMFs produce exact 0.0 or 1.0 (Poisson underflow).
        # Clamping preserves market display (PASS/DO NOT CHASE) while keeping math valid.
        model_prob = max(0.001, min(0.999, float(model_prob)))

        edge_pp = (model_prob - market_no_vig) * 100

        # In live mode, BDL does not update total goals over/under lines — they
        # remain at their pre-game opening prices.  A large negative edge on a
        # total goals line (market >> model) almost always means the line is stale,
        # not a real "market knows better" signal.  Hide them to keep the table
        # clean.  -30pp threshold: safely above any realistic live edge, well below
        # the 50-80pp gaps produced by stale pregame totals mid/late game.
        if mode == "live" and key in TOTAL_GOALS_LINES and edge_pp < -25.0:
            # #region agent log H-3
            try:
                import json as _jl, time as _tl, os as _ol
                _lp = "/Users/josephshackelford/worldcup2026-model/.cursor/debug-3f8dcc.log"
                _ol.makedirs(_ol.path.dirname(_lp), exist_ok=True)
                with open(_lp, "a") as _lf:
                    _lf.write(_jl.dumps({"sessionId":"3f8dcc","hypothesisId":"H-3","location":"generate_xray.py:stale_totals","message":"stale_total_skipped","data":{"match_id":match_id,"key":key,"edge_pp":round(edge_pp,2),"model":round(model_prob,4),"mkt":round(market_no_vig,4)},"timestamp":int(_tl.time()*1000)}) + "\n")
            except Exception:
                pass
            # #endregion
            continue

        model_fair_american = prob_to_american(model_prob)

        # Market odds: use actual odds from edge report when available,
        # otherwise estimate from market_no_vig (fair market decimal = 1/p_no_vig).
        edge_entry = edge_lookup.get(key)
        market_odds_decimal: float | None = None
        market_odds_american: int | None = None
        market_odds_estimated: bool = False
        if edge_entry:
            raw_odds = edge_entry.get("market_odds")
            if raw_odds and isinstance(raw_odds, (int, float)) and raw_odds > 1.0:
                market_odds_decimal = float(raw_odds)
                market_odds_american = decimal_to_american(market_odds_decimal)
        if market_odds_decimal is None and market_no_vig > 0.01:
            # Estimate market fair decimal from no-vig probability.
            # This is the market's implied fair price (no vig), slightly better
            # than actual market odds but allows approximate EV calculation.
            market_odds_decimal = 1.0 / market_no_vig
            market_odds_american = decimal_to_american(market_odds_decimal)
            market_odds_estimated = True

        # EV
        ev_per_100: float | None = None
        if market_odds_decimal is not None:
            ev_per_100 = calculate_ev(model_prob, market_odds_decimal)

        # Previous snapshot
        snap_key = (match_id, key)
        prev_rows = prev_snapshots.get(snap_key, [])
        prev_edge_pp: float | None = prev_rows[-1]["edge_pp"] if prev_rows else None

        # Action
        if mode == "live":
            action = live_action(
                edge_pp, prev_edge_pp,
                pmf_age_min=pmf_age_min,
                odds_age_sec=odds_age_sec,
                market_odds_stale=market_odds_stale,
                regulation_minute=regulation_minute,
            )
        else:
            action = pregame_action(edge_pp, prev_edge_pp)

        # Confidence (reduce by one letter if warnings)
        conf = confidence_grade(edge_pp, match_uncertainty)
        if has_warnings and conf != "D":
            conf = chr(ord(conf) + 1)  # A→B, B→C, C→D

        # Label
        label = MARKET_LABELS.get(key, key.replace("_", " ").title())

        # Selection label (context-aware)
        selection_label = _selection_label(key, home_team, away_team, label)

        trader_note = generate_trader_note(
            market_type=key,
            selection=selection_label,
            model_prob=model_prob,
            market_odds_american=market_odds_american,
            edge_pp=edge_pp,
            action=action,
            ev_per_100=ev_per_100,
            mode=mode,
        )

        market_rows.append({
            "market_id": key,
            "market_label": label,
            "selection_label": selection_label,
            "model_probability": round(model_prob, 4),
            "model_fair_american": model_fair_american,
            "market_odds_american": market_odds_american,
            "market_odds_estimated": market_odds_estimated,
            "market_no_vig_probability": round(market_no_vig, 4),
            "edge_pp": round(edge_pp, 2),
            "ev_per_100": round(ev_per_100, 2) if ev_per_100 is not None else None,
            "confidence": conf,
            "action": action,
            "trader_note": trader_note,
        })

    # Sort by |edge_pp| descending
    market_rows.sort(key=lambda x: abs(x["edge_pp"]), reverse=True)

    return market_rows


def _selection_label(key: str, home: str, away: str, fallback: str) -> str:
    if key == "home_win":
        return f"{home} ML"
    if key == "away_win":
        return f"{away} ML"
    if key == "draw":
        return "Draw"
    if key == "draw_no_bet_home":
        return f"{home} DNB"
    if key == "draw_no_bet_away":
        return f"{away} DNB"
    if "home_over" in key or "home_under" in key:
        return f"{home} {fallback.split(' ', 2)[-1]}"
    if "away_over" in key or "away_under" in key:
        return f"{away} {fallback.split(' ', 2)[-1]}"
    if "asian_handicap_home" in key:
        return f"{home} {fallback.split('AH Home ')[-1]}"
    return fallback


def build_line_movement(
    markets: list[dict],
    prev_snapshots: dict[tuple, list[dict]],
    match_id: str,
) -> dict:
    if not markets:
        return {"snapshots_available": 0, "open_edge_pp": None, "current_edge_pp": None, "edge_change": None, "note": "No data"}

    # Use best (highest abs edge) market as representative
    best = markets[0]
    snap_key = (match_id, best["market_id"])
    prev_rows = prev_snapshots.get(snap_key, [])
    n_snaps = len(prev_rows) + 1

    open_edge = prev_rows[0]["edge_pp"] if prev_rows else best["edge_pp"]
    current_edge = best["edge_pp"]
    edge_change = round(current_edge - open_edge, 2)

    if abs(edge_change) < 0.1:
        note = "Edge stable since open."
    elif edge_change > 0:
        note = "Edge increased from open; model-driven move."
    else:
        note = "Edge decreased from open; market may have adjusted."

    return {
        "snapshots_available": n_snaps,
        "open_edge_pp": round(open_edge, 2),
        "current_edge_pp": round(current_edge, 2),
        "edge_change": edge_change,
        "note": note,
    }


def build_what_changed(
    markets: list[dict],
    prev_snapshots: dict[tuple, list[dict]],
    match_id: str,
) -> list[dict]:
    changes = []
    for mkt in markets:
        key = mkt["market_id"]
        snap_key = (match_id, key)
        prev_rows = prev_snapshots.get(snap_key, [])
        if not prev_rows:
            continue
        prev = prev_rows[-1]
        diffs: dict[str, dict] = {}
        if abs(mkt["model_probability"] - prev.get("model_probability", mkt["model_probability"])) > 0.005:
            diffs["model_probability"] = {
                "prev": prev.get("model_probability"),
                "curr": mkt["model_probability"],
            }
        if mkt["market_odds_american"] is not None and prev.get("market_odds_american") is not None:
            if abs(mkt["market_odds_american"] - prev["market_odds_american"]) >= 2:
                diffs["market_odds_american"] = {
                    "prev": prev.get("market_odds_american"),
                    "curr": mkt["market_odds_american"],
                }
        if abs(mkt["edge_pp"] - prev.get("edge_pp", mkt["edge_pp"])) > 0.2:
            diffs["edge_pp"] = {
                "prev": prev.get("edge_pp"),
                "curr": mkt["edge_pp"],
            }
        if mkt["action"] != prev.get("action", mkt["action"]):
            diffs["action"] = {
                "prev": prev.get("action"),
                "curr": mkt["action"],
            }
        if diffs:
            changes.append({
                "market_id": key,
                "market_label": mkt["market_label"],
                "changes": diffs,
            })
    return changes


def build_clv_signals(
    match_id: str,
    markets: list[dict],
    clv_index: dict[tuple, dict],
) -> list[dict]:
    signals = []
    for mkt in markets:
        key = (str(match_id), mkt["market_id"])
        rec = clv_index.get(key)
        if rec is None:
            continue
        closing_ts = rec.get("closing_timestamp")
        beat_close = None  # null until closing odds confirmed
        signals.append({
            "market_id": mkt["market_id"],
            "market_label": mkt["market_label"],
            "model_prob": rec.get("model_prob"),
            "model_fair_odds": rec.get("model_fair_odds"),
            "prediction_timestamp": rec.get("prediction_timestamp"),
            "closing_timestamp": closing_ts,
            "closing_source": rec.get("closing_source"),
            "beat_close": beat_close,
        })
    return signals


def _top_action_and_confidence(markets: list[dict]) -> tuple[str, str, str | None, float | None]:
    """Returns (top_action, confidence, best_edge_market, best_edge_pct)."""
    if not markets:
        return "WAIT", "D", None, None

    # Priority order for top_action
    action_priority = ["BET", "SMALL BET", "LEAN", "WAIT", "DO NOT CHASE", "PASS"]
    top_action = "PASS"
    for priority_action in action_priority:
        if any(m["action"] == priority_action for m in markets):
            top_action = priority_action
            break

    # Best edge market (positive edge only)
    positive = [m for m in markets if m["edge_pp"] > 0]
    if positive:
        best = positive[0]
        best_edge_market = best["market_id"]
        best_edge_pct = best["edge_pp"]
    else:
        best_edge_market = markets[0]["market_id"] if markets else None
        best_edge_pct = markets[0]["edge_pp"] if markets else None

    # Overall confidence
    confs = [m["confidence"] for m in markets]
    conf_order = {"A": 0, "B": 1, "C": 2, "D": 3}
    best_conf = min(confs, key=lambda c: conf_order.get(c, 99))

    return top_action, best_conf, best_edge_market, best_edge_pct


def _match_uncertainty(pred: dict) -> str:
    uncertainty_pct = pred.get("edge_report", {}).get("lambda_uncertainty_pct", 20)
    if isinstance(uncertainty_pct, (int, float)):
        if uncertainty_pct < 10:
            return "LOW"
        elif uncertainty_pct < 25:
            return "MEDIUM"
    return "HIGH"


def process_pregame_match(
    m: dict,
    clv_index: dict[tuple, dict],
    prev_snapshots: dict[tuple, list[dict]],
    now_utc: datetime,
) -> dict:
    pred = m.get("prediction", {})
    match_id = str(m["match_id"])
    home = m.get("home_team", "")
    away = m.get("away_team", "")

    dm = pred.get("derived_markets", {})
    mim = pred.get("market_implied_markets", {})
    edges = pred.get("edge_report", {}).get("edges", [])
    odds_ts = m.get("odds_timestamp") or pred.get("odds_timestamp")

    odds_age_sec = 0.0
    if odds_ts:
        try:
            ots = datetime.fromisoformat(odds_ts.replace("Z", "+00:00"))
            odds_age_sec = (now_utc - ots).total_seconds()
        except Exception:
            pass

    uncertainty = _match_uncertainty(pred)
    warnings = pred.get("warnings", [])

    markets = build_markets(
        match_id=match_id,
        derived_markets=dm,
        market_implied_markets=mim,
        edge_report_edges=edges,
        mode="pregame",
        home_team=home,
        away_team=away,
        prev_snapshots=prev_snapshots,
        odds_age_sec=odds_age_sec,
        match_uncertainty=uncertainty,
        warnings=warnings,
    )

    top_action, confidence, best_edge_market, best_edge_pct = _top_action_and_confidence(markets)
    line_movement = build_line_movement(markets, prev_snapshots, match_id)
    what_changed = build_what_changed(markets, prev_snapshots, match_id)
    clv_signals = build_clv_signals(match_id, markets, clv_index)

    actionable = [m for m in markets if m["action"] not in ("PASS", "DO NOT CHASE")]
    summary_note = _summary_note(actionable, home, away, "pregame")

    return {
        "match_id": match_id,
        "home_team": home,
        "away_team": away,
        "home_abbr": abbr(home),
        "away_abbr": abbr(away),
        "kickoff_utc": m.get("match_datetime_utc"),
        "status": m.get("status", "scheduled"),
        "mode": "pregame",
        "minute": None,
        "score": None,
        "odds_timestamp": odds_ts,
        "top_action": top_action,
        "best_edge_market": best_edge_market,
        "best_edge_pct": best_edge_pct,
        "confidence": confidence,
        "summary_note": summary_note,
        "markets": markets,
        "line_movement": line_movement,
        "what_changed": what_changed,
        "clv_signals": clv_signals,
    }


def process_live_match(
    lm: dict,
    clv_index: dict[tuple, dict],
    prev_snapshots: dict[tuple, list[dict]],
    now_utc: datetime,
    live_generated_at: str | None,
    pub_match_lookup: dict[str, dict] | None = None,
) -> dict:
    match_id = str(lm.get("match_id", ""))
    home = lm.get("home_team", "")
    away = lm.get("away_team", "")

    dm = lm.get("derived_markets", {})
    # Live JSON may not have market_implied_markets. When missing, use the
    # pregame market_implied_markets from the published prediction (191 markets)
    # so edge = live-model-prob minus pregame-market-no-vig gives a meaningful comparison.
    mim_is_stale = lm.get("market_implied_markets") is None  # True = using pregame fallback
    mim = lm.get("market_implied_markets")
    if mim is None and pub_match_lookup:
        pub_m = pub_match_lookup.get(match_id, {})
        mim = pub_m.get("prediction", {}).get("market_implied_markets")
    if mim is None:
        mim = dm  # last resort: zero-edge fallback


    edges_raw = lm.get("live_edge", {})
    edges: list[dict] = []
    for side in ("home", "draw", "away"):
        e = edges_raw.get(side, {})
        if e:
            mkt_key = {"home": "home_win", "draw": "draw", "away": "away_win"}[side]
            edges.append({
                "market": mkt_key,
                "model_prob": e.get("ev"),
                "market_prob": None,
                "edge_pct": (e.get("edge") or 0) * 100,
                "fair_odds": None,
                "market_odds": None,
                "half_kelly_pct": (e.get("kelly_stake") or 0) * 100,
                "value_flag": e.get("is_value", False),
                "value_reason": "",
            })

    # PMF age
    pmf_age_min = 0.0
    if live_generated_at:
        try:
            gen = datetime.fromisoformat(live_generated_at.replace("Z", "+00:00"))
            pmf_age_min = (now_utc - gen).total_seconds() / 60
        except Exception:
            pass

    warnings = lm.get("warnings", [])
    uncertainty = "MEDIUM"

    h_goals = lm.get("current_home_goals", 0) or 0
    a_goals = lm.get("current_away_goals", 0) or 0

    markets = build_markets(
        match_id=match_id,
        derived_markets=dm,
        market_implied_markets=mim,
        edge_report_edges=edges,
        mode="live",
        home_team=home,
        away_team=away,
        prev_snapshots=prev_snapshots,
        pmf_age_min=pmf_age_min,
        match_uncertainty=uncertainty,
        warnings=warnings,
        market_odds_stale=mim_is_stale,
        regulation_minute=lm.get("regulation_minute"),
        home_goals=h_goals,
        away_goals=a_goals,
    )

    top_action, confidence, best_edge_market, best_edge_pct = _top_action_and_confidence(markets)
    line_movement = build_line_movement(markets, prev_snapshots, match_id)
    what_changed = build_what_changed(markets, prev_snapshots, match_id)
    clv_signals = build_clv_signals(match_id, markets, clv_index)

    minute = lm.get("regulation_minute") or lm.get("clock_display")

    actionable = [m for m in markets if m["action"] not in ("PASS", "DO NOT CHASE")]
    summary_note = _summary_note(actionable, home, away, "live")

    return {
        "match_id": match_id,
        "home_team": home,
        "away_team": away,
        "home_abbr": abbr(home),
        "away_abbr": abbr(away),
        "kickoff_utc": None,
        "status": "live",
        "mode": "live",
        "minute": minute,
        "score": f"{h_goals}–{a_goals}",
        "odds_timestamp": None,
        "top_action": top_action,
        "best_edge_market": best_edge_market,
        "best_edge_pct": best_edge_pct,
        "confidence": confidence,
        "summary_note": summary_note,
        "live_market_odds_stale": mim_is_stale,
        "markets": markets,
        "line_movement": line_movement,
        "what_changed": what_changed,
        "clv_signals": clv_signals,
    }


def _summary_note(actionable: list[dict], home: str, away: str, mode: str) -> str:
    if not actionable:
        return f"No actionable markets for {home} vs {away} at current prices."
    top = actionable[0]
    edge_str = f"+{top['edge_pp']:.1f}" if top["edge_pp"] > 0 else f"{top['edge_pp']:.1f}"
    return (
        f"{top['action']} signal on {top['market_label']} ({edge_str} pp edge). "
        f"{len(actionable)} actionable market{'s' if len(actionable) != 1 else ''} total."
    )


def append_snapshots(date: str, all_match_objects: list[dict], now_utc: datetime) -> None:
    snap_dir = REPO_ROOT / "data" / "xray" / "snapshots"
    snap_dir.mkdir(parents=True, exist_ok=True)
    snap_path = snap_dir / f"{date}.jsonl"
    ts = now_utc.isoformat()
    lines: list[str] = []
    for match_obj in all_match_objects:
        match_id = match_obj["match_id"]
        for mkt in match_obj.get("markets", []):
            row = {
                "match_id": match_id,
                "market_id": mkt["market_id"],
                "timestamp_utc": ts,
                "model_probability": mkt["model_probability"],
                "market_odds_american": mkt["market_odds_american"],
                "edge_pp": mkt["edge_pp"],
                "action": mkt["action"],
            }
            lines.append(json.dumps(row))
    with open(snap_path, "a") as f:
        f.write("\n".join(lines))
        if lines:
            f.write("\n")
    print(f"  Appended {len(lines)} snapshot rows → {snap_path}")


# ── Main ─────────────────────────────────────────────────────────────────────
def generate(date: str | None = None) -> None:
    now_utc = datetime.now(tz=timezone.utc)
    date = date or datetime.now(tz=ET).strftime("%Y-%m-%d")

    print(f"X-Ray generator: {date}")

    # Load inputs
    pub_matches = load_published(date)
    live_doc = load_live()
    clv_index = load_clv()
    prev_snapshots = load_snapshots(date)

    # Filter out matches whose kickoff was >180 minutes ago (almost certainly finished)
    def _is_stale_match(m: dict) -> bool:
        """True if match kickoff was >3 hours ago (likely finished)."""
        ko = m.get("kickoff_utc") or m.get("match_datetime_utc") or m.get("kick_off") or ""
        if not ko:
            return False
        try:
            ko_dt = datetime.fromisoformat(str(ko).replace("Z", "+00:00"))
            if ko_dt.tzinfo is None:
                ko_dt = ko_dt.replace(tzinfo=timezone.utc)
            return (now_utc - ko_dt).total_seconds() > 105 * 60
        except Exception:
            return False

    before = len(pub_matches)
    pub_matches = [m for m in pub_matches if not _is_stale_match(m)]
    stale_filtered = before - len(pub_matches)
    if stale_filtered:
        print(f"  Filtered {stale_filtered} stale match(es) (kickoff >3h ago)")

    print(f"  Published matches: {len(pub_matches)}")
    print(f"  Live matches: {len(live_doc.get('live_matches', []))}")
    print(f"  CLV records: {len(clv_index)}")

    live_match_ids = {str(lm["match_id"]) for lm in live_doc.get("live_matches", [])}
    live_generated_at = live_doc.get("generated_at")

    # Build lookup by match_id so live matches can use pregame market_implied_markets
    pub_match_lookup: dict[str, dict] = {str(m.get("match_id", "")): m for m in pub_matches}

    pregame_results: list[dict] = []
    live_results: list[dict] = []

    # Build a full match kickoff lookup (live matches have kickoff_utc: null,
    # so pull it from the published predictions).
    all_pub_lookup: dict[str, dict] = {str(m.get("match_id", "")): m for m in pub_matches}

    # Process live matches first — skip any that kicked off >3h ago (game over,
    # BDL just hasn't marked them completed yet).
    def _live_match_stale(lm: dict) -> bool:
        mid = str(lm.get("match_id", ""))
        pub = all_pub_lookup.get(mid, {})
        ko_str = pub.get("match_datetime_utc") or pub.get("kickoff_utc") or ""
        if ko_str:
            try:
                ko_dt = datetime.fromisoformat(str(ko_str).replace("Z", "+00:00"))
                if ko_dt.tzinfo is None:
                    ko_dt = ko_dt.replace(tzinfo=timezone.utc)
                return (now_utc - ko_dt).total_seconds() > 105 * 60
            except Exception:
                pass
        # Fallback: if regulation_minute >= 90 and live doc is >5 min old, treat as done.
        # The live workflow runs every ~2 min so a 5-min gap means multiple cycles passed
        # without BDL clearing the match — almost certainly finished.
        minute = lm.get("regulation_minute") or 0
        if minute >= 90 and live_generated_at:
            try:
                gen_dt = datetime.fromisoformat(live_generated_at.replace("Z", "+00:00"))
                if gen_dt.tzinfo is None:
                    gen_dt = gen_dt.replace(tzinfo=timezone.utc)
                if (now_utc - gen_dt).total_seconds() > 5 * 60:
                    return True
            except Exception:
                pass
        return False

    for lm in live_doc.get("live_matches", []):
        if _live_match_stale(lm):
            print(f"  Skipped stale live match: {lm.get('home_team')} vs {lm.get('away_team')} (kickoff >3h ago or min>=90 and data >20min old)")
            continue
        try:
            obj = process_live_match(lm, clv_index, prev_snapshots, now_utc, live_generated_at, pub_match_lookup)
            live_results.append(obj)
        except Exception as e:
            print(f"  WARN: live match {lm.get('match_id')} failed: {e}")

    # Process pregame matches (skip any that are live)
    for m in pub_matches:
        match_id = str(m.get("match_id", ""))
        if match_id in live_match_ids:
            continue
        try:
            obj = process_pregame_match(m, clv_index, prev_snapshots, now_utc)
            pregame_results.append(obj)
        except Exception as e:
            print(f"  WARN: pregame match {match_id} failed: {e}")

    # Build output
    output = {
        "schema_version": "wo_market_xray_v1",
        "generated_at": now_utc.isoformat(),
        "date": date,
        "pregame_matches": pregame_results,
        "live_matches": live_results,
    }

    out_path = REPO_ROOT / "data" / "published" / "wc-xray.json"
    out_path.write_text(json.dumps(output, ensure_ascii=False, indent=2))
    print(f"  ✓ Wrote {out_path} ({out_path.stat().st_size:,} bytes)")
    print(f"    {len(pregame_results)} pregame, {len(live_results)} live matches")

    all_objs = pregame_results + live_results
    append_snapshots(date, all_objs, now_utc)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate Market X-Ray JSON")
    parser.add_argument("--date", default=None, help="Date YYYY-MM-DD (default: today ET)")
    args = parser.parse_args()
    generate(args.date)


if __name__ == "__main__":
    main()
