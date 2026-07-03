# Correct-Score Reconciliation Audit

**Generated**: 2026-07-03T01:05:48Z

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

### Switzerland vs Algeria
- CS outcomes: 27  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-0 | 0.1332 | 0.1216 | 0.0115 |
| 1-1 | 0.1332 | 0.1348 | 0.0016 |
| 2-1 | 0.0999 | 0.0947 | 0.0051 |
| 2-0 | 0.0841 | 0.0944 | 0.0104 |
| 0-0 | 0.0841 | 0.1011 | 0.0170 |
| 0-1 | 0.0726 | 0.0752 | 0.0026 |
| 2-2 | 0.0571 | 0.0490 | 0.0081 |
| 1-2 | 0.0571 | 0.0572 | 0.0001 |
| 3-1 | 0.0420 | 0.0456 | 0.0035 |
| 3-0 | 0.0399 | 0.0482 | 0.0082 |
| 0-2 | 0.0307 | 0.0373 | 0.0066 |
| 3-2 | 0.0285 | 0.0227 | 0.0058 |
| 4-0 | 0.0174 | 0.0190 | 0.0016 |
| 1-3 | 0.0174 | 0.0175 | 0.0002 |
| 2-3 | 0.0174 | 0.0136 | 0.0038 |
| **Sum (top 15)** | **0.9145** | **0.9320** | — |
- High-score mass (total ≥9 goals): 1.55e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Australia vs Egypt
- CS outcomes: 22  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-1 | 0.1459 | 0.1474 | 0.0015 |
| 0-1 | 0.1409 | 0.1429 | 0.0020 |
| 0-0 | 0.1257 | 0.1442 | 0.0185 |
| 1-0 | 0.1089 | 0.1154 | 0.0064 |
| 1-2 | 0.0778 | 0.0751 | 0.0027 |
| 2-1 | 0.0681 | 0.0626 | 0.0054 |
| 0-2 | 0.0681 | 0.0831 | 0.0150 |
| 2-0 | 0.0454 | 0.0569 | 0.0115 |
| 2-2 | 0.0454 | 0.0352 | 0.0102 |
| 0-3 | 0.0292 | 0.0305 | 0.0013 |
| 1-3 | 0.0292 | 0.0251 | 0.0041 |
| 3-1 | 0.0199 | 0.0164 | 0.0035 |
| 2-3 | 0.0178 | 0.0102 | 0.0076 |
| 3-2 | 0.0160 | 0.0082 | 0.0078 |
| 3-0 | 0.0146 | 0.0162 | 0.0016 |
| **Sum (top 15)** | **0.9528** | **0.9693** | — |
- High-score mass (total ≥9 goals): 4.45e-06
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Argentina vs Cabo Verde
- CS outcomes: 25  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 2-0 | 0.1521 | 0.1558 | 0.0037 |
| 3-0 | 0.1344 | 0.1368 | 0.0024 |
| 1-0 | 0.1075 | 0.1212 | 0.0137 |
| 4-0 | 0.0949 | 0.0935 | 0.0014 |
| 2-1 | 0.0672 | 0.0776 | 0.0104 |
| 3-1 | 0.0620 | 0.0691 | 0.0071 |
| 5-0 | 0.0504 | 0.0491 | 0.0013 |
| 1-1 | 0.0504 | 0.0559 | 0.0055 |
| 0-0 | 0.0448 | 0.0460 | 0.0012 |
| 4-1 | 0.0424 | 0.0460 | 0.0035 |
| 6-0 | 0.0260 | 0.0216 | 0.0044 |
| 0-1 | 0.0260 | 0.0241 | 0.0019 |
| 5-1 | 0.0237 | 0.0220 | 0.0017 |
| 2-2 | 0.0175 | 0.0190 | 0.0015 |
| 3-2 | 0.0158 | 0.0180 | 0.0022 |
| **Sum (top 15)** | **0.9151** | **0.9558** | — |
- High-score mass (total ≥9 goals): 2.40e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Colombia vs Ghana
- CS outcomes: 24  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-0 | 0.1502 | 0.1526 | 0.0024 |
| 2-0 | 0.1351 | 0.1437 | 0.0086 |
| 1-1 | 0.1014 | 0.1015 | 0.0002 |
| 2-1 | 0.0954 | 0.0933 | 0.0021 |
| 0-0 | 0.0811 | 0.0908 | 0.0097 |
| 3-0 | 0.0772 | 0.0865 | 0.0093 |
| 3-1 | 0.0579 | 0.0573 | 0.0006 |
| 0-1 | 0.0477 | 0.0532 | 0.0055 |
| 4-0 | 0.0386 | 0.0418 | 0.0032 |
| 2-2 | 0.0353 | 0.0288 | 0.0064 |
| 1-2 | 0.0312 | 0.0298 | 0.0014 |
| 4-1 | 0.0262 | 0.0261 | 0.0000 |
| 3-2 | 0.0238 | 0.0184 | 0.0055 |
| 5-0 | 0.0176 | 0.0159 | 0.0018 |
| 0-2 | 0.0159 | 0.0170 | 0.0011 |
| **Sum (top 15)** | **0.9346** | **0.9567** | — |
- High-score mass (total ≥9 goals): 1.51e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Canada vs Morocco
- CS outcomes: 25  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 0-1 | 0.1369 | 0.1354 | 0.0015 |
| 1-1 | 0.1243 | 0.1270 | 0.0027 |
| 0-2 | 0.1077 | 0.1138 | 0.0060 |
| 1-2 | 0.0951 | 0.0929 | 0.0021 |
| 0-0 | 0.0898 | 0.1053 | 0.0155 |
| 1-0 | 0.0673 | 0.0725 | 0.0052 |
| 0-3 | 0.0539 | 0.0591 | 0.0052 |
| 2-1 | 0.0475 | 0.0471 | 0.0005 |
| 1-3 | 0.0475 | 0.0481 | 0.0005 |
| 2-2 | 0.0425 | 0.0397 | 0.0028 |
| 2-0 | 0.0289 | 0.0311 | 0.0023 |
| 2-3 | 0.0261 | 0.0202 | 0.0059 |
| 0-4 | 0.0238 | 0.0238 | 0.0001 |
| 1-4 | 0.0224 | 0.0192 | 0.0033 |
| 3-1 | 0.0144 | 0.0125 | 0.0020 |
| **Sum (top 15)** | **0.9282** | **0.9477** | — |
- High-score mass (total ≥9 goals): 1.35e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Paraguay vs France
- CS outcomes: 27  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 0-2 | 0.1468 | 0.1515 | 0.0047 |
| 0-3 | 0.1242 | 0.1309 | 0.0067 |
| 0-1 | 0.1153 | 0.1195 | 0.0042 |
| 0-4 | 0.0807 | 0.0862 | 0.0054 |
| 1-2 | 0.0734 | 0.0818 | 0.0084 |
| 1-3 | 0.0673 | 0.0718 | 0.0045 |
| 1-1 | 0.0538 | 0.0606 | 0.0068 |
| 0-0 | 0.0449 | 0.0489 | 0.0040 |
| 0-5 | 0.0449 | 0.0458 | 0.0009 |
| 1-4 | 0.0425 | 0.0461 | 0.0036 |
| 1-0 | 0.0237 | 0.0248 | 0.0011 |
| 1-5 | 0.0237 | 0.0220 | 0.0018 |
| 2-2 | 0.0224 | 0.0216 | 0.0008 |
| 0-6 | 0.0224 | 0.0198 | 0.0026 |
| 2-3 | 0.0197 | 0.0196 | 0.0001 |
| **Sum (top 15)** | **0.9059** | **0.9511** | — |
- High-score mass (total ≥9 goals): 2.37e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Brazil vs Norway
- CS outcomes: 30  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-1 | 0.1126 | 0.1177 | 0.0051 |
| 1-0 | 0.0985 | 0.0925 | 0.0060 |
| 2-1 | 0.0985 | 0.0994 | 0.0009 |
| 2-0 | 0.0750 | 0.0864 | 0.0114 |
| 2-2 | 0.0657 | 0.0603 | 0.0054 |
| 1-2 | 0.0606 | 0.0620 | 0.0013 |
| 3-1 | 0.0563 | 0.0591 | 0.0028 |
| 0-0 | 0.0525 | 0.0682 | 0.0157 |
| 0-1 | 0.0525 | 0.0574 | 0.0049 |
| 3-0 | 0.0464 | 0.0534 | 0.0070 |
| 3-2 | 0.0375 | 0.0343 | 0.0032 |
| 0-2 | 0.0303 | 0.0350 | 0.0047 |
| 4-1 | 0.0254 | 0.0265 | 0.0011 |
| 2-3 | 0.0254 | 0.0210 | 0.0044 |
| 4-0 | 0.0219 | 0.0244 | 0.0025 |
| **Sum (top 15)** | **0.8592** | **0.8976** | — |
- High-score mass (total ≥9 goals): 2.43e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Mexico vs England
- CS outcomes: 25  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-1 | 0.1335 | 0.1405 | 0.0069 |
| 0-1 | 0.1144 | 0.1218 | 0.0074 |
| 1-0 | 0.1001 | 0.1054 | 0.0052 |
| 0-0 | 0.0942 | 0.1165 | 0.0223 |
| 1-2 | 0.0801 | 0.0795 | 0.0007 |
| 2-1 | 0.0728 | 0.0680 | 0.0048 |
| 0-2 | 0.0728 | 0.0778 | 0.0049 |
| 2-0 | 0.0534 | 0.0570 | 0.0036 |
| 2-2 | 0.0471 | 0.0406 | 0.0065 |
| 1-3 | 0.0348 | 0.0316 | 0.0032 |
| 0-3 | 0.0308 | 0.0309 | 0.0001 |
| 3-1 | 0.0258 | 0.0232 | 0.0027 |
| 3-0 | 0.0223 | 0.0194 | 0.0028 |
| 2-3 | 0.0223 | 0.0161 | 0.0061 |
| 3-2 | 0.0195 | 0.0138 | 0.0057 |
| **Sum (top 15)** | **0.9242** | **0.9421** | — |
- High-score mass (total ≥9 goals): 2.90e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### USA vs Belgium
- CS outcomes: 31  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-1 | 0.1211 | 0.1275 | 0.0064 |
| 2-1 | 0.0828 | 0.0842 | 0.0013 |
| 1-0 | 0.0787 | 0.0760 | 0.0027 |
| 1-2 | 0.0787 | 0.0829 | 0.0042 |
| 2-2 | 0.0715 | 0.0665 | 0.0051 |
| 0-1 | 0.0715 | 0.0739 | 0.0023 |
| 0-0 | 0.0562 | 0.0740 | 0.0178 |
| 2-0 | 0.0525 | 0.0597 | 0.0072 |
| 0-2 | 0.0492 | 0.0583 | 0.0091 |
| 3-1 | 0.0394 | 0.0405 | 0.0012 |
| 1-3 | 0.0375 | 0.0398 | 0.0024 |
| 3-2 | 0.0342 | 0.0297 | 0.0045 |
| 2-3 | 0.0342 | 0.0298 | 0.0044 |
| 3-0 | 0.0254 | 0.0290 | 0.0036 |
| 0-3 | 0.0254 | 0.0286 | 0.0032 |
| **Sum (top 15)** | **0.8583** | **0.9003** | — |
- High-score mass (total ≥9 goals): 2.46e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS
