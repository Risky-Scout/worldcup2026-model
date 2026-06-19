"""
Shadow EGM Runner.

Runs the new EGM team-strength layer in shadow mode.
Writes outputs to:
  data/predictions/shadow/
  data/predictions/team_margin_ratings/
  reports/live_shadow/

Does NOT modify public WizardOfOdds predictions.
Only activated when WC_EGM_SHADOW_MODE=True (default) or WC_EGM_LAYER_ENABLED=True.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
import json
import logging
from typing import Optional
import pandas as pd

log = logging.getLogger(__name__)

# Shadow output directories
SHADOW_DIR = Path("data/predictions/shadow")
TEAM_MARGIN_DIR = Path("data/predictions/team_margin_ratings")
SHADOW_REPORT_DIR = Path("reports/live_shadow")
TEAM_STRENGTH_REPORT_DIR = Path("reports/team_strength")

for _d in [SHADOW_DIR, TEAM_MARGIN_DIR, SHADOW_REPORT_DIR, TEAM_STRENGTH_REPORT_DIR]:
    _d.mkdir(parents=True, exist_ok=True)


@dataclass
class ShadowMatchPrediction:
    match_id: int
    home_team: str
    away_team: str
    prediction_timestamp: str

    # EGM layer outputs
    home_neutral_egm: float
    away_neutral_egm: float
    home_pure_strength_egm: float
    away_pure_strength_egm: float
    home_market_strength_egm: float
    away_market_strength_egm: float
    match_expected_goal_margin: float

    # Lambda outputs from EGM
    egm_lambda_home: float
    egm_lambda_away: float

    # Live model lambdas for comparison
    live_lambda_home: Optional[float]
    live_lambda_away: Optional[float]

    # Diagnostics
    sources_used: list[str] = field(default_factory=list)
    model_version: str = "shadow-v0.1"

    def to_dict(self) -> dict:
        return {
            "match_id": self.match_id,
            "home_team": self.home_team,
            "away_team": self.away_team,
            "prediction_timestamp": self.prediction_timestamp,
            "team_strength": {
                "scale": "expected home goals minus expected away goals, regulation time",
                "home_team": self.home_team,
                "away_team": self.away_team,
                "home_neutral_egm": self.home_neutral_egm,
                "away_neutral_egm": self.away_neutral_egm,
                "home_pure_strength_egm": self.home_pure_strength_egm,
                "away_pure_strength_egm": self.away_pure_strength_egm,
                "home_market_strength_egm": self.home_market_strength_egm,
                "away_market_strength_egm": self.away_market_strength_egm,
                "match_expected_goal_margin": self.match_expected_goal_margin,
                "egm_lambda_home": self.egm_lambda_home,
                "egm_lambda_away": self.egm_lambda_away,
                "uncertainty_egm": 0.0,
                "sources_used": self.sources_used,
            },
            "shadow_model": {
                "live_lambda_home": self.live_lambda_home,
                "live_lambda_away": self.live_lambda_away,
                "egm_lambda_home": self.egm_lambda_home,
                "egm_lambda_away": self.egm_lambda_away,
                "lambda_home_diff": (
                    self.egm_lambda_home - self.live_lambda_home
                    if self.live_lambda_home is not None else None
                ),
                "lambda_away_diff": (
                    self.egm_lambda_away - self.live_lambda_away
                    if self.live_lambda_away is not None else None
                ),
                "model_version": self.model_version,
            },
        }


class ShadowEGMRunner:
    """
    Orchestrates the shadow EGM layer.

    Usage:
        runner = ShadowEGMRunner()
        shadow_pred = runner.run_match(
            match_id=...,
            home_team=..., away_team=...,
            matches_history_df=...,
            odds_df=..., injuries_df=..., lineups_df=...,
            player_stats_df=..., team_stats_df=..., futures_df=...,
            match_row=..., stadium_row=...,
            home_standing=..., away_standing=...,
            live_lambda_home=..., live_lambda_away=...,
            prediction_timestamp=...,
        )
        runner.persist(shadow_pred)
    """

    def __init__(self, base_goals: float = 1.30):
        self.base_goals = base_goals
        self._stacker = None
        self._rating_fitter = None

    def _get_or_build_fitter(self, matches_df: pd.DataFrame):
        from src.wc2026.ratings.rating_components import RatingComponentFitter
        if self._rating_fitter is None:
            self._rating_fitter = RatingComponentFitter()
            if not matches_df.empty:
                self._rating_fitter.fit(matches_df)
        return self._rating_fitter

    def run_match(
        self,
        match_id: int,
        home_team: str,
        away_team: str,
        home_team_id: int,
        away_team_id: int,
        home_country_code: str,
        away_country_code: str,
        matches_history_df: pd.DataFrame,
        odds_df: pd.DataFrame,
        injuries_df: pd.DataFrame,
        lineups_df: pd.DataFrame,
        player_stats_df: pd.DataFrame,
        team_stats_df: pd.DataFrame,
        futures_df: pd.DataFrame,
        match_row: dict,
        stadium_row: Optional[dict],
        home_standing: Optional[dict],
        away_standing: Optional[dict],
        home_match_dates: list[str],
        away_match_dates: list[str],
        live_lambda_home: Optional[float],
        live_lambda_away: Optional[float],
        prediction_timestamp: Optional[datetime] = None,
    ) -> ShadowMatchPrediction:
        import numpy as np
        from src.wc2026.ratings.team_margin import TeamMarginRating
        from src.wc2026.models.egm_to_lambdas import (
            egm_components_to_lambdas, MatchContextAdjustment, margin_total_to_lambdas,
        )
        from src.wc2026.ratings.market_ability import compute_match_market_egm
        from src.wc2026.features.match_context import compute_match_context
        from src.wc2026.features.player_strength import build_player_ratings
        from src.wc2026.features.opponent_adjusted_xg import build_team_process_ratings
        from src.wc2026.ratings.futures_ability import compute_futures_ability

        ts = prediction_timestamp or datetime.now(timezone.utc)

        # --- Rating components ---
        fitter = self._get_or_build_fitter(matches_history_df)

        pi_home = fitter.pi_egm(home_team, away_team) or 0.0
        pi_away = fitter.pi_egm(away_team, home_team) or 0.0
        elo_home = fitter.elo_egm(home_team, away_team) or 0.0
        elo_away = fitter.elo_egm(away_team, home_team) or 0.0

        # --- xG process ---
        process_ratings = build_team_process_ratings(
            team_stats_df, prediction_timestamp=ts
        ) if not team_stats_df.empty else {}
        h_proc = process_ratings.get(home_team_id)
        a_proc = process_ratings.get(away_team_id)
        xg_att_home = h_proc.attack_egm_contribution() if h_proc else 0.0
        xg_def_home = h_proc.defense_egm_contribution() if h_proc else 0.0
        xg_att_away = a_proc.attack_egm_contribution() if a_proc else 0.0
        xg_def_away = a_proc.defense_egm_contribution() if a_proc else 0.0

        # --- Player strength ---
        player_ratings = build_player_ratings(
            player_stats_df, prediction_timestamp=ts
        ) if not player_stats_df.empty else {}
        home_player_vals = [r.overall_value_per90 for r in player_ratings.values()
                            if r.team_id == home_team_id]
        away_player_vals = [r.overall_value_per90 for r in player_ratings.values()
                            if r.team_id == away_team_id]
        player_egm_home = float(np.mean(home_player_vals) - 0.5) * 0.1 if home_player_vals else 0.0
        player_egm_away = float(np.mean(away_player_vals) - 0.5) * 0.1 if away_player_vals else 0.0

        # --- Futures ---
        futures_ability = compute_futures_ability(futures_df) if not futures_df.empty else {}
        fut_home = futures_ability.get(home_team_id)
        fut_away = futures_ability.get(away_team_id)
        futures_egm_home = fut_home.log_strength_proxy * 0.1 if fut_home else 0.0
        futures_egm_away = fut_away.log_strength_proxy * 0.1 if fut_away else 0.0

        # --- Market EGM ---
        odds_rows = (
            odds_df[odds_df["match_id"] == match_id].to_dict("records")
            if not odds_df.empty and "match_id" in odds_df.columns
            else []
        )
        mkt_egm_obj = compute_match_market_egm(
            match_id, home_team_id, away_team_id, odds_rows, ts.isoformat()
        ) if odds_rows else None
        market_egm = mkt_egm_obj.market_egm if mkt_egm_obj else 0.0
        market_total = mkt_egm_obj.market_total if mkt_egm_obj else 2.6

        # --- Context ---
        ctx_full = compute_match_context(
            match_row=match_row,
            home_team_country_code=home_country_code,
            away_team_country_code=away_country_code,
            stadium_row=stadium_row,
            home_standing=home_standing,
            away_standing=away_standing,
            home_match_dates=home_match_dates,
            away_match_dates=away_match_dates,
            prediction_timestamp=ts,
        )
        ctx = ctx_full.to_context_adjustment()

        # --- Build feature dicts ---
        pure_features_home = {
            "pi_egm": pi_home, "elo_egm": elo_home,
            "xg_attack_egm": xg_att_home, "xg_defense_egm": xg_def_home,
            "player_egm": player_egm_home, "futures_egm": futures_egm_home,
            "venue_egm": ctx_full.host_home_adj_log,
        }
        pure_features_away = {
            "pi_egm": pi_away, "elo_egm": elo_away,
            "xg_attack_egm": xg_att_away, "xg_defense_egm": xg_def_away,
            "player_egm": player_egm_away, "futures_egm": futures_egm_away,
            "venue_egm": ctx_full.host_away_adj_log,
        }

        stacker = self._get_or_build_stacker(matches_history_df, process_ratings, player_ratings, futures_ability)
        pure_egm_home = stacker.predict_pure(pure_features_home)
        pure_egm_away = stacker.predict_pure(pure_features_away)
        market_features_home = {**pure_features_home, "market_egm": market_egm, "market_total": market_total}
        market_features_away = {**pure_features_away, "market_egm": -market_egm, "market_total": market_total}
        mkt_egm_home = stacker.predict_market(market_features_home)
        mkt_egm_away = stacker.predict_market(market_features_away)

        # Symmetric decomposition: EGM ≈ attack_log - defense_log (opponent)
        attack_log_home = pure_egm_home / 2
        defense_log_home = -pure_egm_home / 2
        attack_log_away = pure_egm_away / 2
        defense_log_away = -pure_egm_away / 2

        home_rating = TeamMarginRating(
            team_id=home_team_id, team_name=home_team,
            abbreviation=None, confederation=None,
            neutral_egm=pure_egm_home,
            attack_log=attack_log_home,
            defense_log=defense_log_home,
            pure_strength_egm=pure_egm_home,
            market_strength_egm=mkt_egm_home,
            pi_component_egm=pi_home,
            elo_component_egm=elo_home,
            xg_process_component_egm=(xg_att_home + xg_def_home),
            player_component_egm=player_egm_home,
            futures_component_egm=futures_egm_home,
            sources_used=list(pure_features_home.keys()),
        )
        away_rating = TeamMarginRating(
            team_id=away_team_id, team_name=away_team,
            abbreviation=None, confederation=None,
            neutral_egm=pure_egm_away,
            attack_log=attack_log_away,
            defense_log=defense_log_away,
            pure_strength_egm=pure_egm_away,
            market_strength_egm=mkt_egm_away,
            pi_component_egm=pi_away,
            elo_component_egm=elo_away,
            xg_process_component_egm=(xg_att_away + xg_def_away),
            player_component_egm=player_egm_away,
            futures_component_egm=futures_egm_away,
            sources_used=list(pure_features_away.keys()),
        )

        lh, la, diag = egm_components_to_lambdas(home_rating, away_rating, ctx, self.base_goals)

        # Apply total-goal anchor to prevent lambda inflation
        WC_TOTAL_BASELINE = 2.65  # World Cup regulation-time average
        # Use market total if available and plausible
        if mkt_egm_obj is not None and 1.5 <= mkt_egm_obj.market_total <= 4.5:
            total_anchor = mkt_egm_obj.market_total
        else:
            total_anchor = WC_TOTAL_BASELINE

        margin = pure_egm_home - pure_egm_away
        lh_anchored, la_anchored = margin_total_to_lambdas(margin, total_anchor)

        return ShadowMatchPrediction(
            match_id=match_id,
            home_team=home_team,
            away_team=away_team,
            prediction_timestamp=ts.isoformat() if hasattr(ts, "isoformat") else str(ts),
            home_neutral_egm=home_rating.neutral_egm,
            away_neutral_egm=away_rating.neutral_egm,
            home_pure_strength_egm=home_rating.pure_strength_egm,
            away_pure_strength_egm=away_rating.pure_strength_egm,
            home_market_strength_egm=home_rating.market_strength_egm,
            away_market_strength_egm=away_rating.market_strength_egm,
            match_expected_goal_margin=lh_anchored - la_anchored,
            egm_lambda_home=lh_anchored,
            egm_lambda_away=la_anchored,
            live_lambda_home=live_lambda_home,
            live_lambda_away=live_lambda_away,
            sources_used=home_rating.sources_used,
        )

    def _get_or_build_stacker(self, matches_df, process_ratings, player_ratings, futures_ability):
        from src.wc2026.models.team_margin_stacker import TeamMarginStacker
        if self._stacker is None:
            self._stacker = TeamMarginStacker()
            if not matches_df.empty and len(matches_df) >= 10:
                feature_rows = self._build_training_rows(matches_df, process_ratings, player_ratings, futures_ability)
                if len(feature_rows) >= 10:
                    features_df = pd.DataFrame(feature_rows)
                    self._stacker.fit(features_df)
        return self._stacker

    def _build_training_rows(self, matches_df, process_ratings, player_ratings, futures_ability):
        import numpy as np
        rows = []
        completed = (
            matches_df.dropna(subset=["home_goals", "away_goals"])
            if "home_goals" in matches_df.columns
            else matches_df
        )
        for _, row in completed.iterrows():
            gd = float(row.get("home_goals", 0)) - float(row.get("away_goals", 0))
            rows.append({
                "match_id": row.get("id", 0),
                "datetime": row.get("datetime", "2020-01-01"),
                "target_gd": gd,
                "pi_egm": 0.0, "elo_egm": 0.0,
                "xg_attack_egm": 0.0, "xg_defense_egm": 0.0,
                "player_egm": 0.0, "futures_egm": 0.0, "venue_egm": 0.0,
                "market_egm": 0.0, "market_total": 2.6,
            })
        return rows

    def persist(self, pred: ShadowMatchPrediction, date_str: Optional[str] = None) -> Path:
        """Write shadow prediction to disk. Returns file path."""
        ds = date_str or datetime.now().strftime("%Y-%m-%d")
        out_path = SHADOW_DIR / f"shadow_{ds}.jsonl"
        with open(out_path, "a") as f:
            f.write(json.dumps(pred.to_dict()) + "\n")
        return out_path

    def persist_team_ratings(self, ratings: list, date_str: Optional[str] = None) -> Path:
        """Write team margin ratings to disk."""
        ds = date_str or datetime.now().strftime("%Y-%m-%d")
        out_path = TEAM_MARGIN_DIR / f"team_margin_ratings_{ds}.json"
        with open(out_path, "w") as f:
            json.dump(
                [r.to_dict() if hasattr(r, "to_dict") else r for r in ratings],
                f, indent=2, default=str,
            )
        return out_path
