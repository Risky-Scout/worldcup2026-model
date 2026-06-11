"""
Live in-game prediction engine.

Theory
------
Given a pre-game model that estimated (λ_h, λ_a) — the home and away
expected goals for the full 90 minutes — we update the prediction
at minute t with current score (g_h, g_a) as follows:

1.  Time adjustment: goals follow a Poisson process over [0, 90].
    At minute t, the remaining intensity over [t, 90] is proportional
    to (90 - t) / 90.  We scale:

        λ_h_remaining = λ_h * (90 - t) / 90
        λ_a_remaining = λ_a * (90 - t) / 90

2.  xG momentum adjustment: if live team_match_stats xG data is
    available, we blend the in-game xG rate with the pre-game lambda
    using an α weight that increases with time played:

        α = min(t / 45, 1.0)  # fully trust in-game xG after 45 min
        λ_h_live = (1 - α) * λ_h_pre + α * (live_xg_h / t * (90 - t))
        λ_a_live = (1 - α) * λ_a_pre + α * (live_xg_a / t * (90 - t))

3.  Shot momentum adjustment: the per-minute momentum signal (positive
    = home favoured) shifts the lambda ratio slightly:

        momentum_factor = 1 + 0.02 * mean_momentum_last_5min
        λ_h_live *= momentum_factor  (capped at ±20%)

4.  The final grid is P(home adds i more goals, away adds j more goals)
    computed from a Dixon-Coles grid with the updated lambdas and rho.

5.  The conditional score distribution is then:
        P(final = (g_h + i, g_a + j)) = P(remaining_h = i, remaining_a = j)

All of this is wrapped by LivePredictor which polls the BDL API and
returns a FootballProbabilityGrid on demand.
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import numpy as np
from penaltyblog.models import FootballProbabilityGrid, create_dixon_coles_grid

if TYPE_CHECKING:
    from wc2026.data.fetcher import DataFetcher
    from wc2026.models.ensemble import EnsembleModel

log = logging.getLogger(__name__)

_MAX_GOALS_LIVE = 8  # remaining goals; unlikely to exceed 8 in remaining time
_MOMENTUM_WEIGHT = 0.02
_MOMENTUM_CAP = 0.20  # max ±20% momentum adjustment
_XG_BLEND_HALFLIFE = 45.0  # minutes until full trust in live xG


class LivePredictor:
    """
    Poll BDL for live match state and update scoreline probabilities.

    Parameters
    ----------
    model : EnsembleModel
        Pre-game fitted model.
    fetcher : DataFetcher
        Data fetcher (live calls bypass cache).
    rho : float
        Dixon-Coles rho to use for the remaining-goals grid.
        Default -0.08 (slight negative for high-minute matches).
    """

    def __init__(
        self,
        model: "EnsembleModel",
        fetcher: "DataFetcher",
        rho: float = -0.08,
    ) -> None:
        self._model = model
        self._fetcher = fetcher
        self._rho = rho

    def predict(
        self,
        match_id: int,
        home_team: str,
        away_team: str,
        neutral_venue: bool = True,
    ) -> dict:
        """
        Fetch live state and return updated full-game score probabilities.

        Returns
        -------
        dict with keys:
            minute, home_score, away_score, status,
            home_win, draw, away_win,
            top_scores (list[dict]),
            home_xg_remaining, away_xg_remaining,
            score_matrix (list[list[float]])
        """
        # Pre-game grid gives us the base lambdas
        pre_grid = self._model.predict(
            home_team, away_team, max_goals=10, neutral_venue=neutral_venue
        )
        λ_h_pre = pre_grid.home_goal_expectation
        λ_a_pre = pre_grid.away_goal_expectation

        # Fetch live state
        live_match = self._fetcher._client.get_match(match_id)
        status = live_match.get("status", "scheduled")

        current_h = live_match.get("home_score") or 0
        current_a = live_match.get("away_score") or 0

        # Determine current minute from events
        events = self._fetcher.live_events(match_id)
        minute = _latest_minute(events, live_match)

        if status == "completed":
            # Match over — return exact outcome
            final_h = live_match.get("home_score", 0) or 0
            final_a = live_match.get("away_score", 0) or 0
            result = "home_win" if final_h > final_a else ("draw" if final_h == final_a else "away_win")
            return {
                "minute": 90,
                "home_score": final_h,
                "away_score": final_a,
                "status": "completed",
                "result": result,
                "home_win": 1.0 if result == "home_win" else 0.0,
                "draw": 1.0 if result == "draw" else 0.0,
                "away_win": 1.0 if result == "away_win" else 0.0,
                "top_scores": [{"home_goals": final_h, "away_goals": final_a, "probability": 1.0}],
                "score_matrix": [[0.0]],
            }

        remaining = max(90 - minute, 0)

        # Time-scaled pre-game lambdas
        λ_h_remaining = λ_h_pre * remaining / 90.0
        λ_a_remaining = λ_a_pre * remaining / 90.0

        # Live xG blend
        team_stats = self._fetcher.live_team_stats(match_id)
        λ_h_remaining, λ_a_remaining = self._blend_xg(
            λ_h_remaining,
            λ_a_remaining,
            λ_h_pre,
            λ_a_pre,
            team_stats,
            minute,
            remaining,
        )

        # Momentum adjustment
        momentum = self._fetcher.live_momentum(match_id)
        λ_h_remaining, λ_a_remaining = self._apply_momentum(
            λ_h_remaining, λ_a_remaining, momentum, minute
        )

        # Clamp to positive
        λ_h_remaining = max(λ_h_remaining, 0.01)
        λ_a_remaining = max(λ_a_remaining, 0.01)

        # Compute rho bounds and clamp
        rho_min = max(-1.0 / λ_h_remaining, -1.0 / λ_a_remaining)
        rho_max = min(1.0, 1.0 / (λ_h_remaining * λ_a_remaining))
        rho = float(np.clip(self._rho, rho_min + 1e-6, rho_max - 1e-6))

        remaining_grid = create_dixon_coles_grid(
            λ_h_remaining, λ_a_remaining, rho=rho, max_goals=_MAX_GOALS_LIVE
        )

        # Shift to final scores
        final_grid = _shift_grid(remaining_grid.grid, current_h, current_a)

        max_final = final_grid.shape[0]
        final_fpg = FootballProbabilityGrid(
            goal_matrix=final_grid,
            home_goal_expectation=current_h + λ_h_remaining,
            away_goal_expectation=current_a + λ_a_remaining,
            normalize=True,
        )

        top = _top_scores(final_fpg, n=15)

        return {
            "match_id": match_id,
            "minute": minute,
            "home_score": current_h,
            "away_score": current_a,
            "status": status,
            "home_win": final_fpg.home_win,
            "draw": final_fpg.draw,
            "away_win": final_fpg.away_win,
            "home_xg_remaining": λ_h_remaining,
            "away_xg_remaining": λ_a_remaining,
            "home_xg_full": current_h + λ_h_remaining,
            "away_xg_full": current_a + λ_a_remaining,
            "top_scores": top,
            "score_matrix": final_fpg.grid.tolist(),
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _blend_xg(
        self,
        λ_h: float,
        λ_a: float,
        λ_h_pre: float,
        λ_a_pre: float,
        team_stats: list[dict],
        minute: int,
        remaining: int,
    ) -> tuple[float, float]:
        if not team_stats or minute < 5:
            return λ_h, λ_a

        live_xg_h = next(
            (ts.get("expected_goals") for ts in team_stats if ts.get("is_home")), None
        )
        live_xg_a = next(
            (ts.get("expected_goals") for ts in team_stats if not ts.get("is_home")), None
        )

        if live_xg_h is None or live_xg_a is None:
            return λ_h, λ_a

        α = min(minute / _XG_BLEND_HALFLIFE, 1.0)

        # Project live xG rate to remaining time
        rate_h = float(live_xg_h) / minute * remaining
        rate_a = float(live_xg_a) / minute * remaining

        blended_h = (1 - α) * λ_h + α * rate_h
        blended_a = (1 - α) * λ_a + α * rate_a
        return blended_h, blended_a

    def _apply_momentum(
        self,
        λ_h: float,
        λ_a: float,
        momentum: list[dict],
        minute: int,
    ) -> tuple[float, float]:
        if not momentum:
            return λ_h, λ_a

        recent = [m["value"] for m in momentum if m.get("minute", 0) >= max(0, minute - 5)]
        if not recent:
            return λ_h, λ_a

        mean_mom = float(np.mean(recent))
        factor_h = 1.0 + np.clip(
            _MOMENTUM_WEIGHT * mean_mom, -_MOMENTUM_CAP, _MOMENTUM_CAP
        )
        factor_a = 1.0 - np.clip(
            _MOMENTUM_WEIGHT * mean_mom, -_MOMENTUM_CAP, _MOMENTUM_CAP
        )
        return λ_h * factor_h, λ_a * factor_a


def _latest_minute(events: list[dict], match: dict) -> int:
    """Estimate current match minute from events or match data."""
    minutes = [e.get("time_minute") for e in events if e.get("time_minute") is not None]
    if minutes:
        return max(int(m) for m in minutes)
    # Fallback: use first/second half scores
    if match.get("first_half_home_score") is not None and match.get("second_half_home_score") is None:
        return 45
    if match.get("second_half_home_score") is not None:
        return 90
    return 0


def _shift_grid(
    remaining_grid: np.ndarray,
    current_h: int,
    current_a: int,
    max_final: int = 15,
) -> np.ndarray:
    """
    Shift remaining-goals grid to final-score coordinates.

    remaining_grid[i, j] = P(home adds i more, away adds j more)
    Returns final_grid[h, a] = P(final home = h, final away = a)
    """
    out = np.zeros((max_final, max_final), dtype=np.float64)
    n_h, n_a = remaining_grid.shape
    for i in range(n_h):
        for j in range(n_a):
            fh = current_h + i
            fa = current_a + j
            if fh < max_final and fa < max_final:
                out[fh, fa] += remaining_grid[i, j]
    return out


def _top_scores(grid: FootballProbabilityGrid, n: int = 15) -> list[dict]:
    mat = grid.grid
    indices = np.argsort(mat, axis=None)[::-1][:n]
    result = []
    for idx in indices:
        h, a = divmod(int(idx), mat.shape[1])
        result.append({"home_goals": h, "away_goals": a, "probability": float(mat[h, a])})
    return result
