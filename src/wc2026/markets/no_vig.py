"""
No-vig probability conversion using penaltyblog.implied.

Supports all 7 penaltyblog methods:
- MULTIPLICATIVE (default, most common)
- ADDITIVE
- POWER
- SHIN
- DIFFERENTIAL_MARGIN_WEIGHTING
- ODDS_RATIO
- LOGARITHMIC

All input odds are in American format (as returned by BDL).
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional

import numpy as np
from penaltyblog.implied.implied import (
    ImpliedMethod,
    OddsFormat,
    calculate_implied,
)

log = logging.getLogger(__name__)


@dataclass
class NoVigResult:
    method: str
    probabilities: list[float]
    margin: float
    market_names: Optional[list[str]] = None

    @property
    def home_win(self) -> float:
        return self.probabilities[0] if len(self.probabilities) > 0 else float("nan")

    @property
    def draw(self) -> float:
        return self.probabilities[1] if len(self.probabilities) > 1 else float("nan")

    @property
    def away_win(self) -> float:
        return self.probabilities[2] if len(self.probabilities) > 2 else float("nan")


def american_to_decimal(american: int) -> float:
    """Convert American odds to decimal odds."""
    if american > 0:
        return american / 100 + 1.0
    else:
        return 100 / abs(american) + 1.0


def strip_vig_1x2(
    home_odds: int,
    draw_odds: int,
    away_odds: int,
    method: str = "multiplicative",
) -> NoVigResult:
    """
    Remove bookmaker margin from 1X2 American odds.

    Returns fair no-vig probabilities using penaltyblog.implied.

    Parameters
    ----------
    home_odds, draw_odds, away_odds : American odds integers
    method : penaltyblog ImpliedMethod name (lowercase string)
    """
    decimals = [
        american_to_decimal(home_odds),
        american_to_decimal(draw_odds),
        american_to_decimal(away_odds),
    ]
    try:
        result = calculate_implied(
            decimals,
            method=method,
            odds_format=OddsFormat.DECIMAL,
            market_names=["home_win", "draw", "away_win"],
        )
        return NoVigResult(
            method=method,
            probabilities=result.probabilities,
            margin=result.margin,
            market_names=result.market_names,
        )
    except Exception as exc:
        log.warning("strip_vig_1x2 failed with method=%s: %s", method, exc)
        # Naive fallback: proportional to implied probs without margin removal
        raw = [1 / d for d in decimals]
        total = sum(raw)
        probs = [r / total for r in raw]
        return NoVigResult(method="naive_fallback", probabilities=probs, margin=total - 1)


def strip_vig_total(
    over_odds: int,
    under_odds: int,
    method: str = "multiplicative",
) -> tuple[float, float]:
    """
    Remove bookmaker margin from over/under American odds.

    Returns (no_vig_over, no_vig_under).
    """
    decimals = [american_to_decimal(over_odds), american_to_decimal(under_odds)]
    try:
        result = calculate_implied(
            decimals,
            method=method,
            odds_format=OddsFormat.DECIMAL,
            market_names=["over", "under"],
        )
        return result.probabilities[0], result.probabilities[1]
    except Exception as exc:
        log.warning("strip_vig_total failed: %s", exc)
        raw = [1 / d for d in decimals]
        total = sum(raw)
        return raw[0] / total, raw[1] / total


def consensus_no_vig_1x2(
    rows: list[dict],
    method: str = "multiplicative",
    stale_minutes: float = 240.0,
) -> Optional[NoVigResult]:
    """
    Aggregate no-vig 1X2 probabilities across multiple vendors.

    Parameters
    ----------
    rows : list of dicts with keys: vendor, moneyline_home, moneyline_draw, moneyline_away, updated_at
    method : ImpliedMethod string
    stale_minutes : exclude lines updated more than this many minutes ago

    Returns
    -------
    NoVigResult with averaged probabilities, or None if no valid lines.
    """
    from datetime import datetime, timezone
    import dateutil.parser

    now = datetime.now(timezone.utc)
    valid_probs: list[list[float]] = []

    for row in rows:
        h = row.get("moneyline_home")
        d = row.get("moneyline_draw")
        a = row.get("moneyline_away")

        if any(v is None for v in (h, d, a)):
            continue

        # Staleness check
        updated = row.get("updated_at")
        if updated:
            try:
                dt = dateutil.parser.parse(updated)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                age_minutes = (now - dt).total_seconds() / 60
                if age_minutes > stale_minutes:
                    log.debug("Skipping stale odds from %s (%.0f min old)", row.get("vendor"), age_minutes)
                    continue
            except Exception:
                pass

        result = strip_vig_1x2(int(h), int(d), int(a), method)
        if result.method != "naive_fallback":
            valid_probs.append(result.probabilities)

    if not valid_probs:
        return None

    avg = np.mean(valid_probs, axis=0).tolist()
    return NoVigResult(
        method=f"consensus_{method}_{len(valid_probs)}_vendors",
        probabilities=avg,
        margin=float(np.mean([1 / sum(1 / american_to_decimal(v) for v in [
            row.get("moneyline_home", -110),
            row.get("moneyline_draw", 250),
            row.get("moneyline_away", 250),
        ]) for row in rows if row.get("moneyline_home")])),
    )
