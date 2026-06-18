"""
Upload today's World Cup predictions JSON to the production server via FTP.

Usage:
    python scripts/upload_predictions.py [--date 2026-06-13]
    make upload
    make upload DATE=2026-06-13

Reads:
    data/published/YYYY-MM-DD.json  (today by default)

Uploads to:
    FTP_HOST  /tools/odds-scanner/predictions/world cup/wc-predictions.json

Environment (in .env or CI secrets):
    FTP_HOST   server hostname or IP
    FTP_USER   FTP username
    FTP_PASS   FTP password
"""
from __future__ import annotations

import argparse
import ftplib
import json
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

REMOTE_DIR = "/tools/odds-scanner/predictions/worldcup"
REMOTE_DIR_HYPHEN = "/tools/odds-scanner/predictions/world-cup/pre-match"
REMOTE_DIR_WC_ROOT = "/tools/odds-scanner/predictions/world-cup"
REMOTE_DIR_SPACE = "/tools/odds-scanner/predictions/world cup"   # legacy path — WoO admin page 96 still points here
REMOTE_FILE = "wc-predictions.json"


def _ensure_remote_dir(ftp: ftplib.FTP, path: str) -> None:
    """Create remote directory tree if it doesn't exist."""
    parts = [p for p in path.split("/") if p]
    current = ""
    for part in parts:
        current += f"/{part}"
        try:
            ftp.cwd(current)
        except ftplib.error_perm:
            try:
                ftp.mkd(current)
                print(f"  Created remote dir: {current}")
            except ftplib.error_perm as e:
                if "exists" not in str(e).lower():
                    raise


def upload(date: str | None = None) -> None:
    host = os.environ.get("FTP_HOST", "").strip()
    user = os.environ.get("FTP_USER", "").strip()
    password = os.environ.get("FTP_PASS", "").strip()

    if not host or not user or not password:
        print("ERROR: FTP_HOST, FTP_USER, and FTP_PASS must be set in .env or environment")
        sys.exit(1)

    date = date or datetime.now(tz=ET).strftime("%Y-%m-%d")
    json_path = REPO_ROOT / "data" / "published" / f"{date}.json"

    if not json_path.exists():
        print(f"WARNING: No published predictions found for {date} (rest day?): {json_path}")
        print("Skipping upload — no file to upload.")
        return

    # Load and enrich with metadata
    doc = json.loads(json_path.read_text())
    doc["generated_at"] = datetime.now(tz=timezone.utc).isoformat()
    doc["date"] = date
    doc["source"] = "wc2026-model"

    payload = json.dumps(doc, ensure_ascii=False, separators=(",", ":"))
    payload_bytes = payload.encode("utf-8")

    print(f"Uploading {date}.json ({len(payload_bytes):,} bytes) → {host}{REMOTE_DIR}/{REMOTE_FILE}")

    with ftplib.FTP(host, timeout=30) as ftp:
        ftp.login(user, password)
        print(f"  Connected: {ftp.getwelcome()[:80]}")

        _ensure_remote_dir(ftp, REMOTE_DIR)
        ftp.cwd(REMOTE_DIR)

        import io
        ftp.storbinary(f"STOR {REMOTE_FILE}", io.BytesIO(payload_bytes))
        try:
            ftp.sendcmd(f"SITE CHMOD 775 {REMOTE_DIR}/{REMOTE_FILE}")
        except Exception:
            pass
        print(f"  ✓ Uploaded: {REMOTE_DIR}/{REMOTE_FILE}")

        # Also write a date-stamped archive copy
        archive_file = f"wc-{date}.json"
        ftp.storbinary(f"STOR {archive_file}", io.BytesIO(payload_bytes))
        try:
            ftp.sendcmd(f"SITE CHMOD 775 {REMOTE_DIR}/{archive_file}")
        except Exception:
            pass
        print(f"  ✓ Archived: {REMOTE_DIR}/{archive_file}")

        # Ensure directory is readable by nginx
        try:
            ftp.sendcmd(f"SITE CHMOD 2775 {REMOTE_DIR}")
        except Exception:
            pass

        # Mirror to world-cup/pre-match/ for PMF distributions page (./wc-predictions.json)
        _ensure_remote_dir(ftp, REMOTE_DIR_HYPHEN)
        ftp.cwd(REMOTE_DIR_HYPHEN)
        ftp.storbinary(f"STOR {REMOTE_FILE}", io.BytesIO(payload_bytes))
        try:
            ftp.sendcmd(f"SITE CHMOD 775 {REMOTE_DIR_HYPHEN}/{REMOTE_FILE}")
            ftp.sendcmd(f"SITE CHMOD 2775 {REMOTE_DIR_HYPHEN}")
        except Exception:
            pass
        print(f"  ✓ Mirrored: {REMOTE_DIR_HYPHEN}/{REMOTE_FILE}")

        # Also mirror to world-cup/ root for ../wc-predictions.json fallback
        _ensure_remote_dir(ftp, REMOTE_DIR_WC_ROOT)
        ftp.cwd(REMOTE_DIR_WC_ROOT)
        ftp.storbinary(f"STOR {REMOTE_FILE}", io.BytesIO(payload_bytes))
        try:
            ftp.sendcmd(f"SITE CHMOD 775 {REMOTE_DIR_WC_ROOT}/{REMOTE_FILE}")
            ftp.sendcmd(f"SITE CHMOD 2775 {REMOTE_DIR_WC_ROOT}")
        except Exception:
            pass
        print(f"  ✓ Mirrored: {REMOTE_DIR_WC_ROOT}/{REMOTE_FILE}")

        # Mirror to legacy "world cup" (space) path — WoO admin page 96 iframe src still uses this
        _ensure_remote_dir(ftp, REMOTE_DIR_SPACE)
        ftp.cwd(REMOTE_DIR_SPACE)
        ftp.storbinary(f"STOR {REMOTE_FILE}", io.BytesIO(payload_bytes))
        try:
            ftp.sendcmd(f"SITE CHMOD 644 {REMOTE_DIR_SPACE}/{REMOTE_FILE}")
            ftp.sendcmd(f"SITE CHMOD 755 {REMOTE_DIR_SPACE}")
        except Exception:
            pass
        print(f"  ✓ Mirrored: {REMOTE_DIR_SPACE}/{REMOTE_FILE}")

    print(f"Done. {len(doc.get('matches', []))} matches uploaded.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Upload WC2026 predictions to FTP")
    parser.add_argument("--date", default=None, help="Date YYYY-MM-DD (default: today ET)")
    args = parser.parse_args()
    upload(args.date)


if __name__ == "__main__":
    main()
