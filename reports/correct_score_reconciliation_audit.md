# Correct-Score Reconciliation Audit

**Generated**: 2026-07-15T02:52:24Z

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

### England vs Argentina
- CS outcomes: 23  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-1 | 0.1466 | 0.1510 | 0.0044 |
| 1-0 | 0.1152 | 0.1025 | 0.0127 |
| 0-1 | 0.1075 | 0.0977 | 0.0098 |
| 0-0 | 0.1008 | 0.1204 | 0.0196 |
| 2-1 | 0.0806 | 0.0780 | 0.0027 |
| 1-2 | 0.0768 | 0.0747 | 0.0021 |
| 2-2 | 0.0576 | 0.0521 | 0.0055 |
| 2-0 | 0.0537 | 0.0639 | 0.0102 |
| 0-2 | 0.0504 | 0.0594 | 0.0091 |
| 3-1 | 0.0288 | 0.0301 | 0.0013 |
| 1-3 | 0.0288 | 0.0281 | 0.0007 |
| 3-2 | 0.0237 | 0.0180 | 0.0057 |
| 3-0 | 0.0224 | 0.0263 | 0.0039 |
| 0-3 | 0.0224 | 0.0237 | 0.0013 |
| 2-3 | 0.0224 | 0.0172 | 0.0052 |
| **Sum (top 15)** | **0.9376** | **0.9431** | — |
- High-score mass (total ≥9 goals): 1.40e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS
