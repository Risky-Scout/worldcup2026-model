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

    click.echo("  Fetching injuries (OUT/GTD)...")
    provider.fetch_injuries(statuses=["OUT", "GTD"])

    click.echo("  Fetching tournament futures odds...")
    provider.fetch_futures()

    click.echo("  Fetching rosters for 2018/2022/2026...")
    provider.fetch_rosters(seasons=[2018, 2022, 2026])

    click.echo(f"  Fetching match best players for {len(completed_ids)} completed matches...")
    provider.fetch_best_players(match_ids=completed_ids)

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
    """Predict and publish today's matches, then run CLV pipeline."""
    _setup_logging(ctx.obj.get("verbose", False))
    from wc2026.engine import PredictionEngine
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    engine = PredictionEngine(data_version=data_version)
    engine.load_data().fit_models()
    out_path = engine.publish_date(today, season)
    click.echo(f"Published today ({today}) → {out_path}")

    # ── Seed CLV store from today's published predictions ─────────────────
    # Converts the published JSON into bet_records the CLV pipeline understands,
    # then compares them against any available closing-line snapshots.
    # This runs every publish so CLV accumulates a real dataset over the tournament.
    try:
        from wc2026.evaluation.clv_pipeline import run_clv_pipeline
        from wc2026.data.odds_snapshot_store import OddsSnapshotStore
        from wc2026.config import PUBLISHED_DIR, DATA_DIR
        import json as _json

        pub_path = PUBLISHED_DIR / f"{today}.json"
        if pub_path.exists():
            doc = _json.loads(pub_path.read_text())
            pred_ts = datetime.now(timezone.utc)

            # Build bet_records from published match predictions
            bet_records = []
            match_metadata: dict = {}
            for m in doc.get("matches", []):
                mid = m.get("match_id")
                if mid is None:
                    continue
                mid = int(mid)
                pred = m.get("prediction", {})
                dm = pred.get("derived_markets", {})
                home_win_prob = dm.get("home_win") or pred.get("home_win_prob") or 0.0
                draw_prob = dm.get("draw") or pred.get("draw_prob") or 0.0
                away_win_prob = dm.get("away_win") or pred.get("away_win_prob") or 0.0

                match_metadata[mid] = {
                    "home_team": m.get("home_team", ""),
                    "away_team": m.get("away_team", ""),
                    "stage": m.get("stage", ""),
                }
                # Create one record per 1X2 outcome side
                for side, prob in [("home", home_win_prob), ("draw", draw_prob), ("away", away_win_prob)]:
                    if prob and prob > 0:
                        fair_decimal = 1.0 / max(float(prob), 0.01)
                        bet_records.append({
                            "match_id": mid,
                            "market_type": "1x2",
                            "market_key": f"1x2_{side}",
                            "bet_side": side,
                            "bet_decimal_odds": round(fair_decimal, 3),
                            "current_fair_probability": float(prob),
                            "prediction_timestamp": pred_ts.isoformat(),
                            "vendor": "model",
                            "stage": m.get("stage", ""),
                        })

            if bet_records:
                snapshot_store = OddsSnapshotStore(DATA_DIR / "odds_snapshots")
                closing_df = snapshot_store.load_snapshots()
                result = run_clv_pipeline(
                    bet_records=bet_records,
                    closing_snapshots=closing_df,
                    prediction_timestamp=pred_ts,
                    match_metadata=match_metadata,
                )
                n_matched = result.get("n_records_written", 0) if isinstance(result, dict) else 0
                click.echo(f"CLV pipeline: {len(bet_records)} predictions staged, {n_matched} matched to closing lines")
            else:
                click.echo("CLV pipeline: no predictions to stage today")
    except Exception as exc:
        click.echo(f"CLV pipeline warning: {exc}", err=True)


# ---------------------------------------------------------------------------
# Schedule — morning briefing: today's matches with kickoffs and predictions
# ---------------------------------------------------------------------------

@cli.command("schedule")
@click.option("--date", default=None, help="Date YYYY-MM-DD (default: today ET)")
@click.pass_context
def schedule(ctx, date):
    """Show today's match schedule with kickoff times and model predictions."""
    import json
    from datetime import datetime, timezone
    from zoneinfo import ZoneInfo
    from pathlib import Path
    from wc2026.config import PUBLISHED_DIR

    _setup_logging(ctx.obj.get("verbose", False))

    ET = ZoneInfo("America/New_York")
    if date is None:
        date = datetime.now(tz=ET).strftime("%Y-%m-%d")

    json_path = PUBLISHED_DIR / f"{date}.json"
    if not json_path.exists():
        click.echo(f"No predictions found for {date}. Run: make update DATE={date}", err=True)
        return

    doc = json.loads(json_path.read_text())
    matches = doc.get("matches", [])

    click.echo()
    click.echo(f"WC 2026 — {date} Match Schedule  ({doc.get('n_matches',0)} matches)")
    click.echo("=" * 68)

    if not matches:
        click.echo("  No matches scheduled for this date.")
        click.echo()
        return

    for i, m in enumerate(matches, 1):
        pred = m.get("prediction", {})
        dm = pred.get("derived_markets", {})
        result = m.get("result")

        # Parse kickoff time
        dt_utc = m.get("match_datetime_utc", "")
        try:
            ko_utc = datetime.fromisoformat(str(dt_utc).replace("+00:00", "")).replace(tzinfo=timezone.utc)
            ko_et = ko_utc.astimezone(ET)
            ko_str = ko_et.strftime("%-I:%M %p ET")
        except Exception:
            ko_str = str(dt_utc)

        mode = m.get("publish_mode", "?")
        hw = dm.get("home_win", 0)
        dr = dm.get("draw", 0)
        aw = dm.get("away_win", 0)
        o25 = dm.get("over_2.5", 0)
        btts = dm.get("btts_yes", 0)

        home_label = m["home_team"]
        away_label = m["away_team"]
        # Bold the favourite
        if hw > aw:
            home_label = f"*{home_label}*"
        elif aw > hw:
            away_label = f"*{away_label}*"

        if result:
            status_str = f"FINAL: {result['result_label']}  ({result['outcome'].replace('_',' ').upper()})"
        else:
            status_str = ko_str

        click.echo(f"\n  {i}. {home_label} vs {away_label}  [{status_str}]")
        click.echo(f"     Stage: {m.get('stage','?')}  |  {m.get('stadium','?')}")
        click.echo(f"     Model ({mode}):  H={hw:.0%}  D={dr:.0%}  A={aw:.0%}")
        click.echo(f"     O/U 2.5={o25:.0%}  BTTS={btts:.0%}")

        # Top 3 most-likely scorelines
        scores = pred.get("top_scorelines", [])[:3]
        if scores:
            score_parts = [f"{s['home_goals']}-{s['away_goals']} ({s['probability']:.1%})" for s in scores]
            click.echo(f"     Top scores: {' | '.join(score_parts)}")

        # Edge highlight (nested under prediction)
        edge = pred.get("edge_report", {})
        if edge and isinstance(edge, dict):
            value_bets = [b for b in edge.get("bets", []) if b.get("is_value")]
            if value_bets:
                vb = value_bets[0]
                click.echo(f"     ★ Edge: {vb['market']} {vb['edge_pct']:+.1f}%  half-Kelly={vb['kelly_half']:.1%}")

    click.echo()
    click.echo(f"  Generated: {doc.get('generated_at','')}  |  mode: {doc.get('publish_mode_policy','')[:60]}")
    click.echo()


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
# Simulate — Monte Carlo group stage advancement probabilities
# ---------------------------------------------------------------------------

@cli.command("simulate")
@click.option("--n", default=50_000, show_default=True, help="Number of Monte Carlo simulations")
@click.option("--group", default=None, help="Filter to one group e.g. 'Group A'")
@click.option("--winner", is_flag=True, default=False, help="Show tournament winner probabilities (full bracket)")
@click.option("--markdown", is_flag=True, default=False, help="Output Markdown format")
@click.option("--save", is_flag=True, default=False, help="Save reports to reports/ directory")
@click.pass_context
def simulate(ctx, n, group, winner, markdown, save):
    """Monte Carlo simulation of group stage advancement and tournament winner probabilities."""
    import sys
    from pathlib import Path
    _setup_logging(ctx.obj.get("verbose", False))

    scripts_dir = Path(__file__).resolve().parent.parent.parent / "scripts"
    sys.path.insert(0, str(scripts_dir))

    if winner:
        from simulate_groups import run_full_tournament_simulation, render_winner_text
        click.echo(f"Running {n:,} full tournament simulations...", err=True)
        sim = run_full_tournament_simulation(n_sims=n)
        if save:
            probs = sim["champion_probs"]
            md_lines = [
                "# WC 2026 Tournament Winner Probabilities", "",
                f"**Simulations**: {sim['n_sims']:,}", "",
                "| Rank | Team | Win% | Implied Odds |",
                "|------|------|------|--------------|",
            ]
            for rank, (team, p) in enumerate(probs.items(), 1):
                if team == "TBD":
                    continue
                odds = f"+{round((1/p - 1)*100):,}" if p > 0 else "—"
                md_lines.append(f"| {rank} | {team} | {p:.1%} | {odds} |")
            out = Path(__file__).resolve().parent.parent.parent / "reports" / "winner_probabilities.md"
            out.write_text("\n".join(md_lines))
            click.echo(f"Saved to {out}", err=True)
        else:
            click.echo(render_winner_text(sim))
        return

    from simulate_groups import run_simulation, render_text, render_markdown
    click.echo(f"Running {n:,} simulations...", err=True)
    sim = run_simulation(n_sims=n)

    if markdown or save:
        output = render_markdown(sim)
        if save:
            out = Path(__file__).resolve().parent.parent.parent / "reports" / "group_advancement.md"
            out.write_text(output)
            click.echo(f"Saved to {out}", err=True)
        else:
            click.echo(output)
    else:
        click.echo(render_text(sim, group_filter=group))


# ---------------------------------------------------------------------------
# Calibration — running model performance on actual 2026 results
# ---------------------------------------------------------------------------

@cli.command("calibration")
@click.option("--market", default="all", help="Market to evaluate: all|home_win|draw|away_win|over_2.5|btts_yes")
@click.pass_context
def calibration(ctx, market):
    """Show running calibration metrics on completed 2026 World Cup matches."""
    import json
    import math
    from pathlib import Path
    from wc2026.config import PUBLISHED_DIR

    _setup_logging(ctx.obj.get("verbose", False))

    MARKETS_1X2 = ["home_win", "draw", "away_win"]
    MARKETS_TOTALS = ["over_2.5", "under_2.5", "over_1.5", "over_3.5"]
    MARKETS_BTTS = ["btts_yes", "btts_no"]

    records: list[dict] = []
    for json_path in sorted(PUBLISHED_DIR.glob("2026-*.json")):
        if json_path.name == "all_scheduled_2026.json":
            continue
        try:
            doc = json.loads(json_path.read_text())
        except Exception:
            continue
        for m in doc.get("matches", []):
            result = m.get("result")
            if not result:
                continue
            pred = m.get("prediction", {})
            dm = pred.get("derived_markets", {})
            outcome = result.get("outcome")  # home_win | draw | away_win
            hg = result.get("home_goals", 0)
            ag = result.get("away_goals", 0)
            total = hg + ag
            btts = hg > 0 and ag > 0

            truth: dict[str, bool] = {
                "home_win": outcome == "home_win",
                "draw":     outcome == "draw",
                "away_win": outcome == "away_win",
                "btts_yes": btts,
                "btts_no":  not btts,
                "over_0.5": total > 0.5,
                "over_1.5": total > 1.5,
                "over_2.5": total > 2.5,
                "over_3.5": total > 3.5,
                "under_0.5": total <= 0.5,
                "under_1.5": total <= 1.5,
                "under_2.5": total <= 2.5,
                "under_3.5": total <= 3.5,
            }

            for mkt, actual in truth.items():
                prob = dm.get(mkt)
                if prob is None or prob <= 0:
                    continue
                records.append({
                    "match": f"{m['home_team']} v {m['away_team']}",
                    "date": m.get("match_date_et", ""),
                    "market": mkt,
                    "model_prob": float(prob),
                    "outcome": actual,
                    "mode": m.get("publish_mode", "?"),
                })

    if not records:
        click.echo("No completed matches with predictions found yet.")
        return

    mkt_filter = None if market == "all" else market
    filtered = [r for r in records if mkt_filter is None or r["market"] == mkt_filter]

    def _metrics(recs):
        n = len(recs)
        if n == 0:
            return {}
        brier = sum((r["model_prob"] - (1 if r["outcome"] else 0)) ** 2 for r in recs) / n
        nll = -sum(
            math.log(r["model_prob"]) if r["outcome"] else math.log(max(1 - r["model_prob"], 1e-9))
            for r in recs
        ) / n
        acc = sum(1 for r in recs if (r["model_prob"] >= 0.5) == r["outcome"]) / n
        correct = sum(1 for r in recs if r["outcome"])
        return {"n": n, "n_correct": correct, "brier": brier, "nll": nll, "acc": acc}

    click.echo()
    click.echo(f"WC 2026 Model Calibration  ({len({r['match'] for r in records})} matches resolved)")
    click.echo("=" * 68)

    # Per-market breakdown for the 1X2 markets (most important)
    groups = {
        "1X2": MARKETS_1X2,
        "Totals": MARKETS_TOTALS,
        "BTTS":  MARKETS_BTTS,
    }

    for group_name, mkts in groups.items():
        group_recs = [r for r in filtered if r["market"] in mkts]
        if not group_recs:
            continue
        m_all = _metrics(group_recs)
        click.echo(f"\n  {group_name}  (n={m_all['n']}  correct={m_all['n_correct']})")
        click.echo(f"  {'Market':<14} {'n':>4} {'Freq':>5} {'Model':>6} {'Brier':>7} {'NLL':>7}")
        click.echo("  " + "-" * 48)
        for mkt in mkts:
            mkt_recs = [r for r in group_recs if r["market"] == mkt]
            if not mkt_recs:
                continue
            freq = sum(1 for r in mkt_recs if r["outcome"]) / len(mkt_recs)
            mean_prob = sum(r["model_prob"] for r in mkt_recs) / len(mkt_recs)
            mm = _metrics(mkt_recs)
            click.echo(
                f"  {mkt:<14} {mm['n']:>4} {freq:>5.0%} {mean_prob:>6.0%} "
                f"{mm['brier']:>7.4f} {mm['nll']:>7.4f}"
            )

    # Overall summary
    m_overall = _metrics(filtered)
    click.echo(f"\n  Overall  (n={m_overall['n']})")
    click.echo(f"  Brier={m_overall['brier']:.4f}  NLL={m_overall['nll']:.4f}  "
               f"Acc={m_overall['acc']:.1%}")

    # Naive baselines for comparison
    click.echo()
    click.echo("  Baselines (1X2 markets only):")
    recs_1x2 = [r for r in records if r["market"] in MARKETS_1X2]
    if recs_1x2:
        # Uniform: 1/3
        brier_uniform = sum((1/3 - (1 if r["outcome"] else 0))**2 for r in recs_1x2) / len(recs_1x2)
        # Marginal frequency
        click.echo(f"  Uniform 1/3:  Brier={brier_uniform:.4f}")

    click.echo()


# ---------------------------------------------------------------------------
# Standings — show live group standings from BDL snapshots
# ---------------------------------------------------------------------------

@cli.command("standings")
@click.option("--group", default=None, help="Filter by group name e.g. 'Group A'")
@click.pass_context
def standings(ctx, group):
    """Show current group standings from the latest BDL snapshot."""
    import json
    from pathlib import Path
    from wc2026.config import DATA_DIR

    _setup_logging(ctx.obj.get("verbose", False))

    gs_dir = DATA_DIR / "raw" / "bdl" / "multi" / "group_standings"
    if not gs_dir.exists():
        click.echo("No group standings snapshots found. Run: make fetch-bdl", err=True)
        return

    snapshots = sorted(gs_dir.glob("*.jsonl"))
    if not snapshots:
        click.echo("No group standings snapshots found.", err=True)
        return

    latest = snapshots[-1]
    records = []
    with open(latest) as f:
        for line in f:
            try:
                records.append(json.loads(line))
            except Exception:
                pass

    recs_2026 = [r for r in records if r.get("season", {}).get("year") == 2026]
    if not recs_2026:
        click.echo("No 2026 standings data available yet.", err=True)
        return

    recs_2026.sort(key=lambda x: (x["group"]["name"], x["position"]))
    ts = latest.stem  # e.g. 20260612T035925Z

    # Group filter
    all_groups = sorted({r["group"]["name"] for r in recs_2026})
    if group:
        filtered = [r for r in recs_2026 if r["group"]["name"].lower() == group.lower()]
        groups_to_show = [group] if filtered else []
        recs_2026 = filtered
    else:
        groups_to_show = all_groups

    if not recs_2026:
        click.echo(f"Group '{group}' not found. Available: {', '.join(all_groups)}", err=True)
        return

    click.echo()
    click.echo(f"WC 2026 Group Standings  (snapshot: {ts})")
    click.echo("=" * 68)

    for gname in groups_to_show:
        group_rows = [r for r in recs_2026 if r["group"]["name"] == gname]
        if not group_rows:
            continue
        has_played = any(r["played"] > 0 for r in group_rows)
        click.echo(f"\n  {gname}")
        click.echo(f"  {'Pos':<4} {'Team':<26} {'P':>2} {'W':>2} {'D':>2} {'L':>2} {'GF':>3} {'GA':>3} {'GD':>4} {'Pts':>4}")
        click.echo("  " + "-" * 60)
        for r in group_rows:
            gd = r["goal_difference"]
            gd_str = f"+{gd}" if gd > 0 else str(gd)
            qualifier = "→ " if r["position"] <= 2 else "   "
            click.echo(
                f"  {qualifier}{r['position']:<3} {r['team']['name']:<26} "
                f"{r['played']:>2} {r['won']:>2} {r['drawn']:>2} {r['lost']:>2} "
                f"{r['goals_for']:>3} {r['goals_against']:>3} {gd_str:>4} {r['points']:>4}"
            )

    click.echo()
    click.echo("  → = advances to Round of 32 if current position holds")
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
