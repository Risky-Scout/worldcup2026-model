# Correct-Score Reconciliation Audit

**Generated**: 2026-07-09T16:39:42Z

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

### France vs Morocco
- CS outcomes: 26  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-0 | 0.1332 | 0.1274 | 0.0058 |
| 1-1 | 0.1142 | 0.1138 | 0.0003 |
| 2-0 | 0.1066 | 0.1182 | 0.0117 |
| 2-1 | 0.1066 | 0.1014 | 0.0051 |
| 0-0 | 0.0727 | 0.0842 | 0.0115 |
| 3-0 | 0.0615 | 0.0726 | 0.0111 |
| 3-1 | 0.0571 | 0.0595 | 0.0024 |
| 0-1 | 0.0533 | 0.0562 | 0.0030 |
| 2-2 | 0.0444 | 0.0403 | 0.0041 |
| 1-2 | 0.0421 | 0.0415 | 0.0006 |
| 3-2 | 0.0285 | 0.0244 | 0.0041 |
| 4-0 | 0.0285 | 0.0344 | 0.0058 |
| 4-1 | 0.0258 | 0.0272 | 0.0014 |
| 0-2 | 0.0222 | 0.0232 | 0.0010 |
| 4-2 | 0.0143 | 0.0109 | 0.0034 |
| **Sum (top 15)** | **0.9108** | **0.9352** | — |
- High-score mass (total ≥9 goals): 1.71e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Spain vs Belgium
- CS outcomes: 28  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-0 | 0.1139 | 0.1040 | 0.0099 |
| 2-1 | 0.1063 | 0.1035 | 0.0028 |
| 1-1 | 0.1063 | 0.1114 | 0.0051 |
| 2-0 | 0.0938 | 0.1035 | 0.0097 |
| 3-1 | 0.0613 | 0.0642 | 0.0029 |
| 3-0 | 0.0569 | 0.0671 | 0.0101 |
| 0-0 | 0.0569 | 0.0706 | 0.0136 |
| 2-2 | 0.0569 | 0.0518 | 0.0052 |
| 0-1 | 0.0469 | 0.0514 | 0.0045 |
| 1-2 | 0.0469 | 0.0492 | 0.0023 |
| 3-2 | 0.0347 | 0.0315 | 0.0031 |
| 4-0 | 0.0285 | 0.0332 | 0.0047 |
| 4-1 | 0.0285 | 0.0308 | 0.0023 |
| 0-2 | 0.0234 | 0.0261 | 0.0026 |
| 2-3 | 0.0194 | 0.0150 | 0.0044 |
| **Sum (top 15)** | **0.8806** | **0.9132** | — |
- High-score mass (total ≥9 goals): 2.26e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Norway vs England
- CS outcomes: 31  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-1 | 0.1115 | 0.1167 | 0.0052 |
| 1-2 | 0.0976 | 0.0997 | 0.0021 |
| 0-1 | 0.0918 | 0.0921 | 0.0002 |
| 0-2 | 0.0781 | 0.0890 | 0.0109 |
| 2-2 | 0.0651 | 0.0595 | 0.0055 |
| 2-1 | 0.0601 | 0.0610 | 0.0009 |
| 1-0 | 0.0558 | 0.0584 | 0.0027 |
| 0-0 | 0.0520 | 0.0676 | 0.0156 |
| 1-3 | 0.0520 | 0.0585 | 0.0064 |
| 0-3 | 0.0459 | 0.0543 | 0.0083 |
| 2-3 | 0.0372 | 0.0344 | 0.0027 |
| 2-0 | 0.0300 | 0.0345 | 0.0045 |
| 3-2 | 0.0252 | 0.0205 | 0.0047 |
| 1-4 | 0.0252 | 0.0270 | 0.0018 |
| 3-1 | 0.0230 | 0.0225 | 0.0005 |
| **Sum (top 15)** | **0.8505** | **0.8957** | — |
- High-score mass (total ≥9 goals): 2.42e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Argentina vs Switzerland
- CS outcomes: 25  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-0 | 0.1428 | 0.1386 | 0.0043 |
| 1-1 | 0.1163 | 0.1215 | 0.0052 |
| 2-0 | 0.1086 | 0.1176 | 0.0091 |
| 2-1 | 0.1018 | 0.0961 | 0.0056 |
| 0-0 | 0.0857 | 0.1015 | 0.0158 |
| 0-1 | 0.0626 | 0.0674 | 0.0048 |
| 3-0 | 0.0582 | 0.0644 | 0.0062 |
| 3-1 | 0.0479 | 0.0502 | 0.0023 |
| 2-2 | 0.0452 | 0.0393 | 0.0059 |
| 1-2 | 0.0452 | 0.0438 | 0.0015 |
| 3-2 | 0.0263 | 0.0205 | 0.0058 |
| 0-2 | 0.0263 | 0.0277 | 0.0015 |
| 4-0 | 0.0239 | 0.0269 | 0.0029 |
| 4-1 | 0.0226 | 0.0210 | 0.0017 |
| 2-3 | 0.0133 | 0.0091 | 0.0043 |
| **Sum (top 15)** | **0.9268** | **0.9455** | — |
- High-score mass (total ≥9 goals): 1.39e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS
