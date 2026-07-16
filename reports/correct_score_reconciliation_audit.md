# Correct-Score Reconciliation Audit

**Generated**: 2026-07-16T21:37:02Z

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
- CS outcomes: 35  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 2-1 | 0.0965 | 0.0940 | 0.0025 |
| 1-1 | 0.0965 | 0.0948 | 0.0017 |
| 2-2 | 0.0702 | 0.0694 | 0.0008 |
| 1-0 | 0.0643 | 0.0641 | 0.0002 |
| 1-2 | 0.0643 | 0.0630 | 0.0013 |
| 2-0 | 0.0594 | 0.0594 | 0.0001 |
| 3-1 | 0.0594 | 0.0591 | 0.0002 |
| 3-2 | 0.0482 | 0.0439 | 0.0043 |
| 0-1 | 0.0406 | 0.0409 | 0.0003 |
| 3-0 | 0.0386 | 0.0390 | 0.0004 |
| 0-0 | 0.0336 | 0.0340 | 0.0005 |
| 2-3 | 0.0336 | 0.0307 | 0.0028 |
| 4-1 | 0.0297 | 0.0279 | 0.0018 |
| 3-3 | 0.0276 | 0.0259 | 0.0017 |
| 0-2 | 0.0276 | 0.0277 | 0.0002 |
| **Sum (top 15)** | **0.7898** | **0.7740** | — |
- High-score mass (total ≥9 goals): 1.39e-04
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Spain vs Argentina
- CS outcomes: 0  |  CS vendors: 0  |  Publish mode: market_reconciled
- No correct-score data available for this match.
