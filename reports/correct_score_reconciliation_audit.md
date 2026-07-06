# Correct-Score Reconciliation Audit

**Generated**: 2026-07-06T04:16:45Z

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
| Total 2026 matches predicted | 6 |
| Matches with any CS data | 6 |
| Matches with 1 CS vendor | 6 |
| Matches with 2+ CS vendors | 0 |

## Per-match correct-score audit

### Portugal vs Spain
- CS outcomes: 29  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-1 | 0.1124 | 0.1185 | 0.0062 |
| 0-1 | 0.0983 | 0.0944 | 0.0039 |
| 1-2 | 0.0983 | 0.0987 | 0.0004 |
| 0-2 | 0.0749 | 0.0856 | 0.0107 |
| 2-2 | 0.0656 | 0.0601 | 0.0054 |
| 1-0 | 0.0605 | 0.0619 | 0.0014 |
| 2-1 | 0.0605 | 0.0627 | 0.0022 |
| 0-0 | 0.0562 | 0.0708 | 0.0147 |
| 1-3 | 0.0524 | 0.0564 | 0.0039 |
| 0-3 | 0.0437 | 0.0510 | 0.0073 |
| 2-0 | 0.0342 | 0.0372 | 0.0030 |
| 2-3 | 0.0342 | 0.0327 | 0.0015 |
| 3-2 | 0.0254 | 0.0209 | 0.0045 |
| 1-4 | 0.0254 | 0.0251 | 0.0003 |
| 3-1 | 0.0231 | 0.0235 | 0.0004 |
| **Sum (top 15)** | **0.8651** | **0.8996** | — |
- High-score mass (total ≥9 goals): 2.34e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### USA vs Belgium
- CS outcomes: 31  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-1 | 0.1211 | 0.1247 | 0.0036 |
| 2-1 | 0.0829 | 0.0860 | 0.0031 |
| 1-2 | 0.0829 | 0.0846 | 0.0018 |
| 1-0 | 0.0716 | 0.0675 | 0.0041 |
| 2-2 | 0.0716 | 0.0695 | 0.0020 |
| 0-1 | 0.0716 | 0.0666 | 0.0050 |
| 2-0 | 0.0492 | 0.0571 | 0.0079 |
| 0-0 | 0.0492 | 0.0666 | 0.0174 |
| 0-2 | 0.0463 | 0.0545 | 0.0082 |
| 3-1 | 0.0394 | 0.0433 | 0.0040 |
| 1-3 | 0.0394 | 0.0419 | 0.0025 |
| 3-2 | 0.0342 | 0.0331 | 0.0011 |
| 2-3 | 0.0342 | 0.0324 | 0.0018 |
| 3-0 | 0.0254 | 0.0301 | 0.0047 |
| 0-3 | 0.0254 | 0.0285 | 0.0031 |
| **Sum (top 15)** | **0.8443** | **0.8865** | — |
- High-score mass (total ≥9 goals): 2.84e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Argentina vs Egypt
- CS outcomes: 26  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-0 | 0.1376 | 0.1480 | 0.0104 |
| 2-0 | 0.1376 | 0.1464 | 0.0088 |
| 2-1 | 0.0939 | 0.0934 | 0.0005 |
| 3-0 | 0.0887 | 0.0941 | 0.0054 |
| 1-1 | 0.0887 | 0.0924 | 0.0037 |
| 0-0 | 0.0665 | 0.0773 | 0.0108 |
| 3-1 | 0.0614 | 0.0613 | 0.0000 |
| 4-0 | 0.0443 | 0.0473 | 0.0030 |
| 0-1 | 0.0399 | 0.0486 | 0.0087 |
| 2-2 | 0.0347 | 0.0290 | 0.0057 |
| 4-1 | 0.0307 | 0.0301 | 0.0006 |
| 1-2 | 0.0285 | 0.0285 | 0.0000 |
| 3-2 | 0.0235 | 0.0198 | 0.0036 |
| 5-0 | 0.0235 | 0.0194 | 0.0040 |
| 5-1 | 0.0142 | 0.0118 | 0.0025 |
| **Sum (top 15)** | **0.9135** | **0.9474** | — |
- High-score mass (total ≥9 goals): 1.65e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Switzerland vs Colombia
- CS outcomes: 25  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-1 | 0.1358 | 0.1406 | 0.0047 |
| 0-1 | 0.1233 | 0.1211 | 0.0022 |
| 1-0 | 0.0943 | 0.0930 | 0.0013 |
| 0-0 | 0.0943 | 0.1135 | 0.0192 |
| 1-2 | 0.0844 | 0.0846 | 0.0002 |
| 0-2 | 0.0763 | 0.0847 | 0.0084 |
| 2-1 | 0.0668 | 0.0638 | 0.0030 |
| 2-2 | 0.0501 | 0.0468 | 0.0033 |
| 2-0 | 0.0445 | 0.0485 | 0.0040 |
| 0-3 | 0.0348 | 0.0379 | 0.0031 |
| 1-3 | 0.0348 | 0.0369 | 0.0021 |
| 2-3 | 0.0236 | 0.0191 | 0.0045 |
| 3-1 | 0.0223 | 0.0207 | 0.0016 |
| 3-2 | 0.0195 | 0.0139 | 0.0056 |
| 3-0 | 0.0174 | 0.0160 | 0.0014 |
| **Sum (top 15)** | **0.9224** | **0.9412** | — |
- High-score mass (total ≥9 goals): 1.27e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### France vs Morocco
- CS outcomes: 27  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-0 | 0.1329 | 0.1238 | 0.0091 |
| 1-1 | 0.1140 | 0.1140 | 0.0001 |
| 2-0 | 0.1064 | 0.1169 | 0.0106 |
| 2-1 | 0.1064 | 0.1016 | 0.0048 |
| 3-0 | 0.0665 | 0.0745 | 0.0081 |
| 0-0 | 0.0665 | 0.0811 | 0.0146 |
| 3-1 | 0.0570 | 0.0602 | 0.0032 |
| 0-1 | 0.0499 | 0.0543 | 0.0045 |
| 2-2 | 0.0469 | 0.0421 | 0.0048 |
| 1-2 | 0.0420 | 0.0419 | 0.0001 |
| 4-0 | 0.0307 | 0.0354 | 0.0047 |
| 3-2 | 0.0285 | 0.0251 | 0.0034 |
| 4-1 | 0.0257 | 0.0280 | 0.0022 |
| 0-2 | 0.0222 | 0.0231 | 0.0009 |
| 4-2 | 0.0131 | 0.0112 | 0.0018 |
| **Sum (top 15)** | **0.9084** | **0.9334** | — |
- High-score mass (total ≥9 goals): 1.81e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Norway vs England
- CS outcomes: 27  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-1 | 0.1214 | 0.1196 | 0.0018 |
| 0-1 | 0.1052 | 0.1071 | 0.0019 |
| 1-2 | 0.0877 | 0.0943 | 0.0066 |
| 0-2 | 0.0751 | 0.0861 | 0.0110 |
| 1-0 | 0.0717 | 0.0720 | 0.0003 |
| 0-0 | 0.0717 | 0.0757 | 0.0040 |
| 2-1 | 0.0657 | 0.0646 | 0.0011 |
| 2-2 | 0.0526 | 0.0533 | 0.0007 |
| 1-3 | 0.0464 | 0.0520 | 0.0056 |
| 2-0 | 0.0438 | 0.0414 | 0.0025 |
| 0-3 | 0.0415 | 0.0486 | 0.0071 |
| 3-1 | 0.0282 | 0.0241 | 0.0041 |
| 2-3 | 0.0282 | 0.0293 | 0.0011 |
| 3-2 | 0.0219 | 0.0190 | 0.0029 |
| 1-4 | 0.0219 | 0.0219 | 0.0001 |
| **Sum (top 15)** | **0.8831** | **0.9091** | — |
- High-score mass (total ≥9 goals): 2.06e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS
