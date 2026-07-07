# Correct-Score Reconciliation Audit

**Generated**: 2026-07-07T19:15:03Z

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
| 1-1 | 0.1405 | 0.1445 | 0.0040 |
| 0-1 | 0.1232 | 0.1115 | 0.0117 |
| 1-0 | 0.0890 | 0.0863 | 0.0026 |
| 0-0 | 0.0890 | 0.1097 | 0.0207 |
| 1-2 | 0.0890 | 0.0866 | 0.0023 |
| 2-1 | 0.0667 | 0.0665 | 0.0002 |
| 0-2 | 0.0667 | 0.0781 | 0.0114 |
| 2-2 | 0.0616 | 0.0528 | 0.0088 |
| 2-0 | 0.0421 | 0.0487 | 0.0065 |
| 1-3 | 0.0381 | 0.0385 | 0.0003 |
| 0-3 | 0.0286 | 0.0358 | 0.0072 |
| 2-3 | 0.0258 | 0.0209 | 0.0049 |
| 3-1 | 0.0222 | 0.0229 | 0.0006 |
| 3-2 | 0.0222 | 0.0161 | 0.0061 |
| 3-0 | 0.0157 | 0.0171 | 0.0014 |
| **Sum (top 15)** | **0.9205** | **0.9361** | — |
- High-score mass (total ≥9 goals): 1.45e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### France vs Morocco
- CS outcomes: 27  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-0 | 0.1240 | 0.1228 | 0.0012 |
| 2-0 | 0.1074 | 0.1192 | 0.0118 |
| 1-1 | 0.1074 | 0.1111 | 0.0036 |
| 2-1 | 0.1007 | 0.0997 | 0.0010 |
| 3-0 | 0.0671 | 0.0755 | 0.0084 |
| 0-0 | 0.0671 | 0.0808 | 0.0136 |
| 3-1 | 0.0576 | 0.0608 | 0.0033 |
| 0-1 | 0.0504 | 0.0542 | 0.0039 |
| 2-2 | 0.0448 | 0.0411 | 0.0036 |
| 1-2 | 0.0448 | 0.0417 | 0.0031 |
| 4-0 | 0.0350 | 0.0369 | 0.0019 |
| 3-2 | 0.0288 | 0.0253 | 0.0034 |
| 4-1 | 0.0288 | 0.0289 | 0.0001 |
| 0-2 | 0.0237 | 0.0230 | 0.0007 |
| 4-2 | 0.0132 | 0.0114 | 0.0018 |
| **Sum (top 15)** | **0.9008** | **0.9327** | — |
- High-score mass (total ≥9 goals): 1.79e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Spain vs Belgium
- CS outcomes: 28  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-0 | 0.1134 | 0.1072 | 0.0062 |
| 2-1 | 0.1058 | 0.1032 | 0.0026 |
| 1-1 | 0.1058 | 0.1110 | 0.0052 |
| 2-0 | 0.0992 | 0.1079 | 0.0087 |
| 3-1 | 0.0611 | 0.0640 | 0.0029 |
| 3-0 | 0.0567 | 0.0684 | 0.0117 |
| 0-0 | 0.0567 | 0.0715 | 0.0148 |
| 2-2 | 0.0529 | 0.0494 | 0.0036 |
| 0-1 | 0.0496 | 0.0524 | 0.0028 |
| 1-2 | 0.0467 | 0.0475 | 0.0008 |
| 3-2 | 0.0345 | 0.0305 | 0.0040 |
| 4-0 | 0.0305 | 0.0344 | 0.0038 |
| 4-1 | 0.0284 | 0.0306 | 0.0022 |
| 0-2 | 0.0221 | 0.0250 | 0.0030 |
| 2-3 | 0.0173 | 0.0137 | 0.0036 |
| **Sum (top 15)** | **0.8808** | **0.9167** | — |
- High-score mass (total ≥9 goals): 2.19e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Norway vs England
- CS outcomes: 28  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-1 | 0.1131 | 0.1169 | 0.0038 |
| 1-2 | 0.0989 | 0.0996 | 0.0006 |
| 0-1 | 0.0931 | 0.0928 | 0.0003 |
| 0-2 | 0.0754 | 0.0869 | 0.0115 |
| 2-2 | 0.0660 | 0.0598 | 0.0062 |
| 2-1 | 0.0609 | 0.0621 | 0.0012 |
| 1-0 | 0.0565 | 0.0597 | 0.0032 |
| 0-0 | 0.0528 | 0.0670 | 0.0143 |
| 1-3 | 0.0528 | 0.0579 | 0.0051 |
| 0-3 | 0.0466 | 0.0531 | 0.0066 |
| 2-3 | 0.0377 | 0.0343 | 0.0034 |
| 2-0 | 0.0304 | 0.0355 | 0.0050 |
| 3-2 | 0.0255 | 0.0210 | 0.0045 |
| 1-4 | 0.0255 | 0.0263 | 0.0008 |
| 3-1 | 0.0233 | 0.0232 | 0.0001 |
| **Sum (top 15)** | **0.8585** | **0.8961** | — |
- High-score mass (total ≥9 goals): 2.42e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS
