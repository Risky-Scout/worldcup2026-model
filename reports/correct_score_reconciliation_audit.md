# Correct-Score Reconciliation Audit

**Generated**: 2026-07-10T01:28:13Z

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
| 1-1 | 0.1128 | 0.1124 | 0.0004 |
| 1-0 | 0.1053 | 0.1030 | 0.0022 |
| 2-1 | 0.1053 | 0.1035 | 0.0018 |
| 2-0 | 0.0929 | 0.1039 | 0.0111 |
| 3-0 | 0.0607 | 0.0686 | 0.0079 |
| 3-1 | 0.0607 | 0.0644 | 0.0037 |
| 0-0 | 0.0564 | 0.0686 | 0.0122 |
| 2-2 | 0.0526 | 0.0498 | 0.0028 |
| 0-1 | 0.0493 | 0.0524 | 0.0030 |
| 1-2 | 0.0493 | 0.0495 | 0.0001 |
| 3-2 | 0.0343 | 0.0317 | 0.0026 |
| 4-0 | 0.0282 | 0.0334 | 0.0052 |
| 4-1 | 0.0282 | 0.0309 | 0.0027 |
| 0-2 | 0.0255 | 0.0263 | 0.0009 |
| 4-2 | 0.0172 | 0.0148 | 0.0024 |
| **Sum (top 15)** | **0.8787** | **0.9133** | — |
- High-score mass (total ≥9 goals): 2.27e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Norway vs England
- CS outcomes: 29  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-1 | 0.1128 | 0.1171 | 0.0043 |
| 1-2 | 0.0987 | 0.1001 | 0.0014 |
| 0-1 | 0.0929 | 0.0913 | 0.0016 |
| 0-2 | 0.0752 | 0.0875 | 0.0123 |
| 2-2 | 0.0658 | 0.0599 | 0.0059 |
| 2-1 | 0.0607 | 0.0611 | 0.0004 |
| 1-0 | 0.0564 | 0.0579 | 0.0015 |
| 1-3 | 0.0564 | 0.0598 | 0.0034 |
| 0-0 | 0.0526 | 0.0676 | 0.0150 |
| 0-3 | 0.0439 | 0.0535 | 0.0097 |
| 2-3 | 0.0376 | 0.0347 | 0.0029 |
| 2-0 | 0.0304 | 0.0344 | 0.0040 |
| 3-1 | 0.0255 | 0.0229 | 0.0026 |
| 3-2 | 0.0255 | 0.0206 | 0.0048 |
| 1-4 | 0.0255 | 0.0271 | 0.0016 |
| **Sum (top 15)** | **0.8597** | **0.8956** | — |
- High-score mass (total ≥9 goals): 2.44e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Argentina vs Switzerland
- CS outcomes: 25  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-0 | 0.1444 | 0.1385 | 0.0059 |
| 1-1 | 0.1244 | 0.1243 | 0.0001 |
| 2-0 | 0.1078 | 0.1173 | 0.0095 |
| 2-1 | 0.0951 | 0.0942 | 0.0009 |
| 0-0 | 0.0851 | 0.1008 | 0.0157 |
| 0-1 | 0.0622 | 0.0666 | 0.0044 |
| 3-0 | 0.0577 | 0.0650 | 0.0072 |
| 3-1 | 0.0476 | 0.0505 | 0.0030 |
| 1-2 | 0.0449 | 0.0437 | 0.0012 |
| 2-2 | 0.0425 | 0.0386 | 0.0040 |
| 3-2 | 0.0261 | 0.0206 | 0.0055 |
| 4-0 | 0.0261 | 0.0277 | 0.0016 |
| 0-2 | 0.0261 | 0.0273 | 0.0012 |
| 4-1 | 0.0225 | 0.0212 | 0.0013 |
| 2-3 | 0.0133 | 0.0090 | 0.0042 |
| **Sum (top 15)** | **0.9256** | **0.9452** | — |
- High-score mass (total ≥9 goals): 1.40e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS
