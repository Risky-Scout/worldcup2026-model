"""
CoreGridSLSQPReconciler — controlled SLSQP on an 8×8 core grid.

The previous SLSQP failure was a 15×15 (225-variable) optimization with hard
equality constraints against a prior that already satisfied them.  That is a
degenerate problem SLSQP cannot solve reliably.

This module fixes both failure modes:

1. **Small core grid (8×8 = 64 variables)**: far fewer degrees of freedom.
   h ∈ {0..7}, a ∈ {0..7} covers 99.99%+ of soccer-match probability.

2. **Soft penalties, not hard equality constraints**: market probabilities
   enter as squared-error terms in the objective, not as SLSQP equalities.
   The only hard constraint is sum(core) = 1 − tail_mass.  This avoids
   over-constrained systems that produce degenerate corner solutions.

3. **Strict prior-derived upper bounds**: each cell p[h,a] has an upper bound
   of max(prior[h,a] × multiplier, abs_cap[h+a]).  For total_goals ≥ 7,
   abs_cap drops steeply, preventing SLSQP from depositing mass in 4-9/11-5.

4. **Explicit tail model**: scores outside 8×8 come from the market_implied
   parametric PMF (scaled), are never freely optimized, and are tracked with
   exact tail_mass.

Reconciliation modes
--------------------
market_implied              goal_expectancy_extended → Poisson PMF
market_reconciled_blend     α*market_implied + (1-α)*composite  + gentle IPF
market_reconciled_slsqp     8×8 core-grid SLSQP with soft penalties
market_reconciled_best      winner of method_comparison validation

Objective
---------
L = w_kl   × KL(p_core || q_core)
  + w_1x2  × Σ (P_1x2 − target)²
  + w_ou   × Σ_k (P_over_k − target_k)²
  + w_btts × (P_btts − target_btts)²
  + w_cs   × Σ_{h,a in core} (p[h,a] − cs_target[h,a])² × cs_weight
  + w_smooth × Σ_adjacent |p[h,a] − p[h',a']|²
  + w_high × Σ_{total≥7} p[h,a]

Hard constraints
----------------
- Σ p[h,a] = 1 − tail_mass   (single equality, well-conditioned)
- bounds: 1e-12 ≤ p[h,a] ≤ cap[h,a]
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Optional

import numpy as np
from scipy.optimize import minimize
from scipy.stats import poisson

log = logging.getLogger(__name__)

_EPS = 1e-12

# ── Per-cell total-goals upper bounds ────────────────────────────────────────
# These are ABSOLUTE caps regardless of the prior.
# total_goals 0-4: no meaningful restriction (normal soccer scores)
# total_goals 5:   3-2, 4-1 — rare but real
# total_goals 6:   4-2, 3-3 — very rare
# total_goals 7:   4-3, 5-2 — once-in-a-generation level in WC
# total_goals 8+:  essentially impossible in WC context
_ABS_CAP_BY_TOTAL: dict[int, float] = {
    0:  0.50,
    1:  0.38,
    2:  0.38,
    3:  0.28,
    4:  0.22,
    5:  0.08,
    6:  0.022,
    7:  0.005,
    8:  0.0008,
    9:  0.0001,
    10: 0.00002,
    11: 0.000004,
    12: 0.0000008,
    13: 0.00000015,
    14: 0.00000003,
}

# Prior multiplier: cell upper bound = max(prior * MULTIPLIER, abs_cap)
_PRIOR_MULTIPLIER = 5.0

# Weight defaults
_DEFAULT_WEIGHTS = {
    "kl": 1.0,          # KL from prior
    "1x2": 25.0,        # 6-vendor 1X2 (most reliable)
    "ou": 18.0,         # O/U lines (one per line)
    "btts": 12.0,       # BTTS
    "cs_1v": 4.0,       # 1-vendor correct-score (low confidence)
    "cs_mv": 14.0,      # 2+-vendor correct-score
    "smooth": 0.3,      # adjacent-cell smoothness
    "high7": 30.0,      # penalty for total_goals == 7 mass
    "high8": 200.0,     # penalty for total_goals 8-14 within core
}


@dataclass
class CoreGridResult:
    """Output of a single CoreGridSLSQPReconciler.reconcile() call."""
    core_pmf: np.ndarray          # 8×8 core grid (sums to 1 - tail_mass)
    full_pmf: np.ndarray          # max_goals × max_goals full grid
    tail_mass_exact: float
    tail_policy: str
    tail_event_buckets: dict
    converged: bool
    optimizer_message: str
    optimizer_fun: float          # final objective value
    method: str                   # "slsqp_core" | "blend" | "fallback"
    constraint_errors: dict       # market constraint absolute errors
    plausibility_pass: bool

    @property
    def top_scores(self) -> list[dict]:
        n = self.full_pmf.shape[0]
        cells = [
            {"home_goals": h, "away_goals": a, "probability": float(self.full_pmf[h, a])}
            for h in range(n) for a in range(n)
        ]
        return sorted(cells, key=lambda x: -x["probability"])[:25]

    def validate(self) -> list[str]:
        """Return list of validation errors (empty = pass)."""
        errs = []
        n = self.full_pmf.shape[0]

        # Sum check
        s = float(self.full_pmf.sum())
        if abs(s - 1.0) > 1e-5:
            errs.append(f"full_pmf sum = {s:.8f}")

        # High-score guard
        for h in range(n):
            for a in range(n):
                if h + a >= 9 and self.full_pmf[h, a] > 1e-4:
                    errs.append(f"impossible score [{h},{a}] P={self.full_pmf[h,a]:.5f}")

        # Top-3 must be plausible
        top = self.top_scores[:3]
        for s_dict in top:
            if s_dict["home_goals"] + s_dict["away_goals"] > 6:
                errs.append(
                    f"implausible top-3 score "
                    f"{s_dict['home_goals']}-{s_dict['away_goals']} "
                    f"P={s_dict['probability']:.4f}"
                )

        # Non-negative
        if float(self.full_pmf.min()) < -1e-10:
            errs.append("full_pmf has negative cells")

        return errs


class CoreGridSLSQPReconciler:
    """
    Controlled SLSQP reconciler on an 8×8 core PMF grid.

    Usage
    -----
    rec = CoreGridSLSQPReconciler()
    result = rec.reconcile(prior_pmf, mc, max_goals=15)
    """

    CORE_N = 8   # 8×8 = 64 optimized variables

    def __init__(self, weights: Optional[dict] = None):
        self.weights = {**_DEFAULT_WEIGHTS, **(weights or {})}

    def reconcile(
        self,
        prior_pmf: np.ndarray,
        mc,                     # MarketConstraints
        max_goals: int = 15,
        cs_n_vendors: int = 0,
    ) -> CoreGridResult:
        """
        Reconcile a prior PMF against market constraints using 8×8 core SLSQP.

        Parameters
        ----------
        prior_pmf       n×n array (composite_rating or market_implied PMF)
        mc              MarketConstraints object from BDL no-vig extraction
        max_goals       output grid size (default 15)
        cs_n_vendors    number of correct-score vendors (affects CS weight)
        """
        n_full = max(max_goals, prior_pmf.shape[0])
        N = self.CORE_N

        # Resize / pad prior to full size
        q_full = _resize_pmf(prior_pmf, n_full)
        q_full = np.clip(q_full, _EPS, None)
        q_full /= q_full.sum()

        # Split into core and tail
        q_core = q_full[:N, :N].copy()
        tail_mass_prior = float(1.0 - q_core.sum())
        tail_mass_prior = max(tail_mass_prior, 0.0)

        # Tail distribution: keep parametric tail from the prior
        tail_pmf = _extract_tail(q_full, N)          # n_full × n_full, zero in core
        tail_event_buckets = _compute_tail_buckets(tail_pmf)

        # Target core sum: 1 - tail_mass (keep tail fixed)
        target_core_sum = max(1.0 - tail_mass_prior, 0.9999)

        # Normalize core prior to sum to target_core_sum
        q_core_norm = q_core / q_core.sum() * target_core_sum
        q_flat = q_core_norm.flatten()   # 64 variables

        # Build per-cell bounds
        bounds = _build_bounds(q_core_norm, N)

        # Build index maps for fast constraint evaluation
        h_idx = np.array([i // N for i in range(N * N)], dtype=int)
        a_idx = np.array([i % N for i in range(N * N)], dtype=int)
        total_idx = h_idx + a_idx

        # Build objective function (KL + soft market penalties)
        objective, grad = self._build_objective(
            q_flat, mc, h_idx, a_idx, total_idx, N, cs_n_vendors
        )

        # Single hard equality: sum(core) = target_core_sum
        constraints = [
            {
                "type": "eq",
                "fun": lambda p: p.sum() - target_core_sum,
                "jac": lambda p: np.ones(N * N),
            }
        ]

        try:
            result = minimize(
                objective,
                x0=q_flat.copy(),
                jac=grad,
                method="SLSQP",
                bounds=bounds,
                constraints=constraints,
                options={
                    "maxiter": 1200,
                    "ftol": 1e-7,
                    "eps": 1e-8,
                },
            )
            converged = result.success
            opt_msg = result.message
            opt_fun = float(result.fun)
            p_opt = np.clip(result.x, 0, None).reshape(N, N)
        except Exception as exc:
            log.warning("CoreGridSLSQP failed: %s", exc)
            p_opt = q_core_norm.copy()
            converged = False
            opt_msg = f"exception: {exc}"
            opt_fun = float("inf")

        # Renormalize core
        p_opt = np.clip(p_opt, 0, None)
        cs = p_opt.sum()
        if cs > _EPS:
            p_opt *= (target_core_sum / cs)

        # Sanity guard on core
        p_opt = _sanitize_core(p_opt, N)

        # Recombine core + tail into full PMF
        full_pmf = tail_pmf.copy()
        full_pmf[:N, :N] = p_opt
        full_pmf = np.clip(full_pmf, 0, None)
        full_pmf /= full_pmf.sum()

        # Compute market constraint errors
        constraint_errors = _compute_constraint_errors(full_pmf, mc)

        # Validation
        core_result = CoreGridResult(
            core_pmf=p_opt,
            full_pmf=full_pmf,
            tail_mass_exact=float(tail_mass_prior),
            tail_policy="parametric tail from market_implied prior, not optimized",
            tail_event_buckets=tail_event_buckets,
            converged=converged,
            optimizer_message=opt_msg,
            optimizer_fun=opt_fun,
            method="slsqp_core_8x8",
            constraint_errors=constraint_errors,
            plausibility_pass=False,
        )
        core_result.plausibility_pass = len(core_result.validate()) == 0
        if not converged:
            log.warning(
                "CoreGridSLSQP did not fully converge (message: %s). "
                "Result still used if plausibility_pass=True.",
                opt_msg,
            )
        return core_result

    def _build_objective(
        self,
        q_flat: np.ndarray,
        mc,
        h_idx: np.ndarray,
        a_idx: np.ndarray,
        total_idx: np.ndarray,
        N: int,
        cs_n_vendors: int,
    ):
        """
        Build objective function and gradient.

        Returns (fun, jac) callables for scipy.optimize.minimize.
        """
        w = self.weights
        q_safe = np.clip(q_flat, _EPS, None)

        # Precompute masks
        hw_mask = (h_idx > a_idx).astype(float)
        dr_mask = (h_idx == a_idx).astype(float)
        aw_mask = (h_idx < a_idx).astype(float)

        ou_masks = {}
        ou_targets = {}
        for line, attr in [
            (0.5, "over_0_5"), (1.5, "over_1_5"), (2.5, "over_2_5"),
            (3.5, "over_3_5"), (4.5, "over_4_5"), (5.5, "over_5_5"), (6.5, "over_6_5"),
        ]:
            v = getattr(mc, attr, None)
            if v is not None:
                ou_masks[attr] = (total_idx > line).astype(float)
                ou_targets[attr] = float(v)

        btts_mask = ((h_idx > 0) & (a_idx > 0)).astype(float)

        # Correct-score targets inside 8×8 core
        cs_cells: list[tuple[int, int, float]] = []
        cs_weight = w["cs_mv"] if cs_n_vendors >= 2 else w["cs_1v"]
        if hasattr(mc, "correct_score") and mc.correct_score:
            for (h, a), prob in mc.correct_score.items():
                if h < N and a < N and prob > 0.0005:
                    cs_cells.append((h, a, float(prob), h * N + a))

        # High-score penalty masks
        high7_mask = (total_idx == 7).astype(float)
        high8plus_mask = (total_idx >= 8).astype(float)

        # Smoothness: penalize |p[h+1,a] - p[h,a]|^2 + |p[h,a+1] - p[h,a]|^2
        smooth_pairs_h = []
        smooth_pairs_a = []
        for h in range(N - 1):
            for a in range(N):
                smooth_pairs_h.append((h * N + a, (h + 1) * N + a))
        for h in range(N):
            for a in range(N - 1):
                smooth_pairs_a.append((h * N + a, h * N + (a + 1)))
        smooth_pairs = smooth_pairs_h + smooth_pairs_a

        def objective(p: np.ndarray) -> float:
            p_safe = np.clip(p, _EPS, None)
            loss = 0.0

            # 1. KL divergence
            loss += w["kl"] * float(np.sum(p_safe * np.log(p_safe / q_safe)))

            # 2. 1X2 soft penalties
            if mc.has_1x2 and mc.home_win is not None:
                p_hw = float((p * hw_mask).sum())
                p_dr = float((p * dr_mask).sum())
                p_aw = float((p * aw_mask).sum())
                loss += w["1x2"] * ((p_hw - mc.home_win) ** 2 +
                                    (p_dr - mc.draw) ** 2 +
                                    (p_aw - mc.away_win) ** 2)

            # 3. O/U soft penalties
            for attr, mask in ou_masks.items():
                p_ou = float((p * mask).sum())
                loss += w["ou"] * (p_ou - ou_targets[attr]) ** 2

            # 4. BTTS soft penalty
            if mc.btts_yes is not None:
                p_btts = float((p * btts_mask).sum())
                loss += w["btts"] * (p_btts - mc.btts_yes) ** 2

            # 5. Correct-score soft penalties
            for h, a, target, idx in cs_cells:
                loss += cs_weight * (p[idx] - target) ** 2

            # 6. Smoothness penalty
            for i, j in smooth_pairs:
                diff = p[i] - p[j]
                loss += w["smooth"] * diff * diff

            # 7. High-score penalties
            loss += w["high7"] * float((p * high7_mask).sum())
            loss += w["high8plus"] * float((p * high8plus_mask).sum()) if "high8plus" in w else 0.0
            loss += w["high8"] * float((p * high8plus_mask).sum())

            return loss

        def gradient(p: np.ndarray) -> np.ndarray:
            p_safe = np.clip(p, _EPS, None)
            g = np.zeros_like(p)

            # 1. KL gradient: d/dp_i [p_i * log(p_i/q_i)] = log(p_i/q_i) + 1
            g += w["kl"] * (np.log(p_safe / q_safe) + 1.0)

            # 2. 1X2 gradients
            if mc.has_1x2 and mc.home_win is not None:
                p_hw = float((p * hw_mask).sum())
                p_dr = float((p * dr_mask).sum())
                p_aw = float((p * aw_mask).sum())
                g += 2 * w["1x2"] * ((p_hw - mc.home_win) * hw_mask +
                                      (p_dr - mc.draw) * dr_mask +
                                      (p_aw - mc.away_win) * aw_mask)

            # 3. O/U gradients
            for attr, mask in ou_masks.items():
                p_ou = float((p * mask).sum())
                g += 2 * w["ou"] * (p_ou - ou_targets[attr]) * mask

            # 4. BTTS gradient
            if mc.btts_yes is not None:
                p_btts = float((p * btts_mask).sum())
                g += 2 * w["btts"] * (p_btts - mc.btts_yes) * btts_mask

            # 5. CS gradients
            for h, a, target, idx in cs_cells:
                g[idx] += 2 * cs_weight * (p[idx] - target)

            # 6. Smoothness gradient
            for i, j in smooth_pairs:
                diff = p[i] - p[j]
                g[i] += 2 * w["smooth"] * diff
                g[j] -= 2 * w["smooth"] * diff

            # 7. High-score penalties
            g += w["high7"] * high7_mask
            g += w["high8"] * high8plus_mask

            return g

        return objective, gradient


# ── Module-level comparison function ─────────────────────────────────────────

def compare_reconciliation_methods(
    prior_pmf: np.ndarray,
    mc,
    max_goals: int = 15,
    blend_alpha: float = 0.80,
    cs_n_vendors: int = 0,
) -> dict:
    """
    Run all three reconciliation methods and return comparison dict.

    Returns
    -------
    {
        "market_implied": CoreGridResult or None,
        "blend": CoreGridResult,
        "slsqp_core": CoreGridResult,
        "best_method": str,
        "best_pmf": np.ndarray,
        "method_scores": {method: validation_loss},
    }
    """
    from .exact_score_reconcile import (
        build_market_implied_pmf, apply_correct_score_adjustment,
        _sanitize_pmf,
    )

    n = max(max_goals, prior_pmf.shape[0])
    results: dict[str, Optional[CoreGridResult]] = {}

    # ── Method 1: market_implied ──────────────────────────────────────────
    mip = prior_pmf  # fallback
    mip_lh, mip_la = 1.3, 1.0
    if mc.has_1x2:
        try:
            mip_raw, mip_lh, mip_la, _ = build_market_implied_pmf(mc, max_goals=n)
            mip = mip_raw
            results["market_implied"] = _pmf_to_result(mip, mc, "market_implied")
        except Exception as exc:
            log.warning("market_implied PMF failed: %s", exc)
            results["market_implied"] = None
    else:
        results["market_implied"] = None

    # ── Method 2: blend ───────────────────────────────────────────────────
    alpha = min(blend_alpha, 0.85)
    p = prior_pmf[:n, :n].copy()
    m = mip[:n, :n].copy()
    p = np.clip(p, 0, None); p /= p.sum()
    m = np.clip(m, 0, None); m /= m.sum()
    blend = alpha * m + (1.0 - alpha) * p
    blend /= blend.sum()
    if mc.has_correct_score and mc.n_cs_outcomes >= 3:
        cs_a = 0.30 if cs_n_vendors <= 1 else 0.50
        blend = apply_correct_score_adjustment(blend, mc.correct_score, alpha=cs_a)
    blend = _sanitize_pmf(blend)
    results["blend"] = _pmf_to_result(blend, mc, "market_reconciled_blend")

    # ── Method 3: SLSQP core-grid ─────────────────────────────────────────
    # Sanitize market-implied PMF before passing to SLSQP: the DC fit for
    # high-lambda matches produces tail cells at [8+, *] that exceed the
    # validate() threshold (1e-4), disqualifying SLSQP unnecessarily.
    # Sanitizing the input ensures the SLSQP inherits a clean tail and can
    # compete against the blend on equal footing.
    _slsqp_input = _sanitize_pmf(mip if mc.has_1x2 else prior_pmf)
    rec = CoreGridSLSQPReconciler()
    slsqp_result = rec.reconcile(_slsqp_input, mc,
                                  max_goals=n, cs_n_vendors=cs_n_vendors)
    results["slsqp_core"] = slsqp_result

    # ── Select best method ────────────────────────────────────────────────
    method_scores: dict[str, float] = {}
    for name, r in results.items():
        if r is None:
            method_scores[name] = float("inf")
            continue
        errs = r.validate()
        if errs:
            method_scores[name] = float("inf")  # disqualify if artifacts
        else:
            method_scores[name] = _validation_loss(r.full_pmf, mc)

    best_method = min(method_scores, key=method_scores.get)

    # Fallback: if SLSQP wins but didn't converge cleanly, prefer blend
    if best_method == "slsqp_core" and not slsqp_result.converged:
        blend_score = method_scores.get("blend", float("inf"))
        slsqp_score = method_scores["slsqp_core"]
        if slsqp_score > blend_score * 0.95:  # SLSQP not meaningfully better
            best_method = "blend"

    best_pmf = results[best_method].full_pmf if results[best_method] else blend

    return {
        "market_implied": results.get("market_implied"),
        "blend": results["blend"],
        "slsqp_core": results["slsqp_core"],
        "best_method": best_method,
        "best_pmf": best_pmf,
        "method_scores": method_scores,
    }


# ── Private helpers ───────────────────────────────────────────────────────────

def _resize_pmf(pmf: np.ndarray, n: int) -> np.ndarray:
    """Resize PMF to n×n, padding with tiny values if needed."""
    cur = pmf.shape[0]
    if cur == n:
        return pmf.copy()
    out = np.full((n, n), _EPS)
    mn = min(cur, n)
    out[:mn, :mn] = pmf[:mn, :mn]
    out = np.clip(out, 0, None)
    s = out.sum()
    if s > _EPS:
        out /= s
    return out


def _extract_tail(full_pmf: np.ndarray, core_n: int) -> np.ndarray:
    """Return full_pmf with core zeroed out (tail only)."""
    tail = full_pmf.copy()
    tail[:core_n, :core_n] = 0.0
    return tail


def _compute_tail_buckets(tail_pmf: np.ndarray) -> dict:
    """Compute tail event buckets for JSON output."""
    n = tail_pmf.shape[0]
    N = 8  # core size
    hw_tail = sum(tail_pmf[h, a] for h in range(n) for a in range(n) if h > a and (h >= N or a >= N))
    dr_tail = sum(tail_pmf[h, a] for h in range(n) for a in range(n) if h == a and (h >= N or a >= N))
    aw_tail = sum(tail_pmf[h, a] for h in range(n) for a in range(n) if h < a and (h >= N or a >= N))
    return {
        "home_8plus_away_0_7": float(sum(tail_pmf[h, a] for h in range(N, n) for a in range(N))),
        "home_0_7_away_8plus": float(sum(tail_pmf[h, a] for h in range(N) for a in range(N, n))),
        "both_8plus": float(sum(tail_pmf[h, a] for h in range(N, n) for a in range(N, n))),
        "other_home_win": float(hw_tail),
        "other_draw": float(dr_tail),
        "other_away_win": float(aw_tail),
    }


def _build_bounds(q_core: np.ndarray, N: int):
    """Build per-cell SLSQP bounds based on prior and absolute caps."""
    bounds = []
    for h in range(N):
        for a in range(N):
            total = h + a
            abs_cap = _ABS_CAP_BY_TOTAL.get(total, 1e-8)
            prior_cap = float(q_core[h, a]) * _PRIOR_MULTIPLIER
            if total >= 8:
                # Hard cap for very high totals — prior cannot override
                upper = abs_cap
            elif total >= 6:
                # Soft cap: prior can raise slightly above abs_cap but not 3×
                upper = min(max(abs_cap, prior_cap), abs_cap * 2)
            else:
                upper = max(abs_cap, prior_cap)
            bounds.append((_EPS, upper))
    return bounds


def _sanitize_core(core: np.ndarray, N: int) -> np.ndarray:
    """Apply absolute caps to core cells and renormalize."""
    for h in range(N):
        for a in range(N):
            total = h + a
            cap = _ABS_CAP_BY_TOTAL.get(total, 1e-8)
            if core[h, a] > cap:
                core[h, a] = cap
    core = np.clip(core, 0, None)
    s = core.sum()
    if s > _EPS:
        core /= s / (s if s < 1.0 else 1.0)  # don't normalize if already OK
    return core


def _pmf_to_result(pmf: np.ndarray, mc, method: str) -> CoreGridResult:
    """Wrap a plain PMF array in a CoreGridResult for comparison."""
    N = CoreGridSLSQPReconciler.CORE_N
    n = pmf.shape[0]
    tail_mass = float(max(0.0, 1.0 - pmf[:N, :N].sum()))
    tail_pmf = _extract_tail(pmf, N)
    cr = CoreGridResult(
        core_pmf=pmf[:N, :N].copy(),
        full_pmf=pmf.copy(),
        tail_mass_exact=tail_mass,
        tail_policy="parametric (Poisson-based market_implied)",
        tail_event_buckets=_compute_tail_buckets(tail_pmf),
        converged=True,
        optimizer_message="n/a",
        optimizer_fun=0.0,
        method=method,
        constraint_errors=_compute_constraint_errors(pmf, mc),
        plausibility_pass=False,
    )
    cr.plausibility_pass = len(cr.validate()) == 0
    return cr


def _compute_constraint_errors(pmf: np.ndarray, mc) -> dict:
    """Compute absolute errors between PMF-derived probabilities and market targets."""
    n = pmf.shape[0]
    errors = {}
    hw = sum(pmf[h, a] for h in range(n) for a in range(n) if h > a)
    dr = sum(pmf[h, a] for h in range(n) for a in range(n) if h == a)
    aw = sum(pmf[h, a] for h in range(n) for a in range(n) if h < a)
    if mc.home_win is not None:
        errors["1x2_home"] = abs(hw - mc.home_win)
        errors["1x2_draw"] = abs(dr - mc.draw)
        errors["1x2_away"] = abs(aw - mc.away_win)
    for attr, line_name in [
        ("over_2_5", "ou_2.5"), ("over_1_5", "ou_1.5"), ("over_3_5", "ou_3.5"),
    ]:
        v = getattr(mc, attr, None)
        if v is not None:
            line = float(line_name.split("_")[1])
            p_ou = sum(pmf[h, a] for h in range(n) for a in range(n) if h + a > line)
            errors[line_name] = abs(p_ou - v)
    if mc.btts_yes is not None:
        p_btts = sum(pmf[h, a] for h in range(n) for a in range(n) if h > 0 and a > 0)
        errors["btts"] = abs(p_btts - mc.btts_yes)
    if mc.has_correct_score:
        cs_err = 0.0
        for (h, a), prob in list(mc.correct_score.items())[:10]:
            if h < n and a < n:
                cs_err += abs(pmf[h, a] - prob)
        errors["cs_sum_top10"] = cs_err
    return {k: round(float(v), 6) for k, v in errors.items()}


def _validation_loss(pmf: np.ndarray, mc) -> float:
    """
    Scalar validation loss: sum of weighted squared market constraint errors.
    Lower = better fit to market.
    """
    errs = _compute_constraint_errors(pmf, mc)
    weights = {
        "1x2_home": 25.0, "1x2_draw": 25.0, "1x2_away": 25.0,
        "ou_2.5": 18.0, "ou_1.5": 15.0, "ou_3.5": 15.0,
        "btts": 12.0, "cs_sum_top10": 4.0,
    }
    loss = sum(weights.get(k, 5.0) * v ** 2 for k, v in errs.items())
    return float(loss)
