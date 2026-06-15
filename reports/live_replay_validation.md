# Live Model Replay Validation — 2022 World Cup

**Generated**: 2026-06-15T22:09:27Z
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
| Mean score NLL (all checkpoints) | 2.3496 |
| Mean 1X2 RPS | 0.156 |
| Mean BTTS Brier | 0.1757 |
| Mean O/U 2.5 Brier | 0.163 |

## Metrics by checkpoint minute

| Minute | N | Score NLL | 1X2 RPS | BTTS Brier | O/U 2.5 | Home cal err | Away cal err |
|--------|---|-----------|---------|------------|---------|-------------|-------------|
| 0 | 64 | 3.315 | 0.2306 | 0.25 | 0.2503 | -0.177 | -0.0675 |
| 5 | 64 | 3.2929 | 0.2321 | 0.2442 | 0.2462 | -0.2011 | -0.0495 |
| 10 | 64 | 3.2529 | 0.233 | 0.2209 | 0.2289 | -0.1813 | -0.0419 |
| 15 | 64 | 2.9959 | 0.2328 | 0.2215 | 0.2201 | -0.2096 | -0.076 |
| 30 | 64 | 2.8419 | 0.2056 | 0.2104 | 0.2047 | -0.2752 | -0.123 |
| 45 | 64 | 2.4572 | 0.1678 | 0.1905 | 0.161 | -0.1391 | -0.1548 |
| 60 | 64 | 2.1504 | 0.1215 | 0.171 | 0.1304 | -0.1379 | -0.1262 |
| 75 | 64 | 1.5949 | 0.0986 | 0.1338 | 0.0904 | -0.071 | -0.1356 |
| 85 | 64 | 1.1939 | 0.0355 | 0.0701 | 0.0691 | -0.1362 | -0.0922 |
| 90 | 64 | 0.4011 | 0.0031 | 0.0449 | 0.0286 | 0.0563 | 0.0262 |

## Score-state calibration

| Score state | N | Home calibration error | Away calibration error |
|------------|---|----------------------|----------------------|
| aw1 | 69 | -0.2709 | -0.1337 |
| aw2+ | 37 | -0.1148 | 0.0545 |
| drawn | 382 | -0.0929 | -0.1039 |
| hw1 | 84 | -0.1506 | 0.0911 |
| hw2+ | 68 | -0.3403 | -0.2139 |

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