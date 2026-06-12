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


_POISSON_FALLBACK_CACHE: dict[tuple, dict] = {}

def _poisson_fallback(lh: float = 1.3, la: float = 1.1, max_g: int = 8) -> dict[tuple[int, int], float]:
    """Balanced Poisson PMF as fallback — cached to avoid repeated scipy calls."""
    key = (round(lh, 4), round(la, 4), max_g)
    if key in _POISSON_FALLBACK_CACHE:
        return _POISSON_FALLBACK_CACHE[key]
    from scipy.stats import poisson
    pmf: dict[tuple[int, int], float] = {}
    for h in range(max_g + 1):
        for a in range(max_g + 1):
            p = poisson.pmf(h, lh) * poisson.pmf(a, la)
            if p > 1e-6:
                pmf[(h, a)] = p
    _POISSON_FALLBACK_CACHE[key] = pmf
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
# Knockout bracket engine
# ─────────────────────────────────────────────────────────────────────────────

# 2026 WC: which 3rd-place slots can come from which groups.
# Source: FIFA 2026 WC bracket structure.
# Key = R32 slot descriptor (as it appears in the data), Value = priority-ordered
# list of groups. In each simulation we pick the highest-priority advancing
# 3rd-place team from the eligible groups.
_THIRD_PLACE_SLOTS: dict[str, list[str]] = {
    "3A/3B/3C/3D/3F": ["A", "B", "C", "D", "F"],
    "3C/3D/3F/3G/3H": ["C", "D", "F", "G", "H"],
    "3C/3E/3F/3H/3I": ["C", "E", "F", "H", "I"],
    "3E/3H/3I/3J/3K": ["E", "H", "I", "J", "K"],
    "3A/3E/3H/3I/3J": ["A", "E", "H", "I", "J"],
    "3B/3E/3F/3I/3J": ["B", "E", "F", "I", "J"],
    "3E/3F/3G/3I/3J": ["E", "F", "G", "I", "J"],
    "3D/3E/3I/3J/3L": ["D", "E", "I", "J", "L"],
}

# Map "G1"/"G2"/"H1"/"H2" slots to the actual group winner/runner-up.
# In the 2026 bracket, G1 = 1G (winner Group G), etc.
_SPECIAL_SLOTS: dict[str, str] = {
    "G1": "1G",
    "G2": "2G",
    "H1": "1H",
    "H2": "2H",
}


def _resolve_slot(
    slot: str,
    group_qualifiers: dict[str, tuple[str, str]],   # group_letter → (1st, 2nd)
    third_pool: dict[str, str],                       # group_letter → team name
    third_assignments: dict[str, str],                # slot_key → team (already assigned)
) -> str:
    """Resolve a bracket slot string to an actual team name."""
    # Normalize special slots (G1→1G, etc.)
    canon = _SPECIAL_SLOTS.get(slot, slot)

    # "1X" / "2X" → group winner / runner-up
    if len(canon) == 2 and canon[0] in "12" and canon[1].upper() in "ABCDEFGHIJKL":
        pos = int(canon[0]) - 1
        g = canon[1].upper()
        teams = group_qualifiers.get(g, ("TBD", "TBD"))
        return teams[pos] if pos < len(teams) else "TBD"

    # 3rd-place compound slot e.g. "3A/3B/3C/3D/3F"
    if slot in _THIRD_PLACE_SLOTS:
        if slot in third_assignments:
            return third_assignments[slot]
        # Assign: first eligible group in priority list that still has a team
        for g in _THIRD_PLACE_SLOTS[slot]:
            if g in third_pool and third_pool[g] not in third_assignments.values():
                team = third_pool[g]
                third_assignments[slot] = team
                return team
        return "TBD"

    return slot  # already a team name or "TBD"


_KO_PMF_CACHE: dict[tuple[str, str], dict[tuple[int, int], float]] = {}
_KO_FALLBACK_PMF: dict[tuple[int, int], float] = {}


def _build_team_strength_pmf(
    home: str,
    away: str,
    team_lambdas: dict[str, tuple[float, float]],  # team → (att_lam, def_lam)
    global_avg: float = 1.25,
    max_g: int = 8,
) -> dict[tuple[int, int], float]:
    """Build a team-strength-aware Poisson PMF for a knockout matchup."""
    key = (home, away)
    if key in _KO_PMF_CACHE:
        return _KO_PMF_CACHE[key]

    h_att, h_def = team_lambdas.get(home, (1.25, 1.25))
    a_att, a_def = team_lambdas.get(away, (1.25, 1.25))
    # Standard Poisson: lh = home_att × away_def / global_avg (with small home advantage)
    lh = max(0.2, h_att * a_def / global_avg * 1.05)  # 5% home advantage (neutral site → 1.0)
    la = max(0.2, a_att * h_def / global_avg)

    pmf: dict[tuple[int, int], float] = {}
    from scipy.stats import poisson as _poisson
    for h in range(max_g + 1):
        for a in range(max_g + 1):
            p = _poisson.pmf(h, lh) * _poisson.pmf(a, la)
            if p > 1e-6:
                pmf[(h, a)] = p
    _KO_PMF_CACHE[key] = pmf
    return pmf


def _simulate_knockout_match(
    home: str,
    away: str,
    pmf_by_mid: dict,
    team_lambdas: dict,
    match_id: Optional[int] = None,
) -> str:
    """
    Simulate a single knockout match and return the winner.
    Uses published PMF if available; otherwise builds a team-strength-aware
    Poisson PMF from composite lambdas (cached by matchup pair).
    Draws after 90 min resolved with 50/50 coin flip (ET/pens simplified).
    """
    global _KO_FALLBACK_PMF
    if home == "TBD" or away == "TBD":
        return random.choice([home, away])

    pmf = (pmf_by_mid.get(match_id) if match_id else None)
    if pmf is None:
        if team_lambdas:
            pmf = _build_team_strength_pmf(home, away, team_lambdas)
        else:
            if not _KO_FALLBACK_PMF:
                _KO_FALLBACK_PMF = _poisson_fallback()
            pmf = _KO_FALLBACK_PMF

    hg, ag = _sample_score(pmf)
    if hg > ag:
        return home
    elif ag > hg:
        return away
    else:
        return random.choice([home, away])


def _simulate_tournament(
    group_qualifiers: dict[str, tuple[str, str]],  # group_letter → (1st, 2nd)
    third_pool: dict[str, str],                      # group_letter → 3rd-place team
    ko_matches: list[dict],                           # R32 / R16 / QF / SF / Final fixtures
    pmf_by_mid: dict,
    team_lambdas: dict,
) -> dict[str, int]:
    """
    Simulate the full knockout bracket for one tournament run.

    ko_matches: sorted list of {match_id, slot_home, slot_away, round_num}
    Returns dict {team: rounds_won} for winner tracking.
    """
    # Current state: slot → team
    # We resolve R32 bracket first, then propagate winners.
    # Match results keyed by match_id: {match_id: winner_team}
    match_winners: dict[int, str] = {}

    # Map "W{n}" → match_id that produced it
    # Tournament match numbers: group stage 1-72, R32 73-88, R16 89-96, QF 97-100, SF 101-102, F 104
    # match_id 146 = tournament match 73, so match_id = tournament_num + 73
    def _tournament_num(mid: int) -> int:
        return mid - 73  # match_id 146 → 73, 147 → 74, etc.

    mid_by_tnum: dict[int, int] = {}
    for m in ko_matches:
        tnum = _tournament_num(m["match_id"])
        mid_by_tnum[tnum] = m["match_id"]

    def _resolve_ko_slot(slot: str, third_assignments: dict) -> str:
        """Resolve W73, L101, or group slot to team name."""
        if slot.startswith("W"):
            tnum = int(slot[1:])
            mid = mid_by_tnum.get(tnum)
            return match_winners.get(mid, "TBD") if mid else "TBD"
        if slot.startswith("L"):
            tnum = int(slot[1:])
            mid = mid_by_tnum.get(tnum)
            # L-slot = loser of that match (3rd-place game)
            return match_winners.get(mid, "TBD") if mid else "TBD"
        return _resolve_slot(slot, group_qualifiers, third_pool, third_assignments)

    third_assignments: dict[str, str] = {}
    winner_counts: dict[str, int] = defaultdict(int)

    for m in sorted(ko_matches, key=lambda x: x["match_id"]):
        home = _resolve_ko_slot(m["slot_home"], third_assignments)
        away = _resolve_ko_slot(m["slot_away"], third_assignments)
        winner = _simulate_knockout_match(home, away, pmf_by_mid, team_lambdas, m.get("match_id"))
        match_winners[m["match_id"]] = winner

    # Final winner = winner of the Final match (match_id 177 = tournament match 104)
    final_mid = mid_by_tnum.get(104) or 177
    champion = match_winners.get(final_mid, "TBD")
    return champion, match_winners


def load_knockout_fixtures() -> list[dict]:
    """Load the R32/R16/QF/SF/Final fixture slots from the processed matches parquet."""
    mdf = pd.read_parquet(PROCESSED_DIR / "v1" / "matches.parquet")
    ko = mdf[(mdf["season"] == 2026) & (mdf["stage"] != "Group Stage")].copy()
    ko = ko[ko["stage"] != "Match for 3rd place"]  # exclude 3rd-place for winner tracking

    fixtures = []
    for _, r in ko.iterrows():
        fixtures.append({
            "match_id": int(r["match_id"]),
            "stage": r["stage"],
            "slot_home": str(r["home_team"]).strip(),
            "slot_away": str(r["away_team"]).strip(),
        })
    return fixtures


def _load_team_lambdas() -> dict[str, tuple[float, float]]:
    """Load attack/defense lambdas for all 2026 teams from the composite prior."""
    try:
        from wc2026.ratings.composite import CompositeTeamPrior
        import pandas as pd
        mdf = pd.read_parquet(PROCESSED_DIR / "v1" / "matches.parquet")
        odds_df = pd.read_parquet(PROCESSED_DIR / "v1" / "odds.parquet")
        ts = pd.read_parquet(PROCESSED_DIR / "v1" / "team_stats.parquet")
        prior = CompositeTeamPrior()
        prior.fit(mdf, odds_df, ts)
        lambdas: dict[str, tuple[float, float]] = {}
        for team, tp in prior._priors.items():
            lambdas[team] = (tp.final_attack_lambda, tp.final_defense_lambda)
        return lambdas
    except Exception as exc:
        print(f"[warn] Could not load composite priors: {exc}", file=sys.stderr)
        return {}


def run_full_tournament_simulation(n_sims: int = 50_000, seed: int = 42) -> dict:
    """
    Extend group stage simulation through the knockout bracket to compute
    tournament winner probabilities for all 48 teams.
    """
    random.seed(seed)
    np.random.seed(seed)

    completed_df, scheduled_df, pmf_by_mid = load_group_state()
    ko_fixtures = load_knockout_fixtures()

    # Load team-strength lambdas for knockout PMF generation
    print("Loading team strength ratings...", file=sys.stderr, flush=True)
    team_lambdas = _load_team_lambdas()
    print(f"  {len(team_lambdas)} teams loaded", file=sys.stderr, flush=True)

    all_gs = pd.concat([completed_df, scheduled_df], ignore_index=True)
    groups_map: dict[str, list[str]] = defaultdict(set)
    for _, row in all_gs.iterrows():
        g = row.get("group") or "Unknown"
        groups_map[g].add(row["home_team"])
        groups_map[g].add(row["away_team"])
    groups_map = {g: sorted(teams) for g, teams in groups_map.items()}

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

    group_names = sorted(groups_map.keys())
    champion_counts: dict[str, int] = defaultdict(int)
    # Also track R32/R16/QF/SF/Final round exits
    round_exits: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))

    for sim_i in range(n_sims):
        # 1. Simulate group stage
        group_qualifiers: dict[str, tuple[str, str]] = {}
        third_pool: dict[str, str] = {}
        third_place_records: list[dict] = []

        for g in group_names:
            g_letter = g.split()[-1]  # "Group A" → "A"
            teams = groups_map[g]
            standings = _simulate_group(g, teams, matches_by_group[g], pmf_by_mid)
            ranked = _rank_group(standings)
            group_qualifiers[g_letter] = (ranked[0], ranked[1])
            third = ranked[2]
            third_pool[g_letter] = third
            s = standings[third]
            third_place_records.append({
                "team": third, "group": g_letter,
                "pts": s["pts"], "gf": s["gf"], "ga": s["ga"], "gd": s["gd"],
            })

        # Determine which 8 3rd-place teams advance (best by pts/GD/GF)
        ranked_thirds = sorted(
            third_place_records,
            key=lambda r: (r["pts"], r["gd"], r["gf"], r["team"]),
            reverse=True,
        )[:8]
        qualifying_third_groups = {r["group"] for r in ranked_thirds}
        # Prune third_pool to only advancing teams
        third_pool_qualified = {
            g: third_pool[g] for g in third_pool if g in qualifying_third_groups
        }

        # 2. Simulate knockout bracket
        champion, match_winners = _simulate_tournament(
            group_qualifiers, third_pool_qualified, ko_fixtures, pmf_by_mid, team_lambdas
        )
        champion_counts[champion] += 1

    return {
        "n_sims": n_sims,
        "champion_probs": {
            team: round(cnt / n_sims, 5)
            for team, cnt in sorted(champion_counts.items(), key=lambda x: -x[1])
        },
    }


def render_winner_text(sim: dict) -> str:
    lines = []
    lines.append(f"\nWC 2026 — Tournament Winner Probabilities  (n={sim['n_sims']:,} sims)")
    lines.append("=" * 60)
    probs = sim["champion_probs"]
    # Top 16 by probability
    top = sorted(probs.items(), key=lambda x: -x[1])
    lines.append(f"\n  {'Rank':<5} {'Team':<28} {'Win%':>6}  {'Odds':>8}")
    lines.append("  " + "-" * 52)
    for rank, (team, p) in enumerate(top, 1):
        if p < 0.001 and rank > 20:
            break
        odds = f"+{round(1/p - 1)*100:,}" if p > 0 else "—"
        lines.append(f"  {rank:<5} {team:<28} {p:>6.1%}  {odds:>8}")
    lines.append("")
    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Monte Carlo WC2026 group stage simulator")
    parser.add_argument("--n", type=int, default=50_000, help="Number of simulations (default: 50000)")
    parser.add_argument("--group", type=str, default=None, help="Filter output to one group e.g. 'Group A'")
    parser.add_argument("--winner", action="store_true", help="Show tournament winner probabilities")
    parser.add_argument("--json", action="store_true", help="Output raw JSON instead of text")
    parser.add_argument("--markdown", action="store_true", help="Output Markdown report")
    parser.add_argument("--save", action="store_true", help="Save report to reports/group_advancement.md")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    import logging
    logging.basicConfig(level=logging.WARNING)

    print(f"Running {args.n:,} simulations...", file=sys.stderr, flush=True)

    if args.winner:
        sim = run_full_tournament_simulation(n_sims=args.n, seed=args.seed)
        if args.json:
            print(json.dumps(sim, indent=2))
        elif args.save:
            md_lines = [
                "# WC 2026 Tournament Winner Probabilities",
                "",
                f"**Simulations**: {sim['n_sims']:,}",
                "",
                "| Rank | Team | Win% | Implied Odds |",
                "|------|------|------|--------------|",
            ]
            for rank, (team, p) in enumerate(sim["champion_probs"].items(), 1):
                odds = f"+{round((1/p - 1)*100):,}" if p > 0 else "—"
                md_lines.append(f"| {rank} | {team} | {p:.1%} | {odds} |")
            out = REPO_ROOT / "reports" / "winner_probabilities.md"
            out.write_text("\n".join(md_lines))
            print(f"Saved to {out}", file=sys.stderr)
        else:
            print(render_winner_text(sim))
        return

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
