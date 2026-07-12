"""
Fallback priors for TeamMarginRating when data is unavailable.

Tier 6: Confederation prior
Tier 7: Global World Cup average fallback

Sources hierarchy:
  1. market_ability   — current match odds
  2. futures_ability  — tournament futures market
  3. pi_elo           — Pi/Elo from completed matches
  4. qualifying       — qualifying goal-difference
  5. player_roster    — player/roster strength
  6. confederation    — confederation average prior
  7. global_fallback  — WC average (0.0 EGM)
"""
from __future__ import annotations

# Confederation prior version: v1.0 (2026-06-18)
# Source: manual calibration from 2006–2022 World Cup average goal margins
# Status: TIER-6 FALLBACK ONLY — these are informative priors, not fitted estimates
# These must eventually be replaced by rolling-origin fitted values once
# sufficient 2026 match data is available (recommended: ≥ 8 completed matches per confederation).
# Do not treat these as empirically validated model coefficients.
CONFEDERATION_PRIOR_VERSION = "v1.0-manual-2026-06-18"
CONFEDERATION_PRIOR_STATUS = "informative_prior_not_fitted"

# Confederation EGM priors (relative to WC average = 0.0)
# Based on historical World Cup performance (2006–2022)
CONFEDERATION_PRIORS: dict[str, float] = {
    "UEFA": 0.15,
    "CONMEBOL": 0.12,
    "CONCACAF": -0.05,
    "CAF": -0.10,
    "AFC": -0.08,
    "OFC": -0.20,
    "unknown": 0.0,
}

# Uncertainty increment per missing tier
UNCERTAINTY_PER_MISSING_TIER: float = 1.0 / 7.0  # ~0.143 per tier


SOURCE_TIER_ORDER = [
    "market_ability",
    "futures_ability",
    "pi_elo",
    "qualifying",
    "player_roster",
    "confederation",
    "global_fallback",
]


def confederation_prior_egm(confederation: str | None) -> float:
    """Return EGM prior for a confederation."""
    if confederation is None:
        return CONFEDERATION_PRIORS["unknown"]
    # Normalize common variants
    conf = str(confederation).upper().strip()
    # Exact match first
    if conf in CONFEDERATION_PRIORS:
        return CONFEDERATION_PRIORS[conf]
    # Common aliases
    _ALIASES = {"AFC": "AFC", "CAF": "CAF", "CONCACAF": "CONCACAF",
                "CONMEBOL": "CONMEBOL", "OFC": "OFC", "UEFA": "UEFA",
                "ASIA": "AFC", "AFRICA": "CAF", "EUROPE": "UEFA",
                "NORTH AMERICA": "CONCACAF", "SOUTH AMERICA": "CONMEBOL"}
    for alias, canon in _ALIASES.items():
        if alias in conf:
            return CONFEDERATION_PRIORS[canon]
    return CONFEDERATION_PRIORS["unknown"]


def compute_uncertainty(sources_used: list[str]) -> float:
    """
    Compute uncertainty_level based on which tiers contributed.
    0.0 = all tiers available (maximum information)
    1.0 = only global fallback used (minimum information)
    """
    tiers_present = sum(1 for tier in SOURCE_TIER_ORDER if tier in sources_used)
    # At least 1 tier always used (global_fallback)
    tiers_missing = max(0, len(SOURCE_TIER_ORDER) - 1 - tiers_present)
    # Scale: all 6 non-fallback tiers missing = 1.0
    return min(1.0, tiers_missing * UNCERTAINTY_PER_MISSING_TIER)


def build_fallback_egm(
    team_name: str,
    team_id: int,
    confederation: str | None,
    component_egms: dict[str, float | None],
    wc_total_baseline: float = 2.65,
) -> tuple[float, list[str], float]:
    """
    Build a team EGM using the fallback hierarchy.

    component_egms: dict mapping source tier name → EGM value (None if unavailable)
      Keys: "market_ability", "futures_ability", "pi_elo", "qualifying",
            "player_roster"

    Returns: (egm, sources_used, uncertainty_level)
    """
    sources_used = []
    contributions = []
    weights = []

    # Tier weights (higher = more trusted)
    tier_weights = {
        "market_ability": 0.35,
        "futures_ability": 0.15,
        "pi_elo": 0.25,
        "qualifying": 0.10,
        "player_roster": 0.10,
        "confederation": 0.05,
    }

    for tier in SOURCE_TIER_ORDER[:-1]:  # skip global_fallback for now
        val = component_egms.get(tier)
        if val is not None and not (val != val):  # not None and not NaN
            contributions.append(val * tier_weights[tier])
            weights.append(tier_weights[tier])
            sources_used.append(tier)

    if weights:
        # Weighted average of available tiers, renormalized
        total_weight = sum(weights)
        egm = sum(contributions) / total_weight
    else:
        # Tier 6: confederation prior
        conf_egm = confederation_prior_egm(confederation)
        if conf_egm != 0.0:
            egm = conf_egm
            sources_used.append("confederation")
        else:
            # Tier 7: global fallback
            egm = 0.0
            sources_used.append("global_fallback")

    uncertainty = compute_uncertainty(sources_used)
    return float(egm), sources_used, float(uncertainty)
