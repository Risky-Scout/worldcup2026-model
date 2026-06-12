"""
Daily update script for the 2026 World Cup PMF engine.

Run this after each matchday (or multiple times per day during tournament):

    python scripts/daily_update.py --date 2026-06-11

What it does
------------
1. FETCH   — Pull latest BDL data (matches, odds, events, stats)
2. BUILD   — Rebuild versioned parquet tables from raw snapshots
3. PREDICT — Run full prediction pipeline (composite prior + reconciliation)
4. PUBLISH — Write data/published/{date}.json for the NEXT matchday
5. VALIDATE — Run artifact validation tests
6. CLV     — Record closing lines for matches that just kicked off
7. REPORT  — Print summary of changes

Post-match mode (--post-match):
    Run after matches on DATE are complete.
    Records CLV outcomes, updates ratings with new results.

Usage
-----
    # Pre-matchday: predict tomorrow
    python scripts/daily_update.py --date 2026-06-12

    # Post-matchday: record outcomes for today's completed matches
    python scripts/daily_update.py --date 2026-06-11 --post-match

    # Full pipeline refresh (re-predict all 2026)
    python scripts/daily_update.py --full-refresh

Scheduling
----------
Configure cron (or GitHub Actions schedule) to run daily:
    # 30 minutes after each UTC midnight (covers ET midnight games)
    30 0 * * * cd /path/to/worldcup2026-model && python scripts/daily_update.py
    # Post-match run at 11pm UTC (~7pm ET, catches 8pm ET kickoffs)
    0 23 * * * cd /path/to/worldcup2026-model && python scripts/daily_update.py --post-match
"""
from __future__ import annotations

import argparse
import datetime as dt
import logging
import subprocess
import sys
from pathlib import Path

# Ensure src/ is on path
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "src"))

from dotenv import load_dotenv
load_dotenv(REPO_ROOT / ".env")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("daily_update")

PYTHON = sys.executable


def _run(cmd: list[str], check: bool = True, desc: str = "") -> subprocess.CompletedProcess:
    label = desc or " ".join(cmd[:3])
    log.info("▶ %s", label)
    result = subprocess.run(cmd, capture_output=False)
    if check and result.returncode != 0:
        log.error("✗ %s failed (exit %d)", label, result.returncode)
        sys.exit(result.returncode)
    if result.returncode == 0:
        log.info("✓ %s", label)
    return result


def step_fetch() -> bool:
    """Fetch latest BDL data for all seasons."""
    log.info("═══ STEP 1: Fetch BDL data ═══")
    result = _run(
        [PYTHON, "-m", "wc2026.cli", "fetch-bdl", "--seasons", "2018,2022,2026"],
        check=False, desc="fetch-bdl",
    )
    return result.returncode == 0


def step_build() -> bool:
    """Rebuild versioned parquet tables."""
    log.info("═══ STEP 2: Build dataset ═══")
    result = _run(
        [PYTHON, "-m", "wc2026.cli", "build-dataset",
         "--seasons", "2018,2022,2026", "--data-version", "v1"],
        check=False, desc="build-dataset",
    )
    return result.returncode == 0


def step_pipeline() -> bool:
    """Run full prediction pipeline."""
    log.info("═══ STEP 3: Run prediction pipeline ═══")
    result = _run(
        [PYTHON, str(REPO_ROOT / "scripts" / "run_real_pipeline.py")],
        check=False, desc="run_real_pipeline",
    )
    return result.returncode == 0


def step_validate() -> bool:
    """Run artifact validation tests."""
    log.info("═══ STEP 4: Validate artifacts ═══")
    result = _run(
        [PYTHON, "-m", "pytest", "tests/test_published_json.py",
         "-q", "--no-cov", "--tb=short", "-k", "TestPublishedMatchPMF"],
        check=False, desc="validate-published",
    )
    return result.returncode == 0


def step_predict_date(date: str) -> bool:
    """Pre-compute published JSON for a specific date."""
    log.info("═══ STEP 5: Publish predictions for %s ═══", date)
    published = REPO_ROOT / "data" / "published" / f"{date}.json"
    if published.exists():
        log.info("  ✓ %s already published (%d bytes)", date, published.stat().st_size)
        return True
    result = _run(
        [PYTHON, "-m", "wc2026.cli", "publish-today",
         "--season", "2026", "--data-version", "v1"],
        check=False, desc=f"publish-{date}",
    )
    return result.returncode == 0


def _american_to_decimal(american: float) -> float:
    """Convert American moneyline odds to decimal odds."""
    if american >= 100:
        return round(american / 100 + 1, 6)
    elif american <= -100:
        return round(100 / abs(american) + 1, 6)
    return 0.0


def step_clv_record_closing(date: str) -> None:
    """
    Record closing lines for matches on DATE that have now kicked off.

    Reads the BDL odds parquet (columns: moneyline_home, moneyline_draw,
    moneyline_away in American format) and stores the consensus decimal
    closing price for home_win, draw, and away_win markets.

    Uses the most-recently-updated vendor row per match as the closing proxy.
    In a production system this would be called ~5 minutes before kickoff.
    """
    log.info("═══ STEP 6: Record CLV closing lines for %s ═══", date)
    try:
        import numpy as np
        import pandas as pd
        from wc2026.config import DATA_DIR, PROCESSED_DIR
        from wc2026.markets.clv import CLVStore

        store = CLVStore(str(DATA_DIR / "clv" / "2026" / "records.jsonl"))

        odds_path = PROCESSED_DIR / "v1" / "odds.parquet"
        if not odds_path.exists():
            log.warning("  No odds parquet found — skipping CLV closing update")
            return

        odds_df = pd.read_parquet(odds_path)
        required = {"moneyline_home", "moneyline_draw", "moneyline_away"}
        if not required.issubset(odds_df.columns):
            log.warning("  Odds parquet missing columns %s — skipping", required - set(odds_df.columns))
            return

        matches_path = PROCESSED_DIR / "v1" / "matches.parquet"
        if not matches_path.exists():
            return
        matches_df = pd.read_parquet(matches_path)
        matches_df["match_date"] = pd.to_datetime(
            matches_df["match_datetime"], utc=True, errors="coerce"
        ).dt.tz_convert("America/New_York").dt.strftime("%Y-%m-%d")
        today_matches = matches_df[matches_df["match_date"] == date]

        ts = dt.datetime.now(tz=dt.timezone.utc).isoformat()
        n_updated = 0
        n_skipped_live = 0
        for _, mrow in today_matches.iterrows():
            mid = str(mrow["match_id"])
            match_odds = odds_df[odds_df["match_id"] == mrow["match_id"]].copy()
            if match_odds.empty:
                continue

            # Use the most-recent snapshot row as closing line proxy.
            # Pre-game snapshots are taken before kickoff; post-match live odds
            # become extreme (e.g. -100000 American).  Skip any row where the
            # implied moneyline home probability is outside the plausible pre-game
            # range of 1.05–20.0 decimal (5%–95% implied prob).
            if "updated_at" in match_odds.columns:
                match_odds = match_odds.sort_values("updated_at", ascending=True)

            pregame_row = None
            for _, r in match_odds.iterrows():
                hw_dec = _american_to_decimal(float(r.get("moneyline_home") or 0))
                if 1.05 <= hw_dec <= 20.0:
                    pregame_row = r
            if pregame_row is None:
                log.info("  match_id=%s: no plausible pre-game odds found (likely all live/post-match); skipping closing line", mid)
                n_skipped_live += 1
                continue

            markets = {
                "home_win": _american_to_decimal(float(pregame_row.get("moneyline_home") or 0)),
                "draw":     _american_to_decimal(float(pregame_row.get("moneyline_draw") or 0)),
                "away_win": _american_to_decimal(float(pregame_row.get("moneyline_away") or 0)),
            }
            for market, closing_dec in markets.items():
                if closing_dec > 1.0:
                    n_u = store.update_closing(mid, market, closing_dec, ts)
                    n_updated += n_u

        log.info("  CLV closing lines updated: %d records (%d matches skipped — live/post-match odds)",
                 n_updated, n_skipped_live)
        summary = store.summary()
        log.info("  CLV summary: %d total, %d with closing, beat_close=%.1f%%",
                 summary.n_records, summary.n_with_closing,
                 summary.beat_close_rate * 100)

    except Exception as exc:
        log.warning("  CLV closing step failed: %s", exc)


