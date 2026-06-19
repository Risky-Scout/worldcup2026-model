"""
Prediction coverage guarantee.

Every scheduled match gets a full EGM prediction.
Missing data increases uncertainty; it never prevents a prediction.

Abstention is ONLY for the CLV/betting edge layer, not for the base prediction.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
import logging

log = logging.getLogger(__name__)

WC_TOTAL_BASELINE = 2.65
WC_DRAW_PROB_BASELINE = 0.265
WC_HOME_WIN_BASELINE = 0.365
WC_AWAY_WIN_BASELINE = 0.370


@dataclass
class FullMatchPrediction:
    """
    Complete prediction for a single match.
    Always populated — never None for any field.
    """
    match_id: int
    home_team: str
    away_team: str
    prediction_timestamp: str

    # EGM layer
    home_neutral_egm: float
    away_neutral_egm: float
    match_expected_goal_margin: float

    # Lambdas (always positive, always anchored to total)
    lambda_home: float
    lambda_away: float
    total_goal_anchor: float

    # Win/draw/loss (always sum to 1.0)
    p_home_win: float
    p_draw: float
    p_away_win: float

    # Uncertainty (0.0 = full data, 1.0 = global fallback only)
    uncertainty_level: float

    # Source traceability
    sources_used: list[str] = field(default_factory=list)
    home_sources: list[str] = field(default_factory=list)
    away_sources: list[str] = field(default_factory=list)

    # PMF (optional for lightweight usage; generate on demand)
    score_pmf_available: bool = False

    def is_high_confidence(self, threshold: float = 0.4) -> bool:
        return self.uncertainty_level <= threshold

    def to_team_strength_dict(self) -> dict:
        """Returns the team_strength object for JSON output."""
        return {
            "scale": "expected goal margin vs average WC team on neutral field",
            "home_team": self.home_team,
            "away_team": self.away_team,
            "home_neutral_egm": self.home_neutral_egm,
            "away_neutral_egm": self.away_neutral_egm,
            "match_expected_goal_margin": self.match_expected_goal_margin,
            "lambda_home": self.lambda_home,
            "lambda_away": self.lambda_away,
            "total_goal_anchor": self.total_goal_anchor,
            "p_home_win": self.p_home_win,
            "p_draw": self.p_draw,
            "p_away_win": self.p_away_win,
            "uncertainty_level": self.uncertainty_level,
            "uncertainty_label": self._uncertainty_label(),
            "sources_used": self.sources_used,
            "home_sources": self.home_sources,
            "away_sources": self.away_sources,
        }

    def _uncertainty_label(self) -> str:
        if self.uncertainty_level <= 0.2:
            return "high_confidence"
        elif self.uncertainty_level <= 0.5:
            return "moderate_confidence"
        elif self.uncertainty_level <= 0.8:
            return "low_confidence"
        else:
            return "prior_only"


def _poisson_pmf_approx(lambda_h: float, lambda_a: float, max_goals: int = 8) -> dict:
    """
    Compute approximate P(home=i, away=j) using independent Poisson.
    Returns dict of (i,j) -> probability.
    """
    import math
    pmf = {}
    total = 0.0
    for i in range(max_goals + 1):
        for j in range(max_goals + 1):
            p = (
                math.exp(-lambda_h) * (lambda_h ** i) / math.factorial(i)
                * math.exp(-lambda_a) * (lambda_a ** j) / math.factorial(j)
            )
            pmf[(i, j)] = p
            total += p
    # Normalize tail mass
    for k in pmf:
        pmf[k] /= max(total, 1e-9)
    return pmf


def build_match_prediction(
    match_id: int,
    home_team: str,
    away_team: str,
    home_egm: float,
    away_egm: float,
    total_anchor: float,
    home_sources: list[str],
    away_sources: list[str],
    home_uncertainty: float,
    away_uncertainty: float,
    prediction_timestamp: Optional[datetime] = None,
) -> FullMatchPrediction:
    """
    Build a complete match prediction from EGM components.
    Always returns a valid prediction — never raises.
    """
    from src.wc2026.models.egm_to_lambdas import margin_total_to_lambdas

    margin = home_egm - away_egm
    lambda_h, lambda_a = margin_total_to_lambdas(margin, total_anchor)

    # Compute win/draw/loss from PMF
    pmf = _poisson_pmf_approx(lambda_h, lambda_a)
    p_home = sum(v for (i, j), v in pmf.items() if i > j)
    p_draw = sum(v for (i, j), v in pmf.items() if i == j)
    p_away = sum(v for (i, j), v in pmf.items() if i < j)

    # Normalize to sum to 1.0
    total_p = p_home + p_draw + p_away
    if total_p > 0:
        p_home /= total_p
        p_draw /= total_p
        p_away /= total_p
    else:
        p_home, p_draw, p_away = WC_HOME_WIN_BASELINE, WC_DRAW_PROB_BASELINE, WC_AWAY_WIN_BASELINE

    # Combined uncertainty: average of home and away
    combined_uncertainty = (home_uncertainty + away_uncertainty) / 2.0

    all_sources = list(dict.fromkeys(home_sources + away_sources))

    ts = prediction_timestamp or datetime.utcnow()

    return FullMatchPrediction(
        match_id=match_id,
        home_team=home_team,
        away_team=away_team,
        prediction_timestamp=ts.isoformat() if hasattr(ts, "isoformat") else str(ts),
        home_neutral_egm=home_egm,
        away_neutral_egm=away_egm,
        match_expected_goal_margin=margin,
        lambda_home=lambda_h,
        lambda_away=lambda_a,
        total_goal_anchor=total_anchor,
        p_home_win=p_home,
        p_draw=p_draw,
        p_away_win=p_away,
        uncertainty_level=combined_uncertainty,
        sources_used=all_sources,
        home_sources=home_sources,
        away_sources=away_sources,
        score_pmf_available=True,
    )


def ensure_prediction_coverage(
    scheduled_matches: list[dict],
    available_team_ratings: dict[int, "TeamMarginRating"],  # type: ignore
    total_anchor: float = WC_TOTAL_BASELINE,
    prediction_timestamp: Optional[datetime] = None,
) -> list[FullMatchPrediction]:
    """
    Guarantee a prediction for every scheduled match.

    scheduled_matches: list of dicts with keys:
      match_id, home_team_id, home_team_name, away_team_id, away_team_name,
      home_confederation (optional), away_confederation (optional)

    available_team_ratings: dict of team_id -> TeamMarginRating
      May be empty or partial; fallbacks fill the gaps.

    Returns: list of FullMatchPrediction, one per scheduled match, NEVER skipping.
    """
    from src.wc2026.ratings.team_margin import TeamMarginRating
    from src.wc2026.ratings.fallback_prior import build_fallback_egm, compute_uncertainty

    predictions = []

    for match in scheduled_matches:
        match_id = int(match.get("match_id", 0))
        h_id = int(match.get("home_team_id", 0))
        a_id = int(match.get("away_team_id", 0))
        h_name = str(match.get("home_team_name", f"Team_{h_id}"))
        a_name = str(match.get("away_team_name", f"Team_{a_id}"))
        h_conf = match.get("home_confederation")
        a_conf = match.get("away_confederation")

        # Get or create home rating
        if h_id in available_team_ratings:
            hr = available_team_ratings[h_id]
        else:
            log.warning(f"No rating for home team {h_name} (id={h_id}), using fallback")
            hr = TeamMarginRating.stub(h_id, h_name, h_conf)

        # Get or create away rating
        if a_id in available_team_ratings:
            ar = available_team_ratings[a_id]
        else:
            log.warning(f"No rating for away team {a_name} (id={a_id}), using fallback")
            ar = TeamMarginRating.stub(a_id, a_name, a_conf)

        try:
            pred = build_match_prediction(
                match_id=match_id,
                home_team=h_name,
                away_team=a_name,
                home_egm=hr.neutral_egm,
                away_egm=ar.neutral_egm,
                total_anchor=total_anchor,
                home_sources=hr.sources_used,
                away_sources=ar.sources_used,
                home_uncertainty=hr.uncertainty_egm,
                away_uncertainty=ar.uncertainty_egm,
                prediction_timestamp=prediction_timestamp,
            )
        except Exception as e:
            # Last-resort fallback: never let an exception prevent a prediction
            log.error(f"Prediction error for match {match_id}: {e}, using baseline")
            pred = build_match_prediction(
                match_id=match_id,
                home_team=h_name,
                away_team=a_name,
                home_egm=0.0,
                away_egm=0.0,
                total_anchor=WC_TOTAL_BASELINE,
                home_sources=["global_fallback"],
                away_sources=["global_fallback"],
                home_uncertainty=1.0,
                away_uncertainty=1.0,
                prediction_timestamp=prediction_timestamp,
            )

        predictions.append(pred)

    return predictions
