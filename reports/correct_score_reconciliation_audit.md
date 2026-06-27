# Correct-Score Reconciliation Audit

**Generated**: 2026-06-27T03:41:58Z

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
| 0-2 | 0.1305 | 0.1350 | 0.0045 |
| 0-3 | 0.1118 | 0.1221 | 0.0103 |
| 0-4 | 0.0824 | 0.0837 | 0.0013 |
| 0-1 | 0.0783 | 0.0923 | 0.0140 |
| 1-2 | 0.0712 | 0.0883 | 0.0172 |
| 1-3 | 0.0712 | 0.0798 | 0.0086 |
| 1-4 | 0.0522 | 0.0569 | 0.0047 |
| 1-1 | 0.0489 | 0.0595 | 0.0106 |
| 0-5 | 0.0489 | 0.0476 | 0.0014 |
| 0-0 | 0.0340 | 0.0341 | 0.0001 |
| 1-5 | 0.0301 | 0.0222 | 0.0079 |
| 0-6 | 0.0280 | 0.0222 | 0.0058 |
| 2-2 | 0.0253 | 0.0284 | 0.0032 |
| 1-0 | 0.0230 | 0.0232 | 0.0002 |
| 2-3 | 0.0230 | 0.0290 | 0.0059 |
| **Sum (top 15)** | **0.8589** | **0.9242** | — |
- High-score mass (total ≥9 goals): 3.08e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Croatia vs Ghana
- CS outcomes: 22  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-0 | 0.1537 | 0.1265 | 0.0272 |
| 1-1 | 0.1381 | 0.1502 | 0.0121 |
| 2-1 | 0.1018 | 0.0918 | 0.0100 |
| 2-0 | 0.0959 | 0.1043 | 0.0085 |
| 0-0 | 0.0959 | 0.1245 | 0.0286 |
| 0-1 | 0.0679 | 0.0637 | 0.0042 |
| 3-0 | 0.0479 | 0.0571 | 0.0092 |
| 2-2 | 0.0479 | 0.0452 | 0.0028 |
| 1-2 | 0.0479 | 0.0434 | 0.0045 |
| 3-1 | 0.0429 | 0.0456 | 0.0027 |
| 3-2 | 0.0263 | 0.0190 | 0.0073 |
| 0-2 | 0.0240 | 0.0261 | 0.0022 |
| 4-0 | 0.0199 | 0.0238 | 0.0040 |
| 4-1 | 0.0177 | 0.0184 | 0.0007 |
| 2-3 | 0.0134 | 0.0086 | 0.0047 |
| **Sum (top 15)** | **0.9412** | **0.9485** | — |
- High-score mass (total ≥9 goals): 1.28e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Colombia vs Portugal
- CS outcomes: 29  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-1 | 0.1048 | 0.1295 | 0.0247 |
| 0-1 | 0.0983 | 0.1003 | 0.0020 |
| 0-2 | 0.0873 | 0.0889 | 0.0016 |
| 1-2 | 0.0873 | 0.0902 | 0.0029 |
| 1-0 | 0.0655 | 0.0662 | 0.0007 |
| 2-1 | 0.0605 | 0.0589 | 0.0015 |
| 0-0 | 0.0605 | 0.0834 | 0.0229 |
| 1-3 | 0.0561 | 0.0533 | 0.0029 |
| 2-2 | 0.0491 | 0.0602 | 0.0111 |
| 0-3 | 0.0491 | 0.0503 | 0.0012 |
| 2-0 | 0.0414 | 0.0379 | 0.0034 |
| 2-3 | 0.0302 | 0.0285 | 0.0017 |
| 3-1 | 0.0254 | 0.0216 | 0.0038 |
| 1-4 | 0.0254 | 0.0224 | 0.0030 |
| 0-4 | 0.0231 | 0.0213 | 0.0018 |
| **Sum (top 15)** | **0.8640** | **0.9129** | — |
- High-score mass (total ≥9 goals): 2.00e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### DR Congo vs Uzbekistan
- CS outcomes: 28  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-0 | 0.1062 | 0.1221 | 0.0159 |
| 2-0 | 0.1062 | 0.1099 | 0.0037 |
| 1-1 | 0.0996 | 0.1070 | 0.0074 |
| 2-1 | 0.0838 | 0.0935 | 0.0097 |
| 0-0 | 0.0724 | 0.0763 | 0.0039 |
| 0-1 | 0.0664 | 0.0702 | 0.0038 |
| 3-0 | 0.0613 | 0.0630 | 0.0017 |
| 3-1 | 0.0569 | 0.0574 | 0.0005 |
| 1-2 | 0.0498 | 0.0518 | 0.0020 |
| 2-2 | 0.0419 | 0.0450 | 0.0031 |
| 0-2 | 0.0379 | 0.0340 | 0.0039 |
| 4-0 | 0.0306 | 0.0276 | 0.0031 |
| 3-2 | 0.0257 | 0.0267 | 0.0010 |
| 4-1 | 0.0257 | 0.0247 | 0.0010 |
| 1-3 | 0.0194 | 0.0167 | 0.0028 |
| **Sum (top 15)** | **0.8838** | **0.9259** | — |
- High-score mass (total ≥9 goals): 1.84e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Jordan vs Argentina
- CS outcomes: 26  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 0-2 | 0.1456 | 0.1437 | 0.0019 |
| 0-3 | 0.1335 | 0.1344 | 0.0009 |
| 0-1 | 0.1001 | 0.1012 | 0.0011 |
| 0-4 | 0.0942 | 0.0896 | 0.0046 |
| 1-2 | 0.0616 | 0.0825 | 0.0209 |
| 1-3 | 0.0616 | 0.0739 | 0.0123 |
| 1-1 | 0.0501 | 0.0567 | 0.0067 |
| 0-5 | 0.0501 | 0.0494 | 0.0006 |
| 0-0 | 0.0445 | 0.0354 | 0.0090 |
| 1-4 | 0.0421 | 0.0526 | 0.0104 |
| 0-6 | 0.0286 | 0.0222 | 0.0064 |
| 1-0 | 0.0258 | 0.0221 | 0.0037 |
| 1-5 | 0.0258 | 0.0222 | 0.0037 |
| 2-2 | 0.0195 | 0.0239 | 0.0044 |
| 2-1 | 0.0174 | 0.0195 | 0.0021 |
| **Sum (top 15)** | **0.9006** | **0.9293** | — |
- High-score mass (total ≥9 goals): 3.06e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Algeria vs Austria
- CS outcomes: 19  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 0-0 | 0.1792 | 0.2098 | 0.0305 |
| 0-1 | 0.1640 | 0.1350 | 0.0290 |
| 1-1 | 0.1606 | 0.1915 | 0.0309 |
| 1-0 | 0.1028 | 0.1004 | 0.0024 |
| 0-2 | 0.0734 | 0.0924 | 0.0190 |
| 1-2 | 0.0701 | 0.0606 | 0.0094 |
| 2-1 | 0.0482 | 0.0493 | 0.0012 |
| 2-2 | 0.0428 | 0.0272 | 0.0156 |
| 2-0 | 0.0335 | 0.0599 | 0.0264 |
| 0-3 | 0.0296 | 0.0248 | 0.0048 |
| 1-3 | 0.0249 | 0.0127 | 0.0121 |
| 3-1 | 0.0126 | 0.0080 | 0.0046 |
| 2-3 | 0.0126 | 0.0030 | 0.0097 |
| 3-0 | 0.0095 | 0.0120 | 0.0025 |
| 3-2 | 0.0095 | 0.0026 | 0.0070 |
| **Sum (top 15)** | **0.9734** | **0.9893** | — |
- High-score mass (total ≥9 goals): 1.92e-07
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
| 1-0 | 0.1231 | 0.1249 | 0.0018 |
| 2-0 | 0.1067 | 0.1125 | 0.0058 |
| 1-1 | 0.1067 | 0.1148 | 0.0081 |
| 2-1 | 0.0941 | 0.0959 | 0.0018 |
| 0-0 | 0.0727 | 0.0858 | 0.0131 |
| 3-0 | 0.0615 | 0.0650 | 0.0035 |
| 0-1 | 0.0615 | 0.0653 | 0.0038 |
| 3-1 | 0.0533 | 0.0554 | 0.0020 |
| 1-2 | 0.0471 | 0.0481 | 0.0011 |
| 2-2 | 0.0444 | 0.0441 | 0.0003 |
| 4-0 | 0.0308 | 0.0288 | 0.0019 |
| 3-2 | 0.0286 | 0.0249 | 0.0036 |
| 0-2 | 0.0286 | 0.0296 | 0.0010 |
| 4-1 | 0.0258 | 0.0242 | 0.0016 |
| 1-3 | 0.0157 | 0.0139 | 0.0017 |
| **Sum (top 15)** | **0.9005** | **0.9335** | — |
- High-score mass (total ≥9 goals): 1.70e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Netherlands vs Morocco
- CS outcomes: 26  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-1 | 0.1374 | 0.1370 | 0.0005 |
| 1-0 | 0.1226 | 0.1205 | 0.0021 |
| 2-1 | 0.0938 | 0.0903 | 0.0035 |
| 0-0 | 0.0839 | 0.1008 | 0.0169 |
| 0-1 | 0.0839 | 0.0866 | 0.0027 |
| 2-0 | 0.0724 | 0.0856 | 0.0132 |
| 1-2 | 0.0664 | 0.0638 | 0.0026 |
| 2-2 | 0.0569 | 0.0489 | 0.0081 |
| 3-1 | 0.0379 | 0.0408 | 0.0029 |
| 0-2 | 0.0379 | 0.0453 | 0.0073 |
| 3-0 | 0.0347 | 0.0407 | 0.0061 |
| 3-2 | 0.0257 | 0.0215 | 0.0042 |
| 1-3 | 0.0221 | 0.0210 | 0.0012 |
| 2-3 | 0.0194 | 0.0149 | 0.0045 |
| 0-3 | 0.0156 | 0.0152 | 0.0005 |
| **Sum (top 15)** | **0.9108** | **0.9328** | — |
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
