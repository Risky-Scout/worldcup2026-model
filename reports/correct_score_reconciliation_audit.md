# Correct-Score Reconciliation Audit

**Generated**: 2026-07-07T22:28:28Z

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

### France vs Morocco
- CS outcomes: 27  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-0 | 0.1331 | 0.1254 | 0.0076 |
| 2-0 | 0.1064 | 0.1169 | 0.0104 |
| 1-1 | 0.1064 | 0.1105 | 0.0040 |
| 2-1 | 0.0998 | 0.0991 | 0.0007 |
| 0-0 | 0.0726 | 0.0827 | 0.0102 |
| 3-0 | 0.0665 | 0.0743 | 0.0077 |
| 3-1 | 0.0570 | 0.0602 | 0.0032 |
| 0-1 | 0.0499 | 0.0548 | 0.0049 |
| 2-2 | 0.0444 | 0.0415 | 0.0028 |
| 1-2 | 0.0399 | 0.0419 | 0.0019 |
| 4-0 | 0.0347 | 0.0361 | 0.0014 |
| 3-2 | 0.0285 | 0.0253 | 0.0032 |
| 4-1 | 0.0285 | 0.0284 | 0.0001 |
| 0-2 | 0.0222 | 0.0233 | 0.0012 |
| 5-0 | 0.0143 | 0.0134 | 0.0009 |
| **Sum (top 15)** | **0.9042** | **0.9338** | — |
- High-score mass (total ≥9 goals): 1.79e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Spain vs Belgium
- CS outcomes: 27  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-0 | 0.1139 | 0.1089 | 0.0049 |
| 2-1 | 0.1063 | 0.1019 | 0.0044 |
| 1-1 | 0.1063 | 0.1097 | 0.0035 |
| 2-0 | 0.0996 | 0.1086 | 0.0089 |
| 3-0 | 0.0613 | 0.0719 | 0.0106 |
| 3-1 | 0.0613 | 0.0631 | 0.0018 |
| 0-0 | 0.0613 | 0.0748 | 0.0135 |
| 2-2 | 0.0498 | 0.0481 | 0.0017 |
| 0-1 | 0.0498 | 0.0521 | 0.0023 |
| 1-2 | 0.0443 | 0.0461 | 0.0018 |
| 3-2 | 0.0347 | 0.0288 | 0.0058 |
| 4-0 | 0.0307 | 0.0347 | 0.0041 |
| 4-1 | 0.0285 | 0.0299 | 0.0014 |
| 0-2 | 0.0221 | 0.0259 | 0.0038 |
| 2-3 | 0.0173 | 0.0140 | 0.0033 |
| **Sum (top 15)** | **0.8870** | **0.9186** | — |
- High-score mass (total ≥9 goals): 2.17e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Norway vs England
- CS outcomes: 28  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-1 | 0.1131 | 0.1162 | 0.0031 |
| 1-2 | 0.0989 | 0.1000 | 0.0011 |
| 0-1 | 0.0931 | 0.0912 | 0.0019 |
| 0-2 | 0.0754 | 0.0866 | 0.0112 |
| 2-2 | 0.0660 | 0.0602 | 0.0058 |
| 2-1 | 0.0609 | 0.0618 | 0.0009 |
| 1-0 | 0.0565 | 0.0582 | 0.0017 |
| 0-0 | 0.0528 | 0.0662 | 0.0134 |
| 1-3 | 0.0528 | 0.0587 | 0.0059 |
| 0-3 | 0.0466 | 0.0538 | 0.0072 |
| 2-3 | 0.0377 | 0.0350 | 0.0027 |
| 2-0 | 0.0304 | 0.0347 | 0.0042 |
| 3-2 | 0.0255 | 0.0211 | 0.0044 |
| 1-4 | 0.0255 | 0.0271 | 0.0015 |
| 3-1 | 0.0233 | 0.0231 | 0.0001 |
| **Sum (top 15)** | **0.8585** | **0.8940** | — |
- High-score mass (total ≥9 goals): 2.48e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS
