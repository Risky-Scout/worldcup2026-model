# Correct-Score Reconciliation Audit

**Generated**: 2026-07-19T00:04:29Z

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
| 1-1 | 0.1265 | 0.1416 | 0.0152 |
| 1-0 | 0.1048 | 0.1089 | 0.0042 |
| 0-0 | 0.0863 | 0.1122 | 0.0260 |
| 2-1 | 0.0815 | 0.0866 | 0.0051 |
| 0-1 | 0.0815 | 0.0850 | 0.0035 |
| 2-0 | 0.0667 | 0.0829 | 0.0162 |
| 1-2 | 0.0611 | 0.0641 | 0.0030 |
| 2-2 | 0.0489 | 0.0505 | 0.0016 |
| 0-2 | 0.0407 | 0.0482 | 0.0075 |
| 3-1 | 0.0349 | 0.0398 | 0.0049 |
| 3-0 | 0.0282 | 0.0383 | 0.0101 |
| 3-2 | 0.0237 | 0.0214 | 0.0022 |
| 1-3 | 0.0204 | 0.0219 | 0.0015 |
| 2-3 | 0.0204 | 0.0156 | 0.0048 |
| 0-3 | 0.0131 | 0.0161 | 0.0030 |
| **Sum (top 15)** | **0.8386** | **0.9334** | — |
- High-score mass (total ≥9 goals): 1.45e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS
