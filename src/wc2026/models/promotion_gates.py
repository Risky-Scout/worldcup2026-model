"""
Promotion gates for the EGM elite model layer.

GREEN LIGHT: shadow mode (WC_EGM_SHADOW_MODE=True)
  - contract tests pass
  - public output unchanged
  - pipeline produces shadow predictions

YELLOW LIGHT: shadow collection (current status after 0a819c6)
  - shadow runner active
  - accumulating production_diff.csv
  - NOT yet approved for public output

RED LIGHT: do not claim CLV superiority
  - no immutable pre-match snapshots existed before 2026-06-18
  - no post-deployment shadow data or CLV reports yet exist

PROMOTION REQUIRES ALL FOUR GATES:

Gate 1 — Branch HEAD confirmation
  Current clean head: 0a819c6
  All 2038 tests pass, 0 failures.
  Public output unchanged (10/10 contract tests).

Gate 2 — WC_USE_EGM_FOR_PUBLIC remains false
  Must remain false until Gates 3 and 4 are satisfied.
  Checked at runtime by validate_gate_2().

Gate 3 — Shadow sanity (pipeline operational, NOT a promotion threshold)
  Minimum 5 matches processed through shadow runner.
  Rolling mean |Δλ| < 0.15 on both home and away.
  This proves the pipeline works; it does NOT prove model improvement.
  Checked by validate_gate_3(shadow_report_path).

Gate 4 — Out-of-sample improvement (REQUIRED for public promotion)
  Minimum 20 completed shadow matches with immutable pre-match snapshots.
  Rolling-origin 1X2 log-loss must improve by ≥ 0.5% vs current live model.
  OR rolling-origin Brier score must improve by ≥ 0.003.
  OR calibration slope must be closer to 1.0 by ≥ 0.05.
  Checked by validate_gate_4(validation_report_path).
"""
from __future__ import annotations

import json
import logging
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import pandas as pd

log = logging.getLogger(__name__)

CLEAN_HEAD = "0a819c6"
PROMOTION_FLAGS_REQUIRED = {
    "WC_BREAKING_SCHEMA_CHANGES_ALLOWED": False,
    "WC_USE_EGM_FOR_PUBLIC": False,   # must be False until Gate 4
}

# Thresholds
GATE_3_MIN_MATCHES = 5
GATE_3_MAX_DELTA_LAMBDA = 0.15
GATE_4_MIN_MATCHES = 20
GATE_4_MIN_LOG_LOSS_IMPROVEMENT = 0.005   # 0.5%
GATE_4_MIN_BRIER_IMPROVEMENT = 0.003
GATE_4_MIN_CALIBRATION_SLOPE_IMPROVEMENT = 0.05


@dataclass
class GateResult:
    gate: int
    name: str
    passed: bool
    reason: str
    metrics: dict


def validate_gate_1() -> GateResult:
    """Gate 1: Branch HEAD is a descendant of CLEAN_HEAD (ancestor check)."""
    try:
        result = subprocess.run(
            ["git", "merge-base", "--is-ancestor", CLEAN_HEAD, "HEAD"],
            capture_output=True,
            cwd=Path.cwd(),
        )
        passed = result.returncode == 0

        head_result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True, text=True, cwd=Path.cwd(),
        )
        head = head_result.stdout.strip()

        reason = (
            f"HEAD={head} is a descendant of {CLEAN_HEAD} (confirmed)"
            if passed
            else f"HEAD={head} is NOT a descendant of {CLEAN_HEAD}"
        )
    except Exception as e:
        passed = False
        reason = f"Could not confirm HEAD ancestry: {e}"
        head = "unknown"

    return GateResult(
        gate=1, name="branch_head_confirmation",
        passed=passed, reason=reason,
        metrics={"head": head, "expected_ancestor": CLEAN_HEAD},
    )


def validate_gate_2() -> GateResult:
    """Gate 2: WC_USE_EGM_FOR_PUBLIC must be False."""
    try:
        import os
        val = os.getenv("WC_USE_EGM_FOR_PUBLIC", "false").lower()
        passed = val != "true"
        reason = (
            "WC_USE_EGM_FOR_PUBLIC=false (correct)"
            if passed
            else "WC_USE_EGM_FOR_PUBLIC=true — BLOCKED: Gate 4 must pass first"
        )
    except Exception as e:
        passed = False
        reason = str(e)
    return GateResult(
        gate=2, name="public_flag_locked",
        passed=passed, reason=reason,
        metrics={"WC_USE_EGM_FOR_PUBLIC": not passed},
    )


def validate_gate_3(
    production_diff_path: Path = Path("reports/live_shadow/production_diff.csv"),
) -> GateResult:
    """
    Gate 3: Shadow sanity check.
    Minimum 5 matches, rolling mean |Δλ| < 0.15.
    IMPORTANT: This is a pipeline sanity check only, NOT a promotion threshold.
    """
    if not production_diff_path.exists():
        return GateResult(
            gate=3, name="shadow_sanity",
            passed=False,
            reason=(
                f"No shadow report at {production_diff_path} — "
                "run pipeline with WC_EGM_SHADOW_MODE=True"
            ),
            metrics={"matches_processed": 0},
        )
    try:
        df = pd.read_csv(production_diff_path)
        n = len(df)
        if n < GATE_3_MIN_MATCHES:
            return GateResult(
                gate=3, name="shadow_sanity",
                passed=False,
                reason=f"Only {n} shadow matches processed, need {GATE_3_MIN_MATCHES}",
                metrics={"matches_processed": n, "required": GATE_3_MIN_MATCHES},
            )
        delta_h = (
            df["lambda_home_diff"].abs().mean()
            if "lambda_home_diff" in df.columns
            else None
        )
        delta_a = (
            df["lambda_away_diff"].abs().mean()
            if "lambda_away_diff" in df.columns
            else None
        )
        if delta_h is None or delta_a is None:
            return GateResult(
                gate=3, name="shadow_sanity",
                passed=False,
                reason="Shadow report missing lambda_home_diff / lambda_away_diff columns",
                metrics={"matches_processed": n},
            )
        passed = delta_h < GATE_3_MAX_DELTA_LAMBDA and delta_a < GATE_3_MAX_DELTA_LAMBDA
        reason = (
            f"Pipeline sanity OK: |Δλ_H|={delta_h:.3f}, |Δλ_A|={delta_a:.3f} "
            f"(threshold={GATE_3_MAX_DELTA_LAMBDA})"
            if passed
            else
            f"Pipeline sanity FAILED: |Δλ_H|={delta_h:.3f}, |Δλ_A|={delta_a:.3f} "
            f"(threshold={GATE_3_MAX_DELTA_LAMBDA})"
        )
        return GateResult(
            gate=3, name="shadow_sanity",
            passed=passed,
            reason=reason + " [NOTE: sanity check only, not promotion threshold]",
            metrics={
                "matches_processed": n,
                "mean_delta_lambda_home": float(delta_h),
                "mean_delta_lambda_away": float(delta_a),
            },
        )
    except Exception as e:
        return GateResult(gate=3, name="shadow_sanity", passed=False, reason=str(e), metrics={})


def validate_gate_4(
    validation_report_path: Optional[Path] = Path(
        "reports/team_strength/rolling_origin_validation.json"
    ),
) -> GateResult:
    """
    Gate 4: Out-of-sample improvement.
    Required for ANY public promotion.
    Minimum 20 completed shadow matches.
    Must show log-loss improvement ≥ 0.5% OR Brier improvement ≥ 0.003.
    """
    if validation_report_path is None or not validation_report_path.exists():
        return GateResult(
            gate=4, name="out_of_sample_improvement",
            passed=False,
            reason=(
                f"No validation report at {validation_report_path}. "
                f"Need {GATE_4_MIN_MATCHES}+ completed shadow matches with "
                "rolling-origin 1X2 log-loss comparison."
            ),
            metrics={"status": "pending", "required_matches": GATE_4_MIN_MATCHES},
        )
    try:
        with open(validation_report_path) as f:
            report = json.load(f)
        n = int(report.get("n_shadow_matches", 0))
        if n < GATE_4_MIN_MATCHES:
            return GateResult(
                gate=4, name="out_of_sample_improvement",
                passed=False,
                reason=f"Only {n} shadow matches with validation, need {GATE_4_MIN_MATCHES}",
                metrics={"n_shadow_matches": n, "required": GATE_4_MIN_MATCHES},
            )
        log_loss_improvement = float(report.get("log_loss_improvement_pct", 0.0))
        brier_improvement = float(report.get("brier_improvement", 0.0))
        calibration_improvement = float(report.get("calibration_slope_improvement", 0.0))

        passed = (
            log_loss_improvement >= GATE_4_MIN_LOG_LOSS_IMPROVEMENT
            or brier_improvement >= GATE_4_MIN_BRIER_IMPROVEMENT
            or calibration_improvement >= GATE_4_MIN_CALIBRATION_SLOPE_IMPROVEMENT
        )
        reason = (
            f"Log-loss Δ={log_loss_improvement:.3%}, Brier Δ={brier_improvement:.4f}, "
            f"Calibration slope Δ={calibration_improvement:.3f} — "
            + ("PROMOTION APPROVED" if passed else "BELOW THRESHOLD — do not promote")
        )
        return GateResult(
            gate=4, name="out_of_sample_improvement",
            passed=passed, reason=reason,
            metrics={
                "n_shadow_matches": n,
                "log_loss_improvement_pct": log_loss_improvement,
                "brier_improvement": brier_improvement,
                "calibration_slope_improvement": calibration_improvement,
            },
        )
    except Exception as e:
        return GateResult(
            gate=4, name="out_of_sample_improvement",
            passed=False, reason=str(e), metrics={},
        )


def run_all_gates(
    production_diff_path: Path = Path("reports/live_shadow/production_diff.csv"),
    validation_report_path: Optional[Path] = Path(
        "reports/team_strength/rolling_origin_validation.json"
    ),
) -> dict:
    """
    Run all 4 gates. Returns dict with results and overall verdict.

    Verdicts:
      SHADOW_READY    — Gates 1+2 pass, 3+4 pending
      SANITY_PASSED   — Gates 1+2+3 pass, Gate 4 pending
      PROMOTION_READY — All 4 gates pass (may set WC_USE_EGM_FOR_PUBLIC=true)
      BLOCKED         — Gate 1 or 2 failed
    """
    g1 = validate_gate_1()
    g2 = validate_gate_2()
    g3 = validate_gate_3(production_diff_path)
    g4 = validate_gate_4(validation_report_path)

    gates = [g1, g2, g3, g4]
    results = {
        f"gate_{g.gate}": {
            "name": g.name,
            "passed": g.passed,
            "reason": g.reason,
            "metrics": g.metrics,
        }
        for g in gates
    }

    if not g1.passed or not g2.passed:
        verdict = "BLOCKED"
    elif not g3.passed and not g4.passed:
        verdict = "SHADOW_READY"
    elif g3.passed and not g4.passed:
        verdict = "SANITY_PASSED"
    elif g3.passed and g4.passed:
        verdict = "PROMOTION_READY"
    else:
        verdict = "SHADOW_READY"

    results["verdict"] = verdict
    results["promotion_approved"] = verdict == "PROMOTION_READY"
    results["current_status"] = (
        "Shadow mode active. Public output unchanged. "
        "Gate 3 requires 5+ shadow matches. "
        "Gate 4 requires 20+ matches with out-of-sample improvement."
    )

    for g in gates:
        log.info(
            "Gate %d (%s): %s — %s",
            g.gate, g.name, "PASS" if g.passed else "FAIL", g.reason,
        )

    return results
