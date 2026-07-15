# Correct-Score Reconciliation Audit

**Generated**: 2026-07-15T17:21:12Z

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
| 1-1 | 0.1523 | 0.1521 | 0.0002 |
| 1-0 | 0.1153 | 0.1059 | 0.0094 |
| 0-1 | 0.1076 | 0.0994 | 0.0082 |
| 0-0 | 0.1009 | 0.1197 | 0.0188 |
| 2-1 | 0.0807 | 0.0785 | 0.0022 |
| 1-2 | 0.0769 | 0.0737 | 0.0032 |
| 2-2 | 0.0577 | 0.0505 | 0.0072 |
| 2-0 | 0.0538 | 0.0656 | 0.0118 |
| 0-2 | 0.0504 | 0.0588 | 0.0084 |
| 3-1 | 0.0288 | 0.0303 | 0.0015 |
| 1-3 | 0.0260 | 0.0266 | 0.0006 |
| 3-0 | 0.0224 | 0.0270 | 0.0046 |
| 3-2 | 0.0224 | 0.0177 | 0.0047 |
| 2-3 | 0.0224 | 0.0165 | 0.0059 |
| 0-3 | 0.0197 | 0.0224 | 0.0027 |
| **Sum (top 15)** | **0.9375** | **0.9450** | — |
- High-score mass (total ≥9 goals): 1.33e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS
