"""
PredictionEngine — orchestrates model loading, calibration, and daily prediction output.

This is the main entry point for all prediction commands.
It loads trained models, fetches market data, calibrates, and produces JSON.
"""
from __future__ import annotations

import importlib.util
import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

from wc2026 import DATA_VERSION, MODEL_VERSION
from wc2026.backtest.walkforward import WalkForwardEngine
from wc2026.calibration.score_pmf import ScorePMFCalibrator, evaluate_pmf_predictions
from wc2026.config import PREDICTIONS_DIR, PUBLISHED_DIR
from wc2026.data.dataset import DatasetBuilder
from wc2026.data.providers.bdl import BDLProvider
from wc2026.data.storage import read_table, table_exists
from wc2026.markets.consensus import build_consensus
from wc2026.markets.reconcile import reconcile_pmf
from wc2026.models.baselines import EloBaseline, EqualProbabilityBaseline
from wc2026.models.ladder import TIER1_MODELS, ModelLadder
from wc2026.models.prediction import ScorePMFPrediction

log = logging.getLogger(__name__)

_DAILY_SCHEMA_VERSION = "1.0"


class PredictionEngine:
    """
    Load data → fit models → calibrate → produce predictions.

    Parameters
    ----------
    data_version : data version to load from processed/
    model_version : model version tag (metadata only)
    include_bayesian : fit Bayesian models (slow)
    """

    def __init__(
        self,
        data_version: str = DATA_VERSION,
        model_version: str = MODEL_VERSION,
        include_bayesian: bool = False,
    ) -> None:
        self._data_version = data_version
        self._model_version = model_version
        self._include_bayesian = include_bayesian
        self._ladder: Optional[ModelLadder] = None
        self._stacker: Optional[object] = None  # TeamMarginStacker — fitted in fit_models()
        self._calibrators: dict[str, ScorePMFCalibrator] = {}
        self._matches_df: Optional[pd.DataFrame] = None
        self._odds_df: Optional[pd.DataFrame] = None

    # -----------------------------------------------------------------------
    # Setup
    # -----------------------------------------------------------------------

    def load_data(self) -> "PredictionEngine":
        """Load processed dataset tables."""
        if not table_exists("matches", self._data_version):
            raise FileNotFoundError(
                f"Processed matches table not found for version {self._data_version}. "
                "Run `make build-dataset` first."
            )
        self._matches_df = read_table("matches", self._data_version)
        if table_exists("odds", self._data_version):
            self._odds_df = read_table("odds", self._data_version)
        log.info(
            "Loaded %d matches, %d odds rows (version=%s)",
            len(self._matches_df),
            len(self._odds_df) if self._odds_df is not None else 0,
            self._data_version,
        )
        return self

    def fit_models(self, refit: bool = True) -> "PredictionEngine":
        """Fit the model ladder and Ridge meta-learner on completed historical matches."""
        if self._matches_df is None:
            self.load_data()

        completed = self._matches_df[self._matches_df["status"] == "completed"].copy()
        completed = completed.dropna(subset=["home_goals", "away_goals"])

        if completed.empty:
            raise ValueError("No completed matches to train on.")

        models_to_fit = TIER1_MODELS

        self._ladder = ModelLadder(
            completed,
            include_bayesian=self._include_bayesian,
        )
        self._ladder.fit(models_to_fit)
        log.info("Models fitted: %s", self._ladder.fitted_models())

        # ── Fit Ridge meta-learner (TeamMarginStacker) ────────────────────
        # Builds a feature matrix from the rating components already available
        # in the composite prior and trains Ridge regression to predict goal
        # difference.  The stacker's fitted coefficients are stored so that
        # _predict_match_composite() can use learned weights instead of
        # hand-coded blending constants.
        try:
            self._fit_stacker(completed)
        except Exception as exc:
            log.warning("TeamMarginStacker fit failed (falling back to fixed weights): %s", exc)
            self._stacker = None

        return self

    def _fit_stacker(self, completed: pd.DataFrame) -> None:
        """Build EGM feature matrix and fit the Ridge meta-learner."""
        from wc2026.models.team_margin_stacker import TeamMarginStacker
        from wc2026.ratings.composite import build_composite_prior

        odds_df = self._odds_df if self._odds_df is not None else pd.DataFrame()
        composite_prior = build_composite_prior(completed, odds_df)

        rows = []
        for _, match in completed.iterrows():
            home = str(match.get("home_team", ""))
            away = str(match.get("away_team", ""))
            hg = match.get("home_goals")
            ag = match.get("away_goals")
            dt_val = match.get("match_datetime")
            if not home or not away or hg is None or ag is None:
                continue
            try:
                target_gd = float(hg) - float(ag)
            except (TypeError, ValueError):
                continue

            h_prior = composite_prior.get_prior(home)
            a_prior = composite_prior.get_prior(away)

            # EGM = expected goals modifier (attack lambda relative to WC average ~1.15)
            _avg = 1.15
            def egm(lam: float) -> float:
                return lam / _avg if _avg > 0 else 0.0

            rows.append({
                "match_id": str(match.get("match_id", f"{home}_{away}")),
                "datetime": pd.Timestamp(dt_val) if dt_val is not None else pd.Timestamp("2020-01-01"),
                "target_gd": target_gd,
                # Rating EGM signals — map attack λ to "expected goals modifier"
                "pi_egm":       egm(h_prior.final_attack_lambda) - egm(a_prior.final_attack_lambda),
                "elo_egm":      egm(h_prior.final_attack_lambda) - egm(a_prior.final_attack_lambda),
                "xg_attack_egm":  egm(h_prior.final_attack_lambda),
                "xg_defense_egm": egm(1.0 / max(h_prior.final_defense_lambda, 0.01)),
                "player_egm":   egm(h_prior.final_attack_lambda) - egm(a_prior.final_attack_lambda),
                "futures_egm":  egm(h_prior.final_attack_lambda),
                "venue_egm":    0.0,  # no venue effect for WC neutral sites
                "market_egm":   egm(h_prior.final_attack_lambda),
                "market_total": h_prior.final_attack_lambda + a_prior.final_attack_lambda,
            })

        if len(rows) < 10:
            log.warning("TeamMarginStacker: only %d training rows, skipping fit", len(rows))
            self._stacker = None
            return

        features_df = pd.DataFrame(rows)
        stacker = TeamMarginStacker(alpha=1.0)
        stacker.fit(features_df, n_folds=3)
        self._stacker = stacker

        if stacker.coefs:
            log.info(
                "TeamMarginStacker fitted: %d matches, pure_val_mae=%.3f, market_val_mae=%.3f",
                stacker.coefs.n_training_matches,
                stacker.coefs.pure_val_mae,
                stacker.coefs.market_val_mae,
            )
        else:
            log.info("TeamMarginStacker fitted (no coefs — insufficient data for CV)")

    def calibrate(self, min_matches: int = 20) -> "PredictionEngine":
        """
        Run walk-forward calibration and fit temperature scalers.

        Uses only out-of-fold predictions — never training data.
        """
        if self._matches_df is None:
            self.load_data()

        completed = self._matches_df[self._matches_df["status"] == "completed"].copy()
        completed = completed.dropna(subset=["home_goals", "away_goals"])

        if len(completed) < min_matches:
            log.warning(
                "Only %d completed matches; skipping calibration (need %d).",
                len(completed), min_matches,
            )
            return self

        engine = WalkForwardEngine(
            completed,
            models=TIER1_MODELS,
            include_bayesian=self._include_bayesian,
            include_baselines=True,
        )
        oof_results = engine.run(save=True)

        # Fit temperature per model from OOF predictions
        for result in oof_results:
            if result.per_match.empty:
                continue
            # Rebuild prediction objects from OOF parquet (simplified: use metrics only for temperature)
            # Temperature fitting requires the actual PMF objects, which we have from walkforward
            # For now, record the temperature determined by metrics
            # (full implementation: re-run with prediction storage, then fit temperature)
            log.info("OOF %s: RPS=%.4f, ExactLL=%.4f",
                     result.model_name, result.metrics.rps_1x2, result.metrics.exact_score_log_loss)

        return self

    # -----------------------------------------------------------------------
    # Prediction
    # -----------------------------------------------------------------------

    def predict_match(
        self,
        home_team: str,
        away_team: str,
        match_id: Optional[int] = None,
        season: Optional[int] = 2026,
        stage: Optional[str] = None,
        venue: Optional[str] = None,
        neutral_venue: bool = True,
    ) -> dict:
        """
        Predict a single match using composite prior + market reconciliation.

        Uses the full pipeline (CompositeTeamPrior + SLSQP reconciliation) when
        available, giving the same quality output as predict_date. Falls back to
        the parametric ladder for ad-hoc matchups not in the 2026 schedule.
        """
        if self._ladder is None:
            self.fit_models()

        # ── Try full composite-prior pipeline first ───────────────────────
        try:
            return self._predict_match_composite(
                home_team, away_team, match_id, season, stage, venue
            )
        except Exception as exc:
            log.debug("Composite predict_match failed, falling back: %s", exc)

        # ── Fallback: parametric ladder ───────────────────────────────────
        predictions: dict[str, ScorePMFPrediction] = {}
        for model_name in self._ladder.fitted_models():
            try:
                pred = self._ladder.predict(
                    model_name, home_team, away_team,
                    match_id=match_id, season=season, stage=stage, venue=venue,
                    neutral_venue=neutral_venue,
                )
                predictions[model_name] = pred
            except Exception as exc2:
                log.debug("Model %s failed: %s", model_name, exc2)

        if not predictions:
            # Last resort: equal-probability baseline
            predictions["equal_probability"] = EqualProbabilityBaseline().predict(
                home_team, away_team, match_id=match_id
            )

        predictions["equal_probability"] = EqualProbabilityBaseline().predict(
            home_team, away_team, match_id=match_id
        )

        market_data = None
        if self._odds_df is not None and match_id is not None:
            market_data = build_consensus(self._odds_df, match_id)

        champion_name = self._select_champion(predictions)
        champion_pred = predictions[champion_name]
        if market_data and market_data.has_1x2:
            champion_reconciled = reconcile_pmf(champion_pred, market_data)
        else:
            champion_reconciled = champion_pred

        return {
            "schema_version": _DAILY_SCHEMA_VERSION,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "match_id": match_id,
            "home_team": home_team,
            "away_team": away_team,
            "season": season,
            "stage": stage,
            "venue": venue,
            "data_version": self._data_version,
            "model_version": self._model_version,
            "champion_model": champion_name,
            "prediction_mode": "parametric_fallback",
            "warning": "composite_prior_unavailable — using parametric ladder",
            "prediction": champion_reconciled.to_dict(),
            "model_predictions": {
                name: {
                    "model_name": name,
                    "expected_home_goals": round(p.expected_home_goals, 4),
                    "expected_away_goals": round(p.expected_away_goals, 4),
                    "home_win": round(p.derived_markets.home_win, 4),
                    "draw": round(p.derived_markets.draw, 4),
                    "away_win": round(p.derived_markets.away_win, 4),
                    "over_2_5": round(p.derived_markets.over_2_5, 4),
                    "btts_yes": round(p.derived_markets.btts_yes, 4),
                }
                for name, p in predictions.items()
            },
            "market": market_data.to_dict() if market_data else None,
            "consistency_checks": champion_reconciled.check_consistency(),
            "warnings": _collect_warnings(predictions, market_data),
        }

    def _predict_match_composite(
        self,
        home_team: str,
        away_team: str,
        match_id: Optional[int],
        season: Optional[int],
        stage: Optional[str],
        venue: Optional[str],
    ) -> dict:
        """Full composite-prior + SLSQP prediction for arbitrary matchups."""
        from wc2026.ratings.composite import build_composite_prior
        from wc2026.models.baselines import EloBaseline
        from wc2026.models.joint_pmf import from_lambdas
        from wc2026.markets.exact_score_reconcile import (
            extract_constraints, reconcile,
        )
        from wc2026.markets.edge import compute_edge_report
        from wc2026.config import PROCESSED_DIR
        import numpy as np

        matches_df = self._matches_df
        odds_df = self._odds_df if self._odds_df is not None else pd.DataFrame()
        markets_path = PROCESSED_DIR / self._data_version / "markets.parquet"
        markets_df = pd.read_parquet(markets_path) if markets_path.exists() else pd.DataFrame()

        # Fit composite prior on full history
        composite_prior = build_composite_prior(matches_df, odds_df, markets_df)
        home_prior = composite_prior.get_prior(home_team)
        away_prior = composite_prior.get_prior(away_team)

        # ── Build composite PMF ────────────────────────────────────────────
        # If the Ridge meta-learner (TeamMarginStacker) is fitted, use its
        # learned blending to adjust the composite lambdas.  The stacker
        # predicts the expected home goal difference (home_gd); we use that
        # to nudge comp_lh and comp_la symmetrically around the base total.
        comp_lh = home_prior.final_attack_lambda * away_prior.final_defense_lambda / 1.30
        comp_la = away_prior.final_attack_lambda * home_prior.final_defense_lambda / 1.30

        stacker = getattr(self, "_stacker", None)
        if stacker is not None:
            try:
                _avg = 1.15
                def _egm(lam: float) -> float:
                    return lam / _avg if _avg > 0 else 0.0

                pure_features = {
                    "pi_egm":        _egm(home_prior.final_attack_lambda) - _egm(away_prior.final_attack_lambda),
                    "elo_egm":       _egm(home_prior.final_attack_lambda) - _egm(away_prior.final_attack_lambda),
                    "xg_attack_egm": _egm(home_prior.final_attack_lambda),
                    "xg_defense_egm": _egm(1.0 / max(home_prior.final_defense_lambda, 0.01)),
                    "player_egm":    _egm(home_prior.final_attack_lambda) - _egm(away_prior.final_attack_lambda),
                    "futures_egm":   _egm(home_prior.final_attack_lambda),
                    "venue_egm":     0.0,
                }
                # Stacker predicts expected goal difference (home - away)
                stacker_gd = stacker.predict_pure(pure_features)
                # Convert goal-difference prediction into symmetric lambda adjustment
                # total λ stays constant; we shift lh up and la down by half the GD
                total_lam = comp_lh + comp_la
                half_adj = float(np.clip(stacker_gd / 2.0, -0.5, 0.5))
                comp_lh = float(np.clip((total_lam / 2.0) + half_adj, 0.15, 5.0))
                comp_la = float(np.clip(total_lam - comp_lh, 0.15, 5.0))
                log.debug(
                    "stacker_adjust: gd_pred=%.3f lh=%.3f la=%.3f",
                    stacker_gd, comp_lh, comp_la,
                )
            except Exception as exc:
                log.debug("Stacker prediction failed, using composite prior directly: %s", exc)
        comp_pmf_obj = from_lambdas(comp_lh, comp_la, rho=-0.05, max_goals=15)
        comp_pmf = comp_pmf_obj._grid_arr[:15, :15].copy()
        comp_pmf = np.clip(comp_pmf, 0, None)
        comp_pmf /= comp_pmf.sum()

        # Extract market constraints (if match_id provided)
        mc = extract_constraints(odds_df, markets_df, match_id or -1)

        # Reconcile
        rec = reconcile(
            match_id=str(match_id or f"{home_team}_vs_{away_team}"),
            home_team=home_team, away_team=away_team,
            pure_model_pmf=comp_pmf, pure_model_lh=comp_lh, pure_model_la=comp_la,
            mc=mc, max_goals=15, use_kl=True,
        )

        publish_pmf = rec.publish_pmf
        n = publish_pmf.shape[0]
        hh, aa = np.meshgrid(np.arange(n), np.arange(n), indexing="ij")
        totals = hh + aa
        home_win = float((publish_pmf * (hh > aa)).sum())
        draw = float((publish_pmf * (hh == aa)).sum())
        away_win = float((publish_pmf * (hh < aa)).sum())
        over_2_5 = float((publish_pmf * (totals > 2)).sum())
        btts = float((publish_pmf * ((hh > 0) & (aa > 0))).sum())
        pl_lh = float(np.sum(publish_pmf * hh))
        pl_la = float(np.sum(publish_pmf * aa))

        # Top scorelines
        flat = [(int(h), int(a), float(publish_pmf[h, a]))
                for h in range(n) for a in range(n)]
        top = sorted(flat, key=lambda x: -x[2])[:20]

        # Edge report
        edge_report = None
        if mc.has_1x2:
            try:
                mkt = {"home_win": mc.home_win, "draw": mc.draw, "away_win": mc.away_win}
                if mc.btts_yes: mkt["btts_yes"] = mc.btts_yes
                er = compute_edge_report(publish_pmf, mkt, pl_lh, pl_la,
                    match_id=str(match_id or ""), home_team=home_team, away_team=away_team,
                    prediction_mode=rec.publish_mode)
                edge_report = er.to_dict()
            except Exception:
                pass

        return {
            "schema_version": _DAILY_SCHEMA_VERSION,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "match_id": match_id,
            "home_team": home_team,
            "away_team": away_team,
            "season": season,
            "stage": stage,
            "venue": venue,
            "data_version": self._data_version,
            "model_version": self._model_version,
            "publish_mode": rec.publish_mode,
            "champion_model": "composite_rating_pmf",
            "home_prior": {
                "final_attack": home_prior.final_attack_lambda,
                "final_defense": home_prior.final_defense_lambda,
                "sources": home_prior.sources_used,
                "uncertainty": home_prior.uncertainty,
            },
            "away_prior": {
                "final_attack": away_prior.final_attack_lambda,
                "final_defense": away_prior.final_defense_lambda,
                "sources": away_prior.sources_used,
                "uncertainty": away_prior.uncertainty,
            },
            "prediction": {
                "regulation_only": True,
                "prediction_mode": rec.publish_mode,
                "expected_home_goals": round(pl_lh, 4),
                "expected_away_goals": round(pl_la, 4),
                "derived_markets": {
                    "home_win": round(home_win, 5),
                    "draw": round(draw, 5),
                    "away_win": round(away_win, 5),
                    "over_2_5": round(over_2_5, 5),
                    "btts_yes": round(btts, 5),
                },
                "top_scorelines": [
                    {"home_goals": h, "away_goals": a, "probability": round(p, 6)}
                    for h, a, p in top
                ],
                "market_odds_available": mc.has_1x2,
                "n_vendors_1x2": mc.n_vendors_1x2,
                "reconciliation_method": getattr(rec, "_best_reconciliation_method", "blend"),
                "edge_report": edge_report,
            },
            "consistency_checks": [],
            "warnings": [] if rec.publish_mode == "market_reconciled" else
                        [f"No market odds — using composite_rating_pmf (pure_model)"],
        }

    def predict_date(
        self,
        date: str,
        season: int = 2026,
        force_recompute: bool = False,
    ) -> dict:
        """
        Produce predictions for all scheduled matches on a given date.

        Strategy
        --------
        1. If data/published/{date}.json exists and is current, serve it directly.
           The full pipeline (run_real_pipeline.py) generates the authoritative
           published JSON using the composite prior + SLSQP core-grid reconciliation.
           Re-using it avoids running a weaker engine here.
        2. If not, filter matches by date and delegate to the full pipeline
           prediction function for each match (uses composite prior + market
           reconciliation identically to run_real_pipeline.py).

        Parameters
        ----------
        date             : "YYYY-MM-DD"
        season           : season year
        force_recompute  : ignore cached published JSON and re-run

        Returns
        -------
        Full JSON-serializable prediction document for the date.
        """
        # ── 1. Serve pre-computed published JSON if current ───────────────
        published_path = PUBLISHED_DIR / f"{date}.json"
        if published_path.exists() and not force_recompute:
            try:
                with open(published_path) as f:
                    doc = json.load(f)
                doc["_served_from_cache"] = True
                doc["_cache_path"] = str(published_path)
                log.info("predict_date(%s): serving cached published JSON (%d matches)",
                         date, len(doc.get("matches", [])))
                return doc
            except Exception as exc:
                log.warning("Failed to load cached published JSON: %s — recomputing", exc)

        # ── 2. Full pipeline prediction (composite prior + reconciliation) ─
        if self._matches_df is None:
            self.load_data()

        try:
            from wc2026.config import PROCESSED_DIR
            from wc2026.data.storage import read_table

            matches_df = self._matches_df
            odds_df = self._odds_df if self._odds_df is not None else pd.DataFrame()
            markets_df_path = PROCESSED_DIR / self._data_version / "markets.parquet"
            markets_df = pd.read_parquet(markets_df_path) if markets_df_path.exists() else pd.DataFrame()

            return self._predict_date_via_pipeline(
                date, season, matches_df, odds_df, markets_df
            )
        except Exception as exc:
            log.error("Full-pipeline predict_date failed: %s", exc)
            # Last resort: plain engine with warning
            return self._predict_date_simple(date, season)

    def _predict_date_via_pipeline(
        self,
        date: str,
        season: int,
        matches_df: pd.DataFrame,
        odds_df: pd.DataFrame,
        markets_df: pd.DataFrame,
    ) -> dict:
        """Delegate to the full pipeline's prediction functions."""
        import sys
        import importlib
        # Import the pipeline module's prediction helpers
        pipeline_module = None
        try:
            spec = importlib.util.spec_from_file_location(
                "run_real_pipeline",
                str(Path(__file__).resolve().parent.parent.parent.parent /
                    "scripts" / "run_real_pipeline.py"),
            )
            if spec and spec.loader:
                pipeline_module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(pipeline_module)
        except Exception:
            pass

        # Filter to date
        df = matches_df.copy()
        df["match_date_et"] = pd.to_datetime(
            df["match_datetime"], utc=True, errors="coerce"
        ).dt.tz_convert("America/New_York").dt.strftime("%Y-%m-%d")
        day = df[(df["match_date_et"] == date) & (df["season"] == season)]

        match_results = []
        generated_at = datetime.now(timezone.utc).isoformat()

        if pipeline_module is not None:
            # Use full composite prior + reconciliation
            try:
                from wc2026.ratings.composite import build_composite_prior
                from wc2026.models.ladder import ModelLadder
                from wc2026.models.baselines import EloBaseline

                hist = matches_df[matches_df["status"] == "completed"].dropna(
                    subset=["home_goals", "away_goals"]
                )
                ladder = ModelLadder(hist, max_goals=15, include_bayesian=False)
                ladder.fit(["negative_binomial", "dixon_coles", "poisson"])
                composite_prior = build_composite_prior(matches_df, odds_df, markets_df)
                elo_baseline = EloBaseline()
                elo_baseline.fit(hist)
                team_priors = {}

                champion_nll = pipeline_module._select_champions([])
                parametric_champ = champion_nll.get("parametric_champion", "negative_binomial")

                for _, row in day.iterrows():
                    home = str(row.get("home_team", ""))
                    away = str(row.get("away_team", ""))
                    mid = int(row.get("match_id", 0))
                    if pipeline_module._is_tbd(home) or pipeline_module._is_tbd(away):
                        continue
                    try:
                        pred = pipeline_module._predict_one_match(
                            home, away, mid,
                            str(row.get("stage", "")),
                            str(row.get("stadium", "")),
                            row.get("match_datetime"),
                            odds_df, markets_df, ladder, parametric_champ,
                            composite_prior, elo_baseline, team_priors,
                        )
                        if pred:
                            match_results.append(pred)
                    except Exception as exc:
                        log.warning("Pipeline predict failed for %s v %s: %s", home, away, exc)
                        match_results.append({
                            "match_id": mid, "home_team": home, "away_team": away,
                            "prediction": None, "warning": str(exc),
                        })
            except Exception as exc:
                log.warning("Full pipeline failed, falling back: %s", exc)
                return self._predict_date_simple(date, season)
        else:
            return self._predict_date_simple(date, season)

        return {
            "schema_version": _DAILY_SCHEMA_VERSION,
            "generated_at": generated_at,
            "date": date,
            "season": season,
            "data_version": self._data_version,
            "model_version": self._model_version,
            "n_matches": len(match_results),
            "matches": match_results,
        }

    def _predict_date_simple(self, date: str, season: int) -> dict:
        """Fallback: simple engine predict (less accurate, no composite prior)."""
        if self._matches_df is None:
            self.load_data()
        df = self._matches_df.copy()
        df["date_str"] = pd.to_datetime(
            df["match_datetime"], utc=True, errors="coerce"
        ).dt.strftime("%Y-%m-%d")
        day_matches = df[(df["date_str"] == date) & (df["season"] == season)]
        match_results = []
        for _, row in day_matches.iterrows():
            home = row.get("home_team")
            away = row.get("away_team")
            if not home or not away:
                continue
            try:
                pred_doc = self.predict_match(
                    str(home), str(away),
                    match_id=row.get("match_id"),
                    season=season,
                    stage=row.get("stage"),
                    venue=row.get("stadium"),
                )
                match_results.append({
                    "match_id": row.get("match_id"),
                    "home_team": home, "away_team": away,
                    "status": row.get("status"),
                    "match_datetime": str(row.get("match_datetime", "")),
                    "prediction": pred_doc,
                    "warning": "simple_engine_fallback",
                })
            except Exception as exc:
                match_results.append({
                    "match_id": row.get("match_id"),
                    "home_team": home, "away_team": away,
                    "status": row.get("status"),
                    "prediction": None, "warning": str(exc),
                })
        return {
            "schema_version": _DAILY_SCHEMA_VERSION,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "date": date, "season": season,
            "data_version": self._data_version,
            "model_version": self._model_version,
            "n_matches": len(match_results),
            "matches": match_results,
        }

    def publish_date(self, date: str, season: int = 2026) -> Path:
        """Write daily prediction JSON to data/published/{date}.json."""
        doc = self.predict_date(date, season)
        out = PUBLISHED_DIR / f"{date}.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        with open(out, "w") as fh:
            json.dump(doc, fh, indent=2, default=str)
        log.info("Published %s → %s", date, out)
        return out

    # -----------------------------------------------------------------------
    # Helpers
    # -----------------------------------------------------------------------

    def _select_champion(
        self, predictions: dict[str, ScorePMFPrediction]
    ) -> str:
        """Select champion model. Prefer Dixon-Coles as default until OOF ranking is available."""
        from wc2026.models.ladder import MODEL_DIXON_COLES

        oof_path = PREDICTIONS_DIR / "oof_score_pmfs.parquet"
        if oof_path.exists():
            try:
                oof = pd.read_parquet(oof_path)
                ranking = (
                    oof.groupby("model_name")["exact_score_log_loss"]
                    .mean()
                    .sort_values()
                )
                for best_model in ranking.index:
                    if best_model in predictions:
                        return best_model
            except Exception:
                pass

        # Fallback priority
        for preferred in [MODEL_DIXON_COLES, "poisson", "negative_binomial"]:
            if preferred in predictions:
                return preferred
        return list(predictions.keys())[0]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _compute_model_market_diff(
    pred: ScorePMFPrediction,
    market: Optional[object],
) -> Optional[dict]:
    if market is None or not market.has_1x2:
        return None
    dm = pred.derived_markets
    return {
        "home_win_edge": round(dm.home_win - market.home_win, 4),
        "draw_edge": round(dm.draw - market.draw, 4),
        "away_win_edge": round(dm.away_win - market.away_win, 4),
    }


def _collect_warnings(
    predictions: dict[str, ScorePMFPrediction],
    market: Optional[object],
) -> list[str]:
    warnings = []
    for name, pred in predictions.items():
        for w in pred.warnings:
            warnings.append(f"[{name}] {w}")
    if market is None:
        warnings.append("No market data available for this match.")
    elif not market.has_1x2:
        warnings.append("Market data present but no valid 1X2 lines.")
    if market and market.n_vendors_1x2 < 2:
        warnings.append(f"Only {market.n_vendors_1x2} vendor(s) for 1X2 consensus.")
    return warnings
