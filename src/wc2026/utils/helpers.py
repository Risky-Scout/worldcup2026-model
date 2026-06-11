"""Odds conversion and utility helpers."""
from __future__ import annotations


def american_to_prob(odds: int) -> float:
    """Convert American odds to implied probability (no vig removed)."""
    if odds > 0:
        return 100 / (odds + 100)
    else:
        return abs(odds) / (abs(odds) + 100)


def prob_to_american(prob: float) -> int:
    """Convert probability to American odds (rounded to nearest integer)."""
    if prob <= 0 or prob >= 1:
        raise ValueError("Probability must be strictly between 0 and 1.")
    if prob >= 0.5:
        return int(round(-100 * prob / (1 - prob)))
    else:
        return int(round(100 * (1 - prob) / prob))


def implied_overround(odds_list: list[int]) -> float:
    """Total implied probability across all outcomes (> 1.0 = vig)."""
    return sum(american_to_prob(o) for o in odds_list)


def fair_odds_from_model(model_prob: float, vig: float = 0.05) -> int:
    """
    Return American odds after applying a house vig.

    Parameters
    ----------
    model_prob : float
        Model's true probability estimate.
    vig : float
        Fractional margin to apply (e.g. 0.05 = 5 %).
    """
    adjusted = model_prob * (1 + vig)
    return prob_to_american(min(adjusted, 0.999))
