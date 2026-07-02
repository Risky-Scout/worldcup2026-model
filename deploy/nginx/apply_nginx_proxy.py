#!/usr/bin/env python3
"""
Injects proxy location blocks for WizardOfOdds model pages into the
wizardofodds.com NGINX vhost config.

Usage:
    sudo python3 ~/deploy/nginx/apply_nginx_proxy.py

Tries these config files in order:
    /etc/nginx/sites-available/wizardofodds.com
    /etc/nginx/conf.d/wizardofodds.com.conf
    /etc/nginx/sites-enabled/default

Safe to run multiple times (idempotent).
"""
import sys
import shutil
import datetime
import os

CANDIDATES = [
    "/etc/nginx/sites-available/wizardofodds.com",
    "/etc/nginx/conf.d/wizardofodds.com.conf",
    "/etc/nginx/sites-enabled/default",
]

BLOCKS_CANDIDATES = [
    os.path.expanduser("~/deploy/nginx/location_blocks_proxy.conf"),
    "/home/woo/deploy/nginx/location_blocks_proxy.conf",
    "/home/ubuntu/deploy/nginx/location_blocks_proxy.conf",
]


def find_file(paths: list[str]) -> str | None:
    for p in paths:
        if os.path.exists(p):
            return p
    return None


def main() -> int:
    nginx_conf = find_file(CANDIDATES)
    if not nginx_conf:
        print("ERROR: Could not find wizardofodds.com NGINX config in:", CANDIDATES, file=sys.stderr)
        return 1

    blocks_file = find_file(BLOCKS_CANDIDATES)
    if not blocks_file:
        print("ERROR: location_blocks_proxy.conf not found", file=sys.stderr)
        return 1

    print(f"Using NGINX config: {nginx_conf}")
    print(f"Using blocks file:  {blocks_file}")

    try:
        conf = open(nginx_conf).read()
    except PermissionError:
        print(f"ERROR: Cannot read {nginx_conf} — run with sudo", file=sys.stderr)
        return 1

    blocks = open(blocks_file).read()

    if "wnba-predictions" in conf:
        print(f"ALREADY DONE — location blocks already present in {nginx_conf}")
        return 0

    # Backup
    bak = nginx_conf + ".bak." + datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    try:
        shutil.copy2(nginx_conf, bak)
        print(f"Backup written: {bak}")
    except PermissionError:
        print(f"ERROR: Cannot backup {nginx_conf} — run with sudo", file=sys.stderr)
        return 1

    # Insertion: before the last 'location / {' or before the last '}'
    for marker in ["location / {", "location /"]:
        idx = conf.rfind(marker)
        if idx != -1:
            break
    else:
        idx = conf.rfind("}")
        if idx == -1:
            print("ERROR: Cannot find insertion point in NGINX config", file=sys.stderr)
            return 1

    new_conf = conf[:idx] + "\n" + blocks + "\n    " + conf[idx:]
    try:
        open(nginx_conf, "w").write(new_conf)
    except PermissionError:
        print(f"ERROR: Cannot write {nginx_conf} — run with sudo", file=sys.stderr)
        return 1

    print(f"Proxy location blocks injected into {nginx_conf}")
    print("")
    print("Next steps:")
    print("  sudo nginx -t")
    print("  sudo systemctl reload nginx")
    print("")
    print("After reload, these URLs will proxy to sportsodds.wizardofodds.com:")
    print("  https://wizardofodds.com/sports-odds/world-cup-market-xray/")
    print("  https://wizardofodds.com/sports-odds/wnba-predictions/")
    print("  https://wizardofodds.com/sports-odds/wnba-distributions/")
    print("  https://wizardofodds.com/sports-odds/wnba-live-edges/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
