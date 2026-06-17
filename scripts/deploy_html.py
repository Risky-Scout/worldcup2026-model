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
    # Pre-match — both canonical and -live copy
    {
        "local": REPO_ROOT / "docs" / "pre-match.html",
        "remote_dir": "/tools/odds-scanner/predictions/worldcup",
        "remote_file": "pre-match.html",
        "description": "Pre-match predictions page",
    },
    {
        "local": REPO_ROOT / "docs" / "pre-match.html",
        "remote_dir": "/tools/odds-scanner/predictions/worldcup",
        "remote_file": "pre-match-live.html",
        "description": "Pre-match predictions page (live copy)",
    },
    # PMF distributions — both canonical and -live copy
    {
        "local": REPO_ROOT / "docs" / "pmf-distributions.html",
        "remote_dir": "/tools/odds-scanner/predictions/world-cup/pre-match",
        "remote_file": "probability-distributions.html",
        "description": "Pre-game PMF distributions page",
    },
    {
        "local": REPO_ROOT / "docs" / "pmf-distributions.html",
        "remote_dir": "/tools/odds-scanner/predictions/world-cup/pre-match",
        "remote_file": "probability-distributions-live.html",
        "description": "Pre-game PMF distributions page (live copy)",
    },
    # Live PMF — both canonical and -live copy
    {
        "local": REPO_ROOT / "docs" / "live-pmf.html",
        "remote_dir": "/tools/odds-scanner/predictions/world-cup/live",
        "remote_file": "probability-distributions.html",
        "description": "Live in-play PMF distributions page",
    },
    {
        "local": REPO_ROOT / "docs" / "live-pmf.html",
        "remote_dir": "/tools/odds-scanner/predictions/world-cup/live",
        "remote_file": "probability-distributions-live.html",
        "description": "Live in-play PMF distributions page (live copy)",
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
            remote_path = f'{d["remote_dir"]}/{d["remote_file"]}'

            # Delete before upload so FTP permission errors on overwrite never block deploys
            try:
                ftp.delete(d["remote_file"])
            except Exception:
                pass

            ftp.storbinary(f'STOR {d["remote_file"]}', io.BytesIO(content))

            # Set 755 so nginx can serve the file
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
