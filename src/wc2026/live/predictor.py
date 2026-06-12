"""
LivePMFPredictor — score-state conditional PMF updated in real time.

Algorithm
---------
Given a MatchState with current score (h, a) at minute t with R remaining
regulation seconds, the live model computes:

    P(final_home = h + Δh, final_away = a + Δa | current state)

using the score-state forward recursion:

For each possible additional score pair (Δh, Δa):
    1. Integrate the hazard model to get expected remaining goals:
       λ_h_rem, λ_a_rem = expected_goals_remaining(state)
    2. Use independent Poisson(λ_h_rem) × Poisson(λ_a_rem) for additional goals.
    3. The final score PMF is the convolution of current score + additional goals.
    4. Calibrate using temperature scaling (T from walk-forward calibration).

Important: the live PMF represents REGULATION remaining goals only.
Extra time and penalty shootout are separate (conditional on score at 90 min).

Regulation-time remaining PMF
------------------------------
For "trivial" score states (team winning by 3+ with <5 min left), the model
compresses: P(0 additional goals) >> 1, and the PMF becomes near-degenerate.
This is correct behavior — don't "smooth" it away.

Output
------
Returns a LivePMFResult with:
- final_score_pmf: JointScorePMF over (home_total, away_total)
- additional_goals_pmf: JointScorePMF over (Δh, Δa)
- expected_remaining_home_goals: λ_h_rem
- expected_remaining_away_goals: λ_a_rem
- home_win_prob, draw_prob, away_win_prob (regulation only)
- next_goal_home_prob, next_goal_away_prob, no_more_goals_prob
- derived markets
- calibration_temperature
"""
from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field
from typing import Optional

import numpy as np
from scipy.stats import poisson

from .state import MatchState
from .hazard import expected_goals_remaining, compute_live_rates

log = logging.getLogger(__name__)

_EPS = 1e-12
_DEFAULT_TEMP = 1.0   # temperature scaling; 1.0 = no calibration


@dataclass
class LivePMFResult:
    """Output of a single LivePMFPredictor.predict() call."""
    match_id: str
    home_team: str
    away_team: str
    regulation_minute: float
    clock_display: str
    current_home_goals: int
    current_away_goals: int

    # PMF over (home_total, away_total) regulation final scores
    final_score_pmf: np.ndarray         # shape (max_goals, max_goals)
    # PMF over additional goals only
    additional_goals_pmf: np.ndarray    # shape (max_delta, max_delta)

    # Expected remaining goals
    expected_remaining_home: float
    expected_remaining_away: float

    # Regulation outcome probabilities (derived from PMF)
    home_win_prob: float
    draw_prob: float
    away_win_prob: float

    # Next-goal and no-more-goals
    next_goal_home_prob: float
    next_goal_away_prob: float
    no_more_goals_prob: float

    # Top scorelines (final score)
    top_scorelines: list

    # Derived markets
    derived_markets: dict

    # Calibration
    calibration_temperature: float = _DEFAULT_TEMP
    method: str = "live_hazard_poisson"
    warnings: list = field(default_factory=list)

    def to_dict(self) -> dict:
        d = {
            "match_id": self.match_id,
            "home_team": self.home_team,
            "away_team": self.away_team,
            "regulation_minute": round(self.regulation_minute, 2),
            "clock_display": self.clock_display,
            "current_score": f"{self.current_home_goals}-{self.current_away_goals}",
            "expected_remaining_home": round(self.expected_remaining_home, 4),
            "expected_remaining_away": round(self.expected_remaining_away, 4),
            "home_win_prob": round(self.home_win_prob, 4),
            "draw_prob": round(self.draw_prob, 4),
            "away_win_prob": round(self.away_win_prob, 4),
            "next_goal_home_prob": round(self.next_goal_home_prob, 4),
            "next_goal_away_prob": round(self.next_goal_away_prob, 4),
            "no_more_goals_prob": round(self.no_more_goals_prob, 4),
            "top_scorelines": self.top_scorelines[:10],
            "derived_markets": self.derived_markets,
            "calibration_temperature": self.calibration_temperature,
            "method": self.method,
            "warnings": self.warnings,
        }
        # Add score PMF grid (capped at 8×8 for output compactness)
        n = min(self.final_score_pmf.shape[0], 8)
        d["final_score_pmf_grid"] = self.final_score_pmf[:n, :n].tolist()
        return d


class LivePMFPredictor:
    """
    Live in-match score PMF predictor.

    Uses the non-homogeneous minute hazard model to estimate remaining goals,
    then computes a Poisson convolution over the current score state.

    Architecture: pregame_pmf is updated each minute with hazard-derived
    remaining-goal expectations rather than the full pregame expectations.

    Parameters
    ----------
    max_delta       Max additional goals per team to model (default 6)
    max_goals       Total goals grid size for output (default 10)
    temperature     Calibration temperature (from walk-forward calibration)
    xg_blend        Blend weight for live xG vs pregame (0–1)
    """

    def __init__(
        self,
        max_delta: int = 6,
        max_goals: int = 10,
        temperature: float = _DEFAULT_TEMP,
        xg_blend: float = 0.60,
    ):
        self.max_delta = max_delta
        self.max_goals = max_goals
        self.temperature = temperature
        self.xg_blend = xg_blend

    def predict(
        self,
        state: MatchState,
        pregame_lh: Optional[float] = None,
        pregame_la: Optional[float] = None,
    ) -> LivePMFResult:
        """
        Compute the live score PMF for a given match state.

        Parameters
        ----------
        state       Current MatchState
        pregame_lh  Pregame expected home goals per 90 (overrides state field)
        pregame_la  Pregame expected away goals per 90
        """
        lh = float(pregame_lh or state.pregame_lh or 1.35)
        la = float(pregame_la or state.pregame_la or 1.00)
        minute = state.regulation_minute
        remaining = state.remaining_regulation_seconds
        h0 = state.home_goals
        a0 = state.away_goals

        warnings = []

        # ── 1. Get live xG rates if available ────────────────────────────
        home_xg_rate = away_xg_rate = None
        if state.home_stats and state.away_stats:
            h_xg = state.home_stats.xg
            a_xg = state.away_stats.xg
            if h_xg is not None and a_xg is not None and minute > 5:
                time_frac = max(minute / 90.0, 0.01)
                home_xg_rate = float(h_xg) / time_frac
                away_xg_rate = float(a_xg) / time_frac
        if home_xg_rate is None:
            warnings.append("xg_unavailable_using_pregame")

        h_disadv = 11 - state.home_effective_players
        a_disadv = 11 - state.away_effective_players

        # ── 2. Expected remaining goals ───────────────────────────────────
        lh_rem, la_rem = expected_goals_remaining(
            minute=minute,
            home_goals=h0,
            away_goals=a0,
            pregame_lh=lh,
            pregame_la=la,
            remaining_seconds=float(remaining),
            home_xg_rate=home_xg_rate,
            away_xg_rate=away_xg_rate,
            home_disadvantage=h_disadv,
            away_disadvantage=a_disadv,
            xg_blend=self.xg_blend,
        )

        # ── 3. Build additional-goals PMF (independent Poisson) ──────────
        d = self.max_delta + 1
        add_pmf = np.outer(
            poisson.pmf(range(d), max(lh_rem, _EPS)),
            poisson.pmf(range(d), max(la_rem, _EPS)),
        )
        add_pmf = np.clip(add_pmf, 0, None)
        add_pmf /= add_pmf.sum()

        # ── 4. Apply temperature scaling ─────────────────────────────────
        if abs(self.temperature - 1.0) > 0.01:
            add_pmf = np.power(add_pmf + _EPS, 1.0 / self.temperature)
            add_pmf /= add_pmf.sum()

        # ── 5. Build final score PMF by shifting ─────────────────────────
        n = self.max_goals
        final_pmf = np.zeros((n, n))
        for dh in range(d):
            for da in range(d):
                fh = h0 + dh
                fa = a0 + da
                if fh < n and fa < n:
                    final_pmf[fh, fa] += add_pmf[dh, da]

        # Any remaining probability mass goes to overflow (high scores)
        overflow = float(1.0 - final_pmf.sum())
        if overflow > 0.01:
            warnings.append(f"overflow_mass_{overflow:.3f}_beyond_{n}x{n}_grid")

        final_pmf = np.clip(final_pmf, 0, None)
        s = final_pmf.sum()
        if s > _EPS:
            final_pmf /= s

        # ── 6. Derive outcome probabilities ──────────────────────────────
        hw = float(sum(final_pmf[h, a] for h in range(n) for a in range(n) if h > a))
        dr = float(sum(final_pmf[h, a] for h in range(n) for a in range(n) if h == a))
        aw = float(sum(final_pmf[h, a] for h in range(n) for a in range(n) if h < a))

        # ── 7. Next-goal probabilities ────────────────────────────────────
        # P(next goal is home) ≈ λ_h_rem / (λ_h_rem + λ_a_rem)
        total_rate = lh_rem + la_rem
        if total_rate > _EPS:
            ng_home = lh_rem / total_rate
            ng_away = la_rem / total_rate
        else:
            ng_home = ng_away = 0.5

        # P(no more goals) = P(Poisson_home(λ_h_rem)=0) × P(Poisson_away(λ_a_rem)=0)
        p_no_more = float(
            math.exp(-max(lh_rem, 0)) * math.exp(-max(la_rem, 0))
        )
        if total_rate > _EPS:
            ng_home_prob = (1 - p_no_more) * ng_home
            ng_away_prob = (1 - p_no_more) * ng_away
        else:
            ng_home_prob = ng_away_prob = 0.0

        # ── 8. Top scorelines ─────────────────────────────────────────────
        top = sorted(
            [{"home_goals": int(h), "away_goals": int(a), "probability": round(float(final_pmf[h, a]), 5)}
             for h in range(n) for a in range(n)],
            key=lambda x: -x["probability"],
        )[:15]

        # ── 9. Derived markets ────────────────────────────────────────────
        btts = float(sum(final_pmf[h, a] for h in range(n) for a in range(n) if h > 0 and a > 0))
        over_0_5 = float(sum(final_pmf[h, a] for h in range(n) for a in range(n) if h + a > 0))
        over_1_5 = float(sum(final_pmf[h, a] for h in range(n) for a in range(n) if h + a > 1))
        over_2_5 = float(sum(final_pmf[h, a] for h in range(n) for a in range(n) if h + a > 2))
        over_3_5 = float(sum(final_pmf[h, a] for h in range(n) for a in range(n) if h + a > 3))
        markets = {
            "home_win": round(hw, 4),
            "draw": round(dr, 4),
            "away_win": round(aw, 4),
            "btts_yes": round(btts, 4),
            "btts_no": round(1 - btts, 4),
            "over_0_5": round(over_0_5, 4),
            "over_1_5": round(over_1_5, 4),
            "over_2_5": round(over_2_5, 4),
            "over_3_5": round(over_3_5, 4),
        }

        return LivePMFResult(
            match_id=state.match_id,
            home_team=state.home_team,
            away_team=state.away_team,
            regulation_minute=minute,
            clock_display=state.clock_display,
            current_home_goals=h0,
            current_away_goals=a0,
            final_score_pmf=final_pmf,
            additional_goals_pmf=add_pmf,
            expected_remaining_home=round(lh_rem, 4),
            expected_remaining_away=round(la_rem, 4),
            home_win_prob=round(hw, 4),
            draw_prob=round(dr, 4),
            away_win_prob=round(aw, 4),
            next_goal_home_prob=round(ng_home_prob, 4),
            next_goal_away_prob=round(ng_away_prob, 4),
            no_more_goals_prob=round(p_no_more, 4),
            top_scorelines=top,
            derived_markets=markets,
            calibration_temperature=self.temperature,
            warnings=warnings,
        )

    def predict_from_bdl(
        self,
        bdl_match: dict,
        bdl_stats: Optional[dict] = None,
        pregame_lh: float = 1.35,
        pregame_la: float = 1.00,
    ) -> Optional[LivePMFResult]:
        """
        Build a MatchState from a BDL match dict and call predict().

        Parameters
        ----------
        bdl_match   BDL match record (from /matches endpoint)
        bdl_stats   BDL team stats dict (from /matches/{id}/team_stats)
        pregame_lh  Pregame expected home goals
        pregame_la  Pregame expected away goals
        """
        from .state import MatchState, MatchStatus, TeamLiveStats
        try:
            # Parse BDL fields
            match_id = str(bdl_match.get("id", "unknown"))
            home = bdl_match.get("home_team", {}).get("full_name", "Home")
            away = bdl_match.get("away_team", {}).get("full_name", "Away")
            status_raw = str(bdl_match.get("status", "")).lower()

            status_map = {
                "1h": MatchStatus.FIRST_HALF,
                "ht": MatchStatus.HALF_TIME,
                "2h": MatchStatus.SECOND_HALF,
                "et": MatchStatus.EXTRA_TIME_FIRST,
                "ft": MatchStatus.COMPLETED,
                "ns": MatchStatus.PREMATCH,
            }
            status = status_map.get(status_raw, MatchStatus.PREMATCH)

            # Clock
            clock_str = str(bdl_match.get("clock_display", "0"))
            try:
                clock_min = int(clock_str.split("+")[0])
            except (ValueError, IndexError):
                clock_min = 0
            match_seconds = clock_min * 60

            # Score
            h_goals = int(bdl_match.get("home_score", 0) or 0)
            a_goals = int(bdl_match.get("away_score", 0) or 0)

            # Live stats (if available)
            h_stats = a_stats = None
            if bdl_stats:
                h_raw = bdl_stats.get("home_team_stats", {})
                a_raw = bdl_stats.get("away_team_stats", {})

                def _safe_float(d, k):
                    v = d.get(k)
                    return float(v) if v is not None else None

                h_stats = TeamLiveStats(
                    shots_total=h_raw.get("shots"),
                    shots_on_target=h_raw.get("shots_on_target"),
                    xg=_safe_float(h_raw, "xg"),
                    xgot=_safe_float(h_raw, "xgot"),
                    big_chances=h_raw.get("big_chances"),
                    corners=h_raw.get("corners"),
                    possession_pct=_safe_float(h_raw, "possession"),
                    fouls=h_raw.get("fouls"),
                    yellow_cards=int(h_raw.get("yellow_cards", 0) or 0),
                    red_cards=int(h_raw.get("red_cards", 0) or 0),
                )
                a_stats = TeamLiveStats(
                    shots_total=a_raw.get("shots"),
                    shots_on_target=a_raw.get("shots_on_target"),
                    xg=_safe_float(a_raw, "xg"),
                    xgot=_safe_float(a_raw, "xgot"),
                    big_chances=a_raw.get("big_chances"),
                    corners=a_raw.get("corners"),
                    possession_pct=_safe_float(a_raw, "possession"),
                    fouls=a_raw.get("fouls"),
                    yellow_cards=int(a_raw.get("yellow_cards", 0) or 0),
                    red_cards=int(a_raw.get("red_cards", 0) or 0),
                )

            state = MatchState(
                match_id=match_id,
                home_team=home,
                away_team=away,
                season=int(bdl_match.get("season", 2026)),
                stage=str(bdl_match.get("stage", "group")),
                status=status,
                clock_display=clock_str,
                match_seconds=match_seconds,
                home_goals=h_goals,
                away_goals=a_goals,
                home_stats=h_stats,
                away_stats=a_stats,
                pregame_lh=pregame_lh,
                pregame_la=pregame_la,
            )
            return self.predict(state, pregame_lh=pregame_lh, pregame_la=pregame_la)

        except Exception as exc:
            log.warning("predict_from_bdl failed: %s", exc)
            return None
