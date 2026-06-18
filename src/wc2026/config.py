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
