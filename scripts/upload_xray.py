"""
Upload Market X-Ray JSON to the production server via FTP.

Usage:
    python scripts/upload_xray.py

Reads:
    data/published/wc-xray.json

Uploads to:
    FTP_HOST  /tools/odds-scanner/predictions/worldcup/wc-xray.json

Environment (in .env or CI secrets):
    FTP_HOST   server hostname or IP
    FTP_USER   FTP username
    FTP_PASS   FTP password
"""
from __future__ import annotations

import ftplib
import io
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "src"))

try:
    from dotenv import load_dotenv
    load_dotenv(REPO_ROOT / ".env")
except ImportError:
    pass

REMOTE_DIR = "/tools/odds-scanner/predictions/worldcup"
REMOTE_FILE = "wc-xray.json"
LOCAL_FILE = REPO_ROOT / "data" / "published" / "wc-xray.json"


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


def upload() -> None:
    host = os.environ.get("FTP_HOST", "").strip()
    user = os.environ.get("FTP_USER", "").strip()
    password = os.environ.get("FTP_PASS", "").strip()

    if not host or not user or not password:
        print("ERROR: FTP_HOST, FTP_USER, and FTP_PASS must be set in .env or environment")
        sys.exit(1)

    if not LOCAL_FILE.exists():
        print(f"WARNING: {LOCAL_FILE} not found — run generate_xray.py first")
        print("Skipping upload.")
        return

    payload_bytes = LOCAL_FILE.read_bytes()
    print(f"Uploading wc-xray.json ({len(payload_bytes):,} bytes) → {host}{REMOTE_DIR}/{REMOTE_FILE}")

    with ftplib.FTP(host, timeout=30) as ftp:
        ftp.login(user, password)
        print(f"  Connected: {ftp.getwelcome()[:80]}")

        _ensure_remote_dir(ftp, REMOTE_DIR)
        ftp.cwd(REMOTE_DIR)

        ftp.storbinary(f"STOR {REMOTE_FILE}", io.BytesIO(payload_bytes))
        try:
            ftp.sendcmd(f"SITE CHMOD 644 {REMOTE_DIR}/{REMOTE_FILE}")
        except Exception:
            pass
        print(f"  ✓ Uploaded: {REMOTE_DIR}/{REMOTE_FILE}")

        try:
            ftp.sendcmd(f"SITE CHMOD 2775 {REMOTE_DIR}")
        except Exception:
            pass

    print("Done.")


def main() -> None:
    upload()


if __name__ == "__main__":
    main()
