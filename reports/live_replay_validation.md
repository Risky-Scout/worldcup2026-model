# Live Model Replay Validation — 2022 World Cup

**Generated**: 2026-06-12T00:28:25Z
**Matches replayed**: 64
**Checkpoints per match**: 10

## Methodology

Each 2022 completed match is replayed minute-by-minute using BDL event data.
At each checkpoint, the live hazard model predicts remaining goals and score
probabilities from the current match state. Predictions are evaluated against
the actual final score.

The hazard model uses:
- Non-homogeneous temporal baseline (calibrated from WC goal distribution)
- Score-state intensity adjustments (Dixon & Robinson 1998)
- Red card multipliers
- Live xG rate blend (when available from BDL stats)

## Overall metrics

| Metric | Value |
|--------|-------|
| Matches replayed | 64 |
| Mean score NLL (all checkpoints) | 2.0744 |
| Mean 1X2 RPS | 0.1412 |
| Mean BTTS Brier | 0.1717 |
| Mean O/U 2.5 Brier | 0.1429 |

## Metrics by checkpoint minute

| Minute | N | Score NLL | 1X2 RPS | BTTS Brier | O/U 2.5 | Home cal err | Away cal err |
|--------|---|-----------|---------|------------|---------|-------------|-------------|
| 0 | 64 | 3.316 | 0.2319 | 0.2498 | 0.2498 | -0.1737 | -0.0691 |
| 5 | 64 | 2.9975 | 0.2264 | 0.2383 | 0.2231 | -0.1246 | -0.0333 |
| 10 | 64 | 2.919 | 0.2184 | 0.2279 | 0.2041 | -0.0914 | -0.0236 |
| 15 | 64 | 2.8081 | 0.2031 | 0.2298 | 0.1922 | -0.0767 | -0.0105 |
| 30 | 64 | 2.5201 | 0.157 | 0.2281 | 0.1723 | -0.037 | -0.0001 |
| 45 | 64 | 2.2792 | 0.1421 | 0.212 | 0.1664 | -0.0383 | -0.0848 |
| 60 | 64 | 1.9347 | 0.1151 | 0.1854 | 0.1299 | -0.0637 | -0.0613 |
| 75 | 64 | 1.1866 | 0.0799 | 0.1002 | 0.0767 | 0.0507 | 0.0009 |
| 85 | 64 | 0.6023 | 0.0349 | 0.0416 | 0.0069 | 0.0173 | 0.0078 |
| 90 | 64 | 0.1805 | 0.0031 | 0.0041 | 0.0076 | 0.1014 | 0.0791 |

## Score-state calibration

| Score state | N | Home calibration error | Away calibration error |
|------------|---|----------------------|----------------------|
| aw1 | 88 | 0.1346 | -0.291 |
| aw2+ | 36 | 0.2394 | 0.1139 |
| drawn | 335 | -0.0219 | 0.0215 |
| hw1 | 102 | -0.0937 | -0.0477 |
| hw2+ | 79 | -0.3982 | 0.0849 |

## Live model implementation status

| Module | Status |
|--------|--------|
| src/wc2026/live/state.py | ✓ Implemented |
| src/wc2026/live/features.py | ✓ Implemented |
| src/wc2026/live/hazard.py | ✓ Implemented (temporal baseline + score-state + red card) |
| src/wc2026/live/predictor.py | ✓ Implemented |
| src/wc2026/live/replay.py | ✓ Implemented |
| src/wc2026/live/validation.py | ✓ Implemented |
| Live xG integration | Partial — uses xG from BDL stats when available |
| Momentum feed | Not yet integrated |
| Live odds | Not yet integrated |
| Live betting edge screening | Not implemented |

## Known limitations

1. **Hazard calibration**: The temporal baseline uses WC 2018+2022 empirical
   distribution as a prior. Minute-specific calibration from replay data will
   be applied in the next version once replay metrics are confirmed.
2. **xG availability**: BDL xG data was not available for most 2022 matches in
   the training snapshot. Replay uses pregame λ for all checkpoints where xG
   is missing — this is correctly flagged in warnings.
3. **No momentum integration**: BDL momentum feed is fetched but not yet used
   as a live feature. Added to features.py for future integration.
4. **No live odds**: Live market odds would improve prediction but introduce
   complex timestamp constraints. Not yet implemented.

## Readiness assessment

| Dimension | Status |
|-----------|--------|
| Pre-game probabilities | **READY** — clean PMF, market-reconciled |
| Pre-game betting edge screening | **NOT READY** — needs fair-odds filter + CLV |
| Live probabilities | **PROTOTYPE** — hazard model implemented, replay validated |
| Live betting edge | **NOT READY** — no live odds integration |