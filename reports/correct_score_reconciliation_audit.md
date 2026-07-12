# Correct-Score Reconciliation Audit

**Generated**: 2026-07-12T18:41:45Z

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
| 1-1 | 0.1308 | 0.1348 | 0.0040 |
| 1-0 | 0.0923 | 0.0851 | 0.0072 |
| 2-1 | 0.0923 | 0.0914 | 0.0009 |
| 1-2 | 0.0747 | 0.0748 | 0.0001 |
| 2-2 | 0.0713 | 0.0640 | 0.0074 |
| 0-1 | 0.0713 | 0.0703 | 0.0011 |
| 2-0 | 0.0604 | 0.0709 | 0.0105 |
| 0-0 | 0.0604 | 0.0817 | 0.0214 |
| 0-2 | 0.0413 | 0.0488 | 0.0075 |
| 3-1 | 0.0392 | 0.0444 | 0.0052 |
| 3-2 | 0.0341 | 0.0295 | 0.0046 |
| 3-0 | 0.0302 | 0.0365 | 0.0064 |
| 1-3 | 0.0280 | 0.0304 | 0.0024 |
| 2-3 | 0.0280 | 0.0239 | 0.0041 |
| 3-3 | 0.0191 | 0.0130 | 0.0061 |
| **Sum (top 15)** | **0.8735** | **0.8996** | — |
- High-score mass (total ≥9 goals): 2.27e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### England vs Argentina
- CS outcomes: 24  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-1 | 0.1468 | 0.1471 | 0.0004 |
| 1-0 | 0.1153 | 0.1061 | 0.0092 |
| 0-1 | 0.1009 | 0.0969 | 0.0040 |
| 0-0 | 0.0950 | 0.1127 | 0.0177 |
| 2-1 | 0.0850 | 0.0809 | 0.0040 |
| 1-2 | 0.0734 | 0.0732 | 0.0002 |
| 2-0 | 0.0621 | 0.0690 | 0.0069 |
| 2-2 | 0.0577 | 0.0514 | 0.0063 |
| 0-2 | 0.0475 | 0.0573 | 0.0098 |
| 3-1 | 0.0310 | 0.0321 | 0.0011 |
| 3-0 | 0.0260 | 0.0288 | 0.0028 |
| 3-2 | 0.0260 | 0.0191 | 0.0069 |
| 1-3 | 0.0260 | 0.0271 | 0.0011 |
| 2-3 | 0.0224 | 0.0174 | 0.0050 |
| 0-3 | 0.0197 | 0.0222 | 0.0025 |
| **Sum (top 15)** | **0.9348** | **0.9414** | — |
- High-score mass (total ≥9 goals): 1.43e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS
