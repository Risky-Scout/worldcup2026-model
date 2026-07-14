# Live Model Replay Validation — 2022 World Cup

**Generated**: 2026-07-14T23:16:04Z
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
| Mean score NLL (all checkpoints) | 2.2272 |
| Mean 1X2 RPS | 0.1497 |
| Mean BTTS Brier | 0.1643 |
| Mean O/U 2.5 Brier | 0.1503 |

## Metrics by checkpoint minute

| Minute | N | Score NLL | 1X2 RPS | BTTS Brier | O/U 2.5 | Home cal err | Away cal err |
|--------|---|-----------|---------|------------|---------|-------------|-------------|
| 0 | 64 | 3.315 | 0.2312 | 0.25 | 0.2503 | -0.177 | -0.0675 |
| 5 | 64 | 3.2882 | 0.2308 | 0.2443 | 0.2465 | -0.1856 | -0.0541 |
| 10 | 64 | 3.2496 | 0.2312 | 0.2206 | 0.2285 | -0.1832 | -0.0346 |
| 15 | 64 | 2.6529 | 0.2077 | 0.18 | 0.1755 | -0.179 | 0.0726 |
| 30 | 64 | 2.5261 | 0.1873 | 0.1761 | 0.1668 | -0.2498 | 0.0135 |
| 45 | 64 | 2.2268 | 0.1551 | 0.1715 | 0.1424 | -0.1219 | -0.0525 |
| 60 | 64 | 1.9608 | 0.1182 | 0.1591 | 0.1169 | -0.1264 | -0.057 |
| 75 | 64 | 1.5263 | 0.0959 | 0.1273 | 0.0799 | -0.062 | -0.0975 |
| 85 | 64 | 1.1291 | 0.0362 | 0.069 | 0.0671 | -0.1325 | -0.0795 |
| 90 | 64 | 0.3974 | 0.0038 | 0.0449 | 0.0289 | 0.0592 | 0.0379 |

## Score-state calibration

| Score state | N | Home calibration error | Away calibration error |
|------------|---|----------------------|----------------------|
| aw1 | 69 | -0.2341 | -0.0284 |
| aw2+ | 37 | -0.1506 | 0.1026 |
| drawn | 382 | -0.1223 | -0.0453 |
| hw1 | 84 | -0.1014 | 0.1312 |
| hw2+ | 68 | -0.1463 | -0.2344 |

## First-Half Market Calibration

Evaluated using Log Loss (Ignorance Score) per penaltyblog's recommendation.
Checkpoints ≤ 45 min where first-half actual scores are available.

| Minute bucket | N | Mean FH NLL | Mean FH Brier |
|--------------|---|------------|--------------|
| 0 (pre-kickoff) | 64 | 1.5201 | 0.6388 |
| 1–15 | 192 | 1.4117 | 0.5852 |
| 16–30 | 64 | 1.0811 | 0.4225 |

**Overall first-half PMF: n=320  mean_NLL=1.3673**

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