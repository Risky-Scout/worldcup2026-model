"""
Closing Line Value (CLV) tracking for pre-game predictions.

CLV measures whether a model's pre-game probability was better or worse than
the market's closing line — the final odds before kickoff, which are considered
the most efficient price in the market.

Theory
------
If model_prob > closing_prob consistently, the model has positive CLV, meaning
it is identifying value that the market has not yet fully priced in.

CLV is the primary long-run validation metric for a betting model — not ROI
(which has too much variance) and not NLL alone (which doesn't benchmark vs market).

Metrics
-------
- clv_raw: (model_prob - closing_prob) in probability units
- clv_pct: clv_raw / closing_prob × 100 (percentage edge vs closing line)
- clv_bits: log2(model_prob / closing_prob) (information gain vs closing line)
- beat_close: True if model_prob > closing_prob
- opening_drift: closing_prob - opening_prob (how much the market moved)
- model_vs_opening: model_prob - opening_prob

Usage
-----
At prediction time (pre-kickoff):
    record = CLVRecord.from_prediction(match_id, market, model_prob,
                                       opening_odds, prediction_timestamp)

After match closes (kickoff - 1 min):
    record.set_closing(closing_odds, closing_timestamp)
    record.compute_clv()

After match ends:
    record.set_outcome(outcome=True/False)

Aggregate reporting:
    summary = CLVSummary.from_records(records)
    summary.to_markdown()
"""
from __future__ import annotations

import datetime as dt
import json
import logging
import math
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Optional

import numpy as np

log = logging.getLogger(__name__)

_EPS = 1e-9


# ── Data classes ──────────────────────────────────────────────────────────────

@dataclass
class CLVRecord:
    """CLV record for one market outcome in one match."""
    # Identity
    match_id: str
    home_team: str
    away_team: str
    market: str               # e.g. "home_win", "over_2_5", "1-0"
    prediction_mode: str      # e.g. "market_reconciled", "pure_model"

    # Prediction
    model_prob: float
    model_fair_odds: float    # 1 / model_prob
    prediction_timestamp: str # ISO-8601

    # Opening line (first available odds)
    opening_prob: Optional[float] = None
    opening_odds_decimal: Optional[float] = None
    opening_timestamp: Optional[str] = None

    # Closing line (last odds before kickoff)
    closing_prob: Optional[float] = None
    closing_odds_decimal: Optional[float] = None
    closing_timestamp: Optional[str] = None
    closing_source: Optional[str] = None     # "live_capture" | "backfill_invalid"

    # Frozen model prob — captured at the moment the closing line is set so
    # subsequent upserts with a live-refreshing model_prob don't corrupt CLV.
    frozen_model_prob: Optional[float] = None
    frozen_at: Optional[str] = None

    # CLV metrics (computed after closing line is known)
    clv_raw: Optional[float] = None          # model_prob - closing_prob
    clv_pct: Optional[float] = None          # clv_raw / closing_prob × 100
    clv_bits: Optional[float] = None         # log2(model / closing)
    beat_close: Optional[bool] = None        # model_prob > closing_prob
    opening_drift: Optional[float] = None    # closing_prob - opening_prob
    model_vs_opening: Optional[float] = None # model_prob - opening_prob

    # Outcome (set post-match)
    outcome: Optional[bool] = None           # True if the outcome occurred
    outcome_timestamp: Optional[str] = None

    # Suppression flag — True for markets excluded from published edge signals
    # (kept in raw records for diagnostics; never surfaced as value picks)
    suppress_from_edge: bool = False

    def set_closing(self, closing_odds_decimal: float, timestamp: str,
                    source: str = "live_capture") -> None:
        """Record the closing line and compute CLV metrics.

        Rejects closing odds timestamped AFTER the outcome was recorded —
        that means the backfill fetched post-match prices which reflect the
        known result, producing meaningless CLV numbers.
        """
        if closing_odds_decimal <= 1.0:
            log.warning("CLV: invalid closing odds %.4f for %s %s",
                        closing_odds_decimal, self.match_id, self.market)
            return
        # Guard: closing must precede outcome — post-match BDL odds are invalid
        if self.outcome_timestamp and timestamp > self.outcome_timestamp:
            log.warning(
                "CLV: closing_timestamp %s is AFTER outcome_timestamp %s for %s %s — "
                "rejecting post-match backfill odds (they reflect the known result)",
                timestamp[:16], self.outcome_timestamp[:16], self.match_id, self.market,
            )
            self.closing_source = "backfill_invalid"
            return
        self.closing_odds_decimal = round(closing_odds_decimal, 4)
        self.closing_prob = round(1.0 / closing_odds_decimal, 6)
        self.closing_timestamp = timestamp
        self.closing_source = source
        # Freeze model_prob at closing time so later upserts don't corrupt CLV
        if self.frozen_model_prob is None:
            self.frozen_model_prob = self.model_prob
            self.frozen_at = timestamp
        self._compute_clv()

    def set_outcome(self, outcome: bool, timestamp: Optional[str] = None) -> None:
        self.outcome = outcome
        self.outcome_timestamp = timestamp or dt.datetime.now(tz=dt.timezone.utc).isoformat()

    def _compute_clv(self) -> None:
        if self.closing_prob is None or self.closing_prob < _EPS:
            return
        # Prefer frozen_model_prob (set at closing time) over live model_prob
        mp = max(self.frozen_model_prob if self.frozen_model_prob is not None else self.model_prob, _EPS)
        cp = max(self.closing_prob, _EPS)
        self.clv_raw = round(mp - cp, 6)
        self.clv_pct = round((mp - cp) / cp * 100, 4)
        self.clv_bits = round(math.log2(mp / cp), 6)
        self.beat_close = mp > cp
        if self.opening_prob is not None:
            self.opening_drift = round(cp - self.opening_prob, 6)
            self.model_vs_opening = round(mp - self.opening_prob, 6)

    def to_dict(self) -> dict:
        return {k: v for k, v in asdict(self).items() if v is not None}

    @classmethod
    def from_prediction(
        cls,
        match_id: str,
        home_team: str,
        away_team: str,
        market: str,
        model_prob: float,
        prediction_mode: str,
        opening_odds_decimal: Optional[float] = None,
        opening_timestamp: Optional[str] = None,
        prediction_timestamp: Optional[str] = None,
    ) -> "CLVRecord":
        ts = prediction_timestamp or dt.datetime.now(tz=dt.timezone.utc).isoformat()
        rec = cls(
            match_id=match_id,
            home_team=home_team,
            away_team=away_team,
            market=market,
            prediction_mode=prediction_mode,
            model_prob=round(float(model_prob), 6),
            model_fair_odds=round(1.0 / max(float(model_prob), _EPS), 4),
            prediction_timestamp=ts,
        )
        if opening_odds_decimal and opening_odds_decimal > 1.0:
            rec.opening_odds_decimal = round(opening_odds_decimal, 4)
            rec.opening_prob = round(1.0 / opening_odds_decimal, 6)
            rec.opening_timestamp = opening_timestamp or ts
        return rec


@dataclass
class CLVSummary:
    """Aggregate CLV statistics across markets and matches."""
    n_records: int = 0
    n_with_closing: int = 0
    n_beat_close: int = 0
    n_with_outcome: int = 0

    # CLV metrics (where closing line is known)
    mean_clv_raw: float = 0.0       # avg (model_p - close_p)
    mean_clv_pct: float = 0.0       # avg % edge vs close
    mean_clv_bits: float = 0.0      # avg log2(model/close)
    beat_close_rate: float = 0.0    # fraction where model > close

    # By market type
    by_market: dict = field(default_factory=dict)

    # Actual ROI (where outcome is known)
    mean_log_score: float = 0.0     # E[log(model_p | outcome)]
    mean_closing_log_score: float = 0.0  # E[log(close_p | outcome)]
    clv_vs_log_score_correlation: float = 0.0

    @classmethod
    def from_records(cls, records: list[CLVRecord]) -> "CLVSummary":
        s = cls()
        s.n_records = len(records)

        clv_recs = [r for r in records if r.clv_raw is not None]
        s.n_with_closing = len(clv_recs)
        s.n_beat_close = sum(1 for r in clv_recs if r.beat_close)

        if clv_recs:
            s.mean_clv_raw = round(float(np.mean([r.clv_raw for r in clv_recs])), 6)
            s.mean_clv_pct = round(float(np.mean([r.clv_pct for r in clv_recs])), 4)
            s.mean_clv_bits = round(float(np.mean([r.clv_bits for r in clv_recs])), 6)
            s.beat_close_rate = round(s.n_beat_close / len(clv_recs), 4)

        # By market
        markets = set(r.market for r in clv_recs)
        for mkt in sorted(markets):
            mkt_recs = [r for r in clv_recs if r.market == mkt]
            if mkt_recs:
                s.by_market[mkt] = {
                    "n": len(mkt_recs),
                    "mean_clv_pct": round(float(np.mean([r.clv_pct for r in mkt_recs])), 3),
                    "beat_close_rate": round(
                        sum(1 for r in mkt_recs if r.beat_close) / len(mkt_recs), 3
                    ),
                }

        # Log scores (where outcome known)
        outcome_recs = [r for r in clv_recs if r.outcome is not None]
        s.n_with_outcome = len(outcome_recs)
        if outcome_recs:
            model_ls = [math.log(max(r.model_prob, _EPS)) if r.outcome
                        else math.log(max(1 - r.model_prob, _EPS))
                        for r in outcome_recs]
            close_ls = [math.log(max(r.closing_prob, _EPS)) if r.outcome
                        else math.log(max(1 - r.closing_prob, _EPS))
                        for r in outcome_recs]
            s.mean_log_score = round(float(np.mean(model_ls)), 6)
            s.mean_closing_log_score = round(float(np.mean(close_ls)), 6)
            if len(outcome_recs) > 2:
                clv_arr = np.array([r.clv_pct for r in outcome_recs])
                ls_arr = np.array(model_ls)
                try:
                    s.clv_vs_log_score_correlation = round(float(np.corrcoef(clv_arr, ls_arr)[0, 1]), 4)
                except Exception:
                    pass

        return s

    def to_markdown(self) -> str:
        lines = [
            "# CLV Summary Report",
            "",
            f"Records: {self.n_records}  |  With closing line: {self.n_with_closing}  "
            f"|  With outcome: {self.n_with_outcome}",
            "",
            "## Aggregate CLV",
            "",
            "| Metric | Value |",
            "|--------|-------|",
            f"| Mean CLV (raw prob) | {self.mean_clv_raw:+.5f} |",
            f"| Mean CLV (%) | {self.mean_clv_pct:+.3f}% |",
            f"| Mean CLV (bits) | {self.mean_clv_bits:+.5f} |",
            f"| Beat closing line rate | {self.beat_close_rate:.1%} ({self.n_beat_close}/{self.n_with_closing}) |",
        ]
        if self.n_with_outcome > 0:
            lines += [
                "",
                "## Log-score vs closing line (post-match)",
                "",
                "| Metric | Value |",
                "|--------|-------|",
                f"| Model mean log score | {self.mean_log_score:.4f} |",
                f"| Closing mean log score | {self.mean_closing_log_score:.4f} |",
                f"| CLV vs log-score correlation | {self.clv_vs_log_score_correlation:.3f} |",
            ]
        if self.by_market:
            lines += [
                "",
                "## By market",
                "",
                "| Market | N | Mean CLV% | Beat close% |",
                "|--------|---|-----------|-------------|",
            ]
            for mkt, stats in sorted(self.by_market.items(), key=lambda x: -abs(x[1]["mean_clv_pct"])):
                lines.append(
                    f"| {mkt} | {stats['n']} | {stats['mean_clv_pct']:+.2f}% "
                    f"| {stats['beat_close_rate']:.1%} |"
                )
        return "\n".join(lines)


# ── Persistence helpers ───────────────────────────────────────────────────────

class CLVStore:
    """
    Simple file-backed CLV record store.

    Records are stored as NDJSON in data/clv/{season}/records.jsonl.
    One line per CLVRecord.  Records are appended as predictions are made
    and updated in-place (by match_id + market) when closing lines arrive.
    """

    def __init__(self, path: str):
        self._path = Path(path)
        self._path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, record: CLVRecord) -> None:
        """Append a new prediction record (legacy; prefer upsert)."""
        with open(self._path, "a") as f:
            f.write(json.dumps(record.to_dict()) + "\n")

    def upsert(self, record: CLVRecord) -> None:
        """Insert or update a CLV record keyed by (match_id, market).

        - First insertion: stores record as-is (opening_prob set from record).
        - Subsequent calls: refreshes model_prob/model_fair_odds/prediction_timestamp
          with the latest values, but PRESERVES opening_prob from first observation
          so the opening line is never overwritten by later odds movements.
        - Closing line and outcome fields are preserved from any prior set_closing /
          set_outcome calls.
        """
        if not self._path.exists():
            with open(self._path, "w") as f:
                f.write(json.dumps(record.to_dict()) + "\n")
            return

        records = self.load_all()
        key = (record.match_id, record.market)
        found = False
        for existing in records:
            if (existing.match_id, existing.market) == key:
                # Preserve opening_prob from first observation
                if existing.opening_prob is not None and record.opening_prob is not None:
                    record.opening_prob = existing.opening_prob
                    record.opening_odds_decimal = existing.opening_odds_decimal
                    record.opening_timestamp = existing.opening_timestamp
                elif existing.opening_prob is not None:
                    record.opening_prob = existing.opening_prob
                    record.opening_odds_decimal = existing.opening_odds_decimal
                    record.opening_timestamp = existing.opening_timestamp
                # Preserve closing/outcome from prior calls
                if existing.closing_prob is not None and record.closing_prob is None:
                    record.closing_prob = existing.closing_prob
                    record.closing_odds_decimal = existing.closing_odds_decimal
                    record.closing_timestamp = existing.closing_timestamp
                    record.clv_raw = existing.clv_raw
                    record.clv_pct = existing.clv_pct
                    record.clv_bits = existing.clv_bits
                    record.beat_close = existing.beat_close
                    record.opening_drift = existing.opening_drift
                    record.model_vs_opening = existing.model_vs_opening
                    record.frozen_model_prob = existing.frozen_model_prob
                    record.frozen_at = existing.frozen_at
                    # Don't overwrite model_prob with a stale live value once
                    # the closing line is locked in — preserve the frozen state.
                    log.debug(
                        "CLV upsert: closing line already set for %s %s — "
                        "preserving frozen_model_prob=%.6f, not refreshing model_prob",
                        existing.match_id, existing.market,
                        existing.frozen_model_prob or existing.model_prob,
                    )
                    record.model_prob = existing.model_prob
                    record.model_fair_odds = existing.model_fair_odds
                if existing.outcome is not None and record.outcome is None:
                    record.outcome = existing.outcome
                    record.outcome_timestamp = existing.outcome_timestamp
                # Replace in-place
                records[records.index(existing)] = record
                found = True
                break

        if not found:
            records.append(record)

        with open(self._path, "w") as f:
            for r in records:
                f.write(json.dumps(r.to_dict()) + "\n")

    def load_all(self) -> list[CLVRecord]:
        """Load all records from the store."""
        if not self._path.exists():
            return []
        records = []
        with open(self._path) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    d = json.loads(line)
                    kwargs = {k: d.get(k) for k in CLVRecord.__dataclass_fields__}
                    # Coerce suppress_from_edge: old records lack the key → None → coerce to bool
                    kwargs["suppress_from_edge"] = bool(kwargs.get("suppress_from_edge") or False)
                    r = CLVRecord(**kwargs)
                    records.append(r)
                except Exception as exc:
                    log.warning("CLV load error: %s | line: %s", exc, line[:80])
        return records

    def update_closing(
        self,
        match_id: str,
        market: str,
        closing_odds_decimal: float,
        closing_timestamp: str,
    ) -> int:
        """Rewrite the store updating records matching match_id + market."""
        records = self.load_all()
        n_updated = 0
        for r in records:
            if r.match_id == match_id and r.market == market:
                r.set_closing(closing_odds_decimal, closing_timestamp)
                n_updated += 1
        # Rewrite
        with open(self._path, "w") as f:
            for r in records:
                f.write(json.dumps(r.to_dict()) + "\n")
        return n_updated

    def update_outcome(
        self,
        match_id: str,
        market: str,
        outcome: bool,
        timestamp: Optional[str] = None,
    ) -> int:
        """Mark outcomes for all records matching match_id + market."""
        records = self.load_all()
        n_updated = 0
        for r in records:
            if r.match_id == match_id and r.market == market:
                r.set_outcome(outcome, timestamp)
                n_updated += 1
        with open(self._path, "w") as f:
            for r in records:
                f.write(json.dumps(r.to_dict()) + "\n")
        return n_updated

    def summary(self) -> CLVSummary:
        return CLVSummary.from_records(self.load_all())


