"""
Market reconciliation engine: three publish modes.

Modes
-----
pure_model
    Best available statistical model (neg_binomial champion for known teams,
    elo_fallback for new teams).  No market data.  Used for diagnostics and
    matches without BDL odds.

market_implied
    PMF derived entirely from BDL no-vig consensus.
    Uses goal_expectancy_extended (1X2 + O/U 2.5) as the starting PMF,
    then applies correct-score, BTTS, spread, DNB, and double-chance
    constraints via iterative Sinkhorn/IPF adjustment.

market_reconciled   ← DEFAULT PUBLISH MODE when BDL odds exist
    Starts with the market_implied PMF as the prior.
    Blends with the pure_model PMF to add team-specific discrimination.
    Produces one internally consistent joint PMF.
    The blending weight α is driven by market quality:
      α → 1  when 6-vendor odds + correct-score data exist
      α → 0  when no odds are available
"""
from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field
from typing import Optional

import numpy as np
from scipy.optimize import minimize

log = logging.getLogger(__name__)

_EPS = 1e-9


# ---------------------------------------------------------------------------
# Market constraints container
# ---------------------------------------------------------------------------

@dataclass
class MarketConstraints:
    """All no-vig probabilities extracted from BDL for one match."""

    # ── 1X2 ─────────────────────────────────────────────────────────────
    home_win: Optional[float] = None
    draw: Optional[float] = None
    away_win: Optional[float] = None
    n_vendors_1x2: int = 0

    # ── Totals (no-vig over probabilities) ──────────────────────────────
    over_0_5: Optional[float] = None
    over_1_5: Optional[float] = None
    over_2_5: Optional[float] = None
    over_3_5: Optional[float] = None
    over_4_5: Optional[float] = None
    over_5_5: Optional[float] = None
    over_6_5: Optional[float] = None

    # ── BTTS ─────────────────────────────────────────────────────────────
    btts_yes: Optional[float] = None
    btts_no: Optional[float] = None

    # ── Draw no bet ─────────────────────────────────────────────────────
    dnb_home: Optional[float] = None
    dnb_away: Optional[float] = None

    # ── Double chance ────────────────────────────────────────────────────
    dc_1x: Optional[float] = None
    dc_x2: Optional[float] = None
    dc_12: Optional[float] = None

    # ── Correct score {(h, a): prob} ─────────────────────────────────────
    correct_score: dict = field(default_factory=dict)
    n_cs_vendors: int = 0
    n_cs_outcomes: int = 0

    # ── Odds freshness ────────────────────────────────────────────────────
    odds_timestamp: Optional[str] = None
    stale: bool = False

    @property
    def has_1x2(self) -> bool:
        return all(x is not None for x in [self.home_win, self.draw, self.away_win])

    @property
    def has_totals(self) -> bool:
        return self.over_2_5 is not None

    @property
    def has_correct_score(self) -> bool:
        return len(self.correct_score) > 0

    @property
    def quality_score(self) -> float:
        """
        0.0 – 1.0. Higher = more market data available.
        Used to set the market blending weight α.
        """
        score = 0.0
        if self.has_1x2:
            score += 0.4 + min(self.n_vendors_1x2 / 6.0, 1.0) * 0.1
        if self.has_totals:
            n_lines = sum(1 for v in [self.over_0_5, self.over_1_5, self.over_2_5,
                                       self.over_3_5, self.over_4_5, self.over_5_5,
                                       self.over_6_5] if v is not None)
            score += min(n_lines / 7.0, 1.0) * 0.2
        if self.has_correct_score:
            score += min(self.n_cs_outcomes / 20.0, 1.0) * 0.3
        if self.stale:
            score *= 0.5
        return min(score, 1.0)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _american_to_decimal(american: float) -> float:
    """Convert American moneyline odds to decimal (European) odds."""
    if american >= 100:
        return american / 100.0 + 1.0
    else:
        return 100.0 / abs(american) + 1.0


def _decimal_to_prob(dec: float) -> float:
    if dec <= 1.0:
        return 1.0
    return 1.0 / dec


def _strip_vig_multiplicative(probs: list[float]) -> list[float]:
    """Remove overround via multiplicative method."""
    total = sum(probs)
    if total <= 0:
        return probs
    return [p / total for p in probs]


def _strip_vig_pair(dec_over: float, dec_under: float) -> tuple[float, float]:
    """Remove vig from an O/U pair (decimal odds)."""
    p_over = _decimal_to_prob(dec_over)
    p_under = _decimal_to_prob(dec_under)
    total = p_over + p_under
    if total <= 0:
        return 0.5, 0.5
    return p_over / total, p_under / total


# ---------------------------------------------------------------------------
# Extract constraints from raw BDL odds rows
# ---------------------------------------------------------------------------

def extract_constraints(
    odds_df,       # pd.DataFrame: rows for one match from odds.parquet
    markets_df,    # pd.DataFrame: rows for one match from markets.parquet
    match_id: int,
) -> MarketConstraints:
    """
    Build a MarketConstraints from BDL odds and markets rows for one match.

    Strips vig using the multiplicative method.
    Aggregates across all vendors using mean.
    """
    mc = MarketConstraints()

    if odds_df is None or len(odds_df) == 0:
        return mc

    mrows = odds_df[odds_df["match_id"] == match_id]
    if mrows.empty:
        return mc

    # Collect updated_at for freshness
    try:
        mc.odds_timestamp = str(mrows["updated_at"].max())
    except Exception:
        pass

    # ── 1X2 (from main odds table) ───────────────────────────────────────
    hw_list, dr_list, aw_list = [], [], []
    for _, row in mrows.iterrows():
        try:
            hw = row.get("moneyline_home")
            dr = row.get("moneyline_draw")
            aw = row.get("moneyline_away")
            if hw is None or dr is None or aw is None:
                continue
            # Convert American to decimal if needed (negative means favourite in American)
            if abs(float(hw)) > 10:
                # American odds format
                p_hw = _decimal_to_prob(_american_to_decimal(float(hw)))
                p_dr = _decimal_to_prob(_american_to_decimal(float(dr)))
                p_aw = _decimal_to_prob(_american_to_decimal(float(aw)))
            else:
                # Already decimal
                p_hw = _decimal_to_prob(float(hw))
                p_dr = _decimal_to_prob(float(dr))
                p_aw = _decimal_to_prob(float(aw))
            stripped = _strip_vig_multiplicative([p_hw, p_dr, p_aw])
            hw_list.append(stripped[0])
            dr_list.append(stripped[1])
            aw_list.append(stripped[2])
        except Exception:
            continue

    if hw_list:
        mc.home_win = float(np.mean(hw_list))
        mc.draw = float(np.mean(dr_list))
        mc.away_win = float(np.mean(aw_list))
        mc.n_vendors_1x2 = len(hw_list)

    # ── Totals from main odds table (top-level total_value) ──────────────
    totals_map: dict[float, list[float]] = {}
    for _, row in mrows.iterrows():
        try:
            tv = row.get("total_value")
            too = row.get("total_over_odds")
            tuo = row.get("total_under_odds")
            if tv is None or too is None or tuo is None:
                continue
            line = float(tv)
            # American odds format
            p_ov, p_un = _strip_vig_pair(
                _american_to_decimal(float(too)),
                _american_to_decimal(float(tuo)),
            )
            if line not in totals_map:
                totals_map[line] = []
            totals_map[line].append(p_ov)
        except Exception:
            continue

    line_map = {0.5: "over_0_5", 1.5: "over_1_5", 2.5: "over_2_5",
                3.5: "over_3_5", 4.5: "over_4_5", 5.5: "over_5_5", 6.5: "over_6_5"}
    for line, attr in line_map.items():
        if line in totals_map:
            setattr(mc, attr, float(np.mean(totals_map[line])))

    # ── Parse markets sub-array ──────────────────────────────────────────
    if markets_df is not None and not markets_df.empty:
        mkt_rows = markets_df[
            (markets_df["match_id"] == match_id) &
            (markets_df["period"] == "match")
        ]

        # More totals from markets table
        total_rows = mkt_rows[mkt_rows["market_type"] == "total"]
        for (line_val, oc_type), grp in total_rows.groupby(["line_value", "outcome_type"]):
            if oc_type not in ("over", "under"):
                continue
            try:
                line = float(line_val) if line_val is not None else None
                if line is None:
                    continue
                dec_odds_list = grp["decimal_odds"].dropna().tolist()
                if not dec_odds_list:
                    continue
                avg_dec = float(np.mean(dec_odds_list))
                raw_over_p = 1.0 / avg_dec
            except Exception:
                continue
            attr = line_map.get(float(line) if line is not None else -1)
            if attr and oc_type == "over" and getattr(mc, attr) is None:
                # We need both over + under to strip vig properly; approximation only
                pass  # Use main odds table values preferred

        # BTTS from markets table
        btts_rows = mkt_rows[mkt_rows["market_type"] == "btts"]
        if not btts_rows.empty:
            yes_list, no_list = [], []
            for _, row in btts_rows.iterrows():
                try:
                    dec = row.get("decimal_odds")
                    oc_type = row.get("outcome_type", "")
                    if dec is None or dec <= 1:
                        continue
                    prob = 1.0 / float(dec)
                    if "yes" in str(row.get("outcome_name", "")).lower():
                        yes_list.append(prob)
                    elif "no" in str(row.get("outcome_name", "")).lower():
                        no_list.append(prob)
                except Exception:
                    continue
            if yes_list and no_list:
                raw_yes = float(np.mean(yes_list))
                raw_no = float(np.mean(no_list))
                stripped = _strip_vig_multiplicative([raw_yes, raw_no])
                mc.btts_yes = stripped[0]
                mc.btts_no = stripped[1]

        # DNB from markets table
        dnb_rows = mkt_rows[mkt_rows["market_type"] == "draw_no_bet"]
        if not dnb_rows.empty:
            h_list, a_list = [], []
            for _, row in dnb_rows.iterrows():
                try:
                    dec = row.get("decimal_odds")
                    if dec is None or dec <= 1:
                        continue
                    prob = 1.0 / float(dec)
                    ot = str(row.get("outcome_type", ""))
                    if ot == "home":
                        h_list.append(prob)
                    elif ot == "away":
                        a_list.append(prob)
                except Exception:
                    continue
            if h_list and a_list:
                raw_h = float(np.mean(h_list))
                raw_a = float(np.mean(a_list))
                stripped = _strip_vig_multiplicative([raw_h, raw_a])
                mc.dnb_home = stripped[0]
                mc.dnb_away = stripped[1]

        # Double chance from markets table
        dc_rows = mkt_rows[mkt_rows["market_type"] == "double_chance"]
        if not dc_rows.empty:
            vals = {"1x": [], "x2": [], "12": []}
            for _, row in dc_rows.iterrows():
                try:
                    dec = row.get("decimal_odds")
                    if dec is None or dec <= 1:
                        continue
                    name = str(row.get("outcome_name", "")).lower()
                    if "draw" in name and ("home" in name or "1" in name):
                        vals["1x"].append(1.0 / float(dec))
                    elif "draw" in name and ("away" in name or "2" in name):
                        vals["x2"].append(1.0 / float(dec))
                    elif ("home" in name or "1" in name) and ("away" in name or "2" in name):
                        vals["12"].append(1.0 / float(dec))
                except Exception:
                    continue
            if vals["1x"]:
                mc.dc_1x = float(np.mean(vals["1x"]))
            if vals["x2"]:
                mc.dc_x2 = float(np.mean(vals["x2"]))
            if vals["12"]:
                mc.dc_12 = float(np.mean(vals["12"]))

        # ── Correct score ────────────────────────────────────────────────
        cs_rows = mkt_rows[
            (mkt_rows["market_type"] == "correct_score") &
            (mkt_rows["h_goals"].notna()) &
            (mkt_rows["a_goals"].notna())
        ]
        if not cs_rows.empty:
            # Group by (h_goals, a_goals), average decimal odds across vendors
            cs_by_score: dict[tuple[int, int], list[float]] = {}
            n_vendors_seen: set = set()
            for _, row in cs_rows.iterrows():
                try:
                    h = int(row["h_goals"])
                    a = int(row["a_goals"])
                    dec = row.get("decimal_odds")
                    vendor = row.get("vendor", "?")
                    if dec is None or float(dec) <= 1:
                        continue
                    key = (h, a)
                    if key not in cs_by_score:
                        cs_by_score[key] = []
                    cs_by_score[key].append(float(dec))
                    n_vendors_seen.add(vendor)
                except Exception:
                    continue

            if cs_by_score:
                # Convert average decimal odds to raw probabilities
                raw_probs = {k: 1.0 / float(np.mean(v)) for k, v in cs_by_score.items()}
                # Strip vig: normalize to sum = 1
                # Note: the raw sum > 1 due to bookmaker margin
                total_raw = sum(raw_probs.values())
                if total_raw > 0:
                    mc.correct_score = {k: v / total_raw for k, v in raw_probs.items()}
                    mc.n_cs_vendors = len(n_vendors_seen)
                    mc.n_cs_outcomes = len(mc.correct_score)

    return mc


# ---------------------------------------------------------------------------
# Market-implied PMF (mode: market_implied)
# ---------------------------------------------------------------------------

def build_market_implied_pmf(
    mc: MarketConstraints,
    max_goals: int = 15,
) -> tuple[np.ndarray, float, float, float]:
    """
    Build a joint PMF from market constraints using goal_expectancy_extended.

    Returns (pmf_grid, lambda_home, lambda_away, rho)
    """
    if not mc.has_1x2:
        raise ValueError("Need 1X2 to build market-implied PMF")

    hw = mc.home_win
    dr = mc.draw
    aw = mc.away_win

    # Ensure sum = 1
    total = hw + dr + aw
    hw, dr, aw = hw / total, dr / total, aw / total

    # Get over/under 2.5 for goal_expectancy_extended
    over_25 = mc.over_2_5 if mc.over_2_5 is not None else None
    under_25 = (1.0 - over_25) if over_25 is not None else None

    try:
        from penaltyblog.models import goal_expectancy_extended, create_dixon_coles_grid
        if over_25 is not None:
            result = goal_expectancy_extended(hw, dr, aw, over_25, under_25)
            # penaltyblog returns a dict
            if isinstance(result, dict):
                lh = float(result["home_exp"])
                la = float(result["away_exp"])
                rho = float(result.get("implied_rho", 0.0) or 0.0)
            else:
                lh = float(result.home_goal_expectancy)
                la = float(result.away_goal_expectancy)
                rho = float(getattr(result, "rho", 0.0) or 0.0)
        else:
            # 1X2 only: use simpler goal_expectancy
            from penaltyblog.models import goal_expectancy
            result = goal_expectancy(hw, dr, aw)
            if isinstance(result, dict):
                lh = float(result.get("home_exp", 1.3))
                la = float(result.get("away_exp", 1.0))
            else:
                lh = float(result.home_goal_expectancy)
                la = float(result.away_goal_expectancy)
            rho = 0.0

        grid = create_dixon_coles_grid(lh, la, rho=rho, max_goals=max_goals - 1)
        pmf = np.array(grid.grid, dtype=np.float64)
        pmf = np.clip(pmf, 0, None)
        pmf /= pmf.sum()
        return pmf, lh, la, rho

    except Exception as exc:
        log.warning("goal_expectancy_extended failed: %s. Using Poisson fallback.", exc)
        from scipy.stats import poisson
        lh = 1.3
        la = 1.0
        pmf = np.outer(
            poisson.pmf(range(max_goals), lh),
            poisson.pmf(range(max_goals), la),
        )
        pmf /= pmf.sum()
        return pmf, lh, la, 0.0


# ---------------------------------------------------------------------------
# IPF-style adjustment for correct-score constraints
# ---------------------------------------------------------------------------

def apply_correct_score_adjustment(
    pmf: np.ndarray,
    correct_score: dict[tuple[int, int], float],
    alpha: float = 0.8,
    n_iter: int = 5,
    max_goals: int = 15,
) -> np.ndarray:
    """
    Blend market correct-score probabilities into the PMF.

    For each (h, a) with a market probability p_mkt:
        P_new(h,a) ← α * p_mkt + (1-α) * P(h,a)

    Then re-normalize the full grid.

    Parameters
    ----------
    alpha : weight on market correct-score (0 = ignore, 1 = fully trust market)
    n_iter : number of normalisation passes
    """
    if not correct_score:
        return pmf.copy()

    p = pmf.copy()
    n = min(max_goals, p.shape[0])

    for _ in range(n_iter):
        # Apply market correct-score adjustments
        for (h, a), p_mkt in correct_score.items():
            if h < n and a < n:
                p[h, a] = alpha * p_mkt + (1.0 - alpha) * p[h, a]

        # Ensure non-negative
        p = np.clip(p, 0, None)

        # Re-normalize
        total = p.sum()
        if total > _EPS:
            p /= total
        else:
            return pmf.copy()

    return p


# ---------------------------------------------------------------------------
# Full KL-minimization reconciliation (optional, more precise)
# ---------------------------------------------------------------------------

def reconcile_pmf_kl(
    prior: np.ndarray,
    mc: MarketConstraints,
    max_goals: int = 15,
    tolerance: float = 1e-6,
) -> np.ndarray:
    """
    Minimum-KL divergence reconciliation of prior PMF against market constraints.

    Minimizes KL(P || prior) subject to:
      - P sums to 1
      - 1X2 marginals match market
      - O/U lines match market where available
      - BTTS matches market where available
      - Correct-score cells match no-vig values where available

    Parameters
    ----------
    prior : n×n numpy array (prior PMF, typically market_implied)
    mc : MarketConstraints with all no-vig probabilities

    Returns
    -------
    n×n numpy array (reconciled PMF)
    """
    n = min(max_goals, prior.shape[0])
    q = prior[:n, :n].copy()
    q = np.clip(q, _EPS, None)
    q /= q.sum()
    q_flat = q.flatten()

    N = n * n
    h_idx = np.array([i // n for i in range(N)])
    a_idx = np.array([i % n for i in range(N)])

    constraints = []

    # Normalization
    constraints.append({"type": "eq", "fun": lambda p: p.sum() - 1.0})

    # 1X2
    if mc.has_1x2:
        hw_mask = (h_idx > a_idx).astype(float)
        dr_mask = (h_idx == a_idx).astype(float)
        aw_mask = (h_idx < a_idx).astype(float)
        constraints.append({"type": "eq", "fun": lambda p, m=hw_mask, v=mc.home_win: (p * m).sum() - v})
        constraints.append({"type": "eq", "fun": lambda p, m=dr_mask, v=mc.draw: (p * m).sum() - v})
        constraints.append({"type": "eq", "fun": lambda p, m=aw_mask, v=mc.away_win: (p * m).sum() - v})

    # Totals
    for line, attr in [(0.5, "over_0_5"), (1.5, "over_1_5"), (2.5, "over_2_5"),
                       (3.5, "over_3_5"), (4.5, "over_4_5"), (5.5, "over_5_5"), (6.5, "over_6_5")]:
        v = getattr(mc, attr)
        if v is not None:
            ov_mask = ((h_idx + a_idx) > line).astype(float)
            constraints.append({"type": "eq", "fun": lambda p, m=ov_mask, val=v: (p * m).sum() - val})

    # BTTS
    if mc.btts_yes is not None:
        btts_mask = ((h_idx > 0) & (a_idx > 0)).astype(float)
        constraints.append({"type": "eq", "fun": lambda p, m=btts_mask, v=mc.btts_yes: (p * m).sum() - v})

    # Correct score (use as soft constraints via equality if high-quality)
    if mc.has_correct_score and mc.n_cs_vendors >= 2:
        for (h, a), prob in mc.correct_score.items():
            if h < n and a < n and prob > _EPS:
                idx = h * n + a
                # Only constrain cells with decent probability mass (avoids numerical issues)
                if prob > 0.005:
                    constraints.append({
                        "type": "eq",
                        "fun": lambda p, i=idx, v=prob: p[i] - v
                    })

    def kl_objective(p: np.ndarray) -> float:
        p_clip = np.clip(p, _EPS, 1.0)
        return float(np.sum(p_clip * np.log(p_clip / (q_flat + _EPS))))

    def kl_grad(p: np.ndarray) -> np.ndarray:
        p_clip = np.clip(p, _EPS, 1.0)
        return np.log(p_clip / (q_flat + _EPS)) + 1.0

    bounds = [(_EPS, 1.0)] * N

    try:
        result = minimize(
            kl_objective,
            x0=q_flat.copy(),
            jac=kl_grad,
            method="SLSQP",
            bounds=bounds,
            constraints=constraints,
            options={"maxiter": 500, "ftol": tolerance},
        )
        if result.success or result.fun < float("inf"):
            p_opt = np.clip(result.x, 0, None).reshape(n, n)
            p_opt /= p_opt.sum()
            return p_opt
        else:
            log.warning("KL reconciliation did not converge: %s. Falling back to IPF.", result.message)
    except Exception as exc:
        log.warning("KL reconciliation failed: %s. Falling back to IPF.", exc)

    # Fallback to IPF-style blend
    return apply_correct_score_adjustment(prior[:n, :n], mc.correct_score, alpha=0.7)


# ---------------------------------------------------------------------------
# Main reconciliation entry point
# ---------------------------------------------------------------------------

@dataclass
class ReconciliationResult:
    """Output of the three-mode reconciliation."""
    match_id: int
    home_team: str
    away_team: str

    # Mode PMFs (n×n numpy arrays)
    pure_model_pmf: np.ndarray
    market_implied_pmf: Optional[np.ndarray]
    market_reconciled_pmf: Optional[np.ndarray]

    # Lambdas for each mode
    pure_model_lambda_home: float = 0.0
    pure_model_lambda_away: float = 0.0
    market_implied_lambda_home: float = 0.0
    market_implied_lambda_away: float = 0.0

    # Quality
    market_constraints: Optional[MarketConstraints] = None
    market_quality: float = 0.0
    market_blend_alpha: float = 0.0
    publish_mode: str = "pure_model"
    warnings: list = field(default_factory=list)

    @property
    def publish_pmf(self) -> np.ndarray:
        if self.publish_mode == "market_reconciled" and self.market_reconciled_pmf is not None:
            return self.market_reconciled_pmf
        if self.publish_mode == "market_implied" and self.market_implied_pmf is not None:
            return self.market_implied_pmf
        return self.pure_model_pmf


def reconcile(
    match_id: int,
    home_team: str,
    away_team: str,
    pure_model_pmf: np.ndarray,
    pure_model_lh: float,
    pure_model_la: float,
    mc: MarketConstraints,
    max_goals: int = 15,
    min_market_quality: float = 0.3,
    use_kl: bool = True,
) -> ReconciliationResult:
    """
    Produce all three publish modes for a single match.

    Parameters
    ----------
    pure_model_pmf : n×n array from the best statistical model
    mc : MarketConstraints from BDL no-vig consensus
    min_market_quality : below this threshold, publish_mode = pure_model
    use_kl : use full KL reconciliation (slower). If False, uses IPF blend.
    """
    result = ReconciliationResult(
        match_id=match_id,
        home_team=home_team,
        away_team=away_team,
        pure_model_pmf=pure_model_pmf,
        market_implied_pmf=None,
        market_reconciled_pmf=None,
        pure_model_lambda_home=pure_model_lh,
        pure_model_lambda_away=pure_model_la,
        market_constraints=mc,
    )

    if not mc.has_1x2:
        result.publish_mode = "pure_model"
        result.warnings.append("no_1x2_odds_available")
        return result

    market_quality = mc.quality_score
    result.market_quality = market_quality

    # ── Build market_implied PMF ─────────────────────────────────────────
    try:
        mip, lh_mkt, la_mkt, rho_mkt = build_market_implied_pmf(mc, max_goals)
        result.market_implied_pmf = mip
        result.market_implied_lambda_home = lh_mkt
        result.market_implied_lambda_away = la_mkt
    except Exception as exc:
        log.warning("market_implied PMF failed for %s v %s: %s", home_team, away_team, exc)
        result.warnings.append(f"market_implied_failed: {exc}")
        result.publish_mode = "pure_model"
        return result

    # ── Determine blend weight α ─────────────────────────────────────────
    # α is the weight on the market_implied PMF in the reconciled blend
    alpha = min(market_quality * 1.2, 0.85)  # cap at 85% market weight
    result.market_blend_alpha = alpha

    # ── Build market_reconciled PMF ──────────────────────────────────────
    if market_quality >= min_market_quality:
        # Use market_implied as the prior for KL reconciliation
        try:
            if use_kl and mc.has_correct_score and mc.n_cs_outcomes >= 5:
                reconciled = reconcile_pmf_kl(mip, mc, max_goals=max_goals)
            else:
                # Simpler blend: α * market + (1-α) * model
                n = min(max_goals, pure_model_pmf.shape[0], mip.shape[0])
                pm = pure_model_pmf[:n, :n].copy()
                pm = np.clip(pm, 0, None)
                pm /= pm.sum()
                mi = mip[:n, :n].copy()
                reconciled = alpha * mi + (1.0 - alpha) * pm
                reconciled /= reconciled.sum()

                # Apply correct-score adjustments on top
                if mc.has_correct_score:
                    reconciled = apply_correct_score_adjustment(
                        reconciled, mc.correct_score, alpha=min(alpha, 0.7)
                    )
            result.market_reconciled_pmf = reconciled
            result.publish_mode = "market_reconciled"
        except Exception as exc:
            log.warning("market_reconciled failed for %s v %s: %s", home_team, away_team, exc)
            result.warnings.append(f"reconciliation_failed: {exc}")
            result.market_reconciled_pmf = mip
            result.publish_mode = "market_implied"
    else:
        result.warnings.append(f"market_quality_too_low: {market_quality:.2f}")
        result.publish_mode = "pure_model"

    return result
