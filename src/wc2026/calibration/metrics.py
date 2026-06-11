"""
Calibration and accuracy metrics for the World Cup model.

Metrics implemented
-------------------
- Brier Score (overall and per-market)
- Log Loss (also called ignorance score / negative log probability)
- RPS — Ranked Probability Score for ordered outcomes (1X2 three-way)
- ECE — Expected Calibration Error (reliability)
- Resolution — variance of predicted probabilities (sharpness)

All metrics follow the convention: *lower is better*.

CalibrationReport
-----------------
Takes an EnsembleModel and a holdout DataFrame and computes all metrics
in a single pass, returning a summary dict and a per-match DataFrame.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

import numpy as np
import pandas as pd

if TYPE_CHECKING:
    from wc2026.models.ensemble import EnsembleModel

_EPS = 1e-9


@dataclass
class CalibrationReport:
    """
    Evaluate the ensemble model on a holdout set of completed matches.

    Parameters
    ----------
    model : EnsembleModel
        Fitted ensemble model.
    df : pd.DataFrame
        Holdout matches (same schema as training data).
    max_goals : int
        Maximum goals to consider in score grid.
    """

    model: "EnsembleModel"
    df: pd.DataFrame
    max_goals: int = 10

    # Populated by evaluate()
    summary: dict = field(default_factory=dict, init=False)
    per_match: pd.DataFrame = field(default_factory=pd.DataFrame, init=False)

    def evaluate(self) -> "CalibrationReport":
        rows = []
        for _, row in self.df.iterrows():
            ht = row["home_team"]
            at = row["away_team"]
            actual_h = int(row["home_goals"])
            actual_a = int(row["away_goals"])
            neutral = bool(row["is_neutral"])

            try:
                grid = self.model.predict(ht, at, self.max_goals, neutral)
            except Exception:
                continue

            p_hw = grid.home_win
            p_draw = grid.draw
            p_aw = grid.away_win

            if actual_h > actual_a:
                outcome = "home_win"
            elif actual_h == actual_a:
                outcome = "draw"
            else:
                outcome = "away_win"

            # Exact score probability
            p_exact = grid.exact_score(actual_h, actual_a)

            # 1X2 Brier Score
            probs_1x2 = np.array([p_hw, p_draw, p_aw], dtype=float)
            probs_1x2 = np.clip(probs_1x2, _EPS, 1.0)
            actual_1x2 = np.array(
                [1.0 if outcome == k else 0.0 for k in ("home_win", "draw", "away_win")]
            )
            brier_1x2 = float(np.mean((probs_1x2 - actual_1x2) ** 2))

            # RPS
            rps = _rps(probs_1x2, actual_1x2)

            # Log loss (outcome)
            p_correct = probs_1x2[np.argmax(actual_1x2)]
            logloss_outcome = -np.log(max(p_correct, _EPS))

            # Log loss (exact score)
            logloss_exact = -np.log(max(p_exact, _EPS))

            rows.append(
                {
                    "home_team": ht,
                    "away_team": at,
                    "actual_home": actual_h,
                    "actual_away": actual_a,
                    "outcome": outcome,
                    "p_home_win": p_hw,
                    "p_draw": p_draw,
                    "p_away_win": p_aw,
                    "p_exact_score": p_exact,
                    "brier_1x2": brier_1x2,
                    "rps": rps,
                    "logloss_outcome": logloss_outcome,
                    "logloss_exact": logloss_exact,
                    "pred_home_xg": grid.home_goal_expectation,
                    "pred_away_xg": grid.away_goal_expectation,
                }
            )

        self.per_match = pd.DataFrame(rows)

        if self.per_match.empty:
            self.summary = {}
            return self

        self.summary = {
            "n_matches": len(self.per_match),
            "mean_brier_1x2": self.per_match["brier_1x2"].mean(),
            "mean_rps": self.per_match["rps"].mean(),
            "mean_logloss_outcome": self.per_match["logloss_outcome"].mean(),
            "mean_logloss_exact": self.per_match["logloss_exact"].mean(),
            "mean_p_exact_score": self.per_match["p_exact_score"].mean(),
            "ece_home_win": _ece(
                self.per_match["p_home_win"].values,
                (self.per_match["outcome"] == "home_win").values.astype(float),
            ),
            "ece_draw": _ece(
                self.per_match["p_draw"].values,
                (self.per_match["outcome"] == "draw").values.astype(float),
            ),
            "ece_away_win": _ece(
                self.per_match["p_away_win"].values,
                (self.per_match["outcome"] == "away_win").values.astype(float),
            ),
        }
        return self

    def __repr__(self) -> str:
        if not self.summary:
            return "CalibrationReport(not evaluated)"
        lines = ["CalibrationReport", "=" * 40]
        for k, v in self.summary.items():
            if isinstance(v, float):
                lines.append(f"  {k:<30} {v:.4f}")
            else:
                lines.append(f"  {k:<30} {v}")
        return "\n".join(lines)


# ------------------------------------------------------------------
# Standalone metric functions
# ------------------------------------------------------------------


def brier_score(probabilities: np.ndarray, outcomes: np.ndarray) -> float:
    """Mean Brier Score across a sequence of binary events."""
    return float(np.mean((probabilities - outcomes) ** 2))


def log_loss(probabilities: np.ndarray, outcomes: np.ndarray) -> float:
    """Mean log loss (negative log probability of the true outcome)."""
    p = np.clip(probabilities, _EPS, 1.0)
    return float(-np.mean(outcomes * np.log(p) + (1 - outcomes) * np.log(1 - p)))


def rps_series(
    probs_matrix: np.ndarray, outcomes_matrix: np.ndarray
) -> np.ndarray:
    """
    RPS for each row of a (N × K) probability matrix.

    Parameters
    ----------
    probs_matrix : (N, K)
        Predicted probabilities for K ordered categories.
    outcomes_matrix : (N, K)
        One-hot encoded actual outcomes.

    Returns
    -------
    np.ndarray of shape (N,) with per-sample RPS.
    """
    cum_p = np.cumsum(probs_matrix, axis=1)
    cum_o = np.cumsum(outcomes_matrix, axis=1)
    return np.mean((cum_p - cum_o) ** 2, axis=1)


def _rps(probs: np.ndarray, actual: np.ndarray) -> float:
    cum_p = np.cumsum(probs)
    cum_a = np.cumsum(actual)
    return float(np.mean((cum_p - cum_a) ** 2))


def _ece(probs: np.ndarray, outcomes: np.ndarray, n_bins: int = 10) -> float:
    """Expected Calibration Error (binned)."""
    bins = np.linspace(0.0, 1.0, n_bins + 1)
    ece = 0.0
    n = len(probs)
    for lo, hi in zip(bins[:-1], bins[1:]):
        mask = (probs >= lo) & (probs < hi)
        if not mask.any():
            continue
        avg_prob = probs[mask].mean()
        avg_outcome = outcomes[mask].mean()
        ece += (mask.sum() / n) * abs(avg_prob - avg_outcome)
    return float(ece)