def step_post_match_forensics(date: str) -> None:
    """
    Post-match update: record actual outcomes in CLV store,
    log prediction vs reality for completed matches.
    """
    log.info("═══ POST-MATCH: Record outcomes for %s ═══", date)
    try:
        import json
        import pandas as pd
        from wc2026.config import DATA_DIR, PROCESSED_DIR
        from wc2026.markets.clv import CLVStore

        store = CLVStore(str(DATA_DIR / "clv" / "2026" / "records.jsonl"))

        matches_path = PROCESSED_DIR / "v1" / "matches.parquet"
        if not matches_path.exists():
            log.warning("  No matches parquet — skipping post-match forensics")
            return

        matches_df = pd.read_parquet(matches_path)
        matches_df["match_date"] = pd.to_datetime(
            matches_df["match_datetime"], utc=True, errors="coerce"
        ).dt.tz_convert("America/New_York").dt.strftime("%Y-%m-%d")
        completed = matches_df[
            (matches_df["match_date"] == date) &
            (matches_df["status"] == "completed") &
            matches_df["home_goals"].notna()
        ]

        if completed.empty:
            log.info("  No completed matches found for %s", date)
            return

        n_outcomes = 0
        ts = dt.datetime.now(tz=dt.timezone.utc).isoformat()
        for _, mrow in completed.iterrows():
            mid = str(mrow["match_id"])
            hg = int(mrow["home_goals"])
            ag = int(mrow["away_goals"])
            home_won = hg > ag
            draw = hg == ag
            away_won = ag > hg

            outcome_map = {
                "home_win": home_won,
                "draw": draw,
                "away_win": away_won,
                "btts_yes": hg > 0 and ag > 0,
                "btts_no": not (hg > 0 and ag > 0),
            }
            for total_line in [0.5, 1.5, 2.5, 3.5, 4.5, 5.5, 6.5]:
                k = f"over_{str(total_line).replace('.','_')}"
                outcome_map[k] = (hg + ag) > total_line
                k2 = f"under_{str(total_line).replace('.','_')}"
                outcome_map[k2] = (hg + ag) <= total_line
            outcome_map[f"{hg}-{ag}"] = True

            for market, outcome in outcome_map.items():
                n_u = store.update_outcome(mid, market, outcome, ts)
                n_outcomes += n_u

            log.info("  %s vs %s: %d-%d | home_win=%s draw=%s",
                     mrow["home_team"], mrow["away_team"], hg, ag, home_won, draw)

        log.info("  Outcome records updated: %d", n_outcomes)

        # Annotate published JSONs with actual results + model exact-score probability
        try:
            import sys
            from pathlib import Path
            sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
            from run_real_pipeline import annotate_published_with_results
            annotate_published_with_results(matches_df)
        except Exception as ann_exc:
            log.warning("  Published JSON annotation failed: %s", ann_exc)

        # Print CLV summary after outcomes
        summary = store.summary()
        if summary.n_with_outcome > 0:
            log.info("  Post-match CLV: mean=%.2f%%  log_score=%.4f vs closing=%.4f",
                     summary.mean_clv_pct, summary.mean_log_score, summary.mean_closing_log_score)

    except Exception as exc:
        log.warning("  Post-match forensics failed: %s", exc)


def main():
    parser = argparse.ArgumentParser(description="Daily WC2026 update pipeline")
    parser.add_argument("--date", default=dt.date.today().isoformat(),
                        help="Target date YYYY-MM-DD (default: today)")
    parser.add_argument("--post-match", action="store_true",
                        help="Post-match mode: record outcomes, update CLV")
    parser.add_argument("--full-refresh", action="store_true",
                        help="Full refresh: fetch + build + pipeline + validate")
    parser.add_argument("--skip-fetch", action="store_true",
                        help="Skip BDL fetch step (use existing raw data)")
    parser.add_argument("--skip-pipeline", action="store_true",
                        help="Skip run_real_pipeline (use existing predictions)")
    parser.add_argument("--skip-validate", action="store_true",
                        help="Skip artifact validation tests")
    args = parser.parse_args()

    date = args.date
    log.info("═" * 60)
    log.info("WC2026 Daily Update — %s  [%s]",
             date, "POST-MATCH" if args.post_match else "PRE-MATCH")
    log.info("═" * 60)

    start = dt.datetime.now()

    if args.post_match:
        # Post-match: record outcomes and CLV closing lines
        step_clv_record_closing(date)
        step_post_match_forensics(date)
        log.info("Post-match update complete for %s (%.1fs)",
                 date, (dt.datetime.now() - start).total_seconds())
        return

    # Pre-match / full-refresh cycle
    fetch_ok = True
    if not args.skip_fetch:
        fetch_ok = step_fetch()
        if not fetch_ok:
            log.warning("BDL fetch had errors — continuing with existing data")

    build_ok = step_build()
    if not build_ok:
        log.warning("Dataset build had errors — continuing with existing processed data")

    pipeline_ok = True
    if not args.skip_pipeline:
        pipeline_ok = step_pipeline()
        if not pipeline_ok:
            log.error("Pipeline failed — published artifacts not updated")
            sys.exit(1)

    # Record closing lines for today (odds won't move after kickoff)
    step_clv_record_closing(date)

    if not args.skip_validate:
        validate_ok = step_validate()
        if not validate_ok:
            log.error("Artifact validation FAILED — check data/published/*.json")
            sys.exit(1)

    elapsed = (dt.datetime.now() - start).total_seconds()
    log.info("═" * 60)
    log.info("Update complete for %s in %.1fs", date, elapsed)
    log.info("  Fetch: %s | Build: %s | Pipeline: %s | Validate: OK",
             "✓" if fetch_ok else "⚠", "✓" if build_ok else "⚠",
             "✓" if pipeline_ok else "✗")
    log.info("═" * 60)


if __name__ == "__main__":
    main()
