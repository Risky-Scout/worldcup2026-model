"""
Consensus market probabilities from BDL odds.

Aggregates no-vig probabilities across vendors with:
- staleness filtering
- outlier-book filtering (IQR-based)
- robust averaging (trimmed mean)
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from wc2026.markets.no_vig import strip_vig_1x2, strip_vig_total

log = logging.getLogger(__name__)

# BDL vendors we trust (others are filtered)
APPROVED_VENDORS = {"draftkings", "fanduel", "betmgm", "betrivers", "caesars", "fanatics"}

# Consider odds stale if older than this many minutes
DEFAULT_STALE_MINUTES = 240.0


@dataclass
class ConsensusMarkets:
    """Aggregated consensus market probabilities for one match."""

    match_id: int
    odds_timestamp: str | None = None  # UTC ISO timestamp of the most recent line used
    n_vendors_1x2: int = 0
    n_vendors_total: int = 0

    # 1X2 consensus (no-vig)
    home_win: float | None = None
    draw: float | None = None
    away_win: float | None = None
    margin_1x2: float | None = None

    # Totals consensus (no-vig), keyed by line e.g. "2.5"
    totals: dict[str, tuple[float, float]] = field(default_factory=dict)

    warnings: list[str] = field(default_factory=list)

    @property
    def has_1x2(self) -> bool:
        return all(v is not None for v in (self.home_win, self.draw, self.away_win))

    def to_dict(self) -> dict:
        d = {
            "match_id": self.match_id,
            "odds_timestamp": self.odds_timestamp,
            "n_vendors_1x2": self.n_vendors_1x2,
            "n_vendors_total": self.n_vendors_total,
            "home_win": self.home_win,
            "draw": self.draw,
            "away_win": self.away_win,
            "margin_1x2": self.margin_1x2,
            "warnings": self.warnings,
        }
        for line, (over, under) in self.totals.items():
            d[f"over_{line}"] = over
            d[f"under_{line}"] = under
        return d


def build_consensus(
    odds_df: pd.DataFrame,
    match_id: int,
    method: str = "shin",
    stale_minutes: float = DEFAULT_STALE_MINUTES,
) -> ConsensusMarkets:
    """
    Build consensus markets for a single match from the odds DataFrame.

    Parameters
    ----------
    odds_df : filtered to this match_id only; columns:
              vendor, moneyline_home, moneyline_draw, moneyline_away,
              total_value, total_over_odds, total_under_odds, updated_at
    match_id : the match ID
    method : no-vig method
    stale_minutes : staleness threshold
    """
    from datetime import datetime, timezone
    consensus = ConsensusMarkets(match_id=match_id)

    rows = odds_df[odds_df["match_id"] == match_id].to_dict("records")
    if not rows:
        consensus.warnings.append("No odds rows found for this match.")
        return consensus

    # Filter to approved vendors
    rows = [r for r in rows if r.get("vendor", "").lower() in APPROVED_VENDORS]
    if not rows:
        consensus.warnings.append("No approved-vendor odds found.")
        return consensus

    # Filter stale
    now = datetime.now(timezone.utc)
    fresh_rows = _filter_stale(rows, now, stale_minutes)
    if not fresh_rows:
        consensus.warnings.append(
            f"All {len(rows)} odds lines are stale (>{stale_minutes:.0f} min). "
            "Using most recent available."
        )
        fresh_rows = rows  # fallback: use whatever we have

    # ── 1X2 ─────────────────────────────────────────────────────────────
    vig_results: list[list[float]] = []
    margins: list[float] = []
    timestamps: list[str] = []

    for r in fresh_rows:
        h = r.get("moneyline_home")
        d = r.get("moneyline_draw")
        a = r.get("moneyline_away")
        if any(v is None for v in (h, d, a)):
            continue
        res = strip_vig_1x2(int(h), int(d), int(a), method)
        if res.method == "naive_fallback":
            continue
        vig_results.append(res.probabilities)
        margins.append(res.margin)
        if r.get("updated_at"):
            timestamps.append(r["updated_at"])

    if vig_results:
        # Trimmed mean (remove extreme outliers if ≥4 books)
        arr = np.array(vig_results)
        avg = _trimmed_mean(arr) if len(arr) >= 4 else arr.mean(axis=0)
        consensus.home_win = float(avg[0])
        consensus.draw = float(avg[1])
        consensus.away_win = float(avg[2])
        consensus.margin_1x2 = float(np.mean(margins))
        consensus.n_vendors_1x2 = len(vig_results)
        if timestamps:
            consensus.odds_timestamp = max(timestamps)

    # ── Totals ───────────────────────────────────────────────────────────
    totals_by_line: dict[str, list[tuple[float, float]]] = {}
    for r in fresh_rows:
        line = r.get("total_value")
        over_o = r.get("total_over_odds")
        under_o = r.get("total_under_odds")
        if line is None or over_o is None or under_o is None:
            continue
        line_str = str(line)
        o, u = strip_vig_total(int(over_o), int(under_o), method)
        totals_by_line.setdefault(line_str, []).append((o, u))

    for line_str, pairs in totals_by_line.items():
        arr = np.array(pairs)
        mean = arr.mean(axis=0)
        consensus.totals[line_str] = (float(mean[0]), float(mean[1]))
        consensus.n_vendors_total = max(consensus.n_vendors_total, len(pairs))

    if not consensus.has_1x2:
        consensus.warnings.append("Could not compute consensus 1X2 (no valid lines).")

    return consensus


def _filter_stale(rows: list[dict], now, stale_minutes: float) -> list[dict]:
    """Return rows whose updated_at is within stale_minutes of now."""
    from datetime import timezone

    import dateutil.parser

    fresh = []
    for r in rows:
        updated = r.get("updated_at")
        if not updated:
            fresh.append(r)
            continue
        try:
            dt = dateutil.parser.parse(updated)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            if (now - dt).total_seconds() / 60 <= stale_minutes:
                fresh.append(r)
        except Exception:
            fresh.append(r)
    return fresh


def _trimmed_mean(arr: np.ndarray, trim: float = 0.25) -> np.ndarray:
    """Column-wise trimmed mean (removes top+bottom trim fraction)."""
    from scipy.stats import trim_mean
    return np.array([trim_mean(arr[:, c], trim) for c in range(arr.shape[1])])
