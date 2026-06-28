# Correct-Score Reconciliation Audit

**Generated**: 2026-06-28T00:17:16Z

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
| Total 2026 matches predicted | 11 |
| Matches with any CS data | 11 |
| Matches with 1 CS vendor | 11 |
| Matches with 2+ CS vendors | 0 |

## Per-match correct-score audit

### Jordan vs Argentina
- CS outcomes: 27  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 0-2 | 0.1438 | 0.1462 | 0.0023 |
| 0-3 | 0.1342 | 0.1400 | 0.0058 |
| 0-1 | 0.0948 | 0.0999 | 0.0052 |
| 0-4 | 0.0948 | 0.0963 | 0.0015 |
| 1-2 | 0.0620 | 0.0808 | 0.0189 |
| 1-3 | 0.0620 | 0.0742 | 0.0122 |
| 0-5 | 0.0575 | 0.0571 | 0.0005 |
| 1-1 | 0.0447 | 0.0519 | 0.0071 |
| 1-4 | 0.0447 | 0.0545 | 0.0098 |
| 0-0 | 0.0403 | 0.0336 | 0.0067 |
| 0-6 | 0.0310 | 0.0223 | 0.0087 |
| 1-5 | 0.0260 | 0.0223 | 0.0037 |
| 1-0 | 0.0224 | 0.0194 | 0.0029 |
| 2-2 | 0.0196 | 0.0213 | 0.0016 |
| 2-1 | 0.0158 | 0.0165 | 0.0007 |
| **Sum (top 15)** | **0.8936** | **0.9363** | — |
- High-score mass (total ≥9 goals): 3.07e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Algeria vs Austria
- CS outcomes: 18  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 0-1 | 0.1939 | 0.1242 | 0.0697 |
| 1-1 | 0.1861 | 0.1952 | 0.0090 |
| 1-0 | 0.1330 | 0.1177 | 0.0153 |
| 0-2 | 0.0980 | 0.0745 | 0.0235 |
| 1-2 | 0.0846 | 0.0466 | 0.0380 |
| 2-1 | 0.0547 | 0.0509 | 0.0039 |
| 2-0 | 0.0465 | 0.0741 | 0.0276 |
| 2-2 | 0.0443 | 0.0209 | 0.0234 |
| 0-3 | 0.0405 | 0.0132 | 0.0272 |
| 1-3 | 0.0300 | 0.0065 | 0.0235 |
| 3-1 | 0.0182 | 0.0087 | 0.0095 |
| 3-0 | 0.0153 | 0.0162 | 0.0010 |
| 2-3 | 0.0141 | 0.0015 | 0.0126 |
| 0-4 | 0.0115 | 0.0014 | 0.0101 |
| 3-2 | 0.0092 | 0.0021 | 0.0071 |
| **Sum (top 15)** | **0.9800** | **0.7538** | — |
- High-score mass (total ≥9 goals): 5.42e-08
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### South Africa vs Canada
- CS outcomes: 25  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 0-1 | 0.1429 | 0.1378 | 0.0050 |
| 1-1 | 0.1231 | 0.1222 | 0.0009 |
| 0-2 | 0.1067 | 0.1162 | 0.0095 |
| 1-2 | 0.1000 | 0.0963 | 0.0037 |
| 0-0 | 0.0842 | 0.0976 | 0.0134 |
| 1-0 | 0.0615 | 0.0666 | 0.0050 |
| 0-3 | 0.0571 | 0.0645 | 0.0074 |
| 2-2 | 0.0471 | 0.0398 | 0.0072 |
| 1-3 | 0.0471 | 0.0508 | 0.0038 |
| 2-1 | 0.0444 | 0.0443 | 0.0002 |
| 2-0 | 0.0258 | 0.0277 | 0.0019 |
| 2-3 | 0.0258 | 0.0211 | 0.0047 |
| 0-4 | 0.0258 | 0.0276 | 0.0018 |
| 1-4 | 0.0222 | 0.0215 | 0.0007 |
| 3-2 | 0.0131 | 0.0094 | 0.0037 |
| **Sum (top 15)** | **0.9268** | **0.9435** | — |
- High-score mass (total ≥9 goals): 1.44e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Brazil vs Japan
- CS outcomes: 27  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-0 | 0.1231 | 0.1245 | 0.0014 |
| 2-0 | 0.1067 | 0.1120 | 0.0053 |
| 1-1 | 0.1067 | 0.1134 | 0.0067 |
| 2-1 | 0.0941 | 0.0965 | 0.0023 |
| 0-0 | 0.0727 | 0.0836 | 0.0109 |
| 3-0 | 0.0616 | 0.0655 | 0.0039 |
| 0-1 | 0.0616 | 0.0645 | 0.0030 |
| 3-1 | 0.0533 | 0.0561 | 0.0028 |
| 1-2 | 0.0471 | 0.0483 | 0.0012 |
| 2-2 | 0.0445 | 0.0444 | 0.0000 |
| 0-2 | 0.0308 | 0.0297 | 0.0011 |
| 4-0 | 0.0286 | 0.0289 | 0.0004 |
| 3-2 | 0.0258 | 0.0251 | 0.0007 |
| 4-1 | 0.0258 | 0.0248 | 0.0010 |
| 1-3 | 0.0174 | 0.0143 | 0.0031 |
| **Sum (top 15)** | **0.8997** | **0.9316** | — |
- High-score mass (total ≥9 goals): 1.75e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Germany vs Paraguay
- CS outcomes: 27  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 2-0 | 0.1223 | 0.1288 | 0.0065 |
| 1-0 | 0.1136 | 0.1134 | 0.0002 |
| 2-1 | 0.0935 | 0.0974 | 0.0039 |
| 3-0 | 0.0883 | 0.0965 | 0.0082 |
| 1-1 | 0.0837 | 0.0878 | 0.0041 |
| 3-1 | 0.0723 | 0.0736 | 0.0013 |
| 0-0 | 0.0530 | 0.0597 | 0.0067 |
| 4-0 | 0.0468 | 0.0540 | 0.0073 |
| 4-1 | 0.0379 | 0.0403 | 0.0024 |
| 2-2 | 0.0379 | 0.0368 | 0.0011 |
| 0-1 | 0.0379 | 0.0390 | 0.0011 |
| 1-2 | 0.0346 | 0.0325 | 0.0021 |
| 3-2 | 0.0284 | 0.0277 | 0.0007 |
| 5-0 | 0.0256 | 0.0251 | 0.0006 |
| 5-1 | 0.0194 | 0.0180 | 0.0014 |
| **Sum (top 15)** | **0.8952** | **0.9305** | — |
- High-score mass (total ≥9 goals): 2.23e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Netherlands vs Morocco
- CS outcomes: 25  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-1 | 0.1342 | 0.1369 | 0.0027 |
| 1-0 | 0.1150 | 0.1179 | 0.0028 |
| 2-1 | 0.0895 | 0.0888 | 0.0006 |
| 0-0 | 0.0848 | 0.1030 | 0.0183 |
| 2-0 | 0.0805 | 0.0896 | 0.0091 |
| 0-1 | 0.0805 | 0.0848 | 0.0043 |
| 1-2 | 0.0671 | 0.0630 | 0.0041 |
| 2-2 | 0.0503 | 0.0474 | 0.0029 |
| 3-1 | 0.0424 | 0.0420 | 0.0004 |
| 3-0 | 0.0403 | 0.0427 | 0.0024 |
| 0-2 | 0.0403 | 0.0451 | 0.0048 |
| 3-2 | 0.0260 | 0.0214 | 0.0046 |
| 1-3 | 0.0260 | 0.0208 | 0.0051 |
| 2-3 | 0.0196 | 0.0145 | 0.0051 |
| 4-1 | 0.0158 | 0.0147 | 0.0010 |
| **Sum (top 15)** | **0.9122** | **0.9328** | — |
- High-score mass (total ≥9 goals): 1.45e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Côte d'Ivoire vs Norway
- CS outcomes: 27  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-1 | 0.1313 | 0.1283 | 0.0030 |
| 0-1 | 0.1050 | 0.1009 | 0.0041 |
| 1-2 | 0.0927 | 0.0943 | 0.0016 |
| 1-0 | 0.0716 | 0.0721 | 0.0005 |
| 0-2 | 0.0716 | 0.0815 | 0.0099 |
| 2-1 | 0.0657 | 0.0670 | 0.0014 |
| 0-0 | 0.0657 | 0.0785 | 0.0128 |
| 2-2 | 0.0606 | 0.0568 | 0.0038 |
| 1-3 | 0.0463 | 0.0496 | 0.0032 |
| 2-0 | 0.0394 | 0.0430 | 0.0036 |
| 0-3 | 0.0375 | 0.0443 | 0.0068 |
| 2-3 | 0.0281 | 0.0284 | 0.0003 |
| 3-1 | 0.0254 | 0.0253 | 0.0001 |
| 3-2 | 0.0254 | 0.0205 | 0.0049 |
| 1-4 | 0.0192 | 0.0198 | 0.0006 |
| **Sum (top 15)** | **0.8856** | **0.9103** | — |
- High-score mass (total ≥9 goals): 2.08e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### France vs Sweden
- CS outcomes: 29  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 2-0 | 0.1137 | 0.1250 | 0.0113 |
| 1-0 | 0.0995 | 0.1049 | 0.0054 |
| 2-1 | 0.0937 | 0.0975 | 0.0038 |
| 3-0 | 0.0937 | 0.1039 | 0.0102 |
| 1-1 | 0.0758 | 0.0768 | 0.0010 |
| 3-1 | 0.0724 | 0.0783 | 0.0059 |
| 4-0 | 0.0569 | 0.0647 | 0.0078 |
| 4-1 | 0.0442 | 0.0481 | 0.0039 |
| 0-0 | 0.0419 | 0.0461 | 0.0042 |
| 2-2 | 0.0379 | 0.0355 | 0.0024 |
| 3-2 | 0.0306 | 0.0305 | 0.0001 |
| 5-0 | 0.0306 | 0.0325 | 0.0019 |
| 0-1 | 0.0284 | 0.0319 | 0.0035 |
| 1-2 | 0.0284 | 0.0288 | 0.0004 |
| 5-1 | 0.0257 | 0.0220 | 0.0037 |
| **Sum (top 15)** | **0.8735** | **0.9267** | — |
- High-score mass (total ≥9 goals): 2.56e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### USA vs Bosnia & Herzegovina
- CS outcomes: 26  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 2-0 | 0.1351 | 0.1358 | 0.0006 |
| 1-0 | 0.1329 | 0.1271 | 0.0058 |
| 2-1 | 0.0938 | 0.0964 | 0.0026 |
| 3-0 | 0.0886 | 0.0959 | 0.0073 |
| 1-1 | 0.0886 | 0.0901 | 0.0015 |
| 0-0 | 0.0664 | 0.0684 | 0.0019 |
| 3-1 | 0.0613 | 0.0669 | 0.0055 |
| 4-0 | 0.0469 | 0.0517 | 0.0048 |
| 0-1 | 0.0399 | 0.0423 | 0.0024 |
| 2-2 | 0.0347 | 0.0342 | 0.0005 |
| 4-1 | 0.0307 | 0.0353 | 0.0046 |
| 1-2 | 0.0285 | 0.0313 | 0.0029 |
| 3-2 | 0.0235 | 0.0241 | 0.0007 |
| 5-0 | 0.0235 | 0.0225 | 0.0009 |
| 5-1 | 0.0156 | 0.0152 | 0.0004 |
| **Sum (top 15)** | **0.9100** | **0.9372** | — |
- High-score mass (total ≥9 goals): 2.00e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Australia vs Egypt
- CS outcomes: 23  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-1 | 0.1474 | 0.1461 | 0.0013 |
| 0-1 | 0.1247 | 0.1392 | 0.0144 |
| 1-0 | 0.1081 | 0.1182 | 0.0101 |
| 0-0 | 0.1013 | 0.1337 | 0.0324 |
| 1-2 | 0.0853 | 0.0783 | 0.0071 |
| 2-1 | 0.0737 | 0.0646 | 0.0091 |
| 0-2 | 0.0676 | 0.0810 | 0.0135 |
| 2-2 | 0.0507 | 0.0378 | 0.0128 |
| 2-0 | 0.0450 | 0.0558 | 0.0107 |
| 0-3 | 0.0290 | 0.0303 | 0.0014 |
| 1-3 | 0.0290 | 0.0261 | 0.0029 |
| 3-1 | 0.0225 | 0.0176 | 0.0049 |
| 2-3 | 0.0225 | 0.0116 | 0.0109 |
| 3-0 | 0.0176 | 0.0169 | 0.0007 |
| 3-2 | 0.0176 | 0.0091 | 0.0085 |
| **Sum (top 15)** | **0.9420** | **0.9662** | — |
- High-score mass (total ≥9 goals): 5.61e-06
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Argentina vs Cabo Verde
- CS outcomes: 28  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 2-0 | 0.1384 | 0.1513 | 0.0130 |
| 3-0 | 0.1213 | 0.1309 | 0.0096 |
| 1-0 | 0.1127 | 0.1281 | 0.0154 |
| 2-1 | 0.0789 | 0.0833 | 0.0045 |
| 4-0 | 0.0751 | 0.0860 | 0.0109 |
| 3-1 | 0.0657 | 0.0717 | 0.0060 |
| 1-1 | 0.0607 | 0.0578 | 0.0029 |
| 4-1 | 0.0438 | 0.0471 | 0.0033 |
| 5-0 | 0.0438 | 0.0472 | 0.0034 |
| 0-0 | 0.0415 | 0.0432 | 0.0017 |
| 5-1 | 0.0254 | 0.0220 | 0.0034 |
| 2-2 | 0.0254 | 0.0198 | 0.0056 |
| 3-2 | 0.0219 | 0.0197 | 0.0022 |
| 6-0 | 0.0219 | 0.0209 | 0.0011 |
| 0-1 | 0.0219 | 0.0243 | 0.0024 |
| **Sum (top 15)** | **0.8984** | **0.9533** | — |
- High-score mass (total ≥9 goals): 2.40e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS
