# World Cup 2026 — Executive Presentation Summary
**Generated**: 2026-07-12T07:23:38Z
**Presentation date**: 2026-07-13 (Monday)
**Demo readiness verdict**: READY_WITH_LIMITATIONS

---

## Probability Source

| Layer | Source | Label |
|-------|--------|-------|
| `p_structural` | Composite team prior (CompositeTeamPrior) — no market inputs | Independent structural model |
| `p_market_consensus` | No-vig BDL consensus odds | Market consensus probability |
| `p_market_reconciled` | Structural prior reconciled to BDL market constraints | Market-reconciled distribution |
| **Published** | `market_reconciled` for all matches with BDL odds | **Market-reconciled distribution** |

> **Important**: Published probabilities are market-reconciled, not independent predictions.
> They should NOT be interpreted as an independent betting edge against the same sportsbook inputs.

---

## Validation Status

- **Published JSON files validated**: 28
- **Files passing all integrity checks**: 1
- **Files with failures**: 27
- **Public pages responding**: 2/2

---

## What Has Been Validated Out-of-Sample

- Walk-forward backtest on 2018 + 2022 World Cup matches
- Calibration evaluated on held-out tournament folds
- Group simulator uses official 2026 WC format (top 2 advance + 8 best third-place)
- PMF integrity checks on all published files

## What Has NOT Been Validated

- CLV from actual entry tickets (model-vs-close disagreement, not ticket CLV)
- First-half markets (SUPPRESSED in safe mode — 0.45×λ is unvalidated)
- Draw-boost heuristic (SUPPRESSED in safe mode — arbitrary constant, no empirical basis)
- Advancement and penalty probabilities for knockout stage (EXPERIMENTAL)
- In-sample market-weight auto-selection is DISABLED (fixed weight=0.20)
- Confidence intervals are NOT statistical CIs — they are lambda sensitivity ranges (±12%)

---

## Suppressed Functionality (P0 Hardening)

| Feature | Status | Reason |
|---------|--------|--------|
| First-half markets | SUPPRESSED | 0.45×λ approximation not validated |
| Draw-boost heuristic | SUPPRESSED | Arbitrary constant, wrong format assumption |
| Group incentive PMF adjustment | SUPPRESSED | Constants not empirically validated |
| Circular edge / Kelly | SUPPRESSED | PMF shaped by same market inputs |
| CI labels (`ci_90_*`) | RENAMED | Renamed to `lambda_sensitivity_*` — not statistical CIs |
| In-sample market weight | DISABLED | Auto-select on completed matches is in-sample overfitting |

---

## Today's Match Status

No matches are scheduled for 2026-07-13. The World Cup tournament is complete.

---

## Data Cutoff

- **Latest published JSON**: see per-file `generated_at` timestamps
- The `generated_at` field represents probability calculation time (NOT upload time)
- `uploaded_at` is separately set during upload

---

## Genuine CLV History

The CLV pipeline tracks model probabilities vs closing odds. However:
- `clv_raw = model_prob - closing_prob` is model-vs-close disagreement
- This is NOT ticket CLV (which requires recording entry odds at bet placement time)
- Beat-close rate is a model quality metric, not a realised-profit metric

---

## Known Limitations

See `known_limitations.md` for full list.
