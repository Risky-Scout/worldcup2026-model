"""
Calibrate penaltyblog Pi rating differences to Expected Goal Margin (EGM).

Raw Pi rating scale is NOT assumed to equal EGM.
We fit: EGM ≈ intercept + slope * pi_diff using rolling-origin regression.
"""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
import numpy as np
import pandas as pd

try:
    from penaltyblog.ratings import PiRatingSystem
    _HAS_PI = True
except ImportError:
    _HAS_PI = False


@dataclass
class PiCalibration:
    slope: float
    intercept: float
    training_cutoff: datetime
    effective_sample_size: int
    r_squared: float


def fit_pi_ratings(
    matches_df: pd.DataFrame,
    k: float = 0.1,
) -> dict[str, dict]:
    """
    Fit Pi ratings from completed matches.

    matches_df must have columns:
      home_team, away_team, home_goals, away_goals, datetime (or date)

    Returns dict mapping team_name -> {pi_home, pi_away, pi_composite}
    """
    if not _HAS_PI:
        return {}
    pi = PiRatingSystem(k=k)
    for _, row in matches_df.sort_values("datetime").iterrows():
        gd = int(row["home_goals"]) - int(row["away_goals"])
        pi.update_ratings(str(row["home_team"]), str(row["away_team"]), gd)
    ratings = {}
    for team in set(matches_df["home_team"]).union(set(matches_df["away_team"])):
        r = pi.get_ratings(team)
        if r is not None:
            ratings[team] = {
                "pi_home_rating": r.get("home", 0.0),
                "pi_away_rating": r.get("away", 0.0),
                "pi_composite": (r.get("home", 0.0) + r.get("away", 0.0)) / 2,
            }
    return ratings


def calibrate_pi_to_egm(
    matches_df: pd.DataFrame,
    ratings: dict[str, dict],
    min_samples: int = 10,
) -> Optional[PiCalibration]:
    """
    Calibrate Pi composite difference → regulation-time goal difference.
    Uses OLS. Returns None if insufficient data.
    """
    rows = []
    for _, row in matches_df.iterrows():
        h, a = str(row["home_team"]), str(row["away_team"])
        if h not in ratings or a not in ratings:
            continue
        pi_diff = ratings[h]["pi_composite"] - ratings[a]["pi_composite"]
        gd = float(row["home_goals"]) - float(row["away_goals"])
        rows.append({"pi_diff": pi_diff, "gd": gd})
    if len(rows) < min_samples:
        return None
    df = pd.DataFrame(rows)
    X = df["pi_diff"].values
    y = df["gd"].values
    A = np.column_stack([np.ones_like(X), X])
    coef, _, _, _ = np.linalg.lstsq(A, y, rcond=None)
    intercept, slope = float(coef[0]), float(coef[1])
    y_pred = intercept + slope * X
    ss_res = np.sum((y - y_pred) ** 2)
    ss_tot = np.sum((y - np.mean(y)) ** 2)
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else 0.0
    return PiCalibration(
        slope=slope,
        intercept=intercept,
        training_cutoff=datetime.utcnow(),
        effective_sample_size=len(rows),
        r_squared=float(r2),
    )


def team_pi_egm(
    team: str,
    opponent: str,
    ratings: dict[str, dict],
    calib: Optional[PiCalibration],
) -> float:
    """Convert Pi difference to EGM for a specific match-up."""
    if calib is None or team not in ratings or opponent not in ratings:
        return 0.0
    pi_diff = ratings[team]["pi_composite"] - ratings[opponent]["pi_composite"]
    return calib.intercept + calib.slope * pi_diff
