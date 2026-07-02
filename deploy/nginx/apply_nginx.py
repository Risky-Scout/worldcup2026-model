#!/usr/bin/env python3
"""
Injects WizardOfOdds model page location blocks into the NGINX default vhost.

Usage:
    sudo python3 /home/woo/wc2026/deploy/nginx/apply_nginx.py

What it does:
    - Backs up /etc/nginx/sites-available/default
    - Injects 4 location blocks (WC Market X-Ray, WNBA Predictions, Distributions, Live Edges)
      before the WordPress catch-all 'location / {' block
    - Prints next steps: sudo nginx -t && sudo systemctl reload nginx

Safe to run multiple times (idempotent — skips if blocks already present).
"""
import sys
import shutil
import datetime

NGINX_CONF = "/etc/nginx/sites-available/default"
BLOCKS_FILE = "/home/woo/wc2026/deploy/nginx/location_blocks.conf"


def main() -> int:
    try:
        conf = open(NGINX_CONF).read()
    except PermissionError:
        print(f"ERROR: Cannot read {NGINX_CONF} — run with sudo", file=sys.stderr)
        return 1

    try:
        blocks = open(BLOCKS_FILE).read()
    except FileNotFoundError:
        print(f"ERROR: {BLOCKS_FILE} not found — did the SCP step complete?", file=sys.stderr)
        return 1

    if "wnba-predictions" in conf:
        print(f"ALREADY DONE — location blocks already present in {NGINX_CONF}")
        return 0

    # Backup
    bak = NGINX_CONF + ".bak." + datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    try:
        shutil.copy2(NGINX_CONF, bak)
        print(f"Backup written: {bak}")
    except PermissionError:
        print(f"ERROR: Cannot backup {NGINX_CONF} — run with sudo", file=sys.stderr)
        return 1

    # Insertion strategy: before the last 'location / {' (WordPress catch-all)
    # Fall back to before the last '}' if no 'location / {' found
    marker = "location / {"
    idx = conf.rfind(marker)
    if idx == -1:
        print("WARNING: 'location / {' not found — inserting before last closing brace")
        idx = conf.rfind("}")
        if idx == -1:
            print("ERROR: Cannot find insertion point in NGINX config", file=sys.stderr)
            return 1

    new_conf = conf[:idx] + "\n" + blocks + "\n    " + conf[idx:]
    try:
        open(NGINX_CONF, "w").write(new_conf)
    except PermissionError:
        print(f"ERROR: Cannot write {NGINX_CONF} — run with sudo", file=sys.stderr)
        return 1

    print(f"Location blocks injected into {NGINX_CONF}")
    print("")
    print("Next steps:")
    print("  sudo nginx -t")
    print("  sudo systemctl reload nginx")
    print("")
    print("After reload, these URLs will serve model pages:")
    print("  https://wizardofodds.com/sports-odds/world-cup-market-xray/")
    print("  https://wizardofodds.com/sports-odds/wnba-predictions/")
    print("  https://wizardofodds.com/sports-odds/wnba-distributions/")
    print("  https://wizardofodds.com/sports-odds/wnba-live-edges/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