# ── Integration helper ────────────────────────────────────────────────────────

def build_clv_records_from_prediction(
    match_id: str,
    home_team: str,
    away_team: str,
    prediction: dict,
    opening_odds: Optional[dict] = None,
) -> list[CLVRecord]:
    """
    Build CLVRecord list from a published prediction dict.

    Parameters
    ----------
    match_id        BDL match identifier
    home_team       Home team name
    away_team       Away team name
    prediction      The "prediction" sub-dict from the published JSON
    opening_odds    Optional dict of market → opening odds decimal

    Returns
    -------
    List of CLVRecord objects (one per market), ready for CLVStore.append()
    """
    mode = prediction.get("prediction_mode", "market_reconciled")
    ts = str(prediction.get("odds_timestamp") or
             dt.datetime.now(tz=dt.timezone.utc).isoformat())

    markets_to_track = [
        "home_win", "draw", "away_win",
        "btts_yes", "btts_no",
        "over_0_5", "over_1_5", "over_2_5", "over_3_5", "over_4_5", "over_5_5", "over_6_5",
        "under_1_5", "under_2_5", "under_3_5",
    ]

    # Markets suppressed from published edge signals (Poisson tail CLV is -20pp to -99pp).
    # Records are kept for raw diagnostics but suppress_from_edge=True is set.
    _SUPPRESS_SET = {"over_5_5", "over_6_5"}

    edge_report = prediction.get("edge_report", {}) or {}
    edge_map = {}
    if edge_report:
        for e in edge_report.get("edges", []):
            edge_map[e["market"]] = e["model_prob"]

    derived = prediction.get("derived_markets", {}) or {}
    records: list[CLVRecord] = []

    for mkt in markets_to_track:
        # derived_markets uses dot notation ("over_2.5") while markets_to_track
        # uses underscore notation ("over_2_5"). Convert last underscore to dot.
        # e.g. "over_2_5" → "over_2.5",  "under_1_5" → "under_1.5"
        if mkt.startswith(("over_", "under_")):
            derived_key = mkt[:mkt.rfind("_")] + "." + mkt[mkt.rfind("_") + 1:]
        else:
            derived_key = mkt
        model_p = edge_map.get(mkt) or derived.get(mkt) or derived.get(derived_key)
        if model_p is None or float(model_p) <= 0:
            continue

        opening_odds_dec = None
        if opening_odds and mkt in opening_odds:
            opening_odds_dec = float(opening_odds[mkt])

        r = CLVRecord.from_prediction(
            match_id=str(match_id),
            home_team=home_team,
            away_team=away_team,
            market=mkt,
            model_prob=float(model_p),
            prediction_mode=mode,
            opening_odds_decimal=opening_odds_dec,
            prediction_timestamp=ts,
        )
        if mkt in _SUPPRESS_SET:
            r.suppress_from_edge = True
        records.append(r)

    return records
