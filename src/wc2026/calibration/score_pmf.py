"""
Score PMF calibration stack.

Stages
------
1. Temperature scaling: p_cal[i,j] ∝ p_raw[i,j] ** (1/T)
   - Fit T on out-of-fold exact-score log loss
   - T > 1 → model is overconfident; T < 1 → underconfident

2. Evaluation metrics (using penaltyblog.metrics where possible):
   - Exact-score log loss (primary)
   - 1X2 RPS (penaltyblog.metrics.compute_average_rps)
   - Multiclass Brier (penaltyblog.metrics.compute_multiclass_brier_score)
   - Ignorance score (penaltyblog.metrics.compute_ignorance_score)
   - ECE (custom — not in penaltyblog)
   - Calibration slope/intercept (custom)
   - Sharpness

IMPORTANT: CalibrationMetrics must be computed on OUT-OF-FOLD predictions only.
           Do not call evaluate() on training data.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional

import numpy as np
import pandas as pd
from penaltyblog.metrics.metrics import (
    compute_average_rps,
    compute_ignorance_score,
    compute_multiclass_brier_score,
)
from scipy.optimize import minimize_scalar

from wc2026.config import TEMPERATURE_GRID
from wc2026.models.prediction import CalibrationStatus, ScorePMFPrediction

log = logging.getLogger(__name__)
_EPS = 1e-9


@dataclass
class CalibrationMetrics:
    """
    Calibration metrics computed on a set of OOF score-PMF predictions.

    All metrics are lower-is-better except sharpness (higher is better).
    """

    n_matches: int = 0
    model_name: str = ""

    # Primary: exact-score log loss
    exact_score_log_loss: float = float("nan")

    # 1X2 markets (from penaltyblog.metrics)
    rps_1x2: float = float("nan")
    brier_1x2: float = float("nan")
    ignorance_1x2: float = float("nan")

    # Calibration quality
    ece_1x2: float = float("nan")   # Expected Calibration Error
    calibration_slope: float = float("nan")   # ideal = 1.0
    calibration_intercept: float = float("nan")  # ideal = 0.0

    # Sharpness (variance of predicted 1X2 probabilities, higher = sharper)
    sharpness: float = float("nan")

    # Temperature (>1 = overconfident, <1 = underconfident)
    temperature: float = 1.0

    def to_dict(self) -> dict:
        return {
            "model": self.model_name,
            "n_matches": self.n_matches,
            "exact_score_log_loss": round(self.exact_score_log_loss, 4),
            "rps_1x2": round(self.rps_1x2, 4),
            "brier_1x2": round(self.brier_1x2, 4),
            "ignorance_1x2": round(self.ignorance_1x2, 4),
            "ece_1x2": round(self.ece_1x2, 4),
            "calibration_slope": round(self.calibration_slope, 4),
            "calibration_intercept": round(self.calibration_intercept, 4),
            "sharpness": round(self.sharpness, 4),
            "temperature": round(self.temperature, 4),
        }

    def __repr__(self) -> str:
        return (
            f"CalibrationMetrics({self.model_name}, n={self.n_matches}, "
            f"exact_ll={self.exact_score_log_loss:.4f}, "
            f"rps={self.rps_1x2:.4f}, "
            f"T={self.temperature:.3f})"
        )


class ScorePMFCalibrator:
    """
    Temperature-scales a raw PMF using out-of-fold exact-score log loss.

    Parameters
    ----------
    temp_grid : list of temperatures to try
    """

    def __init__(self, temp_grid: list[float] = TEMPERATURE_GRID):
        self._temp_grid = temp_grid
        self._temperature: float = 1.0
        self._fitted = False

    def fit(
        self,
        predictions: list[ScorePMFPrediction],
        actuals: list[tuple[int, int]],  # (home_goals, away_goals)
    ) -> "ScorePMFCalibrator":
        """
        Fit temperature T by minimising exact-score log loss on OOF predictions.

        Parameters
        ----------
        predictions : list of ScorePMFPrediction (from OOF, never training data)
        actuals : corresponding (home_goals, away_goals) outcomes
        """
        if len(predictions) != len(actuals):
            raise ValueError("predictions and actuals must have the same length")
        if len(predictions) < 5:
            log.warning("Only %d matches for temperature fitting. Using T=1.0.", len(predictions))
            self._temperature = 1.0
            self._fitted = True
            return self

        pmfs = [p.score_pmf for p in predictions]
        best_T, best_loss = 1.0, float("inf")

        for T in self._temp_grid:
            loss = _mean_exact_log_loss(pmfs, actuals, T)
            if loss < best_loss:
                best_loss = loss
                best_T = T

        # Fine-tune with scipy around the grid minimum
        try:
            res = minimize_scalar(
                lambda T: _mean_exact_log_loss(pmfs, actuals, T),
                bounds=(0.3, 3.0),
                method="bounded",
            )
            if res.fun < best_loss:
                best_T = float(res.x)
        except Exception as exc:
            log.warning("Temperature fine-tuning failed: %s", exc)

        self._temperature = best_T
        self._fitted = True
        log.info("Temperature calibration: T=%.4f (exact-score LL=%.4f)", best_T, best_loss)
        return self

    def transform(self, pred: ScorePMFPrediction) -> ScorePMFPrediction:
        """Apply temperature scaling to a prediction."""
        if not self._fitted:
            raise RuntimeError("Call .fit() first.")
        scaled_pmf = _apply_temperature(pred.score_pmf, self._temperature)
        new_pred = ScorePMFPrediction(
            match_id=pred.match_id,
            home_team=pred.home_team,
            away_team=pred.away_team,
            season=pred.season,
            stage=pred.stage,
            venue=pred.venue,
            model_name=pred.model_name,
            max_goals=pred.max_goals,
            score_pmf=scaled_pmf,
            tail_mass=pred.tail_mass,
            expected_home_goals=pred.expected_home_goals,
            expected_away_goals=pred.expected_away_goals,
            calibration_status=CalibrationStatus.TEMPERATURE_SCALED,
            uncertainty=pred.uncertainty,
            warnings=pred.warnings + [f"temperature_scaled(T={self._temperature:.3f})"],
        )
        return new_pred

    @property
    def temperature(self) -> float:
        return self._temperature


def evaluate_pmf_predictions(
    predictions: list[ScorePMFPrediction],
    actuals: list[tuple[int, int]],
    model_name: str = "",
) -> CalibrationMetrics:
    """
    Compute calibration metrics for a set of OOF score-PMF predictions.

    Uses penaltyblog.metrics for RPS and Brier where available.

    IMPORTANT: Call only with out-of-fold predictions, never training data.
    """
    if len(predictions) != len(actuals):
        raise ValueError("predictions and actuals must have the same length")

    n = len(predictions)
    metrics = CalibrationMetrics(n_matches=n, model_name=model_name)

    if n == 0:
        return metrics

    # ── Exact-score log loss ────────────────────────────────────────────
    exact_lls = []
    for pred, (ah, aa) in zip(predictions, actuals):
        p = pred.exact_score(ah, aa)
        exact_lls.append(-np.log(max(p, _EPS)))
    metrics.exact_score_log_loss = float(np.mean(exact_lls))

    # ── 1X2 arrays ────────────────────────────────────────────────────────
    probs_1x2 = np.array([
        [p.derived_markets.home_win, p.derived_markets.draw, p.derived_markets.away_win]
        for p in predictions
    ], dtype=float)
    probs_1x2 = np.clip(probs_1x2, _EPS, 1.0)
    probs_1x2 /= probs_1x2.sum(axis=1, keepdims=True)

    actual_1x2 = np.array([
        [1.0 if ah > aa else 0.0, 1.0 if ah == aa else 0.0, 1.0 if ah < aa else 0.0]
        for ah, aa in actuals
    ], dtype=float)

    # ── RPS (penaltyblog) ────────────────────────────────────────────────
    try:
        rps_arr = np.zeros(n, dtype=float)
        compute_average_rps(probs_1x2, actual_1x2, n, 3)
        # penaltyblog's compute_average_rps returns a scalar
        metrics.rps_1x2 = float(compute_average_rps(probs_1x2, actual_1x2, n, 3))
    except Exception as exc:
        log.warning("penaltyblog RPS failed: %s. Using manual.", exc)
        cum_p = np.cumsum(probs_1x2, axis=1)
        cum_a = np.cumsum(actual_1x2, axis=1)
        metrics.rps_1x2 = float(np.mean(np.mean((cum_p - cum_a) ** 2, axis=1)))

    # ── Brier (penaltyblog) ──────────────────────────────────────────────
    try:
        metrics.brier_1x2 = float(compute_multiclass_brier_score(actual_1x2, probs_1x2))
    except Exception as exc:
        log.warning("penaltyblog Brier failed: %s. Using manual.", exc)
        metrics.brier_1x2 = float(np.mean(np.sum((probs_1x2 - actual_1x2) ** 2, axis=1)))

    # ── Ignorance (penaltyblog) ────────────────────────────────────────
    try:
        outcome_probs = probs_1x2[actual_1x2 > 0.5]
        metrics.ignorance_1x2 = float(np.mean([-np.log2(max(p, _EPS)) for p in outcome_probs]))
    except Exception as exc:
        log.warning("Ignorance score failed: %s", exc)

    # ── ECE ─────────────────────────────────────────────────────────────
    metrics.ece_1x2 = _compute_ece(probs_1x2[:, 0], actual_1x2[:, 0])

    # ── Calibration slope/intercept ───────────────────────────────────
    try:
        from scipy import stats
        hw_probs = probs_1x2[:, 0]
        hw_actual = actual_1x2[:, 0]
        if np.std(hw_probs) > 1e-6:
            slope, intercept, _, _, _ = stats.linregress(hw_probs, hw_actual)
            metrics.calibration_slope = float(slope)
            metrics.calibration_intercept = float(intercept)
    except Exception:
        pass

    # ── Sharpness ──────────────────────────────────────────────────────
    metrics.sharpness = float(np.mean(np.var(probs_1x2, axis=1)))

    return metrics


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _apply_temperature(pmf: np.ndarray, T: float) -> np.ndarray:
    """Temperature-scaled PMF: p_cal ∝ p_raw^(1/T)."""
    if abs(T - 1.0) < 1e-6:
        return pmf.copy()
    scaled = np.power(np.clip(pmf, 0.0, 1.0), 1.0 / T)
    s = scaled.sum()
    if s > _EPS:
        scaled /= s
    return scaled


def _mean_exact_log_loss(
    pmfs: list[np.ndarray],
    actuals: list[tuple[int, int]],
    T: float,
) -> float:
    losses = []
    for pmf, (ah, aa) in zip(pmfs, actuals):
        scaled = _apply_temperature(pmf, T)
        mg = scaled.shape[0]
        if ah < mg and aa < mg:
            p = float(scaled[ah, aa])
        else:
            p = _EPS
        losses.append(-np.log(max(p, _EPS)))
    return float(np.mean(losses))


def _compute_ece(
    probs: np.ndarray,
    outcomes: np.ndarray,
    n_bins: int = 10,
) -> float:
    """Expected Calibration Error for a binary event."""
    bins = np.linspace(0.0, 1.0, n_bins + 1)
    ece = 0.0
    n = len(probs)
    for lo, hi in zip(bins[:-1], bins[1:]):
        mask = (probs >= lo) & (probs < hi)
        if not mask.any():
            continue
        avg_prob = float(probs[mask].mean())
        avg_outcome = float(outcomes[mask].mean())
        ece += (mask.sum() / n) * abs(avg_prob - avg_outcome)
    return float(ece)
