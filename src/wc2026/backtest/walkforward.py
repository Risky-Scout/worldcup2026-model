"""
Walk-forward backtesting engine.

Contract
--------
- Train only on data available BEFORE the prediction date.
- Generate PMF predictions for each match BEFORE seeing the result.
- Record predictions with full metadata.
- Never look ahead: no future goals, no future lineups, no closing odds
  in standard prediction mode.
- All predictions are saved to data/predictions/oof_score_pmfs.parquet.

Algorithm
---------
For each match i in [start_idx, end]:
  1. train_df = all completed matches with match_datetime < match_i.match_datetime
  2. Fit each requested model on train_df (if not already fitted for a nearby date)
  3. Predict match_i → ScorePMFPrediction
  4. Evaluate prediction vs actual result
  5. Record prediction row

min_train_matches : minimum matches to train a model (default 10).
refit_every : re-fit models every N matches (default 1 = every match).
              Set higher for speed; set 1 for strictest walk-forward.
"""
from __future__ import annotations

import hashlib
import json
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

from wc2026 import DATA_VERSION, MODEL_VERSION
from wc2026.calibration.score_pmf import CalibrationMetrics, evaluate_pmf_predictions
from wc2026.config import PREDICTIONS_DIR, RANDOM_SEED
from wc2026.models.baselines import (
    EloBaseline,
    EqualProbabilityBaseline,
    HistoricalBaseRateBaseline,
)
from wc2026.models.ladder import (
    ALL_MODELS,
    TIER1_MODELS,
    ModelLadder,
)
from wc2026.models.prediction import ScorePMFPrediction

log = logging.getLogger(__name__)

_DEFAULT_MIN_TRAIN = 10
_DEFAULT_REFIT_EVERY = 5  # re-fit every 5 new results


@dataclass
class WalkForwardResult:
    """Aggregated results from a walk-forward run."""

    run_timestamp: str
    model_name: str
    season_filter: Optional[list[int]]
    n_predictions: int
    n_train_matches_final: int
    metrics: CalibrationMetrics
    predictions_path: Optional[Path]
    per_match: pd.DataFrame = field(default_factory=pd.DataFrame)

    def to_dict(self) -> dict:
        return {
            "run_timestamp": self.run_timestamp,
            "model_name": self.model_name,
            "seasons": self.season_filter,
            "n_predictions": self.n_predictions,
            "n_train_matches_final": self.n_train_matches_final,
            "metrics": self.metrics.to_dict(),
            "predictions_path": str(self.predictions_path),
        }


class WalkForwardEngine:
    """
    Strict time-ordered walk-forward backtesting.

    Parameters
    ----------
    df : pd.DataFrame
        Completed matches. Must have: home_team, away_team, home_goals,
        away_goals, match_datetime, is_neutral, match_weight.
        Rows must be sorted by match_datetime ascending.
    models : list[str]
        Model names from ModelLadder.ALL_MODELS or ["all"].
    include_baselines : bool
        If True, also run naive baselines.
    min_train_matches : int
        Minimum history required before making a prediction.
    refit_every : int
        Re-fit models every N steps.
    max_goals : int
        PMF grid size.
    include_bayesian : bool
        Include Bayesian models (slow).
    """

    def __init__(
        self,
        df: pd.DataFrame,
        models: list[str] | None = None,
        include_baselines: bool = True,
        min_train_matches: int = _DEFAULT_MIN_TRAIN,
        refit_every: int = _DEFAULT_REFIT_EVERY,
        max_goals: int = 10,
        include_bayesian: bool = False,  # off by default for speed
        random_seed: int = RANDOM_SEED,
    ) -> None:
        self._df = df.sort_values("match_datetime").reset_index(drop=True)
        self._model_names = models if models else TIER1_MODELS
        self._include_baselines = include_baselines
        self._min_train = min_train_matches
        self._refit_every = refit_every
        self._max_goals = max_goals
        self._include_bayesian = include_bayesian
        self._seed = random_seed

    def run(
        self,
        start_from_idx: Optional[int] = None,
        season_filter: Optional[list[int]] = None,
        save: bool = True,
    ) -> list[WalkForwardResult]:
        """
        Run walk-forward and return one WalkForwardResult per model.

        Parameters
        ----------
        start_from_idx : start prediction from this row index (default = min_train_matches)
        season_filter : if set, only predict matches in these seasons
        save : save predictions to parquet
        """
        df = self._df.copy()
        if season_filter:
            # We always train on all history before; we only evaluate on filtered seasons
            predict_mask = df["season"].isin(season_filter)
        else:
            predict_mask = pd.Series(True, index=df.index)

        start_idx = start_from_idx or self._min_train
        n = len(df)

        # Rows to predict
        predict_indices = [
            i for i in range(start_idx, n)
            if predict_mask.iloc[i]
            and df.iloc[i]["home_goals"] is not None
            and df.iloc[i]["away_goals"] is not None
        ]

        log.info(
            "Walk-forward: %d total matches, %d to predict (start_idx=%d)",
            n, len(predict_indices), start_idx,
        )

        run_ts = datetime.now(timezone.utc).isoformat()

        # Collect per-model per-match prediction rows
        model_rows: dict[str, list[dict]] = {m: [] for m in self._model_names}
        if self._include_baselines:
            for b in ["equal_probability", "historical_base_rate", "elo"]:
                model_rows[b] = []

        # We re-fit every `refit_every` steps. Track last refit index.
        last_refit: dict[str, int] = {}
        fitted_ladders: dict[int, ModelLadder] = {}

        for step, pred_idx in enumerate(predict_indices):
            train_df = df.iloc[:pred_idx]  # strictly before prediction date

            if len(train_df) < self._min_train:
                log.debug("Skipping row %d: not enough training data (%d)", pred_idx, len(train_df))
                continue

            match_row = df.iloc[pred_idx]
            home_team = match_row["home_team"]
            away_team = match_row["away_team"]
            actual_h = int(match_row["home_goals"])
            actual_a = int(match_row["away_goals"])
            neutral = bool(match_row.get("is_neutral", 1))

            # ── penaltyblog models ──────────────────────────────────────
            refit_key = pred_idx // self._refit_every
            if refit_key not in fitted_ladders:
                ladder = ModelLadder(
                    train_df,
                    max_goals=self._max_goals,
                    include_bayesian=self._include_bayesian,
                    random_seed=self._seed,
                )
                try:
                    ladder.fit(self._model_names)
                    fitted_ladders[refit_key] = ladder
                except Exception as exc:
                    log.warning("Ladder fit failed at step %d: %s", step, exc)
                    continue
            else:
                ladder = fitted_ladders[refit_key]

            for model_name in self._model_names:
                if model_name not in ladder.fitted_models():
                    continue
                try:
                    pred = ladder.predict(
                        model_name,
                        home_team,
                        away_team,
                        match_id=int(match_row.get("match_id", 0)),
                        season=match_row.get("season"),
                        stage=match_row.get("stage"),
                        venue=match_row.get("stadium"),
                        neutral_venue=neutral,
                    )
                    model_rows[model_name].append(
                        _prediction_to_row(pred, actual_h, actual_a, train_df)
                    )
                except Exception as exc:
                    log.warning("Predict failed %s row %d: %s", model_name, pred_idx, exc)

            # ── baselines ──────────────────────────────────────────────
            if self._include_baselines:
                eq_pred = EqualProbabilityBaseline(self._max_goals).predict(
                    home_team, away_team,
                    match_id=int(match_row.get("match_id", 0)),
                    season=match_row.get("season"),
                    stage=match_row.get("stage"),
                )
                model_rows["equal_probability"].append(
                    _prediction_to_row(eq_pred, actual_h, actual_a, train_df)
                )

                hist_bl = HistoricalBaseRateBaseline(self._max_goals)
                hist_bl.fit(train_df)
                hist_pred = hist_bl.predict(
                    home_team, away_team,
                    match_id=int(match_row.get("match_id", 0)),
                    season=match_row.get("season"),
                )
                model_rows["historical_base_rate"].append(
                    _prediction_to_row(hist_pred, actual_h, actual_a, train_df)
                )

                elo_bl = EloBaseline(max_goals=self._max_goals)
                elo_bl.fit(train_df)
                elo_pred = elo_bl.predict(
                    home_team, away_team,
                    match_id=int(match_row.get("match_id", 0)),
                )
                model_rows["elo"].append(
                    _prediction_to_row(elo_pred, actual_h, actual_a, train_df)
                )

        # ── Compute calibration metrics per model ────────────────────────
        results = []
        all_rows: list[dict] = []

        for model_name, rows in model_rows.items():
            if not rows:
                continue
            preds = [r["_pred_obj"] for r in rows]
            actuals_list = [(r["actual_home"], r["actual_away"]) for r in rows]

            metrics = evaluate_pmf_predictions(preds, actuals_list, model_name)

            # Fit temperature on OOF predictions (must happen after, never on training data)
            if len(preds) >= 10:
                from wc2026.calibration.score_pmf import ScorePMFCalibrator
                cal = ScorePMFCalibrator()
                cal.fit(preds, actuals_list)
                metrics.temperature = cal.temperature

            # Clean rows for serialization
            clean_rows = [{k: v for k, v in r.items() if k != "_pred_obj"} for r in rows]
            for r in clean_rows:
                r["model_name"] = model_name
                r["run_timestamp"] = run_ts

            all_rows.extend(clean_rows)
            per_match_df = pd.DataFrame(clean_rows)

            result = WalkForwardResult(
                run_timestamp=run_ts,
                model_name=model_name,
                season_filter=season_filter,
                n_predictions=len(rows),
                n_train_matches_final=len(df.iloc[:predict_indices[-1]]) if predict_indices else 0,
                metrics=metrics,
                predictions_path=None,
                per_match=per_match_df,
            )
            results.append(result)

        # ── Save predictions ─────────────────────────────────────────────
        if save and all_rows:
            out_path = PREDICTIONS_DIR / "oof_score_pmfs.parquet"
            pd.DataFrame(all_rows).to_parquet(out_path, index=False)
            for r in results:
                r.predictions_path = out_path
            log.info("Saved %d OOF prediction rows → %s", len(all_rows), out_path)

        _log_summary(results)
        return results


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _prediction_to_row(
    pred: ScorePMFPrediction,
    actual_h: int,
    actual_a: int,
    train_df: pd.DataFrame,
) -> dict:
    dm = pred.derived_markets
    actual_outcome = (
        "home_win" if actual_h > actual_a else
        "draw" if actual_h == actual_a else
        "away_win"
    )
    p_exact = pred.exact_score(actual_h, actual_a)
    p_outcome = {
        "home_win": dm.home_win,
        "draw": dm.draw,
        "away_win": dm.away_win,
    }[actual_outcome]

    return {
        "_pred_obj": pred,  # kept in memory, stripped before parquet save
        "match_id": pred.match_id,
        "prediction_timestamp": pred.prediction_timestamp,
        "home_team": pred.home_team,
        "away_team": pred.away_team,
        "season": pred.season,
        "stage": pred.stage,
        "actual_home": actual_h,
        "actual_away": actual_a,
        "actual_outcome": actual_outcome,
        "p_home_win": dm.home_win,
        "p_draw": dm.draw,
        "p_away_win": dm.away_win,
        "p_exact_score": p_exact,
        "p_actual_outcome": p_outcome,
        "exact_score_log_loss": float(-np.log(max(p_exact, 1e-9))),
        "outcome_log_loss": float(-np.log(max(p_outcome, 1e-9))),
        "expected_home_goals": pred.expected_home_goals,
        "expected_away_goals": pred.expected_away_goals,
        "n_train_matches": len(train_df),
        "data_version": pred.data_version,
        "model_version": pred.model_version,
        "feature_version": pred.feature_version,
        "prediction_hash": pred.prediction_hash,
    }


def _log_summary(results: list[WalkForwardResult]) -> None:
    if not results:
        log.info("No walk-forward results.")
        return
    log.info("=" * 60)
    log.info("WALK-FORWARD SUMMARY")
    log.info("%-25s %8s %8s %8s %8s", "model", "n", "RPS", "Brier", "ExactLL")
    log.info("-" * 60)
    for r in sorted(results, key=lambda x: x.metrics.rps_1x2):
        m = r.metrics
        log.info(
            "%-25s %8d %8.4f %8.4f %8.4f",
            r.model_name[:25],
            r.n_predictions,
            m.rps_1x2,
            m.brier_1x2,
            m.exact_score_log_loss,
        )
    log.info("=" * 60)
