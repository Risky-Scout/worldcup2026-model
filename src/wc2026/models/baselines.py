"""
Naive and rating-based baselines.

Every baseline returns a ScorePMFPrediction with the same schema.

Baselines
---------
1. EqualProbabilityBaseline   — 1/3 each, Poisson with equal lambdas
2. HistoricalBaseRateBaseline — empirical score distribution from WC history
3. EloBaseline                — penaltyblog Elo rating system
4. PiRatingBaseline           — penaltyblog Pi rating system
"""
from __future__ import annotations

import logging
from typing import Optional

import numpy as np
import pandas as pd
from penaltyblog.models import create_dixon_coles_grid
from penaltyblog.ratings.elo import Elo
from penaltyblog.ratings.pi import PiRatingSystem
from scipy.stats import poisson

from wc2026.config import PMF_MAX_GOALS, RANDOM_SEED
from wc2026.models.prediction import CalibrationStatus, ScorePMFPrediction

log = logging.getLogger(__name__)

# World Cup average goals per team per 90-minute match (approximation from WC data)
_WC_AVG_GOALS_PER_TEAM = 1.35


def _make_poisson_pmf(
    lambda_h: float,
    lambda_a: float,
    max_goals: int,
    rho: float = 0.0,
) -> tuple[np.ndarray, float, float]:
    """Return (pmf, tail_mass, total) for a Poisson score grid."""
    lambda_h = max(lambda_h, 0.01)
    lambda_a = max(lambda_a, 0.01)
    grid = create_dixon_coles_grid(lambda_h, lambda_a, rho=rho, max_goals=max_goals)
    raw = grid.goal_matrix
    # Pad to max_goals
    pmf = np.zeros((max_goals, max_goals), dtype=float)
    h = min(raw.shape[0], max_goals)
    a = min(raw.shape[1], max_goals)
    pmf[:h, :a] = raw[:h, :a]
    tail_mass = max(0.0, float(raw.sum()) - float(pmf.sum()))
    s = float(pmf.sum())
    if s > 0:
        pmf = pmf / s * (1.0 - tail_mass)
    return pmf, tail_mass, float(lambda_h), float(lambda_a)


# ---------------------------------------------------------------------------
# Baseline 1: Equal probability
# ---------------------------------------------------------------------------

class EqualProbabilityBaseline:
    """
    PMF based on equal Poisson lambdas for both teams (= average WC goal rate).
    Produces a 1X2 close to [~0.35, ~0.26, ~0.39] which is the rough WC average.
    """

    MODEL_NAME = "equal_probability"

    def __init__(self, max_goals: int = PMF_MAX_GOALS):
        self._max_goals = max_goals

    def predict(
        self,
        home_team: str,
        away_team: str,
        match_id: Optional[int] = None,
        **kwargs,
    ) -> ScorePMFPrediction:
        lam = _WC_AVG_GOALS_PER_TEAM
        pmf, tail, lh, la = _make_poisson_pmf(lam, lam, self._max_goals)
        return ScorePMFPrediction(
            match_id=match_id,
            home_team=home_team,
            away_team=away_team,
            season=kwargs.get("season"),
            stage=kwargs.get("stage"),
            venue=kwargs.get("venue"),
            model_name=self.MODEL_NAME,
            max_goals=self._max_goals,
            score_pmf=pmf,
            tail_mass=tail,
            expected_home_goals=lh,
            expected_away_goals=la,
        )


# ---------------------------------------------------------------------------
# Baseline 2: Historical World Cup base rate
# ---------------------------------------------------------------------------

class HistoricalBaseRateBaseline:
    """
    PMF derived from the empirical score distribution of all historical WC matches.

    If enough training data is available, uses a smoothed empirical matrix.
    Otherwise falls back to EqualProbabilityBaseline.
    """

    MODEL_NAME = "historical_base_rate"
    MIN_MATCHES = 20

    def __init__(self, max_goals: int = PMF_MAX_GOALS):
        self._max_goals = max_goals
        self._pmf: Optional[np.ndarray] = None
        self._avg_home_goals = _WC_AVG_GOALS_PER_TEAM
        self._avg_away_goals = _WC_AVG_GOALS_PER_TEAM

    def fit(self, df: pd.DataFrame) -> "HistoricalBaseRateBaseline":
        """
        Estimate base-rate PMF from historical match data.

        Parameters
        ----------
        df : must have 'home_goals' and 'away_goals' columns.
        """
        df = df.dropna(subset=["home_goals", "away_goals"])
        if len(df) < self.MIN_MATCHES:
            log.warning(
                "Only %d matches for base rate (need %d). Using Poisson fallback.",
                len(df),
                self.MIN_MATCHES,
            )
            return self

        mg = self._max_goals
        counts = np.zeros((mg, mg), dtype=float)
        for _, row in df.iterrows():
            h, a = int(row["home_goals"]), int(row["away_goals"])
            if h < mg and a < mg:
                counts[h, a] += 1.0

        # Apply +1 Laplace smoothing so no cell is exactly 0
        counts += 1.0
        self._pmf = counts / counts.sum()
        self._avg_home_goals = float(df["home_goals"].mean())
        self._avg_away_goals = float(df["away_goals"].mean())
        return self

    def predict(
        self,
        home_team: str,
        away_team: str,
        match_id: Optional[int] = None,
        **kwargs,
    ) -> ScorePMFPrediction:
        if self._pmf is None:
            # Fallback to equal probability
            return EqualProbabilityBaseline(self._max_goals).predict(
                home_team, away_team, match_id, **kwargs
            )
        pmf = self._pmf.copy()
        tail_mass = 0.0
        return ScorePMFPrediction(
            match_id=match_id,
            home_team=home_team,
            away_team=away_team,
            season=kwargs.get("season"),
            stage=kwargs.get("stage"),
            venue=kwargs.get("venue"),
            model_name=self.MODEL_NAME,
            max_goals=self._max_goals,
            score_pmf=pmf,
            tail_mass=tail_mass,
            expected_home_goals=self._avg_home_goals,
            expected_away_goals=self._avg_away_goals,
        )


# ---------------------------------------------------------------------------
# Baseline 3: Elo rating
# ---------------------------------------------------------------------------

class EloBaseline:
    """
    Uses penaltyblog Elo ratings to estimate 1X2, then converts to a Poisson
    PMF with lambdas implied by the Elo win probability.
    """

    MODEL_NAME = "elo"

    def __init__(
        self,
        k: float = 20.0,
        home_field_advantage: float = 0.0,  # neutral venue by default for WC
        max_goals: int = PMF_MAX_GOALS,
    ):
        self._elo = Elo(k=k, home_field_advantage=home_field_advantage)
        self._max_goals = max_goals
        self.fitted = False

    def fit(self, df: pd.DataFrame) -> "EloBaseline":
        """Update Elo ratings in chronological order."""
        df = df.sort_values("match_datetime").dropna(subset=["home_goals", "away_goals"])
        for _, row in df.iterrows():
            h, a = int(row["home_goals"]), int(row["away_goals"])
            result = 0 if h > a else (1 if h == a else 2)
            self._elo.update_ratings(row["home_team"], row["away_team"], result)
        self.fitted = True
        return self

    def predict(
        self,
        home_team: str,
        away_team: str,
        match_id: Optional[int] = None,
        **kwargs,
    ) -> ScorePMFPrediction:
        try:
            probs = self._elo.calculate_match_probabilities(home_team, away_team)
            p_home = probs.get("home_win", 1 / 3)
        except Exception:
            p_home = 1 / 3

        # Convert win probability to goal-expectancy via log-Poisson inversion
        # WC average ~2.7 total goals / match
        total_avg = _WC_AVG_GOALS_PER_TEAM * 2
        # Allocate based on relative attack implied by win prob
        p_ratio = p_home / max(1 - p_home, 0.01)
        lam_h = total_avg * p_ratio / (1 + p_ratio)
        lam_a = total_avg - lam_h
        lam_h = max(lam_h, 0.1)
        lam_a = max(lam_a, 0.1)

        pmf, tail, lh, la = _make_poisson_pmf(lam_h, lam_a, self._max_goals)
        return ScorePMFPrediction(
            match_id=match_id,
            home_team=home_team,
            away_team=away_team,
            season=kwargs.get("season"),
            stage=kwargs.get("stage"),
            venue=kwargs.get("venue"),
            model_name=self.MODEL_NAME,
            max_goals=self._max_goals,
            score_pmf=pmf,
            tail_mass=tail,
            expected_home_goals=lh,
            expected_away_goals=la,
        )
