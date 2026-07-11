# Correct-Score Reconciliation Audit

**Generated**: 2026-07-11T09:17:42Z

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

### Norway vs England
- CS outcomes: 30  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-1 | 0.1113 | 0.1165 | 0.0052 |
| 1-2 | 0.0974 | 0.0985 | 0.0012 |
| 0-1 | 0.0866 | 0.0854 | 0.0011 |
| 0-2 | 0.0742 | 0.0817 | 0.0075 |
| 2-1 | 0.0649 | 0.0664 | 0.0015 |
| 2-2 | 0.0599 | 0.0614 | 0.0015 |
| 1-0 | 0.0556 | 0.0588 | 0.0031 |
| 1-3 | 0.0556 | 0.0581 | 0.0025 |
| 0-0 | 0.0519 | 0.0651 | 0.0132 |
| 0-3 | 0.0433 | 0.0495 | 0.0062 |
| 2-3 | 0.0371 | 0.0356 | 0.0015 |
| 2-0 | 0.0339 | 0.0379 | 0.0040 |
| 3-1 | 0.0251 | 0.0264 | 0.0013 |
| 3-2 | 0.0251 | 0.0234 | 0.0017 |
| 1-4 | 0.0251 | 0.0258 | 0.0007 |
| **Sum (top 15)** | **0.8470** | **0.8906** | — |
- High-score mass (total ≥9 goals): 2.62e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Argentina vs Switzerland
- CS outcomes: 23  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-0 | 0.1445 | 0.1388 | 0.0058 |
| 2-0 | 0.1156 | 0.1207 | 0.0050 |
| 1-1 | 0.1156 | 0.1205 | 0.0049 |
| 2-1 | 0.0952 | 0.0935 | 0.0017 |
| 0-0 | 0.0899 | 0.1035 | 0.0136 |
| 3-0 | 0.0623 | 0.0664 | 0.0041 |
| 0-1 | 0.0623 | 0.0665 | 0.0043 |
| 3-1 | 0.0506 | 0.0508 | 0.0002 |
| 2-2 | 0.0450 | 0.0388 | 0.0062 |
| 1-2 | 0.0450 | 0.0431 | 0.0019 |
| 4-0 | 0.0261 | 0.0276 | 0.0015 |
| 0-2 | 0.0261 | 0.0269 | 0.0008 |
| 3-2 | 0.0238 | 0.0198 | 0.0040 |
| 4-1 | 0.0225 | 0.0209 | 0.0015 |
| 1-3 | 0.0114 | 0.0105 | 0.0009 |
| **Sum (top 15)** | **0.9359** | **0.9484** | — |
- High-score mass (total ≥9 goals): 1.38e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### France vs Spain
- CS outcomes: 29  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-1 | 0.1325 | 0.1349 | 0.0024 |
| 1-0 | 0.0935 | 0.0904 | 0.0031 |
| 2-1 | 0.0935 | 0.0911 | 0.0024 |
| 0-1 | 0.0757 | 0.0760 | 0.0002 |
| 1-2 | 0.0723 | 0.0738 | 0.0015 |
| 0-0 | 0.0663 | 0.0846 | 0.0184 |
| 2-2 | 0.0663 | 0.0605 | 0.0058 |
| 2-0 | 0.0612 | 0.0718 | 0.0106 |
| 0-2 | 0.0442 | 0.0507 | 0.0065 |
| 3-1 | 0.0398 | 0.0432 | 0.0034 |
| 3-2 | 0.0306 | 0.0274 | 0.0032 |
| 3-0 | 0.0284 | 0.0356 | 0.0072 |
| 1-3 | 0.0284 | 0.0299 | 0.0015 |
| 2-3 | 0.0256 | 0.0225 | 0.0032 |
| 0-3 | 0.0194 | 0.0209 | 0.0015 |
| **Sum (top 15)** | **0.8776** | **0.9133** | — |
- High-score mass (total ≥9 goals): 2.11e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS
