"""
Market reconciliation engine: three publish modes.

Modes
-----
pure_model
    Composite team-prior + parametric goal model. No market data.

market_implied
    PMF built entirely from BDL no-vig consensus via goal_expectancy_extended.
    This is a clean Poisson-shaped PMF that already satisfies 1X2 + O/U.

market_reconciled   ← DEFAULT PUBLISH MODE when BDL odds exist
    Linear blend:  α * market_implied + (1-α) * composite_model
    where α scales with market quality (0.85 max when 6 vendors + CS data).
    Correct-score cells gently adjusted with IPF (not SLSQP equality constraints).

IMPORTANT: We do NOT use SLSQP equality-constraint KL optimization.
Reason: market_implied already satisfies 1X2/totals by construction.
Running SLSQP to minimize KL(P||market_implied) subject to those same
constraints is numerically degenerate — SLSQP finds corner solutions that
deposit probability mass in impossible cells (e.g. 4-9, 11-5).

Instead we use:
  1. Linear blend (numerically stable, always valid PMF)
  2. Gentle IPF for correct-score cells (bounded, monotone convergent)
  3. Post-blend sanity check (impossible-score guard)
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field

import numpy as np

log = logging.getLogger(__name__)

_EPS = 1e-9


# ---------------------------------------------------------------------------
# Market constraints container
# ---------------------------------------------------------------------------

@dataclass
class MarketConstraints:
    """All no-vig probabilities extracted from BDL for one match."""

    # ── 1X2 ─────────────────────────────────────────────────────────────
    home_win: float | None = None
    draw: float | None = None
    away_win: float | None = None
    n_vendors_1x2: int = 0

    # ── Totals (no-vig over probabilities) ──────────────────────────────
    over_0_5: float | None = None
    over_1_5: float | None = None
    over_2_5: float | None = None
    over_3_5: float | None = None
    over_4_5: float | None = None
    over_5_5: float | None = None
    over_6_5: float | None = None

    # ── BTTS ─────────────────────────────────────────────────────────────
    btts_yes: float | None = None
    btts_no: float | None = None

    # ── Draw no bet ─────────────────────────────────────────────────────
    dnb_home: float | None = None
    dnb_away: float | None = None

    # ── Double chance ────────────────────────────────────────────────────
    dc_1x: float | None = None
    dc_x2: float | None = None
    dc_12: float | None = None

    # ── Correct score {(h, a): prob} ─────────────────────────────────────
    correct_score: dict = field(default_factory=dict)
    n_cs_vendors: int = 0
    n_cs_outcomes: int = 0

    # ── Asian handicap market-implied probabilities ───────────────────────
    # Key: float line (e.g. -1.0), value: no-vig home-side cover probability
    ah_market: dict = field(default_factory=dict)

    # ── Odds freshness ────────────────────────────────────────────────────
    odds_timestamp: str | None = None
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

    # ── Spread/AH from main odds table ────────────────────────────────────
    ah_map: dict[float, list[float]] = {}  # line → [no-vig home cover prob, ...]
    for _, row in mrows.iterrows():
        try:
            sv = row.get("spread_home_value")
            so = row.get("spread_home_odds")
            if sv is None or so is None:
                continue
            line = float(sv)
            # Convert American spread odds to implied home cover prob
            p_home = _decimal_to_prob(_american_to_decimal(float(so)))
            # Away side: no direct away odds in main table; approximate as 1 - p_home
            # (whole-ball lines would have push but we treat as two-way for simplicity)
            p_away = 1.0 - p_home
            stripped = _strip_vig_multiplicative([p_home, p_away])
            if line not in ah_map:
                ah_map[line] = []
            ah_map[line].append(stripped[0])
        except Exception:
            continue
    if ah_map:
        mc.ah_market = {line: float(np.mean(probs)) for line, probs in ah_map.items()}

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
                1.0 / avg_dec
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
    snapshot_df=None,
) -> tuple[np.ndarray, float, float, float]:
    """
    Build a joint PMF from market constraints using goal_expectancy_extended.

    Returns (pmf_grid, lambda_home, lambda_away, rho)
    """
    if snapshot_df is not None:
        try:
            from wc2026.markets.current_market_pmf import build_market_pmf_full
            result = build_market_pmf_full(snapshot_df)
            if result is not None:
                return result.pmf, result.home_lambda, result.away_lambda, result.rho
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning("CurrentMarketPMF failed, using legacy: %s", e)

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
        from penaltyblog.models import create_dixon_coles_grid, goal_expectancy_extended
        if over_25 is not None:
            result = goal_expectancy_extended(hw, dr, aw, over_25, under_25,
                                              objective="cross_entropy")
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
            result = goal_expectancy(hw, dr, aw, objective="cross_entropy")
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

def _sanitize_pmf(pmf: np.ndarray, max_plausible_goals: int = 8) -> np.ndarray:
    """
    Guard against impossible high-score artifacts.

    Any cell (h, a) where h+a >= max_plausible_goals is capped at a tiny
    epsilon and the freed mass is redistributed proportionally to cells with
    total goals <= 4 (the bulk of soccer scores).

    This is a safety check, not the primary mechanism. A well-built PMF should
    not need this correction. If it fires, it indicates an upstream bug.
    """
    p = pmf.copy()
    n = p.shape[0]
    # Cap probability for implausible scores (total >= max_plausible_goals)
    implausible_threshold = max_plausible_goals
    cap_value = 1e-6
    freed_mass = 0.0
    for h in range(n):
        for a in range(n):
            if h + a >= implausible_threshold and p[h, a] > cap_value:
                freed_mass += p[h, a] - cap_value
                p[h, a] = cap_value
    # Redistribute freed mass to low-score cells (total goals 0-4)
    if freed_mass > 0:
        low_score_mask = np.zeros((n, n), dtype=bool)
        for h in range(n):
            for a in range(n):
                if h + a <= 4:
                    low_score_mask[h, a] = True
        low_total = p[low_score_mask].sum()
        if low_total > _EPS:
            p[low_score_mask] += freed_mass * (p[low_score_mask] / low_total)
    p = np.clip(p, 0, None)
    s = p.sum()
    if s > _EPS:
        p /= s
    return p


def reconcile_pmf_kl(
    prior: np.ndarray,
    mc: MarketConstraints,
    max_goals: int = 15,
    tolerance: float = 1e-6,
) -> np.ndarray:
    """
    DEPRECATED: Formerly used SLSQP to minimize KL(P||prior) with equality
    constraints.  This caused degenerate solutions (impossible high-score
    cells) because market_implied already satisfies 1X2/totals constraints,
    making the optimization numerically degenerate.

    Now delegates to the stable linear-blend approach via reconcile().
    Kept for backward-compatibility of direct callers.
    """
    log.warning(
        "reconcile_pmf_kl called directly — SLSQP removed. "
        "Using stable linear-blend + IPF instead."
    )
    # Apply CS adjustment only
    n = min(max_goals, prior.shape[0])
    p = prior[:n, :n].copy()
    p = np.clip(p, 0, None)
    s = p.sum()
    if s > _EPS:
        p /= s
    if mc.has_correct_score and mc.n_cs_outcomes >= 3:
        cs_alpha = 0.3 if mc.n_cs_vendors <= 1 else 0.5
        p = apply_correct_score_adjustment(p, mc.correct_score, alpha=cs_alpha)
    return _sanitize_pmf(p)


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
    market_implied_pmf: np.ndarray | None
    market_reconciled_pmf: np.ndarray | None

    # Lambdas for each mode
    pure_model_lambda_home: float = 0.0
    pure_model_lambda_away: float = 0.0
    market_implied_lambda_home: float = 0.0
    market_implied_lambda_away: float = 0.0

    # Quality
    market_constraints: MarketConstraints | None = None
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
    use_kl: bool = True,  # kept for API compatibility; SLSQP is never used
) -> ReconciliationResult:
    """
    Produce all three publish modes for a single match.

    market_reconciled strategy (stable linear blend):
      1. Build market_implied PMF via goal_expectancy_extended (already satisfies 1X2/totals)
      2. Blend:  reconciled = α * market_implied + (1-α) * composite_model
         where α = min(market_quality * 0.70, 0.45)
         (cap at 0.45 preserves ≥55% model signal for CLV generation)
      3. Apply gentle IPF for correct-score cells (alpha 0.3 for 1 vendor, 0.5 for 2+)
      4. Sanity-check: cap impossible-score cells (total goals >= 9) to 1e-6

    We never run SLSQP equality-constraint optimization. It is numerically
    degenerate when the prior already satisfies the constraints and produces
    artifacts like P(4-9)=0.026.

    Parameters
    ----------
    pure_model_pmf  n×n composite_rating_pmf (the model prior)
    mc              MarketConstraints from BDL no-vig consensus
    use_kl          kept for API compatibility, ignored
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

    # ── 1. Build market_implied PMF ──────────────────────────────────────
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

    # ── 2. Determine blend weight α ──────────────────────────────────────
    # Cap at 0.25: preserves ≥75% independent model signal in the published PMF.
    # Previous cap of 0.45 still allowed too much market contamination of edge signals.
    # At 0.25 the published prediction retains dominant model signal for CLV generation.
    # Formula: alpha scales with market quality up to 0.25 max.
    alpha = min(market_quality * 0.70, 0.25)
    result.market_blend_alpha = alpha

    if market_quality < min_market_quality:
        result.warnings.append(f"market_quality_too_low: {market_quality:.2f}")
        result.publish_mode = "pure_model"
        return result

    # ── 3. Run all reconciliation methods and select best ─────────────────
    try:
        from .core_grid_reconcile import compare_reconciliation_methods

        comparison = compare_reconciliation_methods(
            prior_pmf=pure_model_pmf,
            mc=mc,
            max_goals=max_goals,
            blend_alpha=alpha,
            cs_n_vendors=mc.n_cs_vendors,
        )

        reconciled = comparison["best_pmf"]
        best_method = comparison["best_method"]
        method_scores = comparison["method_scores"]

        # Attach comparison metadata for reporting
        result._comparison = comparison
        result._best_reconciliation_method = best_method

        if best_method != "blend":
            log.info(
                "CoreGrid SLSQP selected for %s v %s (slsqp_score=%.4f blend_score=%.4f)",
                home_team, away_team,
                method_scores.get("slsqp_core", float("inf")),
                method_scores.get("blend", float("inf")),
            )

        # ── Final sanity guard ────────────────────────────────────────────
        reconciled = _sanitize_pmf(reconciled, max_plausible_goals=8)

        result.market_reconciled_pmf = reconciled
        result.publish_mode = "market_reconciled"

    except Exception as exc:
        log.warning("market_reconciled failed for %s v %s: %s", home_team, away_team, exc)
        result.warnings.append(f"reconciliation_failed: {exc}")
        # Fallback to safe blend
        try:
            n = min(max_goals, pure_model_pmf.shape[0], mip.shape[0])
            pm = np.clip(pure_model_pmf[:n, :n], 0, None)
            pm /= pm.sum()
            mi = np.clip(mip[:n, :n], 0, None)
            mi /= mi.sum()
            reconciled = alpha * mi + (1.0 - alpha) * pm
            reconciled /= reconciled.sum()
            reconciled = _sanitize_pmf(reconciled)
            result.market_reconciled_pmf = reconciled
            result.publish_mode = "market_reconciled"
            result.warnings.append("used_fallback_blend")
        except Exception:
            result.market_reconciled_pmf = mip
            result.publish_mode = "market_implied"

    return result
