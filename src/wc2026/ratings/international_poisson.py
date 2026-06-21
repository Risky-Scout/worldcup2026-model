"""
International Poisson abilities fitted on full international match history.

Reads `data/external/international_results.csv` (Kaggle 1872-2026 dataset).
Applies 3-year half-life exponential time decay on match dates.
Also loads `data/external/former_names.csv` to map historical team names
(e.g. "West Germany" → "Germany", "Zaire" → "DR Congo") before fitting.
Returns per-team {"offensive_ability": float, "defensive_ability": float}.

If the CSV file does not exist, returns an empty dict (graceful fallback).
"""
from __future__ import annotations

import logging
import math
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

log = logging.getLogger(__name__)

_HALF_LIFE_YEARS = 3.0
_DECAY_RATE = math.log(2.0) / _HALF_LIFE_YEARS  # per-year decay constant

_WC_AVG = 1.30  # goal average used as league-average baseline

# Extra aliases for WC 2026 team name normalization not covered by former_names.csv
EXTRA_ALIASES: dict[str, str] = {
    "Korea Republic": "South Korea",
    "IR Iran": "Iran",
    "USA": "United States",
    "Türkiye": "Turkey",
    "Turkey": "Turkey",
    "Ivory Coast": "Côte d'Ivoire",
    "Cote d'Ivoire": "Côte d'Ivoire",
    "Bosnia-Herzegovina": "Bosnia & Herzegovina",
    "Cape Verde": "Cabo Verde",
}


def _load_name_mapping(former_names_path: Path) -> dict[str, str]:
    """
    Build a former_name → current_name mapping from former_names.csv.

    For each (former, current) pair uses the most recent `current` value
    (by end_date) to handle chains like Yugoslavia → Serbia.
    """
    if not former_names_path.exists():
        log.debug("former_names.csv not found at %s — skipping name mapping", former_names_path)
        return {}

    try:
        df = pd.read_csv(former_names_path, low_memory=False)
    except Exception as exc:
        log.warning("Could not read %s: %s", former_names_path, exc)
        return {}

    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]
    required = {"current", "former", "end_date"}
    if not required.issubset(set(df.columns)):
        log.warning("former_names.csv missing columns: %s", required - set(df.columns))
        return {}

    df["end_date"] = pd.to_datetime(df["end_date"], errors="coerce")
    # Sort so the most recent end_date row wins when a former name appears multiple times
    df = df.sort_values("end_date", ascending=True, na_position="first")

    mapping: dict[str, str] = {}
    for _, row in df.iterrows():
        former = str(row["former"]).strip()
        current = str(row["current"]).strip()
        if former and current and former != "nan" and current != "nan":
            mapping[former] = current

    # Overlay EXTRA_ALIASES (they take precedence for WC 2026 normalization)
    mapping.update(EXTRA_ALIASES)

    log.info("international_poisson: loaded %d name aliases", len(mapping))
    return mapping


def _compute_decay_weight(match_date: pd.Timestamp, reference_date: pd.Timestamp) -> float:
    """Exponential time-decay weight with 3-year half-life."""
    years_ago = max((reference_date - match_date).days / 365.25, 0.0)
    return math.exp(-_DECAY_RATE * years_ago)


def fit_international_poisson(
    csv_path: Optional[Path] = None,
    former_names_path: Optional[Path] = None,
    reference_date: Optional[pd.Timestamp] = None,
) -> dict[str, dict[str, float]]:
    """
    Fit a simple bivariate Poisson on the Kaggle international results dataset.

    Parameters
    ----------
    csv_path            Path to international_results.csv.  Defaults to
                        data/external/international_results.csv relative to repo root.
    former_names_path   Path to former_names.csv.  Defaults to
                        data/external/former_names.csv relative to repo root.
    reference_date      Reference date for decay weighting (default: today).

    Returns
    -------
    dict: team_name → {"offensive_ability": float, "defensive_ability": float}
    Empty dict if data file not found or fitting fails.
    """
    repo_root = Path(__file__).resolve().parents[3]

    if csv_path is None:
        csv_path = repo_root / "data" / "external" / "international_results.csv"

    if former_names_path is None:
        former_names_path = repo_root / "data" / "external" / "former_names.csv"

    if not csv_path.exists():
        log.debug("international_results.csv not found at %s — skipping", csv_path)
        return {}

    if reference_date is None:
        reference_date = pd.Timestamp.now()

    try:
        df = pd.read_csv(csv_path, low_memory=False)
    except Exception as exc:
        log.warning("Could not read %s: %s", csv_path, exc)
        return {}

    # Normalise column names
    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]

    # Required columns: date, home_team, away_team, home_score, away_score
    required = {"date", "home_team", "away_team", "home_score", "away_score"}
    if not required.issubset(set(df.columns)):
        log.warning("international_results.csv missing columns: %s", required - set(df.columns))
        return {}

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df[df["date"].notna()].copy()
    df["home_score"] = pd.to_numeric(df["home_score"], errors="coerce")
    df["away_score"] = pd.to_numeric(df["away_score"], errors="coerce")
    df = df[df["home_score"].notna() & df["away_score"].notna()].copy()
    df["home_score"] = df["home_score"].astype(int)
    df["away_score"] = df["away_score"].astype(int)

    log.info("international_poisson: %d matches loaded", len(df))

    # Load name mapping and apply to team columns
    name_map = _load_name_mapping(former_names_path)
    if name_map:
        df["home_team"] = df["home_team"].map(lambda x: name_map.get(str(x).strip(), str(x).strip()))
        df["away_team"] = df["away_team"].map(lambda x: name_map.get(str(x).strip(), str(x).strip()))
        log.info("international_poisson: name mapping applied")

    # Compute decay weights
    df["weight"] = df["date"].apply(lambda d: _compute_decay_weight(d, reference_date))

    # Simple iterative attack/defense estimation (Dixon-Coles style, 1 EM pass)
    # Initialize all teams at league average
    teams = set(df["home_team"].tolist()) | set(df["away_team"].tolist())
    attack = {t: _WC_AVG for t in teams}
    defense = {t: _WC_AVG for t in teams}

    # Run a few EM-style iterations
    for _iter in range(10):
        new_attack: dict[str, list] = {t: [] for t in teams}
        new_defense: dict[str, list] = {t: [] for t in teams}

        for _, row in df.iterrows():
            ht = str(row["home_team"])
            at = str(row["away_team"])
            hg = float(row["home_score"])
            ag = float(row["away_score"])
            w = float(row["weight"])

            # Expected goals
            lam_h = attack.get(ht, _WC_AVG) * defense.get(at, _WC_AVG) / _WC_AVG
            lam_a = attack.get(at, _WC_AVG) * defense.get(ht, _WC_AVG) / _WC_AVG

            lam_h = max(lam_h, 1e-6)
            lam_a = max(lam_a, 1e-6)

            # Weighted score signal
            new_attack[ht].append((w, hg / lam_h * attack.get(ht, _WC_AVG)))
            new_attack[at].append((w, ag / lam_a * attack.get(at, _WC_AVG)))
            new_defense[ht].append((w, ag / lam_a * defense.get(ht, _WC_AVG)))
            new_defense[at].append((w, hg / lam_h * defense.get(at, _WC_AVG)))

        for t in teams:
            if new_attack[t]:
                ws = [x[0] for x in new_attack[t]]
                vs = [x[1] for x in new_attack[t]]
                attack[t] = float(np.average(vs, weights=ws))
            if new_defense[t]:
                ws = [x[0] for x in new_defense[t]]
                vs = [x[1] for x in new_defense[t]]
                defense[t] = float(np.average(vs, weights=ws))

        # Re-centre
        all_att = list(attack.values())
        all_def = list(defense.values())
        att_mean = float(np.mean(all_att))
        def_mean = float(np.mean(all_def))
        if att_mean > 1e-6:
            attack = {t: v / att_mean * _WC_AVG for t, v in attack.items()}
        if def_mean > 1e-6:
            defense = {t: v / def_mean * _WC_AVG for t, v in defense.items()}

    result = {
        t: {
            "offensive_ability": round(float(np.clip(attack.get(t, _WC_AVG), 0.3, 5.0)), 4),
            "defensive_ability": round(float(np.clip(defense.get(t, _WC_AVG), 0.3, 5.0)), 4),
        }
        for t in teams
    }

    log.info(
        "international_poisson: fitted %d teams  att_range=[%.3f, %.3f]  def_range=[%.3f, %.3f]",
        len(result),
        min(v["offensive_ability"] for v in result.values()),
        max(v["offensive_ability"] for v in result.values()),
        min(v["defensive_ability"] for v in result.values()),
        max(v["defensive_ability"] for v in result.values()),
    )

    return result


def load_international_abilities(
    csv_path: Optional[Path] = None,
    former_names_path: Optional[Path] = None,
    reference_date: Optional[pd.Timestamp] = None,
) -> dict[str, dict[str, float]]:
    """Convenience wrapper — same as fit_international_poisson."""
    return fit_international_poisson(
        csv_path=csv_path,
        former_names_path=former_names_path,
        reference_date=reference_date,
    )
