#!/bin/bash
# WC2026 Production Server Setup Script
# Run on the server as root: bash deploy/server_setup.sh
# Or from local: ssh root@45.79.0.107 'bash -s' < deploy/server_setup.sh
set -euo pipefail

REPO_DIR="/var/www/wc2026"
GITHUB_REPO="https://github.com/Risky-Scout/worldcup2026-model.git"
PYTHON="/var/www/wc2026/.venv/bin/python"

echo "=== WC2026 Server Setup ==="
echo "Server: $(hostname) — $(date -u)"

# ── 1. System dependencies ────────────────────────────────────────────────
echo "[1/8] Installing system dependencies…"
apt-get update -qq
apt-get install -y -qq \
    python3.10 python3.10-venv python3.10-dev python3-pip \
    git nginx curl jq \
    2>&1 | tail -5
echo "✓ System dependencies installed"

# ── 2. Clone / update repo ────────────────────────────────────────────────
echo "[2/8] Setting up repository at $REPO_DIR…"
if [ -d "$REPO_DIR/.git" ]; then
    echo "  Repo exists — pulling latest…"
    cd "$REPO_DIR" && git pull origin main
else
    git clone "$GITHUB_REPO" "$REPO_DIR"
fi
echo "✓ Repository ready"

# ── 3. Python virtual environment ─────────────────────────────────────────
echo "[3/8] Creating Python venv and installing dependencies…"
cd "$REPO_DIR"
python3.10 -m venv .venv
.venv/bin/pip install --quiet --upgrade pip
.venv/bin/pip install --quiet -e ".[live]" 2>/dev/null || \
    .venv/bin/pip install --quiet -e . && \
    .venv/bin/pip install --quiet fastapi "uvicorn[standard]" websockets
echo "✓ Python environment ready"

# ── 4. .env file ──────────────────────────────────────────────────────────
echo "[4/8] Checking .env file…"
if [ ! -f "$REPO_DIR/.env" ]; then
    echo "ERROR: .env file missing at $REPO_DIR/.env"
    echo "Please create it with: BDL_API_KEY, FTP_HOST, FTP_USER, FTP_PASS, WEBHOOK_SECRET"
    exit 1
fi
echo "✓ .env found"

# ── 5. Systemd services ───────────────────────────────────────────────────
echo "[5/8] Installing systemd services…"
cp "$REPO_DIR/deploy/wc2026-live.service" /etc/systemd/system/
cp "$REPO_DIR/deploy/wc2026-daily.service" /etc/systemd/system/
cp "$REPO_DIR/deploy/wc2026-daily.timer" /etc/systemd/system/
systemctl daemon-reload
systemctl enable wc2026-live.service
systemctl enable wc2026-daily.timer
systemctl restart wc2026-live.service || systemctl start wc2026-live.service
systemctl start wc2026-daily.timer
echo "✓ Systemd services installed and started"

# Verify live server started
sleep 3
if systemctl is-active --quiet wc2026-live.service; then
    echo "✓ wc2026-live.service is running"
else
    echo "⚠ wc2026-live.service failed to start — check: journalctl -u wc2026-live -n 30"
fi

# ── 6. Nginx configuration ────────────────────────────────────────────────
echo "[6/8] Configuring nginx…"
# Detect existing SSL cert path
SSL_CERT=""
for d in /etc/letsencrypt/live/sportsodds.wizardofodds.com \
          /etc/letsencrypt/live/wizardofodds.com \
          /etc/ssl/certs; do
    if [ -f "$d/fullchain.pem" ]; then
        SSL_CERT="$d"
        break
    fi
done

NGINX_CONF="$REPO_DIR/deploy/nginx-sportsodds.conf"

if [ -n "$SSL_CERT" ]; then
    # Update cert paths in config
    sed -i "s|/etc/letsencrypt/live/sportsodds.wizardofodds.com|$SSL_CERT|g" "$NGINX_CONF"
fi

# Check if there's an existing nginx config for this domain
EXISTING_CONF=""
for f in /etc/nginx/sites-enabled/* /etc/nginx/conf.d/*.conf; do
    if [ -f "$f" ] && grep -q "sportsodds.wizardofodds.com" "$f" 2>/dev/null; then
        EXISTING_CONF="$f"
        break
    fi
done

if [ -n "$EXISTING_CONF" ]; then
    echo "  Found existing nginx config: $EXISTING_CONF"
    echo "  Adding /api/, /ws/, /webhook/ proxy blocks only (preserving rest)…"
    # Inject proxy blocks into existing server block before the closing brace
    PROXY_BLOCKS='
    # WC2026 API proxy (auto-injected by server_setup.sh)
    location /ws/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_read_timeout 3600s;
        proxy_buffering off;
    }
    location ~ ^/(api|webhook|health)(/|$) {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        add_header Access-Control-Allow-Origin "*" always;
    }
    # End WC2026 API proxy'
    # Only inject if not already there
    if ! grep -q "wc2026" "$EXISTING_CONF"; then
        # Insert before last closing brace
        sed -i "$ i\\${PROXY_BLOCKS}" "$EXISTING_CONF"
        echo "  Injected proxy blocks into $EXISTING_CONF"
    else
        echo "  WC2026 proxy blocks already present, skipping injection"
    fi
else
    echo "  No existing config found — installing full nginx config"
    cp "$NGINX_CONF" /etc/nginx/sites-available/sportsodds-wc2026
    ln -sf /etc/nginx/sites-available/sportsodds-wc2026 /etc/nginx/sites-enabled/
fi

nginx -t && systemctl reload nginx && echo "✓ Nginx configured and reloaded" || \
    echo "⚠ Nginx config test failed — check: nginx -t"

# ── 7. Crontab (live snapshot every minute) ───────────────────────────────
echo "[7/8] Setting up live snapshot cron…"
CRON_LINE="* * * * * $PYTHON /var/www/wc2026/scripts/live_snapshot.py >> /var/log/wc2026-live.log 2>&1"
# Add only if not already present
(crontab -l 2>/dev/null | grep -v "live_snapshot" ; echo "$CRON_LINE") | crontab -
echo "✓ Cron job added (every minute)"

# ── 8. Initial pipeline run and health check ──────────────────────────────
echo "[8/8] Running initial pipeline validation…"
cd "$REPO_DIR"
$PYTHON scripts/daily_update.py --skip-fetch --date "$(date +%Y-%m-%d)" 2>&1 | tail -5 || \
    echo "⚠ Initial pipeline run failed — check logs"

# Health check
sleep 2
HEALTH=$(curl -sf http://127.0.0.1:8000/health 2>/dev/null || echo '{"ok":false}')
echo "Health: $HEALTH"

echo ""
echo "=== Setup Complete ==="
echo "  Live server: $(systemctl is-active wc2026-live.service)"
echo "  Daily timer: $(systemctl is-active wc2026-daily.timer)"
echo "  Nginx:       $(systemctl is-active nginx)"
echo ""
echo "Test:"
echo "  curl http://127.0.0.1:8000/health"
echo "  curl https://sportsodds.wizardofodds.com/health"
echo ""
echo "Logs:"
echo "  journalctl -u wc2026-live -f"
echo "  journalctl -u wc2026-daily -f"
echo "  tail -f /var/log/wc2026-live.log"
