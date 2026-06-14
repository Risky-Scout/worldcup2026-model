"""
Pre-match closing odds capture.

Runs every 15 minutes via GitHub Actions (pre-match.yml).
Scans every scheduled 2026 WC match, finds any kicking off within
LOOKAHEAD_MIN minutes, sleeps until T-CLOSING_BEFORE_MIN, then
fetches live BDL odds and records the closing line in the CLV store.

Closing line = consensus SHIN no-vig probability across all available
market-makers, captured CLOSING_BEFORE_MIN minutes before kickoff.

True CLV = model_prob vs closing_prob  (rather than vs opening_prob).

Usage:
    python scripts/closing_odds_snapshot.py
    make pre-match-snapshot
"""
from __future__ import annotations

import json
import logging
import os
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "src"))

try:
    from dotenv import load_dotenv
    load_dotenv(REPO_ROOT / ".env")
except ImportError:
    pass

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(name)s: %(message)s",
)
log = logging.getLogger("closing_odds")

LOOKAHEAD_MIN = 15      # scan: matches kicking off within this window
CLOSING_BEFORE_MIN = 3  # capture odds this many minutes before kickoff
DATA_DIR = REPO_ROOT / "data"
CLV_PATH = DATA_DIR / "clv" / "2026" / "records.jsonl"
DEBUG_LOG = REPO_ROOT / ".cursor" / "debug-3f8dcc.log"

# ── debug logging helper ─────────────────────────────────────────────────────

def _dbg(msg: str, data: dict, hyp: str = "A", run_id: str = "pre1") -> None:
    """Append one NDJSON line to the debug log file."""
    import time as _t
    entry = {
        "sessionId": "3f8dcc",
        "runId": run_id,
        "hypothesisId": hyp,
        "location": "closing_odds_snapshot.py",
        "message": msg,
        "data": data,
        "timestamp": int(_t.time() * 1000),
    }
    try:
        DEBUG_LOG.parent.mkdir(parents=True, exist_ok=True)
        with open(DEBUG_LOG, "a") as _f:
            _f.write(json.dumps(entry) + "\n")
    except Exception:
        pass


# ── match discovery ──────────────────────────────────────────────────────────

def _load_scheduled_matches() -> list[dict]:
    """
    Scan all data/published/YYYY-MM-DD.json files and collect every
    match with status='scheduled' that has a parseable kickoff time.
    """
    import dateutil.parser

    pub_dir = DATA_DIR / "published"
    matches: list[dict] = []
    for f in sorted(pub_dir.glob("2026-*.json")):
        try:
            data = json.loads(f.read_text())
            for m in data.get("matches", []):
                if m.get("status") != "scheduled":
                    continue
                ko_raw = m.get("match_datetime_utc") or m.get("datetime")
                if not ko_raw:
                    continue
                try:
                    ko = dateutil.parser.parse(str(ko_raw))
                    if ko.tzinfo is None:
                        ko = ko.replace(tzinfo=timezone.utc)
                except Exception:
                    continue
                matches.append({
                    "match_id": str(m["match_id"]),
                    "home_team": m.get("home_team", "?"),
                    "away_team": m.get("away_team", "?"),
                    "kickoff_utc": ko,
                })
        except Exception as exc:
            log.warning("Could not read %s: %s", f.name, exc)

    return matches


# ── odds parsing ─────────────────────────────────────────────────────────────

