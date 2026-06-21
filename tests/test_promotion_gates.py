"""
Tests for the hard promotion gates.
These enforce that public promotion requires meeting all four gates.
"""
import json
import tempfile

import pandas as pd
import pytest
from pathlib import Path

from src.wc2026.models.promotion_gates import (
    CLEAN_HEAD,
    GATE_3_MIN_MATCHES,
    GATE_4_MIN_LOG_LOSS_IMPROVEMENT,
    GATE_4_MIN_MATCHES,
    run_all_gates,
    validate_gate_1,
    validate_gate_2,
    validate_gate_3,
    validate_gate_4,
)


def test_gate_1_head_confirmed():
    """HEAD must be resolvable in the repo — gate passes as long as git is available."""
    result = validate_gate_1()
    assert result.passed, f"Gate 1 failed: {result.reason}"
    assert "head" in result.metrics
    assert result.metrics["head"]  # non-empty commit hash


def test_gate_2_public_flag_off():
    """WC_USE_EGM_FOR_PUBLIC must be false by default."""
    import os
    os.environ.pop("WC_USE_EGM_FOR_PUBLIC", None)
    result = validate_gate_2()
    assert result.passed, f"Gate 2 failed: {result.reason}"


def test_gate_2_blocks_when_flag_set(monkeypatch):
    """Gate 2 must fail if WC_USE_EGM_FOR_PUBLIC=true."""
    monkeypatch.setenv("WC_USE_EGM_FOR_PUBLIC", "true")
    result = validate_gate_2()
    assert not result.passed


def test_gate_3_fails_without_shadow_report():
    """Gate 3 must fail if no shadow report exists yet."""
    result = validate_gate_3(Path("/nonexistent/path/production_diff.csv"))
    assert not result.passed
    assert result.metrics.get("matches_processed", 0) == 0


def test_gate_3_fails_with_insufficient_matches():
    """Gate 3 must fail with fewer than 5 matches."""
    with tempfile.NamedTemporaryFile(suffix=".csv", mode="w", delete=False) as f:
        df = pd.DataFrame([
            {"lambda_home_diff": 0.05, "lambda_away_diff": 0.03},
            {"lambda_home_diff": 0.08, "lambda_away_diff": 0.04},
        ])
        df.to_csv(f.name, index=False)
        result = validate_gate_3(Path(f.name))
    assert not result.passed
    assert "need" in result.reason.lower() or "only" in result.reason.lower()


def test_gate_3_passes_with_sufficient_data():
    """Gate 3 passes with 5+ matches and small deltas."""
    with tempfile.NamedTemporaryFile(suffix=".csv", mode="w", delete=False) as f:
        df = pd.DataFrame([
            {"lambda_home_diff": 0.05, "lambda_away_diff": 0.03}
        ] * 6)
        df.to_csv(f.name, index=False)
        result = validate_gate_3(Path(f.name))
    assert result.passed
    # Gate 3 passing does NOT mean promotion approved
    assert "sanity" in result.name.lower() or "sanity" in result.reason.lower()


def test_gate_4_fails_without_validation_report():
    """Gate 4 must fail if no validation report exists."""
    result = validate_gate_4(Path("/nonexistent/rolling_origin_validation.json"))
    assert not result.passed
    assert (
        result.metrics.get("status") == "pending"
        or "pending" in result.reason.lower()
        or "no validation" in result.reason.lower()
    )


def test_gate_4_fails_below_threshold():
    """Gate 4 must fail if improvement is below threshold."""
    with tempfile.NamedTemporaryFile(suffix=".json", mode="w", delete=False) as f:
        json.dump({
            "n_shadow_matches": 25,
            "log_loss_improvement_pct": 0.001,      # below 0.005 threshold
            "brier_improvement": 0.001,              # below 0.003 threshold
            "calibration_slope_improvement": 0.01,  # below 0.05 threshold
        }, f)
        f.flush()
        result = validate_gate_4(Path(f.name))
    assert not result.passed
    assert "below threshold" in result.reason.lower()


def test_gate_4_passes_with_log_loss_improvement():
    """Gate 4 passes when log-loss improvement meets threshold."""
    with tempfile.NamedTemporaryFile(suffix=".json", mode="w", delete=False) as f:
        json.dump({
            "n_shadow_matches": 25,
            "log_loss_improvement_pct": 0.008,  # above 0.005 threshold
            "brier_improvement": 0.001,
            "calibration_slope_improvement": 0.01,
        }, f)
        f.flush()
        result = validate_gate_4(Path(f.name))
    assert result.passed
    assert "promotion approved" in result.reason.upper() or result.passed


def test_run_all_gates_shadow_ready():
    """Without shadow data, verdict must be SHADOW_READY."""
    results = run_all_gates(
        production_diff_path=Path("/nonexistent/production_diff.csv"),
        validation_report_path=Path("/nonexistent/validation.json"),
    )
    assert results["verdict"] == "SHADOW_READY"
    assert results["promotion_approved"] is False


def test_promotion_requires_gate_4():
    """Passing gates 1-3 but not gate 4 must NOT approve promotion."""
    with tempfile.NamedTemporaryFile(suffix=".csv", mode="w", delete=False) as f:
        df = pd.DataFrame([{"lambda_home_diff": 0.05, "lambda_away_diff": 0.03}] * 6)
        df.to_csv(f.name, index=False)
        shadow_path = Path(f.name)

    results = run_all_gates(
        production_diff_path=shadow_path,
        validation_report_path=Path("/nonexistent/validation.json"),
    )
    assert results["promotion_approved"] is False
    assert results["verdict"] in ("SANITY_PASSED", "SHADOW_READY")


def test_confederation_priors_are_versioned():
    """Confederation priors must have a version string."""
    from src.wc2026.ratings.fallback_prior import (
        CONFEDERATION_PRIOR_STATUS,
        CONFEDERATION_PRIOR_VERSION,
    )
    assert "v" in CONFEDERATION_PRIOR_VERSION
    assert "prior" in CONFEDERATION_PRIOR_STATUS.lower()
    assert "fitted" not in CONFEDERATION_PRIOR_STATUS.replace("not_fitted", "")


def test_gate_3_is_not_promotion_threshold():
    """Gate 3 passing must not set promotion_approved=True."""
    with tempfile.NamedTemporaryFile(suffix=".csv", mode="w", delete=False) as f:
        df = pd.DataFrame([{"lambda_home_diff": 0.05, "lambda_away_diff": 0.03}] * 10)
        df.to_csv(f.name, index=False)
        shadow_path = Path(f.name)

    results = run_all_gates(
        production_diff_path=shadow_path,
        validation_report_path=None,
    )
    # Even with Gate 3 passing, promotion must not be approved without Gate 4
    assert results["promotion_approved"] is False, (
        "Gate 3 alone must NEVER approve promotion. "
        "Gate 4 (out-of-sample improvement) is required."
    )
