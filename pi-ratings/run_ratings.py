"""
Standalone Pi ratings runner for World Cup 2026.

Reads:  ../data/processed/v1/matches.parquet
Writes: pi-ratings/ratings_report.csv          (always overwritten — latest)
        pi-ratings/ratings_report_YYYY-MM-DD.csv (dated archive)

Run:
    python pi-ratings/run_ratings.py
    python pi-ratings/run_ratings.py --parquet path/to/matches.parquet
"""
from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

# Allow running from repo root or from pi-ratings/ directory
_REPO_ROOT = Path(__file__).resolve().parent.parent
_DEFAULT_PARQUET = _REPO_ROOT / "data" / "processed" / "v1" / "matches.parquet"
_OUT_DIR = Path(__file__).resolve().parent

sys.path.insert(0, str(_REPO_ROOT / "pi-ratings"))
from pi_model import PiRatings


def load_matches(parquet_path: Path):
    """Load completed matches from parquet, sorted chronologically."""
    try:
        import pandas as pd
    except ImportError:
        raise SystemExit("pandas is required: pip install pandas pyarrow")

    df = pd.read_parquet(parquet_path)
    completed = df[
        (df["status"] == "completed")
        & df["home_goals"].notna()
        & df["away_goals"].notna()
    ].copy()

    # Sort by match datetime if available, else by any date column
    for col in ("match_datetime", "datetime", "date"):
        if col in completed.columns:
            completed = completed.sort_values(col)
            break

    return completed


def build_model(matches_df) -> PiRatings:
    """Fit Pi ratings on all completed matches in chronological order."""
    model = PiRatings(alpha=0.15, beta=0.10)
    for _, row in matches_df.iterrows():
        home = str(row.get("home_team") or row.get("home_name") or "")
        away = str(row.get("away_team") or row.get("away_name") or "")
        hg = int(row["home_goals"])
        ag = int(row["away_goals"])
        # Try to extract date string
        dt = row.get("match_datetime") or row.get("datetime") or row.get("date")
        dt_str = str(dt)[:10] if dt is not None else None
        if home and away:
            model.update(home, away, hg, ag, match_date=dt_str)
    return model


def write_report(model: PiRatings, out_dir: Path) -> Path:
    today = date.today().isoformat()
    latest = out_dir / "ratings_report.csv"
    dated = out_dir / f"ratings_report_{today}.csv"
    csv_text = model.to_csv()
    latest.write_text(csv_text, encoding="utf-8")
    dated.write_text(csv_text, encoding="utf-8")
    return latest


def main():
    parser = argparse.ArgumentParser(description="Pi ratings runner — full pipeline")
    parser.add_argument("--parquet", default=str(_DEFAULT_PARQUET),
                        help="Path to matches.parquet")
    parser.add_argument("--ratings-only", action="store_true",
                        help="Only compute ratings (skip calibration + predictions)")
    args = parser.parse_args()

    parquet_path = Path(args.parquet)
    if not parquet_path.exists():
        raise SystemExit(f"Parquet not found: {parquet_path}\n"
                         "Run 'make build-dataset' first.")

    # ── Step 1: Pi ratings ────────────────────────────────────────────────
    print("=" * 60)
    print("Step 1/4 — Fit Pi ratings on all completed matches")
    print("=" * 60)
    df = load_matches(parquet_path)
    total = len(df)
    seasons = sorted(df["season"].unique().tolist()) if "season" in df.columns else []
    print(f"  {total} completed matches loaded (seasons: {seasons})")

    model = build_model(df)
    n_teams = len(model.all_ratings())
    print(f"  {n_teams} teams rated")

    ratings_path = write_report(model, _OUT_DIR)
    print(f"  Ratings report: {ratings_path}")

    # Print top-15 preview
    print("\n  Top 15 teams by Pi composite (EGM vs average)")
    print(f"  {'Rank':<5} {'Team':<30} {'Pi Comp':>9} {'Pi Home':>9} {'Pi Away':>9} {'Matches':>8}")
    print("  " + "-" * 65)
    for rank, r in enumerate(model.all_ratings()[:15], start=1):
        print(f"  {rank:<5} {r.team:<30} {r.composite:>9.4f} {r.home_rating:>9.4f} {r.away_rating:>9.4f} {r.n_matches:>8}")
    print()

    if args.ratings_only:
        print("--ratings-only flag set: skipping calibration and predictions.")
        return

    # ── Step 2: Calibration ───────────────────────────────────────────────
    print("=" * 60)
    print("Step 2/4 — Daily calibration (rho + total_anchor)")
    print("=" * 60)
    import pandas as pd
    full_df = pd.read_parquet(parquet_path)
    from calibrate import calibrate, save as save_cal, append_log
    cal = calibrate(full_df)
    save_cal(cal)
    append_log(cal)
    print(f"  total_anchor = {cal.total_anchor:.4f}  ({cal.total_source}, n={cal.n_matches_used})")
    print(f"  rho          = {cal.rho:.4f}  ({cal.rho_source})")
    print(f"  log_likelihood = {cal.log_likelihood:.4f}")
    print(f"  rmse_total_goals = {cal.rmse_total_goals:.4f}")
    print()

    # ── Step 3: Predictions ───────────────────────────────────────────────
    print("=" * 60)
    print("Step 3/4 — Predict all scheduled 2026 matches")
    print("=" * 60)
    from predict_matches import build_ratings, run_predictions, write_json
    ratings = build_ratings(full_df)
    predictions = run_predictions(full_df, ratings, cal)
    print(f"  {len(predictions)} match predictions generated")
    json_path = write_json(predictions, _OUT_DIR)
    print(f"  JSON: {json_path}")
    print()

    # ── Step 4: Summary HTML ──────────────────────────────────────────────
    print("=" * 60)
    print("Step 4/4 — Write HTML summary report")
    print("=" * 60)
    from summary import write_summary
    html_path = write_summary(predictions, cal, _OUT_DIR)
    print(f"  HTML: {html_path}")
    print()

    # Final preview
    print("=" * 60)
    print("Prediction preview (first 5 matches)")
    print("=" * 60)
    for p in predictions[:5]:
        ml = p.markets
        print(f"  {p.match_datetime[:10]} | {p.home_team:22s} vs {p.away_team:22s} | "
              f"1X2: {ml.get('home_win',0):.4f}/{ml.get('draw',0):.4f}/{ml.get('away_win',0):.4f} | "
              f"O2.5: {ml.get('over_2_5',0):.4f} | BTTS: {ml.get('btts_yes',0):.4f}")
    print()
    print("All done.")


if __name__ == "__main__":
    main()
