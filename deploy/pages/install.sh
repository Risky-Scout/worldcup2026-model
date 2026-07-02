#!/bin/bash
# ═══════════════════════════════════════════════════════════
# WizardOfOdds Model Pages Installer
# Run as root on wizardofodds.com (13.52.111.2):
#   curl -sL https://raw.githubusercontent.com/Risky-Scout/worldcup2026-model/main/deploy/pages/install.sh | bash
# ═══════════════════════════════════════════════════════════
set -e

REPO_RAW="https://raw.githubusercontent.com/Risky-Scout/worldcup2026-model/main/deploy/pages"

# Auto-detect web root from the existing world-cup page
WEBROOT=$(find /var/www /srv/www /home /usr/share/nginx /data -maxdepth 4 \
  -name "index.html" -path "*/sports-odds/world-cup-2026-predictions/*" 2>/dev/null \
  | head -1 | xargs dirname | xargs dirname | xargs dirname 2>/dev/null)

if [ -z "$WEBROOT" ]; then
  # Fallback: find via nginx config
  WEBROOT=$(nginx -T 2>/dev/null | grep -E '^\s*root\s+' | grep -v '#' \
    | awk '{print $2}' | tr -d ';' | head -1)
fi

if [ -z "$WEBROOT" ]; then
  echo "ERROR: Could not auto-detect web root."
  echo "Run: nginx -T | grep root"
  echo "Then: WEBROOT=/path/to/webroot bash <(curl -sL $REPO_RAW/install.sh)"
  exit 1
fi

echo "Web root: $WEBROOT"
echo ""

PAGES=(
  "world-cup-market-xray"
  "wnba-predictions"
  "wnba-distributions"
  "wnba-live-edges"
)

for slug in "${PAGES[@]}"; do
  DIR="$WEBROOT/sports-odds/$slug"
  mkdir -p "$DIR"
  curl -sL "$REPO_RAW/$slug.html" -o "$DIR/index.html"
  echo "✓  Created: $DIR/index.html"
done

echo ""
echo "═══════════════════════════════════════════════════════"
echo "DONE. Verifying..."
sleep 1
for slug in "${PAGES[@]}"; do
  STATUS=$(curl -s -o /dev/null -w "%{http_code}" "https://wizardofodds.com/sports-odds/$slug/")
  echo "  https://wizardofodds.com/sports-odds/$slug/ -> $STATUS"
done
echo "═══════════════════════════════════════════════════════"
