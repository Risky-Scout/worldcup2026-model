"""
ModelLadder — trains every candidate model and returns a consistent
ScorePMFPrediction for any (home_team, away_team) pair.

Model tiers
-----------
Tier 0 (naive)      : equal probability, historical base rate, rating-only
Tier 1 (penaltyblog): Poisson, DixonColes, Bivariate, WeibullCopula,
                       NegativeBinomial, ZeroInflatedPoisson
Tier 2 (Bayesian)   : BayesianGoalModel, HierarchicalBayesianGoalModel

Every model is fitted with:
- time-decay weights from penaltyblog.models.dixon_coles_weights
- neutral_venue flag where the model supports it

Every model returns a ScorePMFPrediction whose PMF sums to 1.0.
"""
from __future__ import annotations

import logging
import random
from typing import Optional

import numpy as np
import pandas as pd
from penaltyblog.models import (
    BayesianGoalModel,
    BivariatePoissonGoalModel,
    DixonColesGoalModel,
    FootballProbabilityGrid,
    HierarchicalBayesianGoalModel,
    NegativeBinomialGoalModel,
    PoissonGoalsModel,
    WeibullCopulaGoalsModel,
    ZeroInflatedPoissonGoalsModel,
    create_dixon_coles_grid,
    dixon_coles_weights,
)

from wc2026.config import DC_WEIGHT_XI, PMF_MAX_GOALS, RANDOM_SEED
from wc2026.models.prediction import CalibrationStatus, ScorePMFPrediction

log = logging.getLogger(__name__)

# Model names — used as keys in the registry
MODEL_POISSON = "poisson"
MODEL_DIXON_COLES = "dixon_coles"
MODEL_BIVARIATE = "bivariate_poisson"
MODEL_WEIBULL = "weibull_copula"
MODEL_NEG_BINOMIAL = "negative_binomial"
MODEL_ZERO_INF = "zero_inflated_poisson"
MODEL_BAYESIAN = "bayesian"
MODEL_HIERARCHICAL = "hierarchical_bayesian"

TIER1_MODELS = [
    MODEL_POISSON,
    MODEL_DIXON_COLES,
    MODEL_BIVARIATE,
    MODEL_WEIBULL,
    MODEL_NEG_BINOMIAL,
    MODEL_ZERO_INF,
]
TIER2_MODELS = [MODEL_BAYESIAN, MODEL_HIERARCHICAL]
ALL_MODELS = TIER1_MODELS + TIER2_MODELS


class ModelLadder:
    """
    Fits and holds all candidate goal models.

    Parameters
    ----------
    df : pd.DataFrame
        Must contain columns: home_team, away_team, home_goals, away_goals,
        match_weight, is_neutral, match_datetime (sorted ascending).
    max_goals : int
        PMF grid size.
    include_bayesian : bool
        Whether to fit the MCMC-based Bayesian models (slow).
    bayesian_samples : int
        MCMC samples per chain.
    bayesian_chains : int
        Number of parallel MCMC chains.
    """

    def __init__(
        self,
        df: pd.DataFrame,
        max_goals: int = PMF_MAX_GOALS,
        include_bayesian: bool = True,
        bayesian_samples: int = 2000,
        bayesian_chains: int = 4,
        random_seed: int = RANDOM_SEED,
    ) -> None:
        self._df = df.copy()
        self._max_goals = max_goals
        self._include_bayesian = include_bayesian
        self._bayesian_samples = bayesian_samples
        self._bayesian_chains = bayesian_chains
        self._seed = random_seed

        # Fitted model objects keyed by MODEL_* constants
        self._models: dict[str, object] = {}
        self.fitted = False

    # -----------------------------------------------------------------------
    # Fitting
    # -----------------------------------------------------------------------

    def fit(self, models: list[str] | None = None) -> "ModelLadder":
        """
        Fit specified models (default: all Tier 1 + Tier 2 if include_bayesian).
        Returns self.
        """
        np.random.seed(self._seed)
        random.seed(self._seed)

        df = self._df
        if df.empty or len(df) < 3:
            raise ValueError("Need at least 3 matches to fit any model.")

        h = df["home_goals"].values.astype(int)
        a = df["away_goals"].values.astype(int)
        ht = df["home_team"].values
        at = df["away_team"].values

        # penaltyblog time-decay weights
        # dixon_coles_weights returns array aligned with df rows
        w = _compute_weights(df)
        # All WC matches are at neutral venues — force neutral_venue=1 so home
        # advantage is not learned from tournament data (penaltyblog 1.11.0 pins
        # the home advantage parameter to 0 when all training matches are neutral).
        neutral = np.ones(len(df), dtype=int)

        to_fit = models or (
            TIER1_MODELS + (TIER2_MODELS if self._include_bayesian else [])
        )

        for name in to_fit:
            try:
                log.info("Fitting %s …", name)
                self._models[name] = self._fit_one(name, h, a, ht, at, w, neutral)
                log.info("  %s fitted.", name)
            except Exception as exc:
                log.warning("Failed to fit %s: %s", name, exc)

        self.fitted = True
        log.info(
            "ModelLadder fitted: %d models on %d matches.",
            len(self._models),
            len(df),
        )
        return self

    def _fit_one(
        self,
        name: str,
        h, a, ht, at, w, neutral,
    ) -> object:
        kw_base = dict(weights=w)
        kw_neutral = dict(weights=w, neutral_venue=neutral)

        # use_gradient=True + tighter convergence for all MLE models (1.11.0)
        _fit_kw = dict(use_gradient=True, minimizer_options={"maxiter": 3000, "gtol": 1e-8})

        if name == MODEL_POISSON:
            # Pass neutral_venue per penaltyblog 1.11.0 recommendation; fall back
            # to kw_base if this version of the model doesn't support the arg.
            try:
                m = PoissonGoalsModel(h, a, ht, at, **kw_neutral)
                m.fit(**_fit_kw)
            except TypeError:
                m = PoissonGoalsModel(h, a, ht, at, **kw_base)
                m.fit(**_fit_kw)
        elif name == MODEL_DIXON_COLES:
            m = DixonColesGoalModel(h, a, ht, at, **kw_neutral)
            m.fit(**_fit_kw)
        elif name == MODEL_BIVARIATE:
            try:
                m = BivariatePoissonGoalModel(h, a, ht, at, **kw_neutral)
                m.fit(**_fit_kw)
            except TypeError:
                m = BivariatePoissonGoalModel(h, a, ht, at, **kw_base)
                m.fit(**_fit_kw)
        elif name == MODEL_WEIBULL:
            try:
                m = WeibullCopulaGoalsModel(h, a, ht, at, **kw_neutral)
                m.fit(**_fit_kw)
            except TypeError:
                m = WeibullCopulaGoalsModel(h, a, ht, at, **kw_base)
                m.fit(**_fit_kw)
        elif name == MODEL_NEG_BINOMIAL:
            m = NegativeBinomialGoalModel(h, a, ht, at, **kw_neutral)
            m.fit(**_fit_kw)
        elif name == MODEL_ZERO_INF:
            m = ZeroInflatedPoissonGoalsModel(h, a, ht, at, **kw_neutral)
            m.fit(**_fit_kw)
        elif name == MODEL_BAYESIAN:
            m = BayesianGoalModel(h, a, ht, at, **kw_neutral)
            m.fit(
                n_samples=self._bayesian_samples,
                n_chains=self._bayesian_chains,
            )
        elif name == MODEL_HIERARCHICAL:
            m = HierarchicalBayesianGoalModel(h, a, ht, at, **kw_neutral)
            m.fit(
                n_samples=self._bayesian_samples,
                n_chains=self._bayesian_chains,
            )
        else:
            raise ValueError(f"Unknown model: {name}")
        return m

    # -----------------------------------------------------------------------
    # Prediction
    # -----------------------------------------------------------------------

    def predict(
        self,
        model_name: str,
        home_team: str,
        away_team: str,
        match_id: Optional[int] = None,
        season: Optional[int] = None,
        stage: Optional[str] = None,
        venue: Optional[str] = None,
        neutral_venue: bool = True,
    ) -> ScorePMFPrediction:
        """Return ScorePMFPrediction for a single model."""
        if not self.fitted:
            raise RuntimeError("Call .fit() first.")
        if model_name not in self._models:
            raise ValueError(
                f"Model '{model_name}' not fitted. Available: {list(self._models)}"
            )
        model = self._models[model_name]
        try:
            grid: FootballProbabilityGrid = model.predict(
                home_team,
                away_team,
                max_goals=self._max_goals,
                neutral_venue=neutral_venue,
            )
        except Exception as exc:
            raise RuntimeError(
                f"Prediction failed for {model_name} ({home_team} v {away_team}): {exc}"
            ) from exc

        return ScorePMFPrediction.from_grid(
            grid=grid,
            model_name=model_name,
            home_team=home_team,
            away_team=away_team,
            match_id=match_id,
            season=season,
            stage=stage,
            venue=venue,
            max_goals=self._max_goals,
        )

    def predict_batch(
        self,
        model_name: str,
        home_teams: list[str],
        away_teams: list[str],
        match_ids: Optional[list[int]] = None,
        seasons: Optional[list] = None,
        stages: Optional[list[str]] = None,
        venues: Optional[list[str]] = None,
    ) -> list[ScorePMFPrediction]:
        """
        Batch-predict using penaltyblog's predict_many() for efficiency.

        All WC matches are treated as neutral_venue=1. Falls back to per-match
        .predict() calls if predict_many raises an exception.
        """
        if not self.fitted:
            raise RuntimeError("Call .fit() first.")
        if model_name not in self._models:
            raise ValueError(f"Model '{model_name}' not fitted.")

        n = len(home_teams)
        neutral = [1] * n

        try:
            model = self._models[model_name]
            grids: list[FootballProbabilityGrid] = model.predict_many(
                home_teams,
                away_teams,
                max_goals=self._max_goals,
                neutral_venue=neutral,
            )
            return [
                ScorePMFPrediction.from_grid(
                    grid=grid,
                    model_name=model_name,
                    home_team=home_teams[i],
                    away_team=away_teams[i],
                    match_id=match_ids[i] if match_ids else None,
                    season=seasons[i] if seasons else None,
                    stage=stages[i] if stages else None,
                    venue=venues[i] if venues else None,
                    max_goals=self._max_goals,
                )
                for i, grid in enumerate(grids)
            ]
        except Exception as exc:
            log.warning("predict_batch(%s) failed (%s) — falling back to per-match predict", model_name, exc)
            return [
                self.predict(
                    model_name,
                    home_teams[i],
                    away_teams[i],
                    match_id=match_ids[i] if match_ids else None,
                    season=seasons[i] if seasons else None,
                    stage=stages[i] if stages else None,
                    venue=venues[i] if venues else None,
                )
                for i in range(n)
            ]

    def predict_all(
        self,
        home_team: str,
        away_team: str,
        **kwargs,
    ) -> dict[str, ScorePMFPrediction]:
        """Return predictions from every fitted model."""
        out = {}
        for name in self._models:
            try:
                out[name] = self.predict(name, home_team, away_team, **kwargs)
            except Exception as exc:
                log.warning("predict_all skip %s: %s", name, exc)
        return out

    def teams(self) -> list[str]:
        """Return sorted list of teams from the primary (Dixon-Coles) model."""
        for name in [MODEL_DIXON_COLES, MODEL_POISSON, MODEL_BAYESIAN]:
            if name in self._models:
                return sorted(self._models[name].teams)
        return []

    def fitted_models(self) -> list[str]:
        return list(self._models.keys())


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _compute_weights(df: pd.DataFrame) -> np.ndarray:
    """
    Use penaltyblog.models.dixon_coles_weights to compute time-decay
    weights aligned with each row of df.

    Requires a 'match_datetime' column (datetime with timezone).
    Falls back to uniform weights if the column is missing.

    If the DataFrame contains a '_preset_weight' column with all finite positive
    values, those weights are used directly (bypasses xi recomputation).
    This allows callers to blend custom xi values (e.g. xi=0.010 for live 2026
    matches) before passing the combined DataFrame to ModelLadder.
    """
    # Honour pre-computed weights when explicitly set by the caller
    if "_preset_weight" in df.columns:
        arr = df["_preset_weight"].values.astype(float)
        if np.all(np.isfinite(arr)) and np.all(arr > 0):
            return arr

    if "match_datetime" not in df.columns:
        return np.ones(len(df), dtype=float)

    # penaltyblog.dixon_coles_weights expects a pandas Series of dates
    from penaltyblog.models import dixon_coles_weights as pbw

    try:
        dates = pd.to_datetime(df["match_datetime"], utc=True).dt.tz_localize(None)
        weights = pbw(dates, xi=DC_WEIGHT_XI)
        arr = np.asarray(weights, dtype=float)
        arr = np.where(np.isfinite(arr) & (arr > 0), arr, 1.0)
        return arr
    except Exception as exc:
        log.warning("dixon_coles_weights failed (%s). Using uniform weights.", exc)
        return np.ones(len(df), dtype=float)
