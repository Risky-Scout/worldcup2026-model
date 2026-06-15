# Live Model Replay Validation — 2022 World Cup

**Generated**: 2026-06-15T16:49:55Z
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
| Mean score NLL (all checkpoints) | 2.3589 |
| Mean 1X2 RPS | 0.1564 |
| Mean BTTS Brier | 0.1738 |
| Mean O/U 2.5 Brier | 0.162 |

## Metrics by checkpoint minute

| Minute | N | Score NLL | 1X2 RPS | BTTS Brier | O/U 2.5 | Home cal err | Away cal err |
|--------|---|-----------|---------|------------|---------|-------------|-------------|
| 0 | 64 | 3.315 | 0.2306 | 0.25 | 0.2503 | -0.177 | -0.0675 |
| 5 | 64 | 3.2979 | 0.232 | 0.2429 | 0.2447 | -0.1955 | -0.0527 |
| 10 | 64 | 3.2521 | 0.2335 | 0.2197 | 0.2263 | -0.1779 | -0.0444 |
| 15 | 64 | 3.0112 | 0.2345 | 0.218 | 0.2181 | -0.2122 | -0.0752 |
| 30 | 64 | 2.8737 | 0.2085 | 0.2113 | 0.2035 | -0.2757 | -0.1159 |
| 45 | 64 | 2.4878 | 0.1683 | 0.1877 | 0.1604 | -0.1464 | -0.1327 |
| 60 | 64 | 2.1583 | 0.1207 | 0.1669 | 0.1298 | -0.1397 | -0.1071 |
| 75 | 64 | 1.5953 | 0.0978 | 0.1285 | 0.0896 | -0.0754 | -0.1223 |
| 85 | 64 | 1.1998 | 0.0354 | 0.0684 | 0.0683 | -0.139 | -0.0854 |
| 90 | 64 | 0.3981 | 0.0029 | 0.0444 | 0.0287 | 0.0537 | 0.0328 |

## Score-state calibration

| Score state | N | Home calibration error | Away calibration error |
|------------|---|----------------------|----------------------|
| aw1 | 69 | -0.223 | -0.0903 |
| aw2+ | 37 | -0.0431 | 0.0973 |
| drawn | 382 | -0.0973 | -0.1076 |
| hw1 | 84 | -0.1344 | 0.0564 |
| hw2+ | 68 | -0.4356 | -0.1517 |

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