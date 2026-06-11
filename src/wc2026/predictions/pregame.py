"""Pre-game prediction helpers."""
from __future__ import annotations

from typing import TYPE_CHECKING

import pandas as pd

if TYPE_CHECKING:
    from wc2026.models.ensemble import EnsembleModel


def pregame_predict(
    model: "EnsembleModel",
    home_team: str,
    away_team: str,
    max_goals: int = 10,
    neutral_venue: bool = True,
) -> dict:
    """
    Comprehensive pre-game prediction dictionary.

    Returns
    -------
    dict with keys:
        home_team, away_team, home_win, draw, away_win,
        home_xg, away_xg, btts_yes, btts_no,
        over_0_5 .. over_5_5, under_0_5 .. under_5_5,
        score_matrix (list[list[float]]),
        top_scores (list[dict])
    """
    g = model.predict(home_team, away_team, max_goals=max_goals, neutral_venue=neutral_venue)

    top = []
    import numpy as np
    mat = g.grid
    indices = np.argsort(mat, axis=None)[::-1][:15]
    for idx in indices:
        h, a = divmod(int(idx), mat.shape[1])
        top.append({"home_goals": h, "away_goals": a, "probability": float(mat[h, a])})

    result = {
        "home_team": home_team,
        "away_team": away_team,
        "home_win": g.home_win,
        "draw": g.draw,
        "away_win": g.away_win,
        "home_xg": g.home_goal_expectation,
        "away_xg": g.away_goal_expectation,
        "btts_yes": g.btts_yes,
        "btts_no": g.btts_no,
        "double_chance_1x": g.double_chance_1x,
        "double_chance_x2": g.double_chance_x2,
        "double_chance_12": g.double_chance_12,
        "draw_no_bet_home": g.draw_no_bet_home,
        "draw_no_bet_away": g.draw_no_bet_away,
        "expected_points_home": g.expected_points_home(),
        "expected_points_away": g.expected_points_away(),
        "top_scores": top,
        "score_matrix": g.grid.tolist(),
    }

    for line in [0.5, 1.5, 2.5, 3.5, 4.5, 5.5]:
        key = str(line).replace(".", "_")
        result[f"over_{key}"] = g.total_goals("over", line)
        result[f"under_{key}"] = g.total_goals("under", line)

    return result
