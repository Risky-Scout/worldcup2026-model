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

LOG_PATH = REPO_ROOT / ".cursor" / "debug-3f8dcc.log"

def _dbg(msg: str, data: dict, hypothesis: str = "", run_id: str = "live-run-1"):
    """Append a debug NDJSON line to the session log file."""
    import json as _j, time as _t
    rec = {
        "sessionId": "3f8dcc",
        "id": f"log_{int(_t.time()*1000)}",
        "timestamp": int(_t.time()*1000),
        "location": "live_snapshot.py",
        "message": msg,
        "data": data,
        "runId": run_id,
        "hypothesisId": hypothesis,
    }
    try:
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(LOG_PATH, "a") as f:
            f.write(_j.dumps(rec) + "\n")
    except Exception:
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


def _load_pregame_lambdas(date: str) -> dict[str, tuple[float, float]]:
    """
    Load pregame expected goals (lh, la) from today's published JSON.
    Returns dict keyed by match_id → (lh, la).
    Also returns keyed by (home_team, away_team) as fallback.
    """
    pub_path = REPO_ROOT / "data" / "published" / f"{date}.json"
    if not pub_path.exists():
        _dbg("pregame JSON not found", {"date": date, "path": str(pub_path)}, "H-C")
        return {}
    doc = json.loads(pub_path.read_text())
    result = {}
    for m in doc.get("matches", []):
        pred = m.get("prediction", {})
        lh = pred.get("expected_home_goals", 1.35)
        la = pred.get("expected_away_goals", 1.00)
        # Index by match_id, home_team, and (home, away) pair
        mid = str(m.get("match_id", ""))
        home = m.get("home_team", "")
        away = m.get("away_team", "")
        er = pred.get("edge_report", {})
        pregame_lh = er.get("pregame_lh", lh)
        pregame_la = er.get("pregame_la", la)
        if mid:
            result[mid] = (pregame_lh, pregame_la)
        result[f"{home}|{away}"] = (pregame_lh, pregame_la)
    _dbg("pregame lambdas loaded", {"date": date, "n_matches": len(doc.get("matches",[]))}, "H-C")
    return result


def _fetch_live_matches() -> tuple[list[dict], list[dict]]:
    """Fetch all 2026 WC matches from BDL and return live ones."""
    from wc2026.data.providers.bdl import BDLProvider
    provider = BDLProvider(snapshot=False)
    log.info("Fetching 2026 WC matches from BDL…")
    try:
        all_matches = provider.fetch_matches(seasons=[2026])
    except Exception as exc:
        log.error("BDL fetch failed: %s", exc)
        _dbg("BDL fetch failed", {"error": str(exc)}, "H-A")
        return []

    _dbg("BDL fetch complete", {
        "total_matches": len(all_matches),
        "sample_fields": list(all_matches[0].keys()) if all_matches else [],
        "sample_status": all_matches[0].get("status") if all_matches else None,
        "sample_score": f"{all_matches[0].get('home_score')}-{all_matches[0].get('away_score')}" if all_matches else None,
    }, "H-A")

    live, upcoming, finished = [], [], []
    for m in all_matches:
        raw_status = str(m.get("status", "") or "").lower().strip()
        clock_seconds = int(m.get("clock_seconds", 0) or 0)

        if raw_status in LIVE_STATUS_CODES:
            live.append(m)
        elif raw_status in COMPLETED_STATUS_CODES:
            finished.append(m)
        elif raw_status in PREGAME_STATUS_CODES:
            upcoming.append(m)
        elif clock_seconds > 60:
            # Clock is running but status string is unrecognized → treat as live
            _dbg("unknown status with clock > 60s — treating as live", {
                "status": raw_status, "clock_seconds": clock_seconds,
                "match": f"{m.get('home_team', {}).get('full_name','')} vs {m.get('away_team', {}).get('full_name','')}",
            }, "H-B")
            live.append(m)
        else:
            _dbg("unclassified match status", {
                "status": raw_status, "clock_seconds": clock_seconds,
            }, "H-B")
            upcoming.append(m)

    _dbg("match status distribution", {
        "live": len(live),
        "upcoming": len(upcoming),
        "finished": len(finished),
        "unknown": len(all_matches) - len(live) - len(upcoming) - len(finished),
        "unique_statuses": list({str(m.get("status","")).lower() for m in all_matches}),
    }, "H-B")

    log.info("BDL: %d total, %d live, %d upcoming, %d finished",
             len(all_matches), len(live), len(upcoming), len(finished))
    return live, upcoming


def run_live_snapshot() -> dict:
    """Main: fetch live matches, run PMF engine, return snapshot dict."""
    from wc2026.live.predictor import LivePMFPredictor
    from wc2026.live.state import MatchStatus

    now_utc = datetime.now(tz=timezone.utc)
    today_et = now_utc.astimezone(
        __import__("zoneinfo", fromlist=["ZoneInfo"]).ZoneInfo("America/New_York")
    ).date().isoformat()

    predictor = LivePMFPredictor(max_delta=7, max_goals=10)
    pregame_lambdas = _load_pregame_lambdas(today_et)

    try:
        live_matches, upcoming = _fetch_live_matches()
    except Exception as exc:
        log.error("Failed to fetch matches: %s", exc)
        live_matches, upcoming = [], []

    results = []
    for bdl_m in live_matches:
        mid = str(bdl_m.get("id", ""))
        home = (bdl_m.get("home_team") or {}).get("full_name", "Home")
        away = (bdl_m.get("away_team") or {}).get("full_name", "Away")

        # Look up pregame lambdas
        lh, la = pregame_lambdas.get(mid, pregame_lambdas.get(f"{home}|{away}", (1.35, 1.00)))

        _dbg("processing live match", {
            "match_id": mid, "home": home, "away": away,
            "status": bdl_m.get("status"),
            "clock": bdl_m.get("clock_display"),
            "score": f"{bdl_m.get('home_score')}-{bdl_m.get('away_score')}",
            "pregame_lh": lh, "pregame_la": la,
            "lambda_source": "published" if mid in pregame_lambdas else "fallback",
        }, "H-C")

        try:
            result = predictor.predict_from_bdl(bdl_m, pregame_lh=lh, pregame_la=la)
            if result:
                d = result.to_dict()
                d["pregame_lh"] = lh
                d["pregame_la"] = la
                d["bdl_status"] = bdl_m.get("status")
                results.append(d)
                _dbg("live PMF computed", {
                    "match": f"{home} vs {away}",
                    "minute": result.regulation_minute,
                    "score": result.current_score if hasattr(result, 'current_score') else f"{result.current_home_goals}-{result.current_away_goals}",
                    "hw": result.home_win_prob, "dr": result.draw_prob, "aw": result.away_win_prob,
                }, "H-A")
        except Exception as exc:
            log.warning("LivePMF failed for %s vs %s: %s", home, away, exc)
            _dbg("live PMF failed", {"match": f"{home} vs {away}", "error": str(exc)}, "H-A")

    # Build upcoming section (pre-game matches today)
    upcoming_today = []
    for m in upcoming[:10]:
        ko_str = m.get("date_time_utc", "")
        try:
            ko_dt = datetime.fromisoformat(str(ko_str).replace("+00:00", "")).replace(tzinfo=timezone.utc)
            ko_et = ko_dt.astimezone(
                __import__("zoneinfo", fromlist=["ZoneInfo"]).ZoneInfo("America/New_York")
            )
            ko_et_str = ko_et.strftime("%-I:%M %p ET")
        except Exception:
            ko_et_str = str(ko_str)
        home = (m.get("home_team") or {}).get("full_name", "")
        away = (m.get("away_team") or {}).get("full_name", "")
        upcoming_today.append({
            "match_id": str(m.get("id", "")),
            "home_team": home,
            "away_team": away,
            "kickoff_et": ko_et_str,
            "kickoff_utc": ko_str,
            "status": m.get("status", ""),
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

    _dbg("FTP upload complete", {
        "bytes": len(payload),
        "n_live": snapshot.get("n_live", 0),
        "status": snapshot.get("status"),
    }, "H-D")


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


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--health-only", action="store_true",
                        help="Only write a health-OK status file, skip live snapshot")
    args = parser.parse_args()

    log.info("=== WC2026 Live Snapshot ===")
    t0 = time.time()

    if args.health_only:
        write_health_status(True, "Daily pipeline completed successfully")
        log.info("Health status written.")
        return

    try:
        snapshot = run_live_snapshot()
        log.info("Snapshot: status=%s, %d live matches", snapshot["status"], snapshot["n_live"])
        upload_snapshot(snapshot)
        # Also write to local data/live/ for debugging
        live_dir = REPO_ROOT / "data" / "live"
        live_dir.mkdir(parents=True, exist_ok=True)
        (live_dir / "latest.json").write_text(json.dumps(snapshot, indent=2))
        write_health_status(True, f"Live snapshot OK — {snapshot['n_live']} live matches",
                            {"n_live": snapshot["n_live"], "snapshot_status": snapshot["status"]})
    except Exception as exc:
        log.error("Snapshot failed: %s", exc)
        _dbg("snapshot top-level failure", {"error": str(exc)}, "H-A")
        write_health_status(False, f"Live snapshot failed: {exc}")
        sys.exit(1)
    log.info("Done in %.1fs", time.time() - t0)


if __name__ == "__main__":
    main()
