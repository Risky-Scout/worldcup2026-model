# WC2026 Server Deployment — Run When SSH Access Is Ready

## Step 1: SSH into the server
```bash
ssh root@45.79.0.107
```

## Step 2: Write .env file on the server
```bash
cat > /tmp/wc2026.env << 'EOF'
BDL_API_KEY=<your_bdl_key>
FTP_HOST=45.79.0.107
FTP_USER=woo
FTP_PASS=<your_ftp_pass>
WEBHOOK_SECRET=<pick_a_random_secret_eg_openssl_rand_hex_32>
SLACK_WEBHOOK_URL=<optional_slack_webhook_url>
ALERT_EMAIL=<optional_alert_email>
EOF
```

## Step 3: Run the automated setup script
```bash
# Pull repo and run full setup (takes ~3-5 minutes)
git clone https://github.com/Risky-Scout/worldcup2026-model.git /var/www/wc2026
cp /tmp/wc2026.env /var/www/wc2026/.env
bash /var/www/wc2026/deploy/server_setup.sh
```

## Step 4: Verify everything is running
```bash
# Check services
systemctl status wc2026-live
systemctl status wc2026-daily.timer

# Test health endpoint
curl http://127.0.0.1:8000/health
curl https://sportsodds.wizardofodds.com/health

# Check logs
journalctl -u wc2026-live -n 30
```

## Step 5: Register BDL webhook
```bash
cd /var/www/wc2026
source .env
.venv/bin/python scripts/live_snapshot.py \
    --register-webhook https://sportsodds.wizardofodds.com/webhook/bdl
```

## Step 6: Add GitHub Secret for WEBHOOK_SECRET
In GitHub repo Settings → Secrets → Actions:
- Add `WEBHOOK_SECRET` = same value used in .env above
- Add `SLACK_WEBHOOK_URL` if using Slack alerts

## Validation checklist
- [ ] `curl https://sportsodds.wizardofodds.com/health` → `{"ok":true,...}`
- [ ] `systemctl is-active wc2026-live` → `active`
- [ ] `systemctl is-active wc2026-daily.timer` → `active`
- [ ] Live page badge shows "● WebSocket" when connected
- [ ] GitHub Actions daily.yml: "Skip if server healthy" step shows `SKIP_PIPELINE=true`

## Troubleshooting

**Server fails to start:**
```bash
journalctl -u wc2026-live -n 50
# Common: missing dep → cd /var/www/wc2026 && .venv/bin/pip install fastapi "uvicorn[standard]" websockets
```

**Nginx proxy not working:**
```bash
nginx -t                    # test config
cat /var/log/nginx/error.log | tail -20
# Common: SSL cert path wrong in nginx-sportsodds.conf — update and reload
```

**BDL webhook not triggering:**
```bash
# Check webhook is registered at app.balldontlie.io/webhooks
# Verify WEBHOOK_SECRET matches what was registered
journalctl -u wc2026-live | grep webhook
```
