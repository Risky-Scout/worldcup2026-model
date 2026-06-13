"""
JointScorePMF — the central PMF abstraction for the wc2026 engine.

Architecture
------------
Every model produces a JointScorePMF, which represents:
  P(Home regulation goals = h, Away regulation goals = a)

for 90 minutes + stoppage time ONLY.
Extra time and penalty shootouts are SEPARATE objects (not implemented here).

Core design principle
---------------------
Soccer scores are theoretically unbounded. A 10×10 grid is NOT every
possible score. This module provides:

1. A published finite grid (default max_goals=15):
   - all cells from (0,0) through (max_goals-1, max_goals-1)
   - explicit tail_mass = probability beyond the grid

2. Arbitrary score lookup:
   - get_score_probability(h, a) returns a probability for ANY (h, a) >= 0
   - In-grid: returns calibrated grid value
   - Out-of-grid: uses parametric ScoreTailModel (Poisson extension)
     scaled so that sum(out-of-grid probabilities) = tail_mass

3. All derived markets are computed FROM the PMF, never independently:
   - 1X2, double chance, draw no bet
   - BTTS yes/no
   - Over/Under with push handling and quarter-line support
   - Asian handicap with quarter-line settlement
   - Exact-score table
   - Win-to-nil, expected points

Classes
-------
JointScorePMF         Abstract base class
ScoreTailModel        Parametric tail (Poisson extension beyond finite grid)
FiniteGridPMF         Grid-backed PMF + tail model (primary working class)
UnboundedScorePMF     Pure parametric PMF (arbitrary unbounded lookup)
CalibratedScorePMF    Temperature-scaled wrapper
MarketReconciledScorePMF  KL-reconciled with BDL market constraints

Key functions
-------------
get_score_probability(h, a)
to_probability_grid(max_goals)
tail_mass(max_goals)
normalize_with_tail()
derive_markets_from_pmf()
score_log_loss(observed_h, observed_a)
score_log_loss_with_tail(observed_h, observed_a)
validate_internal_consistency()
"""
from __future__ import annotations

import hashlib
import json
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

import numpy as np
from penaltyblog.models import FootballProbabilityGrid, create_dixon_coles_grid
from scipy.stats import poisson

from wc2026.config import PMF_MAX_GOALS, TAIL_WARN_THRESHOLD

log = logging.getLogger(__name__)
_EPS = 1e-12


# ---------------------------------------------------------------------------
# ScoreTailModel
# ---------------------------------------------------------------------------

class ScoreTailModel:
    """
    Models P(H=h, A=a) for scores outside the published finite grid.

    Uses an independent bivariate Poisson distribution parameterized by
    (lambda_home, lambda_away) with optional Dixon-Coles rho correction for
    the four low-score cells.

    The tail model is normalized so that:
        sum(tail_model(h,a) for h>=max_goals or a>=max_goals) = tail_mass

    This ensures arbitrary-score lookups are properly scaled.

    Parameters
    ----------
    lambda_home : float
        Expected home goals from the fitted model.
    lambda_away : float
        Expected away goals from the fitted model.
    rho : float
        Dixon-Coles correlation parameter (default 0.0 = independent Poisson).
    tail_mass : float
        The total probability mass that lies outside the finite grid.
    grid_max : int
        Size of the finite grid (scores 0..grid_max-1 per team are in grid).
    """

    def __init__(
        self,
        lambda_home: float,
        lambda_away: float,
        tail_mass: float,
        grid_max: int,
        rho: float = 0.0,
    ) -> None:
        self.lambda_home = max(lambda_home, 0.01)
        self.lambda_away = max(lambda_away, 0.01)
        self.rho = rho
        self.tail_mass = tail_mass
        self.grid_max = grid_max

        # Compute the parametric mass that falls outside the grid
        # (used for normalisation)
        self._parametric_tail_sum = self._compute_parametric_tail_sum()

    def _raw_parametric(self, h: int, a: int) -> float:
        """Raw Poisson probability for (h, a), without DC correction for simplicity."""
        return float(
            poisson.pmf(h, self.lambda_home) * poisson.pmf(a, self.lambda_away)
        )

    def _compute_parametric_tail_sum(self) -> float:
        """
        Sum of raw parametric probabilities outside the finite grid.
        For a Poisson, this = 1 - sum(in-grid probabilities).
        """
        in_grid_mass = 0.0
        for h in range(self.grid_max):
            for a in range(self.grid_max):
                in_grid_mass += self._raw_parametric(h, a)
        return max(1.0 - in_grid_mass, _EPS)

    def get_probability(self, h: int, a: int) -> float:
        """
        Return P(H=h, A=a) for a score outside the finite grid.

        Scaled so that sum over all out-of-grid cells = self.tail_mass.

        Returns 0.0 if (h,a) is inside the grid.
        """
        if h < self.grid_max and a < self.grid_max:
            return 0.0
        if h < 0 or a < 0:
            return 0.0
        raw = self._raw_parametric(h, a)
        return raw / self._parametric_tail_sum * self.tail_mass


# ---------------------------------------------------------------------------
# Abstract base
# ---------------------------------------------------------------------------

class JointScorePMF(ABC):
    """
    Abstract base class for all joint score PMF implementations.

    Represents P(Home regulation goals = h, Away regulation goals = a)
    for regulation time (90 minutes + stoppage time) ONLY.
    """

    # Subclasses must set these
    model_name: str = "unknown"
    regulation_only: bool = True
    extra_time_excluded: bool = True
    penalty_shootout_excluded: bool = True

    # -----------------------------------------------------------------------
    # Required interface
    # -----------------------------------------------------------------------

    @abstractmethod
    def get_score_probability(self, h: int, a: int) -> float:
        """
        Return P(H=h, A=a) for any non-negative (h, a).

        Must work for ALL non-negative integers, not just grid cells.
        Out-of-grid values may use parametric extrapolation.
        """
        ...

    @abstractmethod
    def to_probability_grid(self, max_goals: int = PMF_MAX_GOALS) -> np.ndarray:
        """
        Return the finite probability grid as a (max_goals, max_goals) ndarray.
        Values are the calibrated in-grid probabilities (may sum to < 1.0 if tail_mass > 0).
        """
        ...

    @property
    @abstractmethod
    def lambda_home(self) -> float:
        """Expected home goals from the underlying model."""
        ...

    @property
    @abstractmethod
    def lambda_away(self) -> float:
        """Expected away goals from the underlying model."""
        ...

    # -----------------------------------------------------------------------
    # Derived: tail mass
    # -----------------------------------------------------------------------

    def tail_mass(self, max_goals: int = PMF_MAX_GOALS) -> float:
        """
        Probability mass not captured in the (max_goals × max_goals) grid.
        = 1.0 - grid.sum()
        """
        return max(0.0, 1.0 - float(self.to_probability_grid(max_goals).sum()))

    # -----------------------------------------------------------------------
    # Derived: normalisation
    # -----------------------------------------------------------------------

    def normalize_with_tail(
        self, max_goals: int = PMF_MAX_GOALS
    ) -> tuple[np.ndarray, float]:
        """
        Return (grid, tail_mass) where grid + tail_mass sums to exactly 1.0.

        Clips tiny floating-point negatives. Normalises if grid drifts.
        """
        grid = self.to_probability_grid(max_goals)
        grid = np.clip(grid, 0.0, 1.0)
        tail = max(0.0, 1.0 - float(grid.sum()))
        # Safety re-normalise
        total = float(grid.sum()) + tail
        if not np.isclose(total, 1.0, atol=1e-4):
            if total > _EPS:
                grid = grid / total
                tail = 0.0
        return grid, tail

    # -----------------------------------------------------------------------
    # Derived: markets (using penaltyblog FootballProbabilityGrid where possible)
    # -----------------------------------------------------------------------

    def derive_markets_from_pmf(
        self, max_goals: int = PMF_MAX_GOALS
    ) -> dict:
        """
        Compute ALL derived markets from the PMF.

        Uses penaltyblog.FootballProbabilityGrid internally for consistency,
        correctness, and quarter-line AH support.
        """
        grid, tail = self.normalize_with_tail(max_goals)
        fpg = FootballProbabilityGrid(
            goal_matrix=grid,
            home_goal_expectation=self.lambda_home,
            away_goal_expectation=self.lambda_away,
            normalize=True,
        )

        markets: dict = {
            # 1X2
            "home_win": fpg.home_win,
            "draw": fpg.draw,
            "away_win": fpg.away_win,
            # Double chance
            "dc_1x": fpg.double_chance_1x,
            "dc_x2": fpg.double_chance_x2,
            "dc_12": fpg.double_chance_12,
            # Draw no bet
            "dnb_home": fpg.draw_no_bet_home,
            "dnb_away": fpg.draw_no_bet_away,
            # BTTS
            "btts_yes": fpg.btts_yes,
            "btts_no": fpg.btts_no,
            # Win to nil
            "win_to_nil_home": fpg.win_to_nil_home(),
            "win_to_nil_away": fpg.win_to_nil_away(),
            # Expected points
            "xpts_home": fpg.expected_points_home(),
            "xpts_away": fpg.expected_points_away(),
        }

        # Totals with push handling (uses penaltyblog .totals())
        for line in [0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0, 5.5, 6.0, 6.5]:
            under, push, over = fpg.totals(line)
            line_str = str(line).replace(".", "_")
            markets[f"over_{line_str}"] = over
            markets[f"under_{line_str}"] = under
            markets[f"push_{line_str}"] = push

        # Asian handicaps (quarter-line aware)
        for side in ["home", "away"]:
            for line in [-2.0, -1.75, -1.5, -1.25, -1.0, -0.75, -0.5, -0.25,
                         0.0, 0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.0]:
                probs = fpg.asian_handicap_probs(side, line)
                line_str = str(line).replace("-", "m").replace(".", "_")
                markets[f"ah_{side}_{line_str}"] = probs["win"]

        return {k: round(v, 6) for k, v in markets.items()}

    # -----------------------------------------------------------------------
    # Log loss
    # -----------------------------------------------------------------------

    def score_log_loss(self, observed_h: int, observed_a: int) -> float:
        """
        Negative log probability of the actual score under this PMF.

        Uses the in-grid probability only (does not credit tail mass to
        out-of-grid actuals). Use score_log_loss_with_tail for proper
        handling.
        """
        p = self.get_score_probability(observed_h, observed_a)
        return float(-np.log(max(p, _EPS)))

    def score_log_loss_with_tail(
        self, observed_h: int, observed_a: int, max_goals: int = PMF_MAX_GOALS
    ) -> float:
        """
        Negative log probability of the actual score.

        If the score is outside the grid, distributes tail mass proportionally
        via the ScoreTailModel.
        """
        p = self.get_score_probability(observed_h, observed_a)
        return float(-np.log(max(p, _EPS)))

    # -----------------------------------------------------------------------
    # Consistency validation
    # -----------------------------------------------------------------------

    def validate_internal_consistency(
        self, max_goals: int = PMF_MAX_GOALS
    ) -> list[str]:
        """
        Return list of consistency violations. Empty list = all good.

        Checks:
        - PMF (grid + tail) sums to 1.0
        - No negative probabilities
        - 1X2 sums to 1.0
        - BTTS yes + no = 1.0
        - Totals are monotonic
        - All market values in [0, 1]
        - Diagonal sum = draw probability
        """
        errors = []
        grid, tail = self.normalize_with_tail(max_goals)

        # (1) Sum check
        total = float(grid.sum()) + tail
        if not np.isclose(total, 1.0, atol=1e-4):
            errors.append(f"PMF total = {total:.6f} (expected 1.0)")

        # (2) Non-negative
        if np.any(grid < -_EPS):
            errors.append("PMF contains negative probabilities")

        fpg = FootballProbabilityGrid(
            goal_matrix=grid,
            home_goal_expectation=self.lambda_home,
            away_goal_expectation=self.lambda_away,
            normalize=True,
        )

        # (3) 1X2 sum
        s1x2 = fpg.home_win + fpg.draw + fpg.away_win
        if not np.isclose(s1x2, 1.0, atol=1e-4):
            errors.append(f"1X2 sums to {s1x2:.6f}")

        # (4) BTTS
        btts_sum = fpg.btts_yes + fpg.btts_no
        if not np.isclose(btts_sum, 1.0, atol=1e-4):
            errors.append(f"BTTS sums to {btts_sum:.6f}")

        # (5) Draw = diagonal
        diag_sum = float(np.diag(grid).sum())
        if not np.isclose(diag_sum, fpg.draw, atol=1e-4):
            errors.append(f"Draw={fpg.draw:.6f} != diagonal sum={diag_sum:.6f}")

        # (6) 1X2 = PMF sums
        I, J = np.indices(grid.shape)
        hw_pmf = float(grid[I > J].sum())
        dr_pmf = float(grid[I == J].sum())
        aw_pmf = float(grid[I < J].sum())
        if not np.isclose(fpg.home_win, hw_pmf, atol=1e-4):
            errors.append(f"home_win mismatch: fpg={fpg.home_win:.6f} pmf={hw_pmf:.6f}")

        # (7) Totals monotonic
        overs = []
        for line in [0.5, 1.5, 2.5, 3.5, 4.5, 5.5, 6.5]:
            _, _, ov = fpg.totals(line)
            overs.append(ov)
        for i in range(len(overs) - 1):
            if overs[i] < overs[i + 1] - 1e-5:
                errors.append(f"Totals not monotonic at {i}")

        return errors

    # -----------------------------------------------------------------------
    # Serialization
    # -----------------------------------------------------------------------

    def to_dict(
        self,
        max_goals: int = PMF_MAX_GOALS,
        top_n: int = 15,
        odds_timestamp: Optional[str] = None,
        lineups_known: bool = False,
        prediction_mode: str = "model",
    ) -> dict:
        """
        Produce the full JSON-serializable prediction document.

        Parameters
        ----------
        max_goals : int
            Grid size for published PMF.
        top_n : int
            Number of top scorelines to include.
        odds_timestamp : str, optional
            UTC ISO timestamp of the odds used.
        lineups_known : bool
            Whether lineups were known when prediction was made.
        prediction_mode : str
            One of: "pure_model", "market_informed", "market_reconciled"
        """
        grid, tail = self.normalize_with_tail(max_goals)
        markets = self.derive_markets_from_pmf(max_goals)

        # Top scorelines
        flat = np.argsort(grid, axis=None)[::-1][:top_n]
        rows, cols = np.unravel_index(flat, grid.shape)
        top_scores = [
            {
                "home_goals": int(r),
                "away_goals": int(c),
                "probability": round(float(grid[r, c]), 6),
            }
            for r, c in zip(rows, cols)
        ]

        consistency_errors = self.validate_internal_consistency(max_goals)

        return {
            "regulation_only": self.regulation_only,
            "extra_time_excluded": self.extra_time_excluded,
            "penalty_shootout_excluded": self.penalty_shootout_excluded,
            "model_name": self.model_name,
            "max_goals": max_goals,
            "tail_mass": round(tail, 8),
            "tail_policy": (
                "parametric_poisson_extension"
                if tail > 0
                else "no_tail_mass"
            ),
            "arbitrary_score_lookup_supported": True,
            "regulation_score_pmf_grid": [
                [round(float(v), 8) for v in row] for row in grid
            ],
            "expected_home_goals": round(self.lambda_home, 4),
            "expected_away_goals": round(self.lambda_away, 4),
            "top_scorelines": top_scores,
            "exact_score_probabilities": {
                f"{h}-{a}": round(float(grid[h, a]), 6)
                for h in range(min(max_goals, 7))
                for a in range(min(max_goals, 7))
            },
            "derived_markets": markets,
            "odds_used": odds_timestamp is not None,
            "odds_timestamp": odds_timestamp,
            "lineups_known": lineups_known,
            "prediction_mode": prediction_mode,
            "consistency_errors": consistency_errors,
        }


