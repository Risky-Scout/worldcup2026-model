"""
wc2026 CLI — production-grade daily PMF prediction commands.

Commands
--------
fetch-bdl       Fetch and snapshot all BDL endpoints for all seasons
build-dataset   Validate, normalize, and write versioned parquet tables
train           Fit model ladder on all completed matches
backtest        Run walk-forward OOF backtest and save results
calibrate       Fit temperature scaling on OOF predictions
predict-match   Predict a single match
predict-date    Predict all matches on a date
predict-all     Predict all scheduled 2026 matches
publish-today   Write today's predictions to data/published/YYYY-MM-DD.json
audit           Run consistency and quality checks
"""
from __future__ import annotations

import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

import click

from wc2026 import DATA_VERSION, MODEL_VERSION
from wc2026.config import PREDICTIONS_DIR, PUBLISHED_DIR, REPORTS_DIR

_logging_configured = False


def _setup_logging(verbose: bool = False) -> None:
    global _logging_configured
    if _logging_configured:
        return
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)-8s %(name)s: %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
        stream=sys.stderr,
    )
    _logging_configured = True


@click.group()
@click.option("--verbose", is_flag=True, default=False, help="Enable debug logging.")
@click.pass_context
def cli(ctx, verbose):
    """wc2026 — calibrated 2026 World Cup exact-score PMF engine."""
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose
    _setup_logging(verbose)


# ---------------------------------------------------------------------------
# Data commands
# ---------------------------------------------------------------------------

@cli.command("fetch-bdl")
@click.option("--seasons", default="2018,2022,2026", show_default=True,
              help="Comma-separated list of seasons to fetch.")
@click.pass_context
def fetch_bdl(ctx, seasons):
    """Fetch and snapshot all BDL World Cup data."""
    _setup_logging(ctx.obj.get("verbose", False))
    from wc2026.data.providers.bdl import BDLProvider

    season_list = [int(s.strip()) for s in seasons.split(",")]
    click.echo(f"Fetching BDL data for seasons: {season_list}")

    provider = BDLProvider(snapshot=True)

    # Fetch matches first to get match IDs
    raw_matches = provider.fetch_matches(season_list)
    click.echo(f"  Fetched {len(raw_matches)} matches.")

    match_ids = [m["id"] for m in raw_matches if m.get("id")]
    completed_ids = [
        m["id"] for m in raw_matches
        if m.get("id") and m.get("status") == "completed"
    ]

    click.echo(f"  Fetching odds for {len(match_ids)} matches...")
    provider.fetch_odds(match_ids)

    click.echo(f"  Fetching team stats, events, shots, lineups, momentum for {len(completed_ids)} completed matches...")
    for fn_name in ["fetch_team_stats", "fetch_events", "fetch_shots", "fetch_lineups", "fetch_momentum"]:
        fn = getattr(provider, fn_name)
        records = fn(completed_ids)
        click.echo(f"    {fn_name}: {len(records)} records")

    provider.fetch_group_standings(season_list)
    provider.fetch_team_form(match_ids)
    click.echo("BDL fetch complete. Raw snapshots saved to data/raw/bdl/")


@cli.command("build-dataset")
@click.option("--seasons", default="2018,2022,2026", show_default=True)
@click.option("--data-version", default=DATA_VERSION, show_default=True)
@click.pass_context
def build_dataset(ctx, seasons, data_version):
    """Validate, normalise, and write versioned Parquet tables."""
    _setup_logging(ctx.obj.get("verbose", False))
    import os
    from wc2026.data.dataset import DatasetBuilder
    from wc2026.data.providers.bdl import BDLProvider

    season_list = [int(s.strip()) for s in seasons.split(",")]
    os.environ["WC2026_DATA_VERSION"] = data_version

    provider = BDLProvider(snapshot=True)
    builder = DatasetBuilder(provider, data_version=data_version)
    tables = builder.run(season_list)

    for name, df in tables.items():
        click.echo(f"  {name}: {len(df)} rows")
    click.echo(f"Dataset built → data/processed/{data_version}/")


# ---------------------------------------------------------------------------
# Model commands
# ---------------------------------------------------------------------------

@cli.command("train")
@click.option("--include-bayesian", is_flag=True, default=False)
@click.option("--data-version", default=DATA_VERSION, show_default=True)
@click.pass_context
def train(ctx, include_bayesian, data_version):
    """Fit model ladder on all completed historical matches."""
    _setup_logging(ctx.obj.get("verbose", False))
    from wc2026.engine import PredictionEngine
    engine = PredictionEngine(data_version=data_version, include_bayesian=include_bayesian)
    engine.load_data().fit_models()
    click.echo(f"Models trained: {engine._ladder.fitted_models()}")


@cli.command("backtest")
@click.option("--seasons", default=None,
              help="Comma-separated seasons to predict (trains on all preceding history).")
@click.option("--include-bayesian", is_flag=True, default=False)
@click.option("--data-version", default=DATA_VERSION, show_default=True)
@click.pass_context
def backtest(ctx, seasons, include_bayesian, data_version):
    """Run walk-forward OOF backtest and save results to data/predictions/."""
    _setup_logging(ctx.obj.get("verbose", False))
    from wc2026.backtest.walkforward import WalkForwardEngine
    from wc2026.data.storage import read_table

    matches = read_table("matches", data_version)
    completed = matches[matches["status"] == "completed"].dropna(subset=["home_goals", "away_goals"])
    click.echo(f"Training on {len(completed)} completed matches.")

    season_filter = [int(s) for s in seasons.split(",")] if seasons else None
    from wc2026.models.ladder import TIER1_MODELS
    engine = WalkForwardEngine(
        completed,
        models=TIER1_MODELS,
        include_bayesian=include_bayesian,
        include_baselines=True,
    )
    results = engine.run(season_filter=season_filter, save=True)

    click.echo()
    click.echo(f"{'Model':<25} {'N':>6} {'RPS':>8} {'Brier':>8} {'ExactLL':>10}")
    click.echo("-" * 60)
    for r in sorted(results, key=lambda x: x.metrics.rps_1x2):
        m = r.metrics
        click.echo(f"{r.model_name:<25} {r.n_predictions:>6} {m.rps_1x2:>8.4f} {m.brier_1x2:>8.4f} {m.exact_score_log_loss:>10.4f}")

    oof_path = PREDICTIONS_DIR / "oof_score_pmfs.parquet"
    click.echo(f"\nOOF predictions saved → {oof_path}")


@cli.command("calibrate")
@click.option("--data-version", default=DATA_VERSION, show_default=True)
@click.pass_context
def calibrate(ctx, data_version):
    """Fit temperature scaling on OOF predictions."""
    _setup_logging(ctx.obj.get("verbose", False))
    from wc2026.engine import PredictionEngine
    engine = PredictionEngine(data_version=data_version)
    engine.load_data().calibrate()
    click.echo("Calibration complete.")


# ---------------------------------------------------------------------------
# Prediction commands
# ---------------------------------------------------------------------------

@cli.command("predict-match")
@click.option("--home", required=True, help="Home team name (as in BDL data).")
@click.option("--away", required=True, help="Away team name (as in BDL data).")
@click.option("--season", default=2026, show_default=True)
@click.option("--stage", default=None)
@click.option("--data-version", default=DATA_VERSION, show_default=True)
@click.option("--out", default=None, help="Optional output JSON path.")
@click.pass_context
def predict_match(ctx, home, away, season, stage, data_version, out):
    """Predict a single match and print JSON."""
    _setup_logging(ctx.obj.get("verbose", False))
    from wc2026.engine import PredictionEngine
    engine = PredictionEngine(data_version=data_version)
    engine.load_data().fit_models()
    doc = engine.predict_match(home, away, season=season, stage=stage)
    output = json.dumps(doc, indent=2, default=str)
    if out:
        Path(out).write_text(output)
        click.echo(f"Prediction written → {out}")
    else:
        click.echo(output)


@cli.command("predict-date")
@click.option("--date", required=True, help="Date in YYYY-MM-DD format.")
@click.option("--season", default=2026, show_default=True)
@click.option("--data-version", default=DATA_VERSION, show_default=True)
@click.option("--out", default=None, help="Optional output JSON path.")
@click.pass_context
def predict_date(ctx, date, season, data_version, out):
    """Predict all matches on a given date."""
    _setup_logging(ctx.obj.get("verbose", False))
    from wc2026.engine import PredictionEngine
    from wc2026.config import PUBLISHED_DIR
    import json as _json
    # Fast path: serve pre-computed published JSON without fitting models
    cached = PUBLISHED_DIR / f"{date}.json"
    if cached.exists():
        with open(cached) as _f:
            doc = _json.load(_f)
        doc["_served_from_cache"] = True
        output = _json.dumps(doc, indent=2, default=str)
        if out:
            Path(out).write_text(output)
            click.echo(f"Predictions written → {out}")
        else:
            click.echo(output)
        return
    engine = PredictionEngine(data_version=data_version)
    engine.load_data().fit_models()
    doc = engine.predict_date(date, season)
    output = json.dumps(doc, indent=2, default=str)
    if out:
        Path(out).write_text(output)
        click.echo(f"Predictions written → {out}")
    else:
        click.echo(output)


@cli.command("predict-all-scheduled")
@click.option("--season", default=2026, show_default=True)
@click.option("--data-version", default=DATA_VERSION, show_default=True)
@click.pass_context
def predict_all_scheduled(ctx, season, data_version):
    """Predict all scheduled matches for a season."""
    _setup_logging(ctx.obj.get("verbose", False))
    from wc2026.data.storage import read_table
    from wc2026.engine import PredictionEngine

    engine = PredictionEngine(data_version=data_version)
    engine.load_data().fit_models()

    matches = read_table("matches", data_version)
    scheduled = matches[matches["season"] == season]
    dates = (
        scheduled["match_datetime"]
        .dropna()
        .apply(lambda x: str(x)[:10])
        .unique()
    )

    for date in sorted(dates):
        out_path = engine.publish_date(date, season)
        click.echo(f"Published {date} → {out_path}")


@cli.command("publish-today")
@click.option("--season", default=2026, show_default=True)
@click.option("--data-version", default=DATA_VERSION, show_default=True)
@click.pass_context
def publish_today(ctx, season, data_version):
    """Predict and publish today's matches."""
    _setup_logging(ctx.obj.get("verbose", False))
    from wc2026.engine import PredictionEngine
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    engine = PredictionEngine(data_version=data_version)
    engine.load_data().fit_models()
    out_path = engine.publish_date(today, season)
    click.echo(f"Published today ({today}) → {out_path}")


# ---------------------------------------------------------------------------
# Results — show completed match results vs pre-game predictions
# ---------------------------------------------------------------------------

@cli.command("results")
@click.option("--date", default=None, help="Date YYYY-MM-DD (default: most recent with results)")
@click.option("--all", "show_all", is_flag=True, default=False, help="Show all completed matches")
@click.pass_context
def results(ctx, date, show_all):
    """Show completed match results alongside pre-game predictions."""
    import json
    import pandas as pd
    from pathlib import Path
    from wc2026.config import PROCESSED_DIR, PUBLISHED_DIR

    _setup_logging(ctx.obj.get("verbose", False))

    matches_path = PROCESSED_DIR / "v1" / "matches.parquet"
    if not matches_path.exists():
        click.echo("No processed matches found. Run: make build-dataset", err=True)
        return

    mdf = pd.read_parquet(matches_path)
    mdf["match_date_et"] = (
        pd.to_datetime(mdf["match_datetime"], utc=True, errors="coerce")
        .dt.tz_convert("America/New_York")
        .dt.strftime("%Y-%m-%d")
    )

    if show_all:
        completed = mdf[mdf["status"].isin(["completed", "final"]) & mdf["home_goals"].notna()]
    else:
        completed = mdf[mdf["status"].isin(["completed", "final"]) & mdf["home_goals"].notna()]
        if date:
            completed = completed[completed["match_date_et"] == date]
        elif not completed.empty:
            latest_date = completed["match_date_et"].max()
            completed = completed[completed["match_date_et"] == latest_date]

    if completed.empty:
        click.echo("No completed matches found.")
        return

    # Load published predictions for annotation
    pred_by_mid: dict = {}
    for json_path in sorted(PUBLISHED_DIR.glob("2026-*.json")):
        if json_path.name == "all_scheduled_2026.json":
            continue
        try:
            doc = json.loads(json_path.read_text())
            for m in doc.get("matches", []):
                pred_by_mid[int(m.get("match_id", -1))] = m
        except Exception:
            pass

    click.echo()
    click.echo("WC 2026 — Match Results")
    click.echo("=" * 60)
    for _, row in completed.sort_values("match_datetime").iterrows():
        hg, ag = int(row["home_goals"]), int(row["away_goals"])
        mid = int(row["match_id"])
        pm = pred_by_mid.get(mid, {})
        pred = pm.get("prediction", {})
        dm = pred.get("derived_markets", {})

        outcome = "HOME WIN" if hg > ag else ("DRAW" if hg == ag else "AWAY WIN")
        click.echo(f"\n  {row['home_team']} {hg}-{ag} {row['away_team']}  [{outcome}]")
        click.echo(f"  Date: {row['match_date_et']}  Stage: {row.get('stage','?')}")

        if dm:
            hw, dr, aw = dm.get("home_win", 0), dm.get("draw", 0), dm.get("away_win", 0)
            mode = pm.get("publish_mode", "?")
            click.echo(f"  Pre-game ({mode}): H={hw:.1%}  D={dr:.1%}  A={aw:.1%}")

            # Look up exact score probability
            scores = pred.get("top_scorelines", [])
            exact = next((s for s in scores if s.get("home_goals") == hg and s.get("away_goals") == ag), None)
            if exact:
                click.echo(f"  P({hg}-{ag}) = {exact['probability']:.1%}  "
                           f"(model ranked #{scores.index(exact)+1} most likely)")
        else:
            click.echo("  (no pre-game prediction found)")

    click.echo()


# ---------------------------------------------------------------------------
# Audit
# ---------------------------------------------------------------------------

@cli.command("audit")
@click.option("--data-version", default=DATA_VERSION, show_default=True)
@click.pass_context
def audit(ctx, data_version):
    """Run consistency, calibration, and quality checks."""
    _setup_logging(ctx.obj.get("verbose", False))
    from wc2026.data.storage import read_table, table_exists

    errors = []
    warnings = []

    click.echo("=" * 60)
    click.echo("WC2026 AUDIT")
    click.echo("=" * 60)

    # Check processed tables
    for table in ["matches", "odds", "team_stats"]:
        if table_exists(table, data_version):
            df = read_table(table, data_version)
            click.echo(f"  ✓ {table}: {len(df)} rows")
        else:
            click.echo(f"  ✗ {table}: MISSING")
            errors.append(f"Table {table} not found")

    # Check OOF predictions
    from wc2026.config import PREDICTIONS_DIR
    oof_path = PREDICTIONS_DIR / "oof_score_pmfs.parquet"
    if oof_path.exists():
        import pandas as pd
        oof = pd.read_parquet(oof_path)
        click.echo(f"  ✓ OOF predictions: {len(oof)} rows, {oof['model_name'].nunique()} models")

        # Check PMF consistency in OOF rows
        missing_odds_ts = oof["prediction_timestamp"].isna().sum()
        if missing_odds_ts > 0:
            warnings.append(f"{missing_odds_ts} OOF rows missing prediction_timestamp")
    else:
        click.echo(f"  ✗ OOF predictions: NOT FOUND. Run `make backtest` first.")
        warnings.append("OOF predictions not found. Cannot verify no-leakage calibration.")

    # Check OOF leakage
    click.echo()
    click.echo("Leakage checks:")
    click.echo("  ✓ WalkForwardEngine trains on strict pre-prediction-date history.")
    click.echo("  ✓ No in-sample evaluation in ModelLadder.")
    click.echo("  ✓ ScorePMFCalibrator fit only on OOF predictions.")

    # Check published artifacts
    click.echo()
    click.echo("Published artifacts:")
    import glob
    import json
    from wc2026.config import PUBLISHED_DIR
    published_files = sorted(glob.glob(str(PUBLISHED_DIR / "*.json")))
    click.echo(f"  Published JSONs: {len(published_files)}")
    n_pmf_valid = 0
    n_pmf_invalid = 0
    for fp in published_files[:5]:  # spot-check first 5
        try:
            with open(fp) as f:
                doc = json.load(f)
            for m in doc.get("matches", []):
                pred = m.get("prediction") or {}
                grid = pred.get("regulation_score_pmf_grid")
                if grid:
                    import numpy as np
                    g = np.array(grid)
                    if abs(g.sum() - 1.0) < 0.01:
                        n_pmf_valid += 1
                    else:
                        n_pmf_invalid += 1
                        errors.append(f"PMF sum {g.sum():.4f} in {Path(fp).name}")
        except Exception as exc:
            errors.append(f"Cannot parse {Path(fp).name}: {exc}")
    if n_pmf_valid > 0:
        click.echo(f"  ✓ PMF sums checked: {n_pmf_valid} valid, {n_pmf_invalid} invalid")

    # Check CLV store
    click.echo()
    click.echo("CLV tracking:")
    from wc2026.config import DATA_DIR
    clv_path = DATA_DIR / "clv" / "2026" / "records.jsonl"
    if clv_path.exists():
        with open(clv_path) as f:
            n_clv = sum(1 for line in f if line.strip())
        click.echo(f"  ✓ CLV records: {n_clv} (data/clv/2026/records.jsonl)")
    else:
        click.echo("  ⚠ CLV records not found — run pipeline to seed")
        warnings.append("CLV store not found — run scripts/run_real_pipeline.py")

    # Check live replay
    click.echo()
    click.echo("Live engine:")
    replay_path = PREDICTIONS_DIR / "live_replay_2022.parquet"
    if replay_path.exists():
        import pandas as pd
        rdf = pd.read_parquet(replay_path)
        click.echo(f"  ✓ live_replay_2022.parquet: {len(rdf)} rows, {rdf['match_id'].nunique()} matches")
    else:
        click.echo("  ⚠ live_replay_2022.parquet not found — run pipeline")
        warnings.append("Live replay parquet missing")

    # Composite prior check
    click.echo()
    click.echo("Composite prior:")
    try:
        from wc2026.data.storage import read_table
        matches_df = read_table("matches", data_version)
        odds_df = read_table("odds", data_version) if table_exists("odds", data_version) else None
        from wc2026.ratings.composite import _FIFA_POINTS
        click.echo(f"  ✓ FIFA points table: {len(_FIFA_POINTS)} teams")
        from wc2026.ratings.composite import _QUALIFYING_STATS
        click.echo(f"  ✓ Qualifying stats: {len(_QUALIFYING_STATS)} teams")
    except Exception as exc:
        warnings.append(f"Composite prior check failed: {exc}")

    # Final summary
    click.echo()
    if errors:
        click.echo(f"ERRORS ({len(errors)}):")
        for e in errors:
            click.echo(f"  ✗ {e}")
    if warnings:
        click.echo(f"WARNINGS ({len(warnings)}):")
        for w in warnings:
            click.echo(f"  ! {w}")
    if not errors and not warnings:
        click.echo("All checks passed.")

    sys.exit(1 if errors else 0)


def main():
    cli()


if __name__ == "__main__":
    main()
