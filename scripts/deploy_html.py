"""
Deploy the pre-match HTML page to the production FTP server.

Usage:
    python scripts/deploy_html.py
    make deploy
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

DEPLOYMENTS = [
    {
        "local": REPO_ROOT / "docs" / "pre-match.html",
        "remote_dir": "/tools/odds-scanner/predictions/world cup",
        "remote_file": "pre match.html",
        "description": "Pre-match predictions page",
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

        for d in DEPLOYMENTS:
            local_path: Path = d["local"]
            if not local_path.exists():
                print(f"  SKIP: {local_path} not found")
                continue

            content = local_path.read_bytes()
            _ensure_remote_dir(ftp, d["remote_dir"])
            ftp.cwd(d["remote_dir"])
            ftp.storbinary(f'STOR {d["remote_file"]}', io.BytesIO(content))
            remote_path = f'{d["remote_dir"]}/{d["remote_file"]}'
            try:
                ftp.sendcmd(f"SITE CHMOD 775 {remote_path}")
            except Exception:
                pass
            size_kb = len(content) / 1024
            print(f"  ✓ {d['description']}: {remote_path} ({size_kb:.1f} KB)")

    print("Deploy complete.")


if __name__ == "__main__":
    deploy()
