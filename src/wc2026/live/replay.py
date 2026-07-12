"""
2022 World Cup minute-by-minute replay engine.

Replays completed 2022 matches using BDL event data, producing predictions
at regulation checkpoints: 0, 5, 10, 15, 30, 45 (HT), 60, 75, 85, 90, FT.

The replay generates:
  data/predictions/live_replay_2022.parquet   — per-checkpoint prediction rows
  reports/live_replay_validation.md           — summary metrics

Each row in the parquet contains:
  match_id, home_team, away_team, checkpoint_minute, clock_display
  current_home_goals, current_away_goals
  final_home_goals, final_away_goals (actual outcome)
  home_win_prob, draw_prob, away_win_prob
  next_goal_home_prob, next_goal_away_prob, no_more_goals_prob
  expected_remaining_home, expected_remaining_away
  actual_additional_home, actual_additional_away
  score_log_loss, btts_brier, 1x2_rps, over_2_5_brier
  method, warnings

Evaluation checkpoints
----------------------
The replay evaluates prediction at:
  0   → pre-kickoff (should match pregame PMF exactly)
  5   → 5 minutes in
  10  → 10 minutes in
  15  → 15 minutes in
  30  → 30 minutes in
  45  → half-time (after 45+x goal events applied)
  60  → 60 minutes
  75  → 75 minutes
  85  → 85 minutes
  90  → 90 minutes (before added time goals)
  FT  → full-time verification

Data requirements
-----------------
The replay uses:
  - matches (2022 season, completed)
  - match events (goals by minute)
  - team stats by half (for xG/shots snapshots at each checkpoint)
  - pregame lambdas from the composite prior + market odds

When BDL event data is unavailable (no minute-by-minute events), the replay
falls back to synthetic events reconstructed from final score and half scores.
"""
from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from .predictor import LivePMFPredictor, LivePMFResult
from .state import MatchState, MatchStatus

log = logging.getLogger(__name__)

CHECKPOINTS = [0, 5, 10, 15, 30, 45, 60, 75, 85, 90]


@dataclass
class ReplayCheckpoint:
    """Single prediction checkpoint in a replayed match."""
    match_id: str
    home_team: str
    away_team: str
    season: int

    checkpoint_minute: int
    clock_display: str

    # State at checkpoint
    current_home_goals: int
    current_away_goals: int
    home_effective_players: int
    away_effective_players: int

    # Actual outcome (regulation 90-min only)
    final_home_goals: int
    final_away_goals: int
    actual_additional_home: int     # final - current at checkpoint
    actual_additional_away: int

    # Prediction
    home_win_prob: float
    draw_prob: float
    away_win_prob: float
    next_goal_home_prob: float
    next_goal_away_prob: float
    no_more_goals_prob: float
    expected_remaining_home: float
    expected_remaining_away: float
    btts_yes_prob: float
    over_2_5_prob: float

    # Metrics
    score_log_loss: float           # -log P(actual final score)
    onex2_rps: float                # RPS for 1X2
    btts_brier: float
    over_2_5_brier: float
    next_goal_log_loss: float       # -log P(who scored next)
    no_more_goals_brier: float

    method: str = "live_hazard_poisson"
    pregame_lh: float = 1.35
    pregame_la: float = 1.00
    xg_available: bool = False
    warnings: list = field(default_factory=list)

    # 4B — First-half actual scores and PMF probabilities
    fh_home_actual: int | None = None
    fh_away_actual: int | None = None
    fh_hw_prob: float | None = None
    fh_draw_prob: float | None = None
    fh_aw_prob: float | None = None
    fh_over_0_5_prob: float | None = None
    fh_btts_prob: float | None = None
    fh_ignorance_score: float | None = None   # Log Loss per penaltyblog
    fh_brier_score: float | None = None

    def to_dict(self) -> dict:
        d = {k: v for k, v in self.__dict__.items() if not isinstance(v, list)}
        # Ensure first-half fields are always present (None when not applicable)
        for fh_field in (
            "fh_home_actual", "fh_away_actual", "fh_hw_prob", "fh_draw_prob",
            "fh_aw_prob", "fh_over_0_5_prob", "fh_btts_prob",
            "fh_ignorance_score", "fh_brier_score",
        ):
            d.setdefault(fh_field, None)
        return d


class MatchReplayer:
    """
    Replays a single completed match at each checkpoint minute.

    Uses BDL goal events to reconstruct score state at each checkpoint.
    Applies the live predictor at each state and evaluates against actual outcome.
    """

    def __init__(self, predictor: LivePMFPredictor | None = None):
        self.predictor = predictor or LivePMFPredictor()

    def replay(
        self,
        match_row: pd.Series,
        events_df: pd.DataFrame | None = None,
        stats_df: pd.DataFrame | None = None,
        pregame_lh: float = 1.35,
        pregame_la: float = 1.00,
        momentum_df: pd.DataFrame | None = None,
    ) -> list[ReplayCheckpoint]:
        """
        Replay a completed match and return checkpoints.

        Parameters
        ----------
        match_row   Row from the matches DataFrame (must have home_goals, away_goals)
        events_df   BDL match events filtered to this match
        stats_df    BDL team stats filtered to this match (used for xG blend)
        pregame_lh  Pregame expected home goals
        pregame_la  Pregame expected away goals
        momentum_df Full momentum DataFrame (match_id, minute, value)
        """
        match_id = str(match_row.get("match_id", match_row.name))
        home = str(match_row.get("home_team", "Home"))
        away = str(match_row.get("away_team", "Away"))
        season = int(match_row.get("season", 2022))
        final_hg = int(match_row.get("home_goals", 0))
        final_ag = int(match_row.get("away_goals", 0))
        # 4A — First-half actual scores for PMF evaluation
        fh_home_actual = int(match_row.get("first_half_home") or 0) if match_row.get("first_half_home") is not None else None
        fh_away_actual = int(match_row.get("first_half_away") or 0) if match_row.get("first_half_away") is not None else None

        # Build goal events from BDL data or synthetic reconstruction
        goal_timeline = self._build_goal_timeline(
            match_id, final_hg, final_ag, events_df
        )
        red_card_timeline = self._build_card_timeline(match_id, events_df, "red_card")

        # Log red cards when present
        if red_card_timeline:
            home_rc_total = sum(1 for _, t in red_card_timeline if t == "home")
            away_rc_total = sum(1 for _, t in red_card_timeline if t == "away")
            if home_rc_total > 0 or away_rc_total > 0:
                last_min = max(m for m, _ in red_card_timeline)
                log.info(
                    "red_cards: match=%s min=%d home_rc=%d away_rc=%d",
                    match_id, last_min, home_rc_total, away_rc_total,
                )

        # Pre-fetch end-of-match team stats for xG blend (scaled linearly by minute)
        h_stats_final = a_stats_final = None
        if stats_df is not None and len(stats_df) > 0:
            try:
                from .state import TeamLiveStats
                orig_mid = match_row.get("match_id", match_row.name)
                m_stats = stats_df[stats_df["match_id"] == orig_mid]
                if len(m_stats) == 0:
                    m_stats = stats_df[stats_df["match_id"].astype(str) == match_id]
                if len(m_stats) > 0:
                    h_raw = m_stats[m_stats["is_home"]]
                    a_raw = m_stats[not m_stats["is_home"]]
                    if len(h_raw) > 0 and len(a_raw) > 0:
                        h_r = h_raw.iloc[0]
                        a_r = a_raw.iloc[0]
                        h_stats_final = h_r
                        a_stats_final = a_r
            except Exception as _se:
                log.debug("stats_df parse failed for %s: %s", match_id, _se)

        checkpoints = []
        for cp_minute in CHECKPOINTS:
            # Reconstruct state at this checkpoint
            h_goals, a_goals, h_eff, a_eff = self._state_at_minute(
                cp_minute, goal_timeline, red_card_timeline, final_hg, final_ag
            )

            # Build per-checkpoint TeamLiveStats by scaling end-of-game xG linearly.
            # This approximation lets the xG blend activate for minute >= 15 checkpoints.
            cp_h_stats = cp_a_stats = None
            if h_stats_final is not None and a_stats_final is not None and cp_minute >= 15:
                try:
                    from .state import TeamLiveStats
                    scale = cp_minute / 90.0
                    def _sv(row, col):
                        v = row.get(col) if hasattr(row, "get") else getattr(row, col, None)
                        return float(v) * scale if v is not None and not pd.isna(v) else None
                    cp_h_stats = TeamLiveStats(
                        xg=_sv(h_stats_final, "expected_goals"),
                        shots_total=None,
                        shots_on_target=None,
                    )
                    cp_a_stats = TeamLiveStats(
                        xg=_sv(a_stats_final, "expected_goals"),
                        shots_total=None,
                        shots_on_target=None,
                    )
                except Exception:
                    pass

            state = MatchState(
                match_id=match_id,
                home_team=home,
                away_team=away,
                season=season,
                stage=str(match_row.get("stage", "group")),
                status=self._minute_to_status(cp_minute),
                clock_display=str(cp_minute),
                match_seconds=cp_minute * 60,
                home_goals=h_goals,
                away_goals=a_goals,
                home_effective_players=h_eff,
                away_effective_players=a_eff,
                home_stats=cp_h_stats,
                away_stats=cp_a_stats,
                pregame_lh=pregame_lh,
                pregame_la=pregame_la,
            )

            try:
                result = self.predictor.predict(
                    state, pregame_lh, pregame_la, momentum_df=momentum_df
                )
                cp = self._build_checkpoint(
                    state, result, final_hg, final_ag, pregame_lh, pregame_la,
                    fh_home_actual=fh_home_actual,
                    fh_away_actual=fh_away_actual,
                )
                checkpoints.append(cp)
            except Exception as exc:
                log.warning("Replay failed at minute %d for %s: %s", cp_minute, match_id, exc)

        return checkpoints

    def _build_goal_timeline(
        self,
        match_id: str,
        final_hg: int,
        final_ag: int,
        events_df: pd.DataFrame | None,
    ) -> list[tuple[int, str]]:
        """
        Return list of (minute, team) tuples for all goals.
        'team' is 'home' or 'away'.

        Falls back to synthetic uniform distribution if no event data.
        """
        if events_df is not None and len(events_df) > 0:
            goal_events = events_df[
                events_df["type"].isin(["goal", "own_goal", "penalty_goal"])
            ].copy()
            if len(goal_events) > 0:
                timeline = []
                for _, row in goal_events.iterrows():
                    minute = int(row.get("clock_minute", 45))
                    team = str(row.get("team", "home")).lower()
                    # own goals credit the other team
                    if row.get("type") == "own_goal":
                        team = "away" if team == "home" else "home"
                    timeline.append((minute, team))
                return sorted(timeline)

        # Synthetic: distribute goals uniformly across the 90 minutes
        timeline = []
        np.random.seed(hash(match_id) % (2 ** 31))
        h_minutes = sorted(np.random.choice(range(1, 90), size=final_hg, replace=False).tolist())
        a_minutes = sorted(np.random.choice(range(1, 90), size=final_ag, replace=False).tolist())
        for m in h_minutes:
            timeline.append((m, "home"))
        for m in a_minutes:
            timeline.append((m, "away"))
        return sorted(timeline)

    def _build_card_timeline(
        self,
        match_id: str,
        events_df: pd.DataFrame | None,
        card_type: str = "red_card",
    ) -> list[tuple[int, str]]:
        """Return list of (minute, team) for red cards."""
        if events_df is None or len(events_df) == 0:
            return []
        cards = events_df[events_df["type"] == card_type]
        return [
            (max(0, min(int(float(row.get("clock_minute") or 50)), 120)),
             str(row.get("team", "home")).lower())
            for _, row in cards.iterrows()
        ]

    def _state_at_minute(
        self,
        minute: int,
        goal_timeline: list,
        card_timeline: list,
        final_hg: int,
        final_ag: int,
    ) -> tuple[int, int, int, int]:
        """Return (home_goals, away_goals, home_eff, away_eff) at given minute."""
        h = sum(1 for m, t in goal_timeline if m <= minute and t == "home")
        a = sum(1 for m, t in goal_timeline if m <= minute and t == "away")
        h_rc = sum(1 for m, t in card_timeline if m <= minute and t == "home")
        a_rc = sum(1 for m, t in card_timeline if m <= minute and t == "away")
        return (
            min(h, final_hg),
            min(a, final_ag),
            max(11 - h_rc, 9),  # min 9 effective
            max(11 - a_rc, 9),
        )

    @staticmethod
    def _minute_to_status(minute: int) -> MatchStatus:
        if minute == 0:
            return MatchStatus.PREMATCH
        if minute < 45:
            return MatchStatus.FIRST_HALF
        if minute == 45:
            return MatchStatus.HALF_TIME
        return MatchStatus.SECOND_HALF

    def _build_checkpoint(
        self,
        state: MatchState,
        result: LivePMFResult,
        final_hg: int,
        final_ag: int,
        pregame_lh: float,
        pregame_la: float,
        fh_home_actual: int | None = None,
        fh_away_actual: int | None = None,
    ) -> ReplayCheckpoint:
        """Build a ReplayCheckpoint from a prediction result and actual outcome."""
        h0 = state.home_goals
        a0 = state.away_goals
        add_h = final_hg - h0
        add_a = final_ag - a0
        n = result.final_score_pmf.shape[0]

        # Score log loss
        if final_hg < n and final_ag < n:
            p_actual = float(result.final_score_pmf[final_hg, final_ag])
            score_ll = -math.log(max(p_actual, 1e-10))
        else:
            score_ll = -math.log(1e-10)

        # 1X2 RPS
        hw_actual = 1.0 if final_hg > final_ag else 0.0
        dr_actual = 1.0 if final_hg == final_ag else 0.0
        aw_actual = 1.0 if final_hg < final_ag else 0.0
        rps = _rps_1x2(result.home_win_prob, result.draw_prob, result.away_win_prob,
                       hw_actual, dr_actual, aw_actual)

        # BTTS Brier
        actual_btts = 1.0 if final_hg > 0 and final_ag > 0 else 0.0
        btts_b = (result.derived_markets.get("btts_yes", 0.5) - actual_btts) ** 2

        # O/U 2.5 Brier
        actual_over = 1.0 if final_hg + final_ag > 2 else 0.0
        ou_b = (result.derived_markets.get("over_2_5", 0.5) - actual_over) ** 2

        # Next goal log loss (if any goal happened between checkpoint and final)
        total_remaining_goals = add_h + add_a
        if total_remaining_goals > 0:
            ng_h = result.next_goal_home_prob
            ng_a = result.next_goal_away_prob
            if add_h > 0 and ng_h > 0:
                ng_ll = -math.log(max(ng_h, 1e-10))
            elif add_a > 0 and ng_a > 0:
                ng_ll = -math.log(max(ng_a, 1e-10))
            else:
                ng_ll = float("inf")
        else:
            # No more goals: score with no_more_goals_prob
            ng_ll = -math.log(max(result.no_more_goals_prob, 1e-10))

        # No-more-goals Brier
        actual_no_more = 1.0 if add_h + add_a == 0 else 0.0
        nmg_brier = (result.no_more_goals_prob - actual_no_more) ** 2

        # 4C — First-half PMF metrics (checkpoint_minute <= 45 only)
        fh_hw_prob = fh_draw_prob_val = fh_aw_prob = None
        fh_over_0_5_prob = fh_btts_prob_val = None
        fh_ignorance = fh_brier = None
        cp_min = int(state.regulation_minute)
        fhm = result.first_half_markets
        if fhm is not None and cp_min <= 45 and fh_home_actual is not None and fh_away_actual is not None:
            try:
                import penaltyblog as pb
                fh_hw_prob = fhm.get("fh_home_win")
                fh_draw_prob_val = fhm.get("fh_draw")
                fh_aw_prob = fhm.get("fh_away_win")
                fh_over_0_5_prob = fhm.get("fh_over_0_5")
                fh_btts_prob_val = fhm.get("fh_btts")
                if fh_hw_prob is not None and fh_draw_prob_val is not None and fh_aw_prob is not None:
                    probs_1x2 = [[fh_hw_prob, fh_draw_prob_val, fh_aw_prob]]
                    fh_outcome = 0 if fh_home_actual > fh_away_actual else (
                        1 if fh_home_actual == fh_away_actual else 2
                    )
                    fh_ignorance = float(pb.metrics.ignorance_score(probs_1x2, [fh_outcome]))
                    fh_brier = float(pb.metrics.multiclass_brier_score(probs_1x2, [fh_outcome]))
            except Exception as _fh_exc:
                log.debug("First-half PMF metrics failed: %s", _fh_exc)


        return ReplayCheckpoint(
            match_id=state.match_id,
            home_team=state.home_team,
            away_team=state.away_team,
            season=state.season,
            checkpoint_minute=cp_min,
            clock_display=state.clock_display,
            current_home_goals=h0,
            current_away_goals=a0,
            home_effective_players=state.home_effective_players,
            away_effective_players=state.away_effective_players,
            final_home_goals=final_hg,
            final_away_goals=final_ag,
            actual_additional_home=max(add_h, 0),
            actual_additional_away=max(add_a, 0),
            home_win_prob=result.home_win_prob,
            draw_prob=result.draw_prob,
            away_win_prob=result.away_win_prob,
            next_goal_home_prob=result.next_goal_home_prob,
            next_goal_away_prob=result.next_goal_away_prob,
            no_more_goals_prob=result.no_more_goals_prob,
            expected_remaining_home=result.expected_remaining_home,
            expected_remaining_away=result.expected_remaining_away,
            btts_yes_prob=result.derived_markets.get("btts_yes", 0.5),
            over_2_5_prob=result.derived_markets.get("over_2_5", 0.5),
            score_log_loss=round(score_ll, 5),
            onex2_rps=round(rps, 5),
            btts_brier=round(btts_b, 5),
            over_2_5_brier=round(ou_b, 5),
            next_goal_log_loss=round(ng_ll, 5) if ng_ll != float("inf") else 99.0,
            no_more_goals_brier=round(nmg_brier, 5),
            method=result.method,
            pregame_lh=pregame_lh,
            pregame_la=pregame_la,
            xg_available=result.method == "live_hazard_poisson" and "xg_unavailable" not in " ".join(result.warnings),
            warnings=result.warnings,
            fh_home_actual=fh_home_actual,
            fh_away_actual=fh_away_actual,
            fh_hw_prob=fh_hw_prob,
            fh_draw_prob=fh_draw_prob_val,
            fh_aw_prob=fh_aw_prob,
            fh_over_0_5_prob=fh_over_0_5_prob,
            fh_btts_prob=fh_btts_prob_val,
            fh_ignorance_score=fh_ignorance,
            fh_brier_score=fh_brier,
        )


def _rps_1x2(ph: float, pd: float, pa: float,
             ah: float, ad: float, aa: float) -> float:
    """Ranked Probability Score for 1X2 outcome."""
    # Cumulative probabilities: P(HW), P(HW or D)
    cum_p = [ph, ph + pd]
    cum_a = [ah, ah + ad]
    return sum((cum_p[i] - cum_a[i]) ** 2 for i in range(2)) / 2.0


def run_2022_replay(
    matches_df: pd.DataFrame,
    events_df: pd.DataFrame | None = None,
    stats_df: pd.DataFrame | None = None,
    pregame_lambdas: dict | None = None,
    output_path: str | None = None,
    momentum_df: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """
    Run the full 2022 World Cup replay and return a DataFrame of checkpoints.

    Parameters
    ----------
    matches_df      DataFrame with 2022 completed matches
    events_df       Optional BDL events DataFrame (match_id, type, clock_minute, team)
    stats_df        Optional BDL stats DataFrame (used for xG blend)
    pregame_lambdas Dict mapping match_id → (lh, la) from the composite prior
    output_path     If provided, save parquet to this path
    momentum_df     Optional momentum DataFrame (match_id, minute, value)

    Returns
    -------
    DataFrame with one row per (match, checkpoint_minute)
    """
    predictor = LivePMFPredictor()
    replayer = MatchReplayer(predictor)

    # Normalize BDL event columns to the internal schema expected by MatchReplayer.
    # BDL uses: incident_type, incident_class, time_minute, is_home
    # Internal expects: type, clock_minute, team
    events_norm: pd.DataFrame | None = None
    if events_df is not None and len(events_df) > 0:
        ev = events_df.copy()
        # Rename incident_type → type if needed
        if "incident_type" in ev.columns and "type" not in ev.columns:
            ev = ev.rename(columns={"incident_type": "type"})
        # Map incident_class for goals: ownGoal → own_goal, penalty → penalty_goal
        if "incident_class" in ev.columns:
            class_map = {"ownGoal": "own_goal", "penalty": "penalty_goal"}
            ev["type"] = ev.apply(
                lambda r: class_map.get(r.get("incident_class", ""), r["type"])
                if r["type"] == "goal" else r["type"],
                axis=1,
            )
            # Map card classes: red/yellowRed → red_card, yellow → yellow_card
            card_class_map = {"red": "red_card", "yellowRed": "red_card", "yellow": "yellow_card"}
            ev["type"] = ev.apply(
                lambda r: card_class_map.get(r.get("incident_class", ""), r["type"])
                if r["type"] == "card" else r["type"],
                axis=1,
            )
        # Rename time_minute → clock_minute if needed
        if "time_minute" in ev.columns and "clock_minute" not in ev.columns:
            ev = ev.rename(columns={"time_minute": "clock_minute"})
        # Derive team from is_home column if present
        if "is_home" in ev.columns and "team" not in ev.columns:
            ev["team"] = ev["is_home"].map(
                lambda x: "home" if (x is True or x == 1 or x == "True") else "away"
            )
        # Handle own goals: they're credited to the *other* team; swap in type only
        # (the timeline builder already handles own_goal swapping)
        events_norm = ev

    rows = []
    wc2022 = matches_df[
        (matches_df["season"] == 2022) &
        (matches_df.get("status", pd.Series(["completed"] * len(matches_df))) == "completed") &
        matches_df["home_goals"].notna()
    ].copy()

    log.info("Replaying %d completed 2022 matches...", len(wc2022))

    for idx, match_row in wc2022.iterrows():
        mid = str(match_row.get("match_id", idx))
        lh, la = 1.35, 1.00
        if pregame_lambdas and mid in pregame_lambdas:
            lh, la = pregame_lambdas[mid]

        match_events = None
        if events_norm is not None:
            # Match IDs may be int or str; compare with original type first, fall back to cast
            try:
                orig_mid = match_row.get("match_id", idx)
                match_events = events_norm[events_norm["match_id"] == orig_mid]
                if len(match_events) == 0:
                    # Try string comparison
                    match_events = events_norm[events_norm["match_id"].astype(str) == mid]
            except Exception:
                match_events = events_norm[events_norm["match_id"].astype(str) == mid]

        match_stats = None
        if stats_df is not None:
            try:
                match_stats = stats_df[stats_df["match_id"] == int(mid)]
            except (ValueError, TypeError):
                match_stats = stats_df[stats_df["match_id"].astype(str) == mid]

        cps = replayer.replay(match_row, match_events, match_stats, lh, la, momentum_df=momentum_df)
        for cp in cps:
            rows.append(cp.to_dict())

    df = pd.DataFrame(rows)
    if output_path and len(df) > 0:
        df.to_parquet(output_path, index=False)
        log.info("Written live_replay_2022.parquet (%d rows, %d matches)",
                 len(df), len(wc2022))
    return df