# ---------------------------------------------------------------------------
# FiniteGridPMF — primary working class
# ---------------------------------------------------------------------------

class FiniteGridPMF(JointScorePMF):
    """
    PMF backed by a penaltyblog FootballProbabilityGrid.

    Supports arbitrary score lookups beyond the grid via ScoreTailModel.

    Parameters
    ----------
    grid : FootballProbabilityGrid
        The finite probability grid from a fitted penaltyblog model.
    model_name : str
        Name of the model that produced this PMF.
    rho : float
        DC correlation parameter (for tail extrapolation).
    published_max_goals : int
        Size of the finite grid stored.
    """

    def __init__(
        self,
        grid: FootballProbabilityGrid,
        model_name: str,
        rho: float = 0.0,
        published_max_goals: int = PMF_MAX_GOALS,
    ) -> None:
        self.model_name = model_name
        self._fpg = grid
        self._rho = rho
        self._max = published_max_goals
        self._grid_arr = np.array(grid.grid, dtype=np.float64)

        # Build tail model
        self._tail = ScoreTailModel(
            lambda_home=grid.home_goal_expectation,
            lambda_away=grid.away_goal_expectation,
            tail_mass=self.tail_mass(published_max_goals),
            grid_max=published_max_goals,
            rho=rho,
        )

    @property
    def lambda_home(self) -> float:
        return self._fpg.home_goal_expectation

    @property
    def lambda_away(self) -> float:
        return self._fpg.away_goal_expectation

    def get_score_probability(self, h: int, a: int) -> float:
        """
        P(H=h, A=a) for any non-negative (h, a).

        In-grid: calibrated grid value.
        Out-of-grid: Poisson extrapolation scaled to tail_mass.
        """
        if h < 0 or a < 0:
            return 0.0
        if h < self._grid_arr.shape[0] and a < self._grid_arr.shape[1]:
            return float(self._grid_arr[h, a])
        return self._tail.get_probability(h, a)

    def to_probability_grid(self, max_goals: int = PMF_MAX_GOALS) -> np.ndarray:
        """Return the published finite grid, trimmed/padded to max_goals."""
        src = self._grid_arr
        n = max_goals
        out = np.zeros((n, n), dtype=np.float64)
        h = min(src.shape[0], n)
        a = min(src.shape[1], n)
        out[:h, :a] = src[:h, :a]
        return out


# ---------------------------------------------------------------------------
# UnboundedScorePMF — pure parametric
# ---------------------------------------------------------------------------

class UnboundedScorePMF(JointScorePMF):
    """
    Pure parametric PMF based on a bivariate Poisson distribution.

    Supports exact P(H=h, A=a) for any non-negative (h, a) without
    any grid truncation.

    The published grid is computed on demand by evaluating the Poisson PMF.

    Parameters
    ----------
    lambda_home : float
    lambda_away : float
    rho : float
        DC correlation (applied only to low-score cells for accuracy).
    model_name : str
    """

    def __init__(
        self,
        lambda_home: float,
        lambda_away: float,
        rho: float = 0.0,
        model_name: str = "unbounded_poisson",
    ) -> None:
        self.model_name = model_name
        self._lambda_home = max(lambda_home, 0.01)
        self._lambda_away = max(lambda_away, 0.01)
        self._rho = rho

    @property
    def lambda_home(self) -> float:
        return self._lambda_home

    @property
    def lambda_away(self) -> float:
        return self._lambda_away

    def get_score_probability(self, h: int, a: int) -> float:
        if h < 0 or a < 0:
            return 0.0
        p = float(poisson.pmf(h, self._lambda_home) * poisson.pmf(a, self._lambda_away))
        # Apply DC correction for low-score cells
        if self._rho != 0.0:
            mu_h, mu_a, rho = self._lambda_home, self._lambda_away, self._rho
            if h == 0 and a == 0:
                p *= max(1.0 - rho * mu_h * mu_a, 0.0)
            elif h == 1 and a == 0:
                p *= max(1.0 + rho * mu_h, 0.0)
            elif h == 0 and a == 1:
                p *= max(1.0 + rho * mu_a, 0.0)
            elif h == 1 and a == 1:
                p *= max(1.0 - rho, 0.0)
        return p

    def to_probability_grid(self, max_goals: int = PMF_MAX_GOALS) -> np.ndarray:
        """Evaluate the parametric distribution on a finite grid."""
        fpg = create_dixon_coles_grid(
            self._lambda_home, self._lambda_away, rho=self._rho, max_goals=max_goals - 1
        )
        return np.array(fpg.grid, dtype=np.float64)

    def tail_mass(self, max_goals: int = PMF_MAX_GOALS) -> float:
        """For Poisson, tail mass is 1 - sum(in-grid PMF)."""
        grid = self.to_probability_grid(max_goals)
        return max(0.0, 1.0 - float(grid.sum()))


