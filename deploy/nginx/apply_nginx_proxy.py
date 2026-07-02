#!/usr/bin/env python3
"""
Injects proxy_pass location blocks into the HTTPS server block of the
wizardofodds.com NGINX config.

Usage (run as root on 13.52.111.2):
    python3 apply_nginx_proxy.py [--dry-run]

What it does:
    1. Finds the wizardofodds.com NGINX vhost config file
    2. Backs it up with a timestamp
    3. Locates the HTTPS server block (listen 443 / ssl_certificate)
    4. Inserts proxy_pass location blocks before 'location / {' in that block
    5. Prints the next steps: nginx -t && systemctl reload nginx

Safe to run multiple times (idempotent).
Supports --dry-run to preview without writing.
"""
import sys
import os
import re
import shutil
import datetime
import argparse

DRY_RUN = "--dry-run" in sys.argv

NGINX_CANDIDATES = [
    "/etc/nginx/sites-available/wizardofodds.com",
    "/etc/nginx/conf.d/wizardofodds.com.conf",
    "/etc/nginx/sites-available/default",
]

PROXY_BLOCKS = """\
    # ── WizardOfOdds model pages — proxy to sportsodds ───────────────────────
    location /sports-odds/world-cup-market-xray/ {
        proxy_pass https://sportsodds.wizardofodds.com/tools/odds-scanner/predictions/world-cup/market-xray/;
        proxy_set_header Host sportsodds.wizardofodds.com;
        proxy_ssl_server_name on;
        add_header Cache-Control "no-cache, must-revalidate";
    }
    location /sports-odds/wnba-predictions/ {
        proxy_pass https://sportsodds.wizardofodds.com/tools/odds-scanner/predictions/WNBA/Pre-Game/Edge/;
        proxy_set_header Host sportsodds.wizardofodds.com;
        proxy_ssl_server_name on;
        add_header Cache-Control "no-cache, must-revalidate";
    }
    location /sports-odds/wnba-distributions/ {
        proxy_pass https://sportsodds.wizardofodds.com/tools/odds-scanner/predictions/WNBA/Pre-Game/Distributions/;
        proxy_set_header Host sportsodds.wizardofodds.com;
        proxy_ssl_server_name on;
        add_header Cache-Control "no-cache, must-revalidate";
    }
    location /sports-odds/wnba-live-edges/ {
        proxy_pass https://sportsodds.wizardofodds.com/tools/odds-scanner/predictions/WNBA/In-Play/Edges/;
        proxy_set_header Host sportsodds.wizardofodds.com;
        proxy_ssl_server_name on;
        add_header Cache-Control "no-cache, must-revalidate";
    }
    # ── End WizardOfOdds model pages ─────────────────────────────────────────
"""


def find_conf() -> str:
    for path in NGINX_CANDIDATES:
        if os.path.isfile(path):
            return path
    # Last resort: search sites-available
    base = "/etc/nginx/sites-available/"
    if os.path.isdir(base):
        files = os.listdir(base)
        for name in ["wizardofodds", "woo", "woo2026"]:
            if name in files:
                return os.path.join(base, name)
    raise FileNotFoundError(f"No wizardofodds.com NGINX config in: {NGINX_CANDIDATES}")


def find_https_block_insertion_point(conf: str) -> int:
    """
    Returns the character index where the proxy blocks should be inserted.
    Targets the HTTPS server block (listen 443 / ssl_certificate).
    Inserts before 'location / {' or before the block's closing '}'.
    """
    # Split config into server blocks
    # Each server block starts with optional whitespace then "server {"
    # We'll work with positions in the original string

    # Find all server block start positions
    server_starts = [m.start() for m in re.finditer(r'^\s*server\s*\{', conf, re.MULTILINE)]

    if not server_starts:
        # No server blocks found — fall back to last 'location / {'
        idx = conf.rfind("location / {")
        if idx != -1:
            return idx
        return conf.rfind("}")

    # For each server block, find its extent by tracking brace depth
    server_blocks = []
    for start in server_starts:
        # Find the opening brace
        brace_open = conf.index("{", start)
        depth = 0
        end = brace_open
        for i, ch in enumerate(conf[brace_open:], brace_open):
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    end = i
                    break
        block_text = conf[start:end + 1]
        server_blocks.append((start, end + 1, block_text))

    # Find the HTTPS server block (has listen 443 or ssl_certificate)
    https_block = None
    for start, end, text in server_blocks:
        if "listen 443" in text or "ssl_certificate" in text:
            https_block = (start, end, text)

    if https_block is None:
        print("WARNING: No HTTPS server block found — targeting last server block")
        https_block = server_blocks[-1]

    start, end, block_text = https_block
    print(f"  Targeting server block at chars {start}-{end} (len={end-start})")

    # Find 'location / {' within this block (use last occurrence)
    local_idx = block_text.rfind("location / {")
    if local_idx != -1:
        global_idx = start + local_idx
        print(f"  Insertion point: before 'location / {{' at char {global_idx}")
        return global_idx

    # Fallback: before the block's closing brace
    global_idx = end - 1
    print(f"  Insertion point: before closing brace at char {global_idx}")
    return global_idx


def main() -> int:
    print("=== WizardOfOdds NGINX Proxy Block Injector ===")

    try:
        conf_path = find_conf()
    except FileNotFoundError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1

    print(f"Config file: {conf_path}")

    try:
        conf = open(conf_path).read()
    except PermissionError:
        print("ERROR: Permission denied — run as root", file=sys.stderr)
        return 1

    if "wnba-predictions" in conf:
        print("ALREADY DONE — proxy blocks already present. Skipping.")
        return 0

    print(f"Config size: {len(conf)} chars")

    # Find insertion point
    idx = find_https_block_insertion_point(conf)

    new_conf = conf[:idx] + "\n" + PROXY_BLOCKS + "\n" + conf[idx:]

    if DRY_RUN:
        print("\n--- DRY RUN: would write this around insertion point ---")
        print(new_conf[max(0, idx - 50):idx + len(PROXY_BLOCKS) + 50])
        print("--- end dry run ---")
        return 0

    # Backup
    bak = conf_path + ".bak." + datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    try:
        shutil.copy2(conf_path, bak)
        print(f"Backup: {bak}")
    except PermissionError:
        print("ERROR: Cannot backup — run as root", file=sys.stderr)
        return 1

    try:
        open(conf_path, "w").write(new_conf)
    except PermissionError:
        print("ERROR: Cannot write — run as root", file=sys.stderr)
        return 1

    print(f"Proxy blocks injected into: {conf_path}")
    print("")
    print("Next steps:")
    print("  nginx -t")
    print("  systemctl reload nginx")
    print("")
    print("After reload, verify:")
    print("  curl -I https://wizardofodds.com/sports-odds/world-cup-market-xray/")
    print("  curl -I https://wizardofodds.com/sports-odds/wnba-predictions/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
