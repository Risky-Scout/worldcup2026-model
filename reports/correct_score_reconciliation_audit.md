# Correct-Score Reconciliation Audit

**Generated**: 2026-07-01T00:03:18Z

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
| Total 2026 matches predicted | 13 |
| Matches with any CS data | 12 |
| Matches with 1 CS vendor | 12 |
| Matches with 2+ CS vendors | 0 |

## Per-match correct-score audit

### Mexico vs Ecuador
- CS outcomes: 21  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-0 | 0.1606 | 0.1567 | 0.0039 |
| 1-1 | 0.1437 | 0.1459 | 0.0022 |
| 0-0 | 0.1365 | 0.1504 | 0.0139 |
| 0-1 | 0.1024 | 0.1046 | 0.0022 |
| 2-0 | 0.0819 | 0.0981 | 0.0162 |
| 2-1 | 0.0819 | 0.0785 | 0.0034 |
| 1-2 | 0.0546 | 0.0524 | 0.0022 |
| 2-2 | 0.0431 | 0.0320 | 0.0111 |
| 0-2 | 0.0390 | 0.0470 | 0.0080 |
| 3-0 | 0.0315 | 0.0374 | 0.0059 |
| 3-1 | 0.0292 | 0.0271 | 0.0021 |
| 3-2 | 0.0178 | 0.0097 | 0.0081 |
| 1-3 | 0.0134 | 0.0118 | 0.0016 |
| 2-3 | 0.0115 | 0.0062 | 0.0053 |
| 0-3 | 0.0108 | 0.0113 | 0.0005 |
| **Sum (top 15)** | **0.9579** | **0.9690** | — |
- High-score mass (total ≥9 goals): 4.22e-06
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### England vs DR Congo
- CS outcomes: 24  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-0 | 0.1554 | 0.1515 | 0.0040 |
| 2-0 | 0.1497 | 0.1583 | 0.0086 |
| 3-0 | 0.1078 | 0.1142 | 0.0064 |
| 2-1 | 0.0898 | 0.0876 | 0.0022 |
| 1-1 | 0.0770 | 0.0803 | 0.0033 |
| 0-0 | 0.0674 | 0.0764 | 0.0090 |
| 3-1 | 0.0622 | 0.0619 | 0.0003 |
| 4-0 | 0.0577 | 0.0627 | 0.0049 |
| 4-1 | 0.0311 | 0.0324 | 0.0013 |
| 0-1 | 0.0311 | 0.0365 | 0.0054 |
| 5-0 | 0.0261 | 0.0274 | 0.0014 |
| 2-2 | 0.0261 | 0.0217 | 0.0044 |
| 3-2 | 0.0197 | 0.0160 | 0.0037 |
| 1-2 | 0.0197 | 0.0194 | 0.0003 |
| 5-1 | 0.0158 | 0.0139 | 0.0019 |
| **Sum (top 15)** | **0.9366** | **0.9603** | — |
- High-score mass (total ≥9 goals): 1.78e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Belgium vs Senegal
- CS outcomes: 27  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-1 | 0.1332 | 0.1364 | 0.0032 |
| 1-0 | 0.1065 | 0.1062 | 0.0003 |
| 2-1 | 0.0999 | 0.0929 | 0.0070 |
| 2-0 | 0.0726 | 0.0829 | 0.0102 |
| 0-0 | 0.0726 | 0.0930 | 0.0204 |
| 0-1 | 0.0726 | 0.0799 | 0.0072 |
| 1-2 | 0.0666 | 0.0669 | 0.0003 |
| 2-2 | 0.0615 | 0.0538 | 0.0077 |
| 3-1 | 0.0421 | 0.0430 | 0.0010 |
| 3-0 | 0.0381 | 0.0406 | 0.0025 |
| 0-2 | 0.0347 | 0.0460 | 0.0113 |
| 3-2 | 0.0307 | 0.0243 | 0.0064 |
| 1-3 | 0.0258 | 0.0242 | 0.0016 |
| 2-3 | 0.0222 | 0.0178 | 0.0044 |
| 4-1 | 0.0157 | 0.0156 | 0.0001 |
| **Sum (top 15)** | **0.8948** | **0.9235** | — |
- High-score mass (total ≥9 goals): 1.71e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### USA vs Bosnia & Herzegovina
- CS outcomes: 26  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 2-0 | 0.1330 | 0.1338 | 0.0008 |
| 1-0 | 0.1227 | 0.1219 | 0.0008 |
| 3-0 | 0.0939 | 0.0964 | 0.0026 |
| 2-1 | 0.0886 | 0.0945 | 0.0059 |
| 1-1 | 0.0840 | 0.0899 | 0.0059 |
| 3-1 | 0.0665 | 0.0687 | 0.0022 |
| 0-0 | 0.0614 | 0.0665 | 0.0052 |
| 4-0 | 0.0499 | 0.0516 | 0.0017 |
| 0-1 | 0.0420 | 0.0432 | 0.0012 |
| 4-1 | 0.0347 | 0.0363 | 0.0017 |
| 2-2 | 0.0347 | 0.0356 | 0.0009 |
| 1-2 | 0.0285 | 0.0321 | 0.0036 |
| 3-2 | 0.0257 | 0.0253 | 0.0004 |
| 5-0 | 0.0235 | 0.0221 | 0.0014 |
| 5-1 | 0.0173 | 0.0155 | 0.0018 |
| **Sum (top 15)** | **0.9062** | **0.9335** | — |
- High-score mass (total ≥9 goals): 2.05e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Spain vs Austria
- CS outcomes: 26  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 2-0 | 0.1383 | 0.1422 | 0.0039 |
| 1-0 | 0.1337 | 0.1312 | 0.0025 |
| 2-1 | 0.0944 | 0.0951 | 0.0007 |
| 3-0 | 0.0944 | 0.1031 | 0.0087 |
| 1-1 | 0.0802 | 0.0839 | 0.0037 |
| 3-1 | 0.0617 | 0.0673 | 0.0055 |
| 0-0 | 0.0617 | 0.0660 | 0.0043 |
| 4-0 | 0.0501 | 0.0572 | 0.0070 |
| 0-1 | 0.0382 | 0.0391 | 0.0009 |
| 4-1 | 0.0349 | 0.0372 | 0.0023 |
| 2-2 | 0.0309 | 0.0302 | 0.0007 |
| 3-2 | 0.0259 | 0.0228 | 0.0030 |
| 5-0 | 0.0259 | 0.0260 | 0.0001 |
| 1-2 | 0.0259 | 0.0268 | 0.0009 |
| 5-1 | 0.0157 | 0.0161 | 0.0004 |
| **Sum (top 15)** | **0.9120** | **0.9441** | — |
- High-score mass (total ≥9 goals): 2.02e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Portugal vs Croatia
- CS outcomes: 25  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-0 | 0.1329 | 0.1242 | 0.0087 |
| 1-1 | 0.1227 | 0.1258 | 0.0031 |
| 2-1 | 0.0997 | 0.0972 | 0.0025 |
| 2-0 | 0.0938 | 0.1047 | 0.0108 |
| 0-0 | 0.0725 | 0.0913 | 0.0188 |
| 0-1 | 0.0664 | 0.0674 | 0.0009 |
| 2-2 | 0.0532 | 0.0468 | 0.0064 |
| 3-0 | 0.0498 | 0.0585 | 0.0086 |
| 3-1 | 0.0498 | 0.0523 | 0.0025 |
| 1-2 | 0.0498 | 0.0502 | 0.0004 |
| 3-2 | 0.0285 | 0.0241 | 0.0044 |
| 0-2 | 0.0285 | 0.0311 | 0.0026 |
| 4-0 | 0.0257 | 0.0256 | 0.0002 |
| 4-1 | 0.0221 | 0.0219 | 0.0002 |
| 1-3 | 0.0173 | 0.0147 | 0.0026 |
| **Sum (top 15)** | **0.9128** | **0.9357** | — |
- High-score mass (total ≥9 goals): 1.65e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Switzerland vs Algeria
- CS outcomes: 26  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-1 | 0.1326 | 0.1360 | 0.0034 |
| 1-0 | 0.1224 | 0.1158 | 0.0066 |
| 2-1 | 0.0936 | 0.0920 | 0.0016 |
| 2-0 | 0.0795 | 0.0897 | 0.0101 |
| 0-0 | 0.0795 | 0.0989 | 0.0193 |
| 0-1 | 0.0758 | 0.0777 | 0.0020 |
| 1-2 | 0.0663 | 0.0623 | 0.0040 |
| 2-2 | 0.0568 | 0.0509 | 0.0060 |
| 3-1 | 0.0398 | 0.0440 | 0.0042 |
| 3-0 | 0.0379 | 0.0447 | 0.0068 |
| 0-2 | 0.0379 | 0.0417 | 0.0038 |
| 3-2 | 0.0284 | 0.0233 | 0.0051 |
| 1-3 | 0.0221 | 0.0201 | 0.0020 |
| 2-3 | 0.0194 | 0.0150 | 0.0044 |
| 4-0 | 0.0173 | 0.0172 | 0.0001 |
| **Sum (top 15)** | **0.9092** | **0.9291** | — |
- High-score mass (total ≥9 goals): 1.62e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Australia vs Egypt
- CS outcomes: 22  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-1 | 0.1454 | 0.1469 | 0.0015 |
| 0-1 | 0.1380 | 0.1415 | 0.0036 |
| 0-0 | 0.1253 | 0.1434 | 0.0181 |
| 1-0 | 0.1086 | 0.1152 | 0.0066 |
| 1-2 | 0.0814 | 0.0765 | 0.0049 |
| 2-1 | 0.0678 | 0.0627 | 0.0051 |
| 0-2 | 0.0678 | 0.0830 | 0.0151 |
| 2-2 | 0.0479 | 0.0358 | 0.0121 |
| 2-0 | 0.0452 | 0.0569 | 0.0117 |
| 1-3 | 0.0291 | 0.0252 | 0.0039 |
| 0-3 | 0.0263 | 0.0300 | 0.0037 |
| 3-1 | 0.0226 | 0.0168 | 0.0058 |
| 3-0 | 0.0177 | 0.0167 | 0.0010 |
| 2-3 | 0.0177 | 0.0103 | 0.0074 |
| 3-2 | 0.0145 | 0.0082 | 0.0063 |
| **Sum (top 15)** | **0.9553** | **0.9692** | — |
- High-score mass (total ≥9 goals): 4.53e-06
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Argentina vs Cabo Verde
- CS outcomes: 25  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 2-0 | 0.1596 | 0.1607 | 0.0011 |
| 3-0 | 0.1356 | 0.1346 | 0.0011 |
| 1-0 | 0.1163 | 0.1309 | 0.0146 |
| 4-0 | 0.0904 | 0.0872 | 0.0032 |
| 2-1 | 0.0678 | 0.0779 | 0.0101 |
| 3-1 | 0.0581 | 0.0660 | 0.0079 |
| 0-0 | 0.0509 | 0.0506 | 0.0003 |
| 1-1 | 0.0509 | 0.0579 | 0.0070 |
| 5-0 | 0.0479 | 0.0441 | 0.0038 |
| 4-1 | 0.0388 | 0.0423 | 0.0036 |
| 0-1 | 0.0263 | 0.0267 | 0.0004 |
| 6-0 | 0.0239 | 0.0184 | 0.0055 |
| 5-1 | 0.0226 | 0.0215 | 0.0011 |
| 2-2 | 0.0177 | 0.0191 | 0.0014 |
| 3-2 | 0.0160 | 0.0174 | 0.0014 |
| **Sum (top 15)** | **0.9227** | **0.9553** | — |
- High-score mass (total ≥9 goals): 2.24e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Colombia vs Ghana
- CS outcomes: 25  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-0 | 0.1556 | 0.1508 | 0.0048 |
| 2-0 | 0.1323 | 0.1379 | 0.0056 |
| 1-1 | 0.1058 | 0.1078 | 0.0020 |
| 2-1 | 0.0934 | 0.0923 | 0.0011 |
| 0-0 | 0.0882 | 0.0974 | 0.0092 |
| 3-0 | 0.0721 | 0.0796 | 0.0075 |
| 0-1 | 0.0529 | 0.0577 | 0.0048 |
| 3-1 | 0.0496 | 0.0535 | 0.0039 |
| 4-0 | 0.0345 | 0.0373 | 0.0028 |
| 2-2 | 0.0345 | 0.0313 | 0.0032 |
| 1-2 | 0.0345 | 0.0340 | 0.0005 |
| 3-2 | 0.0220 | 0.0190 | 0.0031 |
| 4-1 | 0.0220 | 0.0240 | 0.0020 |
| 0-2 | 0.0194 | 0.0193 | 0.0001 |
| 5-0 | 0.0142 | 0.0134 | 0.0008 |
| **Sum (top 15)** | **0.9309** | **0.9552** | — |
- High-score mass (total ≥9 goals): 1.45e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Canada vs Morocco
- CS outcomes: 25  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 0-1 | 0.1358 | 0.1330 | 0.0029 |
| 1-1 | 0.1164 | 0.1235 | 0.0071 |
| 0-2 | 0.1087 | 0.1108 | 0.0021 |
| 0-0 | 0.0906 | 0.1039 | 0.0134 |
| 1-2 | 0.0906 | 0.0913 | 0.0007 |
| 1-0 | 0.0679 | 0.0747 | 0.0068 |
| 0-3 | 0.0627 | 0.0594 | 0.0033 |
| 1-3 | 0.0479 | 0.0482 | 0.0003 |
| 2-1 | 0.0453 | 0.0488 | 0.0035 |
| 2-2 | 0.0407 | 0.0414 | 0.0007 |
| 2-0 | 0.0291 | 0.0327 | 0.0036 |
| 0-4 | 0.0291 | 0.0238 | 0.0053 |
| 2-3 | 0.0226 | 0.0203 | 0.0023 |
| 1-4 | 0.0226 | 0.0190 | 0.0037 |
| 3-1 | 0.0146 | 0.0139 | 0.0006 |
| **Sum (top 15)** | **0.9246** | **0.9447** | — |
- High-score mass (total ≥9 goals): 1.41e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Paraguay vs France
- CS outcomes: 0  |  CS vendors: 0  |  Publish mode: market_reconciled
- No correct-score data available for this match.

### Brazil vs Norway
- CS outcomes: 27  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-1 | 0.1226 | 0.1238 | 0.0012 |
| 1-0 | 0.1063 | 0.1053 | 0.0010 |
| 2-1 | 0.0997 | 0.0987 | 0.0010 |
| 2-0 | 0.0797 | 0.0914 | 0.0116 |
| 0-0 | 0.0664 | 0.0795 | 0.0130 |
| 0-1 | 0.0664 | 0.0671 | 0.0007 |
| 1-2 | 0.0613 | 0.0602 | 0.0011 |
| 2-2 | 0.0569 | 0.0535 | 0.0034 |
| 3-1 | 0.0498 | 0.0537 | 0.0039 |
| 3-0 | 0.0443 | 0.0521 | 0.0078 |
| 0-2 | 0.0347 | 0.0368 | 0.0021 |
| 3-2 | 0.0307 | 0.0289 | 0.0018 |
| 4-1 | 0.0221 | 0.0228 | 0.0006 |
| 1-3 | 0.0221 | 0.0206 | 0.0015 |
| 4-0 | 0.0194 | 0.0223 | 0.0028 |
| **Sum (top 15)** | **0.8826** | **0.9167** | — |
- High-score mass (total ≥9 goals): 1.99e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS
