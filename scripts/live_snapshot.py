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
LIVE_FILE = "wc-live.json"


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
        doc = json.loads(pub_path.read_text())
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


def _fetch_live_matches() -> tuple[list[dict], list[dict]]:
    """Fetch all 2026 WC matches from BDL and return live ones."""
    from wc2026.data.providers.bdl import BDLProvider
    provider = BDLProvider(snapshot=False)
    log.info("Fetching 2026 WC matches from BDL…")
    try:
        all_matches = provider.fetch_matches(seasons=[2026])
    except Exception as exc:
        log.error("BDL fetch failed: %s", exc)
        log.error("BDL fetch failed: %s", exc)
        return []

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
                ko_dt = datetime.fromisoformat(str(ko_str).replace("Z", "+00:00"))
                mins_since_ko = (now_utc - ko_dt).total_seconds() / 60.0
            except Exception:
                mins_since_ko = -999.0
            if mins_since_ko >= 3.0:
                # Kickoff passed ≥3 min ago and BDL still says scheduled → treat as live
                home_name = (m.get("home_team") or {}).get("name") or "?"
                away_name = (m.get("away_team") or {}).get("name") or "?"
                log.warning(
                    "BDL lag detected: '%s' still 'scheduled' %.1f min after kickoff — "
                    "treating as live (0-0 min=0): %s vs %s",
                    m.get("id"), mins_since_ko, home_name, away_name,
                )
                live.append(m)
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

    log.info("BDL: %d total, %d live, %d upcoming, %d finished",
             len(all_matches), len(live), len(upcoming), len(finished))
    return live, upcoming


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
        # 3B — Shin devigging
        odds = [float(live_hw_odds), float(live_dr_odds), float(live_aw_odds)]
        # Guard against invalid odds (<= 1.0)
        if any(o <= 1.0 for o in odds):
            raise ValueError(f"Invalid odds: {odds}")
        implied = pb.implied.calculate_implied(odds, method=ImpliedMethod.SHIN)
        market_margin = float(implied.margin)
        shin_z = implied.method_params.get("z") if implied.method_params else None

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
        live_matches, upcoming = _fetch_live_matches()
    except Exception as exc:
        log.error("Failed to fetch matches: %s", exc)
        live_matches, upcoming = [], []

    # Fetch live team stats + shots for all live matches in one batch call each
    live_ids = [m.get("id") for m in live_matches if m.get("id")]
    live_team_stats: dict[str, list] = {}   # match_id → [team_match_stats rows]
    live_shots: dict[str, list] = {}        # match_id → [match_shots rows]
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
            log.info("Live stats fetched: %d team-stat rows, %d shot rows for %d matches",
                     len(stats_rows), len(shots_rows), len(live_ids))
        except Exception as exc:
            log.warning("Could not fetch live team stats/shots: %s", exc)

    results = []
    for bdl_m in live_matches:
        mid = str(bdl_m.get("id", ""))
        home = (bdl_m.get("home_team") or {}).get("name") or (bdl_m.get("home_team") or {}).get("full_name", "Home")
        away = (bdl_m.get("away_team") or {}).get("name") or (bdl_m.get("away_team") or {}).get("full_name", "Away")

        # Look up pregame lambdas
        lh, la = pregame_lambdas.get(mid, pregame_lambdas.get(f"{home}|{away}", (1.35, 1.00)))
        bdl_stats = live_team_stats.get(mid) or None
        bdl_shots = live_shots.get(mid) or None

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

        log.info("Processing live match: %s vs %s  status=%s clock=%s score=%s-%s lambda_src=%s stats=%s",
                 home, away, bdl_m.get("status"), bdl_m.get("clock_display"),
                 bdl_m.get("home_score"), bdl_m.get("away_score"),
                 "published" if mid in pregame_lambdas else "fallback",
                 "yes" if bdl_stats else "none")

        try:
            result = predictor.predict_from_bdl(bdl_m, pregame_lh=lh, pregame_la=la,
                                                bdl_stats=bdl_stats, bdl_shots=bdl_shots)
            if result:
                d = result.to_dict()
                d["pregame_lh"] = lh
                d["pregame_la"] = la
                d["bdl_status"] = bdl_m.get("status")

                # 3B–3E — Compute live betting edge with Shin devigging
                live_edge = _compute_live_edge(
                    result, _live_hw_odds, _live_dr_odds, _live_aw_odds,
                    _pregame_fallback, home, away,
                )
                d["live_edge"] = live_edge

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
            ko_dt = datetime.fromisoformat(str(ko_str).replace("+00:00", "")).replace(tzinfo=timezone.utc)
            ko_et = ko_dt.astimezone(
                __import__("zoneinfo", fromlist=["ZoneInfo"]).ZoneInfo("America/New_York")
            )
            ko_et_str = ko_et.strftime("%-I:%M %p ET")
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

    snapshot = {
        "generated_at": now_utc.isoformat(),
        "date": today_et,
        "status": "live" if results else ("quiet" if not live_matches else "error"),
        "n_live": len(results),
        "live_matches": results,
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
        for remote_dir in [FTP_DIR_SPACE, FTP_DIR_HYPHEN]:
            _ensure_remote_dir_and_chmod(ftp, remote_dir)
            ftp.cwd(remote_dir)
            ftp.storbinary(f"STOR {LIVE_FILE}", io.BytesIO(payload))
            try:
                ftp.sendcmd(f"SITE CHMOD 775 {remote_dir}/{LIVE_FILE}")
            except Exception:
                pass
        log.info("✓ Uploaded wc-live.json to both paths")

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
            for remote_dir in [FTP_DIR_SPACE, FTP_DIR_HYPHEN,
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
        log.info("Snapshot: status=%s, %d live matches", snapshot["status"], snapshot["n_live"])
        upload_snapshot(snapshot)
        # Write to local data/live/ for the FastAPI server to serve
        live_dir = REPO_ROOT / "data" / "live"
        live_dir.mkdir(parents=True, exist_ok=True)
        (live_dir / "latest.json").write_text(json.dumps(snapshot, indent=2))
        # Push to live server for instant WebSocket broadcast
        push_to_live_server(snapshot)
        write_health_status(True, f"Live snapshot OK — {snapshot['n_live']} live matches",
                            {"n_live": snapshot["n_live"], "snapshot_status": snapshot["status"]})
    except Exception as exc:
        log.error("Snapshot failed: %s", exc)
        write_health_status(False, f"Live snapshot failed: {exc}")
        sys.exit(1)
    log.info("Done in %.1fs", time.time() - t0)


if __name__ == "__main__":
    main()
