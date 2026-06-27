# Correct-Score Reconciliation Audit

**Generated**: 2026-06-27T23:41:17Z

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
- CS outcomes: 28  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 0-2 | 0.1393 | 0.1436 | 0.0043 |
| 0-3 | 0.1323 | 0.1394 | 0.0071 |
| 0-1 | 0.0934 | 0.1001 | 0.0067 |
| 0-4 | 0.0934 | 0.0955 | 0.0021 |
| 1-3 | 0.0662 | 0.0748 | 0.0086 |
| 1-2 | 0.0611 | 0.0812 | 0.0201 |
| 0-5 | 0.0567 | 0.0563 | 0.0004 |
| 1-1 | 0.0467 | 0.0525 | 0.0058 |
| 1-4 | 0.0467 | 0.0558 | 0.0091 |
| 0-0 | 0.0397 | 0.0335 | 0.0062 |
| 0-6 | 0.0305 | 0.0223 | 0.0083 |
| 1-5 | 0.0256 | 0.0223 | 0.0033 |
| 1-0 | 0.0221 | 0.0198 | 0.0023 |
| 2-2 | 0.0173 | 0.0215 | 0.0042 |
| 2-3 | 0.0173 | 0.0237 | 0.0065 |
| **Sum (top 15)** | **0.8882** | **0.9421** | — |
- High-score mass (total ≥9 goals): 3.10e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Algeria vs Austria
- CS outcomes: 18  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 0-1 | 0.1953 | 0.1246 | 0.0707 |
| 1-1 | 0.1803 | 0.1926 | 0.0123 |
| 1-0 | 0.1339 | 0.1181 | 0.0158 |
| 0-2 | 0.0987 | 0.0745 | 0.0241 |
| 1-2 | 0.0852 | 0.0468 | 0.0384 |
| 2-1 | 0.0551 | 0.0511 | 0.0040 |
| 2-0 | 0.0469 | 0.0743 | 0.0274 |
| 2-2 | 0.0446 | 0.0213 | 0.0233 |
| 0-3 | 0.0408 | 0.0133 | 0.0275 |
| 1-3 | 0.0302 | 0.0066 | 0.0237 |
| 3-1 | 0.0184 | 0.0088 | 0.0096 |
| 3-0 | 0.0154 | 0.0164 | 0.0010 |
| 2-3 | 0.0142 | 0.0015 | 0.0127 |
| 0-4 | 0.0116 | 0.0014 | 0.0102 |
| 3-2 | 0.0093 | 0.0021 | 0.0072 |
| **Sum (top 15)** | **0.9798** | **0.7535** | — |
- High-score mass (total ≥9 goals): 9.94e-08
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### South Africa vs Canada
- CS outcomes: 25  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 0-1 | 0.1429 | 0.1405 | 0.0024 |
| 1-1 | 0.1231 | 0.1233 | 0.0003 |
| 0-2 | 0.1067 | 0.1163 | 0.0096 |
| 1-2 | 0.1000 | 0.0953 | 0.0047 |
| 0-0 | 0.0842 | 0.0996 | 0.0154 |
| 1-0 | 0.0615 | 0.0693 | 0.0077 |
| 0-3 | 0.0571 | 0.0628 | 0.0057 |
| 2-2 | 0.0471 | 0.0392 | 0.0078 |
| 1-3 | 0.0471 | 0.0493 | 0.0023 |
| 2-1 | 0.0444 | 0.0446 | 0.0002 |
| 2-0 | 0.0258 | 0.0289 | 0.0031 |
| 2-3 | 0.0258 | 0.0203 | 0.0055 |
| 0-4 | 0.0258 | 0.0262 | 0.0004 |
| 1-4 | 0.0222 | 0.0203 | 0.0019 |
| 3-2 | 0.0131 | 0.0093 | 0.0038 |
| **Sum (top 15)** | **0.9268** | **0.9454** | — |
- High-score mass (total ≥9 goals): 1.38e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Brazil vs Japan
- CS outcomes: 27  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-0 | 0.1232 | 0.1243 | 0.0011 |
| 2-0 | 0.1068 | 0.1121 | 0.0053 |
| 1-1 | 0.1068 | 0.1131 | 0.0063 |
| 2-1 | 0.0942 | 0.0965 | 0.0023 |
| 0-0 | 0.0728 | 0.0833 | 0.0105 |
| 3-0 | 0.0616 | 0.0657 | 0.0040 |
| 0-1 | 0.0616 | 0.0645 | 0.0029 |
| 3-1 | 0.0534 | 0.0562 | 0.0028 |
| 1-2 | 0.0471 | 0.0483 | 0.0012 |
| 2-2 | 0.0445 | 0.0444 | 0.0001 |
| 3-2 | 0.0286 | 0.0256 | 0.0030 |
| 4-0 | 0.0286 | 0.0291 | 0.0004 |
| 0-2 | 0.0286 | 0.0292 | 0.0006 |
| 4-1 | 0.0258 | 0.0249 | 0.0009 |
| 1-3 | 0.0157 | 0.0141 | 0.0016 |
| **Sum (top 15)** | **0.8996** | **0.9315** | — |
- High-score mass (total ≥9 goals): 1.76e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Germany vs Paraguay
- CS outcomes: 27  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 2-0 | 0.1223 | 0.1289 | 0.0065 |
| 1-0 | 0.1136 | 0.1134 | 0.0002 |
| 2-1 | 0.0935 | 0.0974 | 0.0039 |
| 3-0 | 0.0883 | 0.0965 | 0.0081 |
| 1-1 | 0.0837 | 0.0877 | 0.0041 |
| 3-1 | 0.0723 | 0.0735 | 0.0012 |
| 0-0 | 0.0530 | 0.0596 | 0.0066 |
| 4-0 | 0.0468 | 0.0540 | 0.0073 |
| 4-1 | 0.0379 | 0.0403 | 0.0025 |
| 2-2 | 0.0379 | 0.0368 | 0.0010 |
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
- CS outcomes: 26  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-1 | 0.1331 | 0.1356 | 0.0025 |
| 1-0 | 0.1229 | 0.1204 | 0.0024 |
| 2-1 | 0.0940 | 0.0901 | 0.0039 |
| 0-0 | 0.0887 | 0.1040 | 0.0153 |
| 0-1 | 0.0799 | 0.0852 | 0.0053 |
| 2-0 | 0.0761 | 0.0873 | 0.0112 |
| 1-2 | 0.0614 | 0.0621 | 0.0007 |
| 2-2 | 0.0532 | 0.0479 | 0.0053 |
| 3-1 | 0.0420 | 0.0417 | 0.0003 |
| 3-0 | 0.0380 | 0.0419 | 0.0038 |
| 0-2 | 0.0380 | 0.0449 | 0.0069 |
| 3-2 | 0.0258 | 0.0213 | 0.0045 |
| 1-3 | 0.0222 | 0.0207 | 0.0015 |
| 2-3 | 0.0195 | 0.0148 | 0.0047 |
| 4-0 | 0.0157 | 0.0151 | 0.0006 |
| **Sum (top 15)** | **0.9105** | **0.9330** | — |
- High-score mass (total ≥9 goals): 1.46e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Côte d'Ivoire vs Norway
- CS outcomes: 27  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-1 | 0.1223 | 0.1260 | 0.0037 |
| 0-1 | 0.0994 | 0.0997 | 0.0003 |
| 1-2 | 0.0935 | 0.0945 | 0.0010 |
| 1-0 | 0.0723 | 0.0725 | 0.0003 |
| 2-1 | 0.0723 | 0.0683 | 0.0039 |
| 0-2 | 0.0723 | 0.0827 | 0.0104 |
| 0-0 | 0.0662 | 0.0800 | 0.0138 |
| 2-2 | 0.0611 | 0.0572 | 0.0040 |
| 1-3 | 0.0442 | 0.0489 | 0.0048 |
| 2-0 | 0.0378 | 0.0428 | 0.0049 |
| 0-3 | 0.0378 | 0.0444 | 0.0065 |
| 2-3 | 0.0306 | 0.0288 | 0.0018 |
| 3-1 | 0.0256 | 0.0250 | 0.0006 |
| 3-2 | 0.0256 | 0.0202 | 0.0054 |
| 1-4 | 0.0194 | 0.0198 | 0.0004 |
| **Sum (top 15)** | **0.8804** | **0.9108** | — |
- High-score mass (total ≥9 goals): 2.08e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### France vs Sweden
- CS outcomes: 29  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 2-0 | 0.1137 | 0.1250 | 0.0112 |
| 1-0 | 0.0995 | 0.1042 | 0.0046 |
| 2-1 | 0.0937 | 0.0975 | 0.0038 |
| 3-0 | 0.0937 | 0.1039 | 0.0102 |
| 1-1 | 0.0758 | 0.0772 | 0.0014 |
| 3-1 | 0.0724 | 0.0783 | 0.0059 |
| 4-0 | 0.0569 | 0.0646 | 0.0078 |
| 4-1 | 0.0442 | 0.0481 | 0.0038 |
| 0-0 | 0.0419 | 0.0466 | 0.0047 |
| 2-2 | 0.0379 | 0.0357 | 0.0022 |
| 3-2 | 0.0306 | 0.0305 | 0.0002 |
| 5-0 | 0.0306 | 0.0325 | 0.0019 |
| 0-1 | 0.0284 | 0.0318 | 0.0034 |
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
| 2-0 | 0.1351 | 0.1360 | 0.0008 |
| 1-0 | 0.1329 | 0.1270 | 0.0059 |
| 2-1 | 0.0938 | 0.0963 | 0.0025 |
| 3-0 | 0.0886 | 0.0958 | 0.0072 |
| 1-1 | 0.0886 | 0.0907 | 0.0021 |
| 0-0 | 0.0664 | 0.0692 | 0.0028 |
| 3-1 | 0.0613 | 0.0666 | 0.0053 |
| 4-0 | 0.0469 | 0.0516 | 0.0047 |
| 0-1 | 0.0399 | 0.0424 | 0.0026 |
| 2-2 | 0.0347 | 0.0342 | 0.0005 |
| 4-1 | 0.0307 | 0.0351 | 0.0044 |
| 1-2 | 0.0285 | 0.0313 | 0.0028 |
| 3-2 | 0.0235 | 0.0240 | 0.0005 |
| 5-0 | 0.0235 | 0.0224 | 0.0011 |
| 5-1 | 0.0156 | 0.0150 | 0.0006 |
| **Sum (top 15)** | **0.9100** | **0.9375** | — |
- High-score mass (total ≥9 goals): 1.99e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Australia vs Egypt
- CS outcomes: 23  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-1 | 0.1474 | 0.1448 | 0.0026 |
| 0-1 | 0.1247 | 0.1394 | 0.0147 |
| 1-0 | 0.1081 | 0.1185 | 0.0104 |
| 0-0 | 0.1013 | 0.1325 | 0.0311 |
| 1-2 | 0.0853 | 0.0784 | 0.0070 |
| 2-1 | 0.0737 | 0.0648 | 0.0089 |
| 0-2 | 0.0676 | 0.0805 | 0.0130 |
| 2-2 | 0.0507 | 0.0380 | 0.0127 |
| 2-0 | 0.0450 | 0.0556 | 0.0105 |
| 0-3 | 0.0290 | 0.0304 | 0.0014 |
| 1-3 | 0.0290 | 0.0264 | 0.0025 |
| 3-1 | 0.0225 | 0.0179 | 0.0046 |
| 2-3 | 0.0225 | 0.0119 | 0.0106 |
| 3-0 | 0.0176 | 0.0170 | 0.0006 |
| 3-2 | 0.0176 | 0.0094 | 0.0082 |
| **Sum (top 15)** | **0.9420** | **0.9654** | — |
- High-score mass (total ≥9 goals): 5.94e-06
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Argentina vs Cabo Verde
- CS outcomes: 28  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 2-0 | 0.1384 | 0.1513 | 0.0129 |
| 3-0 | 0.1213 | 0.1310 | 0.0096 |
| 1-0 | 0.1127 | 0.1280 | 0.0154 |
| 2-1 | 0.0789 | 0.0833 | 0.0045 |
| 4-0 | 0.0751 | 0.0859 | 0.0108 |
| 3-1 | 0.0657 | 0.0717 | 0.0060 |
| 1-1 | 0.0607 | 0.0577 | 0.0029 |
| 4-1 | 0.0438 | 0.0472 | 0.0034 |
| 5-0 | 0.0438 | 0.0472 | 0.0034 |
| 0-0 | 0.0415 | 0.0432 | 0.0017 |
| 5-1 | 0.0254 | 0.0220 | 0.0034 |
| 2-2 | 0.0254 | 0.0198 | 0.0057 |
| 3-2 | 0.0219 | 0.0197 | 0.0022 |
| 6-0 | 0.0219 | 0.0209 | 0.0010 |
| 0-1 | 0.0219 | 0.0243 | 0.0024 |
| **Sum (top 15)** | **0.8984** | **0.9532** | — |
- High-score mass (total ≥9 goals): 2.41e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS
