# Correct-Score Reconciliation Audit

**Generated**: 2026-07-15T09:50:25Z

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
- CS outcomes: 24  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-1 | 0.1523 | 0.1519 | 0.0004 |
| 1-0 | 0.1153 | 0.1062 | 0.0092 |
| 0-1 | 0.1076 | 0.0995 | 0.0082 |
| 0-0 | 0.1009 | 0.1196 | 0.0187 |
| 2-1 | 0.0807 | 0.0786 | 0.0021 |
| 1-2 | 0.0769 | 0.0736 | 0.0033 |
| 2-2 | 0.0577 | 0.0504 | 0.0072 |
| 2-0 | 0.0538 | 0.0658 | 0.0120 |
| 0-2 | 0.0504 | 0.0587 | 0.0083 |
| 3-1 | 0.0288 | 0.0304 | 0.0016 |
| 1-3 | 0.0260 | 0.0265 | 0.0005 |
| 3-0 | 0.0224 | 0.0271 | 0.0047 |
| 3-2 | 0.0224 | 0.0177 | 0.0047 |
| 2-3 | 0.0224 | 0.0165 | 0.0059 |
| 0-3 | 0.0197 | 0.0223 | 0.0026 |
| **Sum (top 15)** | **0.9375** | **0.9449** | — |
- High-score mass (total ≥9 goals): 1.34e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS
