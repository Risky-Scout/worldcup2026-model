"""
Pre-game edge screening for World Cup betting markets.

Given a calibrated joint PMF and a set of market (no-vig) probabilities, this
module computes:

  1. Fair odds — the reciprocal of PMF-derived probabilities
  2. Edge — (model_prob - market_prob) / market_prob
  3. Half-Kelly bet fraction — using the standard Kelly criterion
  4. Parametric 90% confidence interval on model probabilities
     (via normal approximation on the Poisson λ uncertainty)
  5. CLV tracking framework — compares prediction to closing line

Usage
-----
    edge = compute_edge_report(pmf_grid, markets, pregame_lh, pregame_la)
    edge.to_dict()   # → ready for JSON serialisation

Edge filter rules
-----------------
A market is flagged for potential value if ALL of the following hold:
  - edge ≥ MIN_EDGE_THRESHOLD (default 0.04 = 4%)
  - model CI lower bound > market_prob (model consistently favours outcome)
  - market_prob > MIN_LIQUIDITY_PROB (default 0.02 = avoid long-shot noise)
  - odds are not stale (updated_at check at call site)

Half-Kelly
----------
f* = edge / odds_decimal   (where edge = model_p - market_p)
Capped at MAX_KELLY_FRACTION (default 0.05 = 5% of bankroll) to prevent
over-sizing due to model uncertainty.

Disclaimer
----------
Edge estimates are outputs of a probabilistic model.  They are not guaranteed
profit signals.  Model error, market liquidity, odds movement, and variance
all affect realised returns.  Always apply bankroll management.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field

import numpy as np

try:
    from penaltyblog.betting import kelly_criterion as _pb_kelly_criterion
    _HAS_PB_KELLY = True
except Exception:
    _HAS_PB_KELLY = False

log = logging.getLogger(__name__)

# ── Constants ─────────────────────────────────────────────────────────────────
MIN_EDGE_THRESHOLD = 0.04      # flag edge ≥ 4%
MIN_LIQUIDITY_PROB = 0.02      # ignore sub-2% market implied
MAX_KELLY_FRACTION = 0.15      # cap half-Kelly at 15% of bankroll (edge-dependent)
CI_Z = 1.645                   # 90% one-sided z-score
LAMBDA_UNCERTAINTY_FRAC = 0.12 # ±12% λ uncertainty for CI (conservative)


# ── Data classes ──────────────────────────────────────────────────────────────

@dataclass
class MarketEdge:
    """Edge analysis for one market outcome."""
    market: str            # e.g. "home_win", "over_2_5", "btts_yes", "1-0"
    model_prob: float
    market_prob: float     # no-vig market probability
    edge: float            # (model_prob - market_prob) / market_prob
    fair_odds_decimal: float
    market_odds_decimal: float
    # NOTE: these are NOT statistical confidence intervals. They are a sensitivity
    # analysis produced by perturbing λ ± LAMBDA_UNCERTAINTY_FRAC (default ±12%).
    # They reflect model sensitivity to λ uncertainty, not frequentist coverage.
    lambda_sensitivity_lower: float  # lower bound at λ ± 12% (renamed from ci_lower_90)
    lambda_sensitivity_upper: float  # upper bound at λ ± 12% (renamed from ci_upper_90)
    half_kelly: float      # recommended half-Kelly fraction (capped; disabled for market_reconciled)
    value_flag: bool       # True if passes all filter criteria (never True for market_reconciled)
    value_reason: str      # human-readable reason for value_flag

    def to_dict(self) -> dict:
        return {
            "market": self.market,
            "model_prob": round(self.model_prob, 5),
            "market_prob": round(self.market_prob, 5),
            "edge_pct": round(self.edge * 100, 2),
            "fair_odds": round(self.fair_odds_decimal, 3),
            "market_odds": round(self.market_odds_decimal, 3),
            # Sensitivity range (not a CI): see LAMBDA_UNCERTAINTY_FRAC constant
            "lambda_sensitivity_lower": round(self.lambda_sensitivity_lower, 5),
            "lambda_sensitivity_upper": round(self.lambda_sensitivity_upper, 5),
            "half_kelly_pct": round(self.half_kelly * 100, 3),
            "value_flag": self.value_flag,
            "value_reason": self.value_reason,
        }


@dataclass
class EdgeReport:
    """Full edge report for one match prediction."""
    match_id: str
    home_team: str
    away_team: str
    prediction_mode: str       # pure_model / market_reconciled / etc.
    pregame_lh: float
    pregame_la: float
    lambda_uncertainty: float  # fractional uncertainty on λ

    edges: list[MarketEdge] = field(default_factory=list)
    n_value_markets: int = 0
    top_value_market: str | None = None
    model_vs_market_summary: str = ""
    disclaimer: str = (
        "Edge estimates are model outputs only. Not guaranteed profit signals."
    )

    def to_dict(self) -> dict:
        return {
            "match_id": self.match_id,
            "home_team": self.home_team,
            "away_team": self.away_team,
            "prediction_mode": self.prediction_mode,
            "pregame_lh": round(self.pregame_lh, 4),
            "pregame_la": round(self.pregame_la, 4),
            "lambda_uncertainty_pct": round(self.lambda_uncertainty * 100, 1),
            "n_value_markets": self.n_value_markets,
            "top_value_market": self.top_value_market,
            "model_vs_market_summary": self.model_vs_market_summary,
            "edges": [e.to_dict() for e in self.edges],
            "disclaimer": self.disclaimer,
        }

    def value_markets(self) -> list[MarketEdge]:
        return [e for e in self.edges if e.value_flag]


# ── Core computation ──────────────────────────────────────────────────────────

def _prob_to_decimal_odds(prob: float) -> float:
    """Convert probability to decimal odds, clamped to reasonable range."""
    prob = max(prob, 0.001)
    return round(1.0 / prob, 4)


def _edge_dependent_kelly_cap(edge_frac: float) -> float:
    """
    Return Kelly cap proportional to conviction (edge size).
    Prevents over-sizing on marginal edges while allowing full allocation on strong ones.
    """
    if edge_frac >= 0.15:
        return MAX_KELLY_FRACTION
    elif edge_frac >= 0.08:
        return MAX_KELLY_FRACTION * 0.67
    elif edge_frac >= 0.04:
        return MAX_KELLY_FRACTION * 0.40
    else:
        return MAX_KELLY_FRACTION * 0.20


def _half_kelly(model_p: float, market_odds_dec: float) -> float:
    """
    Compute half-Kelly bet fraction using penaltyblog.betting.kelly_criterion.
    Falls back to the manual formula if penaltyblog is unavailable.
    Capped at edge-dependent fraction of MAX_KELLY_FRACTION (15% of bankroll max).
    """
    if market_odds_dec <= 1.01:
        return 0.0

    # Compute raw edge for edge-dependent cap
    market_p = 1.0 / market_odds_dec if market_odds_dec > 0 else 0.5
    edge_frac = (model_p - market_p) / market_p if market_p > 0 else 0.0
    kelly_cap = _edge_dependent_kelly_cap(edge_frac)

    if _HAS_PB_KELLY:
        try:
            result = _pb_kelly_criterion(market_odds_dec, model_p, fraction=0.5)
            stake = float(result.stake)
            return min(max(stake, 0.0), kelly_cap)
        except Exception:
            pass
    # Manual fallback: standard Kelly formula halved
    full_kelly = (model_p * market_odds_dec - 1.0) / (market_odds_dec - 1.0)
    half = max(full_kelly / 2.0, 0.0)
    return min(half, kelly_cap)


def _poisson_ci(lh: float, la: float, pmf_func, uncertainty: float = LAMBDA_UNCERTAINTY_FRAC) -> tuple:
    """
    Compute 90% CI on model probability by perturbing λ ± uncertainty.

    Returns (lower, upper) by evaluating the PMF at:
      λ_low  = (lh*(1-u), la*(1+u))  — worst case for outcome
      λ_high = (lh*(1+u), la*(1-u))  — best case for outcome

    pmf_func(lh, la) → probability (scalar)
    """
    u = uncertainty
    try:
        p_low = float(pmf_func(lh * (1 - u), la * (1 + u)))
        p_high = float(pmf_func(lh * (1 + u), la * (1 - u)))
        # Also try the reverse
        p_low2 = float(pmf_func(lh * (1 + u), la * (1 - u)))
        p_high2 = float(pmf_func(lh * (1 - u), la * (1 + u)))
        lower = min(p_low, p_low2)
        upper = max(p_high, p_high2)
        return float(np.clip(lower, 0, 1)), float(np.clip(upper, 0, 1))
    except Exception:
        return 0.0, 1.0


def _value_flag(
    edge: float,
    model_p: float,
    market_p: float,
    ci_lower: float,
) -> tuple[bool, str]:
    """Return (value_flag, reason_string) applying all filter criteria."""
    reasons = []

    if edge < MIN_EDGE_THRESHOLD:
        return False, f"edge {edge*100:.1f}% below threshold {MIN_EDGE_THRESHOLD*100:.0f}%"

    if market_p < MIN_LIQUIDITY_PROB:
        return False, f"market_prob {market_p:.4f} too low (liquidity filter)"

    if ci_lower <= market_p:
        reasons.append(f"CI lower {ci_lower:.4f} ≤ market {market_p:.4f} (uncertain)")
        return False, "; ".join(reasons)

    return True, f"edge={edge*100:.1f}% CI_lower={ci_lower:.4f}>market={market_p:.4f}"


def compute_market_edges(
    pmf: np.ndarray,
    market_probs: dict,
    lh: float,
    la: float,
    uncertainty: float = LAMBDA_UNCERTAINTY_FRAC,
    prediction_mode: str = "market_reconciled",
) -> list[MarketEdge]:
    """
    Compute edge for each available market.

    Parameters
    ----------
    pmf              Normalized 2D numpy array (home_goals × away_goals)
    market_probs     Dict of market_name → no-vig market probability, e.g.:
                       {"home_win": 0.52, "draw": 0.28, "away_win": 0.20,
                        "over_2_5": 0.61, "btts_yes": 0.48, ...}
    lh, la           Pre-game attack lambdas (home, away)
    uncertainty      Fractional λ uncertainty for sensitivity range computation
    prediction_mode  Publish mode — when "market_reconciled" (or "market_implied"),
                     circular edge detection fires: value_flag is forced to False
                     and Kelly is set to 0 because the PMF was shaped by the same
                     market data being compared. Only structural-model PMFs may
                     generate value_flag=True outputs.

    Returns
    -------
    List of MarketEdge objects, sorted by edge descending
    """
    # Circular edge guard: market-reconciled / market-implied PMFs cannot produce
    # an independent edge signal vs the same market inputs used to construct them.
    _circular_mode = prediction_mode in ("market_reconciled", "market_implied")
    if _circular_mode:
        log.debug(
            "compute_market_edges: prediction_mode=%s — "
            "value_flag forced to False (circular edge guard active)",
            prediction_mode,
        )
    n = pmf.shape[0]
    edges: list[MarketEdge] = []

    # ── Build standard masks ─────────────────────────────────────────────
    h_idx = np.arange(n)
    a_idx = np.arange(n)
    hh, aa = np.meshgrid(h_idx, a_idx, indexing="ij")
    totals = hh + aa

    home_mask = (hh > aa).astype(float)
    draw_mask = (hh == aa).astype(float)
    away_mask = (hh < aa).astype(float)
    btts_mask = ((hh > 0) & (aa > 0)).astype(float)

    def pmf_1x2_hw(l_h, l_a):
        from scipy.stats import poisson
        g = np.outer(poisson.pmf(h_idx, l_h), poisson.pmf(a_idx, l_a))
        return float((g * home_mask).sum())

    def pmf_1x2_dr(l_h, l_a):
        from scipy.stats import poisson
        g = np.outer(poisson.pmf(h_idx, l_h), poisson.pmf(a_idx, l_a))
        return float((g * draw_mask).sum())

    def pmf_1x2_aw(l_h, l_a):
        from scipy.stats import poisson
        g = np.outer(poisson.pmf(h_idx, l_h), poisson.pmf(a_idx, l_a))
        return float((g * away_mask).sum())

    def pmf_btts(l_h, l_a):
        from scipy.stats import poisson
        g = np.outer(poisson.pmf(h_idx, l_h), poisson.pmf(a_idx, l_a))
        return float((g * btts_mask).sum())

    def pmf_over(threshold):
        def _f(l_h, l_a):
            from scipy.stats import poisson
            g = np.outer(poisson.pmf(h_idx, l_h), poisson.pmf(a_idx, l_a))
            mask = (totals > threshold).astype(float)
            return float((g * mask).sum())
        return _f

    def pmf_exact(h_goals, a_goals):
        def _f(l_h, l_a):
            from scipy.stats import poisson
            return float(poisson.pmf(h_goals, l_h) * poisson.pmf(a_goals, l_a))
        return _f

    # Map market names to PMF functions
    market_funcs: dict = {
        "home_win": pmf_1x2_hw,
        "draw": pmf_1x2_dr,
        "away_win": pmf_1x2_aw,
        "btts_yes": pmf_btts,
        "btts_no": lambda l_h, l_a: 1.0 - pmf_btts(l_h, l_a),
    }
    for k in [0.5, 1.5, 2.5, 3.5, 4.5, 5.5, 6.5]:
        market_funcs[f"over_{str(k).replace('.','_')}"] = pmf_over(k)
        market_funcs[f"under_{str(k).replace('.','_')}"] = (
            lambda l_h, l_a, _k=k: 1.0 - pmf_over(_k)(l_h, l_a)
        )

    # PMF-derived model probs (from the actual calibrated grid)
    model_hw = float((pmf * home_mask).sum())
    model_dr = float((pmf * draw_mask).sum())
    model_aw = float((pmf * away_mask).sum())
    model_btts = float((pmf * btts_mask).sum())

    model_probs_grid: dict[str, float] = {
        "home_win": model_hw,
        "draw": model_dr,
        "away_win": model_aw,
        "btts_yes": model_btts,
        "btts_no": 1.0 - model_btts,
    }
    for k in [0.5, 1.5, 2.5, 3.5, 4.5, 5.5, 6.5]:
        over_mask = (totals > k).astype(float)
        model_probs_grid[f"over_{str(k).replace('.','_')}"] = float((pmf * over_mask).sum())
        model_probs_grid[f"under_{str(k).replace('.','_')}"] = (
            1.0 - model_probs_grid[f"over_{str(k).replace('.','_')}"]
        )

    # Add exact-score markets from the grid
    for h_g in range(min(n, 8)):
        for a_g in range(min(n, 8)):
            key = f"{h_g}-{a_g}"
            model_probs_grid[key] = float(pmf[h_g, a_g]) if h_g < n and a_g < n else 0.0
            if key not in market_funcs:
                market_funcs[key] = pmf_exact(h_g, a_g)

    # ── Compute edge for each available market prob ───────────────────────
    for mkt_name, mkt_prob in market_probs.items():
        if mkt_prob is None or np.isnan(mkt_prob) or mkt_prob <= 0:
            continue

        model_p = model_probs_grid.get(mkt_name)
        if model_p is None:
            # Try to compute from PMF function
            fn = market_funcs.get(mkt_name)
            if fn is None:
                continue
            model_p = float(fn(lh, la))

        if model_p <= 0 or np.isnan(model_p):
            continue

        # CI via λ perturbation
        fn = market_funcs.get(mkt_name)
        if fn is not None:
            ci_lo, ci_hi = _poisson_ci(lh, la, fn, uncertainty)
        else:
            # Fallback: ±uncertainty directly on model_p
            ci_lo = max(model_p * (1 - uncertainty * CI_Z), 0.0)
            ci_hi = min(model_p * (1 + uncertainty * CI_Z), 1.0)

        edge = (model_p - mkt_prob) / mkt_prob if mkt_prob > 0 else 0.0
        fair_odds = _prob_to_decimal_odds(model_p)
        mkt_odds = _prob_to_decimal_odds(mkt_prob)

        if _circular_mode:
            # Circular edge: zero Kelly, force value_flag=False
            kelly = 0.0
            v_flag = False
            v_reason = (
                f"CIRCULAR_EDGE_SUPPRESSED: prediction_mode={prediction_mode}; "
                "PMF was shaped by the same market inputs — edge is not independent"
            )
        else:
            kelly = _half_kelly(model_p, mkt_odds)
            v_flag, v_reason = _value_flag(edge, model_p, mkt_prob, ci_lo)

        edges.append(MarketEdge(
            market=mkt_name,
            model_prob=round(float(model_p), 6),
            market_prob=round(float(mkt_prob), 6),
            edge=round(float(edge), 6),
            fair_odds_decimal=round(float(fair_odds), 4),
            market_odds_decimal=round(float(mkt_odds), 4),
            lambda_sensitivity_lower=round(float(ci_lo), 6),
            lambda_sensitivity_upper=round(float(ci_hi), 6),
            half_kelly=round(float(kelly), 6),
            value_flag=v_flag,
            value_reason=v_reason,
        ))

    return sorted(edges, key=lambda e: -e.edge)


def compute_edge_report(
    pmf: np.ndarray,
    market_probs: dict,
    lh: float,
    la: float,
    match_id: str = "",
    home_team: str = "",
    away_team: str = "",
    prediction_mode: str = "market_reconciled",
    uncertainty: float = LAMBDA_UNCERTAINTY_FRAC,
) -> EdgeReport:
    """
    Compute full pre-game edge report for a single match.

    Parameters
    ----------
    pmf            Calibrated joint PMF grid (numpy 2D array, sums to 1)
    market_probs   No-vig market probabilities dict
    lh, la         Pre-game attack lambdas
    match_id       BDL match identifier
    home_team      Home team name
    away_team      Away team name
    prediction_mode  e.g. "market_reconciled", "pure_model"
    uncertainty    Fractional λ uncertainty (default 12%)
    """
    edges = compute_market_edges(pmf, market_probs, lh, la, uncertainty,
                                 prediction_mode=prediction_mode)

    value_mkts = [e for e in edges if e.value_flag]
    top = value_mkts[0].market if value_mkts else None

    # Summary sentence
    n = pmf.shape[0]
    h_idx = np.arange(n)
    a_idx = np.arange(n)
    hh, aa = np.meshgrid(h_idx, a_idx, indexing="ij")
    home_mask = (hh > aa).astype(float)
    draw_mask = (hh == aa).astype(float)
    away_mask = (hh < aa).astype(float)
    model_hw = float((pmf * home_mask).sum())
    model_dr = float((pmf * draw_mask).sum())
    model_aw = float((pmf * away_mask).sum())

    mkt_hw = market_probs.get("home_win", float("nan"))
    mkt_aw = market_probs.get("away_win", float("nan"))
    summary = (
        f"Model: H={model_hw:.1%} D={model_dr:.1%} A={model_aw:.1%}  "
        f"Market: H={mkt_hw:.1%} A={mkt_aw:.1%}  "
        f"Value markets: {len(value_mkts)}"
    )

    return EdgeReport(
        match_id=match_id,
        home_team=home_team,
        away_team=away_team,
        prediction_mode=prediction_mode,
        pregame_lh=round(lh, 4),
        pregame_la=round(la, 4),
        lambda_uncertainty=uncertainty,
        edges=edges,
        n_value_markets=len(value_mkts),
        top_value_market=top,
        model_vs_market_summary=summary,
    )


def format_edge_table(edges: list[MarketEdge], max_rows: int = 20) -> str:
    """Format edge list as a markdown table string."""
    lines = [
        "| Market | Model% | Market% | Edge% | Fair odds | Mkt odds | Half-Kelly% | Value |",
        "|--------|--------|---------|-------|-----------|----------|-------------|-------|",
    ]
    for e in edges[:max_rows]:
        flag = "✅" if e.value_flag else "—"
        lines.append(
            f"| {e.market} | {e.model_prob*100:.2f} | {e.market_prob*100:.2f} | "
            f"{e.edge*100:+.1f} | {e.fair_odds_decimal:.3f} | {e.market_odds_decimal:.3f} | "
            f"{e.half_kelly*100:.2f} | {flag} |"
        )
    return "\n".join(lines)
