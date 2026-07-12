# Correct-Score Reconciliation Audit

**Generated**: 2026-07-12T03:27:57Z

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
| Total 2026 matches predicted | 1 |
| Matches with any CS data | 1 |
| Matches with 1 CS vendor | 1 |
| Matches with 2+ CS vendors | 0 |

## Per-match correct-score audit

### France vs Spain
- CS outcomes: 28  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-1 | 0.1320 | 0.1350 | 0.0030 |
| 1-0 | 0.0932 | 0.0902 | 0.0030 |
| 2-1 | 0.0932 | 0.0917 | 0.0015 |
| 2-2 | 0.0720 | 0.0617 | 0.0103 |
| 0-1 | 0.0720 | 0.0734 | 0.0014 |
| 1-2 | 0.0720 | 0.0726 | 0.0006 |
| 0-0 | 0.0660 | 0.0850 | 0.0190 |
| 2-0 | 0.0609 | 0.0734 | 0.0125 |
| 0-2 | 0.0417 | 0.0490 | 0.0073 |
| 3-1 | 0.0396 | 0.0441 | 0.0045 |
| 3-2 | 0.0344 | 0.0285 | 0.0060 |
| 3-0 | 0.0283 | 0.0367 | 0.0085 |
| 1-3 | 0.0283 | 0.0289 | 0.0006 |
| 2-3 | 0.0283 | 0.0224 | 0.0059 |
| 3-3 | 0.0193 | 0.0118 | 0.0075 |
| **Sum (top 15)** | **0.8812** | **0.9044** | — |
- High-score mass (total ≥9 goals): 2.13e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS
