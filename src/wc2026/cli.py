"""
wc2026 command-line interface.

Commands
--------
wc2026 fetch         — Download and cache all BDL World Cup data
wc2026 train         — Fit the ensemble model and save it
wc2026 predict       — Pre-game scoreline probabilities
wc2026 live          — Live in-game prediction for a match ID
wc2026 calibrate     — Evaluate the model on holdout data
"""
from __future__ import annotations

import json
import logging
import pickle
from pathlib import Path

import click
from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table

load_dotenv()
console = Console()
logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

MODEL_PATH = Path("model.pkl")
SEASONS = [2018, 2022, 2026]


@click.group()
def cli():
    """2026 FIFA World Cup predictive model."""
    pass


# ------------------------------------------------------------------
# fetch
# ------------------------------------------------------------------

@cli.command()
@click.option("--seasons", default="2018,2022,2026", help="Comma-separated seasons.")
@click.option("--no-cache", is_flag=True, default=False, help="Force re-download.")
def fetch(seasons: str, no_cache: bool) -> None:
    """Download and cache all BDL match data."""
    from wc2026.data import DataFetcher

    season_list = [int(s.strip()) for s in seasons.split(",")]
    fetcher = DataFetcher()

    if no_cache:
        fetcher.clear_cache()
        console.print("[yellow]Cache cleared.[/yellow]")

    with console.status("Fetching matches …"):
        matches = fetcher.matches(seasons=season_list, force_refresh=no_cache)
    console.print(f"[green]✓ {len(matches)} matches fetched.[/green]")

    completed_ids = [m["id"] for m in matches if m.get("status") == "completed"]
    console.print(f"  {len(completed_ids)} completed matches.")

    with console.status("Fetching team match stats …"):
        stats = fetcher.team_match_stats(match_ids=completed_ids)
    console.print(f"[green]✓ {len(stats)} team-match stat rows.[/green]")

    with console.status("Fetching shot data …"):
        shots = fetcher.match_shots(match_ids=completed_ids)
    console.print(f"[green]✓ {len(shots)} shot events.[/green]")

    console.print("[bold green]Data fetch complete.[/bold green]")


# ------------------------------------------------------------------
# train
# ------------------------------------------------------------------

@cli.command()
@click.option("--seasons", default="2018,2022,2026", help="Comma-separated seasons.")
@click.option("--no-bayesian", is_flag=True, default=False, help="Skip Bayesian model (faster).")
@click.option("--output", default="model.pkl", type=str)
def train(seasons: str, no_bayesian: bool, output: str) -> None:
    """Fit the full ensemble model and save to disk."""
    from wc2026.data import DataFetcher, build_match_dataframe
    from wc2026.models import EnsembleModel

    season_list = [int(s.strip()) for s in seasons.split(",")]
    fetcher = DataFetcher()

    with console.status("Loading data …"):
        matches = fetcher.completed_matches(seasons=season_list)
        completed_ids = [m["id"] for m in matches]
        stats = fetcher.team_match_stats(match_ids=completed_ids) if completed_ids else []
        shots = fetcher.match_shots(match_ids=completed_ids) if completed_ids else []

    df = build_match_dataframe(matches, team_stats=stats, shots=shots)
    console.print(f"Training on [bold]{len(df)}[/bold] completed matches.")

    if len(df) < 5:
        console.print("[red]Not enough data to train. Run `wc2026 fetch` first.[/red]")
        raise SystemExit(1)

    with console.status("Training ensemble (this takes a few minutes) …"):
        model = EnsembleModel.from_dataframe(df, bayesian=not no_bayesian)

    out_path = Path(output)
    model.save(out_path)
    console.print(f"[green]✓ Model saved to {out_path}[/green]")
    console.print(f"  Teams: {len(model.teams())}")
    console.print(f"  Weights: {model._trainer.weights}")


# ------------------------------------------------------------------
# predict
# ------------------------------------------------------------------

@cli.command()
@click.argument("home_team")
@click.argument("away_team")
@click.option("--model", "model_path", default="model.pkl")
@click.option("--max-goals", default=10, type=int)
@click.option("--json-output", is_flag=True, default=False)
def predict(
    home_team: str,
    away_team: str,
    model_path: str,
    max_goals: int,
    json_output: bool,
) -> None:
    """Pre-game scoreline probabilities for HOME_TEAM vs AWAY_TEAM."""
    from wc2026.models import EnsembleModel
    from wc2026.predictions.pregame import pregame_predict

    model = EnsembleModel.load(model_path)
    result = pregame_predict(model, home_team, away_team, max_goals=max_goals)

    if json_output:
        click.echo(json.dumps(result, indent=2))
        return

    # Pretty print
    console.rule(f"[bold]{home_team} vs {away_team}[/bold]")

    # 1X2
    t = Table(title="Match Result")
    t.add_column("Outcome", style="bold")
    t.add_column("Probability", justify="right")
    t.add_row(f"{home_team} Win", f"{result['home_win']:.1%}")
    t.add_row("Draw", f"{result['draw']:.1%}")
    t.add_row(f"{away_team} Win", f"{result['away_win']:.1%}")
    console.print(t)

    # Goals markets
    t2 = Table(title="Goals Markets")
    t2.add_column("Market")
    t2.add_column("Probability", justify="right")
    for line in ["1_5", "2_5", "3_5"]:
        t2.add_row(f"Over {line.replace('_', '.')}", f"{result[f'over_{line}']:.1%}")
        t2.add_row(f"Under {line.replace('_', '.')}", f"{result[f'under_{line}']:.1%}")
    t2.add_row("BTTS Yes", f"{result['btts_yes']:.1%}")
    t2.add_row("BTTS No", f"{result['btts_no']:.1%}")
    console.print(t2)

    # Expected goals
    console.print(
        f"\nExpected goals: [cyan]{home_team} {result['home_xg']:.2f}[/cyan] "
        f"– [cyan]{result['away_xg']:.2f} {away_team}[/cyan]"
    )

    # Top scorelines
    t3 = Table(title="Top Scorelines")
    t3.add_column("Score")
    t3.add_column("Probability", justify="right")
    for s in result["top_scores"][:10]:
        t3.add_row(f"{s['home_goals']}-{s['away_goals']}", f"{s['probability']:.2%}")
    console.print(t3)


# ------------------------------------------------------------------
# live
# ------------------------------------------------------------------

@cli.command()
@click.argument("match_id", type=int)
@click.argument("home_team")
@click.argument("away_team")
@click.option("--model", "model_path", default="model.pkl")
@click.option("--json-output", is_flag=True, default=False)
def live(
    match_id: int,
    home_team: str,
    away_team: str,
    model_path: str,
    json_output: bool,
) -> None:
    """Live in-game prediction for MATCH_ID."""
    from wc2026.data import DataFetcher
    from wc2026.models import EnsembleModel
    from wc2026.predictions.live import LivePredictor

    model = EnsembleModel.load(model_path)
    fetcher = DataFetcher()
    predictor = LivePredictor(model, fetcher)

    result = predictor.predict(match_id, home_team, away_team)

    if json_output:
        out = {k: v for k, v in result.items() if k != "score_matrix"}
        click.echo(json.dumps(out, indent=2))
        return

    console.rule(
        f"[bold]LIVE: {home_team} {result['home_score']}-{result['away_score']} {away_team}[/bold]"
        f"  [dim]min {result['minute']}[/dim]"
    )
    t = Table(title="Updated Win Probabilities")
    t.add_column("Outcome", style="bold")
    t.add_column("Probability", justify="right")
    t.add_row(f"{home_team} Win", f"{result['home_win']:.1%}")
    t.add_row("Draw", f"{result['draw']:.1%}")
    t.add_row(f"{away_team} Win", f"{result['away_win']:.1%}")
    console.print(t)

    console.print(
        f"\nExpected remaining goals: "
        f"[cyan]{home_team} {result['home_xg_remaining']:.2f}[/cyan] "
        f"– [cyan]{result['away_xg_remaining']:.2f} {away_team}[/cyan]"
    )

    t2 = Table(title="Top Final Scorelines")
    t2.add_column("Score")
    t2.add_column("Probability", justify="right")
    for s in result["top_scores"][:10]:
        t2.add_row(f"{s['home_goals']}-{s['away_goals']}", f"{s['probability']:.2%}")
    console.print(t2)


# ------------------------------------------------------------------
# calibrate
# ------------------------------------------------------------------

@cli.command()
@click.option("--model", "model_path", default="model.pkl")
@click.option("--holdout-frac", default=0.2, type=float, help="Fraction of data for holdout.")
@click.option("--plot", is_flag=True, default=False)
def calibrate(model_path: str, holdout_frac: float, plot: bool) -> None:
    """Evaluate model calibration on held-out completed matches."""
    from wc2026.calibration import CalibrationReport
    from wc2026.data import DataFetcher, build_match_dataframe
    from wc2026.models import EnsembleModel

    fetcher = DataFetcher()
    model = EnsembleModel.load(model_path)

    matches = fetcher.completed_matches(seasons=SEASONS)
    completed_ids = [m["id"] for m in matches]
    stats = fetcher.team_match_stats(match_ids=completed_ids) if completed_ids else []
    df = build_match_dataframe(matches, team_stats=stats)

    cutoff = int(len(df) * (1 - holdout_frac))
    holdout = df.iloc[cutoff:].reset_index(drop=True)
    console.print(f"Evaluating on {len(holdout)} holdout matches.")

    report = CalibrationReport(model, holdout)
    report.evaluate()
    console.print(report)

    if plot:
        from wc2026.calibration.plots import plot_calibration_summary
        fig = plot_calibration_summary(report.per_match)
        out = Path("calibration_report.png")
        fig.savefig(out, dpi=150, bbox_inches="tight")
        console.print(f"[green]Plot saved to {out}[/green]")


if __name__ == "__main__":
    cli()
