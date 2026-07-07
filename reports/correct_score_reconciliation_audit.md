# Correct-Score Reconciliation Audit

**Generated**: 2026-07-07T03:02:44Z

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
| Total 2026 matches predicted | 5 |
| Matches with any CS data | 5 |
| Matches with 1 CS vendor | 5 |
| Matches with 2+ CS vendors | 0 |

## Per-match correct-score audit

### Argentina vs Egypt
- CS outcomes: 26  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-0 | 0.1466 | 0.1476 | 0.0010 |
| 2-0 | 0.1414 | 0.1479 | 0.0065 |
| 3-0 | 0.0949 | 0.1001 | 0.0052 |
| 2-1 | 0.0896 | 0.0913 | 0.0017 |
| 1-1 | 0.0849 | 0.0890 | 0.0041 |
| 0-0 | 0.0733 | 0.0792 | 0.0059 |
| 3-1 | 0.0620 | 0.0623 | 0.0003 |
| 4-0 | 0.0474 | 0.0514 | 0.0039 |
| 0-1 | 0.0424 | 0.0452 | 0.0028 |
| 4-1 | 0.0288 | 0.0309 | 0.0021 |
| 2-2 | 0.0288 | 0.0272 | 0.0016 |
| 1-2 | 0.0260 | 0.0262 | 0.0002 |
| 3-2 | 0.0224 | 0.0192 | 0.0032 |
| 5-0 | 0.0224 | 0.0213 | 0.0010 |
| 5-1 | 0.0144 | 0.0126 | 0.0018 |
| **Sum (top 15)** | **0.9253** | **0.9512** | — |
- High-score mass (total ≥9 goals): 1.69e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Switzerland vs Colombia
- CS outcomes: 26  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-1 | 0.1410 | 0.1419 | 0.0009 |
| 0-1 | 0.1236 | 0.1195 | 0.0041 |
| 0-0 | 0.0893 | 0.1086 | 0.0194 |
| 1-2 | 0.0893 | 0.0868 | 0.0025 |
| 1-0 | 0.0846 | 0.0887 | 0.0041 |
| 0-2 | 0.0731 | 0.0838 | 0.0108 |
| 2-1 | 0.0670 | 0.0648 | 0.0022 |
| 2-2 | 0.0574 | 0.0487 | 0.0087 |
| 2-0 | 0.0402 | 0.0477 | 0.0075 |
| 1-3 | 0.0383 | 0.0385 | 0.0002 |
| 0-3 | 0.0309 | 0.0375 | 0.0066 |
| 2-3 | 0.0259 | 0.0201 | 0.0058 |
| 3-1 | 0.0223 | 0.0213 | 0.0010 |
| 3-2 | 0.0196 | 0.0146 | 0.0050 |
| 3-0 | 0.0143 | 0.0158 | 0.0014 |
| **Sum (top 15)** | **0.9167** | **0.9383** | — |
- High-score mass (total ≥9 goals): 1.36e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### France vs Morocco
- CS outcomes: 27  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-0 | 0.1341 | 0.1272 | 0.0069 |
| 2-0 | 0.1073 | 0.1175 | 0.0102 |
| 1-1 | 0.1073 | 0.1112 | 0.0039 |
| 2-1 | 0.1006 | 0.0992 | 0.0014 |
| 0-0 | 0.0731 | 0.0838 | 0.0107 |
| 3-0 | 0.0670 | 0.0741 | 0.0070 |
| 3-1 | 0.0536 | 0.0587 | 0.0050 |
| 0-1 | 0.0536 | 0.0565 | 0.0028 |
| 2-2 | 0.0447 | 0.0414 | 0.0033 |
| 1-2 | 0.0402 | 0.0418 | 0.0015 |
| 4-0 | 0.0309 | 0.0347 | 0.0038 |
| 3-2 | 0.0287 | 0.0249 | 0.0039 |
| 4-1 | 0.0287 | 0.0279 | 0.0009 |
| 0-2 | 0.0237 | 0.0237 | 0.0000 |
| 5-0 | 0.0132 | 0.0129 | 0.0003 |
| **Sum (top 15)** | **0.9069** | **0.9354** | — |
- High-score mass (total ≥9 goals): 1.75e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Spain vs Belgium
- CS outcomes: 28  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-0 | 0.1053 | 0.1045 | 0.0007 |
| 1-1 | 0.1053 | 0.1102 | 0.0050 |
| 2-0 | 0.0987 | 0.1065 | 0.0078 |
| 2-1 | 0.0929 | 0.0990 | 0.0061 |
| 3-0 | 0.0607 | 0.0691 | 0.0084 |
| 3-1 | 0.0607 | 0.0643 | 0.0036 |
| 0-0 | 0.0607 | 0.0715 | 0.0108 |
| 0-1 | 0.0526 | 0.0535 | 0.0009 |
| 2-2 | 0.0464 | 0.0488 | 0.0023 |
| 1-2 | 0.0464 | 0.0485 | 0.0020 |
| 3-2 | 0.0343 | 0.0314 | 0.0029 |
| 4-0 | 0.0304 | 0.0339 | 0.0035 |
| 4-1 | 0.0304 | 0.0312 | 0.0008 |
| 0-2 | 0.0282 | 0.0266 | 0.0016 |
| 1-3 | 0.0193 | 0.0154 | 0.0038 |
| **Sum (top 15)** | **0.8723** | **0.9145** | — |
- High-score mass (total ≥9 goals): 2.22e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Norway vs England
- CS outcomes: 28  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-1 | 0.1119 | 0.1164 | 0.0045 |
| 0-1 | 0.0979 | 0.0885 | 0.0094 |
| 1-2 | 0.0979 | 0.0991 | 0.0012 |
| 0-2 | 0.0824 | 0.0858 | 0.0033 |
| 1-0 | 0.0602 | 0.0582 | 0.0020 |
| 2-1 | 0.0602 | 0.0632 | 0.0029 |
| 0-0 | 0.0602 | 0.0694 | 0.0091 |
| 2-2 | 0.0602 | 0.0608 | 0.0005 |
| 1-3 | 0.0522 | 0.0579 | 0.0057 |
| 0-3 | 0.0461 | 0.0524 | 0.0063 |
| 2-0 | 0.0341 | 0.0355 | 0.0014 |
| 2-3 | 0.0341 | 0.0343 | 0.0002 |
| 1-4 | 0.0253 | 0.0264 | 0.0012 |
| 3-1 | 0.0230 | 0.0243 | 0.0013 |
| 0-4 | 0.0230 | 0.0241 | 0.0011 |
| **Sum (top 15)** | **0.8689** | **0.8963** | — |
- High-score mass (total ≥9 goals): 2.50e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS
