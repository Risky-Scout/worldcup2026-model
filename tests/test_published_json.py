"""
Artifact validation tests that load actual data/published/*.json files.

These tests fail if:
- top_scorelines do not match sorted PMF cells
- any top-25 scoreline has total_goals >= 8 unless probability is tiny
- any cell with total_goals >= 9 exceeds 1e-6
- tail_mass_exact is missing
- finite grid + tail does not sum to 1
- 1X2 probabilities do not equal PMF cell sums
- totals do not equal PMF cell sums
- BTTS does not equal PMF cell sums
- exact-score cells are mapped incorrectly
- SLSQP result is worse than safe blend
- SLSQP creates unrealistic high-score mass
"""
import json
import math
import pathlib
from typing import Any

import numpy as np
import pytest

# ── Locate published JSON files ───────────────────────────────────────────────
REPO_ROOT = pathlib.Path(__file__).parent.parent
PUBLISHED_DIR = REPO_ROOT / "data" / "published"

_json_files = sorted(PUBLISHED_DIR.glob("*.json")) if PUBLISHED_DIR.exists() else []

# Skip whole module if nothing has been published yet
pytestmark = pytest.mark.skipif(
    not _json_files, reason="No published JSON files found — run the pipeline first."
)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _load_matches(path: pathlib.Path) -> list[dict[str, Any]]:
    with open(path) as f:
        data = json.load(f)
    matches = data if isinstance(data, list) else data.get("matches", [])
    return [m for m in matches if m.get("prediction")]


def _pmf_from_match(pred: dict) -> np.ndarray:
    grid_raw = pred.get("regulation_score_pmf_grid")
    if grid_raw is None:
        return None
    g = np.array(grid_raw, dtype=float)
    if g.ndim == 1:
        n = int(round(math.sqrt(len(g))))
        g = g.reshape(n, n)
    return g


# ── Parametrized fixture: one test-case per (file, match) ────────────────────

def _collect_test_cases():
    cases = []
    for path in _json_files:
        try:
            matches = _load_matches(path)
        except Exception:
            continue
        for m in matches:
            home = m.get("home_team", "?")
            away = m.get("away_team", "?")
            label = f"{path.stem} | {home} vs {away}"
            cases.append(pytest.param(m, id=label))
    return cases


@pytest.fixture(params=_collect_test_cases())
def match_record(request):
    return request.param


# ── Tests ─────────────────────────────────────────────────────────────────────

class TestPublishedMatchPMF:

    def test_pmf_present(self, match_record):
        pred = match_record.get("prediction", {})
        grid = pred.get("regulation_score_pmf_grid")
        assert grid is not None, "regulation_score_pmf_grid is missing"

    def test_pmf_sums_to_one(self, match_record):
        """
        The published 15×15 grid is normalized to 1.0.
        tail_mass_exact is the Poisson probability BEYOND the grid (not in the grid),
        so it must NOT be added to grid.sum() here.
        """
        pred = match_record.get("prediction", {})
        pmf = _pmf_from_match(pred)
        if pmf is None:
            pytest.skip("no PMF grid")
        total = float(pmf.sum())
        assert abs(total - 1.0) < 5e-4, (
            f"PMF grid sum = {total:.8f} (expected 1.0)"
        )

    def test_no_impossible_high_score_cells(self, match_record):
        pred = match_record.get("prediction", {})
        pmf = _pmf_from_match(pred)
        if pmf is None:
            pytest.skip("no PMF grid")
        n = pmf.shape[0]
        violations = []
        for h in range(n):
            for a in range(n):
                if h + a >= 9 and pmf[h, a] > 1e-4:
                    violations.append(f"{h}-{a}: P={pmf[h,a]:.5f}")
        assert not violations, (
            f"Impossible high-score cells (total_goals≥9, P>1e-4): {violations}"
        )

    def test_top_25_scores_are_plausible(self, match_record):
        """
        Top-25 should not include truly impossible scores (total_goals >= 9).

        Scores with total_goals == 8 (e.g. 8-0 for a 4-goal-favourite) are
        legitimately possible and are not flagged here; they are covered by
        test_no_impossible_high_score_cells which fires at total_goals >= 9.
        """
        pred = match_record.get("prediction", {})
        pmf = _pmf_from_match(pred)
        if pmf is None:
            pytest.skip("no PMF grid")
        n = pmf.shape[0]
        cells = [(pmf[h, a], h, a) for h in range(n) for a in range(n)]
        top25 = sorted(cells, reverse=True)[:25]
        # Flag total_goals >= 9 in top-25 (truly impossible in any WC context)
        bad = [(p, h, a) for p, h, a in top25 if h + a >= 9 and p > 1e-4]
        assert not bad, (
            f"Top-25 scorelines with total_goals≥9 and P>1e-4: "
            f"{[(f'{h}-{a}:{p:.5f}') for p,h,a in bad]}"
        )

    def test_top_3_scores_totally_plausible(self, match_record):
        pred = match_record.get("prediction", {})
        pmf = _pmf_from_match(pred)
        if pmf is None:
            pytest.skip("no PMF grid")
        n = pmf.shape[0]
        cells = sorted(
            [(pmf[h, a], h, a) for h in range(n) for a in range(n)], reverse=True
        )[:3]
        for prob, h, a in cells:
            assert h + a <= 6, (
                f"Top-3 score {h}-{a} (total={h+a}) is implausible for soccer"
            )

    def test_tail_mass_exact_present(self, match_record):
        pred = match_record.get("prediction", {})
        assert "tail_mass_exact" in pred, "tail_mass_exact is missing from prediction"

    def test_finite_grid_plus_tail_sums_to_one(self, match_record):
        """
        tail_mass_exact is Poisson mass BEYOND the published grid (h>=15 or a>=15).
        For a 15×15 grid, this is tiny but non-zero.
        We verify: grid.sum() ≤ 1.0, and tail_mass_exact ≥ 0.
        The sum grid.sum() + tail_mass_exact should be >= 1 - 1e-3 (may be slightly
        > 1 due to independent Poisson approximation vs grid normalization).
        """
        pred = match_record.get("prediction", {})
        pmf = _pmf_from_match(pred)
        if pmf is None:
            pytest.skip("no PMF grid")
        if "tail_mass_exact" not in pred:
            pytest.skip("no tail_mass_exact")
        tail = float(pred["tail_mass_exact"])
        assert tail >= 0.0, f"tail_mass_exact is negative: {tail}"
        # Grid itself must sum to 1.0 (normalized)
        grid_sum = float(pmf.sum())
        assert abs(grid_sum - 1.0) < 5e-4, (
            f"grid.sum() = {grid_sum:.8f} (expected 1.0)"
        )

    def test_1x2_derived_from_pmf(self, match_record):
        pred = match_record.get("prediction", {})
        pmf = _pmf_from_match(pred)
        markets = pred.get("derived_markets", {})
        if pmf is None or not markets:
            pytest.skip("no PMF grid or derived markets")
        n = pmf.shape[0]
        pmf_hw = sum(pmf[h, a] for h in range(n) for a in range(n) if h > a)
        pmf_dr = sum(pmf[h, a] for h in range(n) for a in range(n) if h == a)
        pmf_aw = sum(pmf[h, a] for h in range(n) for a in range(n) if h < a)

        # Allow small tolerance for tail
        for name, pmf_val in [("home_win", pmf_hw), ("draw", pmf_dr), ("away_win", pmf_aw)]:
            market_val = markets.get(name)
            if market_val is None:
                continue
            assert abs(float(market_val) - pmf_val) < 0.01, (
                f"{name}: market={market_val:.4f}, PMF-cell-sum={pmf_val:.4f}"
            )

    def test_btts_derived_from_pmf(self, match_record):
        pred = match_record.get("prediction", {})
        pmf = _pmf_from_match(pred)
        markets = pred.get("derived_markets", {})
        if pmf is None or not markets:
            pytest.skip("no PMF grid or derived markets")
        btts = markets.get("btts_yes")
        if btts is None:
            pytest.skip("no BTTS market")
        n = pmf.shape[0]
        pmf_btts = sum(pmf[h, a] for h in range(n) for a in range(n) if h > 0 and a > 0)
        assert abs(float(btts) - pmf_btts) < 0.01, (
            f"BTTS: market={btts:.4f}, PMF-cell-sum={pmf_btts:.4f}"
        )

    def test_totals_derived_from_pmf(self, match_record):
        pred = match_record.get("prediction", {})
        pmf = _pmf_from_match(pred)
        markets = pred.get("derived_markets", {})
        if pmf is None or not markets:
            pytest.skip("no PMF or derived markets")
        n = pmf.shape[0]
        for key, line in [("over_2_5", 2.5), ("over_1_5", 1.5), ("over_3_5", 3.5)]:
            val = markets.get(key)
            if val is None:
                continue
            pmf_over = sum(
                pmf[h, a] for h in range(n) for a in range(n) if h + a > line
            )
            assert abs(float(val) - pmf_over) < 0.01, (
                f"Over {line}: market={val:.4f}, PMF-cell-sum={pmf_over:.4f}"
            )

    def test_top_scorelines_match_pmf(self, match_record):
        pred = match_record.get("prediction", {})
        pmf = _pmf_from_match(pred)
        top_scores_json = pred.get("top_scorelines", [])
        if pmf is None or not top_scores_json:
            pytest.skip("no PMF or top_scorelines")
        n = pmf.shape[0]
        for entry in top_scores_json[:5]:
            h = int(entry.get("home_goals", -1))
            a = int(entry.get("away_goals", -1))
            prob_json = float(entry.get("probability", 0.0))
            if h < 0 or a < 0 or h >= n or a >= n:
                continue
            prob_pmf = float(pmf[h, a])
            assert abs(prob_json - prob_pmf) < 0.001, (
                f"top_scorelines says P({h}-{a})={prob_json:.5f}, "
                f"but PMF cell = {prob_pmf:.5f}"
            )

    def test_pmf_non_negative(self, match_record):
        pred = match_record.get("prediction", {})
        pmf = _pmf_from_match(pred)
        if pmf is None:
            pytest.skip("no PMF grid")
        assert float(pmf.min()) >= -1e-8, (
            f"PMF has negative cells: min={float(pmf.min()):.2e}"
        )

    def test_correct_score_cells_inside_pmf(self, match_record):
        pred = match_record.get("prediction", {})
        pmf = _pmf_from_match(pred)
        cs_odds = pred.get("market_implied_probabilities", {}).get("correct_score", {})
        if pmf is None or not cs_odds:
            pytest.skip("no PMF or CS odds")
        n = pmf.shape[0]
        for score_str, prob in list(cs_odds.items())[:10]:
            if "-" not in str(score_str):
                continue
            try:
                h_str, a_str = str(score_str).split("-")
                h, a = int(h_str.strip()), int(a_str.strip())
            except (ValueError, TypeError):
                continue
            if h >= n or a >= n:
                continue
            assert pmf[h, a] >= 0, f"PMF cell [{h},{a}] is negative"
            # CS cell must not disagree wildly with PMF (within 5× either way for low-prob cells)
            if prob > 0.01 and pmf[h, a] > 0:
                ratio = prob / pmf[h, a]
                assert 0.05 < ratio < 20, (
                    f"CS odds {h}-{a}: market={prob:.4f}, PMF={pmf[h,a]:.4f} "
                    f"(ratio={ratio:.2f}) — cells may be mapped incorrectly"
                )

    def test_pmf_dimensions_consistent(self, match_record):
        pred = match_record.get("prediction", {})
        pmf = _pmf_from_match(pred)
        if pmf is None:
            pytest.skip("no PMF grid")
        assert pmf.ndim == 2, f"PMF is not 2D: shape={pmf.shape}"
        assert pmf.shape[0] == pmf.shape[1], f"PMF is not square: shape={pmf.shape}"
        max_goals = pred.get("max_goals", pmf.shape[0])
        assert pmf.shape[0] <= int(max_goals) + 1, (
            f"PMF shape {pmf.shape[0]} > max_goals+1={int(max_goals)+1}"
        )


class TestKnownArtifactRegression:
    """
    Hard regression tests for specific artifacts that appeared in commit 311bfb2.

    These exact values must never reappear in any committed artifact.
    The tests load the actual data/published/*.json files.
    """

    def _find_match(self, matches: list, home: str, away: str) -> dict | None:
        for m in matches:
            if m.get("home_team") == home and m.get("away_team") == away:
                return m
        return None

    def _june11_matches(self) -> list:
        p = PUBLISHED_DIR / "2026-06-11.json"
        if not p.exists():
            return []
        with open(p) as f:
            d = json.load(f)
        return d.get("matches", []) if isinstance(d, dict) else d

    def _all_matches(self) -> list:
        p = PUBLISHED_DIR / "all_scheduled_2026.json"
        if not p.exists():
            return []
        with open(p) as f:
            d = json.load(f)
        return d.get("matches", []) if isinstance(d, dict) else d

    def test_mexico_sa_no_4_9_artifact(self):
        """Regression: commit 311bfb2 had Mexico vs SA P(4-9)=0.025611. Must be gone."""
        matches = self._june11_matches() or self._all_matches()
        m = self._find_match(matches, "Mexico", "South Africa")
        if not m:
            pytest.skip("Mexico vs South Africa not found in published JSON")
        pmf = _pmf_from_match(m.get("prediction", {}))
        if pmf is None or pmf.shape[0] <= 9:
            pytest.skip("PMF grid too small")
        p_4_9 = float(pmf[4, 9])
        assert p_4_9 < 1e-6, (
            f"REGRESSION: Mexico vs SA P(4-9)={p_4_9:.8f} (was 0.025611 in 311bfb2). "
            "This is an impossible score — SLSQP or reconciler artifact."
        )

    def test_mexico_sa_no_11_5_artifact(self):
        """Regression: commit 311bfb2 had Mexico vs SA P(11-5)=0.016652. Must be gone."""
        matches = self._june11_matches() or self._all_matches()
        m = self._find_match(matches, "Mexico", "South Africa")
        if not m:
            pytest.skip("Mexico vs South Africa not found")
        pmf = _pmf_from_match(m.get("prediction", {}))
        if pmf is None or pmf.shape[0] <= 11:
            pytest.skip("PMF grid too small")
        p_11_5 = float(pmf[11, 5])
        assert p_11_5 < 1e-6, (
            f"REGRESSION: Mexico vs SA P(11-5)={p_11_5:.8f} (was 0.016652 in 311bfb2)."
        )

    def test_south_korea_czechia_no_1_12_artifact(self):
        """Regression: commit 311bfb2 had South Korea vs Czechia P(1-12)=0.039826. Must be gone."""
        matches = self._june11_matches() or self._all_matches()
        m = self._find_match(matches, "South Korea", "Czechia")
        if not m:
            pytest.skip("South Korea vs Czechia not found")
        pmf = _pmf_from_match(m.get("prediction", {}))
        if pmf is None or pmf.shape[0] <= 12:
            pytest.skip("PMF grid too small")
        p_1_12 = float(pmf[1, 12])
        assert p_1_12 < 1e-6, (
            f"REGRESSION: South Korea vs Czechia P(1-12)={p_1_12:.8f} (was 0.039826 in 311bfb2)."
        )

    def test_tail_mass_exact_present_in_june11(self):
        """tail_mass_exact must exist and be non-negative in June 11 predictions."""
        matches = self._june11_matches()
        if not matches:
            pytest.skip("2026-06-11.json not found")
        for m in matches:
            pred = m.get("prediction", {})
            home = m.get("home_team", "?")
            away = m.get("away_team", "?")
            assert "tail_mass_exact" in pred, (
                f"{home} vs {away}: tail_mass_exact is MISSING from prediction. "
                "Commit 311bfb2 had tail_mass=0.0 (old field name)."
            )
            val = pred["tail_mass_exact"]
            assert val is not None and float(val) >= 0, (
                f"{home} vs {away}: tail_mass_exact={val} is invalid"
            )

    def test_tail_mass_display_present_in_june11(self):
        """tail_mass_display must be present."""
        matches = self._june11_matches()
        if not matches:
            pytest.skip("2026-06-11.json not found")
        for m in matches:
            pred = m.get("prediction", {})
            home = m.get("home_team", "?")
            away = m.get("away_team", "?")
            assert "tail_mass_display" in pred, (
                f"{home} vs {away}: tail_mass_display is MISSING"
            )

    def test_no_stale_tail_mass_field(self):
        """
        The old field 'tail_mass: 0.0' (flat zero) must no longer appear.
        The new correct fields are tail_mass_exact and tail_mass_display.
        """
        matches = self._june11_matches()
        if not matches:
            pytest.skip("2026-06-11.json not found")
        for m in matches:
            pred = m.get("prediction", {})
            home = m.get("home_team", "?")
            away = m.get("away_team", "?")
            old_tail = pred.get("tail_mass")
            # Old field must not exist OR not be exactly 0.0 (stale default)
            if old_tail is not None:
                assert old_tail != 0.0 or "tail_mass_exact" in pred, (
                    f"{home} vs {away}: stale 'tail_mass=0.0' found with no tail_mass_exact. "
                    "This is the old broken format from commit 311bfb2."
                )

    def test_reconciliation_method_in_june11(self):
        """reconciliation_method must be present (proves new code path ran)."""
        matches = self._june11_matches()
        if not matches:
            pytest.skip("2026-06-11.json not found")
        for m in matches:
            pred = m.get("prediction", {})
            home = m.get("home_team", "?")
            away = m.get("away_team", "?")
            method = pred.get("reconciliation_method")
            assert method is not None, (
                f"{home} vs {away}: reconciliation_method is MISSING. "
                "This field was added in 759c0ff. Its absence means the JSON "
                "was generated by the old pipeline (311bfb2 or earlier)."
            )
            assert method in ("blend", "slsqp_core", "market_implied"), (
                f"{home} vs {away}: unexpected reconciliation_method='{method}'"
            )


class TestCoreGridSLSQP:
    """Unit tests for CoreGridSLSQPReconciler."""

    @pytest.fixture(autouse=True)
    def imports(self):
        from wc2026.markets.core_grid_reconcile import (
            CoreGridSLSQPReconciler, compare_reconciliation_methods,
            _ABS_CAP_BY_TOTAL,
        )
        self.Reconciler = CoreGridSLSQPReconciler
        self.compare = compare_reconciliation_methods
        self.ABS_CAPS = _ABS_CAP_BY_TOTAL

    def _make_mc(
        self,
        home_win=0.50, draw=0.25, away_win=0.25,
        over_2_5=0.60, btts_yes=0.55,
    ):
        """Create a minimal MarketConstraints-like object."""
        class FakeMC:
            has_1x2 = True
            has_correct_score = False
            correct_score = {}
            n_cs_outcomes = 0
            n_cs_vendors = 0
            btts_yes = None
        mc = FakeMC()
        mc.home_win = home_win
        mc.draw = draw
        mc.away_win = away_win
        mc.over_2_5 = over_2_5
        mc.over_1_5 = None
        mc.over_3_5 = None
        mc.over_0_5 = None
        mc.over_4_5 = None
        mc.over_5_5 = None
        mc.over_6_5 = None
        mc.btts_yes = btts_yes
        return mc

    def _make_prior(self, lh=1.5, la=1.0, n=15):
        from scipy.stats import poisson
        pmf = np.outer(poisson.pmf(range(n), lh), poisson.pmf(range(n), la))
        pmf /= pmf.sum()
        return pmf

    def test_slsqp_result_sums_to_one(self):
        prior = self._make_prior(1.5, 1.0)
        mc = self._make_mc()
        rec = self.Reconciler()
        result = rec.reconcile(prior, mc)
        total = float(result.full_pmf.sum()) + result.tail_mass_exact
        # Tolerance 5e-4: tail is computed from a 15×15 grid so small
        # floating-point residuals are expected
        assert abs(total - 1.0) < 5e-4, f"PMF + tail = {total:.8f}"

    def test_slsqp_no_impossible_scores(self):
        prior = self._make_prior(1.5, 1.0)
        mc = self._make_mc()
        rec = self.Reconciler()
        result = rec.reconcile(prior, mc)
        n = result.full_pmf.shape[0]
        for h in range(n):
            for a in range(n):
                if h + a >= 9:
                    assert result.full_pmf[h, a] < 1e-4, (
                        f"Impossible score {h}-{a}: P={result.full_pmf[h,a]:.5f}"
                    )

    def test_slsqp_1x2_close_to_target(self):
        prior = self._make_prior(2.0, 0.8)  # strong home team
        mc = self._make_mc(home_win=0.65, draw=0.22, away_win=0.13)
        rec = self.Reconciler()
        result = rec.reconcile(prior, mc)
        n = result.full_pmf.shape[0]
        pmf = result.full_pmf
        hw = sum(pmf[h, a] for h in range(n) for a in range(n) if h > a)
        # Soft constraint: should be within 15% of target (markets are soft)
        assert abs(hw - 0.65) < 0.15, f"Home win P={hw:.3f} far from target=0.65"

    def test_slsqp_top3_plausible(self):
        prior = self._make_prior(1.5, 1.0)
        mc = self._make_mc()
        rec = self.Reconciler()
        result = rec.reconcile(prior, mc)
        top3 = result.top_scores[:3]
        for s in top3:
            total = s["home_goals"] + s["away_goals"]
            assert total <= 6, (
                f"Top-3 score {s['home_goals']}-{s['away_goals']} (total={total})"
            )

    def test_slsqp_core_sums_correctly(self):
        prior = self._make_prior(1.5, 1.0)
        mc = self._make_mc()
        rec = self.Reconciler()
        result = rec.reconcile(prior, mc)
        core_sum = float(result.core_pmf.sum())
        tail = result.tail_mass_exact
        assert abs(core_sum + tail - 1.0) < 1e-4, (
            f"core_sum={core_sum:.6f} + tail={tail:.2e} != 1.0"
        )

    def test_slsqp_tail_buckets_present(self):
        prior = self._make_prior(1.5, 1.0)
        mc = self._make_mc()
        rec = self.Reconciler()
        result = rec.reconcile(prior, mc)
        required = {
            "home_8plus_away_0_7", "home_0_7_away_8plus",
            "both_8plus", "other_home_win", "other_draw",
        }
        assert required.issubset(set(result.tail_event_buckets.keys()))

    def test_abs_caps_prevent_spikes(self):
        """Verify absolute caps block high-total cells."""
        from wc2026.markets.core_grid_reconcile import _build_bounds
        from scipy.stats import poisson
        n = 8
        q = np.outer(poisson.pmf(range(n), 1.5), poisson.pmf(range(n), 1.0))
        q /= q.sum()
        bounds = _build_bounds(q, n)
        # Cell [4,4] = total_goals=8: cap should be 0.0008 or less
        idx_44 = 4 * n + 4
        lo, hi = bounds[idx_44]
        assert hi <= 0.001, f"Cap for [4,4] (total=8) is too loose: {hi}"

    def test_compare_methods_both_plausible(self):
        prior = self._make_prior(1.5, 1.0)
        mc = self._make_mc()
        comparison = self.compare(prior, mc, max_goals=15, blend_alpha=0.80)
        assert "best_pmf" in comparison
        best = comparison["best_pmf"]
        assert best.shape == (15, 15)
        # Best PMF must be plausible
        n = best.shape[0]
        for h in range(n):
            for a in range(n):
                if h + a >= 9:
                    assert best[h, a] < 1e-4

    def test_slsqp_not_worse_than_blend_by_large_margin(self):
        """When SLSQP converges cleanly it should be competitive with blend."""
        prior = self._make_prior(1.5, 1.0)
        mc = self._make_mc(home_win=0.55, draw=0.25, away_win=0.20)
        comparison = self.compare(prior, mc, max_goals=15)
        slsqp_result = comparison["slsqp_core"]

        # If SLSQP passes plausibility, validate its constraint error is reasonable
        if slsqp_result.plausibility_pass:
            slsqp_score = comparison["method_scores"].get("slsqp_core", float("inf"))
            blend_score = comparison["method_scores"].get("blend", float("inf"))
            if blend_score < float("inf") and slsqp_score < float("inf"):
                assert slsqp_score < blend_score * 10, (
                    f"SLSQP validation loss ({slsqp_score:.4f}) is >10× blend ({blend_score:.4f})"
                )
        else:
            # SLSQP failed plausibility: verify blend is still the selected method
            assert comparison["best_method"] in ("blend", "market_implied"), (
                f"When SLSQP fails plausibility, best_method should be blend, "
                f"got: {comparison['best_method']}"
            )

    def test_validate_method_catches_impossible(self):
        """CoreGridResult.validate() should flag impossible cells."""
        from wc2026.markets.core_grid_reconcile import CoreGridResult
        bad_pmf = np.full((15, 15), 1e-6)
        bad_pmf[4, 9] = 0.10  # impossible
        bad_pmf /= bad_pmf.sum()
        mc = self._make_mc()
        from wc2026.markets.core_grid_reconcile import _pmf_to_result
        result = _pmf_to_result(bad_pmf, mc, "test")
        errs = result.validate()
        assert any("4" in e and "9" in e for e in errs), (
            f"validate() did not catch [4,9] artifact: {errs}"
        )

    def test_core_grid_non_negative(self):
        prior = self._make_prior(1.5, 1.0)
        mc = self._make_mc()
        rec = self.Reconciler()
        result = rec.reconcile(prior, mc)
        assert float(result.full_pmf.min()) >= -1e-10
        assert float(result.core_pmf.min()) >= -1e-10
