# Correct-Score Reconciliation Audit

**Generated**: 2026-07-11T18:30:00Z

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
| Total 2026 matches predicted | 3 |
| Matches with any CS data | 3 |
| Matches with 1 CS vendor | 3 |
| Matches with 2+ CS vendors | 0 |

## Per-match correct-score audit

### Norway vs England
- CS outcomes: 30  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-1 | 0.1113 | 0.1165 | 0.0052 |
| 1-2 | 0.0974 | 0.0985 | 0.0012 |
| 0-1 | 0.0866 | 0.0854 | 0.0011 |
| 0-2 | 0.0742 | 0.0817 | 0.0075 |
| 2-1 | 0.0649 | 0.0664 | 0.0015 |
| 2-2 | 0.0599 | 0.0614 | 0.0015 |
| 1-0 | 0.0556 | 0.0588 | 0.0031 |
| 1-3 | 0.0556 | 0.0581 | 0.0025 |
| 0-0 | 0.0519 | 0.0651 | 0.0132 |
| 0-3 | 0.0433 | 0.0495 | 0.0062 |
| 2-3 | 0.0371 | 0.0356 | 0.0015 |
| 2-0 | 0.0339 | 0.0379 | 0.0040 |
| 3-1 | 0.0251 | 0.0264 | 0.0013 |
| 3-2 | 0.0251 | 0.0234 | 0.0017 |
| 1-4 | 0.0251 | 0.0258 | 0.0007 |
| **Sum (top 15)** | **0.8470** | **0.8906** | — |
- High-score mass (total ≥9 goals): 2.62e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Argentina vs Switzerland
- CS outcomes: 22  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-0 | 0.1471 | 0.1382 | 0.0089 |
| 1-1 | 0.1244 | 0.1229 | 0.0016 |
| 2-0 | 0.1156 | 0.1196 | 0.0040 |
| 2-1 | 0.0952 | 0.0939 | 0.0013 |
| 0-0 | 0.0899 | 0.1017 | 0.0118 |
| 3-0 | 0.0622 | 0.0667 | 0.0045 |
| 0-1 | 0.0622 | 0.0658 | 0.0036 |
| 3-1 | 0.0476 | 0.0504 | 0.0029 |
| 2-2 | 0.0426 | 0.0384 | 0.0042 |
| 1-2 | 0.0426 | 0.0431 | 0.0005 |
| 4-0 | 0.0261 | 0.0279 | 0.0018 |
| 0-2 | 0.0261 | 0.0267 | 0.0006 |
| 3-2 | 0.0238 | 0.0201 | 0.0037 |
| 4-1 | 0.0225 | 0.0212 | 0.0012 |
| 1-3 | 0.0123 | 0.0108 | 0.0014 |
| **Sum (top 15)** | **0.9400** | **0.9474** | — |
- High-score mass (total ≥9 goals): 1.39e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### France vs Spain
- CS outcomes: 29  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-1 | 0.1325 | 0.1348 | 0.0023 |
| 1-0 | 0.0935 | 0.0893 | 0.0043 |
| 2-1 | 0.0935 | 0.0914 | 0.0021 |
| 0-1 | 0.0757 | 0.0749 | 0.0008 |
| 1-2 | 0.0723 | 0.0739 | 0.0016 |
| 0-0 | 0.0663 | 0.0842 | 0.0180 |
| 2-2 | 0.0663 | 0.0610 | 0.0053 |
| 2-0 | 0.0612 | 0.0714 | 0.0103 |
| 0-2 | 0.0442 | 0.0503 | 0.0062 |
| 3-1 | 0.0398 | 0.0435 | 0.0038 |
| 3-2 | 0.0306 | 0.0278 | 0.0028 |
| 3-0 | 0.0284 | 0.0357 | 0.0074 |
| 1-3 | 0.0284 | 0.0300 | 0.0016 |
| 2-3 | 0.0256 | 0.0227 | 0.0029 |
| 0-3 | 0.0194 | 0.0209 | 0.0015 |
| **Sum (top 15)** | **0.8776** | **0.9120** | — |
- High-score mass (total ≥9 goals): 2.15e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS
