"""
Daily calibration for the Pi Ratings prediction engine.

Fits two parameters from completed World Cup 2026 matches:

  1. total_anchor — the expected total goals for an average match.
     Closed-form solution: mean(actual_total_goals over completed matches).
     Falls back to 2.65 (historical World Cup average) if < 5 matches.

  2. rho — Dixon-Coles low-score correlation.
     Grid search over [-0.20, 0.05] in 0.01 steps to maximise log-likelihood.
     Falls back to -0.05 if < 10 completed matches.

Both parameters are written to calibration_state.json and appended to
calibration_log.csv for a full reproducible history.

Usage (standalone):
    python pi-ratings/calibrate.py
"""
from __future__ import annotations

import csv
import json
import math
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

_REPO_ROOT = Path(__file__).resolve().parent.parent
_PI_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_PI_DIR))

from pi_model import DixonColesPMF, PiRatings

_FALLBACK_TOTAL = 2.65
_FALLBACK_RHO   = -0.05
_MIN_MATCHES_TOTAL = 5
_MIN_MATCHES_RHO   = 10
_RHO_GRID = [round(-0.20 + i * 0.01, 2) for i in range(26)]  # -0.20 … +0.05


@dataclass
class CalibrationState:
    rho: float
    total_anchor: float
    n_matches_used: int
    calibrated_at: str       # ISO 8601 UTC
    log_likelihood: float    # at fitted rho; 0.0 if fallback
    rmse_total_goals: float  # root mean sq error of total goals; 0.0 if fallback
    rho_source: str          # "fitted" | "fallback"
    total_source: str        # "fitted" | "fallback"

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "CalibrationState":
        return cls(**d)


def _poisson_log_pmf(k: int, lam: float) -> float:
    """log P(X=k) for X ~ Poisson(lam). Returns -inf for invalid."""
    if k < 0 or lam <= 0:
        return -math.inf
    return -lam + k * math.log(lam) - sum(math.log(i) for i in range(1, k + 1))


def _tau_log(h: int, a: int, lh: float, la: float, rho: float) -> float:
    """log of Dixon-Coles tau correction factor."""
    if h == 0 and a == 0:
        v = 1.0 - lh * la * rho
    elif h == 1 and a == 0:
        v = 1.0 + la * rho
    elif h == 0 and a == 1:
        v = 1.0 + lh * rho
    elif h == 1 and a == 1:
        v = 1.0 - rho
    else:
        return 0.0   # log(1) = 0
    return math.log(v) if v > 0 else -math.inf


def _match_log_likelihood(h: int, a: int, lh: float, la: float, rho: float) -> float:
    """Log-likelihood of one completed match result under the DC model."""
    return (
        _tau_log(h, a, lh, la, rho)
        + _poisson_log_pmf(h, lh)
        + _poisson_log_pmf(a, la)
    )


def _fit_rho(matches: list[dict], ratings: PiRatings, total_anchor: float) -> tuple[float, float]:
    """
    Grid search rho over _RHO_GRID to maximise total log-likelihood.

    Each match dict must have: home_team, away_team, home_goals, away_goals.
    Returns (best_rho, log_likelihood_at_best_rho).
    """
    best_rho = _FALLBACK_RHO
    best_ll  = -math.inf

    for rho in _RHO_GRID:
        ll = 0.0
        valid = 0
        for m in matches:
            h_team = m["home_team"]
            a_team = m["away_team"]
            hg = int(m["home_goals"])
            ag = int(m["away_goals"])
            margin = ratings.get_rating(h_team).composite - ratings.get_rating(a_team).composite
            lh = max(0.30, total_anchor / 2 + margin / 2)
            la = max(0.30, total_anchor / 2 - margin / 2)
            val = _match_log_likelihood(hg, ag, lh, la, rho)
            if math.isfinite(val):
                ll += val
                valid += 1
        if valid > 0 and ll > best_ll:
            best_ll = ll
            best_rho = rho

    return best_rho, best_ll


def calibrate(matches_df) -> CalibrationState:
    """
    Fit calibration parameters from a matches DataFrame.

    Expected columns: home_team, away_team, home_goals, away_goals,
                      season, status, match_datetime (or datetime).
    """
    import pandas as pd  # only used here for DataFrame handling

    # Filter to completed 2026 matches with goals
    completed = matches_df[
        (matches_df["status"] == "completed")
        & matches_df["home_goals"].notna()
        & matches_df["away_goals"].notna()
    ].copy()

    # Sort chronologically
    for col in ("match_datetime", "datetime", "date"):
        if col in completed.columns:
            completed = completed.sort_values(col)
            break

    # Build Pi ratings on ALL completed matches (same as run_ratings.py)
    ratings = PiRatings(alpha=0.15, beta=0.10)
    for _, row in completed.iterrows():
        home = str(row.get("home_team") or "")
        away = str(row.get("away_team") or "")
        hg = int(row["home_goals"])
        ag = int(row["away_goals"])
        dt = row.get("match_datetime") or row.get("datetime") or row.get("date")
        dt_str = str(dt)[:10] if dt is not None else None
        if home and away:
            ratings.update(home, away, hg, ag, match_date=dt_str)

    # Use only 2026 completed matches for calibration (in-tournament signal)
    cal_rows = completed[completed["season"] == 2026] if "season" in completed.columns else completed
    cal_matches = cal_rows.to_dict("records")
    n = len(cal_matches)

    now_utc = datetime.now(timezone.utc).isoformat()

    # ── Total anchor ──────────────────────────────────────────────────────
    if n >= _MIN_MATCHES_TOTAL:
        totals = [int(m["home_goals"]) + int(m["away_goals"]) for m in cal_matches]
        total_anchor = sum(totals) / len(totals)
        total_source = "fitted"
    else:
        total_anchor = _FALLBACK_TOTAL
        total_source = "fallback"

    # ── RMSE of total goals ───────────────────────────────────────────────
    if n >= _MIN_MATCHES_TOTAL:
        errs = []
        for m in cal_matches:
            actual = int(m["home_goals"]) + int(m["away_goals"])
            predicted = total_anchor
            errs.append((actual - predicted) ** 2)
        rmse = math.sqrt(sum(errs) / len(errs))
    else:
        rmse = 0.0

    # ── Rho ───────────────────────────────────────────────────────────────
    if n >= _MIN_MATCHES_RHO:
        rho, ll = _fit_rho(cal_matches, ratings, total_anchor)
        rho_source = "fitted"
    else:
        rho = _FALLBACK_RHO
        ll = 0.0
        rho_source = "fallback"

    return CalibrationState(
        rho=round(rho, 4),
        total_anchor=round(total_anchor, 4),
        n_matches_used=n,
        calibrated_at=now_utc,
        log_likelihood=round(ll, 4),
        rmse_total_goals=round(rmse, 4),
        rho_source=rho_source,
        total_source=total_source,
    )


def save(state: CalibrationState, path: Path | None = None) -> Path:
    """Write calibration_state.json."""
    path = path or (_PI_DIR / "calibration_state.json")
    path.write_text(json.dumps(state.to_dict(), indent=2), encoding="utf-8")
    return path


def load(path: Path | None = None) -> Optional[CalibrationState]:
    """Load calibration_state.json. Returns None if missing."""
    path = path or (_PI_DIR / "calibration_state.json")
    if not path.exists():
        return None
    return CalibrationState.from_dict(json.loads(path.read_text(encoding="utf-8")))


def append_log(state: CalibrationState, log_path: Path | None = None) -> None:
    """Append one row to calibration_log.csv (creates file if absent)."""
    log_path = log_path or (_PI_DIR / "calibration_log.csv")
    fieldnames = [
        "calibrated_at", "n_matches_used", "total_anchor", "total_source",
        "rho", "rho_source", "log_likelihood", "rmse_total_goals",
    ]
    write_header = not log_path.exists()
    with open(log_path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        if write_header:
            writer.writeheader()
        writer.writerow(state.to_dict())


def main():
    import pandas as pd
    parquet = _REPO_ROOT / "data" / "processed" / "v1" / "matches.parquet"
    if not parquet.exists():
        raise SystemExit(f"Parquet not found: {parquet}\nRun 'make build-dataset' first.")
    df = pd.read_parquet(parquet)
    state = calibrate(df)
    out = save(state)
    append_log(state)
    print(f"Calibration complete → {out}")
    print(f"  total_anchor : {state.total_anchor}  ({state.total_source}, n={state.n_matches_used})")
    print(f"  rho          : {state.rho}  ({state.rho_source})")
    print(f"  log_likelihood: {state.log_likelihood}")
    print(f"  rmse_total   : {state.rmse_total_goals}")


if __name__ == "__main__":
    main()
