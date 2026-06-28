# Correct-Score Reconciliation Audit

**Generated**: 2026-06-28T08:26:10Z

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
| Total 2026 matches predicted | 9 |
| Matches with any CS data | 9 |
| Matches with 1 CS vendor | 9 |
| Matches with 2+ CS vendors | 0 |

## Per-match correct-score audit

### South Africa vs Canada
- CS outcomes: 26  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 0-1 | 0.1361 | 0.1370 | 0.0009 |
| 1-1 | 0.1236 | 0.1230 | 0.0006 |
| 0-2 | 0.1004 | 0.1148 | 0.0144 |
| 1-2 | 0.1004 | 0.0965 | 0.0039 |
| 0-0 | 0.0803 | 0.0960 | 0.0157 |
| 1-0 | 0.0618 | 0.0679 | 0.0062 |
| 0-3 | 0.0574 | 0.0640 | 0.0066 |
| 2-2 | 0.0502 | 0.0402 | 0.0100 |
| 2-1 | 0.0472 | 0.0450 | 0.0022 |
| 1-3 | 0.0472 | 0.0508 | 0.0036 |
| 2-0 | 0.0259 | 0.0285 | 0.0026 |
| 2-3 | 0.0259 | 0.0213 | 0.0046 |
| 0-4 | 0.0259 | 0.0272 | 0.0013 |
| 1-4 | 0.0223 | 0.0214 | 0.0009 |
| 3-2 | 0.0143 | 0.0096 | 0.0047 |
| **Sum (top 15)** | **0.9191** | **0.9432** | — |
- High-score mass (total ≥9 goals): 1.45e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Brazil vs Japan
- CS outcomes: 27  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-0 | 0.1231 | 0.1244 | 0.0013 |
| 2-0 | 0.1067 | 0.1120 | 0.0053 |
| 1-1 | 0.1067 | 0.1133 | 0.0066 |
| 2-1 | 0.0941 | 0.0965 | 0.0024 |
| 0-0 | 0.0727 | 0.0835 | 0.0107 |
| 3-0 | 0.0616 | 0.0656 | 0.0041 |
| 0-1 | 0.0616 | 0.0645 | 0.0029 |
| 3-1 | 0.0533 | 0.0562 | 0.0029 |
| 1-2 | 0.0471 | 0.0483 | 0.0012 |
| 2-2 | 0.0445 | 0.0444 | 0.0000 |
| 0-2 | 0.0308 | 0.0296 | 0.0012 |
| 4-0 | 0.0286 | 0.0290 | 0.0004 |
| 3-2 | 0.0258 | 0.0251 | 0.0007 |
| 4-1 | 0.0258 | 0.0249 | 0.0009 |
| 1-3 | 0.0174 | 0.0143 | 0.0031 |
| **Sum (top 15)** | **0.8997** | **0.9317** | — |
- High-score mass (total ≥9 goals): 1.75e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Germany vs Paraguay
- CS outcomes: 27  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 2-0 | 0.1223 | 0.1314 | 0.0090 |
| 1-0 | 0.1136 | 0.1177 | 0.0041 |
| 2-1 | 0.0935 | 0.0968 | 0.0033 |
| 3-0 | 0.0883 | 0.0958 | 0.0075 |
| 1-1 | 0.0837 | 0.0896 | 0.0059 |
| 3-1 | 0.0723 | 0.0720 | 0.0003 |
| 0-0 | 0.0530 | 0.0629 | 0.0099 |
| 4-0 | 0.0468 | 0.0526 | 0.0059 |
| 4-1 | 0.0379 | 0.0386 | 0.0007 |
| 2-2 | 0.0379 | 0.0358 | 0.0021 |
| 0-1 | 0.0379 | 0.0409 | 0.0031 |
| 1-2 | 0.0346 | 0.0321 | 0.0025 |
| 3-2 | 0.0284 | 0.0264 | 0.0020 |
| 5-0 | 0.0256 | 0.0239 | 0.0017 |
| 5-1 | 0.0194 | 0.0168 | 0.0026 |
| **Sum (top 15)** | **0.8952** | **0.9333** | — |
- High-score mass (total ≥9 goals): 2.13e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Netherlands vs Morocco
- CS outcomes: 26  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-1 | 0.1331 | 0.1377 | 0.0046 |
| 1-0 | 0.1229 | 0.1199 | 0.0030 |
| 2-1 | 0.0940 | 0.0902 | 0.0038 |
| 0-0 | 0.0841 | 0.1045 | 0.0204 |
| 0-1 | 0.0799 | 0.0839 | 0.0040 |
| 2-0 | 0.0761 | 0.0881 | 0.0121 |
| 1-2 | 0.0666 | 0.0626 | 0.0039 |
| 2-2 | 0.0570 | 0.0491 | 0.0079 |
| 3-1 | 0.0399 | 0.0413 | 0.0014 |
| 0-2 | 0.0380 | 0.0443 | 0.0062 |
| 3-0 | 0.0347 | 0.0414 | 0.0067 |
| 3-2 | 0.0285 | 0.0215 | 0.0070 |
| 1-3 | 0.0222 | 0.0201 | 0.0021 |
| 2-3 | 0.0195 | 0.0144 | 0.0051 |
| 4-1 | 0.0157 | 0.0147 | 0.0010 |
| **Sum (top 15)** | **0.9120** | **0.9337** | — |
- High-score mass (total ≥9 goals): 1.45e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Côte d'Ivoire vs Norway
- CS outcomes: 27  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-1 | 0.1220 | 0.1247 | 0.0027 |
| 0-1 | 0.1058 | 0.0989 | 0.0068 |
| 1-2 | 0.0933 | 0.0946 | 0.0012 |
| 0-2 | 0.0793 | 0.0833 | 0.0040 |
| 1-0 | 0.0721 | 0.0705 | 0.0016 |
| 2-1 | 0.0661 | 0.0671 | 0.0010 |
| 0-0 | 0.0661 | 0.0782 | 0.0121 |
| 2-2 | 0.0567 | 0.0574 | 0.0007 |
| 1-3 | 0.0467 | 0.0503 | 0.0036 |
| 0-3 | 0.0417 | 0.0458 | 0.0040 |
| 2-0 | 0.0378 | 0.0416 | 0.0038 |
| 2-3 | 0.0283 | 0.0290 | 0.0006 |
| 3-1 | 0.0256 | 0.0255 | 0.0001 |
| 3-2 | 0.0220 | 0.0204 | 0.0016 |
| 1-4 | 0.0220 | 0.0207 | 0.0013 |
| **Sum (top 15)** | **0.8855** | **0.9079** | — |
- High-score mass (total ≥9 goals): 2.15e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### France vs Sweden
- CS outcomes: 28  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 2-0 | 0.1221 | 0.1263 | 0.0042 |
| 1-0 | 0.0992 | 0.1036 | 0.0044 |
| 3-0 | 0.0992 | 0.1047 | 0.0055 |
| 2-1 | 0.0934 | 0.0969 | 0.0035 |
| 3-1 | 0.0722 | 0.0778 | 0.0056 |
| 1-1 | 0.0722 | 0.0759 | 0.0037 |
| 4-0 | 0.0611 | 0.0648 | 0.0037 |
| 4-1 | 0.0441 | 0.0476 | 0.0035 |
| 0-0 | 0.0418 | 0.0457 | 0.0039 |
| 2-2 | 0.0345 | 0.0361 | 0.0016 |
| 5-0 | 0.0305 | 0.0317 | 0.0012 |
| 3-2 | 0.0284 | 0.0302 | 0.0019 |
| 0-1 | 0.0284 | 0.0322 | 0.0039 |
| 1-2 | 0.0256 | 0.0293 | 0.0036 |
| 5-1 | 0.0234 | 0.0220 | 0.0013 |
| **Sum (top 15)** | **0.8761** | **0.9249** | — |
- High-score mass (total ≥9 goals): 2.58e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### USA vs Bosnia & Herzegovina
- CS outcomes: 26  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-0 | 0.1320 | 0.1290 | 0.0030 |
| 2-0 | 0.1320 | 0.1361 | 0.0041 |
| 2-1 | 0.0932 | 0.0957 | 0.0025 |
| 3-0 | 0.0880 | 0.0961 | 0.0081 |
| 1-1 | 0.0834 | 0.0887 | 0.0053 |
| 3-1 | 0.0609 | 0.0666 | 0.0056 |
| 0-0 | 0.0609 | 0.0673 | 0.0063 |
| 4-0 | 0.0528 | 0.0538 | 0.0010 |
| 0-1 | 0.0377 | 0.0418 | 0.0041 |
| 4-1 | 0.0344 | 0.0361 | 0.0017 |
| 2-2 | 0.0344 | 0.0337 | 0.0008 |
| 1-2 | 0.0305 | 0.0308 | 0.0003 |
| 3-2 | 0.0256 | 0.0241 | 0.0014 |
| 5-0 | 0.0233 | 0.0229 | 0.0004 |
| 5-1 | 0.0172 | 0.0154 | 0.0018 |
| **Sum (top 15)** | **0.9064** | **0.9381** | — |
- High-score mass (total ≥9 goals): 2.01e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Australia vs Egypt
- CS outcomes: 22  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-1 | 0.1462 | 0.1444 | 0.0018 |
| 0-1 | 0.1364 | 0.1406 | 0.0042 |
| 0-0 | 0.1170 | 0.1356 | 0.0187 |
| 1-0 | 0.1092 | 0.1165 | 0.0073 |
| 1-2 | 0.0780 | 0.0758 | 0.0021 |
| 2-1 | 0.0682 | 0.0641 | 0.0041 |
| 0-2 | 0.0682 | 0.0809 | 0.0127 |
| 2-0 | 0.0482 | 0.0577 | 0.0095 |
| 2-2 | 0.0455 | 0.0366 | 0.0089 |
| 0-3 | 0.0292 | 0.0303 | 0.0011 |
| 1-3 | 0.0292 | 0.0263 | 0.0029 |
| 3-1 | 0.0227 | 0.0183 | 0.0044 |
| 3-0 | 0.0178 | 0.0175 | 0.0003 |
| 2-3 | 0.0178 | 0.0114 | 0.0064 |
| 3-2 | 0.0161 | 0.0094 | 0.0066 |
| **Sum (top 15)** | **0.9497** | **0.9656** | — |
- High-score mass (total ≥9 goals): 5.82e-06
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Argentina vs Cabo Verde
- CS outcomes: 25  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 2-0 | 0.1581 | 0.1601 | 0.0020 |
| 3-0 | 0.1344 | 0.1356 | 0.0012 |
| 1-0 | 0.1152 | 0.1306 | 0.0154 |
| 4-0 | 0.0949 | 0.0914 | 0.0035 |
| 2-1 | 0.0672 | 0.0770 | 0.0098 |
| 3-1 | 0.0576 | 0.0663 | 0.0087 |
| 5-0 | 0.0504 | 0.0472 | 0.0032 |
| 1-1 | 0.0474 | 0.0550 | 0.0076 |
| 0-0 | 0.0448 | 0.0467 | 0.0019 |
| 4-1 | 0.0403 | 0.0438 | 0.0035 |
| 5-1 | 0.0260 | 0.0220 | 0.0040 |
| 6-0 | 0.0260 | 0.0202 | 0.0058 |
| 0-1 | 0.0224 | 0.0249 | 0.0025 |
| 2-2 | 0.0175 | 0.0186 | 0.0011 |
| 3-2 | 0.0144 | 0.0172 | 0.0028 |
| **Sum (top 15)** | **0.9167** | **0.9565** | — |
- High-score mass (total ≥9 goals): 2.31e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS
