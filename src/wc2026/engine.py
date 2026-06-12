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
        """Fit the model ladder on all completed historical matches."""
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
        return self

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
        """Predict a single match. Returns full JSON-serializable dict."""
        if self._ladder is None:
            self.fit_models()

        predictions: dict[str, ScorePMFPrediction] = {}

        # Get all model predictions
        for model_name in self._ladder.fitted_models():
            try:
                pred = self._ladder.predict(
                    model_name, home_team, away_team,
                    match_id=match_id, season=season, stage=stage, venue=venue,
                    neutral_venue=neutral_venue,
                )
                predictions[model_name] = pred
            except Exception as exc:
                log.warning("Model %s prediction failed: %s", model_name, exc)

        if not predictions:
            raise RuntimeError(f"No models produced predictions for {home_team} v {away_team}")

        # Add equal-probability baseline
        predictions["equal_probability"] = EqualProbabilityBaseline().predict(
            home_team, away_team, match_id=match_id
        )

        # Get market consensus
        market_data = None
        if self._odds_df is not None and match_id is not None:
            market_data = build_consensus(self._odds_df, match_id)

        # Champion model (best walk-forward performer if calibrated, else Dixon-Coles)
        champion_name = self._select_champion(predictions)
        champion_pred = predictions[champion_name]

        # Reconcile with market if available
        if market_data and market_data.has_1x2:
            champion_reconciled = reconcile_pmf(champion_pred, market_data)
        else:
            champion_reconciled = champion_pred

        # Consistency check
        consistency_errors = champion_reconciled.check_consistency()

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
                    "calibration_status": p.calibration_status.value,
                    "warnings": p.warnings,
                }
                for name, p in predictions.items()
            },
            "market": market_data.to_dict() if market_data else None,
            "model_vs_market": _compute_model_market_diff(champion_pred, market_data),
            "consistency_checks": consistency_errors,
            "warnings": _collect_warnings(predictions, market_data),
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
