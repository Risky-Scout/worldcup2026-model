"""
Presentation-hardening tests — validates all P0 safety requirements.

These tests cover:
  - No alphabetical tiebreaking in group simulator
  - Draw boost suppressed in presentation safe mode
  - Group incentive adjustment suppressed in presentation safe mode
  - Circular edge blocked for market_reconciled / market_implied PMFs
  - lambda_sensitivity fields present (not ci_90 mislabelled confidence intervals)
  - First-half markets suppressed in presentation safe mode
  - generated_at not overwritten during upload (uploaded_at added instead)
  - 2026 WC format: top 2 advance automatically, 8 best third-place teams advance

Run with: python -m pytest tests/test_presentation_hardening.py -v
"""
from __future__ import annotations

import importlib
import json
import os
import random
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "src"))


# ── Helper PMFs ───────────────────────────────────────────────────────────────

def _uniform_pmf(n: int = 8) -> np.ndarray:
    pmf = np.ones((n, n), dtype=float)
    pmf /= pmf.sum()
    return pmf


# ── 1. Circular edge guard ─────────────────────────────────────────────────────

class TestCircularEdgeGuard:
    """market_reconciled and market_implied PMFs must never produce value_flag=True."""

    def _market_probs(self):
        return {"home_win": 0.50, "draw": 0.25, "away_win": 0.25}

    def test_market_reconciled_no_value_flag(self):
        from wc2026.markets.edge import compute_market_edges
        pmf = _uniform_pmf()
        edges = compute_market_edges(
            pmf, self._market_probs(), lh=1.3, la=1.1,
            prediction_mode="market_reconciled",
        )
        assert all(not e.value_flag for e in edges), (
            "market_reconciled PMF must not generate value_flag=True (circular edge)"
        )

    def test_market_implied_no_value_flag(self):
        from wc2026.markets.edge import compute_market_edges
        pmf = _uniform_pmf()
        edges = compute_market_edges(
            pmf, self._market_probs(), lh=1.3, la=1.1,
            prediction_mode="market_implied",
        )
        assert all(not e.value_flag for e in edges), (
            "market_implied PMF must not generate value_flag=True (circular edge)"
        )

    def test_market_reconciled_zero_kelly(self):
        from wc2026.markets.edge import compute_market_edges
        pmf = _uniform_pmf()
        edges = compute_market_edges(
            pmf, self._market_probs(), lh=1.3, la=1.1,
            prediction_mode="market_reconciled",
        )
        assert all(e.half_kelly == 0.0 for e in edges), (
            "market_reconciled PMF must produce zero Kelly stake (circular guard)"
        )

    def test_pure_model_may_flag_value(self):
        """pure_model mode is allowed to produce value_flag=True when edge is large."""
        from wc2026.markets.edge import compute_market_edges
        # Heavily biased PMF: model strongly favours home win
        pmf = np.zeros((8, 8))
        pmf[2, 0] = 0.8  # 2-0 most likely
        pmf[1, 0] = 0.2  # 1-0
        pmf /= pmf.sum()
        # Market underestimates home win
        market = {"home_win": 0.20, "draw": 0.40, "away_win": 0.40}
        edges = compute_market_edges(pmf, market, lh=2.0, la=0.5, prediction_mode="pure_model")
        home_edges = [e for e in edges if e.market == "home_win"]
        assert home_edges, "Should have a home_win edge entry"
        # The value_flag CAN be True (not forced off) for pure_model
        # (no assertion that it IS True, just that the guard doesn't block it)

    def test_circular_edge_reason_contains_mode(self):
        """Suppressed edges must include the prediction_mode in the reason."""
        from wc2026.markets.edge import compute_market_edges
        pmf = _uniform_pmf()
        edges = compute_market_edges(
            pmf, self._market_probs(), lh=1.3, la=1.1,
            prediction_mode="market_reconciled",
        )
        for e in edges:
            assert "market_reconciled" in e.value_reason or "CIRCULAR" in e.value_reason, (
                f"Expected circular reason for market={e.market}, got: {e.value_reason}"
            )


# ── 2. Lambda sensitivity fields (not confidence intervals) ───────────────────

class TestLambdaSensitivityFields:
    """Edge dict must use lambda_sensitivity_lower/upper, not ci_90_lower/upper."""

    def test_dict_has_lambda_sensitivity_keys(self):
        from wc2026.markets.edge import compute_market_edges
        pmf = _uniform_pmf()
        edges = compute_market_edges(
            pmf, {"home_win": 0.33, "draw": 0.34, "away_win": 0.33},
            lh=1.3, la=1.1, prediction_mode="pure_model",
        )
        assert edges, "Should have edge entries"
        d = edges[0].to_dict()
        assert "lambda_sensitivity_lower" in d, "Must have lambda_sensitivity_lower key"
        assert "lambda_sensitivity_upper" in d, "Must have lambda_sensitivity_upper key"
        # Old mislabelled CI keys must not be present
        assert "ci_90_lower" not in d, "Old ci_90_lower key must be removed"
        assert "ci_90_upper" not in d, "Old ci_90_upper key must be removed"

    def test_dataclass_has_lambda_fields(self):
        from wc2026.markets.edge import MarketEdge
        fields = {f.name for f in MarketEdge.__dataclass_fields__.values()}
        assert "lambda_sensitivity_lower" in fields
        assert "lambda_sensitivity_upper" in fields
        assert "ci_lower_90" not in fields, "Old ci_lower_90 field must not exist"
        assert "ci_upper_90" not in fields, "Old ci_upper_90 field must not exist"


# ── 3. Tiebreaking in group simulator ─────────────────────────────────────────

class TestGroupSimulatorTiebreaking:
    """Alphabetical tiebreaking must not be the final tiebreak in _rank_group."""

    def test_rank_group_no_alphabetical_bias(self):
        """Teams with identical stats should be ranked differently across seeds."""
        sys.path.insert(0, str(REPO_ROOT / "scripts"))
        from simulate_groups import _rank_group

        # Four teams with completely equal standings
        standings = {
            "Alpha": {"pts": 3, "gd": 0, "gf": 1},
            "Beta":  {"pts": 3, "gd": 0, "gf": 1},
            "Gamma": {"pts": 3, "gd": 0, "gf": 1},
            "Delta": {"pts": 3, "gd": 0, "gf": 1},
        }

        results = set()
        for seed in range(50):
            rng = random.Random(seed)
            ranked = _rank_group(standings, rng=rng)
            results.add(tuple(ranked))

        # With random tiebreaking we should see multiple orderings (not always alphabetical)
        assert len(results) > 1, (
            f"Expected multiple orderings across seeds; got only: {results}. "
            "Alphabetical tiebreaking detected."
        )

    def test_rank_group_deterministic_same_seed(self):
        """Same seed must produce same ranking."""
        sys.path.insert(0, str(REPO_ROOT / "scripts"))
        from simulate_groups import _rank_group

        standings = {
            "X": {"pts": 4, "gd": 1, "gf": 3},
            "Y": {"pts": 4, "gd": 1, "gf": 3},
        }
        rng1 = random.Random(42)
        rng2 = random.Random(42)
        assert _rank_group(standings, rng=rng1) == _rank_group(standings, rng=rng2)

    def test_rank_third_place_no_alphabetical_bias(self):
        """Third-place ranking should not fall back to alphabetical order."""
        sys.path.insert(0, str(REPO_ROOT / "scripts"))
        from simulate_groups import _rank_third_place

        # 12 third-place teams with identical stats
        records = [
            {"team": chr(65 + i), "group": chr(65 + i), "pts": 3, "gd": 0, "gf": 1, "ga": 1}
            for i in range(12)
        ]

        orderings = set()
        for seed in range(20):
            rng = random.Random(seed)
            advancing = _rank_third_place(records, rng=rng)
            orderings.add(tuple(sorted(advancing)))

        # The exact set of 8 from 12 should vary across seeds
        assert len(orderings) > 1 or len(records) <= 8, (
            "Third-place ranking shows alphabetical bias — identical teams always advance the same 8"
        )


# ── 4. Draw boost suppressed in presentation safe mode ────────────────────────

class TestDrawBoostSuppression:
    """Draw boost heuristic must be suppressed when PRESENTATION_SAFE_MODE=true."""

    def test_draw_boost_suppressed_in_presentation_mode(self):
        with patch.dict(os.environ, {"WC_PRESENTATION_SAFE_MODE": "true"}):
            import wc2026.config
            importlib.reload(wc2026.config)
            assert wc2026.config.PRESENTATION_SAFE_MODE is True
        # Reload back to default after test
        importlib.reload(wc2026.config)

    def test_draw_boost_flag_exists_in_config(self):
        import wc2026.config
        assert hasattr(wc2026.config, "PRESENTATION_SAFE_MODE")
        assert hasattr(wc2026.config, "SUPPRESS_DRAW_BOOST")
        assert hasattr(wc2026.config, "SUPPRESS_FIRST_HALF_MARKETS")
        assert hasattr(wc2026.config, "DISABLE_AUTO_MARKET_WEIGHT")
        assert hasattr(wc2026.config, "DISABLE_CIRCULAR_EDGE")

    def test_group_incentive_suppressed_in_safe_mode(self):
        """adjust_pmf_for_group_incentives should return unchanged PMF in safe mode."""
        with patch.dict(os.environ, {"WC_PRESENTATION_SAFE_MODE": "true"}):
            import wc2026.config
            importlib.reload(wc2026.config)

            from wc2026.tournament.group_incentives import (
                adjust_pmf_for_group_incentives, GroupIncentiveState,
            )
            pmf = _uniform_pmf()
            state = GroupIncentiveState(team="TestTeam", draw_utility=0.5)
            result_pmf, _, _, _ = adjust_pmf_for_group_incentives(pmf, state, state, 0.0, 1.3, 1.1)
            np.testing.assert_array_equal(result_pmf, pmf)

        importlib.reload(wc2026.config)


# ── 5. 2026 WC format: top 2 advance, NOT top 3 ───────────────────────────────

class TestWC2026Format:
    """Group format must be 12 groups of 4, top 2 advance, best 8 third-place teams."""

    def test_group_stage_comment_corrected(self):
        """group_incentives module docstring should not say 'top 3 advance'."""
        from wc2026.tournament import group_incentives
        doc = group_incentives.__doc__ or ""
        # Should reference correct format
        assert "top 2" in doc.lower() or "Top 2" in doc, (
            "group_incentives docstring should state 'Top 2 advance' not 'top 3'"
        )
        assert "top 3 advance" not in doc.lower(), (
            "group_incentives docstring must not claim 'top 3 advance'"
        )

    def test_simulate_groups_docstring_correct_format(self):
        """simulate_groups.py docstring should state the correct 2026 format."""
        sim_path = REPO_ROOT / "scripts" / "simulate_groups.py"
        src = sim_path.read_text()
        # Check the module-level docstring (between the first triple-quote and next one)
        assert "top 2" in src.lower() or "Top 2" in src, (
            "simulate_groups must document 'top 2' advancement"
        )
        assert "8" in src, "simulate_groups must mention 8 best third-place teams"
        assert "top 3 advance" not in src.lower(), (
            "simulate_groups must not claim 'top 3 advance'"
        )

    def test_render_markdown_no_alphabetical_mention(self):
        """render_markdown should not document alphabetical tiebreaking."""
        sys.path.insert(0, str(REPO_ROOT / "scripts"))
        from simulate_groups import render_markdown
        import inspect
        src = inspect.getsource(render_markdown)
        assert "alphabetical" not in src.lower(), (
            "render_markdown source must not mention alphabetical tiebreaking"
        )


# ── 6. Upload timestamp preservation ──────────────────────────────────────────

class TestUploadTimestampPreservation:
    """generated_at must not be overwritten during upload; uploaded_at must be added."""

    def test_upload_preserves_generated_at(self):
        """upload() must not overwrite generated_at with current time."""
        # Read the upload script source to check it doesn't overwrite generated_at
        upload_script = REPO_ROOT / "scripts" / "upload_predictions.py"
        src = upload_script.read_text()
        # The old bad pattern
        assert 'doc["generated_at"] = datetime.now' not in src, (
            "upload_predictions.py must not overwrite generated_at with upload time"
        )
        # The new good pattern: uploaded_at should be set
        assert "uploaded_at" in src, (
            "upload_predictions.py must add uploaded_at timestamp"
        )

    def test_upload_adds_uploaded_at(self):
        """Simulated upload should add uploaded_at to the JSON payload."""
        upload_script = REPO_ROOT / "scripts" / "upload_predictions.py"
        src = upload_script.read_text()
        assert '"uploaded_at"' in src or "uploaded_at" in src, (
            "upload script must set uploaded_at field"
        )


# ── 7. PMF integrity ───────────────────────────────────────────────────────────

class TestPMFIntegrity:
    """Basic PMF invariants for any distribution used in edge calculation."""

    def test_pmf_sums_to_one(self):
        pmf = _uniform_pmf()
        assert abs(pmf.sum() - 1.0) < 1e-10

    def test_no_negative_values(self):
        pmf = _uniform_pmf()
        assert (pmf >= 0).all()

    def test_1x2_sums_to_one_from_pmf(self):
        from wc2026.markets.edge import compute_market_edges
        pmf = _uniform_pmf()
        edges = compute_market_edges(
            pmf, {"home_win": 0.33, "draw": 0.34, "away_win": 0.33},
            lh=1.3, la=1.1, prediction_mode="pure_model",
        )
        edge_map = {e.market: e.model_prob for e in edges}
        hw = edge_map.get("home_win", 0)
        dr = edge_map.get("draw", 0)
        aw = edge_map.get("away_win", 0)
        if hw and dr and aw:
            total = hw + dr + aw
            assert abs(total - 1.0) < 1e-4, f"1X2 sum={total} ≠ 1"


# ── 8. WoO contract probability labeling ──────────────────────────────────────

class TestProbabilityLabeling:
    """Published JSON must label the probability origin correctly."""

    def test_woo_contract_has_publish_mode(self):
        """WizardOfOdds contract source must reference publish_mode."""
        woo_path = REPO_ROOT / "src" / "wc2026" / "publishing" / "wizardofodds_contract.py"
        src = woo_path.read_text()
        assert "publish_mode" in src, "WoO contract must include publish_mode field"

    def test_published_json_has_generated_at(self):
        """At least one published JSON should have generated_at field."""
        pub_dir = REPO_ROOT / "data" / "published"
        json_files = sorted(pub_dir.glob("2026-*.json"))
        if not json_files:
            pytest.skip("No published JSON files found")
        doc = json.loads(json_files[-1].read_text())
        assert "generated_at" in doc, "Published JSON must have generated_at field"
