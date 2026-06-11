# penaltyblog Gap Audit — v0.2.0

**Audit date**: 2026-06-11  
**penaltyblog version**: 1.11.0  
**Against**: entire `src/wc2026/` tree

---

## What was deleted (old v0.1 code)

| File | Reason for deletion |
|------|---------------------|
| `src/wc2026/models/trainer.py` | `_calibrate_weights()` evaluated on training data — leakage. Invalid calibration. |
| `src/wc2026/models/ensemble.py` | Hardcoded ensemble weights, no out-of-fold validation |
| `src/wc2026/data/fetcher.py` | `diskcache`-based fetcher without schema validation, raw snapshots, or cursor pagination |
| `src/wc2026/data/preprocessor.py` | Custom `_decay_weight()` duplicated `penaltyblog.dixon_coles_weights`. Brittle `host_teams` hardcoding. |
| `src/wc2026/calibration/metrics.py` | Reimplemented RPS, Brier, Log Loss — all already in `penaltyblog.metrics` |
| `src/wc2026/predictions/live.py` | Flat lambda scaling (`λ_remaining = λ * (90-t)/90`) — not a valid hazard model |
| `src/wc2026/utils/helpers.py` | American odds conversion reimplemented — use `penaltyblog.implied` |

---

## What penaltyblog replaces (currently in use)

| Custom approach (old) | penaltyblog replacement (new) | Status |
|-----------------------|-------------------------------|--------|
| Custom `_decay_weight(date, ref)` | `penaltyblog.models.dixon_coles_weights(dates, xi=...)` | ✅ Replaced |
| Custom RPS, Brier, Log Loss | `penaltyblog.metrics.compute_average_rps`, `compute_multiclass_brier_score`, `compute_ignorance_score` | ✅ Replaced |
| American odds → implied prob | `penaltyblog.implied.calculate_implied(odds, method, odds_format=AMERICAN)` — 7 methods | ✅ Replaced |
| Hardcoded DixonColes only | Full model ladder: Poisson, DixonColes, BivariatePoisson, WeibullCopula, NegBinomial, ZeroInflated, Bayesian, HierarchicalBayesian | ✅ All implemented |
| No rating baselines | `penaltyblog.ratings.Elo`, `PiRatingSystem` | ✅ Elo used; Pi pending |

---

## What remains custom (and why)

| Component | Custom or penaltyblog? | Justification |
|-----------|----------------------|---------------|
| BDL provider (`providers/bdl.py`) | Custom | penaltyblog has no BDL connector. BDL is the primary data feed. |
| Pydantic schemas (`data/schemas.py`) | Custom | penaltyblog does not validate BDL API responses. Required for fail-loud schema enforcement. |
| Storage layer (`data/storage.py`) | Custom | Parquet versioning and raw snapshots are not in penaltyblog. |
| `ScorePMFPrediction` dataclass | Custom | Standard output schema enforcing PMF validity, tail mass, and derived market consistency. penaltyblog's `FootballProbabilityGrid` is used internally; this wraps it with audit metadata. |
| Walk-forward engine (`backtest/walkforward.py`) | Custom | `penaltyblog.backtest.Backtest` is a betting strategy simulator (P&L, Kelly), not a model training walk-forward engine. Our engine trains models on strictly pre-prediction-date history. |
| Temperature scaling (`calibration/score_pmf.py`) | Custom | penaltyblog has no exact-score temperature calibration. |
| ECE, calibration slope/intercept | Custom | penaltyblog.metrics does not include these. |
| KL reconciliation (`markets/reconcile.py`) | Custom | No equivalent in penaltyblog. Market-model reconciliation via scipy L-BFGS-B. |
| Consensus markets (`markets/consensus.py`) | Custom | penaltyblog.implied strips vig per-vendor; we aggregate across vendors. |

---

## What penaltyblog matchflow can do (partially used)

penaltyblog `matchflow` is designed for Opta/StatsBomb event data with specific field schemas. BDL's event and shot data does not conform to those schemas natively. Current status:

- **Not integrated** into primary pipeline: BDL events are stored as flat parquet and queried directly.
- **Possible future use**: If BDL event data is mapped to Opta-compatible field names, MatchFlow's `Flow`, `Group`, and rolling aggregation steps could replace custom pandas aggregation.

---

## What is truly working (tested, not scaffolded)

| Component | Evidence |
|-----------|----------|
| ScorePMFPrediction schema | 18 unit tests pass (PMF sum, negativity, 1X2 consistency, BTTS, totals monotonicity, serialization) |
| BDL schema validation | 6 tests pass (required field enforcement, nullable fields, unknown field tolerance) |
| No-vig conversion | 15 tests pass (7 penaltyblog methods, American and decimal formats) |
| Temperature calibration | 9 tests pass |
| KL reconciliation | 6 tests pass |
| ModelLadder (Tier 1) | 10 tests pass (Poisson, DixonColes, BivariatePoisson fitted and validated) |
| Baselines | 3 tests pass |
| WalkForward engine | 4 tests pass (no-leakage verified, metrics finite, PMF sum check) |
| Total | 74 tests, all passing |

---

## What is scaffolded (not yet run end-to-end)

| Component | Status | Blocker |
|-----------|--------|---------|
| BDL fetch (real data) | Scaffolded | Needs `BDL_API_KEY` in `.env` |
| Bayesian models | Scaffolded (disabled by default) | Slow MCMC; not benchmarked on WC data |
| Full backtest on 2018/2022 | Scaffolded | Needs `make fetch-bdl && make build-dataset` first |
| Temperature scaling on real WC data | Scaffolded | Needs backtest first |
| Market reconciliation (real odds) | Scaffolded | Needs BDL odds data |
| Live replay validation | Not started | Needs `make fetch-bdl` + event data |
| Pi rating baseline | Not connected | Elo is connected; Pi pending |

---

## Acceptance criterion checklist

| Requirement | Status |
|-------------|--------|
| PMF sums to 1.0 | ✅ Tested, enforced at construction |
| All probabilities ≥ 0 | ✅ Tested |
| 1X2 sums to 1.0 | ✅ Tested |
| BTTS yes + no = 1.0 | ✅ Tested |
| Totals monotonic | ✅ Tested |
| No in-sample calibration | ✅ WalkForwardEngine trains on strictly pre-prediction-date data |
| Schema validation | ✅ Pydantic validates every BDL record |
| Odds timestamp present | ✅ ConsensusMarkets records `odds_timestamp` |
| Stale odds filtered | ✅ ConsensusMarkets has `stale_minutes` filter |
| No fake completeness | ✅ Unrun components are clearly marked as scaffolded |
