# Correct-Score Reconciliation Audit

**Generated**: 2026-07-12T09:44:07Z

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
| 1-1 | 0.1311 | 0.1352 | 0.0042 |
| 2-1 | 0.0983 | 0.0936 | 0.0047 |
| 1-0 | 0.0925 | 0.0851 | 0.0074 |
| 2-2 | 0.0715 | 0.0637 | 0.0078 |
| 0-1 | 0.0715 | 0.0703 | 0.0012 |
| 1-2 | 0.0715 | 0.0733 | 0.0018 |
| 2-0 | 0.0605 | 0.0715 | 0.0110 |
| 0-0 | 0.0605 | 0.0823 | 0.0218 |
| 3-1 | 0.0414 | 0.0451 | 0.0037 |
| 0-2 | 0.0393 | 0.0479 | 0.0086 |
| 3-2 | 0.0342 | 0.0294 | 0.0048 |
| 3-0 | 0.0302 | 0.0369 | 0.0067 |
| 1-3 | 0.0281 | 0.0300 | 0.0019 |
| 2-3 | 0.0281 | 0.0237 | 0.0044 |
| 3-3 | 0.0192 | 0.0128 | 0.0063 |
| **Sum (top 15)** | **0.8778** | **0.9008** | — |
- High-score mass (total ≥9 goals): 2.27e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### England vs Argentina
- CS outcomes: 27  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-1 | 0.1329 | 0.1454 | 0.0125 |
| 1-0 | 0.0938 | 0.1044 | 0.0106 |
| 0-1 | 0.0886 | 0.0943 | 0.0057 |
| 2-1 | 0.0839 | 0.0819 | 0.0020 |
| 1-2 | 0.0797 | 0.0726 | 0.0072 |
| 0-0 | 0.0725 | 0.1065 | 0.0340 |
| 2-2 | 0.0613 | 0.0526 | 0.0087 |
| 2-0 | 0.0570 | 0.0731 | 0.0161 |
| 0-2 | 0.0532 | 0.0594 | 0.0062 |
| 3-1 | 0.0347 | 0.0340 | 0.0006 |
| 1-3 | 0.0347 | 0.0269 | 0.0077 |
| 3-0 | 0.0285 | 0.0307 | 0.0022 |
| 3-2 | 0.0285 | 0.0200 | 0.0084 |
| 2-3 | 0.0257 | 0.0170 | 0.0088 |
| 0-3 | 0.0235 | 0.0211 | 0.0024 |
| **Sum (top 15)** | **0.8984** | **0.9398** | — |
- High-score mass (total ≥9 goals): 1.44e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS
