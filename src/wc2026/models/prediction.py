"""
ScorePMFPrediction — the single canonical output schema for every model.

Every model in the ladder returns this object. This enforces:
- normalized PMF summing to exactly 1.0
- explicit tail mass beyond max_goals
- all derived markets computed from the PMF (never independently)
- internal consistency checks
- metadata for reproducibility
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum

import numpy as np
from penaltyblog.models import FootballProbabilityGrid

from wc2026 import DATA_VERSION, FEATURE_VERSION, MODEL_VERSION
from wc2026.config import PMF_MAX_GOALS, TAIL_WARN_THRESHOLD


class CalibrationStatus(str, Enum):
    UNCALIBRATED = "uncalibrated"
    CALIBRATED = "calibrated"
    MARKET_CALIBRATED = "market_calibrated"
    TEMPERATURE_SCALED = "temperature_scaled"


@dataclass
class DerivedMarkets:
    """All markets derived from the score PMF. Never computed independently."""

    # 1X2
    home_win: float = 0.0
    draw: float = 0.0
    away_win: float = 0.0

    # Double chance
    dc_1x: float = 0.0
    dc_x2: float = 0.0
    dc_12: float = 0.0

    # Draw no bet
    dnb_home: float = 0.0
    dnb_away: float = 0.0

    # BTTS
    btts_yes: float = 0.0
    btts_no: float = 0.0

    # Totals (over/under)
    over_0_5: float = 0.0
    over_1_5: float = 0.0
    over_2_5: float = 0.0
    over_3_5: float = 0.0
    over_4_5: float = 0.0
    over_5_5: float = 0.0
    over_6_5: float = 0.0

    # Asian handicap (home perspective)
    ah_home_minus_0_5: float = 0.0
    ah_home_minus_1_0: float = 0.0
    ah_home_minus_1_5: float = 0.0
    ah_home_plus_0_5: float = 0.0
    ah_home_plus_1_0: float = 0.0
    ah_home_plus_1_5: float = 0.0

    def to_dict(self) -> dict:
        return {k: round(v, 6) for k, v in self.__dict__.items()}


@dataclass
class ScorePMFPrediction:
    """
    Canonical output for every goal model in the ladder.

    The `score_pmf` matrix is the single source of truth.
    All `derived_markets` values are computed from it.
    """

    match_id: int | None = None
    home_team: str = "TBD"
    away_team: str = "TBD"
    season: int | None = None
    stage: str | None = None
    venue: str | None = None
    model_name: str = "unknown"
    model_version: str = MODEL_VERSION
    data_version: str = DATA_VERSION
    feature_version: str = FEATURE_VERSION
    max_goals: int = PMF_MAX_GOALS
    prediction_timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    # The PMF — shape (max_goals, max_goals)
    score_pmf: np.ndarray = field(default_factory=lambda: np.zeros((PMF_MAX_GOALS, PMF_MAX_GOALS)))

    # Explicit tail mass: probability mass beyond max_goals × max_goals
    tail_mass: float = 0.0

    # Expected goals from the model
    expected_home_goals: float = 0.0
    expected_away_goals: float = 0.0

    # Derived markets (always from PMF)
    derived_markets: DerivedMarkets = field(default_factory=DerivedMarkets)

    # Quality metadata
    calibration_status: CalibrationStatus = CalibrationStatus.UNCALIBRATED
    uncertainty: dict | None = None
    warnings: list[str] = field(default_factory=list)

    # Hash for reproducibility
    prediction_hash: str = ""

    def __post_init__(self) -> None:
        self._validate_pmf()
        self.derived_markets = self._compute_derived_markets()
        self.prediction_hash = self._compute_hash()

    # -----------------------------------------------------------------------
    # Construction from penaltyblog FootballProbabilityGrid
    # -----------------------------------------------------------------------

    @classmethod
    def from_grid(
        cls,
        grid: FootballProbabilityGrid,
        model_name: str,
        home_team: str,
        away_team: str,
        match_id: int | None = None,
        season: int | None = None,
        stage: str | None = None,
        venue: str | None = None,
        max_goals: int = PMF_MAX_GOALS,
        calibration_status: CalibrationStatus = CalibrationStatus.UNCALIBRATED,
        uncertainty: dict | None = None,
    ) -> ScorePMFPrediction:
        raw = grid.grid
        # Clip tiny floating-point negatives (can arise from Dixon-Coles tau
        # correction under neutral_venue; values are negligibly small, < 1e-9).
        raw = np.clip(raw, 0.0, None)

        # Trim or pad to max_goals × max_goals
        mg = max_goals
        padded = np.zeros((mg, mg), dtype=np.float64)
        h = min(raw.shape[0], mg)
        a = min(raw.shape[1], mg)
        padded[:h, :a] = raw[:h, :a]

        # Tail mass = probability in rows/cols beyond max_goals
        total_raw = raw.sum()
        in_grid = padded.sum()
        tail_mass = max(0.0, float(total_raw - in_grid))

        # Normalise so grid + tail = 1.0
        grid_sum = float(padded.sum())
        if grid_sum > 0:
            padded = padded / grid_sum * (1.0 - tail_mass)

        return cls(
            match_id=match_id,
            home_team=home_team,
            away_team=away_team,
            season=season,
            stage=stage,
            venue=venue,
            model_name=model_name,
            max_goals=max_goals,
            score_pmf=padded,
            tail_mass=tail_mass,
            expected_home_goals=grid.home_goal_expectation,
            expected_away_goals=grid.away_goal_expectation,
            calibration_status=calibration_status,
            uncertainty=uncertainty,
        )

    # -----------------------------------------------------------------------
    # PMF validation
    # -----------------------------------------------------------------------

    def _validate_pmf(self) -> None:
        m = self.score_pmf
        if m.ndim != 2:
            raise ValueError("score_pmf must be 2D")
        if np.any(m < -1e-9):
            raise ValueError("score_pmf contains negative probabilities")
        total = float(m.sum()) + self.tail_mass
        if not np.isclose(total, 1.0, atol=1e-4):
            raise ValueError(
                f"score_pmf (+ tail_mass={self.tail_mass:.6f}) sums to {total:.6f}, not 1.0"
            )
        if self.tail_mass > TAIL_WARN_THRESHOLD:
            self.warnings.append(
                f"Tail mass {self.tail_mass:.3%} exceeds {TAIL_WARN_THRESHOLD:.0%}. "
                f"Consider increasing max_goals."
            )
        # Clip tiny negatives from floating point
        self.score_pmf = np.clip(m, 0.0, 1.0)

    # -----------------------------------------------------------------------
    # Market derivation
    # -----------------------------------------------------------------------

    def _compute_derived_markets(self) -> DerivedMarkets:
        m = self.score_pmf
        n = m.shape[0]
        i, j = np.indices((n, n))

        home_win = float(m[i > j].sum())
        draw = float(m[i == j].sum())
        away_win = float(m[i < j].sum())

        btts_yes = float(m[(i > 0) & (j > 0)].sum())
        btts_no = 1.0 - btts_yes

        s = i + j  # total goals matrix

        def over(line: float) -> float:
            return float(m[s > line].sum())

        def ah_win(home_hdp: float) -> float:
            """AH win prob for home at given handicap (positive = home receives)."""
            gd = i - j
            if home_hdp == int(home_hdp):  # integer: can push
                win = float(m[gd + home_hdp > 0].sum())
                # push is excluded from win; net exposure: win / (win + lose)
            else:
                win = float(m[gd + home_hdp > 0].sum())
            return win

        return DerivedMarkets(
            home_win=home_win,
            draw=draw,
            away_win=away_win,
            dc_1x=home_win + draw,
            dc_x2=draw + away_win,
            dc_12=home_win + away_win,
            dnb_home=home_win / max(home_win + away_win, 1e-9),
            dnb_away=away_win / max(home_win + away_win, 1e-9),
            btts_yes=btts_yes,
            btts_no=btts_no,
            over_0_5=over(0.5),
            over_1_5=over(1.5),
            over_2_5=over(2.5),
            over_3_5=over(3.5),
            over_4_5=over(4.5),
            over_5_5=over(5.5),
            over_6_5=over(6.5),
            ah_home_minus_0_5=ah_win(-0.5),
            ah_home_minus_1_0=ah_win(-1.0),
            ah_home_minus_1_5=ah_win(-1.5),
            ah_home_plus_0_5=ah_win(0.5),
            ah_home_plus_1_0=ah_win(1.0),
            ah_home_plus_1_5=ah_win(1.5),
        )

    # -----------------------------------------------------------------------
    # Consistency checks
    # -----------------------------------------------------------------------

    def check_consistency(self) -> list[str]:
        """Return list of consistency violations (empty = all good)."""
        errors = []
        m = self.score_pmf
        dm = self.derived_markets

        total = float(m.sum()) + self.tail_mass
        if not np.isclose(total, 1.0, atol=1e-4):
            errors.append(f"PMF sums to {total:.6f}, not 1.0")

        if np.any(m < -1e-9):
            errors.append("PMF contains negative probabilities")

        if not np.isclose(dm.home_win + dm.draw + dm.away_win, 1.0, atol=1e-4):
            errors.append("1X2 does not sum to 1.0")

        if not np.isclose(dm.btts_yes + dm.btts_no, 1.0, atol=1e-4):
            errors.append("BTTS yes + no != 1.0")

        for attr in ["dc_1x", "dc_x2", "dc_12", "dnb_home", "dnb_away"]:
            v = getattr(dm, attr)
            if not (0.0 <= v <= 1.0 + 1e-6):
                errors.append(f"{attr}={v:.6f} out of [0,1]")

        # Totals monotonicity
        overs = [dm.over_0_5, dm.over_1_5, dm.over_2_5, dm.over_3_5,
                 dm.over_4_5, dm.over_5_5, dm.over_6_5]
        for k in range(len(overs) - 1):
            if overs[k] < overs[k + 1] - 1e-6:
                errors.append(f"Totals not monotonic: over_{k}_5={overs[k]:.4f} < over_{k+1}_5={overs[k+1]:.4f}")

        return errors

    # -----------------------------------------------------------------------
    # Serialization
    # -----------------------------------------------------------------------

    def top_scores(self, n: int = 15) -> list[dict]:
        m = self.score_pmf
        flat = np.argsort(m, axis=None)[::-1][:n]
        rows, cols = np.unravel_index(flat, m.shape)
        return [
            {"home_goals": int(r), "away_goals": int(c), "probability": round(float(m[r, c]), 6)}
            for r, c in zip(rows, cols)
        ]

    def exact_score(self, h: int, a: int) -> float:
        if 0 <= h < self.score_pmf.shape[0] and 0 <= a < self.score_pmf.shape[1]:
            return float(self.score_pmf[h, a])
        return 0.0

    def to_dict(self) -> dict:
        return {
            "match_id": self.match_id,
            "prediction_timestamp": self.prediction_timestamp,
            "home_team": self.home_team,
            "away_team": self.away_team,
            "season": self.season,
            "stage": self.stage,
            "venue": self.venue,
            "model_name": self.model_name,
            "model_version": self.model_version,
            "data_version": self.data_version,
            "feature_version": self.feature_version,
            "max_goals": self.max_goals,
            "tail_mass": round(self.tail_mass, 6),
            "expected_home_goals": round(self.expected_home_goals, 4),
            "expected_away_goals": round(self.expected_away_goals, 4),
            "score_pmf": [[round(float(v), 6) for v in row] for row in self.score_pmf],
            "top_scores": self.top_scores(),
            "derived_markets": self.derived_markets.to_dict(),
            "calibration_status": self.calibration_status.value,
            "uncertainty": self.uncertainty,
            "warnings": self.warnings,
            "prediction_hash": self.prediction_hash,
        }

    def _compute_hash(self) -> str:
        payload = json.dumps(
            {
                "model": self.model_name,
                "home": self.home_team,
                "away": self.away_team,
                "pmf_sum": round(float(self.score_pmf.sum()), 8),
                "pmf_00": round(float(self.score_pmf[0, 0]), 8) if self.score_pmf.size > 0 else 0.0,
                "ts": self.prediction_timestamp,
            },
            sort_keys=True,
        )
        return hashlib.sha1(payload.encode()).hexdigest()[:12]
