#!/usr/bin/env python3
"""
Creates static HTML redirect files at clean /sports-odds/ paths in the sportsodds web root.
These files redirect visitors to the actual page locations without requiring NGINX config changes.

Run via SSH as woo@45.79.0.107 (home dir = /var/www/sportsodds).

Creates:
  ~/sports-odds/world-cup-market-xray/index.html  → /tools/odds-scanner/predictions/world-cup/market-xray/
  ~/sports-odds/wnba-predictions/index.html        → /tools/odds-scanner/predictions/WNBA/Pre-Game/Edge/
  ~/sports-odds/wnba-distributions/index.html      → /tools/odds-scanner/predictions/WNBA/Pre-Game/Distributions/
  ~/sports-odds/wnba-live-edges/index.html         → /tools/odds-scanner/predictions/WNBA/In-Play/Edges/
"""
import os

WEBROOT = os.path.expanduser("~")   # /var/www/sportsodds on sportsodds server

REDIRECTS = [
    (
        "sports-odds/world-cup-market-xray",
        "/tools/odds-scanner/predictions/world-cup/market-xray/",
        "World Cup Market X-Ray",
    ),
    (
        "sports-odds/wnba-predictions",
        "/tools/odds-scanner/predictions/WNBA/Pre-Game/Edge/",
        "WNBA Pre-Game Edge Board",
    ),
    (
        "sports-odds/wnba-distributions",
        "/tools/odds-scanner/predictions/WNBA/Pre-Game/Distributions/",
        "WNBA Pre-Game Distributions",
    ),
    (
        "sports-odds/wnba-live-edges",
        "/tools/odds-scanner/predictions/WNBA/In-Play/Edges/",
        "WNBA In-Play Live Edges",
    ),
]

REDIRECT_HTML = """\
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>WizardOfOdds — {title}</title>
  <meta http-equiv="refresh" content="0;url={url}">
  <script>window.location.replace("{url}");</script>
</head>
<body>
  <p>Loading <a href="{url}">{title}</a>…</p>
</body>
</html>
"""


def main() -> None:
    for slug, target_url, title in REDIRECTS:
        dest_dir = os.path.join(WEBROOT, slug)
        dest_file = os.path.join(dest_dir, "index.html")

        os.makedirs(dest_dir, exist_ok=True)
        html = REDIRECT_HTML.format(url=target_url, title=title)
        with open(dest_file, "w") as f:
            f.write(html)
        print(f"Created: {dest_file}  ->  {target_url}")

    print("\nDone. Test these URLs:")
    for slug, _, _ in REDIRECTS:
        print(f"  https://sportsodds.wizardofodds.com/{slug}/")


if __name__ == "__main__":
    main()
