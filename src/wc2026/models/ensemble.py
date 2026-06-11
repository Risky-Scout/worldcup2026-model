"""
EnsembleModel — the public prediction interface.

Wraps a fitted ModelTrainer and exposes a clean, match-centric API
for pre-game scoreline predictions.
"""
from __future__ import annotations

import pickle
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from penaltyblog.models import FootballProbabilityGrid

from wc2026.models.trainer import ModelTrainer


class EnsembleModel:
    """
    Public interface for ensemble match predictions.

    Usage
    -----
    >>> model = EnsembleModel.from_dataframe(df)
    >>> grid = model.predict("Brazil", "France")
    >>> print(grid)
    >>> print(f"Brazil win: {grid.home_win:.1%}")
    >>> print(f"Exact 1-0: {grid.exact_score(1, 0):.2%}")
    """

    def __init__(self, trainer: ModelTrainer) -> None:
        self._trainer = trainer

    # ------------------------------------------------------------------
    # Constructors
    # ------------------------------------------------------------------

    @classmethod
    def from_dataframe(
        cls,
        df: pd.DataFrame,
        bayesian: bool = True,
        **trainer_kwargs: Any,
    ) -> "EnsembleModel":
        trainer = ModelTrainer(df, bayesian=bayesian, **trainer_kwargs)
        trainer.fit()
        return cls(trainer)

    @classmethod
    def load(cls, path: str | Path) -> "EnsembleModel":
        with open(path, "rb") as fh:
            return pickle.load(fh)

    def save(self, path: str | Path) -> None:
        with open(path, "wb") as fh:
            pickle.dump(self, fh)

    # ------------------------------------------------------------------
    # Prediction
    # ------------------------------------------------------------------

    def predict(
        self,
        home_team: str,
        away_team: str,
        max_goals: int = 10,
        neutral_venue: bool = True,
    ) -> FootballProbabilityGrid:
        """
        Full scoreline probability distribution.

        Returns a FootballProbabilityGrid with:
        - grid[i, j] = P(home scores i, away scores j)
        - .home_win / .draw / .away_win
        - .exact_score(i, j)
        - .total_goals(over_under, strike)
        - .asian_handicap(side, line)
        - .btts_yes / .btts_no
        - .expected_points_home() / .expected_points_away()
        """
        return self._trainer.predict_grid(home_team, away_team, max_goals, neutral_venue)

    def predict_summary(
        self,
        home_team: str,
        away_team: str,
        max_goals: int = 10,
        neutral_venue: bool = True,
    ) -> pd.Series:
        """Return a named Series of the most-used probabilities."""
        g = self.predict(home_team, away_team, max_goals, neutral_venue)
        top_scores = self._top_scores(g, n=10)
        data = {
            "home_team": home_team,
            "away_team": away_team,
            "home_win": g.home_win,
            "draw": g.draw,
            "away_win": g.away_win,
            "btts_yes": g.btts_yes,
            "over_2_5": g.total_goals("over", 2.5),
            "under_2_5": g.total_goals("under", 2.5),
            "over_1_5": g.total_goals("over", 1.5),
            "under_1_5": g.total_goals("under", 1.5),
            "over_3_5": g.total_goals("over", 3.5),
            "home_xg": g.home_goal_expectation,
            "away_xg": g.away_goal_expectation,
            **{f"score_{h}_{a}": p for (h, a), p in top_scores},
        }
        return pd.Series(data)

    def score_probability_table(
        self,
        home_team: str,
        away_team: str,
        max_goals: int = 7,
        neutral_venue: bool = True,
    ) -> pd.DataFrame:
        """
        Return an (max_goals × max_goals) DataFrame of scoreline probabilities.

        Rows = home goals, columns = away goals.
        """
        g = self.predict(home_team, away_team, max_goals, neutral_venue)
        matrix = g.grid[:max_goals, :max_goals]
        return pd.DataFrame(
            matrix,
            index=[f"Home {i}" for i in range(max_goals)],
            columns=[f"Away {j}" for j in range(max_goals)],
        )

    def top_scores(
        self,
        home_team: str,
        away_team: str,
        n: int = 15,
        max_goals: int = 10,
        neutral_venue: bool = True,
    ) -> pd.DataFrame:
        """Return a DataFrame of the top-n most likely scorelines."""
        g = self.predict(home_team, away_team, max_goals, neutral_venue)
        rows = self._top_scores(g, n=n)
        return pd.DataFrame(
            [{"home_goals": h, "away_goals": a, "probability": p} for (h, a), p in rows]
        )

    def teams(self) -> list[str]:
        return self._trainer.teams()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _top_scores(
        grid: FootballProbabilityGrid, n: int
    ) -> list[tuple[tuple[int, int], float]]:
        mat = grid.grid
        indices = np.argsort(mat, axis=None)[::-1][:n]
        rows_idx, cols_idx = np.unravel_index(indices, mat.shape)
        return [
            ((int(r), int(c)), float(mat[r, c]))
            for r, c in zip(rows_idx, cols_idx)
        ]
