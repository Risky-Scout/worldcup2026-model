# Correct-Score Reconciliation Audit

**Generated**: 2026-07-14T20:51:56Z

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
| 1-1 | 0.1333 | 0.1372 | 0.0038 |
| 1-0 | 0.0941 | 0.0832 | 0.0109 |
| 2-1 | 0.0941 | 0.0907 | 0.0034 |
| 0-1 | 0.0800 | 0.0729 | 0.0071 |
| 1-2 | 0.0762 | 0.0763 | 0.0001 |
| 0-0 | 0.0727 | 0.0887 | 0.0160 |
| 2-2 | 0.0667 | 0.0628 | 0.0039 |
| 2-0 | 0.0615 | 0.0685 | 0.0070 |
| 0-2 | 0.0421 | 0.0501 | 0.0080 |
| 3-1 | 0.0381 | 0.0423 | 0.0042 |
| 3-2 | 0.0308 | 0.0278 | 0.0030 |
| 3-0 | 0.0286 | 0.0343 | 0.0058 |
| 1-3 | 0.0286 | 0.0313 | 0.0027 |
| 2-3 | 0.0258 | 0.0236 | 0.0022 |
| 0-3 | 0.0195 | 0.0220 | 0.0025 |
| **Sum (top 15)** | **0.8922** | **0.9116** | — |
- High-score mass (total ≥9 goals): 2.17e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### England vs Argentina
- CS outcomes: 24  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-1 | 0.1481 | 0.1509 | 0.0028 |
| 1-0 | 0.1143 | 0.1043 | 0.0099 |
| 0-1 | 0.1000 | 0.0952 | 0.0048 |
| 0-0 | 0.0941 | 0.1161 | 0.0220 |
| 2-1 | 0.0842 | 0.0803 | 0.0039 |
| 1-2 | 0.0762 | 0.0737 | 0.0025 |
| 2-0 | 0.0571 | 0.0673 | 0.0101 |
| 2-2 | 0.0571 | 0.0517 | 0.0055 |
| 0-2 | 0.0500 | 0.0581 | 0.0081 |
| 3-1 | 0.0308 | 0.0316 | 0.0008 |
| 3-2 | 0.0258 | 0.0187 | 0.0071 |
| 1-3 | 0.0258 | 0.0268 | 0.0010 |
| 3-0 | 0.0235 | 0.0279 | 0.0044 |
| 2-3 | 0.0235 | 0.0172 | 0.0064 |
| 0-3 | 0.0195 | 0.0221 | 0.0026 |
| **Sum (top 15)** | **0.9301** | **0.9420** | — |
- High-score mass (total ≥9 goals): 1.41e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS
