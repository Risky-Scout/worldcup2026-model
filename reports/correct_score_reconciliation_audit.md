# Correct-Score Reconciliation Audit

**Generated**: 2026-07-07T18:03:11Z

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
| Total 2026 matches predicted | 4 |
| Matches with any CS data | 4 |
| Matches with 1 CS vendor | 4 |
| Matches with 2+ CS vendors | 0 |

## Per-match correct-score audit

### Switzerland vs Colombia
- CS outcomes: 26  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-1 | 0.1404 | 0.1429 | 0.0025 |
| 0-1 | 0.1231 | 0.1152 | 0.0078 |
| 1-0 | 0.0889 | 0.0872 | 0.0017 |
| 0-0 | 0.0889 | 0.1088 | 0.0199 |
| 1-2 | 0.0889 | 0.0872 | 0.0017 |
| 0-2 | 0.0727 | 0.0823 | 0.0095 |
| 2-1 | 0.0667 | 0.0650 | 0.0016 |
| 2-2 | 0.0571 | 0.0505 | 0.0067 |
| 2-0 | 0.0421 | 0.0474 | 0.0053 |
| 1-3 | 0.0381 | 0.0390 | 0.0009 |
| 0-3 | 0.0286 | 0.0371 | 0.0085 |
| 2-3 | 0.0258 | 0.0207 | 0.0051 |
| 3-1 | 0.0222 | 0.0217 | 0.0006 |
| 3-2 | 0.0195 | 0.0151 | 0.0044 |
| 3-0 | 0.0174 | 0.0164 | 0.0010 |
| **Sum (top 15)** | **0.9204** | **0.9364** | — |
- High-score mass (total ≥9 goals): 1.42e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### France vs Morocco
- CS outcomes: 27  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-0 | 0.1240 | 0.1230 | 0.0009 |
| 2-0 | 0.1074 | 0.1193 | 0.0119 |
| 1-1 | 0.1074 | 0.1109 | 0.0034 |
| 2-1 | 0.1007 | 0.0997 | 0.0010 |
| 3-0 | 0.0671 | 0.0755 | 0.0084 |
| 0-0 | 0.0671 | 0.0806 | 0.0134 |
| 3-1 | 0.0576 | 0.0609 | 0.0033 |
| 0-1 | 0.0504 | 0.0543 | 0.0039 |
| 2-2 | 0.0448 | 0.0411 | 0.0037 |
| 1-2 | 0.0448 | 0.0417 | 0.0031 |
| 4-0 | 0.0350 | 0.0369 | 0.0019 |
| 3-2 | 0.0288 | 0.0254 | 0.0034 |
| 4-1 | 0.0288 | 0.0289 | 0.0002 |
| 0-2 | 0.0237 | 0.0230 | 0.0007 |
| 4-2 | 0.0132 | 0.0114 | 0.0018 |
| **Sum (top 15)** | **0.9008** | **0.9326** | — |
- High-score mass (total ≥9 goals): 1.79e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Spain vs Belgium
- CS outcomes: 28  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-0 | 0.1134 | 0.1062 | 0.0072 |
| 2-1 | 0.1058 | 0.1033 | 0.0026 |
| 1-1 | 0.1058 | 0.1113 | 0.0055 |
| 2-0 | 0.0992 | 0.1077 | 0.0084 |
| 3-1 | 0.0611 | 0.0641 | 0.0030 |
| 3-0 | 0.0567 | 0.0684 | 0.0117 |
| 0-0 | 0.0567 | 0.0718 | 0.0151 |
| 2-2 | 0.0529 | 0.0496 | 0.0033 |
| 0-1 | 0.0496 | 0.0520 | 0.0024 |
| 1-2 | 0.0467 | 0.0476 | 0.0009 |
| 3-2 | 0.0345 | 0.0306 | 0.0039 |
| 4-0 | 0.0305 | 0.0344 | 0.0039 |
| 4-1 | 0.0284 | 0.0307 | 0.0023 |
| 0-2 | 0.0221 | 0.0249 | 0.0029 |
| 2-3 | 0.0173 | 0.0138 | 0.0035 |
| **Sum (top 15)** | **0.8808** | **0.9164** | — |
- High-score mass (total ≥9 goals): 2.20e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Norway vs England
- CS outcomes: 28  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-1 | 0.1131 | 0.1166 | 0.0036 |
| 1-2 | 0.0989 | 0.0997 | 0.0008 |
| 0-1 | 0.0931 | 0.0926 | 0.0005 |
| 0-2 | 0.0754 | 0.0871 | 0.0118 |
| 2-2 | 0.0660 | 0.0601 | 0.0059 |
| 2-1 | 0.0609 | 0.0620 | 0.0011 |
| 1-0 | 0.0565 | 0.0599 | 0.0033 |
| 0-0 | 0.0528 | 0.0670 | 0.0143 |
| 1-3 | 0.0528 | 0.0580 | 0.0052 |
| 0-3 | 0.0466 | 0.0533 | 0.0068 |
| 2-3 | 0.0377 | 0.0343 | 0.0033 |
| 2-0 | 0.0304 | 0.0354 | 0.0050 |
| 3-2 | 0.0255 | 0.0211 | 0.0044 |
| 1-4 | 0.0255 | 0.0265 | 0.0010 |
| 3-1 | 0.0233 | 0.0231 | 0.0002 |
| **Sum (top 15)** | **0.8585** | **0.8969** | — |
- High-score mass (total ≥9 goals): 2.44e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS
