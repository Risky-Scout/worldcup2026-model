# Correct-Score Reconciliation Audit

**Generated**: 2026-07-18T21:04:40Z

## Method

Correct-score odds are used via **gentle IPF** (iterative proportional fitting),
NOT via SLSQP equality constraints.

Reason SLSQP was removed: the market_implied PMF already satisfies 1X2/totals
by construction. Running SLSQP with those same constraints as equalities is
numerically degenerate → optimizer deposits mass in impossible cells (4-9, 11-5).

IPF approach: `P_new(h,a) = α * P_mkt(h,a) + (1-α) * P_prior(h,a)`, then renormalize.
- α = 0.30 when n_cs_vendors = 1 (low confidence)
- α = 0.50 when n_cs_vendors ≥ 2 (higher confidence)

## Summary

| Metric | Value |
|--------|-------|
| Total 2026 matches predicted | 2 |
| Matches with any CS data | 2 |
| Matches with 1 CS vendor | 2 |
| Matches with 2+ CS vendors | 0 |

## Per-match correct-score audit

### France vs England
- CS outcomes: 75  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 2-1 | 0.0846 | 0.0891 | 0.0046 |
| 1-1 | 0.0846 | 0.0897 | 0.0051 |
| 2-2 | 0.0653 | 0.0696 | 0.0043 |
| 1-0 | 0.0553 | 0.0593 | 0.0040 |
| 2-0 | 0.0553 | 0.0594 | 0.0041 |
| 3-1 | 0.0553 | 0.0597 | 0.0044 |
| 1-2 | 0.0553 | 0.0584 | 0.0031 |
| 3-2 | 0.0449 | 0.0433 | 0.0016 |
| 3-0 | 0.0378 | 0.0411 | 0.0033 |
| 0-1 | 0.0378 | 0.0404 | 0.0026 |
| 4-1 | 0.0312 | 0.0310 | 0.0002 |
| 0-0 | 0.0312 | 0.0335 | 0.0023 |
| 2-3 | 0.0312 | 0.0299 | 0.0014 |
| 3-3 | 0.0257 | 0.0257 | 0.0000 |
| 0-2 | 0.0257 | 0.0274 | 0.0017 |
| **Sum (top 15)** | **0.7213** | **0.7575** | — |
- High-score mass (total ≥9 goals): 1.45e-04
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Spain vs Argentina
- CS outcomes: 78  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-1 | 0.1286 | 0.1436 | 0.0150 |
| 1-0 | 0.1128 | 0.1113 | 0.0015 |
| 2-1 | 0.0815 | 0.0858 | 0.0044 |
| 0-0 | 0.0815 | 0.1113 | 0.0299 |
| 0-1 | 0.0815 | 0.0853 | 0.0038 |
| 2-0 | 0.0667 | 0.0819 | 0.0152 |
| 1-2 | 0.0611 | 0.0646 | 0.0036 |
| 2-2 | 0.0489 | 0.0510 | 0.0021 |
| 0-2 | 0.0367 | 0.0476 | 0.0109 |
| 3-1 | 0.0349 | 0.0392 | 0.0043 |
| 3-0 | 0.0282 | 0.0377 | 0.0095 |
| 3-2 | 0.0237 | 0.0210 | 0.0026 |
| 1-3 | 0.0204 | 0.0221 | 0.0018 |
| 2-3 | 0.0179 | 0.0154 | 0.0025 |
| 0-3 | 0.0131 | 0.0164 | 0.0033 |
| **Sum (top 15)** | **0.8372** | **0.9343** | — |
- High-score mass (total ≥9 goals): 1.45e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS
