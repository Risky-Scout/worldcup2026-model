# Correct-Score Reconciliation Audit

**Generated**: 2026-07-17T09:47:36Z

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
| 2-1 | 0.0897 | 0.0935 | 0.0037 |
| 1-1 | 0.0897 | 0.0944 | 0.0046 |
| 2-2 | 0.0684 | 0.0720 | 0.0036 |
| 1-0 | 0.0598 | 0.0638 | 0.0039 |
| 2-0 | 0.0552 | 0.0593 | 0.0041 |
| 3-1 | 0.0552 | 0.0593 | 0.0040 |
| 1-2 | 0.0552 | 0.0581 | 0.0029 |
| 3-2 | 0.0449 | 0.0431 | 0.0018 |
| 0-1 | 0.0378 | 0.0406 | 0.0028 |
| 3-0 | 0.0342 | 0.0376 | 0.0034 |
| 0-0 | 0.0312 | 0.0339 | 0.0027 |
| 2-3 | 0.0312 | 0.0297 | 0.0015 |
| 4-1 | 0.0276 | 0.0279 | 0.0003 |
| 3-3 | 0.0276 | 0.0272 | 0.0004 |
| 0-2 | 0.0256 | 0.0274 | 0.0017 |
| **Sum (top 15)** | **0.7335** | **0.7677** | — |
- High-score mass (total ≥9 goals): 1.45e-04
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Spain vs Argentina
- CS outcomes: 78  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-1 | 0.1303 | 0.1445 | 0.0142 |
| 1-0 | 0.1123 | 0.1117 | 0.0006 |
| 2-1 | 0.0811 | 0.0853 | 0.0042 |
| 0-0 | 0.0811 | 0.1118 | 0.0307 |
| 0-1 | 0.0811 | 0.0863 | 0.0052 |
| 2-0 | 0.0663 | 0.0819 | 0.0155 |
| 1-2 | 0.0608 | 0.0646 | 0.0038 |
| 2-2 | 0.0521 | 0.0512 | 0.0010 |
| 3-1 | 0.0347 | 0.0386 | 0.0038 |
| 0-2 | 0.0347 | 0.0478 | 0.0130 |
| 3-0 | 0.0281 | 0.0372 | 0.0091 |
| 3-2 | 0.0235 | 0.0207 | 0.0028 |
| 1-3 | 0.0203 | 0.0221 | 0.0018 |
| 2-3 | 0.0203 | 0.0156 | 0.0047 |
| 0-3 | 0.0130 | 0.0165 | 0.0035 |
| **Sum (top 15)** | **0.8397** | **0.9356** | — |
- High-score mass (total ≥9 goals): 1.41e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS
