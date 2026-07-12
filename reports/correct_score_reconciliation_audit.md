# Correct-Score Reconciliation Audit

**Generated**: 2026-07-12T19:36:23Z

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
- CS outcomes: 28  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-1 | 0.1309 | 0.1341 | 0.0032 |
| 1-0 | 0.0924 | 0.0849 | 0.0075 |
| 2-1 | 0.0924 | 0.0917 | 0.0007 |
| 0-1 | 0.0748 | 0.0709 | 0.0039 |
| 1-2 | 0.0748 | 0.0747 | 0.0001 |
| 2-2 | 0.0714 | 0.0638 | 0.0076 |
| 0-0 | 0.0655 | 0.0830 | 0.0176 |
| 2-0 | 0.0604 | 0.0706 | 0.0102 |
| 3-1 | 0.0413 | 0.0451 | 0.0037 |
| 0-2 | 0.0413 | 0.0484 | 0.0071 |
| 3-0 | 0.0302 | 0.0367 | 0.0065 |
| 3-2 | 0.0302 | 0.0288 | 0.0014 |
| 1-3 | 0.0302 | 0.0307 | 0.0005 |
| 2-3 | 0.0281 | 0.0238 | 0.0043 |
| 0-3 | 0.0192 | 0.0207 | 0.0016 |
| **Sum (top 15)** | **0.8831** | **0.9079** | — |
- High-score mass (total ≥9 goals): 2.27e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### England vs Argentina
- CS outcomes: 24  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-1 | 0.1468 | 0.1472 | 0.0004 |
| 1-0 | 0.1153 | 0.1061 | 0.0092 |
| 0-1 | 0.1009 | 0.0969 | 0.0040 |
| 0-0 | 0.0950 | 0.1126 | 0.0177 |
| 2-1 | 0.0850 | 0.0810 | 0.0040 |
| 1-2 | 0.0734 | 0.0732 | 0.0002 |
| 2-0 | 0.0621 | 0.0690 | 0.0069 |
| 2-2 | 0.0577 | 0.0514 | 0.0063 |
| 0-2 | 0.0475 | 0.0573 | 0.0098 |
| 3-1 | 0.0310 | 0.0322 | 0.0011 |
| 3-0 | 0.0260 | 0.0288 | 0.0028 |
| 3-2 | 0.0260 | 0.0191 | 0.0070 |
| 1-3 | 0.0260 | 0.0271 | 0.0011 |
| 2-3 | 0.0224 | 0.0174 | 0.0050 |
| 0-3 | 0.0197 | 0.0222 | 0.0025 |
| **Sum (top 15)** | **0.9348** | **0.9414** | — |
- High-score mass (total ≥9 goals): 1.43e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS
