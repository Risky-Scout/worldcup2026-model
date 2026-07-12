# Correct-Score Reconciliation Audit

**Generated**: 2026-07-12T13:39:08Z

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
- CS outcomes: 29  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-1 | 0.1311 | 0.1354 | 0.0043 |
| 2-1 | 0.0983 | 0.0935 | 0.0048 |
| 1-0 | 0.0925 | 0.0844 | 0.0082 |
| 2-2 | 0.0715 | 0.0643 | 0.0072 |
| 0-1 | 0.0715 | 0.0704 | 0.0011 |
| 1-2 | 0.0715 | 0.0739 | 0.0024 |
| 2-0 | 0.0605 | 0.0709 | 0.0104 |
| 0-0 | 0.0605 | 0.0824 | 0.0219 |
| 3-1 | 0.0414 | 0.0451 | 0.0038 |
| 0-2 | 0.0393 | 0.0481 | 0.0088 |
| 3-2 | 0.0342 | 0.0296 | 0.0046 |
| 3-0 | 0.0302 | 0.0365 | 0.0063 |
| 1-3 | 0.0281 | 0.0309 | 0.0028 |
| 2-3 | 0.0281 | 0.0239 | 0.0042 |
| 3-3 | 0.0192 | 0.0131 | 0.0061 |
| **Sum (top 15)** | **0.8778** | **0.9024** | — |
- High-score mass (total ≥9 goals): 2.27e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### England vs Argentina
- CS outcomes: 27  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-1 | 0.1329 | 0.1460 | 0.0131 |
| 1-0 | 0.0938 | 0.1041 | 0.0103 |
| 0-1 | 0.0886 | 0.0949 | 0.0063 |
| 2-1 | 0.0839 | 0.0813 | 0.0026 |
| 1-2 | 0.0797 | 0.0729 | 0.0069 |
| 0-0 | 0.0725 | 0.1074 | 0.0349 |
| 2-2 | 0.0613 | 0.0526 | 0.0088 |
| 2-0 | 0.0570 | 0.0725 | 0.0156 |
| 0-2 | 0.0532 | 0.0601 | 0.0069 |
| 3-1 | 0.0347 | 0.0335 | 0.0012 |
| 1-3 | 0.0347 | 0.0271 | 0.0076 |
| 3-0 | 0.0285 | 0.0301 | 0.0016 |
| 3-2 | 0.0285 | 0.0197 | 0.0088 |
| 2-3 | 0.0257 | 0.0169 | 0.0088 |
| 0-3 | 0.0235 | 0.0214 | 0.0021 |
| **Sum (top 15)** | **0.8984** | **0.9405** | — |
- High-score mass (total ≥9 goals): 1.43e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS
