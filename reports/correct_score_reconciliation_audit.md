# Correct-Score Reconciliation Audit

**Generated**: 2026-07-13T22:11:46Z

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

### France vs Spain
- CS outcomes: 27  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-1 | 0.1319 | 0.1364 | 0.0045 |
| 1-0 | 0.0931 | 0.0825 | 0.0107 |
| 2-1 | 0.0931 | 0.0917 | 0.0015 |
| 1-2 | 0.0754 | 0.0749 | 0.0005 |
| 2-2 | 0.0720 | 0.0646 | 0.0074 |
| 0-1 | 0.0720 | 0.0682 | 0.0037 |
| 0-0 | 0.0660 | 0.0854 | 0.0194 |
| 2-0 | 0.0609 | 0.0705 | 0.0096 |
| 0-2 | 0.0417 | 0.0483 | 0.0067 |
| 3-1 | 0.0396 | 0.0445 | 0.0049 |
| 3-2 | 0.0344 | 0.0296 | 0.0049 |
| 3-0 | 0.0283 | 0.0361 | 0.0078 |
| 1-3 | 0.0283 | 0.0303 | 0.0020 |
| 2-3 | 0.0283 | 0.0239 | 0.0044 |
| 3-3 | 0.0193 | 0.0132 | 0.0061 |
| **Sum (top 15)** | **0.8841** | **0.8999** | — |
- High-score mass (total ≥9 goals): 2.28e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### England vs Argentina
- CS outcomes: 24  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-1 | 0.1488 | 0.1495 | 0.0006 |
| 1-0 | 0.1091 | 0.1034 | 0.0057 |
| 0-1 | 0.1023 | 0.0965 | 0.0058 |
| 0-0 | 0.0963 | 0.1149 | 0.0186 |
| 2-1 | 0.0862 | 0.0815 | 0.0046 |
| 1-2 | 0.0744 | 0.0730 | 0.0014 |
| 2-0 | 0.0585 | 0.0681 | 0.0097 |
| 2-2 | 0.0546 | 0.0507 | 0.0039 |
| 0-2 | 0.0512 | 0.0581 | 0.0070 |
| 3-1 | 0.0315 | 0.0322 | 0.0007 |
| 3-0 | 0.0264 | 0.0289 | 0.0025 |
| 1-3 | 0.0264 | 0.0269 | 0.0005 |
| 3-2 | 0.0241 | 0.0188 | 0.0052 |
| 2-3 | 0.0227 | 0.0172 | 0.0056 |
| 0-3 | 0.0200 | 0.0221 | 0.0021 |
| **Sum (top 15)** | **0.9323** | **0.9417** | — |
- High-score mass (total ≥9 goals): 1.42e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS
