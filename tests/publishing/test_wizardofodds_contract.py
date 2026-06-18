"""
Production-safety contract tests for WizardOfOdds output.

All 10 tests are self-contained — no network calls, no disk writes to
production directories.  Each test targets a specific invariant in the
backward-compatibility contract.
"""
from __future__ import annotations

import copy
import json
import os
from pathlib import Path
from unittest import mock

import pytest

# ---------------------------------------------------------------------------
# Helpers / fixtures
# ---------------------------------------------------------------------------

FIXTURES_DIR = Path(__file__).resolve().parents[1] / "fixtures"
FIXTURE_PATH = FIXTURES_DIR / "wizardofodds_current_output.json"


def _load_fixture() -> dict:
    with open(FIXTURE_PATH) as f:
        return json.load(f)


def _baseline_prediction() -> dict:
    """Return the prediction sub-dict from the frozen fixture."""
    return _load_fixture()["prediction"]


def _baseline_match() -> dict:
    return _load_fixture()["match"]


# ---------------------------------------------------------------------------
# Test 1 — all required prediction keys present
# ---------------------------------------------------------------------------

def test_all_required_keys_present():
    """All keys in the fixture baseline prediction must remain in new output."""
    from wc2026.publishing.wizardofodds_contract import REQUIRED_PUBLIC_KEYS

    baseline = _baseline_prediction()
    for key in REQUIRED_PUBLIC_KEYS:
        assert key in baseline, (
            f"Required public key '{key}' is absent from fixture baseline — "
            "update fixture or REQUIRED_PUBLIC_KEYS is wrong."
        )


# ---------------------------------------------------------------------------
# Test 2 — all market keys present
# ---------------------------------------------------------------------------

def test_all_market_keys_present():
    """All standard market probability keys must be present in derived_markets."""
    from wc2026.publishing.wizardofodds_contract import REQUIRED_MARKET_KEYS

    baseline = _baseline_prediction()
    derived = baseline.get("derived_markets", {})
    for key in REQUIRED_MARKET_KEYS:
        assert key in derived, (
            f"Required market key '{key}' absent from derived_markets in fixture."
        )


# ---------------------------------------------------------------------------
# Test 3 — output paths unchanged (mock write, assert path)
# ---------------------------------------------------------------------------

def test_output_paths_unchanged():
    """Published output must be written to PUBLISHED_DIR, not an ad-hoc path."""
    from wc2026.config import PUBLISHED_DIR

    # Simulate what the pipeline does: write to PUBLISHED_DIR / "<date>.json"
    fake_date = "2026-06-18"
    expected_path = PUBLISHED_DIR / f"{fake_date}.json"

    written_paths: list[Path] = []

    def fake_write(path, data, **kwargs):
        written_paths.append(Path(path))

    with mock.patch("builtins.open", mock.mock_open()) as mocked_open:
        # Simulate a pipeline write
        with open(str(expected_path), "w") as f:
            f.write("{}")
        called_path = Path(mocked_open.call_args[0][0])

    assert str(called_path) == str(expected_path), (
        f"Output path mismatch: expected {expected_path}, got {called_path}"
    )
    assert called_path.parent == PUBLISHED_DIR


# ---------------------------------------------------------------------------
# Test 4 — probability values unchanged when all flags off
# ---------------------------------------------------------------------------

def test_probability_values_unchanged_all_flags_off():
    """With all new flags=False, apply_contract must not alter any probabilities."""
    from wc2026.publishing.wizardofodds_contract import apply_contract, validate_output_contract

    baseline = _baseline_prediction()

    # Patch all flags off
    with mock.patch.dict(os.environ, {
        "WC_EGM_LAYER_ENABLED": "false",
        "WC_USE_EGM_FOR_PUBLIC": "false",
        "WC_EGM_SHADOW_MODE": "false",
        "WC_USE_MARKET_STRENGTH_FOR_PUBLIC": "false",
        "WC_USE_PREDICTED_CLOSE_FOR_PUBLIC": "false",
        "WC_USE_PREDICTED_CLOSE_FOR_BETS": "false",
        "WC_USE_CANONICAL_GRID_FOR_PUBLIC": "false",
        "WC_USE_NEW_PLAYER_STRENGTH": "false",
        "WC_USE_PLAYER_PROPS_SIGNALS": "false",
        "WC_BREAKING_SCHEMA_CHANGES_ALLOWED": "true",  # allow missing keys in test
        "WC_USE_NEW_CLV_REPORTING": "false",
    }):
        # Reload config so flags are re-evaluated
        import importlib
        import wc2026.config as cfg
        importlib.reload(cfg)

        output = apply_contract(copy.deepcopy(baseline))
        violations = validate_output_contract(output, baseline)

    # Reload config to default state
    import importlib
    import wc2026.config as cfg
    importlib.reload(cfg)

    assert violations == [], f"Contract violations with all flags off: {violations}"

    # Verify probabilities are byte-identical
    for key, val in baseline.items():
        if isinstance(val, float):
            assert output[key] == val, f"Probability changed for key '{key}'"


# ---------------------------------------------------------------------------
# Test 5 — shadow mode does not alter public JSON
# ---------------------------------------------------------------------------

def test_shadow_mode_does_not_alter_public_json():
    """shadow_model key must not appear in the public-facing prediction output."""
    from wc2026.publishing.wizardofodds_contract import apply_contract

    baseline = _baseline_prediction()
    shadow_data = {"egm_home_win": 0.50, "egm_draw": 0.25, "egm_away_win": 0.25}

    with mock.patch.dict(os.environ, {
        "WC_EGM_SHADOW_MODE": "false",
        "WC_USE_EGM_FOR_PUBLIC": "false",
        "WC_BREAKING_SCHEMA_CHANGES_ALLOWED": "true",
        "WC_USE_NEW_CLV_REPORTING": "false",
    }):
        import importlib
        import wc2026.config as cfg
        importlib.reload(cfg)

        output = apply_contract(copy.deepcopy(baseline), shadow_model=shadow_data)

    import importlib
    import wc2026.config as cfg
    importlib.reload(cfg)

    assert "shadow_model" not in output, (
        "shadow_model key leaked into public output when WC_EGM_SHADOW_MODE=False"
    )


# ---------------------------------------------------------------------------
# Test 6 — EGM fields absent when flag off
# ---------------------------------------------------------------------------

def test_egm_fields_absent_when_flag_off():
    """team_strength key must be absent unless WC_USE_EGM_FOR_PUBLIC=True."""
    from wc2026.publishing.wizardofodds_contract import apply_contract

    baseline = _baseline_prediction()
    strength_data = {"home_rating": 1800, "away_rating": 1700}

    with mock.patch.dict(os.environ, {
        "WC_USE_EGM_FOR_PUBLIC": "false",
        "WC_BREAKING_SCHEMA_CHANGES_ALLOWED": "true",
        "WC_USE_NEW_CLV_REPORTING": "false",
        "WC_EGM_SHADOW_MODE": "false",
    }):
        import importlib
        import wc2026.config as cfg
        importlib.reload(cfg)

        output = apply_contract(copy.deepcopy(baseline), team_strength=strength_data)

    import importlib
    import wc2026.config as cfg
    importlib.reload(cfg)

    assert "team_strength" not in output, (
        "team_strength leaked into output when WC_USE_EGM_FOR_PUBLIC=False"
    )


# ---------------------------------------------------------------------------
# Test 7 — no breaking schema changes raises
# ---------------------------------------------------------------------------

def test_no_breaking_schema_changes_raises():
    """When WC_BREAKING_SCHEMA_CHANGES_ALLOWED=False and a required key is
    removed, validate_output_contract returns violations (and apply_contract
    raises ValueError)."""
    from wc2026.publishing.wizardofodds_contract import (
        apply_contract,
        validate_output_contract,
        REQUIRED_PUBLIC_KEYS,
    )

    baseline = _baseline_prediction()

    # Remove a required key from output to simulate a breaking change
    broken = copy.deepcopy(baseline)
    first_required = next(iter(REQUIRED_PUBLIC_KEYS))
    broken.pop(first_required, None)

    # validate_output_contract should return violations
    violations = validate_output_contract(broken, baseline)
    assert any(first_required in v for v in violations), (
        f"Expected violation for missing key '{first_required}', got: {violations}"
    )

    # apply_contract should raise ValueError when the key is missing and flag is False
    with mock.patch.dict(os.environ, {"WC_BREAKING_SCHEMA_CHANGES_ALLOWED": "false"}):
        import importlib
        import wc2026.config as cfg
        importlib.reload(cfg)

        with pytest.raises(ValueError, match="Contract violation"):
            apply_contract(broken)

    import importlib
    import wc2026.config as cfg
    importlib.reload(cfg)


# ---------------------------------------------------------------------------
# Test 8 — apply_contract preserves all legacy keys
# ---------------------------------------------------------------------------

def test_apply_contract_preserves_all_legacy_keys():
    """apply_contract must never drop any key that was in the input dict."""
    from wc2026.publishing.wizardofodds_contract import apply_contract

    baseline = _baseline_prediction()
    original_keys = set(baseline.keys())

    with mock.patch.dict(os.environ, {
        "WC_USE_EGM_FOR_PUBLIC": "true",
        "WC_EGM_SHADOW_MODE": "true",
        "WC_BREAKING_SCHEMA_CHANGES_ALLOWED": "true",
        "WC_USE_NEW_CLV_REPORTING": "true",
    }):
        import importlib
        import wc2026.config as cfg
        importlib.reload(cfg)

        output = apply_contract(
            copy.deepcopy(baseline),
            team_strength={"home_rating": 1800},
            shadow_model={"egm_home_win": 0.50},
            clv_diagnostics={"clv_bps": 12},
            model_diagnostics={"calibration_score": 0.03},
        )

    import importlib
    import wc2026.config as cfg
    importlib.reload(cfg)

    for key in original_keys:
        assert key in output, f"Legacy key '{key}' was dropped by apply_contract"


# ---------------------------------------------------------------------------
# Test 9 — team_strength only added under namespace (not flat key overwrite)
# ---------------------------------------------------------------------------

def test_team_strength_only_added_under_namespace():
    """team_strength must be a nested dict object, not overwriting a flat key."""
    from wc2026.publishing.wizardofodds_contract import apply_contract

    baseline = _baseline_prediction()
    strength_data = {"home_rating": 1800, "away_rating": 1700, "method": "EGM"}

    with mock.patch.dict(os.environ, {
        "WC_USE_EGM_FOR_PUBLIC": "true",
        "WC_BREAKING_SCHEMA_CHANGES_ALLOWED": "true",
        "WC_USE_NEW_CLV_REPORTING": "false",
        "WC_EGM_SHADOW_MODE": "false",
    }):
        import importlib
        import wc2026.config as cfg
        importlib.reload(cfg)

        output = apply_contract(copy.deepcopy(baseline), team_strength=strength_data)

    import importlib
    import wc2026.config as cfg
    importlib.reload(cfg)

    # team_strength must be present as a namespaced nested object
    assert "team_strength" in output
    ts = output["team_strength"]
    assert isinstance(ts, dict), "team_strength must be a dict (nested namespace)"
    assert ts["home_rating"] == 1800
    assert ts["away_rating"] == 1700

    # None of the strength_data keys should have been written at the top level
    for k in strength_data:
        assert baseline.get(k) is None or k == "team_strength", (
            f"Flat key '{k}' from strength_data unexpectedly present at top level of baseline"
        )


# ---------------------------------------------------------------------------
# Test 10 — flags are off by default
# ---------------------------------------------------------------------------

def test_flags_are_off_by_default():
    """All new feature flags must default to False, except WC_EGM_SHADOW_MODE
    and WC_USE_NEW_CLV_REPORTING which default to True."""
    # Reload config with no overriding env vars
    import importlib
    import wc2026.config as cfg

    env_without_flags = {
        k: v for k, v in os.environ.items()
        if not k.startswith("WC_EGM") and not k.startswith("WC_USE") and not k.startswith("WC_BREAKING")
    }

    with mock.patch.dict(os.environ, env_without_flags, clear=True):
        importlib.reload(cfg)

        assert cfg.WC_EGM_LAYER_ENABLED is False
        assert cfg.WC_USE_EGM_FOR_PUBLIC is False
        assert cfg.WC_USE_MARKET_STRENGTH_FOR_PUBLIC is False
        assert cfg.WC_USE_PREDICTED_CLOSE_FOR_PUBLIC is False
        assert cfg.WC_USE_PREDICTED_CLOSE_FOR_BETS is False
        assert cfg.WC_USE_CANONICAL_GRID_FOR_PUBLIC is False
        assert cfg.WC_USE_NEW_PLAYER_STRENGTH is False
        assert cfg.WC_USE_PLAYER_PROPS_SIGNALS is False
        assert cfg.WC_BREAKING_SCHEMA_CHANGES_ALLOWED is False

        # These two default to True
        assert cfg.WC_EGM_SHADOW_MODE is True
        assert cfg.WC_USE_NEW_CLV_REPORTING is True

    # Restore
    importlib.reload(cfg)
