# Production Readiness Assessment

**Generated**: 2026-06-12T00:17:01Z

## Status: NOT YET PUBLISHABLE AS STANDALONE PREDICTION TOOL

The pipeline produces real, market-anchored predictions for all 72 named 2026 WC matches.
The publish champion is market_reconciled for all matches with BDL odds.
The composite team prior replaces plain Elo=1500 for all teams.

## What is production-ready

| Capability | Status |
|------------|--------|
| BDL real data ingestion | ✅ 9 models, 128 OOF matches |
| June 11 opening day: Mexico+SA, Korea+Czechia | ✅ |
| market_reconciled publish champion | ✅ all 72 named matches |
| Composite team prior (market-implied + Elo + Pi + Massey) | ✅ |
| 48/48 teams with market-implied lambdas | ✅ |
| Plain Elo=1500 removed as fallback for new teams | ✅ |
| 5,047 correct-score rows used in KL reconciliation | ✅ |
| Temperature calibration fitted on OOF (not defaulting to T=1.0) | ✅ |
| PMF sums to 1.0, all markets derived from single PMF | ✅ |
| 110 tests passing | ✅ |

## What is NOT yet production-ready

| Gap | Impact | Next step |
|-----|--------|-----------|
| Live in-game model | HIGH | Validate on 2022 minute replay |
| parametric_champion loses to Poisson(1.35) | HIGH | More data (2026 results) |
| No FIFA ranking integration | MEDIUM | Add to composite prior |
| No qualifying performance data | MEDIUM | Add to composite prior |
| Correct-score reconciliation not backtested | MEDIUM | Need historical CS odds |
| Temperature T≈3.0 for parametric models | MEDIUM | More OOF data |
| No opening-line vs closing-line tracking | LOW | Daily BDL snapshots |

## Champion policy summary

| Champion | Model | NLL | Used for |
|----------|-------|-----|---------|
| diagnostic_champion | equal_probability | 3.0219 | Audit only |
| pure_model_champion | negative_binomial | 4.5159 if available | Parametric prior |
| rating_champion | negative_binomial | N/A | Composite prior |
| market_champion | market_implied | N/A | Direct market inference |
| **publish_champion** | **market_reconciled** | — | **Published predictions** |