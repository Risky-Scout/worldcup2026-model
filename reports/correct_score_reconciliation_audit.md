# Correct-Score Reconciliation Audit

**Generated**: 2026-07-11T23:25:59Z

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
- CS outcomes: 23  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-0 | 0.1477 | 0.1430 | 0.0047 |
| 1-1 | 0.1250 | 0.1245 | 0.0005 |
| 2-0 | 0.1083 | 0.1182 | 0.0099 |
| 2-1 | 0.0956 | 0.0929 | 0.0026 |
| 0-0 | 0.0956 | 0.1077 | 0.0121 |
| 0-1 | 0.0625 | 0.0690 | 0.0065 |
| 3-0 | 0.0580 | 0.0638 | 0.0058 |
| 3-1 | 0.0478 | 0.0487 | 0.0009 |
| 2-2 | 0.0451 | 0.0372 | 0.0079 |
| 1-2 | 0.0428 | 0.0427 | 0.0000 |
| 0-2 | 0.0262 | 0.0279 | 0.0017 |
| 3-2 | 0.0239 | 0.0190 | 0.0049 |
| 4-0 | 0.0239 | 0.0260 | 0.0022 |
| 4-1 | 0.0226 | 0.0198 | 0.0028 |
| 2-3 | 0.0123 | 0.0085 | 0.0038 |
| **Sum (top 15)** | **0.9372** | **0.9490** | — |
- High-score mass (total ≥9 goals): 1.31e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### France vs Spain
- CS outcomes: 29  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-1 | 0.1330 | 0.1358 | 0.0028 |
| 1-0 | 0.0939 | 0.0905 | 0.0034 |
| 2-1 | 0.0939 | 0.0915 | 0.0024 |
| 0-1 | 0.0725 | 0.0744 | 0.0019 |
| 1-2 | 0.0725 | 0.0735 | 0.0010 |
| 2-2 | 0.0665 | 0.0608 | 0.0057 |
| 2-0 | 0.0614 | 0.0725 | 0.0112 |
| 0-0 | 0.0614 | 0.0832 | 0.0218 |
| 0-2 | 0.0420 | 0.0497 | 0.0077 |
| 3-1 | 0.0399 | 0.0436 | 0.0037 |
| 3-2 | 0.0347 | 0.0283 | 0.0064 |
| 3-0 | 0.0285 | 0.0361 | 0.0076 |
| 1-3 | 0.0285 | 0.0296 | 0.0011 |
| 2-3 | 0.0285 | 0.0228 | 0.0057 |
| 3-3 | 0.0173 | 0.0119 | 0.0055 |
| **Sum (top 15)** | **0.8745** | **0.9043** | — |
- High-score mass (total ≥9 goals): 2.13e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS
