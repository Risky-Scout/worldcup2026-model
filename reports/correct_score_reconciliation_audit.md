# Correct-Score Reconciliation Audit

**Generated**: 2026-07-19T09:45:10Z

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

### Spain vs Argentina
- CS outcomes: 78  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-1 | 0.1287 | 0.1446 | 0.0159 |
| 1-0 | 0.1048 | 0.1106 | 0.0058 |
| 2-1 | 0.0863 | 0.0869 | 0.0006 |
| 0-0 | 0.0815 | 0.1133 | 0.0318 |
| 0-1 | 0.0815 | 0.0874 | 0.0060 |
| 2-0 | 0.0667 | 0.0834 | 0.0167 |
| 1-2 | 0.0611 | 0.0638 | 0.0027 |
| 2-2 | 0.0524 | 0.0504 | 0.0020 |
| 0-2 | 0.0349 | 0.0480 | 0.0131 |
| 3-1 | 0.0319 | 0.0377 | 0.0058 |
| 3-0 | 0.0282 | 0.0373 | 0.0091 |
| 3-2 | 0.0262 | 0.0207 | 0.0055 |
| 1-3 | 0.0204 | 0.0215 | 0.0011 |
| 2-3 | 0.0204 | 0.0151 | 0.0053 |
| 0-3 | 0.0131 | 0.0161 | 0.0030 |
| **Sum (top 15)** | **0.8379** | **0.9369** | — |
- High-score mass (total ≥9 goals): 1.37e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS
