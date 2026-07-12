"""Central configuration: paths, seeds, data versions."""
from __future__ import annotations

import os
from pathlib import Path

# --------------------------------------------------------------------------
# Reproducibility
# --------------------------------------------------------------------------
RANDOM_SEED: int = 42

# --------------------------------------------------------------------------
# Paths
# --------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = REPO_ROOT / "data"
RAW_DIR = DATA_DIR / "raw" / "bdl"
PROCESSED_DIR = DATA_DIR / "processed"
PREDICTIONS_DIR = DATA_DIR / "predictions"
PUBLISHED_DIR = DATA_DIR / "published"
REPORTS_DIR = REPO_ROOT / "reports"
MODELS_DIR = REPO_ROOT / "models"

for _d in (RAW_DIR, PROCESSED_DIR, PREDICTIONS_DIR, PUBLISHED_DIR, REPORTS_DIR, MODELS_DIR):
    _d.mkdir(parents=True, exist_ok=True)

# --------------------------------------------------------------------------
# Versioning
# --------------------------------------------------------------------------
DATA_VERSION: str = os.environ.get("WC2026_DATA_VERSION", "v1")
MODEL_VERSION: str = os.environ.get("WC2026_MODEL_VERSION", "v1")
FEATURE_VERSION: str = os.environ.get("WC2026_FEATURE_VERSION", "v1")

# --------------------------------------------------------------------------
# BDL API
# --------------------------------------------------------------------------
BDL_BASE_URL = "https://api.balldontlie.io/fifa/worldcup/v1"
BDL_SEASONS = [2018, 2022, 2026]
BDL_PER_PAGE = 100
BDL_REQ_DELAY = 0.15  # seconds between requests (400 req/min < 600 GOAT limit)

# --------------------------------------------------------------------------
# Model defaults
# --------------------------------------------------------------------------
DC_WEIGHT_XI: float = float(os.environ.get("WC2026_DC_WEIGHT_XI", "0.0018"))
# xi for the 2026 WC completed match recency weighting (higher = more recent-focused).
# Overridable via env var for manual tuning without code changes.
DC_WEIGHT_XI_2026: float = float(os.environ.get("WC2026_DC_WEIGHT_XI_2026", "0.018"))
PMF_MAX_GOALS: int = 15       # penaltyblog default grid size; tail mass is tiny at 15
TAIL_WARN_THRESHOLD: float = 0.005  # warn if tail mass exceeds 0.5% (at max_goals=15)

# --------------------------------------------------------------------------
# Calibration
# --------------------------------------------------------------------------
MIN_MATCHES_FOR_CALIBRATION: int = 20
TEMPERATURE_GRID = [0.5, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.5, 2.0]

# --------------------------------------------------------------------------
# Live model
# --------------------------------------------------------------------------
LIVE_MAX_REMAINING_GOALS: int = 8
LIVE_XG_BLEND_HALFLIFE_MINUTES: float = 45.0
LIVE_MOMENTUM_WEIGHT: float = 0.02
LIVE_MOMENTUM_CAP: float = 0.20

# --------------------------------------------------------------------------
# Group incentive adjustment
# --------------------------------------------------------------------------
GROUP_INCENTIVE_PMF_LEVEL: bool = True  # When True, use PMF-level group incentive adjustment
DEFAULT_AH_LINES: list = [round(x * 0.25, 2) for x in range(-12, 13)]
TOTAL_LINES: list = [0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0, 5.5, 6.0, 6.5]

# --------------------------------------------------------------------------
# Elite model feature flags — ALL disabled by default for production safety
# Live outputs remain byte-identical when all flags below are False/default.
# Override at runtime via environment variables (set to "true" to enable).
# --------------------------------------------------------------------------
WC_EGM_LAYER_ENABLED: bool = os.getenv("WC_EGM_LAYER_ENABLED", "false").lower() == "true"
WC_EGM_SHADOW_MODE: bool = os.getenv("WC_EGM_SHADOW_MODE", "true").lower() == "true"
WC_USE_EGM_FOR_PUBLIC: bool = os.getenv("WC_USE_EGM_FOR_PUBLIC", "false").lower() == "true"
WC_USE_MARKET_STRENGTH_FOR_PUBLIC: bool = os.getenv("WC_USE_MARKET_STRENGTH_FOR_PUBLIC", "false").lower() == "true"
WC_USE_PREDICTED_CLOSE_FOR_PUBLIC: bool = os.getenv("WC_USE_PREDICTED_CLOSE_FOR_PUBLIC", "false").lower() == "true"
WC_USE_PREDICTED_CLOSE_FOR_BETS: bool = os.getenv("WC_USE_PREDICTED_CLOSE_FOR_BETS", "false").lower() == "true"
WC_USE_CANONICAL_GRID_FOR_PUBLIC: bool = os.getenv("WC_USE_CANONICAL_GRID_FOR_PUBLIC", "false").lower() == "true"
WC_USE_NEW_PLAYER_STRENGTH: bool = os.getenv("WC_USE_NEW_PLAYER_STRENGTH", "false").lower() == "true"
WC_USE_PLAYER_PROPS_SIGNALS: bool = os.getenv("WC_USE_PLAYER_PROPS_SIGNALS", "false").lower() == "true"
WC_BREAKING_SCHEMA_CHANGES_ALLOWED: bool = os.getenv("WC_BREAKING_SCHEMA_CHANGES_ALLOWED", "false").lower() == "true"
WC_USE_NEW_CLV_REPORTING: bool = os.getenv("WC_USE_NEW_CLV_REPORTING", "true").lower() == "true"

# --------------------------------------------------------------------------
# Presentation-safe mode — enables a collection of conservative runtime
# guards for public-facing outputs (demo / audit / betting-adjacent use).
#
# When PRESENTATION_SAFE_MODE=true the pipeline enforces:
#   • draw-boost heuristic suppressed (was mislabelled "top 3 advance")
#   • first-half markets suppressed (0.45 λ approximation is not validated)
#   • in-sample market-weight auto-selection disabled (use fixed default)
#   • circular edge / Kelly output blocked for market-reconciled PMFs
#   • lambda sensitivity ranges NOT labelled as confidence intervals
#   • generated_at preserved; uploaded_at added separately during upload
#
# Activate at runtime:
#   export WC_PRESENTATION_SAFE_MODE=true
# or pass --presentation-safe-mode to the pipeline CLI.
# --------------------------------------------------------------------------
PRESENTATION_SAFE_MODE: bool = os.getenv("WC_PRESENTATION_SAFE_MODE", "false").lower() == "true"

# When True, first-half markets are always suppressed regardless of safe mode.
SUPPRESS_FIRST_HALF_MARKETS: bool = os.getenv("WC_SUPPRESS_FIRST_HALF_MARKETS", "false").lower() == "true"

# When True, draw-boost heuristic is suppressed regardless of safe mode.
SUPPRESS_DRAW_BOOST: bool = os.getenv("WC_SUPPRESS_DRAW_BOOST", "false").lower() == "true"

# When True, in-sample market-weight auto-selection is disabled.
DISABLE_AUTO_MARKET_WEIGHT: bool = os.getenv("WC_DISABLE_AUTO_MARKET_WEIGHT", "false").lower() == "true"

# When True, circular edge / Kelly output is blocked for market-reconciled PMFs.
DISABLE_CIRCULAR_EDGE: bool = os.getenv("WC_DISABLE_CIRCULAR_EDGE", "false").lower() == "true"
