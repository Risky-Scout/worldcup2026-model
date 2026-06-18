"""
WizardOfOdds backward-compatibility contract adapter.

ONE JOB: given a raw internal prediction dict (new model output), produce an
output dict that is backward-compatible with the existing WizardOfOdds JSON
schema.

Rules enforced by this module:
  - ALL existing keys are preserved unchanged.
  - New keys are ONLY added under approved namespaces:
      team_strength, model_diagnostics, shadow_model, clv_diagnostics
  - Additive keys are only injected when the corresponding feature flag is
    enabled (WC_USE_EGM_FOR_PUBLIC, etc.).
  - validate_output_contract() returns a list of violation strings; an empty
    list means the contract is satisfied.
"""
from __future__ import annotations

import copy
from typing import Any

# ---------------------------------------------------------------------------
# Approved namespaces for new additive keys
# ---------------------------------------------------------------------------
_APPROVED_NAMESPACES: frozenset[str] = frozenset(
    {"team_strength", "model_diagnostics", "shadow_model", "clv_diagnostics"}
)

# ---------------------------------------------------------------------------
# REQUIRED_PUBLIC_KEYS — the frozen set of keys that MUST be present in every
# published prediction dict (top-level prediction object).  Discovered from
# data/published/2026-06-18.json on 2026-06-18.
# ---------------------------------------------------------------------------
REQUIRED_PUBLIC_KEYS: frozenset[str] = frozenset(
    {
        "regulation_only",
        "extra_time_excluded",
        "penalty_shootout_excluded",
        "prediction_mode",
        "composite_model",
        "composite_sources",
        "pure_parametric_model",
        "odds_used",
        "odds_timestamp",
        "lineups_known",
        "arbitrary_score_lookup_supported",
        "max_goals",
        "tail_mass_exact",
        "tail_mass_display",
        "tail_threshold",
        "tail_policy",
        "core_grid_tail_mass",
        "tail_event_buckets",
        "regulation_score_pmf_grid",
        "expected_home_goals",
        "expected_away_goals",
        "derived_markets",
        "top_scorelines",
        "composite_rating_markets",
        "composite_expected_home_goals",
        "composite_expected_away_goals",
        "pure_model_markets",
        "pure_model_expected_home_goals",
        "pure_model_expected_away_goals",
        "market_implied_markets",
        "market_correct_score_probs",
        "composite_vs_market_differences",
        "model_vs_market_differences",
        "reconciliation_method",
        "warnings",
        "consistency_errors",
        "edge_report",
    }
)

# ---------------------------------------------------------------------------
# REQUIRED_MARKET_KEYS — the standard market probability keys present inside
# derived_markets / composite_rating_markets / etc.
# ---------------------------------------------------------------------------
REQUIRED_MARKET_KEYS: frozenset[str] = frozenset(
    {
        "home_win",
        "draw",
        "away_win",
        "btts_yes",
        "btts_no",
        "win_to_nil_home",
        "win_to_nil_away",
        "double_chance_1x",
        "double_chance_x2",
        "double_chance_12",
        "draw_no_bet_home",
        "draw_no_bet_away",
        "expected_points_home",
        "expected_points_away",
        "asian_handicap_home_-0.5",
        "asian_handicap_away_-0.5",
        "over_0.5",
        "under_0.5",
        "over_1.5",
        "under_1.5",
        "over_2.5",
        "under_2.5",
        "over_3.5",
        "under_3.5",
        "over_4.5",
        "under_4.5",
        "over_5.5",
        "under_5.5",
        "over_6.5",
        "under_6.5",
    }
)

# ---------------------------------------------------------------------------
# REQUIRED_MATCH_KEYS — top-level keys on each match object in published JSON
# ---------------------------------------------------------------------------
REQUIRED_MATCH_KEYS: frozenset[str] = frozenset(
    {
        "match_id",
        "home_team",
        "away_team",
        "stage",
        "stadium",
        "match_datetime_utc",
        "match_date_et",
        "status",
        "publish_mode",
        "composite_model_used",
        "composite_sources",
        "pure_parametric_model",
        "market_blend_alpha",
        "market_quality",
        "home_prior",
        "away_prior",
        "n_vendors_1x2",
        "n_correct_score_outcomes",
        "n_cs_vendors",
        "odds_timestamp",
        "prediction",
    }
)

# ---------------------------------------------------------------------------
# apply_contract
# ---------------------------------------------------------------------------

def apply_contract(
    legacy_prediction: dict,
    team_strength: dict | None = None,
    shadow_model: dict | None = None,
    clv_diagnostics: dict | None = None,
    model_diagnostics: dict | None = None,
) -> dict:
    """
    Merge new additive objects into a legacy prediction dict.

    Never removes or renames any existing key.
    Only adds new keys under approved namespaces:
        team_strength, shadow_model, clv_diagnostics, model_diagnostics

    Raises ValueError if WC_BREAKING_SCHEMA_CHANGES_ALLOWED=False and any
    key from REQUIRED_PUBLIC_KEYS is missing from legacy_prediction.

    Returns a shallow copy of legacy_prediction with additive keys appended.
    """
    # Import here to avoid circular imports at module load time
    from wc2026 import config  # noqa: PLC0415

    if not config.WC_BREAKING_SCHEMA_CHANGES_ALLOWED:
        missing = REQUIRED_PUBLIC_KEYS - set(legacy_prediction.keys())
        if missing:
            raise ValueError(
                f"Contract violation: required public keys missing from prediction: "
                f"{sorted(missing)}"
            )

    result = copy.copy(legacy_prediction)

    if team_strength is not None and config.WC_USE_EGM_FOR_PUBLIC:
        result["team_strength"] = team_strength

    if shadow_model is not None and config.WC_EGM_SHADOW_MODE:
        result["shadow_model"] = shadow_model

    if clv_diagnostics is not None and config.WC_USE_NEW_CLV_REPORTING:
        result["clv_diagnostics"] = clv_diagnostics

    if model_diagnostics is not None:
        result["model_diagnostics"] = model_diagnostics

    return result


# ---------------------------------------------------------------------------
# validate_output_contract
# ---------------------------------------------------------------------------

def validate_output_contract(
    output: dict,
    baseline: dict,
    allow_new_keys: bool = True,
    probability_tolerance: float = 1e-9,
) -> list[str]:
    """
    Compare *output* against *baseline* and return a list of violations.

    Violations include:
      - missing key  (a key in baseline not present in output)
      - renamed key  (treated as: key present in baseline but absent in output)
      - changed probability value beyond *probability_tolerance*
      - new namespace key injected when WC_USE_EGM_FOR_PUBLIC is False

    An empty list means the contract is satisfied.
    """
    from wc2026 import config  # noqa: PLC0415

    violations: list[str] = []

    baseline_keys = set(baseline.keys())
    output_keys = set(output.keys())

    # Check for missing keys
    for key in baseline_keys:
        if key not in output_keys:
            violations.append(f"missing_key: '{key}' present in baseline but absent in output")

    # Check for removed required public keys
    for key in REQUIRED_PUBLIC_KEYS:
        if key not in output_keys:
            violations.append(f"missing_required_key: '{key}' absent from output")

    # Check probability values for shared numeric keys
    for key in baseline_keys & output_keys:
        b_val = baseline[key]
        o_val = output[key]
        if isinstance(b_val, float) and isinstance(o_val, float):
            if abs(b_val - o_val) > probability_tolerance:
                violations.append(
                    f"value_changed: '{key}' baseline={b_val} output={o_val} "
                    f"delta={abs(b_val - o_val):.2e}"
                )
        elif isinstance(b_val, dict) and isinstance(o_val, dict):
            for sub_key in set(b_val.keys()):
                if sub_key not in o_val:
                    violations.append(
                        f"missing_subkey: '{key}.{sub_key}' absent from output"
                    )
                elif isinstance(b_val[sub_key], float) and isinstance(o_val[sub_key], float):
                    delta = abs(b_val[sub_key] - o_val[sub_key])
                    if delta > probability_tolerance:
                        violations.append(
                            f"value_changed: '{key}.{sub_key}' baseline={b_val[sub_key]} "
                            f"output={o_val[sub_key]} delta={delta:.2e}"
                        )

    # Check that unapproved namespace keys are not injected when flags are off
    if not config.WC_USE_EGM_FOR_PUBLIC and "team_strength" in output_keys:
        violations.append(
            "namespace_leak: 'team_strength' present in output but WC_USE_EGM_FOR_PUBLIC=False"
        )

    if not allow_new_keys:
        unexpected = output_keys - baseline_keys - _APPROVED_NAMESPACES
        for key in sorted(unexpected):
            violations.append(f"unexpected_key: '{key}' not in baseline and not an approved namespace")

    return violations
