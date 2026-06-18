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
- first_half_markets (only when minute <= 45)
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

    # First-half markets (None when minute > 45 — already settled)
    first_half_markets: Optional[dict] = None

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
            "current_home_goals": self.current_home_goals,
            "current_away_goals": self.current_away_goals,
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
            "first_half_markets": self.first_half_markets,
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
        momentum_df=None,
        home_defensive_depth: Optional[float] = None,
        away_defensive_depth: Optional[float] = None,
    ) -> "LivePMFResult":
        """
        Compute the live score PMF for a given match state.

        Parameters
        ----------
        state       Current MatchState
        pregame_lh  Pregame expected home goals per 90 (overrides state field)
        pregame_la  Pregame expected away goals per 90
        momentum_df Optional momentum DataFrame (match_id, minute, value) for
                    hazard scaling — loaded once outside the hot loop.
        home_defensive_depth  Mean avg_x of home outfield players (0–100).
                    < 35 = parking the bus; > 55 = high press.
        away_defensive_depth  Same for away team.
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
        xg_used = False
        if state.home_stats and state.away_stats:
            h_xg = state.home_stats.xg
            a_xg = state.away_stats.xg
            if h_xg is not None and a_xg is not None and minute >= 15:
                time_frac = max(minute / 90.0, 0.01)
                home_xg_rate = float(h_xg) / time_frac
                away_xg_rate = float(a_xg) / time_frac
                xg_used = True

                # xT-inspired shot quality adjustment via xGOT/xG ratio.
                # When xGOT (xG on target) > xG, chances were higher quality
                # (better positioned, on frame).  Scale the live xG rate by this
                # quality factor, capped to avoid overreaction on small samples.
                # Only applies when minute > 20 (enough shots for a stable ratio).
                if minute >= 20:
                    h_xgot = state.home_stats.xgot
                    a_xgot = state.away_stats.xgot
                    if h_xgot is not None and float(h_xg) > 0.05:
                        h_quality = float(np.clip(float(h_xgot) / float(h_xg), 0.75, 1.35))
                        home_xg_rate = home_xg_rate * h_quality
                    if a_xgot is not None and float(a_xg) > 0.05:
                        a_quality = float(np.clip(float(a_xgot) / float(a_xg), 0.75, 1.35))
                        away_xg_rate = away_xg_rate * a_quality

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
            match_id=state.match_id,
            momentum_df=momentum_df,
            home_defensive_depth=home_defensive_depth,
            away_defensive_depth=away_defensive_depth,
        )

        # ── Fix 3 log: mandatory xG blend status on every live snapshot ──
        log.info(
            "xG blend: %s | match=%s min=%d | xg_h=%.3f xg_a=%.3f | lam_h=%.3f lam_a=%.3f",
            "ACTIVE" if xg_used else "INACTIVE",
            state.match_id,
            int(minute),
            home_xg_rate or 0.0,
            away_xg_rate or 0.0,
            lh_rem,
            la_rem,
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

        # ── 10. First-half PMF (Fix 5) ────────────────────────────────────
        # Only computed when match is still in first half; first-half markets
        # are already settled once minute > 45.
        first_half_markets = None
        if minute <= 45:
            fh_remaining_secs = max(0.0, 45.0 * 60 - state.match_seconds)
            if fh_remaining_secs > 0:
                lh_fh, la_fh = expected_goals_remaining(
                    minute=minute,
                    home_goals=h0,
                    away_goals=a0,
                    pregame_lh=lh,
                    pregame_la=la,
                    remaining_seconds=fh_remaining_secs,
                    home_xg_rate=home_xg_rate,
                    away_xg_rate=away_xg_rate,
                    home_disadvantage=h_disadv,
                    away_disadvantage=a_disadv,
                    xg_blend=self.xg_blend,
                    match_id=state.match_id,
                    momentum_df=momentum_df,
                )
                d_fh = min(d, 7)
                fh_add_pmf = np.outer(
                    poisson.pmf(range(d_fh), max(lh_fh, _EPS)),
                    poisson.pmf(range(d_fh), max(la_fh, _EPS)),
                )
                fh_add_pmf /= fh_add_pmf.sum()

                fh_hw = float(sum(
                    fh_add_pmf[dh, da]
                    for dh in range(d_fh) for da in range(d_fh)
                    if h0 + dh > a0 + da
                ))
                fh_dr = float(sum(
                    fh_add_pmf[dh, da]
                    for dh in range(d_fh) for da in range(d_fh)
                    if h0 + dh == a0 + da
                ))
                fh_aw = float(sum(
                    fh_add_pmf[dh, da]
                    for dh in range(d_fh) for da in range(d_fh)
                    if h0 + dh < a0 + da
                ))
                fh_over_0_5 = float(sum(
                    fh_add_pmf[dh, da]
                    for dh in range(d_fh) for da in range(d_fh)
                    if h0 + a0 + dh + da >= 1
                ))
                fh_btts = float(sum(
                    fh_add_pmf[dh, da]
                    for dh in range(d_fh) for da in range(d_fh)
                    if h0 + dh >= 1 and a0 + da >= 1
                ))
                first_half_markets = {
                    "fh_home_win": round(fh_hw, 4),
                    "fh_draw": round(fh_dr, 4),
                    "fh_away_win": round(fh_aw, 4),
                    "fh_over_0_5": round(fh_over_0_5, 4),
                    "fh_btts": round(fh_btts, 4),
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
            first_half_markets=first_half_markets,
            calibration_temperature=self.temperature,
            warnings=warnings,
        )

    def predict_from_bdl(
        self,
        bdl_match: dict,
        bdl_stats: Optional[list] = None,
        pregame_lh: float = 1.35,
        pregame_la: float = 1.00,
        bdl_shots: Optional[list] = None,
        events_df=None,
        momentum_df=None,
        avg_positions: Optional[list] = None,
    ) -> Optional["LivePMFResult"]:
        """
        Build a MatchState from a BDL match dict and call predict().

        Parameters
        ----------
        bdl_match   BDL match record (from /matches endpoint)
        bdl_stats   BDL team stats dict (from /matches/{id}/team_stats)
        pregame_lh  Pregame expected home goals
        pregame_la  Pregame expected away goals
        events_df   Optional events DataFrame (loaded once upstream) for red cards.
                    Columns: match_id, incident_type, incident_class,
                             time_minute, is_home
        momentum_df Optional momentum DataFrame (match_id, minute, value)
        avg_positions  Optional list of BDL match_avg_positions records.
                    Used to compute per-team defensive block depth.
        """
        from .state import MatchState, MatchStatus, TeamLiveStats
        try:
            # Parse BDL fields
            match_id = str(bdl_match.get("id", "unknown"))
            home = bdl_match.get("home_team", {}).get("name") or bdl_match.get("home_team", {}).get("full_name", "Home")
            away = bdl_match.get("away_team", {}).get("name") or bdl_match.get("away_team", {}).get("full_name", "Away")
            status_raw = str(bdl_match.get("status", "")).lower()

            status_map = {
                "1h": MatchStatus.FIRST_HALF,
                "first half": MatchStatus.FIRST_HALF,
                "1st half": MatchStatus.FIRST_HALF,
                "ht": MatchStatus.HALF_TIME,
                "halftime": MatchStatus.HALF_TIME,
                "half time": MatchStatus.HALF_TIME,
                "2h": MatchStatus.SECOND_HALF,
                "second half": MatchStatus.SECOND_HALF,
                "2nd half": MatchStatus.SECOND_HALF,
                "et": MatchStatus.EXTRA_TIME_FIRST,
                "extra time": MatchStatus.EXTRA_TIME_FIRST,
                "extra_time": MatchStatus.EXTRA_TIME_FIRST,
                "ft": MatchStatus.COMPLETED,
                "finished": MatchStatus.COMPLETED,
                "completed": MatchStatus.COMPLETED,
                "full time": MatchStatus.COMPLETED,
                "full_time": MatchStatus.COMPLETED,
                "ns": MatchStatus.PREMATCH,
                "scheduled": MatchStatus.PREMATCH,
                "not started": MatchStatus.PREMATCH,
                "in_progress": MatchStatus.SECOND_HALF,   # fallback; clock will correct
                "in progress": MatchStatus.SECOND_HALF,
                "live": MatchStatus.SECOND_HALF,
                "ongoing": MatchStatus.SECOND_HALF,
                "active": MatchStatus.SECOND_HALF,
            }
            status = status_map.get(status_raw, MatchStatus.PREMATCH)

            # Clock — BDL sometimes returns clock_display/clock_seconds as None
            # (especially at halftime). Infer minute from available fields.
            clock_str = str(bdl_match.get("clock_display") or "")
            clock_secs_raw = bdl_match.get("clock_seconds")
            if clock_secs_raw is not None:
                match_seconds = int(clock_secs_raw)
                clock_min = match_seconds // 60
            else:
                try:
                    clock_min = int(clock_str.split("+")[0]) if clock_str else 0
                except (ValueError, IndexError):
                    clock_min = 0
                # Halftime inference: BDL may return clock_display=None during halftime.
                # Guard: only infer min=45 if at least 43 minutes have elapsed since
                # kickoff, because BDL also initializes first_half scores to 0 at
                # kickoff (not None), so a naive non-None check would fire immediately.
                fh_home = bdl_match.get("first_half_home_score")
                fh_away = bdl_match.get("first_half_away_score")
                # Estimate elapsed time from kickoff datetime (used for halftime guard
                # and as a clock fallback when BDL provides no clock data at all)
                from datetime import datetime as _dt, timezone as _tz
                ko_str = bdl_match.get("datetime") or bdl_match.get("date_time_utc", "")
                try:
                    ko_dt = _dt.fromisoformat(str(ko_str).replace("Z", "+00:00"))
                    mins_elapsed = (_dt.now(tz=_tz.utc) - ko_dt).total_seconds() / 60.0
                except Exception:
                    mins_elapsed = 999.0

                if clock_min == 0 and fh_home is not None and fh_away is not None:
                    # Estimate match minute from wall-clock elapsed time.
                    # Rough timeline: kickoff + 45min 1H + ~2min stoppage + 15min HT
                    #   ≈ 62 minutes elapsed before 2nd half kickoff.
                    if mins_elapsed < 43.0:
                        # Match started — BDL clock not yet available; use elapsed as proxy
                        clock_min = min(int(mins_elapsed), 44)
                    elif mins_elapsed < 62.0:
                        # Past 45-min mark but before 2nd-half start → halftime break
                        clock_min = 45
                    else:
                        # 2nd half is underway; estimate minute = 45 + (elapsed - 62)
                        # (assumes ~62 min elapsed when 2nd half kicks off)
                        clock_min = min(45 + max(0, int(mins_elapsed - 62)), 90)
                elif clock_min == 0 and mins_elapsed >= 1.0:
                    # No first-half scores yet but match started — use elapsed as proxy
                    clock_min = min(int(mins_elapsed), 44)
                match_seconds = clock_min * 60

            # Score — BDL docs say home_score/away_score are null only pre-kickoff.
            # In practice they may also lag during live play.  Primary path: use
            # home_score directly.  Fallback when null: sum available period scores.
            _raw_h = bdl_match.get("home_score")
            _raw_a = bdl_match.get("away_score")
            h_goals = int(_raw_h or 0)
            a_goals = int(_raw_a or 0)
            if _raw_h is None:
                h_goals = (int(bdl_match.get("first_half_home_score") or 0) +
                           int(bdl_match.get("second_half_home_score") or 0) +
                           int(bdl_match.get("extra_time_home_score") or 0))
            if _raw_a is None:
                a_goals = (int(bdl_match.get("first_half_away_score") or 0) +
                           int(bdl_match.get("second_half_away_score") or 0) +
                           int(bdl_match.get("extra_time_away_score") or 0))
            if _raw_h is None or _raw_a is None:
                log.debug("Score from half-period fields (home_score was null): %s-%s %d-%d",
                          home, away, h_goals, a_goals)

            # ── Fix 1: Count red cards from events_df ─────────────────────
            home_rc = 0
            away_rc = 0
            if events_df is not None and len(events_df) > 0:
                try:
                    try:
                        mid_int = int(match_id)
                        m_ev = events_df[events_df["match_id"] == mid_int]
                    except (TypeError, ValueError):
                        m_ev = events_df[events_df["match_id"].astype(str) == match_id]

                    if len(m_ev) > 0:
                        rc_mask = (
                            (m_ev["incident_type"] == "card") &
                            (m_ev["incident_class"].isin(["red", "yellowRed"])) &
                            (m_ev["time_minute"].notna()) &
                            (m_ev["time_minute"] <= clock_min)
                        )
                        rc_events = m_ev[rc_mask]
                        home_rc = int((rc_events["is_home"] == True).sum())
                        away_rc = int((rc_events["is_home"] == False).sum())
                except Exception as _rc_exc:
                    log.debug("Red card extraction failed: %s", _rc_exc)

            if home_rc > 0 or away_rc > 0:
                log.info(
                    "red_cards: match=%s min=%d home_rc=%d away_rc=%d",
                    match_id, clock_min, home_rc, away_rc,
                )

            # Live stats (if available).
            # bdl_stats is a list of team_match_stats rows [{match_id, team_id, is_home, ...}, ...]
            # Spec fields: shots_total, shots_on_target, expected_goals, big_chances,
            #   corners, possession_pct, fouls, yellow_cards.
            # NOTE: xgot does NOT exist in team_match_stats — it lives in match_shots only.
            h_stats = a_stats = None
            if bdl_stats:
                def _safe_float(d, k):
                    v = d.get(k)
                    return float(v) if v is not None else None

                h_raw = next((r for r in bdl_stats if r.get("is_home") is True), {})
                a_raw = next((r for r in bdl_stats if r.get("is_home") is False), {})

                # xgot from match_shots: sum xgot per is_home flag
                h_xgot = a_xgot = None
                if bdl_shots:
                    h_xgot_vals = [s.get("xgot") for s in bdl_shots
                                   if s.get("is_home") is True and s.get("xgot") is not None]
                    a_xgot_vals = [s.get("xgot") for s in bdl_shots
                                   if s.get("is_home") is False and s.get("xgot") is not None]
                    h_xgot = float(sum(h_xgot_vals)) if h_xgot_vals else None
                    a_xgot = float(sum(a_xgot_vals)) if a_xgot_vals else None

                h_stats = TeamLiveStats(
                    shots_total=h_raw.get("shots_total"),
                    shots_on_target=h_raw.get("shots_on_target"),
                    xg=_safe_float(h_raw, "expected_goals"),
                    xgot=h_xgot,
                    big_chances=h_raw.get("big_chances"),
                    corners=h_raw.get("corners"),
                    possession_pct=_safe_float(h_raw, "possession_pct"),
                    fouls=h_raw.get("fouls"),
                    yellow_cards=int(h_raw.get("yellow_cards", 0) or 0),
                    red_cards=home_rc,
                )
                a_stats = TeamLiveStats(
                    shots_total=a_raw.get("shots_total"),
                    shots_on_target=a_raw.get("shots_on_target"),
                    xg=_safe_float(a_raw, "expected_goals"),
                    xgot=a_xgot,
                    big_chances=a_raw.get("big_chances"),
                    corners=a_raw.get("corners"),
                    possession_pct=_safe_float(a_raw, "possession_pct"),
                    fouls=a_raw.get("fouls"),
                    yellow_cards=int(a_raw.get("yellow_cards", 0) or 0),
                    red_cards=away_rc,
                )

            state = MatchState(
                match_id=match_id,
                home_team=home,
                away_team=away,
                season=int((bdl_match.get("season") or {}).get("year", 2026) if isinstance(bdl_match.get("season"), dict) else bdl_match.get("season", 2026)),
                stage=(lambda s: s.get("name", "Group Stage") if isinstance(s, dict) else str(s or "Group Stage"))(bdl_match.get("stage")),
                status=status,
                clock_display=clock_str,
                match_seconds=match_seconds,
                home_goals=h_goals,
                away_goals=a_goals,
                home_effective_players=max(9, 11 - home_rc),
                away_effective_players=max(9, 11 - away_rc),
                home_stats=h_stats,
                away_stats=a_stats,
                pregame_lh=pregame_lh,
                pregame_la=pregame_la,
            )

            # ── Compute defensive block depth from avg_positions ──────────
            home_defensive_depth: Optional[float] = None
            away_defensive_depth: Optional[float] = None
            if avg_positions:
                h_xs = [
                    float(r["avg_x"]) for r in avg_positions
                    if r.get("is_home") is True
                    and r.get("avg_x") is not None
                    # Exclude GK: typically avg_x < 5 for home, > 100 for away
                    and float(r.get("avg_x", 50)) > 5
                ]
                a_xs = [
                    float(r["avg_x"]) for r in avg_positions
                    if r.get("is_home") is False
                    and r.get("avg_x") is not None
                    and float(r.get("avg_x", 50)) < 100
                ]
                if h_xs:
                    home_defensive_depth = float(sum(h_xs) / len(h_xs))
                    log.debug(
                        "home_defensive_depth=%.1f (n=%d outfield players)",
                        home_defensive_depth, len(h_xs)
                    )
                if a_xs:
                    # Away team's avg_x is measured from their own goal end;
                    # invert to match the same 0=own_goal, 100=opp_goal scale
                    away_defensive_depth = float(100.0 - sum(a_xs) / len(a_xs))
                    log.debug(
                        "away_defensive_depth=%.1f (n=%d outfield players, inverted)",
                        away_defensive_depth, len(a_xs)
                    )

            return self.predict(
                state,
                pregame_lh=pregame_lh,
                pregame_la=pregame_la,
                momentum_df=momentum_df,
                home_defensive_depth=home_defensive_depth,
                away_defensive_depth=away_defensive_depth,
            )

        except Exception as exc:
            log.warning("predict_from_bdl failed: %s", exc)
            return None
