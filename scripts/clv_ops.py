"""CLV operations script — closing lines, outcomes, summary reports."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent.parent / ".env")


def cmd_summary():
    from wc2026.markets.clv import CLVStore
    from wc2026.config import DATA_DIR
    store = CLVStore(str(DATA_DIR / "clv" / "2026" / "records.jsonl"))
    s = store.summary()
    print(s.to_markdown())
    print()
    print(f"Records: {s.n_records}  |  With closing: {s.n_with_closing}"
          f"  |  Beat close: {s.n_beat_close}/{s.n_with_closing}"
          f"  |  Mean CLV: {s.mean_clv_pct:+.3f}%")


def cmd_close(date: str):
    """Try to record closing lines from current BDL odds snapshot for DATE matches."""
    import datetime as dt
    import pandas as pd
    from wc2026.markets.clv import CLVStore
    from wc2026.config import DATA_DIR, PROCESSED_DIR

    store = CLVStore(str(DATA_DIR / "clv" / "2026" / "records.jsonl"))
    matches_path = PROCESSED_DIR / "v1" / "matches.parquet"
    odds_path = PROCESSED_DIR / "v1" / "odds.parquet"

    if not matches_path.exists():
        print(f"No matches parquet found — run make build-dataset first")
        return

    matches_df = pd.read_parquet(matches_path)
    matches_df["match_date"] = (
        pd.to_datetime(matches_df["match_datetime"], utc=True, errors="coerce")
        .dt.tz_convert("America/New_York")
        .dt.strftime("%Y-%m-%d")
    )
    today_matches = matches_df[matches_df["match_date"] == date]

    if today_matches.empty:
        print(f"No matches found for {date}")
        return

    if not odds_path.exists():
        print("No odds parquet found — run make fetch-bdl first")
        return

    odds_df = pd.read_parquet(odds_path)
    ts = dt.datetime.now(tz=dt.timezone.utc).isoformat()

    n_updated = 0
    for _, mrow in today_matches.iterrows():
        mid = str(mrow["match_id"])
        home = str(mrow.get("home_team", ""))
        away = str(mrow.get("away_team", ""))

        match_odds = odds_df[odds_df["match_id"] == mrow["match_id"]].copy()
        if match_odds.empty:
            print(f"  No odds for {home} vs {away} (match_id={mid})")
            continue

        # Sort by freshest odds
        if "updated_at" in match_odds.columns:
            match_odds = match_odds.sort_values("updated_at", ascending=False)

        # Home win closing price
        hw = match_odds[
            match_odds.get("outcome_name", pd.Series(dtype=str))
            .str.lower().isin(["home", "home win", "1"])
        ].head(1)
        if not hw.empty:
            dec = float(hw.iloc[0].get("decimal_odds", 0) or 0)
            if dec > 1.0:
                n = store.update_closing(mid, "home_win", dec, ts)
                n_updated += n

        # Away win closing price
        aw = match_odds[
            match_odds.get("outcome_name", pd.Series(dtype=str))
            .str.lower().isin(["away", "away win", "2"])
        ].head(1)
        if not aw.empty:
            dec = float(aw.iloc[0].get("decimal_odds", 0) or 0)
            if dec > 1.0:
                n = store.update_closing(mid, "away_win", dec, ts)
                n_updated += n

        print(f"  {home} vs {away}: {n_updated} CLV records updated")

    s = store.summary()
    print(f"\nCLV: {s.n_records} total, {s.n_with_closing} with closing,"
          f" beat_close={s.beat_close_rate:.1%}")


def cmd_record_outcome(match_id: str, home_goals: int, away_goals: int):
    """Record actual outcomes for a completed match."""
    import datetime as dt
    from wc2026.markets.clv import CLVStore
    from wc2026.config import DATA_DIR

    store = CLVStore(str(DATA_DIR / "clv" / "2026" / "records.jsonl"))
    ts = dt.datetime.now(tz=dt.timezone.utc).isoformat()
    hg, ag = home_goals, away_goals

    outcome_map = {
        "home_win": hg > ag,
        "draw": hg == ag,
        "away_win": ag > hg,
        "btts_yes": hg > 0 and ag > 0,
        "btts_no": not (hg > 0 and ag > 0),
        f"{hg}-{ag}": True,
    }
    for line in [0.5, 1.5, 2.5, 3.5, 4.5, 5.5, 6.5]:
        outcome_map[f"over_{str(line).replace('.','_')}"] = (hg + ag) > line

    n_total = 0
    for market, outcome in outcome_map.items():
        n = store.update_outcome(match_id, market, outcome, ts)
        n_total += n

    print(f"Match {match_id} ({hg}-{ag}): {n_total} CLV records updated")
    s = store.summary()
    if s.n_with_outcome > 0:
        print(f"CLV: mean={s.mean_clv_pct:+.3f}% | beat_close={s.beat_close_rate:.1%}"
              f" | {s.n_with_outcome} with outcome")


def main():
    parser = argparse.ArgumentParser(description="CLV operations")
    sub = parser.add_subparsers(dest="cmd")

    sub.add_parser("summary", help="Print CLV summary report")

    p_close = sub.add_parser("close", help="Record closing lines for a date")
    p_close.add_argument("--date", required=True, help="YYYY-MM-DD")

    p_outcome = sub.add_parser("outcome", help="Record match outcome")
    p_outcome.add_argument("--match-id", required=True)
    p_outcome.add_argument("--home-goals", type=int, required=True)
    p_outcome.add_argument("--away-goals", type=int, required=True)

    args = parser.parse_args()

    if args.cmd == "summary":
        cmd_summary()
    elif args.cmd == "close":
        cmd_close(args.date)
    elif args.cmd == "outcome":
        cmd_record_outcome(args.match_id, args.home_goals, args.away_goals)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
