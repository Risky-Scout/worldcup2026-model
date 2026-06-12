"""
Monte Carlo Group Stage Simulator for WC 2026.

Simulates all remaining group-stage matches using the published PMF predictions
to estimate:
  - P(advance | team): probability each team finishes top-2 in their group
  - P(third-place advance | team): probability each third-place team is among
    the 8 best third-place qualifiers advancing to the Round of 32
  - Expected points, goals for/against distributions

Usage:
    python scripts/simulate_groups.py [--n 50000] [--group "Group A"]
    make simulate
    wc2026 simulate

2026 WC format:
    - 12 groups of 4 teams, 6 matches per group
    - Top 2 from each group advance directly (24 teams)
    - Best 8 of the 12 third-place teams also advance (8 teams)
    - Total: 32 teams advance to Round of 32
"""
from __future__ import annotations

import argparse
import json
import math
import random
import sys
from collections import defaultdict
from pathlib import Path
from typing import Optional

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "src"))

from dotenv import load_dotenv
load_dotenv(REPO_ROOT / ".env")

import numpy as np
import pandas as pd

from wc2026.config import PROCESSED_DIR, PUBLISHED_DIR, DATA_DIR


# ─────────────────────────────────────────────────────────────────────────────
# Data loading
# ─────────────────────────────────────────────────────────────────────────────

def load_group_state() -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    """
    Returns:
        completed_df:  group-stage matches already played (with scores)
        scheduled_df:  group-stage matches not yet played
        pmf_by_mid:    {match_id: {(h,a): prob}} from published JSONs
    """
    mdf = pd.read_parquet(PROCESSED_DIR / "v1" / "matches.parquet")
    gs = mdf[(mdf["stage"] == "Group Stage") & (mdf["season"] == 2026)].copy()

    completed = gs[gs["status"].isin(["completed", "final"]) & gs["home_goals"].notna()].copy()
    scheduled = gs[gs["status"] == "scheduled"].copy()

    # Load published PMFs keyed by match_id
    pmf_by_mid: dict[int, dict[tuple[int, int], float]] = {}
    for json_path in sorted(PUBLISHED_DIR.glob("2026-*.json")):
        if json_path.name == "all_scheduled_2026.json":
            continue
        try:
            doc = json.loads(json_path.read_text())
        except Exception:
            continue
        for m in doc.get("matches", []):
            mid = int(m.get("match_id", -1))
            # Build a (h, a) → prob dict from top_scorelines
            scores = m.get("prediction", {}).get("top_scorelines", [])
            if not scores:
                continue
            pmf: dict[tuple[int, int], float] = {}
            for s in scores:
                pmf[(int(s["home_goals"]), int(s["away_goals"]))] = float(s["probability"])
            pmf_by_mid[mid] = pmf

    return completed, scheduled, pmf_by_mid


# ─────────────────────────────────────────────────────────────────────────────
# Simulation primitives
# ─────────────────────────────────────────────────────────────────────────────

def _sample_score(pmf: dict[tuple[int, int], float]) -> tuple[int, int]:
    """Sample a (home_goals, away_goals) from a PMF dict."""
    outcomes = list(pmf.keys())
    probs = [pmf[o] for o in outcomes]
    total = sum(probs)
    # Normalise in case of floating-point drift
    probs = [p / total for p in probs]
    idx = random.choices(range(len(outcomes)), weights=probs, k=1)[0]
    return outcomes[idx]


def _poisson_fallback(lh: float = 1.3, la: float = 1.1, max_g: int = 8) -> dict[tuple[int, int], float]:
    """Balanced Poisson PMF as fallback when no published prediction exists."""
    pmf: dict[tuple[int, int], float] = {}
    from scipy.stats import poisson
    for h in range(max_g + 1):
        for a in range(max_g + 1):
            p = poisson.pmf(h, lh) * poisson.pmf(a, la)
            if p > 1e-6:
                pmf[(h, a)] = p
    return pmf


def _simulate_group(
    group_name: str,
    teams: list[str],
    matches: list[dict],           # list of {match_id, home, away, home_g, away_g, completed}
    pmf_by_mid: dict,
) -> dict[str, dict]:
    """
    Simulate one group and return standings dict {team: {pts, gf, ga, gd}}.
    Completed matches use actual scores; unplayed matches are sampled from PMF.
    """
    pts = {t: 0 for t in teams}
    gf = {t: 0 for t in teams}
    ga = {t: 0 for t in teams}

    for m in matches:
        if m["completed"]:
            hg, ag = m["home_g"], m["away_g"]
        else:
            mid = m["match_id"]
            pmf = pmf_by_mid.get(mid)
            if pmf is None:
                pmf = _poisson_fallback()
            hg, ag = _sample_score(pmf)

        home, away = m["home"], m["away"]
        gf[home] += hg; ga[home] += ag
        gf[away] += ag; ga[away] += hg

        if hg > ag:
            pts[home] += 3
        elif hg == ag:
            pts[home] += 1; pts[away] += 1
        else:
            pts[away] += 3

    return {t: {"pts": pts[t], "gf": gf[t], "ga": ga[t], "gd": gf[t] - ga[t]} for t in teams}


def _rank_group(standings: dict[str, dict]) -> list[str]:
    """
    Rank teams by: points > GD > GF > team name (no H2H for simplicity).
    Returns list of team names sorted 1st→4th.
    """
    return sorted(
        standings.keys(),
        key=lambda t: (
            standings[t]["pts"],
            standings[t]["gd"],
            standings[t]["gf"],
            t,  # alphabetical tiebreak
        ),
        reverse=True,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Third-place ranking (2026 WC uses best 8 of 12)
# ─────────────────────────────────────────────────────────────────────────────

def _rank_third_place(
    third_place_records: list[dict],  # [{team, group, pts, gf, ga, gd}]
) -> list[str]:
    """
    Sort all third-place teams and return the 8 that advance.
    Ranking: points > GD > GF > alphabetical.
    """
    ranked = sorted(
        third_place_records,
        key=lambda r: (r["pts"], r["gd"], r["gf"], r["team"]),
        reverse=True,
    )
    return [r["team"] for r in ranked[:8]]


# ─────────────────────────────────────────────────────────────────────────────
# Monte Carlo driver
# ─────────────────────────────────────────────────────────────────────────────

def run_simulation(n_sims: int = 50_000, seed: int = 42) -> dict:
    """
    Run n_sims Monte Carlo simulations of the group stage.

    Returns a results dict with per-team advancement probabilities and
    expected-value statistics.
    """
    random.seed(seed)
    np.random.seed(seed)

    completed_df, scheduled_df, pmf_by_mid = load_group_state()

    # Build group → teams and group → matches lookup
    all_gs = pd.concat([completed_df, scheduled_df], ignore_index=True)
    groups_map: dict[str, list[str]] = defaultdict(set)
    for _, row in all_gs.iterrows():
        g = row.get("group") or "Unknown"
        groups_map[g].add(row["home_team"])
        groups_map[g].add(row["away_team"])
    groups_map = {g: sorted(teams) for g, teams in groups_map.items()}

    # Build match list per group
    matches_by_group: dict[str, list[dict]] = defaultdict(list)
    for _, row in all_gs.iterrows():
        g = row.get("group") or "Unknown"
        completed = row["status"] in ("completed", "final") and pd.notna(row.get("home_goals"))
        matches_by_group[g].append({
            "match_id": int(row["match_id"]),
            "home": row["home_team"],
            "away": row["away_team"],
            "home_g": int(row["home_goals"]) if completed else 0,
            "away_g": int(row["away_goals"]) if completed else 0,
            "completed": completed,
        })

    # Counters
    advance_direct: dict[str, int] = defaultdict(int)  # top-2
    advance_third: dict[str, int] = defaultdict(int)   # 3rd-place advance
    finish_pos: dict[str, dict[int, int]] = {
        t: {1: 0, 2: 0, 3: 0, 4: 0} for g in groups_map.values() for t in g
    }
    exp_pts: dict[str, list[float]] = defaultdict(list)
    exp_gf: dict[str, list[float]] = defaultdict(list)
    exp_ga: dict[str, list[float]] = defaultdict(list)

    group_names = sorted(groups_map.keys())

    for _ in range(n_sims):
        third_place_records: list[dict] = []

        for g in group_names:
            teams = groups_map[g]
            standings = _simulate_group(g, teams, matches_by_group[g], pmf_by_mid)
            ranked = _rank_group(standings)

            # Top 2 advance directly
            advance_direct[ranked[0]] += 1
            advance_direct[ranked[1]] += 1

            # Track finishing positions
            for pos, team in enumerate(ranked, 1):
                finish_pos[team][pos] += 1

            # Third-place team enters the 3rd-place pool
            third = ranked[2]
            r = standings[third]
            third_place_records.append({
                "team": third, "group": g,
                "pts": r["pts"], "gf": r["gf"], "ga": r["ga"], "gd": r["gd"],
            })

            # Accumulate expected stats
            for team in teams:
                s = standings[team]
                exp_pts[team].append(s["pts"])
                exp_gf[team].append(s["gf"])
                exp_ga[team].append(s["ga"])

        # Determine which 3rd-place teams advance
        advancing_thirds = _rank_third_place(third_place_records)
        for t in advancing_thirds:
            advance_third[t] += 1

    # Aggregate
    results: dict[str, dict] = {}
    for g in group_names:
        teams = groups_map[g]
        group_results = {}
        for team in teams:
            group_results[team] = {
                "group": g,
                "p_1st":   round(finish_pos[team][1] / n_sims, 4),
                "p_2nd":   round(finish_pos[team][2] / n_sims, 4),
                "p_3rd":   round(finish_pos[team][3] / n_sims, 4),
                "p_4th":   round(finish_pos[team][4] / n_sims, 4),
                "p_advance_direct": round(advance_direct[team] / n_sims, 4),
                "p_advance_as_third": round(advance_third[team] / n_sims, 4),
                "p_advance_total": round(
                    (advance_direct[team] + advance_third[team]) / n_sims, 4
                ),
                "exp_pts": round(float(np.mean(exp_pts[team])), 2),
                "exp_gf":  round(float(np.mean(exp_gf[team])), 2),
                "exp_ga":  round(float(np.mean(exp_ga[team])), 2),
            }
        results[g] = group_results

    return {
        "n_sims": n_sims,
        "groups": results,
        "group_names": group_names,
    }


# ─────────────────────────────────────────────────────────────────────────────
# CLI rendering
# ─────────────────────────────────────────────────────────────────────────────

def render_text(sim: dict, group_filter: Optional[str] = None) -> str:
    lines = []
    lines.append(f"\nWC 2026 — Group Stage Advancement Probabilities  (n={sim['n_sims']:,} sims)")
    lines.append("=" * 72)

    for gname in sim["group_names"]:
        if group_filter and gname.lower() != group_filter.lower():
            continue
        group = sim["groups"][gname]
        lines.append(f"\n  {gname}")
        lines.append(
            f"  {'Team':<26} {'Adv%':>5} {'1st':>5} {'2nd':>5} {'3rd':>5} {'4th':>5} "
            f"{'xPts':>5} {'xGF':>4} {'xGA':>4}"
        )
        lines.append("  " + "-" * 68)
        # Sort by p_advance_total desc
        ranked_teams = sorted(group.keys(), key=lambda t: -group[t]["p_advance_total"])
        for team in ranked_teams:
            r = group[team]
            adv = r["p_advance_total"]
            # Bullet for advance % ≥ 80%
            bullet = "→ " if adv >= 0.80 else ("~ " if adv >= 0.50 else "  ")
            lines.append(
                f"  {bullet}{team:<24} {adv:>5.0%} "
                f"{r['p_1st']:>5.0%} {r['p_2nd']:>5.0%} {r['p_3rd']:>5.0%} {r['p_4th']:>5.0%} "
                f"{r['exp_pts']:>5.1f} {r['exp_gf']:>4.1f} {r['exp_ga']:>4.1f}"
            )

    lines.append("\n  → = ≥80% chance to advance  ~ = 50-79%")
    lines.append("  Adv% = P(finish top-2) + P(advance as best 3rd-place)")
    lines.append("")
    return "\n".join(lines)


def render_markdown(sim: dict) -> str:
    from datetime import datetime, timezone
    ts = datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    lines = [
        f"# WC 2026 Group Stage Advancement Probabilities",
        f"",
        f"**Generated**: {ts}  **Simulations**: {sim['n_sims']:,}",
        f"",
        f"Methodology: Monte Carlo simulation of all remaining group-stage fixtures",
        f"using published PMF predictions (market_reconciled where available).",
        f"Tiebreaking: pts > GD > GF > alphabetical (no H2H in simulation).",
        f"Third-place advancement: best 8 of 12 third-place teams by pts/GD/GF.",
        f"",
    ]
    for gname in sim["group_names"]:
        group = sim["groups"][gname]
        lines += [
            f"## {gname}",
            f"",
            f"| Team | Adv% | 1st | 2nd | 3rd | 4th | xPts | xGF | xGA |",
            f"|------|------|-----|-----|-----|-----|------|-----|-----|",
        ]
        for team in sorted(group.keys(), key=lambda t: -group[t]["p_advance_total"]):
            r = group[team]
            lines.append(
                f"| {team} | **{r['p_advance_total']:.0%}** "
                f"| {r['p_1st']:.0%} | {r['p_2nd']:.0%} "
                f"| {r['p_3rd']:.0%} | {r['p_4th']:.0%} "
                f"| {r['exp_pts']:.1f} | {r['exp_gf']:.1f} | {r['exp_ga']:.1f} |"
            )
        lines.append("")
    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Monte Carlo WC2026 group stage simulator")
    parser.add_argument("--n", type=int, default=50_000, help="Number of simulations (default: 50000)")
    parser.add_argument("--group", type=str, default=None, help="Filter output to one group e.g. 'Group A'")
    parser.add_argument("--json", action="store_true", help="Output raw JSON instead of text")
    parser.add_argument("--markdown", action="store_true", help="Output Markdown report")
    parser.add_argument("--save", action="store_true", help="Save report to reports/group_advancement.md")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    import logging
    logging.basicConfig(level=logging.WARNING)

    print(f"Running {args.n:,} simulations...", file=sys.stderr, flush=True)
    sim = run_simulation(n_sims=args.n, seed=args.seed)

    if args.json:
        print(json.dumps(sim, indent=2))
    elif args.markdown or args.save:
        md = render_markdown(sim)
        if args.save:
            out = REPO_ROOT / "reports" / "group_advancement.md"
            out.write_text(md)
            print(f"Saved to {out}", file=sys.stderr)
        else:
            print(md)
    else:
        print(render_text(sim, group_filter=args.group))


if __name__ == "__main__":
    main()
