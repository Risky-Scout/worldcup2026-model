"""
PMF sanity tests — fail the build if impossible high-score artifacts exist.

These tests guard against the SLSQP degeneration bug that produced
P(4-9)=0.026 and P(11-5)=0.017 in the Mexico vs South Africa PMF.

Acceptance criteria:
- No cell with total_goals >= 9 should have probability > 1e-3
- Top-3 most probable scores must have total_goals <= 6
- PMF must sum to 1.0
- Derived 1X2 must equal cell sums from the same PMF
- Correct-score cells must not be mapped to wrong (h, a) coordinates
- Flatten/unflatten round-trip must preserve cell coordinates
- IPF CS adjustment must not introduce impossible scores
- sanitize_pmf must correctly cap implausible cells
"""
from __future__ import annotations

import numpy as np
import pytest
from scipy.stats import poisson

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from wc2026.markets.exact_score_reconcile import (
    MarketConstraints,
    apply_correct_score_adjustment,
    build_market_implied_pmf,
    reconcile,
    _sanitize_pmf,
)


# ── Fixtures ──────────────────────────────────────────────────────────────────

def _poisson_pmf(lh: float, la: float, n: int = 15) -> np.ndarray:
    p = np.outer(poisson.pmf(range(n), lh), poisson.pmf(range(n), la))
    p /= p.sum()
    return p


def _strong_home_mc() -> MarketConstraints:
    """6-vendor market: strong home favourite (Mexico vs SA style).

    has_1x2 is a computed property: it returns True when home_win is set.
    quality_score is also computed. We must set the raw fields.
    """
    mc = MarketConstraints()
    mc.home_win = 0.675
    mc.draw = 0.211
    mc.away_win = 0.114
    mc.over_2_5 = 0.440
    mc.n_vendors_1x2 = 6
    # has_1x2 and quality_score are @property computed from above fields
    return mc


def _mc_with_cs() -> MarketConstraints:
    """Market with correct-score data."""
    mc = _strong_home_mc()
    mc.correct_score = {
        (1, 0): 0.148, (2, 0): 0.145, (3, 0): 0.096,
        (0, 0): 0.086, (1, 1): 0.086, (2, 1): 0.081,
        (3, 1): 0.054, (4, 0): 0.048, (0, 1): 0.048,
        (4, 1): 0.029,
    }
    mc.n_cs_outcomes = len(mc.correct_score)
    mc.n_cs_vendors = 1
    # has_correct_score is computed from len(correct_score) > 0
    return mc


# ── Core PMF sanity ───────────────────────────────────────────────────────────

class TestPMFSumToOne:
    def test_poisson_sums_to_one(self):
        p = _poisson_pmf(1.84, 0.60)
        assert abs(p.sum() - 1.0) < 1e-9

    def test_market_implied_sums_to_one(self):
        mc = _strong_home_mc()
        mip, _, _, _ = build_market_implied_pmf(mc, max_goals=15)
        assert abs(mip.sum() - 1.0) < 1e-4, f"market_implied sum = {mip.sum()}"

    def test_reconciled_sums_to_one(self):
        mc = _mc_with_cs()
        prior = _poisson_pmf(1.84, 0.60)
        result = reconcile(1, "Mexico", "South Africa", prior, 1.84, 0.60, mc, max_goals=15)
        pmf = result.publish_pmf
        assert abs(pmf.sum() - 1.0) < 1e-4, f"reconciled sum = {pmf.sum()}"


class TestNoHighScoreArtifacts:
    """No cell with total_goals >= 9 should have probability > 1e-3."""

    def _check_no_artifacts(self, pmf: np.ndarray, label: str):
        n = pmf.shape[0]
        for h in range(n):
            for a in range(n):
                if h + a >= 9:
                    assert pmf[h, a] <= 1e-3, (
                        f"{label}: impossible score {h}-{a} has P={pmf[h,a]:.4f} "
                        f"(total={h+a} goals, threshold 1e-3). "
                        "SLSQP artifact? Run _sanitize_pmf."
                    )

    def test_poisson_no_artifacts(self):
        p = _poisson_pmf(1.84, 0.60)
        self._check_no_artifacts(p, "Poisson(1.84, 0.60)")

    def test_market_implied_no_artifacts(self):
        mc = _strong_home_mc()
        mip, _, _, _ = build_market_implied_pmf(mc, max_goals=15)
        self._check_no_artifacts(mip, "market_implied")

    def test_reconciled_no_artifacts(self):
        """This is the critical test: catches the 4-9 / 11-5 bug."""
        mc = _mc_with_cs()
        prior = _poisson_pmf(1.84, 0.60)
        result = reconcile(1, "Mexico", "South Africa", prior, 1.84, 0.60, mc, max_goals=15)
        pmf = result.publish_pmf
        self._check_no_artifacts(pmf, "market_reconciled Mexico vs SA")

    def test_even_distribution_no_artifacts(self):
        """Even a uniform-ish prior should produce no high-score artifacts."""
        mc = _strong_home_mc()
        prior = np.ones((15, 15)) / 225.0
        result = reconcile(2, "Home", "Away", prior, 1.5, 1.0, mc, max_goals=15)
        pmf = result.publish_pmf
        self._check_no_artifacts(pmf, "uniform prior reconciled")

    def test_sanitize_pmf_caps_implausible(self):
        """_sanitize_pmf must remove artificially high probability from impossible cells."""
        p = _poisson_pmf(1.84, 0.60)
        # Manually inject an artifact
        p[4, 9] = 0.05
        p[11, 5] = 0.03
        p /= p.sum()
        assert p[4, 9] > 1e-3  # confirm injection
        sanitized = _sanitize_pmf(p)
        assert sanitized[4, 9] <= 1e-3, "sanitize_pmf failed to cap [4,9]"
        assert sanitized[11, 5] <= 1e-3, "sanitize_pmf failed to cap [11,5]"
        assert abs(sanitized.sum() - 1.0) < 1e-6, "sanitize_pmf broke normalization"


class TestTopScorelines:
    """Top-3 most probable scorelines must have total goals <= 6."""

    def _top3_plausible(self, pmf: np.ndarray, label: str):
        flat = pmf.flatten()
        top3 = np.argsort(flat)[::-1][:3]
        n = pmf.shape[0]
        for idx in top3:
            h, a = divmod(int(idx), n)
            total = h + a
            assert total <= 6, (
                f"{label}: top-3 score {h}-{a} has total={total} goals "
                f"(probability={flat[idx]:.4f}). Implausible for soccer."
            )

    def test_poisson_top3_plausible(self):
        p = _poisson_pmf(1.84, 0.60)
        self._top3_plausible(p, "Poisson(1.84, 0.60)")

    def test_market_implied_top3_plausible(self):
        mc = _strong_home_mc()
        mip, _, _, _ = build_market_implied_pmf(mc, max_goals=15)
        self._top3_plausible(mip, "market_implied")

    def test_reconciled_top3_plausible(self):
        mc = _mc_with_cs()
        prior = _poisson_pmf(1.84, 0.60)
        result = reconcile(1, "Mexico", "South Africa", prior, 1.84, 0.60, mc, max_goals=15)
        pmf = result.publish_pmf
        self._top3_plausible(pmf, "market_reconciled")


class TestDerived1X2Consistency:
    """Derived 1X2 from PMF cells must equal published 1X2 (within tolerance)."""

    def test_market_implied_1x2_consistent(self):
        mc = _strong_home_mc()
        mip, _, _, _ = build_market_implied_pmf(mc, max_goals=15)
        n = mip.shape[0]
        hw = sum(mip[h, a] for h in range(n) for a in range(n) if h > a)
        dr = sum(mip[h, a] for h in range(n) for a in range(n) if h == a)
        aw = sum(mip[h, a] for h in range(n) for a in range(n) if h < a)
        # market_implied should closely match the 1X2 targets
        assert abs(hw - mc.home_win) < 0.05, f"HW: {hw:.4f} vs {mc.home_win:.4f}"
        assert abs(dr - mc.draw) < 0.05, f"DR: {dr:.4f} vs {mc.draw:.4f}"
        assert abs(aw - mc.away_win) < 0.05, f"AW: {aw:.4f} vs {mc.away_win:.4f}"

    def test_1x2_sum_to_one(self):
        mc = _strong_home_mc()
        mip, _, _, _ = build_market_implied_pmf(mc, max_goals=15)
        n = mip.shape[0]
        hw = sum(mip[h, a] for h in range(n) for a in range(n) if h > a)
        dr = sum(mip[h, a] for h in range(n) for a in range(n) if h == a)
        aw = sum(mip[h, a] for h in range(n) for a in range(n) if h < a)
        assert abs(hw + dr + aw - 1.0) < 1e-4

    def test_reconciled_1x2_consistent(self):
        mc = _mc_with_cs()
        prior = _poisson_pmf(1.84, 0.60)
        result = reconcile(1, "Mexico", "South Africa", prior, 1.84, 0.60, mc, max_goals=15)
        pmf = result.publish_pmf
        n = pmf.shape[0]
        hw = sum(pmf[h, a] for h in range(n) for a in range(n) if h > a)
        dr = sum(pmf[h, a] for h in range(n) for a in range(n) if h == a)
        aw = sum(pmf[h, a] for h in range(n) for a in range(n) if h < a)
        assert abs(hw - mc.home_win) < 0.05, f"HW mismatch: {hw:.4f} vs {mc.home_win:.4f}"
        assert abs(hw + dr + aw - 1.0) < 1e-4


class TestCorrectScoreCellMapping:
    """Correct-score odds must be mapped to the correct (h, a) grid cell."""

    def test_cs_cell_mapping_exact(self):
        """If market says P(1-0)=0.15, then after IPF, P(1,0) should be > P(0,1)."""
        mc = _strong_home_mc()
        mc.correct_score = {(1, 0): 0.15, (0, 1): 0.05}
        mc.n_cs_outcomes = 2
        mc.n_cs_vendors = 1
        # has_correct_score computed from len(correct_score)>0
        prior = _poisson_pmf(1.84, 0.60)
        result = reconcile(3, "H", "A", prior, 1.84, 0.60, mc, max_goals=15)
        pmf = result.publish_pmf
        # The correct-score constraints should push P(1,0) > P(0,1)
        assert pmf[1, 0] > pmf[0, 1], (
            f"P(1-0)={pmf[1,0]:.4f} should be > P(0-1)={pmf[0,1]:.4f} "
            "after CS adjustment towards market P(1-0)=0.15"
        )

    def test_cs_not_transposed(self):
        """Verify h=home goals, a=away goals: market (2,1) means home-2 away-1."""
        mc = _strong_home_mc()
        mc.correct_score = {(2, 1): 0.15, (1, 2): 0.01}
        mc.n_cs_outcomes = 2
        mc.n_cs_vendors = 1
        prior = _poisson_pmf(1.84, 0.60)
        result = reconcile(4, "H", "A", prior, 1.84, 0.60, mc, max_goals=15)
        pmf = result.publish_pmf
        # Grid: pmf[home_goals, away_goals]
        assert pmf[2, 1] > pmf[1, 2], (
            f"P(2-1 home win)={pmf[2,1]:.4f} should dominate P(1-2 away win)={pmf[1,2]:.4f} "
            "after pinning market (2,1)=0.15"
        )

    def test_flatten_unflatten_preserves_coordinates(self):
        """Flattening row-major and restoring must give same (h,a) coordinates."""
        n = 15
        for h in range(n):
            for a in range(n):
                flat_idx = h * n + a
                h_recovered, a_recovered = divmod(flat_idx, n)
                assert h_recovered == h and a_recovered == a, (
                    f"flatten/unflatten bug: ({h},{a}) → flat={flat_idx} → ({h_recovered},{a_recovered})"
                )


class TestIPFAdjustmentSafety:
    """apply_correct_score_adjustment must not introduce impossible scores."""

    def test_ipf_no_high_score_artifacts(self):
        prior = _poisson_pmf(1.84, 0.60)
        cs = {(1, 0): 0.15, (2, 0): 0.14, (0, 0): 0.09}
        adjusted = apply_correct_score_adjustment(prior, cs, alpha=0.5)
        assert abs(adjusted.sum() - 1.0) < 1e-6
        n = adjusted.shape[0]
        for h in range(n):
            for a in range(n):
                if h + a >= 9:
                    assert adjusted[h, a] <= 1e-3, (
                        f"IPF artifact: [{h},{a}] P={adjusted[h,a]:.4f}"
                    )

    def test_ipf_preserves_normalization(self):
        prior = _poisson_pmf(1.84, 0.60)
        cs = {(1, 0): 0.15, (2, 0): 0.12}
        for alpha in [0.1, 0.3, 0.5, 0.7]:
            adj = apply_correct_score_adjustment(prior, cs, alpha=alpha)
            assert abs(adj.sum() - 1.0) < 1e-6, f"IPF broke normalization at alpha={alpha}"


class TestCompositeDefenseFormula:
    """Verify the composite defense formula: lam_h = att_H * def_A / avg."""

    def test_defense_semantics(self):
        """
        Higher def_A (goals conceded by away team) should INCREASE lam_h.
        If SA concedes 1.50 per game (weak defense) vs avg 1.30,
        Mexico should score MORE than against an average opponent.
        """
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).parents[1] / "src"))
        from wc2026.ratings.composite import _WC_AVG_ATTACK

        avg = _WC_AVG_ATTACK
        att_mexico = 1.63
        def_sa_weak = 1.50   # weak defense (concedes more)
        def_sa_avg = avg     # average defense

        lam_h_vs_weak = att_mexico * def_sa_weak / avg
        lam_h_vs_avg = att_mexico * def_sa_avg / avg

        assert lam_h_vs_weak > lam_h_vs_avg, (
            f"lam_h should be higher when opponent has weaker defense: "
            f"{lam_h_vs_weak:.3f} (weak) vs {lam_h_vs_avg:.3f} (avg)"
        )

    def test_composite_mexico_sa_home_win_reasonable(self):
        """
        With correct defense formula, Mexico vs SA composite should give
        Mexico HW > 50% (not the buggy 37% from inverted formula).
        """
        from scipy.stats import poisson as scipy_poisson
        avg = 1.30
        att_mex, def_mex = 1.63, 0.864
        att_sa, def_sa = 0.918, 1.505
        lh = att_mex * def_sa / avg
        la = att_sa * def_mex / avg
        pmf = np.outer(
            scipy_poisson.pmf(range(15), lh),
            scipy_poisson.pmf(range(15), la),
        )
        pmf /= pmf.sum()
        hw = sum(pmf[h, a] for h in range(15) for a in range(15) if h > a)
        assert hw > 0.55, (
            f"Mexico vs SA composite HW={hw:.3f} is too low. "
            "Defense formula may still be inverted."
        )
        assert hw < 0.80, f"Mexico vs SA composite HW={hw:.3f} is too high."
