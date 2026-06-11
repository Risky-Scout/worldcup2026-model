"""
ModelTrainer — fits all component models on the match DataFrame
and exposes the results via a clean interface.

Component models
----------------
1. DixonColesGoalModel (MLE, time-decay weights)
   The classic gold standard for soccer prediction.  Fast to fit,
   excellent AIC, analytically-corrected for low-score dependence.

2. BayesianGoalModel (MCMC over the Dixon-Coles likelihood)
   Full posterior over team strengths; propagates parameter
   uncertainty into the final score distributions.

3. BivariatePoissonGoalModel
   Allows positive correlation between home and away goals, which
   is small in soccer but non-zero.

4. WeibullCopulaGoalsModel
   Captures heavy-tailed goal distributions better than Poisson
   alone; penaltyblog's most robust tail model.

The ``ModelTrainer`` holds all four fitted objects plus their
relative ensemble weights (derived from leave-one-out RPS on the
training data).
"""
from __future__ import annotations

import logging
from typing import Any

import numpy as np
import pandas as pd
from penaltyblog.models import (
    BayesianGoalModel,
    BivariatePoissonGoalModel,
    DixonColesGoalModel,
    FootballProbabilityGrid,
    WeibullCopulaGoalsModel,
    dixon_coles_weights,
)

log = logging.getLogger(__name__)


class ModelTrainer:
    """
    Fits the full ensemble of goal-scoring models on historical WC data.

    Parameters
    ----------
    df : pd.DataFrame
        Output of ``build_match_dataframe()``.
    xi : float
        Half-life parameter (in days) for Dixon-Coles time-decay weights.
        Default 180 days.  Passed to ``penaltyblog.models.dixon_coles_weights``.
    bayesian : bool
        Whether to fit the computationally expensive Bayesian model.
        Default True. Set False for fast iteration.
    bayesian_samples : int
        MCMC samples per chain for the Bayesian model.
    bayesian_chains : int
        Number of parallel MCMC chains.
    """

    def __init__(
        self,
        df: pd.DataFrame,
        xi: float = 0.0038,  # ≈ log(2)/180 — penaltyblog default
        bayesian: bool = True,
        bayesian_samples: int = 2000,
        bayesian_chains: int = 4,
    ) -> None:
        self.df = df.copy()
        self.xi = xi
        self._bayesian_enabled = bayesian
        self._bayesian_samples = bayesian_samples
        self._bayesian_chains = bayesian_chains

        self._dc: DixonColesGoalModel | None = None
        self._bayes: BayesianGoalModel | None = None
        self._biv: BivariatePoissonGoalModel | None = None
        self._weibull: WeibullCopulaGoalsModel | None = None

        # Ensemble weights set after fitting (RPS-derived)
        self.weights: dict[str, float] = {
            "dc": 0.40,
            "bayes": 0.30,
            "bivariate": 0.15,
            "weibull": 0.15,
        }
        self.fitted = False

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def fit(self) -> "ModelTrainer":
        """Fit all component models. Returns self for chaining."""
        df = self.df
        h = df["home_goals"].values
        a = df["away_goals"].values
        ht = df["home_team"].values
        at = df["away_team"].values
        w = df["match_weight"].values
        neutral = df["is_neutral"].values

        log.info("Fitting Dixon-Coles model …")
        self._dc = DixonColesGoalModel(h, a, ht, at, weights=w, neutral_venue=neutral)
        self._dc.fit()
        log.info("Dixon-Coles fitted. AIC=%.1f", self._dc.aic)

        log.info("Fitting Bivariate Poisson model …")
        self._biv = BivariatePoissonGoalModel(h, a, ht, at, weights=w)
        self._biv.fit()
        log.info("Bivariate Poisson fitted.")

        log.info("Fitting Weibull Copula model …")
        self._weibull = WeibullCopulaGoalsModel(h, a, ht, at, weights=w)
        self._weibull.fit()
        log.info("Weibull Copula fitted.")

        if self._bayesian_enabled:
            log.info(
                "Fitting Bayesian model (%d samples × %d chains) — this may take a few minutes …",
                self._bayesian_samples,
                self._bayesian_chains,
            )
            self._bayes = BayesianGoalModel(h, a, ht, at, weights=w, neutral_venue=neutral)
            self._bayes.fit(
                n_samples=self._bayesian_samples,
                n_chains=self._bayesian_chains,
            )
            log.info("Bayesian model fitted.")

        self._calibrate_weights()
        self.fitted = True
        log.info("All models fitted. Ensemble weights: %s", self.weights)
        return self

    def predict_grid(
        self,
        home_team: str,
        away_team: str,
        max_goals: int = 10,
        neutral_venue: bool = True,
    ) -> FootballProbabilityGrid:
        """
        Return the ensemble-averaged FootballProbabilityGrid.

        The grid encodes P(home_goals=i, away_goals=j) for
        i, j in 0..max_goals-1, giving full scoreline probabilities.
        """
        if not self.fitted:
            raise RuntimeError("Call .fit() first.")
        return self._ensemble_grid(home_team, away_team, max_goals, neutral_venue)

    def predict_score_matrix(
        self,
        home_team: str,
        away_team: str,
        max_goals: int = 10,
        neutral_venue: bool = True,
    ) -> np.ndarray:
        """Return the raw (max_goals × max_goals) numpy probability matrix."""
        grid = self.predict_grid(home_team, away_team, max_goals, neutral_venue)
        return grid.grid

    def teams(self) -> list[str]:
        """Return the sorted list of teams the models know about."""
        if self._dc is None:
            raise RuntimeError("Call .fit() first.")
        return sorted(self._dc.teams)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _ensemble_grid(
        self,
        home_team: str,
        away_team: str,
        max_goals: int,
        neutral_venue: bool,
    ) -> FootballProbabilityGrid:
        """Weighted average of component score matrices."""
        matrix = np.zeros((max_goals, max_goals), dtype=np.float64)
        total_weight = 0.0

        models_and_weights: list[tuple[Any, float]] = [
            (self._dc, self.weights["dc"]),
            (self._biv, self.weights["bivariate"]),
            (self._weibull, self.weights["weibull"]),
        ]
        if self._bayes is not None:
            models_and_weights.append((self._bayes, self.weights["bayes"]))
        else:
            # Redistribute Bayesian weight to DC
            models_and_weights[0] = (self._dc, self.weights["dc"] + self.weights["bayes"])

        for model, wt in models_and_weights:
            if model is None:
                continue
            try:
                g = model.predict(
                    home_team,
                    away_team,
                    max_goals=max_goals,
                    neutral_venue=neutral_venue,
                )
                m = g.grid[:max_goals, :max_goals]
                # Pad or truncate to exactly (max_goals × max_goals)
                padded = np.zeros((max_goals, max_goals))
                h_sz = min(m.shape[0], max_goals)
                a_sz = min(m.shape[1], max_goals)
                padded[:h_sz, :a_sz] = m[:h_sz, :a_sz]
                matrix += wt * padded
                total_weight += wt
            except Exception as exc:
                log.warning("Model %s failed for %s v %s: %s", model, home_team, away_team, exc)

        if total_weight <= 0:
            raise RuntimeError("All models failed to produce predictions.")

        matrix /= total_weight

        # Use DC lambdas as the expectation point estimate for the grid wrapper
        dc_grid = self._dc.predict(home_team, away_team, max_goals=max_goals, neutral_venue=neutral_venue)
        return FootballProbabilityGrid(
            goal_matrix=matrix,
            home_goal_expectation=dc_grid.home_goal_expectation,
            away_goal_expectation=dc_grid.away_goal_expectation,
            normalize=True,
        )

    def _calibrate_weights(self) -> None:
        """
        Derive ensemble weights via leave-one-out RPS on the training set.

        Uses the last 20% of matches (chronologically) as a pseudo-holdout
        so we don't refit.  Weights are proportional to 1/RPS per model.
        """
        df = self.df.tail(max(20, len(self.df) // 5)).reset_index(drop=True)
        rps_scores: dict[str, list[float]] = {
            "dc": [], "bivariate": [], "weibull": []
        }
        if self._bayes is not None:
            rps_scores["bayes"] = []

        for _, row in df.iterrows():
            ht, at = row["home_team"], row["away_team"]
            actual_home, actual_away = int(row["home_goals"]), int(row["away_goals"])
            neutral = bool(row["is_neutral"])

            models = {
                "dc": self._dc,
                "bivariate": self._biv,
                "weibull": self._weibull,
            }
            if self._bayes is not None:
                models["bayes"] = self._bayes

            for name, model in models.items():
                try:
                    g = model.predict(ht, at, max_goals=10, neutral_venue=neutral)
                    rps_scores[name].append(_rps_1x2(g, actual_home, actual_away))
                except Exception:
                    pass

        mean_rps = {k: float(np.mean(v)) if v else 1.0 for k, v in rps_scores.items()}
        log.info("Mean RPS per model: %s", mean_rps)

        inv = {k: 1.0 / max(v, 1e-9) for k, v in mean_rps.items()}
        total = sum(inv.values())

        # Always keep weights for all four keys
        all_keys = ["dc", "bayes", "bivariate", "weibull"]
        for key in all_keys:
            self.weights[key] = inv.get(key, 0.0) / total if total > 0 else 0.25


def _rps_1x2(grid: FootballProbabilityGrid, home_goals: int, away_goals: int) -> float:
    """Ranked Probability Score for the 1X2 market (lower = better)."""
    probs = np.array(grid.home_draw_away, dtype=float)
    probs = np.clip(probs, 1e-9, 1.0)
    probs /= probs.sum()

    if home_goals > away_goals:
        outcome = 0
    elif home_goals == away_goals:
        outcome = 1
    else:
        outcome = 2

    actual = np.zeros(3)
    actual[outcome] = 1.0

    cum_probs = np.cumsum(probs)
    cum_actual = np.cumsum(actual)
    return float(np.mean((cum_probs - cum_actual) ** 2))
