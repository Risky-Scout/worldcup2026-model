# Production Readiness Assessment

**Generated**: 2026-07-16T12:24:17Z

## Status: PRE-GAME PMF READY — LIVE BETTING NOT YET APPROVED

The pipeline produces real, market-anchored predictions for all 72 named 2026 WC matches.
The publish champion is market_reconciled for all matches with BDL odds.
The composite team prior now integrates market odds, FIFA rankings, qualifying performance,
penaltyblog ratings, and confederation strength — no team defaults to Elo=1500.

## What is production-ready

| Capability | Status |
|------------|--------|
| BDL real data ingestion (2018+2022+2026) | ✅ 10 models, 128 OOF matches |
| Opening day June 11: Mexico+SA, Korea+Czechia | ✅ correct schedules and priors |
| market_reconciled publish champion | ✅ all 72 named group-stage matches |
| Composite prior: market + FIFA + qualifying + Elo + Pi + Massey | ✅ all 48 teams |
| 48/48 teams with market-implied lambdas | ✅ |
| No team defaults to Elo=1500 for named WC teams | ✅ |
| FIFA March 2026 rankings integrated | ✅ |
| WC 2026 qualifying performance integrated | ✅ |
| 5,047 correct-score rows used in KL reconciliation | ✅ |
| Temperature calibration fitted on OOF predictions | ✅ T values: 1.077–3.000 |
| PMF sums to 1.0, all markets derived from single PMF | ✅ |
| Published artifacts: no impossible high-score cells | ✅ |
| tail_mass_exact in every published JSON | ✅ |
| O/U monotonically decreasing in every published JSON | ✅ |
| Live in-game PMF engine (hazard + Poisson convolution) | ✅ |
| Live replay: 64 2022 matches × 10 checkpoints, real BDL events | ✅ 0 synthetic rows |
| Live NLL: 3.31→0.40 correctly decreasing over 90 min | ✅ |
| Pre-game edge screening (fair odds + half-Kelly + 90% CI) | ✅ |
| CLV tracking store (prediction → closing line comparison) | ✅ |
| GitHub Actions CI (test + validate-published + validate-live) | ✅ |
| 1290 tests passing | ✅ |

## What is NOT yet production-ready

| Gap | Impact | Next step |
|-----|--------|-----------|
| parametric models lose to Poisson(1.35) baseline | HIGH | Needs 2026 match results to accumulate |
| Correct-score reconciliation not walk-forward backtested | MEDIUM | Need historical CS odds (2018/2022) from BDL |
| Temperature T≈3.0 for parametric models | MEDIUM | Expected: 128 WC matches too few for stable estimation |
| Opening vs closing line drift tracking | LOW | Requires daily BDL odds snapshots as 2026 progresses |
| Live betting edge screening | LOW | Requires BDL live-match odds endpoint |
| First-half PMF | LOW | Needs BDL first-half score data |

## Champion policy summary

| Champion | Model | NLL | Used for |
|----------|-------|-----|---------|
| diagnostic_champion | pi_rating | 3.0046 | Audit only |
| pure_model_champion | negative_binomial | 4.4369 if available | Parametric prior |
| rating_champion | negative_binomial | N/A | Composite prior |
| market_champion | market_implied | N/A | Direct market inference |
| **publish_champion** | **market_reconciled** | — | **Published predictions** |