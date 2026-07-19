# Correct-Score Reconciliation Audit

**Generated**: 2026-07-19T17:03:18Z

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
| 1-1 | 0.1322 | 0.1454 | 0.0132 |
| 1-0 | 0.1057 | 0.1115 | 0.0058 |
| 2-1 | 0.0822 | 0.0861 | 0.0039 |
| 0-0 | 0.0822 | 0.1129 | 0.0307 |
| 0-1 | 0.0822 | 0.0873 | 0.0051 |
| 2-0 | 0.0617 | 0.0820 | 0.0203 |
| 1-2 | 0.0617 | 0.0639 | 0.0022 |
| 2-2 | 0.0529 | 0.0503 | 0.0026 |
| 0-2 | 0.0370 | 0.0483 | 0.0113 |
| 3-1 | 0.0322 | 0.0382 | 0.0060 |
| 3-0 | 0.0264 | 0.0373 | 0.0108 |
| 3-2 | 0.0239 | 0.0207 | 0.0032 |
| 1-3 | 0.0206 | 0.0215 | 0.0009 |
| 2-3 | 0.0206 | 0.0151 | 0.0055 |
| 0-3 | 0.0132 | 0.0161 | 0.0028 |
| **Sum (top 15)** | **0.8347** | **0.9364** | — |
- High-score mass (total ≥9 goals): 1.38e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS
