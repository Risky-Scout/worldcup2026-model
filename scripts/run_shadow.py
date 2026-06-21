"""
Shadow EGM runner driver.

Loads already-built processed parquet tables, runs ShadowEGMRunner for every
scheduled 2026 match, persists JSONL + team-ratings JSON, and writes
reports/shadow_ratings_report.csv for easy side-by-side review.

Safe to run after run_real_pipeline.py (reads same parquet, writes separate outputs).
Never touches data/published/ or any WizardOfOdds output.

Usage:
    python scripts/run_shadow.py
"""
from __future__ import annotations

import csv
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [shadow] %(levelname)s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

# Repo root on sys.path so wc2026 package imports work
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

REPORTS_DIR = REPO_ROOT / "reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)


def _safe_read(table: str) -> "pd.DataFrame":
    import pandas as pd
    from wc2026.data.storage import read_table
    try:
        return read_table(table)
    except FileNotFoundError:
        log.warning("Table '%s' not found — using empty DataFrame", table)
        return pd.DataFrame()


def load_tables() -> dict:
    """Load all processed parquet tables needed by the shadow runner."""
    log.info("Loading processed parquet tables...")
    tables = {
        "matches":     _safe_read("matches"),
        "odds":        _safe_read("odds"),
        "team_stats":  _safe_read("team_stats"),
        "injuries":    _safe_read("injuries"),
        "futures":     _safe_read("futures"),
        "rosters":     _safe_read("rosters"),
        "best_players": _safe_read("best_players"),
    }
    for name, df in tables.items():
        log.info("  %-15s %d rows", name, len(df))
    return tables


def get_scheduled_2026(matches_df: "pd.DataFrame") -> "pd.DataFrame":
    """Return all named scheduled 2026 matches."""
    sched = matches_df[
        (matches_df["season"] == 2026) &
        (matches_df["status"] == "scheduled")
    ].copy()
    # Filter out TBD placeholders (W73, L101, 1A, 2B, etc.)
    def _is_tbd(name: str) -> bool:
        if not name or not isinstance(name, str):
            return True
        s = name.strip()
        if len(s) <= 4 and len(s) >= 2 and s[0] in "WL" and s[1:].isdigit():
            return True
        if len(s) == 2 and s[0].isdigit() and s[1].isalpha():
            return True
        return False

    sched = sched[
        ~sched["home_team"].apply(_is_tbd) &
        ~sched["away_team"].apply(_is_tbd)
    ]
    return sched.sort_values("match_datetime").reset_index(drop=True)


