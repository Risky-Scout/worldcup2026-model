"""Closing-line forecaster: predict where the market will close from pre-match structural features."""
from __future__ import annotations
import logging
from dataclasses import dataclass, field
from typing import Optional

import numpy as np
import pandas as pd

log = logging.getLogger(__name__)

_FEATURE_COLS = [
    "structural_log_home_lambda_minus_market",
    "structural_log_away_lambda_minus_market",
    "structural_total_minus_market",
    "structural_goal_diff_minus_market",
    "vendor_count",
    "market_quality",
    "horizon_seconds",
    "host_team_indicator",
    "neutral_venue",
]

_TARGET_COLS = [
    "target_log_home_lambda_move",
    "target_log_away_lambda_move",
    "target_rho_move",
]


class InsufficientDataError(ValueError):
    pass


@dataclass
class FoldMetrics:
    fold: int
    n_train: int
    n_test: int
    mae_log_home: float
    mae_log_away: float
    mae_rho: float
    direction_accuracy_home: float
    direction_accuracy_away: float


@dataclass
class ClosePrediction:
    predicted_close_home_lambda: float
    predicted_close_away_lambda: float
    predicted_close_rho: float
    predicted_close_pmf: Optional[np.ndarray]
    uncertainty_home: float
    uncertainty_away: float
    feature_coefficients: dict


class ClosingLineForecaster:
    def __init__(self, model_type: str = "ridge"):
        self.model_type = model_type
        self._models = {}
        self._residual_std = {}
        self._is_fitted = False
        self._feature_cols = []

    def _make_model(self):
        try:
            from sklearn.linear_model import Ridge, HuberRegressor, ElasticNet
        except ImportError:
            raise ImportError("scikit-learn required. Run: pip install scikit-learn>=1.4")

        if self.model_type == "ridge":
            return Ridge(alpha=1.0)
        elif self.model_type == "huber":
            return HuberRegressor(epsilon=1.35, max_iter=200)
        elif self.model_type == "elasticnet":
            return ElasticNet(alpha=0.1, l1_ratio=0.5)
        else:
            return Ridge(alpha=1.0)

    def fit(self, dataset: pd.DataFrame, n_folds: int = 5) -> list[FoldMetrics]:
        """Fit using rolling-origin validation. Returns per-fold metrics."""
        if dataset is None or len(dataset) < 2:
            raise InsufficientDataError(f"Need at least 2 rows, got {len(dataset) if dataset is not None else 0}")

        # Sort by prediction_timestamp for temporal ordering
        if "prediction_timestamp" in dataset.columns:
            dataset = dataset.sort_values("prediction_timestamp").reset_index(drop=True)

        # Select available feature columns
        available_features = [c for c in _FEATURE_COLS if c in dataset.columns]
        if not available_features:
            raise InsufficientDataError("No feature columns found in dataset")

        available_targets = [c for c in _TARGET_COLS if c in dataset.columns]
        if not available_targets:
            raise InsufficientDataError("No target columns found in dataset")

        X = dataset[available_features].fillna(0).values
        fold_metrics = []
        n = len(dataset)
        fold_size = max(1, n // (n_folds + 1))

        for fold_idx in range(min(n_folds, n - 1)):
            cutoff = (fold_idx + 1) * fold_size
            if cutoff >= n:
                break
            X_train, X_test = X[:cutoff], X[cutoff:min(cutoff + fold_size, n)]
            if len(X_train) < 1 or len(X_test) < 1:
                continue

            fold_models = {}
            for target in available_targets:
                y_train = dataset[target].iloc[:cutoff].fillna(0).values
                model = self._make_model()
                model.fit(X_train, y_train)
                fold_models[target] = model

            n_test = len(X_test)

            y_pred_h = fold_models["target_log_home_lambda_move"].predict(X_test) if "target_log_home_lambda_move" in fold_models else np.zeros(n_test)
            y_pred_a = fold_models["target_log_away_lambda_move"].predict(X_test) if "target_log_away_lambda_move" in fold_models else np.zeros(n_test)
            y_pred_rho = fold_models["target_rho_move"].predict(X_test) if "target_rho_move" in fold_models else np.zeros(n_test)

            slice_end = min(cutoff + fold_size, n)
            y_true_h = dataset["target_log_home_lambda_move"].iloc[cutoff:slice_end].fillna(0).values if "target_log_home_lambda_move" in dataset else np.zeros(n_test)
            y_true_a = dataset["target_log_away_lambda_move"].iloc[cutoff:slice_end].fillna(0).values if "target_log_away_lambda_move" in dataset else np.zeros(n_test)
            y_true_rho = dataset["target_rho_move"].iloc[cutoff:slice_end].fillna(0).values if "target_rho_move" in dataset else np.zeros(n_test)

            fold_metrics.append(FoldMetrics(
                fold=fold_idx,
                n_train=cutoff,
                n_test=n_test,
                mae_log_home=float(np.mean(np.abs(y_pred_h[:n_test] - y_true_h[:n_test]))),
                mae_log_away=float(np.mean(np.abs(y_pred_a[:n_test] - y_true_a[:n_test]))),
                mae_rho=float(np.mean(np.abs(y_pred_rho[:n_test] - y_true_rho[:n_test]))),
                direction_accuracy_home=float(np.mean(np.sign(y_pred_h[:n_test]) == np.sign(y_true_h[:n_test]))),
                direction_accuracy_away=float(np.mean(np.sign(y_pred_a[:n_test]) == np.sign(y_true_a[:n_test]))),
            ))

        # Fit final models on all data
        for target in available_targets:
            y_all = dataset[target].fillna(0).values
            model = self._make_model()
            model.fit(X, y_all)
            self._models[target] = model
            residuals = y_all - model.predict(X)
            self._residual_std[target] = float(np.std(residuals))

        self._feature_cols = available_features
        self._is_fitted = True
        return fold_metrics

    def predict(self, features: pd.DataFrame) -> ClosePrediction:
        if not self._is_fitted:
            raise RuntimeError("Model not fitted. Call fit() first.")

        available = [c for c in self._feature_cols if c in features.columns]
        X = features[available].fillna(0).values[:1]

        pred_log_h = float(self._models["target_log_home_lambda_move"].predict(X)[0]) if "target_log_home_lambda_move" in self._models else 0.0
        pred_log_a = float(self._models["target_log_away_lambda_move"].predict(X)[0]) if "target_log_away_lambda_move" in self._models else 0.0
        pred_rho_move = float(self._models["target_rho_move"].predict(X)[0]) if "target_rho_move" in self._models else 0.0

        curr_lh = float(features.get("current_market_home_lambda", pd.Series([1.3])).iloc[0])
        curr_la = float(features.get("current_market_away_lambda", pd.Series([1.0])).iloc[0])
        curr_rho = float(features.get("current_market_rho", pd.Series([-0.05])).iloc[0])

        pred_lh = curr_lh * np.exp(pred_log_h)
        pred_la = curr_la * np.exp(pred_log_a)
        pred_rho = float(np.clip(curr_rho + pred_rho_move, -0.5, 0.0))

        # Build predicted close PMF
        predicted_pmf = None
        try:
            from penaltyblog.models import create_dixon_coles_grid
            grid = create_dixon_coles_grid(pred_lh, pred_la, rho=pred_rho, max_goals=14)
            predicted_pmf = np.array(grid.grid, dtype=np.float64)
            predicted_pmf = predicted_pmf / predicted_pmf.sum()
        except Exception:
            pass

        # Feature coefficients
        coefficients = {}
        for target, model in self._models.items():
            if hasattr(model, "coef_"):
                for feat, coef in zip(self._feature_cols, model.coef_):
                    coefficients[f"{target}/{feat}"] = float(coef)

        return ClosePrediction(
            predicted_close_home_lambda=float(pred_lh),
            predicted_close_away_lambda=float(pred_la),
            predicted_close_rho=pred_rho,
            predicted_close_pmf=predicted_pmf,
            uncertainty_home=self._residual_std.get("target_log_home_lambda_move", 0.1),
            uncertainty_away=self._residual_std.get("target_log_away_lambda_move", 0.1),
            feature_coefficients=coefficients,
        )