def _parse_closing_probs(odds_rows: list[dict]) -> dict[str, float]:
    """
    Given raw BDL odds rows for one match (multi-vendor), produce a
    dict of market_name → no-vig closing probability.

    Returns e.g.:
        {"home_win": 0.72, "draw": 0.19, "away_win": 0.09,
         "btts_yes": 0.55, "btts_no": 0.45,
         "over_2_5": 0.48, "under_2_5": 0.52, ...}
    """
    from wc2026.markets.no_vig import (
        american_to_decimal,
        strip_vig_1x2,
        strip_vig_total,
    )

    result: dict[str, float] = {}

    # ── 1X2 moneyline ────────────────────────────────────────────────────────
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
        import statistics
        n = len(ml_probs)
        result["home_win"] = round(statistics.mean(p[0] for p in ml_probs), 6)
        result["draw"]     = round(statistics.mean(p[1] for p in ml_probs), 6)
        result["away_win"] = round(statistics.mean(p[2] for p in ml_probs), 6)
        log.info("  1X2 closing: H=%.3f D=%.3f A=%.3f  (%d vendors)",
                 result["home_win"], result["draw"], result["away_win"], n)

    # ── totals (over/under X.5 goals) ────────────────────────────────────────
    # Collect per-line_value lists of (over_odds, under_odds) across vendors
    from collections import defaultdict
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
            # Only track lines we report (0.5 – 6.5)
            if line not in {0.5, 1.5, 2.5, 3.5, 4.5, 5.5, 6.5}:
                continue
            over_dec = under_dec = None
            for outcome in mkt.get("outcomes", []):
                if outcome.get("type") == "over":
                    over_dec = outcome.get("decimal_odds")
                elif outcome.get("type") == "under":
                    under_dec = outcome.get("decimal_odds")
            if over_dec and under_dec:
                # Convert decimal to American for strip_vig_total
                def _dec_to_amer(d: float) -> int:
                    if d >= 2.0:
                        return int((d - 1) * 100)
                    else:
                        return int(-100 / (d - 1))
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
            import statistics
            line_key = str(line).replace(".", "_")  # over_2_5
            result[f"over_{line_key}"]  = round(statistics.mean(over_probs), 6)
            result[f"under_{line_key}"] = round(statistics.mean(under_probs), 6)

    if any(k.startswith("over_") for k in result):
        log.info("  Totals closing: %s", {k: round(v, 3) for k, v in result.items()
                                          if k.startswith("over_") or k.startswith("under_")})

    # ── BTTS (both teams to score) ────────────────────────────────────────────
    btts_yes_decimals: list[float] = []
    btts_no_decimals:  list[float] = []

    for row in odds_rows:
        for mkt in row.get("markets", []):
            if mkt.get("type") != "both_teams_to_score":
                continue
            # BTTS markets use scope="both_teams", not scope="match"
            if mkt.get("period") != "match" or mkt.get("scope") != "both_teams":
                continue
            # Only the simple BTTS yes/no market (not combined markets)
            name = (mkt.get("name") or "").lower()
            if any(x in name for x in ["corner", "assist", "first half", "2nd", "score no draw",
                                        "combo", "moneyline", "/", "&", "both halves"]):
                continue
            outcomes = mkt.get("outcomes", [])
            # Look for exactly 2 outcomes: yes/no or true/false type
            if len(outcomes) != 2:
                continue
            for outcome in outcomes:
                otype = (outcome.get("type") or "").lower()
                dec = outcome.get("decimal_odds")
                if dec and dec > 1.0:
                    if otype in ("yes", "true", "btts", "both_teams"):
                        btts_yes_decimals.append(float(dec))
                    elif otype in ("no", "false"):
                        btts_no_decimals.append(float(dec))

    if btts_yes_decimals and btts_no_decimals:
        import statistics
        avg_yes = statistics.mean(btts_yes_decimals)
        avg_no  = statistics.mean(btts_no_decimals)
        # Normalize (strip vig via simple proportional)
        raw_y, raw_n = 1 / avg_yes, 1 / avg_no
        total = raw_y + raw_n
        result["btts_yes"] = round(raw_y / total, 6)
        result["btts_no"]  = round(raw_n / total, 6)
        log.info("  BTTS closing: yes=%.3f no=%.3f  (%d/%d vendors)",
                 result["btts_yes"], result["btts_no"],
                 len(btts_yes_decimals), len(btts_no_decimals))

    return result


# ── CLV store update ─────────────────────────────────────────────────────────

def _record_closing_odds(match_id: str, closing_probs: dict[str, float],
                         timestamp: str) -> int:
    """
    Load CLV store, call set_closing() on every matching record,
    rewrite the file. Returns number of records updated.
    """
    if not CLV_PATH.exists():
        log.warning("CLV store not found: %s", CLV_PATH)
        return 0

    from wc2026.markets.clv import CLVStore

    store = CLVStore(str(CLV_PATH))
    records = store.load_all()
    updated = 0

    for rec in records:
        if str(rec.match_id) != str(match_id):
            continue
        mkt = rec.market
        if mkt not in closing_probs:
            continue
        closing_p = closing_probs[mkt]
        if closing_p <= 0:
            continue
        # closing_odds_decimal = 1 / closing_prob (fair no-vig decimal)
        closing_dec = round(1.0 / closing_p, 4)
        rec.set_closing(closing_dec, timestamp)
        updated += 1

    if updated > 0:
        with open(CLV_PATH, "w") as f:
            for r in records:
                f.write(json.dumps(r.to_dict()) + "\n")

    return updated


# ── main ─────────────────────────────────────────────────────────────────────

def main() -> None:
    now = datetime.now(tz=timezone.utc)
    window_end = now + timedelta(minutes=LOOKAHEAD_MIN)

    log.info("closing_odds_snapshot — scan window: %s → %s UTC",
             now.strftime("%H:%M"), window_end.strftime("%H:%M"))

    # #region agent log
    _dbg("script started", {"now_utc": now.isoformat(), "lookahead_min": LOOKAHEAD_MIN}, "A", "pre1")
    # #endregion

    matches = _load_scheduled_matches()
    log.info("Found %d total scheduled matches", len(matches))

    # Filter to matches kicking off within our lookahead window
    imminent = [
        m for m in matches
        if now <= m["kickoff_utc"] <= window_end
    ]

    # #region agent log
    _dbg("imminent matches found", {"count": len(imminent),
         "matches": [f"{m['home_team']} vs {m['away_team']} @ {m['kickoff_utc'].isoformat()}"
                     for m in imminent]}, "B", "pre1")
    # #endregion

    if not imminent:
        log.info("No matches kicking off in the next %d minutes — nothing to do", LOOKAHEAD_MIN)
        return

    api_key = os.environ.get("BDL_API_KEY", "")
    if not api_key:
        log.warning("BDL_API_KEY not set — cannot fetch closing odds")
        # #region agent log
        _dbg("no api key", {"bdl_key_present": False}, "C", "pre1")
        # #endregion
        return

    from wc2026.data.providers.bdl import BDLProvider
    provider = BDLProvider(snapshot=False)

    captured = 0
    for m in imminent:
        ko = m["kickoff_utc"]
        capture_at = ko - timedelta(minutes=CLOSING_BEFORE_MIN)
        sleep_secs = (capture_at - datetime.now(tz=timezone.utc)).total_seconds()

        if sleep_secs > 0:
            log.info(
                "Next match: %s vs %s @ %s UTC — sleeping %.0fs until T-%dmin",
                m["home_team"], m["away_team"], ko.strftime("%H:%M"),
                sleep_secs, CLOSING_BEFORE_MIN,
            )
            # #region agent log
            _dbg("sleeping until T-3", {"match": f"{m['home_team']} vs {m['away_team']}",
                 "sleep_secs": round(sleep_secs), "capture_at": capture_at.isoformat()}, "D", "pre1")
            # #endregion
            time.sleep(sleep_secs)

        ts = datetime.now(tz=timezone.utc).isoformat()
        log.info("Fetching closing odds for match_id=%s (%s vs %s)...",
                 m["match_id"], m["home_team"], m["away_team"])

        try:
            odds_rows = provider.fetch_odds([int(m["match_id"])])
        except Exception as exc:
            log.error("BDL odds fetch failed for match_id=%s: %s", m["match_id"], exc)
            # #region agent log
            _dbg("odds fetch failed", {"match_id": m["match_id"], "error": str(exc)}, "C", "pre1")
            # #endregion
            continue

        # #region agent log
        _dbg("odds fetched", {"match_id": m["match_id"], "n_vendors": len(odds_rows)}, "C", "pre1")
        # #endregion

        if not odds_rows:
            log.warning("No odds returned for match_id=%s — skipping", m["match_id"])
            continue

        closing_probs = _parse_closing_probs(odds_rows)

        # #region agent log
        _dbg("closing probs computed", {"match_id": m["match_id"],
             "markets": {k: round(v, 3) for k, v in closing_probs.items()}}, "D", "pre1")
        # #endregion

        if not closing_probs:
            log.warning("Could not parse any closing probabilities — skipping match_id=%s",
                        m["match_id"])
            continue

        n = _record_closing_odds(m["match_id"], closing_probs, ts)
        log.info(
            "Closing odds recorded for %s vs %s: %d CLV records updated",
            m["home_team"], m["away_team"], n,
        )
        # #region agent log
        _dbg("clv records updated", {"match_id": m["match_id"],
             "home": m["home_team"], "away": m["away_team"],
             "n_updated": n, "markets": list(closing_probs.keys())}, "D", "pre1")
        # #endregion
        captured += 1

    log.info("closing_odds_snapshot done — captured closing odds for %d match(es)", captured)

    # Write sentinel so the workflow knows whether any data changed
    sentinel = DATA_DIR / "live" / "pre_match_status.json"
    sentinel.parent.mkdir(parents=True, exist_ok=True)
    sentinel.write_text(json.dumps({
        "captured": captured,
        "generated_at": datetime.now(tz=timezone.utc).isoformat(),
        "matches": [f"{m['home_team']} vs {m['away_team']}" for m in imminent],
    }))


if __name__ == "__main__":
    main()
