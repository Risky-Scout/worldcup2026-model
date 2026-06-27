# Correct-Score Reconciliation Audit

**Generated**: 2026-06-27T04:54:30Z

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
| Total 2026 matches predicted | 10 |
| Matches with any CS data | 10 |
| Matches with 1 CS vendor | 10 |
| Matches with 2+ CS vendors | 0 |

## Per-match correct-score audit

### Panama vs England
- CS outcomes: 29  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 0-2 | 0.1219 | 0.1316 | 0.0097 |
| 0-3 | 0.1132 | 0.1232 | 0.0100 |
| 0-1 | 0.0834 | 0.0948 | 0.0114 |
| 0-4 | 0.0834 | 0.0870 | 0.0036 |
| 1-2 | 0.0720 | 0.0870 | 0.0150 |
| 1-3 | 0.0720 | 0.0810 | 0.0089 |
| 1-1 | 0.0528 | 0.0591 | 0.0062 |
| 1-4 | 0.0495 | 0.0570 | 0.0074 |
| 0-5 | 0.0466 | 0.0490 | 0.0024 |
| 0-0 | 0.0345 | 0.0342 | 0.0002 |
| 1-5 | 0.0305 | 0.0222 | 0.0083 |
| 2-2 | 0.0256 | 0.0277 | 0.0022 |
| 2-3 | 0.0256 | 0.0289 | 0.0034 |
| 0-6 | 0.0256 | 0.0222 | 0.0034 |
| 1-0 | 0.0220 | 0.0225 | 0.0005 |
| **Sum (top 15)** | **0.8587** | **0.9275** | — |
- High-score mass (total ≥9 goals): 3.00e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Croatia vs Ghana
- CS outcomes: 22  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-0 | 0.1536 | 0.1283 | 0.0253 |
| 1-1 | 0.1380 | 0.1510 | 0.0130 |
| 2-1 | 0.1018 | 0.0915 | 0.0103 |
| 2-0 | 0.0958 | 0.1050 | 0.0093 |
| 0-0 | 0.0905 | 0.1234 | 0.0329 |
| 0-1 | 0.0678 | 0.0645 | 0.0034 |
| 2-2 | 0.0509 | 0.0455 | 0.0054 |
| 3-0 | 0.0479 | 0.0569 | 0.0090 |
| 1-2 | 0.0479 | 0.0430 | 0.0049 |
| 3-1 | 0.0428 | 0.0452 | 0.0023 |
| 3-2 | 0.0263 | 0.0187 | 0.0076 |
| 0-2 | 0.0263 | 0.0267 | 0.0004 |
| 4-0 | 0.0199 | 0.0236 | 0.0037 |
| 4-1 | 0.0177 | 0.0181 | 0.0004 |
| 2-3 | 0.0133 | 0.0084 | 0.0049 |
| **Sum (top 15)** | **0.9404** | **0.9496** | — |
- High-score mass (total ≥9 goals): 1.26e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Colombia vs Portugal
- CS outcomes: 28  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-1 | 0.1051 | 0.1299 | 0.0247 |
| 0-1 | 0.0986 | 0.0996 | 0.0011 |
| 1-2 | 0.0928 | 0.0915 | 0.0013 |
| 0-2 | 0.0876 | 0.0879 | 0.0003 |
| 1-0 | 0.0657 | 0.0670 | 0.0013 |
| 2-1 | 0.0607 | 0.0598 | 0.0008 |
| 0-0 | 0.0607 | 0.0833 | 0.0227 |
| 1-3 | 0.0563 | 0.0526 | 0.0037 |
| 2-2 | 0.0493 | 0.0605 | 0.0112 |
| 0-3 | 0.0464 | 0.0485 | 0.0021 |
| 2-0 | 0.0394 | 0.0384 | 0.0010 |
| 2-3 | 0.0303 | 0.0283 | 0.0021 |
| 3-1 | 0.0254 | 0.0221 | 0.0033 |
| 0-4 | 0.0254 | 0.0209 | 0.0045 |
| 1-4 | 0.0254 | 0.0219 | 0.0036 |
| **Sum (top 15)** | **0.8691** | **0.9122** | — |
- High-score mass (total ≥9 goals): 2.01e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### DR Congo vs Uzbekistan
- CS outcomes: 28  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-0 | 0.1136 | 0.1233 | 0.0098 |
| 2-0 | 0.1060 | 0.1086 | 0.0026 |
| 1-1 | 0.0994 | 0.1076 | 0.0082 |
| 2-1 | 0.0883 | 0.0946 | 0.0063 |
| 0-0 | 0.0723 | 0.0771 | 0.0048 |
| 0-1 | 0.0662 | 0.0696 | 0.0033 |
| 3-0 | 0.0611 | 0.0626 | 0.0014 |
| 3-1 | 0.0568 | 0.0570 | 0.0002 |
| 1-2 | 0.0497 | 0.0520 | 0.0023 |
| 2-2 | 0.0397 | 0.0451 | 0.0053 |
| 0-2 | 0.0379 | 0.0337 | 0.0041 |
| 4-0 | 0.0306 | 0.0274 | 0.0032 |
| 4-1 | 0.0284 | 0.0249 | 0.0034 |
| 3-2 | 0.0256 | 0.0265 | 0.0008 |
| 1-3 | 0.0194 | 0.0167 | 0.0027 |
| **Sum (top 15)** | **0.8950** | **0.9267** | — |
- High-score mass (total ≥9 goals): 1.84e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Jordan vs Argentina
- CS outcomes: 27  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 0-2 | 0.1422 | 0.1432 | 0.0010 |
| 0-3 | 0.1328 | 0.1350 | 0.0023 |
| 0-1 | 0.0937 | 0.0998 | 0.0061 |
| 0-4 | 0.0937 | 0.0895 | 0.0042 |
| 1-3 | 0.0664 | 0.0752 | 0.0088 |
| 1-2 | 0.0613 | 0.0827 | 0.0215 |
| 0-5 | 0.0531 | 0.0502 | 0.0029 |
| 1-1 | 0.0469 | 0.0564 | 0.0096 |
| 0-0 | 0.0443 | 0.0363 | 0.0080 |
| 1-4 | 0.0443 | 0.0528 | 0.0086 |
| 0-6 | 0.0284 | 0.0222 | 0.0063 |
| 1-0 | 0.0257 | 0.0222 | 0.0035 |
| 1-5 | 0.0257 | 0.0222 | 0.0035 |
| 2-1 | 0.0173 | 0.0194 | 0.0021 |
| 2-2 | 0.0173 | 0.0234 | 0.0061 |
| **Sum (top 15)** | **0.8930** | **0.9306** | — |
- High-score mass (total ≥9 goals): 3.02e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Algeria vs Austria
- CS outcomes: 22  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-1 | 0.1622 | 0.1930 | 0.0308 |
| 0-0 | 0.1588 | 0.2071 | 0.0483 |
| 0-1 | 0.1411 | 0.1310 | 0.0102 |
| 1-0 | 0.1016 | 0.1039 | 0.0023 |
| 1-2 | 0.0762 | 0.0624 | 0.0138 |
| 0-2 | 0.0726 | 0.0914 | 0.0188 |
| 2-1 | 0.0544 | 0.0498 | 0.0046 |
| 2-2 | 0.0476 | 0.0283 | 0.0193 |
| 2-0 | 0.0381 | 0.0603 | 0.0222 |
| 0-3 | 0.0272 | 0.0240 | 0.0032 |
| 1-3 | 0.0272 | 0.0128 | 0.0144 |
| 3-1 | 0.0149 | 0.0079 | 0.0070 |
| 2-3 | 0.0149 | 0.0030 | 0.0119 |
| 3-0 | 0.0115 | 0.0120 | 0.0004 |
| 3-2 | 0.0107 | 0.0025 | 0.0082 |
| **Sum (top 15)** | **0.9593** | **0.9894** | — |
- High-score mass (total ≥9 goals): 1.67e-07
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### South Africa vs Canada
- CS outcomes: 24  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 0-1 | 0.1399 | 0.1402 | 0.0003 |
| 1-1 | 0.1159 | 0.1197 | 0.0038 |
| 0-2 | 0.1082 | 0.1169 | 0.0087 |
| 1-2 | 0.0954 | 0.0942 | 0.0013 |
| 0-0 | 0.0854 | 0.0991 | 0.0137 |
| 1-0 | 0.0676 | 0.0707 | 0.0031 |
| 0-3 | 0.0541 | 0.0622 | 0.0081 |
| 1-3 | 0.0507 | 0.0508 | 0.0001 |
| 2-1 | 0.0451 | 0.0446 | 0.0005 |
| 2-2 | 0.0451 | 0.0394 | 0.0057 |
| 2-0 | 0.0290 | 0.0292 | 0.0002 |
| 2-3 | 0.0262 | 0.0208 | 0.0054 |
| 0-4 | 0.0262 | 0.0265 | 0.0003 |
| 1-4 | 0.0225 | 0.0207 | 0.0018 |
| 3-1 | 0.0133 | 0.0116 | 0.0017 |
| **Sum (top 15)** | **0.9245** | **0.9465** | — |
- High-score mass (total ≥9 goals): 1.39e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Brazil vs Japan
- CS outcomes: 27  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-0 | 0.1231 | 0.1245 | 0.0014 |
| 2-0 | 0.1067 | 0.1119 | 0.0052 |
| 1-1 | 0.1067 | 0.1151 | 0.0084 |
| 2-1 | 0.0941 | 0.0958 | 0.0017 |
| 0-0 | 0.0727 | 0.0860 | 0.0133 |
| 3-0 | 0.0615 | 0.0646 | 0.0030 |
| 0-1 | 0.0615 | 0.0656 | 0.0041 |
| 3-1 | 0.0533 | 0.0551 | 0.0018 |
| 1-2 | 0.0471 | 0.0485 | 0.0015 |
| 2-2 | 0.0444 | 0.0444 | 0.0000 |
| 4-0 | 0.0308 | 0.0285 | 0.0022 |
| 3-2 | 0.0286 | 0.0249 | 0.0036 |
| 0-2 | 0.0286 | 0.0299 | 0.0013 |
| 4-1 | 0.0258 | 0.0241 | 0.0017 |
| 1-3 | 0.0157 | 0.0142 | 0.0015 |
| **Sum (top 15)** | **0.9005** | **0.9331** | — |
- High-score mass (total ≥9 goals): 1.71e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Netherlands vs Morocco
- CS outcomes: 26  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-1 | 0.1374 | 0.1357 | 0.0017 |
| 1-0 | 0.1226 | 0.1217 | 0.0009 |
| 2-1 | 0.0938 | 0.0902 | 0.0036 |
| 0-0 | 0.0839 | 0.0993 | 0.0154 |
| 0-1 | 0.0839 | 0.0877 | 0.0038 |
| 2-0 | 0.0724 | 0.0855 | 0.0131 |
| 1-2 | 0.0664 | 0.0641 | 0.0023 |
| 2-2 | 0.0569 | 0.0485 | 0.0084 |
| 3-1 | 0.0379 | 0.0407 | 0.0028 |
| 0-2 | 0.0379 | 0.0458 | 0.0078 |
| 3-0 | 0.0347 | 0.0405 | 0.0058 |
| 3-2 | 0.0257 | 0.0215 | 0.0042 |
| 1-3 | 0.0221 | 0.0212 | 0.0009 |
| 2-3 | 0.0194 | 0.0151 | 0.0044 |
| 0-3 | 0.0156 | 0.0154 | 0.0002 |
| **Sum (top 15)** | **0.9108** | **0.9330** | — |
- High-score mass (total ≥9 goals): 1.47e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### USA vs Bosnia & Herzegovina
- CS outcomes: 26  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-0 | 0.1331 | 0.1319 | 0.0012 |
| 2-0 | 0.1331 | 0.1363 | 0.0032 |
| 2-1 | 0.0940 | 0.0960 | 0.0021 |
| 1-1 | 0.0887 | 0.0927 | 0.0040 |
| 3-0 | 0.0841 | 0.0919 | 0.0079 |
| 0-0 | 0.0665 | 0.0720 | 0.0054 |
| 3-1 | 0.0614 | 0.0650 | 0.0036 |
| 4-0 | 0.0470 | 0.0490 | 0.0021 |
| 0-1 | 0.0420 | 0.0457 | 0.0036 |
| 2-2 | 0.0347 | 0.0339 | 0.0008 |
| 4-1 | 0.0307 | 0.0333 | 0.0026 |
| 1-2 | 0.0307 | 0.0321 | 0.0014 |
| 3-2 | 0.0258 | 0.0236 | 0.0021 |
| 5-0 | 0.0222 | 0.0204 | 0.0018 |
| 0-2 | 0.0157 | 0.0161 | 0.0005 |
| **Sum (top 15)** | **0.9097** | **0.9401** | — |
- High-score mass (total ≥9 goals): 1.89e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS
