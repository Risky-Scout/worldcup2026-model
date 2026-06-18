"""
Single import point for all penaltyblog functionality used in this repo.
Do not import penaltyblog directly anywhere else in production code.
All penaltyblog calls go through this adapter.
"""
from __future__ import annotations
from typing import Optional
import numpy as np

# ── ratings ──────────────────────────────────────────────────────────────
try:
    from penaltyblog.ratings import PiRatingSystem as _PiRatingSystem
    HAS_PI = True
except ImportError:
    HAS_PI = False
    _PiRatingSystem = None  # type: ignore

try:
    from penaltyblog.ratings import EloRatingSystem as _EloRatingSystem
    HAS_ELO = True
except ImportError:
    HAS_ELO = False
    _EloRatingSystem = None  # type: ignore

try:
    from penaltyblog.ratings import MasseyRatingSystem as _MasseyRatingSystem
    HAS_MASSEY = True
except ImportError:
    HAS_MASSEY = False
    _MasseyRatingSystem = None  # type: ignore

try:
    from penaltyblog.ratings import ColleyRatingSystem as _ColleyRatingSystem
    HAS_COLLEY = True
except ImportError:
    HAS_COLLEY = False
    _ColleyRatingSystem = None  # type: ignore

# ── models / probability grid ─────────────────────────────────────────────
try:
    from penaltyblog.models import FootballProbabilityGrid as _FootballProbabilityGrid
    HAS_GRID = True
except ImportError:
    HAS_GRID = False
    _FootballProbabilityGrid = None  # type: ignore

try:
    from penaltyblog.models import create_dixon_coles_grid as _create_dc_grid
    HAS_DC = True
except ImportError:
    HAS_DC = False
    _create_dc_grid = None  # type: ignore

try:
    from penaltyblog.models import goal_expectancy as _goal_expectancy
    from penaltyblog.models import goal_expectancy_extended as _goal_expectancy_extended
    HAS_GOAL_EXP = True
except ImportError:
    HAS_GOAL_EXP = False
    _goal_expectancy = _goal_expectancy_extended = None  # type: ignore

# ── implied ───────────────────────────────────────────────────────────────
try:
    from penaltyblog.implied import calculate_implied as _calculate_implied
    HAS_IMPLIED = True
except ImportError:
    HAS_IMPLIED = False
    _calculate_implied = None  # type: ignore


# ── Public API ────────────────────────────────────────────────────────────

def create_pi_rating_system(k: float = 0.1):
    """Return a new PiRatingSystem instance, or None if not available."""
    if not HAS_PI:
        return None
    return _PiRatingSystem(k=k)


def create_elo_rating_system(**kwargs):
    if not HAS_ELO:
        return None
    return _EloRatingSystem(**kwargs)


def create_massey_rating_system(**kwargs):
    if not HAS_MASSEY:
        return None
    return _MasseyRatingSystem(**kwargs)


def create_colley_rating_system(**kwargs):
    if not HAS_COLLEY:
        return None
    return _ColleyRatingSystem(**kwargs)


def create_probability_grid(lambda_home: float, lambda_away: float, rho: float = 0.0, max_goals: int = 10):
    """Return a FootballProbabilityGrid, or None if not available."""
    if not HAS_GRID:
        return None
    return _FootballProbabilityGrid(lambda_home, lambda_away, rho=rho, max_goals=max_goals)


def create_dixon_coles_grid(lambda_home: float, lambda_away: float, rho: float = 0.0, max_goals: int = 10):
    if not HAS_DC:
        return None
    return _create_dc_grid(lambda_home, lambda_away, rho=rho, max_goals=max_goals)


def goal_expectancy_1x2(p_home: float, p_draw: float, p_away: float) -> Optional[dict]:
    if not HAS_GOAL_EXP:
        return None
    try:
        return _goal_expectancy(p_home, p_draw, p_away)
    except Exception:
        return None


def goal_expectancy_1x2_ou25(
    p_home: float, p_draw: float, p_away: float, p_over_25: float
) -> Optional[dict]:
    if not HAS_GOAL_EXP:
        return None
    try:
        return _goal_expectancy_extended(p_home, p_draw, p_away, p_over_25)
    except Exception:
        return None


def calculate_no_vig_probabilities(odds: list[float], method: str = "shin") -> Optional[list[float]]:
    """De-vig a set of decimal odds. Returns list of fair probabilities."""
    if not HAS_IMPLIED:
        # Basic additive fallback
        raws = [1.0/o for o in odds if o > 0]
        if len(raws) != len(odds):
            return None
        total = sum(raws)
        return [r/total for r in raws]
    try:
        return list(_calculate_implied(odds, method=method))
    except Exception:
        raws = [1.0/o for o in odds if o > 0]
        total = sum(raws)
        return [r/total for r in raws]
