# Correct-Score Reconciliation Audit

**Generated**: 2026-07-15T23:57:19Z

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
| Matches with any CS data | 1 |
| Matches with 1 CS vendor | 1 |
| Matches with 2+ CS vendors | 0 |

## Per-match correct-score audit

### France vs England
- CS outcomes: 28  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-1 | 0.1302 | 0.1198 | 0.0105 |
| 2-1 | 0.0977 | 0.0912 | 0.0065 |
| 1-0 | 0.0868 | 0.0817 | 0.0051 |
| 2-2 | 0.0710 | 0.0667 | 0.0044 |
| 0-1 | 0.0710 | 0.0659 | 0.0052 |
| 1-2 | 0.0710 | 0.0660 | 0.0050 |
| 2-0 | 0.0601 | 0.0584 | 0.0018 |
| 0-0 | 0.0601 | 0.0565 | 0.0036 |
| 3-1 | 0.0411 | 0.0415 | 0.0004 |
| 0-2 | 0.0391 | 0.0366 | 0.0025 |
| 3-2 | 0.0372 | 0.0344 | 0.0028 |
| 3-0 | 0.0340 | 0.0339 | 0.0001 |
| 1-3 | 0.0279 | 0.0265 | 0.0014 |
| 2-3 | 0.0279 | 0.0254 | 0.0025 |
| 4-1 | 0.0191 | 0.0193 | 0.0003 |
| **Sum (top 15)** | **0.8744** | **0.8239** | — |
- High-score mass (total ≥9 goals): 1.22e-04
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Spain vs Argentina
- CS outcomes: 0  |  CS vendors: 0  |  Publish mode: market_reconciled
- No correct-score data available for this match.
