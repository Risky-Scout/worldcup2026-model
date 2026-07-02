#!/usr/bin/env python3
"""
Adds clean /sports-odds/ URL aliases to the sportsodds.wizardofodds.com NGINX config.
Run as woo on 45.79.0.107.

Usage:
    python3 apply_sportsodds_aliases.py

Creates these short URLs on sportsodds.wizardofodds.com:
  /sports-odds/world-cup-market-xray/  ->  /tools/odds-scanner/predictions/world-cup/market-xray/
  /sports-odds/wnba-predictions/       ->  /tools/odds-scanner/predictions/WNBA/Pre-Game/Edge/
  /sports-odds/wnba-distributions/     ->  /tools/odds-scanner/predictions/WNBA/Pre-Game/Distributions/
  /sports-odds/wnba-live-edges/        ->  /tools/odds-scanner/predictions/WNBA/In-Play/Edges/
"""
import sys
import re
import shutil
import datetime

CONF = "/etc/nginx/sites-available/sportsodds"
FTP_ROOT = "/var/www/sportsodds"

BLOCKS = f"""
    # ── Clean short URLs for model pages (added by deploy pipeline) ───────────
    location /sports-odds/world-cup-market-xray/ {{
        alias {FTP_ROOT}/tools/odds-scanner/predictions/world-cup/market-xray/;
        index index.html;
        try_files $uri $uri/ =404;
        add_header Cache-Control "no-cache, must-revalidate";
    }}
    location /sports-odds/wnba-predictions/ {{
        alias {FTP_ROOT}/tools/odds-scanner/predictions/WNBA/Pre-Game/Edge/;
        index index.html;
        try_files $uri $uri/ =404;
        add_header Cache-Control "no-cache, must-revalidate";
    }}
    location /sports-odds/wnba-distributions/ {{
        alias {FTP_ROOT}/tools/odds-scanner/predictions/WNBA/Pre-Game/Distributions/;
        index index.html;
        try_files $uri $uri/ =404;
        add_header Cache-Control "no-cache, must-revalidate";
    }}
    location /sports-odds/wnba-live-edges/ {{
        alias {FTP_ROOT}/tools/odds-scanner/predictions/WNBA/In-Play/Edges/;
        index index.html;
        try_files $uri $uri/ =404;
        add_header Cache-Control "no-cache, must-revalidate";
    }}
    # ── End clean short URLs ──────────────────────────────────────────────────
"""


def main() -> int:
    conf = open(CONF).read()

    if "sports-odds/wnba-predictions" in conf:
        print("ALREADY DONE — clean URL blocks already present")
        return 0

    bak = "/tmp/sportsodds.bak." + datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    shutil.copy2(CONF, bak)
    print(f"Backup: {bak}")

    # Find server blocks and target the HTTPS one
    server_starts = [m.start() for m in re.finditer(r"^\s*server\s*\{", conf, re.MULTILINE)]
    blist = []
    for s in server_starts:
        brace = conf.index("{", s)
        depth = 0
        end = brace
        for i, ch in enumerate(conf[brace:], brace):
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
            if depth == 0:
                end = i
                break
        blist.append((s, end + 1, conf[s : end + 1]))

    https_block = next(
        (b for b in blist if "listen 443" in b[2] or "ssl_certificate" in b[2]),
        blist[-1],
    )
    start, end, text = https_block
    print(f"Targeting server block at chars {start}-{end}")

    local_idx = text.rfind("location /")
    if local_idx == -1:
        local_idx = len(text) - 2
    global_idx = start + local_idx

    open(CONF, "w").write(conf[:global_idx] + BLOCKS + conf[global_idx:])
    print(f"Clean URL blocks injected into {CONF}")
    print("Run: sudo nginx -t && sudo systemctl reload nginx")
    return 0


if __name__ == "__main__":
    sys.exit(main())
