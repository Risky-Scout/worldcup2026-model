"""
Deploy Market X-Ray HTML/CSS/JS files to the production FTP server.

Usage:
    python scripts/upload_xray_html.py

Uploads:
    docs/market-xray/index.html  → tools/odds-scanner/predictions/world-cup/market-xray/index.html
    docs/market-xray/match.html  → tools/odds-scanner/predictions/world-cup/market-xray/match.html
    docs/market-xray/xray.js     → tools/odds-scanner/predictions/world-cup/market-xray/xray.js
    docs/market-xray/xray.css    → tools/odds-scanner/predictions/world-cup/market-xray/xray.css

Environment (in .env or CI secrets):
    FTP_HOST   server hostname or IP
    FTP_USER   FTP username
    FTP_PASS   FTP password
"""
from __future__ import annotations

import ftplib
import io
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

try:
    from dotenv import load_dotenv
    load_dotenv(REPO_ROOT / ".env")
except ImportError:
    pass

REMOTE_DIR = "/tools/odds-scanner/predictions/world-cup/market-xray"

DEPLOYMENTS = [
    {
        "local": REPO_ROOT / "docs" / "market-xray" / "index.html",
        "remote_file": "index.html",
        "description": "Market X-Ray main table page",
    },
    {
        "local": REPO_ROOT / "docs" / "market-xray" / "match.html",
        "remote_file": "match.html",
        "description": "Market X-Ray match detail page",
    },
    {
        "local": REPO_ROOT / "docs" / "market-xray" / "xray.js",
        "remote_file": "xray.js",
        "description": "Market X-Ray shared JS helpers",
    },
    {
        "local": REPO_ROOT / "docs" / "market-xray" / "xray.css",
        "remote_file": "xray.css",
        "description": "Market X-Ray styles",
    },
]


def _ensure_remote_dir(ftp: ftplib.FTP, path: str) -> None:
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


def deploy() -> None:
    host = os.environ.get("FTP_HOST", "").strip()
    user = os.environ.get("FTP_USER", "").strip()
    password = os.environ.get("FTP_PASS", "").strip()

    if not host or not user or not password:
        print("ERROR: FTP_HOST, FTP_USER, and FTP_PASS must be set in .env or environment")
        sys.exit(1)

    print(f"Connecting to {host}…")
    with ftplib.FTP(host, timeout=30) as ftp:
        ftp.login(user, password)
        print(f"  Connected: {ftp.getwelcome()[:80]}")

        _ensure_remote_dir(ftp, REMOTE_DIR)

        for d in DEPLOYMENTS:
            local_path: Path = d["local"]
            if not local_path.exists():
                print(f"  SKIP: {local_path} not found")
                continue

            content = local_path.read_bytes()
            ftp.cwd(REMOTE_DIR)
            remote_path = f'{REMOTE_DIR}/{d["remote_file"]}'

            # Delete before upload so FTP permission errors on overwrite never block deploys
            try:
                ftp.delete(d["remote_file"])
            except Exception:
                pass

            ftp.storbinary(f'STOR {d["remote_file"]}', io.BytesIO(content))

            # Set 644 so nginx can serve the file
            for mode in ("755", "644"):
                try:
                    ftp.sendcmd(f"SITE CHMOD {mode} {remote_path}")
                    break
                except Exception:
                    pass

            size_kb = len(content) / 1024
            print(f"  ✓ {d['description']}: {remote_path} ({size_kb:.1f} KB)")

    print("Deploy complete.")


if __name__ == "__main__":
    deploy()
