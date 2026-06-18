"""
Individual rating-system EGM components.
Each component: fit on historical data → produce team EGM estimates.
"""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
import numpy as np
import pandas as pd

from src.wc2026.ratings.pi_margin import (
    fit_pi_ratings, calibrate_pi_to_egm, team_pi_egm,
    PiCalibration,
)

try:
    from penaltyblog.ratings import EloRatingSystem as _Elo
    _HAS_ELO = True
except ImportError:
    _HAS_ELO = False


@dataclass
class ComponentEGM:
    """EGM estimate from a single rating system for a team vs average opponent."""
    team: str
    egm: float
    raw_rating: float
    rating_diff_vs_avg: float
    slope: float
    intercept: float
    training_cutoff: datetime
    effective_n: int
    source: str


def _ols_calibrate(X: np.ndarray, y: np.ndarray) -> tuple[float, float, float]:
    """Returns (slope, intercept, r2)."""
    A = np.column_stack([np.ones_like(X), X])
    coef, _, _, _ = np.linalg.lstsq(A, y, rcond=None)
    intercept, slope = float(coef[0]), float(coef[1])
    y_pred = intercept + slope * X
    ss_tot = np.sum((y - np.mean(y)) ** 2)
    r2 = 1.0 - np.sum((y - y_pred) ** 2) / ss_tot if ss_tot > 0 else 0.0
    return slope, intercept, float(r2)


class RatingComponentFitter:
    """
    Fits multiple rating systems and calibrates each to EGM.
    All fitting uses only matches known before prediction_timestamp.
    """

    def __init__(self, min_samples: int = 10, pi_k: float = 0.1):
        self.min_samples = min_samples
        self.pi_k = pi_k
        self._pi_ratings: dict = {}
        self._pi_calib: Optional[PiCalibration] = None
        self._elo_ratings: dict = {}
        self._elo_slope: float = 0.0
        self._elo_intercept: float = 0.0

    def fit(self, matches_df: pd.DataFrame) -> "RatingComponentFitter":
        """
        matches_df columns required: home_team, away_team, home_goals, away_goals, datetime
        """
        completed = matches_df.dropna(subset=["home_goals", "away_goals"])
        if completed.empty:
            return self

        # Pi ratings
        self._pi_ratings = fit_pi_ratings(completed, k=self.pi_k)
        self._pi_calib = calibrate_pi_to_egm(completed, self._pi_ratings, self.min_samples)

        # Elo ratings (if available)
        if _HAS_ELO:
            try:
                elo = _Elo()
                for _, row in completed.sort_values("datetime").iterrows():
                    gd = int(row["home_goals"]) - int(row["away_goals"])
                    elo.update_ratings(str(row["home_team"]), str(row["away_team"]), gd)
                # Extract elo ratings
                teams = set(completed["home_team"]).union(completed["away_team"])
                self._elo_ratings = {}
                for t in teams:
                    r = elo.get_ratings(str(t))
                    if r is not None:
                        self._elo_ratings[str(t)] = float(r) if not isinstance(r, dict) else float(r.get("rating", 0.0))
                # Calibrate elo diff -> GD
                rows = []
                for _, row in completed.iterrows():
                    h, a = str(row["home_team"]), str(row["away_team"])
                    if h in self._elo_ratings and a in self._elo_ratings:
                        rows.append({
                            "elo_diff": self._elo_ratings[h] - self._elo_ratings[a],
                            "gd": float(row["home_goals"]) - float(row["away_goals"]),
                        })
                if len(rows) >= self.min_samples:
                    df2 = pd.DataFrame(rows)
                    self._elo_slope, self._elo_intercept, _ = _ols_calibrate(
                        df2["elo_diff"].values, df2["gd"].values
                    )
            except Exception:
                pass

        return self

    def pi_egm(self, home_team: str, away_team: str) -> Optional[float]:
        if not self._pi_ratings or self._pi_calib is None:
            return None
        return team_pi_egm(home_team, away_team, self._pi_ratings, self._pi_calib)

    def elo_egm(self, home_team: str, away_team: str) -> Optional[float]:
        if not self._elo_ratings:
            return None
        h = self._elo_ratings.get(home_team)
        a = self._elo_ratings.get(away_team)
        if h is None or a is None:
            return None
        return self._elo_intercept + self._elo_slope * (h - a)
