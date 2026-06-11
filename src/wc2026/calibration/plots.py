"""Calibration visualizations."""
from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns

if TYPE_CHECKING:
    import pandas as pd
    from penaltyblog.models import FootballProbabilityGrid


def plot_reliability_diagram(
    probs: "np.ndarray",
    outcomes: "np.ndarray",
    n_bins: int = 10,
    label: str = "Model",
    ax: "plt.Axes | None" = None,
    save_path: "Path | None" = None,
) -> "plt.Axes":
    """
    Reliability diagram (calibration curve) for a binary event.

    Points above the diagonal = under-confident.
    Points below the diagonal = over-confident.
    """
    if ax is None:
        _, ax = plt.subplots(figsize=(6, 6))

    bins = np.linspace(0.0, 1.0, n_bins + 1)
    bin_means, bin_true = [], []
    for lo, hi in zip(bins[:-1], bins[1:]):
        mask = (probs >= lo) & (probs < hi)
        if mask.sum() > 0:
            bin_means.append(probs[mask].mean())
            bin_true.append(outcomes[mask].mean())

    ax.plot([0, 1], [0, 1], "k--", lw=1, label="Perfect calibration")
    ax.plot(bin_means, bin_true, "o-", label=label)
    ax.set_xlabel("Mean predicted probability")
    ax.set_ylabel("Fraction of positives")
    ax.set_title(f"Reliability diagram — {label}")
    ax.legend()
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)

    if save_path:
        plt.savefig(save_path, bbox_inches="tight", dpi=150)

    return ax


def plot_score_heatmap(
    grid: "FootballProbabilityGrid",
    home_team: str,
    away_team: str,
    max_goals: int = 7,
    ax: "plt.Axes | None" = None,
    save_path: "Path | None" = None,
) -> "plt.Axes":
    """
    Heatmap of exact-score probabilities.

    Rows = home goals (0-based), columns = away goals (0-based).
    """
    if ax is None:
        _, ax = plt.subplots(figsize=(8, 7))

    mat = grid.grid[:max_goals, :max_goals] * 100  # convert to %

    sns.heatmap(
        mat,
        annot=True,
        fmt=".1f",
        cmap="YlOrRd",
        ax=ax,
        cbar_kws={"label": "Probability (%)"},
        xticklabels=[str(i) for i in range(max_goals)],
        yticklabels=[str(i) for i in range(max_goals)],
    )
    ax.set_xlabel(f"{away_team} goals")
    ax.set_ylabel(f"{home_team} goals")
    ax.set_title(f"Score probabilities: {home_team} vs {away_team}")

    if save_path:
        plt.savefig(save_path, bbox_inches="tight", dpi=150)

    return ax


def plot_calibration_summary(
    report_df: "pd.DataFrame",
    save_path: "Path | None" = None,
) -> "plt.Figure":
    """Three-panel calibration summary: reliability diagrams for 1X2."""
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    for ax, (col, label) in zip(
        axes,
        [
            ("p_home_win", "Home Win"),
            ("p_draw", "Draw"),
            ("p_away_win", "Away Win"),
        ],
    ):
        probs = report_df[col].values
        actual = (report_df["outcome"] == col.replace("p_", "").replace("_", " ").title()).values.astype(float)
        # Fix mapping
        outcome_map = {
            "p_home_win": "home_win",
            "p_draw": "draw",
            "p_away_win": "away_win",
        }
        actual = (report_df["outcome"] == outcome_map[col]).values.astype(float)
        plot_reliability_diagram(probs, actual, label=label, ax=ax)

    fig.suptitle("1X2 Calibration — World Cup Model", fontsize=14)
    plt.tight_layout()

    if save_path:
        fig.savefig(save_path, bbox_inches="tight", dpi=150)

    return fig
