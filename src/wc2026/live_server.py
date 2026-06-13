"""
WC2026 Live PMF FastAPI Server

Endpoints:
  POST /webhook/bdl        — BDL push events (goal, status change, etc.)
  GET  /ws/live            — WebSocket: pushed PMF on every event
  GET  /api/live           — REST fallback: latest wc-live.json as JSON
  GET  /api/pre-match      — REST: today's wc-predictions.json
  GET  /health             — Health check for monitoring

Run:
  uvicorn wc2026.live_server:app --host 127.0.0.1 --port 8000 --workers 1

The server loads LivePMFPredictor and pregame lambdas ONCE at startup.
On each BDL webhook event it recomputes the live PMF and broadcasts to
all connected WebSocket clients in < 200ms.
"""
from __future__ import annotations

import asyncio
import hashlib
import hmac
import json
import logging
import os
import sys
import time
from contextlib import asynccontextmanager
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "src"))

try:
    from dotenv import load_dotenv
    load_dotenv(REPO_ROOT / ".env")
except ImportError:
    pass

log = logging.getLogger("wc2026.live_server")
logging.basicConfig(level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(name)s: %(message)s")

_STARTUP_TIME = time.time()

# ── State (shared across requests — single worker only) ───────────────────
_predictor = None          # LivePMFPredictor instance
_pregame_lambdas: dict = {}  # match_id / "Home|Away" → (lh, la)
_latest_snapshot: dict = {"status": "starting", "n_live": 0, "live_matches": [],
                           "generated_at": datetime.now(tz=timezone.utc).isoformat()}
_live_json_path: Path = REPO_ROOT / "data" / "live" / "latest.json"
_pre_match_json_path: Path = REPO_ROOT / "data" / "published"
_ws_clients: set[WebSocket] = set()
_lambda_date: str = ""     # date pregame lambdas were loaded for


# ── Startup / shutdown ─────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load model at startup; schedule daily lambda reload."""
    global _predictor
    log.info("Starting WC2026 Live Server…")
    try:
        from wc2026.live.predictor import LivePMFPredictor
        _predictor = LivePMFPredictor(max_delta=7, max_goals=10)
        log.info("LivePMFPredictor loaded.")
    except Exception as exc:
        log.error("Failed to load LivePMFPredictor: %s", exc)

    _load_pregame_lambdas()
    # After lambdas are loaded, _load_pregame_lambdas already wires the
    # temperature.  Log the final startup state for diagnostics.
    if _predictor is not None:
        log.info(
            "LivePMFPredictor ready: T=%.4f  xg_blend=%.2f  max_delta=%d",
            _predictor.temperature, _predictor.xg_blend, _predictor.max_delta,
        )

    # Background: reload lambdas daily at midnight and heartbeat ping
    asyncio.create_task(_daily_reload_task())
    asyncio.create_task(_heartbeat_task())

    # Load latest snapshot from disk if it exists
    if _live_json_path.exists():
        try:
            global _latest_snapshot
            _latest_snapshot = json.loads(_live_json_path.read_text())
        except Exception:
            pass

    log.info("Server ready. Predictor: %s, lambdas: %d matches",
             "OK" if _predictor else "MISSING", len(_pregame_lambdas))
    yield
    log.info("Shutting down WC2026 Live Server.")


app = FastAPI(title="WC2026 Live PMF Server", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


# ── Calibration temperature loader ────────────────────────────────────────
def _load_calib_temperature() -> float:
    """
    Read the latest calibration temperature from data/calibration/health.jsonl.

    This is written by run_real_pipeline.py on every daily run and contains
    the T derived from the Elo OOF walkforward (formula: (T_elo+1)/2, capped
    [1.0, 1.4]).  Returns 1.0 if the file does not exist or cannot be parsed.
    """
    health_path = REPO_ROOT / "data" / "calibration" / "health.jsonl"
    if not health_path.exists():
        return 1.0
    try:
        lines = health_path.read_text().strip().splitlines()
        if not lines:
            return 1.0
        rec = json.loads(lines[-1])
        T = float(rec.get("calib_temperature", 1.0))
        # Sanity clamp: reject implausible values
        T = max(1.0, min(T, 1.5))
        return T
    except Exception as exc:
        log.warning("Could not read calib temperature from health.jsonl: %s", exc)
        return 1.0


# ── Pregame lambda loader ──────────────────────────────────────────────────
def _load_pregame_lambdas() -> None:
    global _pregame_lambdas, _lambda_date
    today = date.today().isoformat()
    pub_path = _pre_match_json_path / f"{today}.json"
    if not pub_path.exists():
        # Try yesterday as fallback
        import datetime as _dt
        yesterday = (_dt.date.today() - _dt.timedelta(days=1)).isoformat()
        pub_path = _pre_match_json_path / f"{yesterday}.json"

    if not pub_path.exists():
        log.warning("No published JSON found for pregame lambdas — using defaults")
        return

    try:
        doc = json.loads(pub_path.read_text())
        lambdas = {}
        for m in doc.get("matches", []):
            pred = m.get("prediction", {})
            lh = float(pred.get("expected_home_goals") or pred.get("composite_expected_home_goals") or 1.35)
            la = float(pred.get("expected_away_goals") or pred.get("composite_expected_away_goals") or 1.00)
            mid = str(m.get("match_id", ""))
            home = m.get("home_team", "")
            away = m.get("away_team", "")
            if mid:
                lambdas[mid] = (lh, la)
            lambdas[f"{home}|{away}"] = (lh, la)
        _pregame_lambdas = lambdas
        _lambda_date = today
        log.info("Pregame lambdas loaded from %s: %d matches", pub_path.name,
                 len(doc.get("matches", [])))

        # Wire calibrated temperature from daily pipeline into live predictor.
        # The pipeline writes T to data/calibration/health.jsonl each run.
        # Without this, the live model defaults to T=1.0 (uncalibrated).
        if _predictor is not None:
            new_T = _load_calib_temperature()
            if abs(new_T - _predictor.temperature) > 0.005:
                old_T = _predictor.temperature
                _predictor.temperature = new_T
                log.info(
                    "Live predictor calibration temperature updated: %.4f → %.4f",
                    old_T, new_T,
                )
            else:
                log.info("Live predictor temperature unchanged: T=%.4f", _predictor.temperature)
    except Exception as exc:
        log.warning("Failed to load pregame lambdas: %s", exc)


# ── Background tasks ───────────────────────────────────────────────────────
async def _daily_reload_task():
    """Reload pregame lambdas at midnight each day and monitor for stale snapshots."""
    _last_alert_sent: float = 0.0

    while True:
        await asyncio.sleep(3600)  # check every hour
        today = date.today().isoformat()
        if today != _lambda_date:
            log.info("New day detected — reloading pregame lambdas.")
            _load_pregame_lambdas()

        # Alert if live snapshot is stale during match window (14:00–03:00 UTC)
        now_h = datetime.now(tz=timezone.utc).hour
        is_match_window = now_h >= 14 or now_h <= 3
        if is_match_window and _latest_snapshot.get("n_live", 0) > 0:
            try:
                last_dt = datetime.fromisoformat(
                    _latest_snapshot.get("generated_at", "2000-01-01").replace("Z", "+00:00"))
                stale_secs = (datetime.now(tz=timezone.utc) - last_dt).total_seconds()
                if stale_secs > 600 and (time.time() - _last_alert_sent) > 1800:
                    msg = (f"Live snapshot is {int(stale_secs/60)} min stale "
                           f"({_latest_snapshot.get('n_live')} matches were live)")
                    log.warning(msg)
                    _send_alert("Live snapshot stale during match window", msg)
                    _last_alert_sent = time.time()
            except Exception:
                pass


async def _heartbeat_task():
    """Send ping to all WebSocket clients every 30s to keep connections alive."""
    while True:
        await asyncio.sleep(30)
        dead = set()
        for ws in list(_ws_clients):
            try:
                await ws.send_json({"type": "ping", "ts": time.time()})
            except Exception:
                dead.add(ws)
        for ws in dead:
            _ws_clients.discard(ws)


# ── Core: compute live PMF and broadcast ──────────────────────────────────
def _compute_live_snapshot(bdl_matches: list[dict]) -> dict:
    """Run LivePMFPredictor on a list of BDL match records. Returns snapshot dict."""
    from zoneinfo import ZoneInfo
    now_utc = datetime.now(tz=timezone.utc)
    today_et = now_utc.astimezone(ZoneInfo("America/New_York")).date().isoformat()

    results = []
    for bdl_m in bdl_matches:
        mid = str(bdl_m.get("id", ""))
        home = (bdl_m.get("home_team") or {}).get("full_name", "Home")
        away = (bdl_m.get("away_team") or {}).get("full_name", "Away")
        lh, la = _pregame_lambdas.get(mid, _pregame_lambdas.get(f"{home}|{away}", (1.35, 1.00)))

        try:
            result = _predictor.predict_from_bdl(bdl_m, pregame_lh=lh, pregame_la=la)
            if result:
                d = result.to_dict()
                d["pregame_lh"] = lh
                d["pregame_la"] = la
                d["bdl_status"] = bdl_m.get("status")
                results.append(d)
        except Exception as exc:
            log.warning("LivePMF failed for %s vs %s: %s", home, away, exc)

    return {
        "generated_at": now_utc.isoformat(),
        "date": today_et,
        "status": "live" if results else "quiet",
        "n_live": len(results),
        "live_matches": results,
        "source": "websocket",
    }


async def _broadcast(snapshot: dict) -> None:
    """Write snapshot to disk and push to all WebSocket clients."""
    global _latest_snapshot
    _latest_snapshot = snapshot

    # Write to disk (fallback for polling clients + FTP sync)
    _live_json_path.parent.mkdir(parents=True, exist_ok=True)
    _live_json_path.write_text(json.dumps(snapshot, ensure_ascii=False))

    payload = json.dumps({"type": "pmf_update", "data": snapshot})
    dead = set()
    for ws in list(_ws_clients):
        try:
            await ws.send_text(payload)
        except Exception:
            dead.add(ws)
    for ws in dead:
        _ws_clients.discard(ws)

    if _ws_clients:
        log.info("Broadcast to %d WebSocket clients (n_live=%d)", len(_ws_clients), snapshot["n_live"])


# ── BDL Webhook event classification ──────────────────────────────────────
_LIVE_STATUSES = {
    "1h", "2h", "ht", "et", "pso",
    "in_progress", "in progress", "live", "ongoing", "active",
    "first half", "second half", "halftime", "half time",
    "1st half", "2nd half", "extra time", "extra_time",
}


def _is_live_match(bdl_m: dict) -> bool:
    status = str(bdl_m.get("status", "") or "").lower().strip()
    clock_seconds = int(bdl_m.get("clock_seconds", 0) or 0)
    return status in _LIVE_STATUSES or clock_seconds > 60


# ── Webhook signature verification ────────────────────────────────────────
def _verify_webhook_signature(body: bytes, signature_header: str | None) -> bool:
    secret = os.environ.get("WEBHOOK_SECRET", "")
    if not secret:
        return True  # No secret configured — accept all (dev mode)
    if not signature_header:
        return False
    expected = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    # BDL may send "sha256=<hex>" format
    sig = signature_header.replace("sha256=", "").strip()
    return hmac.compare_digest(expected, sig)


# ── Endpoints ─────────────────────────────────────────────────────────────

@app.post("/webhook/bdl")
async def webhook_bdl(request: Request):
    """
    Receive BDL push events. Triggered on: goal.scored, match.started,
    match.halftime, match.ended, match.status_changed.
    """
    body = await request.body()
    sig = request.headers.get("X-BDL-Signature") or request.headers.get("X-Signature")
    if not _verify_webhook_signature(body, sig):
        log.warning("Webhook signature verification failed")
        raise HTTPException(status_code=401, detail="Invalid signature")

    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    event_type = payload.get("event", payload.get("type", "unknown"))
    match_data = payload.get("match", payload.get("data", payload))
    log.info("Webhook: event=%s", event_type)

    if _predictor is None:
        log.error("Predictor not loaded — cannot process webhook")
        return {"ok": False, "error": "predictor_not_ready"}

    # Handle both single match and array
    if isinstance(match_data, list):
        matches = match_data
    elif isinstance(match_data, dict):
        matches = [match_data]
    else:
        return {"ok": True, "processed": 0, "event": event_type}

    live_matches = [m for m in matches if _is_live_match(m)]
    if not live_matches and event_type not in ("match.ended", "match.status_changed"):
        return {"ok": True, "processed": 0, "note": "no_live_matches_in_event"}

    # For match.ended, send the final completed state
    if not live_matches:
        live_matches = matches

    snapshot = _compute_live_snapshot(live_matches)
    await _broadcast(snapshot)

    return {"ok": True, "processed": len(live_matches), "n_live": snapshot["n_live"],
            "event": event_type}


@app.websocket("/ws/live")
async def websocket_live(ws: WebSocket):
    """WebSocket endpoint — clients receive pushed PMF on every BDL event."""
    await ws.accept()
    _ws_clients.add(ws)
    client_ip = ws.client.host if ws.client else "unknown"
    log.info("WebSocket connected: %s (total=%d)", client_ip, len(_ws_clients))

    try:
        # Send current snapshot immediately on connect
        await ws.send_text(json.dumps({
            "type": "pmf_update",
            "data": _latest_snapshot,
        }))

        # Keep connection alive — actual updates come via _broadcast()
        while True:
            try:
                await asyncio.wait_for(ws.receive_text(), timeout=45)
            except asyncio.TimeoutError:
                # No client message in 45s — send keepalive
                await ws.send_json({"type": "keepalive", "ts": time.time()})
    except WebSocketDisconnect:
        log.info("WebSocket disconnected: %s", client_ip)
    except Exception as exc:
        log.warning("WebSocket error (%s): %s", client_ip, exc)
    finally:
        _ws_clients.discard(ws)


@app.get("/api/live")
async def api_live():
    """REST fallback — returns latest live PMF snapshot."""
    return JSONResponse(_latest_snapshot)


@app.get("/api/pre-match")
async def api_pre_match():
    """REST — returns today's pre-game predictions JSON."""
    today = date.today().isoformat()
    path = _pre_match_json_path / f"{today}.json"
    if not path.exists():
        import datetime as _dt
        yesterday = (_dt.date.today() - _dt.timedelta(days=1)).isoformat()
        path = _pre_match_json_path / f"{yesterday}.json"
    if not path.exists():
        raise HTTPException(status_code=404, detail="No predictions available")
    return JSONResponse(json.loads(path.read_text()))


def _send_alert(subject: str, body: str) -> None:
    """Non-blocking alert via Slack or email."""
    import urllib.request
    slack_url = os.environ.get("SLACK_WEBHOOK_URL", "")
    if slack_url:
        try:
            payload = f'{{"text": "🚨 WC2026: {subject}\\n{body}"}}'.encode()
            req = urllib.request.Request(slack_url, data=payload,
                                         headers={"Content-Type": "application/json"})
            urllib.request.urlopen(req, timeout=5)
        except Exception:
            pass


@app.get("/health")
async def health():
    """Health check endpoint."""
    uptime_s = int(time.time() - _STARTUP_TIME)
    last_update = _latest_snapshot.get("generated_at", "never")
    n_live = _latest_snapshot.get("n_live", 0)
    predictor_ok = _predictor is not None
    lambdas_count = len(_pregame_lambdas)

    # Check if live snapshot is stale during match hours
    stale = False
    try:
        last_dt = datetime.fromisoformat(last_update.replace("Z", "+00:00"))
        stale_secs = (datetime.now(tz=timezone.utc) - last_dt).total_seconds()
        stale = stale_secs > 600  # > 10 min
    except Exception:
        stale = True

    return {
        "ok": predictor_ok,
        "uptime_s": uptime_s,
        "last_update": last_update,
        "n_live": n_live,
        "ws_clients": len(_ws_clients),
        "lambdas_loaded": lambdas_count,
        "lambda_date": _lambda_date,
        "snapshot_stale": stale,
        "version": "1.0.0",
    }


@app.post("/api/refresh-snapshot")
async def refresh_snapshot(request: Request):
    """
    Internal endpoint — called by live_snapshot.py to push a newly computed
    snapshot into the server's state and broadcast to WebSocket clients.
    Requires X-Internal-Token header matching WEBHOOK_SECRET.
    """
    token = request.headers.get("X-Internal-Token", "")
    secret = os.environ.get("WEBHOOK_SECRET", "")
    if secret and not hmac.compare_digest(token, secret):
        raise HTTPException(status_code=401, detail="Unauthorized")

    body = await request.body()
    try:
        snapshot = json.loads(body)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    await _broadcast(snapshot)
    return {"ok": True, "n_live": snapshot.get("n_live", 0), "ws_clients": len(_ws_clients)}


@app.get("/api/reload-lambdas")
async def reload_lambdas(request: Request):
    """Force-reload pregame lambdas from today's published JSON."""
    token = request.headers.get("X-Internal-Token", "")
    secret = os.environ.get("WEBHOOK_SECRET", "")
    if secret and not hmac.compare_digest(token, secret):
        raise HTTPException(status_code=401, detail="Unauthorized")
    _load_pregame_lambdas()
    return {"ok": True, "lambdas": len(_pregame_lambdas), "date": _lambda_date}
