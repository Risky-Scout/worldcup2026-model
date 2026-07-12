# Correct-Score Reconciliation Audit

**Generated**: 2026-07-12T00:02:03Z

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
| Matches with any CS data | 2 |
| Matches with 1 CS vendor | 2 |
| Matches with 2+ CS vendors | 0 |

## Per-match correct-score audit

### Argentina vs Switzerland
- CS outcomes: 22  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-0 | 0.1481 | 0.1419 | 0.0062 |
| 1-1 | 0.1253 | 0.1245 | 0.0008 |
| 2-0 | 0.1086 | 0.1181 | 0.0095 |
| 2-1 | 0.0958 | 0.0934 | 0.0024 |
| 0-0 | 0.0958 | 0.1077 | 0.0118 |
| 0-1 | 0.0679 | 0.0693 | 0.0014 |
| 3-0 | 0.0582 | 0.0645 | 0.0063 |
| 3-1 | 0.0479 | 0.0492 | 0.0012 |
| 2-2 | 0.0453 | 0.0375 | 0.0078 |
| 1-2 | 0.0429 | 0.0422 | 0.0006 |
| 0-2 | 0.0263 | 0.0271 | 0.0009 |
| 3-2 | 0.0240 | 0.0191 | 0.0048 |
| 4-0 | 0.0240 | 0.0265 | 0.0025 |
| 4-1 | 0.0199 | 0.0198 | 0.0001 |
| 2-3 | 0.0115 | 0.0083 | 0.0032 |
| **Sum (top 15)** | **0.9414** | **0.9490** | — |
- High-score mass (total ≥9 goals): 1.32e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### France vs Spain
- CS outcomes: 29  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-1 | 0.1330 | 0.1355 | 0.0026 |
| 1-0 | 0.0939 | 0.0908 | 0.0031 |
| 2-1 | 0.0939 | 0.0916 | 0.0023 |
| 0-1 | 0.0725 | 0.0745 | 0.0019 |
| 1-2 | 0.0725 | 0.0734 | 0.0009 |
| 2-2 | 0.0665 | 0.0607 | 0.0058 |
| 2-0 | 0.0614 | 0.0727 | 0.0113 |
| 0-0 | 0.0614 | 0.0830 | 0.0216 |
| 0-2 | 0.0420 | 0.0496 | 0.0076 |
| 3-1 | 0.0399 | 0.0437 | 0.0038 |
| 3-2 | 0.0347 | 0.0284 | 0.0063 |
| 3-0 | 0.0285 | 0.0362 | 0.0077 |
| 1-3 | 0.0285 | 0.0295 | 0.0010 |
| 2-3 | 0.0285 | 0.0228 | 0.0057 |
| 3-3 | 0.0173 | 0.0118 | 0.0055 |
| **Sum (top 15)** | **0.8745** | **0.9043** | — |
- High-score mass (total ≥9 goals): 2.13e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS
