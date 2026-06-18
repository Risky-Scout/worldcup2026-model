"""
Market-implied Expected Goal Margin from /fifa/worldcup/v1/odds.

Process:
1. Load as-of odds snapshot for match.
2. Build vendor-level no-vig 1X2 probabilities.
3. If O/U 2.5 available, use penaltyblog goal_expectancy_extended.
4. Else use goal_expectancy with 1X2.
5. Derive market_egm = market_lambda_home - market_lambda_away.
6. Accumulate across matches with time decay for team-level market ability.
"""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
import numpy as np
import pandas as pd

try:
    from penaltyblog.models import goal_expectancy, goal_expectancy_extended
    _HAS_PENALTYBLOG_GE = True
except ImportError:
    _HAS_PENALTYBLOG_GE = False

try:
    from penaltyblog.implied import calculate_implied
    _HAS_IMPLIED = True
except ImportError:
    _HAS_IMPLIED = False


@dataclass
class MatchMarketEGM:
    match_id: int
    home_team_id: int
    away_team_id: int
    market_lambda_home: float
    market_lambda_away: float
    market_egm: float
    market_total: float
    market_rho: Optional[float]
    vendor_count: int
    method_used: str     # "goal_expectancy_extended" | "goal_expectancy" | "fallback"
    observed_at: str


def _devig_1x2(home_odds: float, draw_odds: float, away_odds: float) -> tuple[float, float, float]:
    """Shin or basic additive de-vig on 1X2."""
    if home_odds <= 0 or draw_odds <= 0 or away_odds <= 0:
        raise ValueError("Non-positive odds")
    raw = [1/home_odds, 1/draw_odds, 1/away_odds]
    total = sum(raw)
    return raw[0]/total, raw[1]/total, raw[2]/total


def compute_match_market_egm(
    match_id: int,
    home_team_id: int,
    away_team_id: int,
    odds_rows: list[dict],
    observed_at: str,
) -> Optional[MatchMarketEGM]:
    """
    odds_rows: list of dicts with BDL top-level odds fields for this match.
    Uses the first vendor that has complete 1X2 data.
    """
    if not odds_rows:
        return None

    # Try each vendor for complete 1X2 + O/U 2.5
    best: Optional[dict] = None
    for row in odds_rows:
        try:
            _devig_1x2(
                float(row["moneyline_home_odds"]),
                float(row["moneyline_draw_odds"]),
                float(row["moneyline_away_odds"]),
            )
            best = row
            # prefer row with O/U 2.5
            tv = row.get("total_value")
            if tv is not None and abs(float(tv) - 2.5) < 0.01:
                break
        except (TypeError, ValueError, KeyError):
            continue

    if best is None:
        return None

    try:
        ph, pd_, pa = _devig_1x2(
            float(best["moneyline_home_odds"]),
            float(best["moneyline_draw_odds"]),
            float(best["moneyline_away_odds"]),
        )
    except Exception:
        return None

    tv = best.get("total_value")
    has_ou25 = tv is not None and abs(float(tv) - 2.5) < 0.01
    method = "fallback"
    lambda_h, lambda_a = 1.1, 1.1  # neutral default

    if _HAS_PENALTYBLOG_GE:
        try:
            if has_ou25:
                po = float(best["total_over_odds"])
                pu = float(best["total_under_odds"])
                p_over = 1/po / (1/po + 1/pu)
                result = goal_expectancy_extended(ph, pd_, pa, p_over)
                lambda_h = float(result.get("home_goals", 1.1))
                lambda_a = float(result.get("away_goals", 1.1))
                method = "goal_expectancy_extended"
            else:
                result = goal_expectancy(ph, pd_, pa)
                lambda_h = float(result.get("home_goals", 1.1))
                lambda_a = float(result.get("away_goals", 1.1))
                method = "goal_expectancy"
        except Exception:
            pass

    vendor_count = len(set(r.get("vendor", "?") for r in odds_rows))

    return MatchMarketEGM(
        match_id=match_id,
        home_team_id=home_team_id,
        away_team_id=away_team_id,
        market_lambda_home=lambda_h,
        market_lambda_away=lambda_a,
        market_egm=lambda_h - lambda_a,
        market_total=lambda_h + lambda_a,
        market_rho=None,
        vendor_count=vendor_count,
        method_used=method,
        observed_at=observed_at,
    )


def compute_team_market_ability(
    team_id: int,
    match_egms: list[MatchMarketEGM],
    decay_halflife_days: float = 90.0,
    min_matches: int = 3,
) -> float:
    """
    Accumulate match-level market EGMs for a team with time decay.
    Returns 0.0 if insufficient data.
    """
    if not match_egms:
        return 0.0
    now = datetime.utcnow()
    values, weights = [], []
    for m in match_egms:
        if m.home_team_id == team_id:
            egm = m.market_egm
        elif m.away_team_id == team_id:
            egm = -m.market_egm
        else:
            continue
        try:
            obs = datetime.fromisoformat(m.observed_at.replace("Z", "+00:00"))
            days_ago = (now - obs.replace(tzinfo=None)).days
        except Exception:
            days_ago = 0
        w = np.exp(-np.log(2) * days_ago / decay_halflife_days)
        values.append(egm)
        weights.append(w)
    if len(values) < min_matches:
        return 0.0
    return float(np.average(values, weights=weights))