def run_shadow(tables: dict) -> list[dict]:
    """Run shadow EGM runner for all scheduled 2026 matches. Returns per-match summaries."""
    import pandas as pd
    from wc2026.models.shadow_egm_runner import ShadowEGMRunner

    matches_df = tables["matches"]
    odds_df = tables["odds"]
    team_stats_df = tables["team_stats"]
    injuries_df = tables.get("injuries", pd.DataFrame())
    futures_df = tables.get("futures", pd.DataFrame())

    # Completed matches used for rating fitting
    completed = matches_df[
        matches_df["status"] == "completed"
    ].copy() if not matches_df.empty else pd.DataFrame()

    sched = get_scheduled_2026(matches_df)
    log.info("Found %d named scheduled 2026 matches", len(sched))

    runner = ShadowEGMRunner()
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    summaries = []

    for idx, row in sched.iterrows():
        match_id = int(row.get("match_id", idx))
        home_team = str(row["home_team"])
        away_team = str(row["away_team"])

        try:
            pred = runner.run_match(
                match_id=match_id,
                home_team=home_team,
                away_team=away_team,
                home_team_id=int(row.get("home_team_id", 0) or 0),
                away_team_id=int(row.get("away_team_id", 0) or 0),
                home_country_code=str(row.get("home_country_code", "") or ""),
                away_country_code=str(row.get("away_country_code", "") or ""),
                matches_history_df=completed,
                odds_df=odds_df,
                injuries_df=injuries_df,
                lineups_df=pd.DataFrame(),
                player_stats_df=pd.DataFrame(),
                team_stats_df=team_stats_df,
                futures_df=futures_df,
                match_row=row.to_dict(),
                stadium_row=None,
                home_standing=None,
                away_standing=None,
                home_match_dates=[],
                away_match_dates=[],
                live_lambda_home=None,
                live_lambda_away=None,
                prediction_timestamp=datetime.now(timezone.utc),
            )
            runner.persist(pred, date_str=date_str)
            summaries.append({
                "match_id": match_id,
                "home_team": home_team,
                "away_team": away_team,
                "match_datetime": str(row.get("match_datetime", ""))[:16],
                "home_neutral_egm": round(pred.home_neutral_egm, 3),
                "away_neutral_egm": round(pred.away_neutral_egm, 3),
                "match_egm": round(pred.match_expected_goal_margin, 3),
                "egm_lambda_home": round(pred.egm_lambda_home, 3),
                "egm_lambda_away": round(pred.egm_lambda_away, 3),
                "sources": ",".join(pred.sources_used),
                "model_version": pred.model_version,
            })
            log.info("  [%3d] %-22s vs %-22s  EGM=%.3f  λH=%.2f λA=%.2f",
                     len(summaries), home_team, away_team,
                     pred.match_expected_goal_margin,
                     pred.egm_lambda_home, pred.egm_lambda_away)
        except Exception as exc:
            log.warning("  FAILED %s vs %s: %s", home_team, away_team, exc)

    return summaries


def collect_team_ratings(summaries: list[dict]) -> list[dict]:
    """
    Aggregate per-match EGM predictions into per-team ratings for the CSV report.
    Uses the home_neutral_egm as the team's neutral EGM estimate.
    """
    from collections import defaultdict
    team_egms: dict[str, list[float]] = defaultdict(list)

    for s in summaries:
        team_egms[s["home_team"]].append(s["home_neutral_egm"])
        team_egms[s["away_team"]].append(s["away_neutral_egm"])

    rows = []
    for team, egms in team_egms.items():
        rows.append({
            "team": team,
            "pi_composite": round(sum(egms) / len(egms), 4),
            "n_matches": len(egms),
            "avg_egm_vs_average": round(sum(egms) / len(egms), 4),
        })
    rows.sort(key=lambda r: r["pi_composite"], reverse=True)
    for i, r in enumerate(rows, start=1):
        r["rank"] = i
    return rows


def write_shadow_ratings_report(summaries: list[dict], team_ratings: list[dict]) -> Path:
    """Write reports/shadow_ratings_report.csv with per-team strength summary."""
    out_path = REPORTS_DIR / "shadow_ratings_report.csv"
    fieldnames = ["rank", "team", "pi_composite", "avg_egm_vs_average", "n_matches"]
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(team_ratings)
    log.info("Shadow ratings report: %s  (%d teams)", out_path, len(team_ratings))
    return out_path


def write_shadow_match_report(summaries: list[dict]) -> Path:
    """Write reports/shadow_match_predictions.csv with per-match EGM outputs."""
    out_path = REPORTS_DIR / "shadow_match_predictions.csv"
    if not summaries:
        return out_path
    fieldnames = list(summaries[0].keys())
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(summaries)
    log.info("Shadow match predictions: %s  (%d matches)", out_path, len(summaries))
    return out_path


def main():
    log.info("=== Shadow EGM Runner ===")
    tables = load_tables()

    if tables["matches"].empty:
        log.error("matches table is empty — run 'make build-dataset' first")
        sys.exit(1)

    summaries = run_shadow(tables)
    log.info("Shadow runner complete: %d predictions", len(summaries))

    if summaries:
        team_ratings = collect_team_ratings(summaries)
        write_shadow_ratings_report(summaries, team_ratings)
        write_shadow_match_report(summaries)
    else:
        log.warning("No shadow predictions produced — check logs above")

    log.info("Done.")


if __name__ == "__main__":
    main()
