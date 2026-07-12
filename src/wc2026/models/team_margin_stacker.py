"""
Team Margin Stacker.

Trains two EGM stacking models:
  A. pure_strength_egm — excludes current-match /odds
  B. market_strength_egm — includes de-vigged current-match market EGM

Uses rolling-origin validation only. No random splits.
Primary target: regulation-time goal difference.
Model choices: Ridge, ElasticNet, HuberRegressor (start simple).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

import numpy as np
import pandas as pd

try:
    from sklearn.linear_model import Ridge
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import StandardScaler
    _HAS_SKLEARN = True
except ImportError:
    _HAS_SKLEARN = False



@dataclass
class StackerFoldMetrics:
    fold: int
    train_size: int
    val_size: int
    pure_goal_diff_mae: float
    market_goal_diff_mae: float
    pure_r2: float
    market_r2: float


@dataclass
class StackerCoefficients:
    feature_names: list[str]
    pure_coefs: list[float]
    pure_intercept: float
    market_coefs: list[float]
    market_intercept: float
    training_cutoff: datetime
    n_training_matches: int
    pure_val_mae: float
    market_val_mae: float
    fold_metrics: list[StackerFoldMetrics] = field(default_factory=list)


class TeamMarginStacker:
    """
    Fits pure_strength_egm and market_strength_egm stackers.

    Input feature matrix rows = (match, team_side).
    Target = regulation-time goal difference from that team's perspective.

    Pure features (no current-match odds):
      - pi_egm
      - elo_egm
      - xg_attack_egm
      - xg_defense_egm
      - player_egm
      - futures_egm
      - venue_egm

    Market features (adds current-match market signal):
      - all pure features
      - market_egm
      - market_total
    """

    PURE_FEATURES = [
        "pi_egm", "elo_egm",
        "xg_attack_egm", "xg_defense_egm",
        "player_egm", "futures_egm", "venue_egm",
    ]
    MARKET_FEATURES = PURE_FEATURES + ["market_egm", "market_total"]

    def __init__(self, alpha: float = 1.0, min_train_matches: int = 10):
        self.alpha = alpha
        self.min_train_matches = min_train_matches
        self._pure_pipeline: object | None = None
        self._market_pipeline: object | None = None
        self.coefs: StackerCoefficients | None = None

    def _build_pipeline(self) -> object:
        if not _HAS_SKLEARN:
            return None
        return Pipeline([
            ("scaler", StandardScaler()),
            ("model", Ridge(alpha=self.alpha, fit_intercept=True)),
        ])

    def fit(
        self,
        features_df: pd.DataFrame,
        n_folds: int = 3,
    ) -> TeamMarginStacker:
        """
        features_df must have columns:
          match_id, datetime, target_gd,
          pi_egm, elo_egm, xg_attack_egm, xg_defense_egm,
          player_egm, futures_egm, venue_egm,
          market_egm, market_total

        Rows are ordered chronologically. Rolling-origin splits by datetime.
        """
        if not _HAS_SKLEARN or features_df.empty:
            return self

        df = features_df.dropna(subset=["target_gd"]).copy()
        df = df.sort_values("datetime").reset_index(drop=True)

        if len(df) < self.min_train_matches:
            return self

        # Rolling-origin CV
        fold_size = len(df) // (n_folds + 1)
        fold_metrics = []

        for fold in range(n_folds):
            train_end = fold_size * (fold + 1)
            val_end = fold_size * (fold + 2)
            if val_end > len(df):
                break
            train = df.iloc[:train_end]
            val = df.iloc[train_end:val_end]

            X_pure_tr = train[self.PURE_FEATURES].fillna(0).values
            X_pure_v = val[self.PURE_FEATURES].fillna(0).values
            X_mkt_tr = train[self.MARKET_FEATURES].fillna(0).values
            X_mkt_v = val[self.MARKET_FEATURES].fillna(0).values
            y_tr = train["target_gd"].values
            y_v = val["target_gd"].values

            p_pipe = self._build_pipeline()
            m_pipe = self._build_pipeline()
            p_pipe.fit(X_pure_tr, y_tr)
            m_pipe.fit(X_mkt_tr, y_tr)

            p_pred = p_pipe.predict(X_pure_v)
            m_pred = m_pipe.predict(X_mkt_v)
            p_mae = float(np.mean(np.abs(p_pred - y_v)))
            m_mae = float(np.mean(np.abs(m_pred - y_v)))

            ss_tot = float(np.sum((y_v - np.mean(y_v)) ** 2))
            p_r2 = 1.0 - float(np.sum((y_v - p_pred) ** 2)) / ss_tot if ss_tot > 0 else 0.0
            m_r2 = 1.0 - float(np.sum((y_v - m_pred) ** 2)) / ss_tot if ss_tot > 0 else 0.0

            fold_metrics.append(StackerFoldMetrics(
                fold=fold, train_size=len(train), val_size=len(val),
                pure_goal_diff_mae=p_mae, market_goal_diff_mae=m_mae,
                pure_r2=p_r2, market_r2=m_r2,
            ))

        # Final fit on all data
        X_pure_all = df[self.PURE_FEATURES].fillna(0).values
        X_mkt_all = df[self.MARKET_FEATURES].fillna(0).values
        y_all = df["target_gd"].values

        self._pure_pipeline = self._build_pipeline()
        self._market_pipeline = self._build_pipeline()
        self._pure_pipeline.fit(X_pure_all, y_all)
        self._market_pipeline.fit(X_mkt_all, y_all)

        p_coefs = list(self._pure_pipeline.named_steps["model"].coef_)
        m_coefs = list(self._market_pipeline.named_steps["model"].coef_)

        avg_p_mae = float(np.mean([f.pure_goal_diff_mae for f in fold_metrics])) if fold_metrics else 999.0
        avg_m_mae = float(np.mean([f.market_goal_diff_mae for f in fold_metrics])) if fold_metrics else 999.0

        self.coefs = StackerCoefficients(
            feature_names=self.PURE_FEATURES,
            pure_coefs=p_coefs,
            pure_intercept=float(self._pure_pipeline.named_steps["model"].intercept_),
            market_coefs=m_coefs,
            market_intercept=float(self._market_pipeline.named_steps["model"].intercept_),
            training_cutoff=datetime.now(timezone.utc),
            n_training_matches=len(df),
            pure_val_mae=avg_p_mae,
            market_val_mae=avg_m_mae,
            fold_metrics=fold_metrics,
        )
        return self

    def predict_pure(self, features: dict) -> float:
        """Predict pure_strength_egm for a single match side."""
        if self._pure_pipeline is None:
            # Fallback: weighted average of available signals
            return (
                features.get("pi_egm", 0.0) * 0.4
                + features.get("elo_egm", 0.0) * 0.2
                + features.get("xg_attack_egm", 0.0) * 0.2
                + features.get("player_egm", 0.0) * 0.1
                + features.get("futures_egm", 0.0) * 0.1
            )
        X = np.array([[features.get(f, 0.0) for f in self.PURE_FEATURES]])
        return float(self._pure_pipeline.predict(X)[0])

    def predict_market(self, features: dict) -> float:
        """Predict market_strength_egm for a single match side."""
        if self._market_pipeline is None:
            return self.predict_pure(features) * 0.7 + features.get("market_egm", 0.0) * 0.3
        X = np.array([[features.get(f, 0.0) for f in self.MARKET_FEATURES]])
        return float(self._market_pipeline.predict(X)[0])
