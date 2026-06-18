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
    python scripts/closing_odds_snapshot.py               # normal mode
    python scripts/closing_odds_snapshot.py --fallback-window 15
        Fallback mode: instead of waiting for future kickoffs, scan for
        matches that kicked off within the last N minutes and try to
        capture their closing odds from BDL (which often still has
        pre-game lines available briefly after kickoff).  Skips any
        match whose closing line is already recorded.
    python scripts/closing_odds_snapshot.py --backfill
        Backfill mode: find all CLV records where outcome is set but
        closing_prob is None, attempt historical BDL odds lookup, and
        store results.  Records with no available data are marked with
        closing_missing=true so we know they were attempted.
    make pre-match-snapshot
"""
from __future__ import annotations

import argparse
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

LOOKAHEAD_MIN = 25      # scan: matches kicking off within this window
                        # Must be > live.yml's T-20 dispatch threshold so pre-match.yml
                        # dispatched at T-20 still finds the match in the lookahead window.
CLOSING_BEFORE_MIN = 3  # capture odds this many minutes before kickoff
LOOKBACK_MIN = 10       # also capture if match kicked off within last N min (handles late triggers)
DATA_DIR = REPO_ROOT / "data"
CLV_PATH = DATA_DIR / "clv" / "2026" / "records.jsonl"


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
                if m.get("status") not in ("scheduled", "in_progress"):
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

_SUPPRESS_EDGE_MARKETS = {"over_5_5", "over_6_5"}


def _record_closing_odds(match_id: str, closing_probs: dict[str, float],
                         timestamp: str, source: str = "live_capture") -> int:
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
        rec.set_closing(closing_dec, timestamp, source=source)
        # Ensure suppression flag is set for tail markets
        if mkt in _SUPPRESS_EDGE_MARKETS:
            rec.suppress_from_edge = True
        updated += 1

    if updated > 0:
        with open(CLV_PATH, "w") as f:
            for r in records:
                f.write(json.dumps(r.to_dict()) + "\n")

    return updated


# ── main helpers ─────────────────────────────────────────────────────────────

def _fetch_and_record(provider, match_id: str, home_team: str, away_team: str,
                      ts: str, closing_source: str = "live_capture") -> int:
    """Fetch BDL odds for one match and write closing lines into CLV store.

    Returns the number of CLV records updated (0 if fetch failed or no data).
    """
    try:
        odds_rows = provider.fetch_odds([int(match_id)])
    except Exception as exc:
        log.error("BDL odds fetch failed for match_id=%s: %s", match_id, exc)
        return 0

    if not odds_rows:
        log.warning("No odds returned for match_id=%s — skipping", match_id)
        return 0

    closing_probs = _parse_closing_probs(odds_rows)
    if not closing_probs:
        log.warning("Could not parse any closing probabilities — skipping match_id=%s",
                    match_id)
        return 0

    n = _record_closing_odds(match_id, closing_probs, ts, source=closing_source)
    log.info("Closing odds recorded for %s vs %s: %d CLV records updated",
             home_team, away_team, n)
    return n


def _mark_closing_missing(match_id: str, reason: str) -> int:
    """Mark all CLV records for a match as closing_missing so we know it was attempted."""
    if not CLV_PATH.exists():
        return 0

    updated = 0
    lines_out: list[str] = []
    with open(CLV_PATH) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                d = json.loads(line)
                if str(d.get("match_id")) == str(match_id) and d.get("closing_prob") is None:
                    d["closing_missing"] = True
                    d["closing_missing_reason"] = reason
                    updated += 1
                lines_out.append(json.dumps(d))
            except Exception:
                lines_out.append(line)

    with open(CLV_PATH, "w") as f:
        for l in lines_out:
            f.write(l + "\n")
    return updated


# ── main ─────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Capture closing odds for CLV tracking")
    parser.add_argument(
        "--fallback-window", type=int, default=0, metavar="N",
        help="Fallback mode: scan for matches that kicked off within the last N minutes "
             "and capture their closing odds. Skips matches already captured.",
    )
    parser.add_argument(
        "--backfill", action="store_true",
        help="Backfill mode: for all CLV records with outcome but no closing_prob, "
             "attempt historical BDL odds lookup.",
    )
    parser.add_argument(
        "--audit", action="store_true",
        help="Audit mode: find all completed CLV records with outcome but no closing_prob "
             "and outcome_timestamp within the last 72 hours, attempt BDL odds fetch, "
             "and store results with closing_source='audit_backfill'.",
    )
    args = parser.parse_args()

    api_key = os.environ.get("BDL_API_KEY", "")
    if not api_key:
        log.warning("BDL_API_KEY not set — cannot fetch closing odds")
        return

    from wc2026.data.providers.bdl import BDLProvider
    provider = BDLProvider(snapshot=False)

    if args.audit:
        _run_audit(provider)
        return

    if args.backfill:
        _run_backfill(provider)
        return

    if args.fallback_window > 0:
        _run_fallback(provider, args.fallback_window)
        return

    _run_normal(provider)


def _run_normal(provider) -> None:
    """Normal mode: find imminent matches (future or just-kicked-off), sleep until T-3, capture."""
    now = datetime.now(tz=timezone.utc)
    window_end = now + timedelta(minutes=LOOKAHEAD_MIN)

    log.info("closing_odds_snapshot (normal) — scan window: %s → %s UTC",
             now.strftime("%H:%M"), window_end.strftime("%H:%M"))

    matches = _load_scheduled_matches()

    lookback_start = now - timedelta(minutes=LOOKBACK_MIN)
    imminent = [
        m for m in matches
        if lookback_start <= m["kickoff_utc"] <= window_end
    ]

    log.info("SCAN: checking %d scheduled matches, lookahead=%d min", len(matches), LOOKAHEAD_MIN)

    # #region agent log — H-A: closing odds scan result
    try:
        import json as _j
        open("/Users/josephshackelford/worldcup2026-model/.cursor/debug-3f8dcc.log", "a").write(_j.dumps({"sessionId": "3f8dcc", "hypothesisId": "H-A", "location": "closing_odds_snapshot.py:scan", "message": "scan result", "data": {"n_matches_total": len(matches), "n_imminent": len(imminent), "lookahead_min": LOOKAHEAD_MIN, "imminent_matches": [{"home": m["home_team"], "away": m["away_team"], "ko_utc": m["kickoff_utc"].isoformat(), "min_to_ko": round((m["kickoff_utc"] - now).total_seconds()/60, 1)} for m in imminent], "now_utc": now.isoformat()}, "timestamp": int(time.time() * 1000)}) + "\n")
    except Exception:
        pass
    # #endregion

    if not imminent:
        minutes_to_next = None
        future = sorted(
            (m for m in matches if m["kickoff_utc"] > now),
            key=lambda x: x["kickoff_utc"],
        )
        if future:
            minutes_to_next = int((future[0]["kickoff_utc"] - now).total_seconds() / 60)
            log.info("NO MATCH IMMINENT: next kickoff in %d min", minutes_to_next)
        else:
            log.info("NO MATCH IMMINENT: no future scheduled matches found")
        _write_sentinel(0, imminent)
        return

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
            time.sleep(sleep_secs)
        else:
            log.info(
                "Match %s vs %s already past T-%dmin (%.0fs ago) — capturing immediately",
                m["home_team"], m["away_team"], CLOSING_BEFORE_MIN, abs(sleep_secs),
            )

        ts = datetime.now(tz=timezone.utc).isoformat()
        log.info("Fetching closing odds for match_id=%s (%s vs %s)...",
                 m["match_id"], m["home_team"], m["away_team"])

        # Check if already captured (could have been done by a concurrent run)
        if CLV_PATH.exists():
            from wc2026.markets.clv import CLVStore as _CLVStore
            _existing_recs = _CLVStore(str(CLV_PATH)).load_all()
            _existing_source = next(
                (r.closing_source for r in _existing_recs
                 if str(r.match_id) == str(m["match_id"]) and r.closing_prob is not None),
                None,
            )
            if _existing_source is not None:
                log.info(
                    "SKIP already captured: match_id=%s source=%s",
                    m["match_id"], _existing_source,
                )
                captured += 1
                continue

        try:
            n_updated = _fetch_and_record(
                provider, m["match_id"], m["home_team"], m["away_team"], ts
            )
            if n_updated > 0:
                log.info(
                    "CAPTURE: match_id=%s %s vs %s — %d markets fetched",
                    m["match_id"], m["home_team"], m["away_team"], n_updated,
                )
                captured += 1
        except Exception as exc:
            log.error("Unexpected error for match_id=%s: %s", m["match_id"], exc)

    log.info("closing_odds_snapshot done — captured closing odds for %d match(es)", captured)

    # #region agent log — H-A: capture result
    try:
        import json as _j
        open("/Users/josephshackelford/worldcup2026-model/.cursor/debug-3f8dcc.log", "a").write(_j.dumps({"sessionId": "3f8dcc", "hypothesisId": "H-A", "location": "closing_odds_snapshot.py:done", "message": "capture complete", "data": {"captured": captured, "n_imminent": len(imminent)}, "timestamp": int(time.time() * 1000)}) + "\n")
    except Exception:
        pass
    # #endregion

    _write_sentinel(captured, imminent)


def _run_fallback(provider, window_minutes: int) -> None:
    """Fallback mode: capture closing odds for matches that kicked off recently."""
    now = datetime.now(tz=timezone.utc)
    lookback_start = now - timedelta(minutes=window_minutes)

    log.info(
        "closing_odds_snapshot (fallback, window=%dmin) — looking for matches "
        "that kicked off between %s and %s UTC",
        window_minutes, lookback_start.strftime("%H:%M"), now.strftime("%H:%M"),
    )

    # We need to load ALL matches (including recently completed) for this scan.
    # _load_scheduled_matches only returns status=scheduled/in_progress, so we
    # build a broader list from published files.
    import dateutil.parser

    pub_dir = DATA_DIR / "published"
    all_matches: list[dict] = []
    for f in sorted(pub_dir.glob("2026-*.json")):
        try:
            data = json.loads(f.read_text())
            for m in data.get("matches", []):
                ko_raw = m.get("match_datetime_utc") or m.get("datetime")
                if not ko_raw:
                    continue
                try:
                    ko = dateutil.parser.parse(str(ko_raw))
                    if ko.tzinfo is None:
                        ko = ko.replace(tzinfo=timezone.utc)
                except Exception:
                    continue
                all_matches.append({
                    "match_id": str(m["match_id"]),
                    "home_team": m.get("home_team", "?"),
                    "away_team": m.get("away_team", "?"),
                    "kickoff_utc": ko,
                })
        except Exception as exc:
            log.warning("Could not read %s: %s", f.name, exc)

    # Find matches that kicked off in the fallback window
    recent = [m for m in all_matches if lookback_start <= m["kickoff_utc"] <= now]
    if not recent:
        log.info("No matches kicked off in the last %d minutes — nothing to do", window_minutes)
        return

    # Load CLV store to check which already have closing lines
    already_captured: set[str] = set()
    if CLV_PATH.exists():
        from wc2026.markets.clv import CLVStore
        store = CLVStore(str(CLV_PATH))
        for rec in store.load_all():
            if rec.closing_prob is not None:
                already_captured.add(str(rec.match_id))

    captured = 0
    for m in recent:
        if m["match_id"] in already_captured:
            log.info("match_id=%s (%s vs %s) already has closing odds — skipping",
                     m["match_id"], m["home_team"], m["away_team"])
            continue

        log.info("Fallback capture for match_id=%s (%s vs %s, kicked off %s UTC)",
                 m["match_id"], m["home_team"], m["away_team"],
                 m["kickoff_utc"].strftime("%H:%M"))
        ts = datetime.now(tz=timezone.utc).isoformat()
        try:
            n_updated = _fetch_and_record(provider, m["match_id"], m["home_team"], m["away_team"], ts)
            if n_updated > 0:
                captured += 1
        except Exception as exc:
            log.error("Fallback error for match_id=%s: %s", m["match_id"], exc)

    log.info("Fallback done — captured closing odds for %d match(es)", captured)


def _run_backfill(provider) -> None:
    """Backfill mode: attempt historical BDL odds for matches with outcome but no closing_prob."""
    if not CLV_PATH.exists():
        log.warning("CLV store not found: %s", CLV_PATH)
        return

    from wc2026.markets.clv import CLVStore
    store = CLVStore(str(CLV_PATH))
    records = store.load_all()

    # Find unique match_ids where ANY record has outcome set but no closing_prob
    needs_backfill: dict[str, dict] = {}
    for rec in records:
        mid = str(rec.match_id)
        if rec.outcome is not None and rec.closing_prob is None:
            if mid not in needs_backfill:
                needs_backfill[mid] = {
                    "home_team": rec.home_team,
                    "away_team": rec.away_team,
                }

    # Exclude matches that have already been attempted (via closing_missing=true flag
    # set by _mark_closing_missing, or via closing_source="backfill_invalid" set by
    # set_closing's guard when BDL returned post-match prices).
    # Both conditions mean "we tried and it didn't produce valid closing odds".
    already_attempted: set[str] = set()
    with open(CLV_PATH) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                d = json.loads(line)
                mid = str(d.get("match_id", ""))
                if not mid:
                    continue
                # closing_missing=True  → BDL had no odds data at all
                # backfill_invalid      → BDL had odds but they were post-match (guard rejected)
                if (d.get("closing_missing") or d.get("closing_source") == "backfill_invalid"):
                    already_attempted.add(mid)
            except Exception:
                pass

    # Remove matches where any record was already attempted (avoid redundant API calls
    # and repeated "backfill_invalid" churn).
    for mid in list(needs_backfill.keys()):
        if mid in already_attempted:
            log.debug("Backfill: skipping match_id=%s (already attempted)", mid)
            del needs_backfill[mid]

    if not needs_backfill:
        log.info("Backfill: no matches need closing odds — already complete")
        return

    log.info("Backfill: found %d match(es) with outcome but no closing odds: %s",
             len(needs_backfill),
             [f"{mid}={v['home_team']} vs {v['away_team']}" for mid, v in needs_backfill.items()])

    n_backfilled = 0
    n_missing = 0

    for mid, info in sorted(needs_backfill.items(), key=lambda x: int(x[0]) if x[0].isdigit() else 0):
        home, away = info["home_team"], info["away_team"]
        log.info("Backfill: fetching historical odds for match_id=%s (%s vs %s)...",
                 mid, home, away)

        ts = datetime.now(tz=timezone.utc).isoformat()
        try:
            n_updated = _fetch_and_record(provider, mid, home, away, ts)
            if n_updated > 0:
                n_backfilled += 1
                log.info("Backfill: ✓ match_id=%s closing odds captured", mid)
            else:
                n_missing += 1
                n_marked = _mark_closing_missing(
                    mid, "BDL returned no odds during backfill attempt"
                )
                log.info("Backfill: ✗ match_id=%s — no odds available, marked %d records "
                         "as closing_missing", mid, n_marked)
        except Exception as exc:
            n_missing += 1
            n_marked = _mark_closing_missing(mid, f"backfill fetch error: {exc}")
            log.error("Backfill: error for match_id=%s: %s — marked %d records as closing_missing",
                      mid, exc, n_marked)

    log.info(
        "Backfill complete — %d match(es) backfilled, %d marked as missing",
        n_backfilled, n_missing,
    )


def _run_audit(provider) -> None:
    """Audit mode: recover recent missing closing odds for completed matches.

    Scans CLV records that have an outcome but no closing_prob, filters to those
    whose outcome_timestamp is within the last 72 hours, then attempts a BDL
    odds fetch for each.  Records recovered are marked closing_source='audit_backfill'.
    """
    if not CLV_PATH.exists():
        log.warning("Audit: CLV store not found: %s", CLV_PATH)
        return

    from wc2026.markets.clv import CLVStore

    store = CLVStore(str(CLV_PATH))
    records = store.load_all()

    now = datetime.now(tz=timezone.utc)
    cutoff = now - timedelta(hours=72)

    # Find unique match_ids: completed (outcome set), no closing_prob, recent outcome
    candidates: dict[str, dict] = {}
    for rec in records:
        mid = str(rec.match_id)
        if rec.outcome is None or rec.closing_prob is not None:
            continue
        # Check outcome_timestamp within 72 h
        if rec.outcome_timestamp:
            try:
                ots_str = rec.outcome_timestamp
                if ots_str.endswith("Z"):
                    ots_str = ots_str[:-1] + "+00:00"
                ots = datetime.fromisoformat(ots_str)
                if ots.tzinfo is None:
                    ots = ots.replace(tzinfo=timezone.utc)
                if ots < cutoff:
                    continue
            except Exception:
                continue
        if mid not in candidates:
            candidates[mid] = {
                "home_team": rec.home_team,
                "away_team": rec.away_team,
            }

    n_attempted = len(candidates)
    log.info("Audit: found %d match(es) with completed outcome but no closing odds (within 72h)",
             n_attempted)

    if n_attempted == 0:
        print("Audit summary: 0 matches attempted, 0 recovered")
        return

    n_recovered = 0
    for mid, info in sorted(candidates.items()):
        home, away = info["home_team"], info["away_team"]
        log.info("Audit: fetching odds for match_id=%s (%s vs %s)...", mid, home, away)
        ts = now.isoformat()
        try:
            n_updated = _fetch_and_record(
                provider, mid, home, away, ts, closing_source="audit_backfill"
            )
            if n_updated > 0:
                n_recovered += 1
                log.info("Audit: ✓ match_id=%s — %d records updated", mid, n_updated)
            else:
                log.info("Audit: ✗ match_id=%s — no odds available", mid)
        except Exception as exc:
            log.error("Audit: error for match_id=%s: %s", mid, exc)

    summary = (
        f"Audit summary: {n_attempted} match(es) attempted, "
        f"{n_recovered} successfully recovered"
    )
    log.info(summary)
    print(summary)


def _write_sentinel(captured: int, imminent: list[dict]) -> None:
    sentinel = DATA_DIR / "live" / "pre_match_status.json"
    sentinel.parent.mkdir(parents=True, exist_ok=True)
    sentinel.write_text(json.dumps({
        "captured": captured,
        "generated_at": datetime.now(tz=timezone.utc).isoformat(),
        "matches": [f"{m['home_team']} vs {m['away_team']}" for m in imminent],
    }))


if __name__ == "__main__":
    main()
