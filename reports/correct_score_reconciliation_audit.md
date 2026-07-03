# Correct-Score Reconciliation Audit

**Generated**: 2026-07-03T04:52:20Z

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

### Switzerland vs Algeria
- CS outcomes: 24  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-0 | 0.1347 | 0.1217 | 0.0130 |
| 1-1 | 0.1347 | 0.1376 | 0.0029 |
| 2-1 | 0.1010 | 0.0941 | 0.0069 |
| 0-0 | 0.0898 | 0.1073 | 0.0175 |
| 2-0 | 0.0851 | 0.0944 | 0.0094 |
| 0-1 | 0.0770 | 0.0768 | 0.0002 |
| 1-2 | 0.0577 | 0.0567 | 0.0011 |
| 2-2 | 0.0505 | 0.0470 | 0.0035 |
| 3-0 | 0.0425 | 0.0481 | 0.0056 |
| 3-1 | 0.0425 | 0.0444 | 0.0019 |
| 0-2 | 0.0311 | 0.0372 | 0.0061 |
| 3-2 | 0.0261 | 0.0214 | 0.0047 |
| 4-0 | 0.0176 | 0.0184 | 0.0008 |
| 4-1 | 0.0176 | 0.0167 | 0.0008 |
| 1-3 | 0.0176 | 0.0170 | 0.0006 |
| **Sum (top 15)** | **0.9253** | **0.9388** | — |
- High-score mass (total ≥9 goals): 1.50e-05
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
| 2-0 | 0.1521 | 0.1568 | 0.0046 |
| 3-0 | 0.1344 | 0.1373 | 0.0029 |
| 1-0 | 0.1075 | 0.1222 | 0.0147 |
| 4-0 | 0.0949 | 0.0939 | 0.0010 |
| 2-1 | 0.0672 | 0.0773 | 0.0101 |
| 3-1 | 0.0620 | 0.0688 | 0.0068 |
| 5-0 | 0.0504 | 0.0494 | 0.0010 |
| 1-1 | 0.0504 | 0.0555 | 0.0051 |
| 0-0 | 0.0448 | 0.0461 | 0.0013 |
| 4-1 | 0.0424 | 0.0458 | 0.0033 |
| 6-0 | 0.0260 | 0.0217 | 0.0043 |
| 0-1 | 0.0260 | 0.0240 | 0.0020 |
| 5-1 | 0.0237 | 0.0220 | 0.0017 |
| 2-2 | 0.0175 | 0.0185 | 0.0010 |
| 3-2 | 0.0158 | 0.0177 | 0.0019 |
| **Sum (top 15)** | **0.9151** | **0.9569** | — |
- High-score mass (total ≥9 goals): 2.38e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Colombia vs Ghana
- CS outcomes: 24  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-0 | 0.1485 | 0.1501 | 0.0016 |
| 2-0 | 0.1408 | 0.1453 | 0.0045 |
| 1-1 | 0.0961 | 0.1009 | 0.0048 |
| 2-1 | 0.0859 | 0.0896 | 0.0036 |
| 3-0 | 0.0859 | 0.0896 | 0.0037 |
| 0-0 | 0.0817 | 0.0927 | 0.0110 |
| 3-1 | 0.0544 | 0.0561 | 0.0017 |
| 0-1 | 0.0480 | 0.0531 | 0.0051 |
| 4-0 | 0.0430 | 0.0428 | 0.0002 |
| 4-1 | 0.0292 | 0.0266 | 0.0026 |
| 2-2 | 0.0292 | 0.0286 | 0.0005 |
| 1-2 | 0.0292 | 0.0297 | 0.0005 |
| 3-2 | 0.0227 | 0.0181 | 0.0046 |
| 5-0 | 0.0199 | 0.0161 | 0.0038 |
| 0-2 | 0.0178 | 0.0171 | 0.0006 |
| **Sum (top 15)** | **0.9321** | **0.9564** | — |
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
| 1-1 | 0.1335 | 0.1408 | 0.0072 |
| 0-1 | 0.1144 | 0.1217 | 0.0072 |
| 1-0 | 0.1001 | 0.1048 | 0.0047 |
| 0-0 | 0.0942 | 0.1169 | 0.0226 |
| 1-2 | 0.0801 | 0.0796 | 0.0005 |
| 2-1 | 0.0728 | 0.0678 | 0.0050 |
| 0-2 | 0.0728 | 0.0781 | 0.0053 |
| 2-0 | 0.0534 | 0.0567 | 0.0033 |
| 2-2 | 0.0471 | 0.0406 | 0.0066 |
| 1-3 | 0.0348 | 0.0317 | 0.0031 |
| 0-3 | 0.0308 | 0.0311 | 0.0003 |
| 3-1 | 0.0258 | 0.0231 | 0.0028 |
| 3-0 | 0.0223 | 0.0193 | 0.0030 |
| 2-3 | 0.0223 | 0.0162 | 0.0061 |
| 3-2 | 0.0195 | 0.0138 | 0.0058 |
| **Sum (top 15)** | **0.9242** | **0.9420** | — |
- High-score mass (total ≥9 goals): 2.90e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Portugal vs Spain
- CS outcomes: 28  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-1 | 0.1217 | 0.1235 | 0.0018 |
| 0-1 | 0.1130 | 0.1058 | 0.0072 |
| 1-2 | 0.0989 | 0.0975 | 0.0013 |
| 0-2 | 0.0879 | 0.0920 | 0.0041 |
| 0-0 | 0.0659 | 0.0789 | 0.0130 |
| 1-0 | 0.0608 | 0.0662 | 0.0054 |
| 2-1 | 0.0565 | 0.0607 | 0.0042 |
| 2-2 | 0.0527 | 0.0536 | 0.0009 |
| 1-3 | 0.0494 | 0.0529 | 0.0035 |
| 0-3 | 0.0465 | 0.0517 | 0.0052 |
| 2-0 | 0.0304 | 0.0366 | 0.0062 |
| 2-3 | 0.0304 | 0.0286 | 0.0018 |
| 0-4 | 0.0233 | 0.0222 | 0.0010 |
| 1-4 | 0.0233 | 0.0225 | 0.0007 |
| 3-1 | 0.0220 | 0.0217 | 0.0003 |
| **Sum (top 15)** | **0.8826** | **0.9145** | — |
- High-score mass (total ≥9 goals): 2.01e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### USA vs Belgium
- CS outcomes: 31  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-1 | 0.1211 | 0.1277 | 0.0066 |
| 2-1 | 0.0828 | 0.0844 | 0.0015 |
| 1-0 | 0.0787 | 0.0760 | 0.0027 |
| 1-2 | 0.0787 | 0.0827 | 0.0040 |
| 2-2 | 0.0715 | 0.0665 | 0.0050 |
| 0-1 | 0.0715 | 0.0735 | 0.0020 |
| 0-0 | 0.0562 | 0.0742 | 0.0180 |
| 2-0 | 0.0525 | 0.0598 | 0.0074 |
| 0-2 | 0.0492 | 0.0581 | 0.0089 |
| 3-1 | 0.0394 | 0.0407 | 0.0013 |
| 1-3 | 0.0375 | 0.0397 | 0.0022 |
| 3-2 | 0.0342 | 0.0298 | 0.0044 |
| 2-3 | 0.0342 | 0.0297 | 0.0045 |
| 3-0 | 0.0254 | 0.0292 | 0.0038 |
| 0-3 | 0.0254 | 0.0284 | 0.0030 |
| **Sum (top 15)** | **0.8583** | **0.9003** | — |
- High-score mass (total ≥9 goals): 2.46e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS
