"""
Team Margin Ratings report generator.
Writes reports/team_strength/team_margin_ratings.csv and team_margin_components.csv
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd
from src.wc2026.ratings.team_margin import TeamMarginRating

REPORT_DIR = Path("reports/team_strength")
REPORT_DIR.mkdir(parents=True, exist_ok=True)


def write_team_margin_ratings_csv(ratings: list[TeamMarginRating]) -> Path:
    """Write team margin ratings to CSV."""
    rows = [r.to_dict() for r in ratings]
    df = pd.DataFrame(rows)
    out = REPORT_DIR / "team_margin_ratings.csv"
    df.to_csv(out, index=False)
    return out


def write_team_margin_components_csv(ratings: list[TeamMarginRating]) -> Path:
    """Write component breakdown to CSV."""
    rows = []
    for r in ratings:
        rows.append({
            "team_name": r.team_name,
            "team_id": r.team_id,
            "confederation": r.confederation,
            "neutral_egm": r.neutral_egm,
            "pure_strength_egm": r.pure_strength_egm,
            "market_strength_egm": r.market_strength_egm,
            "pi_component": r.pi_component_egm,
            "elo_component": r.elo_component_egm,
            "market_component": r.market_component_egm,
            "xg_process_component": r.xg_process_component_egm,
            "player_component": r.player_component_egm,
            "goalkeeper_component": r.goalkeeper_component_egm,
            "futures_component": r.futures_component_egm,
            "uncertainty_egm": r.uncertainty_egm,
            "sample_size_effective": r.sample_size_effective,
            "sources_used": "|".join(r.sources_used),
            "model_version": r.model_version,
        })
    df = pd.DataFrame(rows).sort_values("pure_strength_egm", ascending=False)
    out = REPORT_DIR / "team_margin_components.csv"
    df.to_csv(out, index=False)
    return out
