"""
Generate a comprehensive matchday briefing report.

Usage:
    python scripts/matchday_report.py [--date 2026-06-12]
    make report
    make report DATE=2026-06-12

Outputs reports/matchday_YYYY-MM-DD.md with:
  - Today's matches: kickoff, venue, model predictions, top scorelines
  - Current group standings context for each group represented
  - Advancement probabilities for teams playing today
  - Model vs market differences for flagged bets
  - Completed match results (if past date)
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "src"))
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from dotenv import load_dotenv
load_dotenv(REPO_ROOT / ".env")

from wc2026.config import PUBLISHED_DIR, DATA_DIR

ET = ZoneInfo("America/New_York")


def _load_standings() -> dict[str, list[dict]]:
    """Load latest BDL group standings snapshot."""
    gs_dir = DATA_DIR / "raw" / "bdl" / "multi" / "group_standings"
    if not gs_dir.exists():
        return {}
    snapshots = sorted(gs_dir.glob("*.jsonl"))
    if not snapshots:
        return {}
    records = []
    with open(snapshots[-1]) as f:
        for line in f:
            try:
                records.append(json.loads(line))
            except Exception:
                pass
    by_group: dict[str, list[dict]] = {}
    for r in records:
        if r.get("season", {}).get("year") != 2026:
            continue
        g = r["group"]["name"]
        by_group.setdefault(g, []).append(r)
    for g in by_group:
        by_group[g].sort(key=lambda x: x["position"])
    return by_group


def _load_advancement_probs() -> dict[str, float]:
    """Load group advancement probabilities from pre-computed cached markdown report."""
    adv_path = REPO_ROOT / "reports" / "group_advancement.md"
    if not adv_path.exists():
        return {}
    probs: dict[str, float] = {}
    for line in adv_path.read_text().splitlines():
        if line.startswith("|") and "%" in line:
            parts = [p.strip() for p in line.split("|")]
            # columns: | Team | Adv% | 1st | 2nd | 3rd | 4th | xPts | xGF | xGA |
            if len(parts) >= 4:
                try:
                    team = parts[1].strip()
                    adv_str = parts[2].replace("**", "").replace("%", "").strip()
                    pct = float(adv_str) / 100
                    if team and 0 <= pct <= 1:
                        probs[team] = pct
                except Exception:
                    pass
    return probs


def _load_winner_probs() -> dict[str, float]:
    """Load tournament winner probabilities from cached simulation."""
    wp_path = REPO_ROOT / "reports" / "winner_probabilities.md"
    if not wp_path.exists():
        return {}
    probs = {}
    for line in wp_path.read_text().splitlines():
        if line.startswith("|") and "%" in line:
            parts = [p.strip() for p in line.split("|")]
            if len(parts) >= 4:
                try:
                    team = parts[2]
                    pct = float(parts[3].replace("%", "").replace("**", "").strip()) / 100
                    probs[team] = pct
                except Exception:
                    pass
    return probs


def generate_report(date: str) -> str:
    json_path = PUBLISHED_DIR / f"{date}.json"
    if not json_path.exists():
        return f"# WC 2026 — {date}\n\nNo predictions found for this date.\n"

    doc = json.loads(json_path.read_text())
    matches = doc.get("matches", [])
    standings = _load_standings()
    adv_probs = _load_advancement_probs()
    win_probs = _load_winner_probs()

    ts = datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    lines = [
        f"# WC 2026 — {date} Matchday Briefing",
        f"",
        f"**Generated**: {ts}",
        f"**Matches**: {len(matches)}",
        f"",
    ]

    # ── Groups represented today ──────────────────────────────────────────
    groups_today: set[str] = set()
    for m in matches:
        # Find group by looking at standings
        for grp, rows in standings.items():
            teams = {r["team"]["name"] for r in rows}
            if m["home_team"] in teams or m["away_team"] in teams:
                groups_today.add(grp)

    # ── Matches ───────────────────────────────────────────────────────────
    lines.append("## Today's Matches")
    lines.append("")

    for i, m in enumerate(matches, 1):
        pred = m.get("prediction", {})
        dm = pred.get("derived_markets", {})
        result = m.get("result")

        # Kickoff time
        try:
            dt_utc = datetime.fromisoformat(
                str(m.get("match_datetime_utc", "")).replace("+00:00", "")
            ).replace(tzinfo=timezone.utc)
            ko_et = dt_utc.astimezone(ET)
            ko_str = ko_et.strftime("%-I:%M %p ET")
        except Exception:
            ko_str = str(m.get("match_datetime_utc", ""))

        hw = dm.get("home_win", 0)
        dr = dm.get("draw", 0)
        aw = dm.get("away_win", 0)
        o25 = dm.get("over_2.5", 0)
        o15 = dm.get("over_1.5", 0)
        btts = dm.get("btts_yes", 0)
        fav = m["home_team"] if hw > aw else (m["away_team"] if aw > hw else "Draw")

        lines += [
            f"### {i}. {m['home_team']} vs {m['away_team']}",
            f"",
            f"**{ko_str}** | {m.get('stage','?')} | {m.get('stadium','?')}",
            f"",
        ]

        if result:
            r = result
            lines.append(f"**RESULT**: {r['result_label']} ({r['outcome'].replace('_',' ').upper()})")
            p = r.get("model_prob_exact_score")
            if p:
                lines.append(f"Model's P({r['result_label']}) = {p:.1%}")
            lines.append("")

        lines += [
            f"| Market | Home ({m['home_team']}) | Draw | Away ({m['away_team']}) |",
            f"|--------|------|------|------|",
            f"| **1X2** | **{hw:.1%}** | **{dr:.1%}** | **{aw:.1%}** |",
            f"| O/U 1.5 | {o15:.0%} over | — | {1-o15:.0%} under |",
            f"| O/U 2.5 | {o25:.0%} over | — | {1-o25:.0%} under |",
            f"| BTTS | {btts:.0%} yes | — | {1-btts:.0%} no |",
            f"",
            f"**Favourite**: {fav}  |  **Mode**: {m.get('publish_mode','?')}  "
            f"|  **Market quality**: {m.get('market_quality',0):.2f}",
            f"",
        ]

        # Top scorelines
        scores = pred.get("top_scorelines", [])[:5]
        if scores:
            lines.append("**Top 5 most-likely scorelines:**")
            lines.append("")
            lines.append("| Score | Probability |")
            lines.append("|-------|-------------|")
            for s in scores:
                lines.append(f"| {s['home_goals']}-{s['away_goals']} | {s['probability']:.2%} |")
            lines.append("")

        # Advancement context
        for team in [m["home_team"], m["away_team"]]:
            p_adv = adv_probs.get(team)
            p_win = win_probs.get(team)
            if p_adv is not None:
                parts = [f"**{team}**: Group advance {p_adv:.0%}"]
                if p_win:
                    parts.append(f"WC winner {p_win:.1%}")
                lines.append("  ".join(parts))
        lines.append("")

        # Edge flags
        er = pred.get("edge_report", {})
        if er and isinstance(er, dict):
            bets = [b for b in er.get("bets", []) if b.get("is_value")]
            if bets:
                lines.append("**⚡ Model Edge Detected:**")
                for b in bets[:3]:
                    lines.append(
                        f"- {b['market']}: model {b.get('model_prob',0):.1%} "
                        f"vs market {b.get('market_prob',0):.1%} "
                        f"(edge {b.get('edge_pct',0):+.1f}%)"
                    )
                lines.append("")

    # ── Standings ──────────────────────────────────────────────────────────
    if groups_today and standings:
        lines += ["---", "", "## Group Standings Context", ""]
        for grp in sorted(groups_today):
            rows = standings.get(grp, [])
            if not rows:
                continue
            lines += [f"### {grp}", ""]
            lines += [
                "| Pos | Team | P | W | D | L | GF | GA | GD | Pts |",
                "|-----|------|---|---|---|---|----|----|-----|-----|",
            ]
            for r in rows:
                gd = r["goal_difference"]
                gd_str = f"+{gd}" if gd > 0 else str(gd)
                adv = "→ " if r["position"] <= 2 else "   "
                lines.append(
                    f"| {adv}{r['position']} | {r['team']['name']} | {r['played']} | "
                    f"{r['won']} | {r['drawn']} | {r['lost']} | {r['goals_for']} | "
                    f"{r['goals_against']} | {gd_str} | **{r['points']}** |"
                )
            lines.append("")

    # ── Model metadata ────────────────────────────────────────────────────
    lines += [
        "---",
        "",
        "## Model Notes",
        "",
        f"- **Prediction mode**: {doc.get('publish_mode_policy','').split('.')[0]}",
        f"- **Data source**: {doc.get('data_source','')}",
        f"- **PMF definition**: {doc.get('regulation_time_definition','')}",
        "",
    ]

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Generate WC2026 matchday briefing report")
    parser.add_argument("--date", default=None, help="Date YYYY-MM-DD (default: today ET)")
    parser.add_argument("--out", default=None, help="Output path (default: reports/matchday_YYYY-MM-DD.md)")
    args = parser.parse_args()

    import logging
    logging.disable(logging.WARNING)

    date = args.date or datetime.now(tz=ET).strftime("%Y-%m-%d")
    report = generate_report(date)

    out_path = Path(args.out) if args.out else REPO_ROOT / "reports" / f"matchday_{date}.md"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(report)
    print(f"Saved: {out_path}")
    print(report[:800])


if __name__ == "__main__":
    main()
