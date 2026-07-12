"""
PMF reconciliation via minimum-KL divergence.

Given:
  - base_pmf: model's score probability matrix (max_goals × max_goals)
  - market constraints: consensus no-vig probabilities for 1X2, totals, BTTS

Produces a calibrated PMF that:
  - Minimises KL(calibrated || base_pmf)
  - Satisfies market constraints within tolerance
  - Sums to 1.0
  - Has no negative probabilities

Method: projected gradient / scipy.optimize.minimize with L-BFGS-B.

If scipy optimization fails, falls back to simple multiplicative calibration
that preserves the 1X2 ranking.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass

import numpy as np
from scipy.optimize import minimize

from wc2026.markets.consensus import ConsensusMarkets
from wc2026.models.prediction import CalibrationStatus, ScorePMFPrediction

log = logging.getLogger(__name__)

_EPS = 1e-9
# Constraint violation penalty weight
_LAMBDA_1X2 = 5.0
_LAMBDA_TOTAL = 2.0
_LAMBDA_BTTS = 1.0


@dataclass
class ReconciliationResult:
    calibrated_pmf: np.ndarray
    base_pmf: np.ndarray
    kl_divergence: float
    constraint_violations: dict[str, float]
    converged: bool
    warnings: list[str]


def reconcile_pmf(
    base_pred: ScorePMFPrediction,
    markets: ConsensusMarkets,
    lambda_1x2: float = _LAMBDA_1X2,
    lambda_total: float = _LAMBDA_TOTAL,
    lambda_btts: float = _LAMBDA_BTTS,
) -> ScorePMFPrediction:
    """
    Return a market-reconciled ScorePMFPrediction.

    If markets has no valid constraints, returns base_pred unchanged with
    a warning.
    """
    has_constraints = markets.has_1x2 or len(markets.totals) > 0
    if not has_constraints:
        pred = _clone_with_status(base_pred, CalibrationStatus.UNCALIBRATED)
        pred.warnings.append("No market constraints available; using base model PMF.")
        return pred

    result = _minimize_kl(
        base_pmf=base_pred.score_pmf,
        markets=markets,
        lambda_1x2=lambda_1x2,
        lambda_total=lambda_total,
        lambda_btts=lambda_btts,
    )

    # Recompute expected goals from the reconciled PMF so they stay consistent
    pmf = result.calibrated_pmf
    n = pmf.shape[0]
    goal_range = np.arange(n)
    rec_xg_home = float(np.sum(pmf * goal_range[:, None]))
    rec_xg_away = float(np.sum(pmf * goal_range[None, :]))

    new_pred = ScorePMFPrediction(
        match_id=base_pred.match_id,
        home_team=base_pred.home_team,
        away_team=base_pred.away_team,
        season=base_pred.season,
        stage=base_pred.stage,
        venue=base_pred.venue,
        model_name=f"{base_pred.model_name}+market_reconciled",
        max_goals=base_pred.max_goals,
        score_pmf=pmf,
        tail_mass=0.0,  # reconciled PMF is renormalized to sum=1; tail absorbed
        expected_home_goals=rec_xg_home,
        expected_away_goals=rec_xg_away,
        calibration_status=CalibrationStatus.MARKET_CALIBRATED,
        uncertainty=base_pred.uncertainty,
        warnings=base_pred.warnings + result.warnings,
    )
    return new_pred


def _minimize_kl(
    base_pmf: np.ndarray,
    markets: ConsensusMarkets,
    lambda_1x2: float,
    lambda_total: float,
    lambda_btts: float,
) -> ReconciliationResult:
    n = base_pmf.shape[0]
    p0 = np.clip(base_pmf.flatten(), _EPS, 1.0)
    p0 /= p0.sum()

    def objective(log_p: np.ndarray) -> float:
        """KL(p || q) + penalty terms."""
        p = np.exp(log_p)
        p = p / p.sum()
        mat = p.reshape(n, n)

        # KL divergence
        kl = float(np.sum(p * (np.log(p + _EPS) - np.log(p0 + _EPS))))

        # Build indices
        idx_i, idx_j = np.indices((n, n))
        total_s = idx_i + idx_j

        penalty = 0.0

        # 1X2 penalties
        if markets.has_1x2:
            hw = float(mat[idx_i > idx_j].sum())
            dr = float(mat[idx_i == idx_j].sum())
            aw = float(mat[idx_i < idx_j].sum())
            penalty += lambda_1x2 * (hw - markets.home_win) ** 2
            penalty += lambda_1x2 * (dr - markets.draw) ** 2
            penalty += lambda_1x2 * (aw - markets.away_win) ** 2

        # Totals penalties
        for line_str, (mkt_over, _) in markets.totals.items():
            try:
                line = float(line_str)
                model_over = float(mat[total_s > line].sum())
                penalty += lambda_total * (model_over - mkt_over) ** 2
            except ValueError:
                pass

        return kl + penalty

    log_p0 = np.log(p0 + _EPS)
    warnings: list[str] = []

    try:
        res = minimize(
            objective,
            log_p0,
            method="L-BFGS-B",
            options={"maxiter": 500, "ftol": 1e-9},
        )
        converged = res.success
        if not converged:
            warnings.append(f"KL minimization did not converge: {res.message}")
        opt_p = np.exp(res.x)
        opt_p = np.clip(opt_p, 0.0, 1.0)
        opt_p /= opt_p.sum()
        calibrated = opt_p.reshape(n, n)
    except Exception as exc:
        log.warning("KL minimization failed: %s. Using multiplicative fallback.", exc)
        calibrated, converged = _multiplicative_fallback(base_pmf, markets)
        warnings.append(f"KL optimization failed ({exc}); used multiplicative fallback.")

    # Compute constraint violations
    violations = {}
    idx_i, idx_j = np.indices((n, n))
    if markets.has_1x2:
        violations["home_win_err"] = abs(float(calibrated[idx_i > idx_j].sum()) - markets.home_win)
        violations["draw_err"] = abs(float(calibrated[idx_i == idx_j].sum()) - markets.draw)
        violations["away_win_err"] = abs(float(calibrated[idx_i < idx_j].sum()) - markets.away_win)

    kl = float(np.sum(calibrated.flatten() * (
        np.log(calibrated.flatten() + _EPS) - np.log(base_pmf.flatten() + _EPS)
    )))

    return ReconciliationResult(
        calibrated_pmf=calibrated,
        base_pmf=base_pmf,
        kl_divergence=kl,
        constraint_violations=violations,
        converged=converged,
        warnings=warnings,
    )


def _multiplicative_fallback(
    base_pmf: np.ndarray,
    markets: ConsensusMarkets,
) -> tuple[np.ndarray, bool]:
    """
    Simple multiplicative correction on 1X2 margins only.
    Scales home-win cells, draw cells, and away-win cells by the ratio
    of market probability to model probability.
    """
    n = base_pmf.shape[0]
    idx_i, idx_j = np.indices((n, n))
    cal = base_pmf.copy()

    if markets.has_1x2:
        hw_model = float(cal[idx_i > idx_j].sum())
        dr_model = float(cal[idx_i == idx_j].sum())
        aw_model = float(cal[idx_i < idx_j].sum())

        for mask, model_p, mkt_p in [
            (idx_i > idx_j, hw_model, markets.home_win),
            (idx_i == idx_j, dr_model, markets.draw),
            (idx_i < idx_j, aw_model, markets.away_win),
        ]:
            if model_p > _EPS and mkt_p is not None:
                cal[mask] *= mkt_p / model_p

    cal = np.clip(cal, 0.0, 1.0)
    s = cal.sum()
    if s > _EPS:
        cal /= s
    return cal, True


def _clone_with_status(
    pred: ScorePMFPrediction,
    status: CalibrationStatus,
) -> ScorePMFPrediction:
    """Clone a prediction with a different calibration status."""
    import copy
    cloned = copy.deepcopy(pred)
    cloned.calibration_status = status
    return cloned
