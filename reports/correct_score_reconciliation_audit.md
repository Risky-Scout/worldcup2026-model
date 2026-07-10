# Correct-Score Reconciliation Audit

**Generated**: 2026-07-10T10:46:30Z

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
| Total 2026 matches predicted | 3 |
| Matches with any CS data | 3 |
| Matches with 1 CS vendor | 3 |
| Matches with 2+ CS vendors | 0 |

## Per-match correct-score audit

### Spain vs Belgium
- CS outcomes: 28  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-0 | 0.1065 | 0.1017 | 0.0048 |
| 1-1 | 0.1065 | 0.1119 | 0.0054 |
| 2-1 | 0.0998 | 0.1013 | 0.0015 |
| 2-0 | 0.0940 | 0.1051 | 0.0111 |
| 3-0 | 0.0614 | 0.0696 | 0.0081 |
| 3-1 | 0.0614 | 0.0647 | 0.0033 |
| 0-0 | 0.0571 | 0.0715 | 0.0145 |
| 2-2 | 0.0532 | 0.0504 | 0.0029 |
| 0-1 | 0.0470 | 0.0510 | 0.0040 |
| 1-2 | 0.0470 | 0.0483 | 0.0013 |
| 3-2 | 0.0380 | 0.0322 | 0.0059 |
| 4-0 | 0.0285 | 0.0339 | 0.0054 |
| 4-1 | 0.0285 | 0.0311 | 0.0026 |
| 0-2 | 0.0258 | 0.0260 | 0.0002 |
| 4-2 | 0.0195 | 0.0149 | 0.0045 |
| **Sum (top 15)** | **0.8743** | **0.9138** | — |
- High-score mass (total ≥9 goals): 2.24e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Norway vs England
- CS outcomes: 29  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-1 | 0.1130 | 0.1180 | 0.0051 |
| 1-2 | 0.0988 | 0.0998 | 0.0010 |
| 0-1 | 0.0930 | 0.0909 | 0.0021 |
| 0-2 | 0.0753 | 0.0871 | 0.0118 |
| 2-2 | 0.0659 | 0.0603 | 0.0056 |
| 2-1 | 0.0608 | 0.0614 | 0.0006 |
| 1-0 | 0.0565 | 0.0582 | 0.0017 |
| 1-3 | 0.0565 | 0.0594 | 0.0029 |
| 0-0 | 0.0494 | 0.0672 | 0.0178 |
| 0-3 | 0.0439 | 0.0530 | 0.0091 |
| 2-3 | 0.0395 | 0.0349 | 0.0046 |
| 2-0 | 0.0304 | 0.0348 | 0.0044 |
| 3-1 | 0.0255 | 0.0231 | 0.0024 |
| 3-2 | 0.0255 | 0.0208 | 0.0047 |
| 1-4 | 0.0255 | 0.0268 | 0.0013 |
| **Sum (top 15)** | **0.8596** | **0.8958** | — |
- High-score mass (total ≥9 goals): 2.44e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Argentina vs Switzerland
- CS outcomes: 25  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-0 | 0.1444 | 0.1376 | 0.0067 |
| 1-1 | 0.1244 | 0.1240 | 0.0004 |
| 2-0 | 0.1078 | 0.1167 | 0.0089 |
| 2-1 | 0.0951 | 0.0945 | 0.0006 |
| 0-0 | 0.0851 | 0.1001 | 0.0151 |
| 0-1 | 0.0622 | 0.0663 | 0.0041 |
| 3-0 | 0.0577 | 0.0650 | 0.0073 |
| 3-1 | 0.0476 | 0.0508 | 0.0033 |
| 1-2 | 0.0449 | 0.0440 | 0.0009 |
| 2-2 | 0.0425 | 0.0389 | 0.0036 |
| 3-2 | 0.0261 | 0.0208 | 0.0053 |
| 4-0 | 0.0261 | 0.0277 | 0.0017 |
| 0-2 | 0.0261 | 0.0274 | 0.0013 |
| 4-1 | 0.0225 | 0.0214 | 0.0011 |
| 2-3 | 0.0133 | 0.0092 | 0.0040 |
| **Sum (top 15)** | **0.9256** | **0.9446** | — |
- High-score mass (total ≥9 goals): 1.41e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS
