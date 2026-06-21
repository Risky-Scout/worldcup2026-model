# Live Model Replay Validation — 2022 World Cup

**Generated**: 2026-06-21T02:13:57Z
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
| Mean score NLL (all checkpoints) | 2.2287 |
| Mean 1X2 RPS | 0.1496 |
| Mean BTTS Brier | 0.1644 |
| Mean O/U 2.5 Brier | 0.1503 |

## Metrics by checkpoint minute

| Minute | N | Score NLL | 1X2 RPS | BTTS Brier | O/U 2.5 | Home cal err | Away cal err |
|--------|---|-----------|---------|------------|---------|-------------|-------------|
| 0 | 64 | 3.315 | 0.2306 | 0.25 | 0.2503 | -0.177 | -0.0675 |
| 5 | 64 | 3.2929 | 0.2321 | 0.2442 | 0.2462 | -0.2011 | -0.0495 |
| 10 | 64 | 3.2529 | 0.233 | 0.2209 | 0.2289 | -0.1813 | -0.0419 |
| 15 | 64 | 2.6563 | 0.2079 | 0.1803 | 0.1751 | -0.1842 | 0.0733 |
| 30 | 64 | 2.53 | 0.1862 | 0.1767 | 0.1675 | -0.2527 | 0.0115 |
| 45 | 64 | 2.2293 | 0.1551 | 0.1724 | 0.142 | -0.1239 | -0.0536 |
| 60 | 64 | 1.958 | 0.1157 | 0.1584 | 0.117 | -0.1285 | -0.058 |
| 75 | 64 | 1.5265 | 0.0954 | 0.1273 | 0.0802 | -0.0621 | -0.0986 |
| 85 | 64 | 1.1294 | 0.0361 | 0.0691 | 0.0671 | -0.1332 | -0.0795 |
| 90 | 64 | 0.3973 | 0.0037 | 0.0448 | 0.0288 | 0.0589 | 0.038 |

## Score-state calibration

| Score state | N | Home calibration error | Away calibration error |
|------------|---|----------------------|----------------------|
| aw1 | 69 | -0.2432 | -0.0212 |
| aw2+ | 37 | -0.1556 | 0.1058 |
| drawn | 382 | -0.1263 | -0.0461 |
| hw1 | 84 | -0.0932 | 0.1222 |
| hw2+ | 68 | -0.1477 | -0.2348 |

## First-Half Market Calibration

Evaluated using Log Loss (Ignorance Score) per penaltyblog's recommendation.
Checkpoints ≤ 45 min where first-half actual scores are available.

| Minute bucket | N | Mean FH NLL | Mean FH Brier |
|--------------|---|------------|--------------|
| 0 (pre-kickoff) | 64 | 1.5201 | 0.6388 |
| 1–15 | 192 | 1.4173 | 0.5871 |
| 16–30 | 64 | 1.0850 | 0.4236 |

**Overall first-half PMF: n=320  mean_NLL=1.3714**

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