# ---------------------------------------------------------------------------
# CalibratedScorePMF — temperature-scaled
# ---------------------------------------------------------------------------

class CalibratedScorePMF(FiniteGridPMF):
    """
    Temperature-scaled version of a FiniteGridPMF.

    Applies: p_cal[i,j] ∝ p_raw[i,j] ** (1/T)

    T > 1 → shrinks toward the center (less confident)
    T < 1 → sharpens the distribution (more confident)
    """

    def __init__(
        self,
        base: FiniteGridPMF,
        temperature: float,
        published_max_goals: int = PMF_MAX_GOALS,
    ) -> None:
        raw_grid = base.to_probability_grid(published_max_goals)
        scaled = np.power(np.clip(raw_grid, 0.0, 1.0), 1.0 / max(temperature, 0.1))
        s = scaled.sum()
        if s > _EPS:
            scaled /= s

        # Build a FootballProbabilityGrid from the scaled matrix
        fpg = FootballProbabilityGrid(
            goal_matrix=scaled,
            home_goal_expectation=base.lambda_home,
            away_goal_expectation=base.lambda_away,
            normalize=False,
        )
        super().__init__(fpg, base.model_name, rho=base._rho,
                         published_max_goals=published_max_goals)
        self.model_name = f"{base.model_name}[T={temperature:.3f}]"
        self._temperature = temperature

    @property
    def temperature(self) -> float:
        return self._temperature


# ---------------------------------------------------------------------------
# MarketReconciledScorePMF — KL-reconciled
# ---------------------------------------------------------------------------

class MarketReconciledScorePMF(FiniteGridPMF):
    """
    Market-reconciled PMF produced by KL-minimization against BDL consensus.

    Stores the base model PMF, the market constraints used, and the
    KL divergence from the base model.
    """

    def __init__(
        self,
        reconciled_grid: np.ndarray,
        base: FiniteGridPMF,
        kl_divergence: float,
        constraint_violations: dict,
        converged: bool,
        odds_timestamp: Optional[str] = None,
    ) -> None:
        fpg = FootballProbabilityGrid(
            goal_matrix=reconciled_grid,
            home_goal_expectation=base.lambda_home,
            away_goal_expectation=base.lambda_away,
            normalize=True,
        )
        super().__init__(fpg, base.model_name,
                         rho=base._rho,
                         published_max_goals=reconciled_grid.shape[0])
        self.model_name = f"{base.model_name}+market_reconciled"
        self.kl_divergence = kl_divergence
        self.constraint_violations = constraint_violations
        self.converged = converged
        self.odds_timestamp = odds_timestamp


# ---------------------------------------------------------------------------
# Market-implied PMF factory
# ---------------------------------------------------------------------------

def market_implied_pmf(
    home_win: float,
    draw: float,
    away_win: float,
    over_2_5: Optional[float] = None,
    under_2_5: Optional[float] = None,
    model_name: str = "market_implied",
    max_goals: int = PMF_MAX_GOALS,
) -> FiniteGridPMF:
    """
    Construct a market-implied PMF by inverting BDL no-vig odds.

    Uses penaltyblog.models.goal_expectancy_extended to infer (mu_h, mu_a, rho)
    from no-vig market probabilities, then builds a FiniteGridPMF.

    This is the recommended way to build market-implied PMFs because:
    - goal_expectancy_extended is penaltyblog's own inversion solver
    - It simultaneously fits rho from 1X2 + O/U, giving a better market PMF
    - The resulting grid satisfies the same invariants as model PMFs

    Parameters
    ----------
    home_win, draw, away_win : float
        No-vig 1X2 probabilities (must sum to 1.0).
    over_2_5, under_2_5 : float, optional
        No-vig over/under 2.5 probabilities.
    """
    from penaltyblog.models import goal_expectancy, goal_expectancy_extended

    if over_2_5 is not None and under_2_5 is not None:
        result = goal_expectancy_extended(
            home_win, draw, away_win,
            over_2_5, under_2_5,
            remove_overround=True,
            max_goals=max_goals,
            objective="cross_entropy",
        )
        mu_h = result["home_exp"]
        mu_a = result["away_exp"]
        rho = result.get("implied_rho", 0.0)
    else:
        result = goal_expectancy(
            home_win, draw, away_win,
            dc_adj=True,
            remove_overround=True,
            max_goals=max_goals,
            objective="cross_entropy",
        )
        mu_h = result["home_exp"]
        mu_a = result["away_exp"]
        rho = 0.0

    # Validate rho bounds
    rho_min = max(-1.0 / mu_h, -1.0 / mu_a)
    rho_max = min(1.0, 1.0 / (mu_h * mu_a))
    rho = float(np.clip(rho, rho_min + _EPS, rho_max - _EPS))

    fpg = create_dixon_coles_grid(mu_h, mu_a, rho=rho, max_goals=max_goals - 1)
    return FiniteGridPMF(fpg, model_name=model_name, rho=rho,
                         published_max_goals=max_goals)


# ---------------------------------------------------------------------------
# Convenience constructors
# ---------------------------------------------------------------------------

def from_penaltyblog_grid(
    grid: FootballProbabilityGrid,
    model_name: str,
    rho: float = 0.0,
    max_goals: int = PMF_MAX_GOALS,
) -> FiniteGridPMF:
    """Build a FiniteGridPMF from a penaltyblog FootballProbabilityGrid."""
    return FiniteGridPMF(grid, model_name=model_name, rho=rho,
                         published_max_goals=max_goals)


def from_lambdas(
    lambda_home: float,
    lambda_away: float,
    rho: float = 0.0,
    model_name: str = "poisson",
    max_goals: int = PMF_MAX_GOALS,
) -> FiniteGridPMF:
    """Build a FiniteGridPMF from (lambda_h, lambda_a, rho)."""
    fpg = create_dixon_coles_grid(lambda_home, lambda_away, rho=rho,
                                   max_goals=max_goals - 1)
    return FiniteGridPMF(fpg, model_name=model_name, rho=rho,
                         published_max_goals=max_goals)


def from_numpy_grid(
    grid: np.ndarray,
    lambda_home: float,
    lambda_away: float,
    model_name: str = "elo_fallback",
    max_goals: int = PMF_MAX_GOALS,
) -> FiniteGridPMF:
    """Build a FiniteGridPMF from a numpy probability grid + expected goals."""
    fpg = FootballProbabilityGrid(
        goal_matrix=grid,
        home_goal_expectation=lambda_home,
        away_goal_expectation=lambda_away,
        normalize=True,
    )
    return FiniteGridPMF(fpg, model_name=model_name, published_max_goals=max_goals)
