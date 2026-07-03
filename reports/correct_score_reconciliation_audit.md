# Correct-Score Reconciliation Audit

**Generated**: 2026-07-03T11:37:17Z

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

### Australia vs Egypt
- CS outcomes: 23  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-1 | 0.1450 | 0.1483 | 0.0033 |
| 0-1 | 0.1401 | 0.1449 | 0.0048 |
| 0-0 | 0.1180 | 0.1429 | 0.0248 |
| 1-0 | 0.1033 | 0.1112 | 0.0079 |
| 1-2 | 0.0826 | 0.0777 | 0.0049 |
| 0-2 | 0.0751 | 0.0890 | 0.0139 |
| 2-1 | 0.0636 | 0.0594 | 0.0042 |
| 2-2 | 0.0486 | 0.0358 | 0.0129 |
| 2-0 | 0.0435 | 0.0536 | 0.0102 |
| 1-3 | 0.0318 | 0.0263 | 0.0054 |
| 0-3 | 0.0295 | 0.0328 | 0.0032 |
| 2-3 | 0.0202 | 0.0103 | 0.0099 |
| 3-1 | 0.0180 | 0.0148 | 0.0031 |
| 3-2 | 0.0148 | 0.0076 | 0.0072 |
| 3-0 | 0.0135 | 0.0145 | 0.0010 |
| **Sum (top 15)** | **0.9475** | **0.9691** | — |
- High-score mass (total ≥9 goals): 4.27e-06
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Argentina vs Cabo Verde
- CS outcomes: 24  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 2-0 | 0.1569 | 0.1595 | 0.0026 |
| 3-0 | 0.1360 | 0.1378 | 0.0018 |
| 1-0 | 0.1088 | 0.1255 | 0.0167 |
| 4-0 | 0.0960 | 0.0940 | 0.0019 |
| 2-1 | 0.0680 | 0.0765 | 0.0085 |
| 3-1 | 0.0628 | 0.0681 | 0.0054 |
| 5-0 | 0.0544 | 0.0503 | 0.0041 |
| 1-1 | 0.0480 | 0.0540 | 0.0060 |
| 4-1 | 0.0429 | 0.0452 | 0.0023 |
| 0-0 | 0.0429 | 0.0452 | 0.0023 |
| 6-0 | 0.0263 | 0.0217 | 0.0046 |
| 5-1 | 0.0240 | 0.0220 | 0.0020 |
| 0-1 | 0.0227 | 0.0236 | 0.0009 |
| 3-2 | 0.0160 | 0.0171 | 0.0011 |
| 2-2 | 0.0160 | 0.0178 | 0.0018 |
| **Sum (top 15)** | **0.9216** | **0.9583** | — |
- High-score mass (total ≥9 goals): 2.37e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Colombia vs Ghana
- CS outcomes: 25  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-0 | 0.1444 | 0.1443 | 0.0001 |
| 2-0 | 0.1348 | 0.1424 | 0.0075 |
| 1-1 | 0.0952 | 0.1002 | 0.0051 |
| 2-1 | 0.0899 | 0.0917 | 0.0018 |
| 3-0 | 0.0851 | 0.0908 | 0.0057 |
| 0-0 | 0.0770 | 0.0886 | 0.0115 |
| 3-1 | 0.0622 | 0.0600 | 0.0022 |
| 4-0 | 0.0449 | 0.0451 | 0.0002 |
| 0-1 | 0.0449 | 0.0502 | 0.0052 |
| 2-2 | 0.0311 | 0.0296 | 0.0015 |
| 1-2 | 0.0311 | 0.0299 | 0.0012 |
| 4-1 | 0.0289 | 0.0281 | 0.0008 |
| 3-2 | 0.0225 | 0.0190 | 0.0035 |
| 5-0 | 0.0197 | 0.0173 | 0.0024 |
| 0-2 | 0.0176 | 0.0166 | 0.0010 |
| **Sum (top 15)** | **0.9294** | **0.9538** | — |
- High-score mass (total ≥9 goals): 1.57e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Canada vs Morocco
- CS outcomes: 23  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 0-1 | 0.1380 | 0.1328 | 0.0052 |
| 1-1 | 0.1231 | 0.1258 | 0.0026 |
| 0-2 | 0.1067 | 0.1121 | 0.0054 |
| 1-2 | 0.1001 | 0.0955 | 0.0046 |
| 0-0 | 0.0889 | 0.1028 | 0.0139 |
| 1-0 | 0.0728 | 0.0720 | 0.0007 |
| 0-3 | 0.0534 | 0.0594 | 0.0061 |
| 2-1 | 0.0471 | 0.0471 | 0.0000 |
| 1-3 | 0.0471 | 0.0489 | 0.0018 |
| 2-2 | 0.0445 | 0.0412 | 0.0033 |
| 2-0 | 0.0286 | 0.0303 | 0.0017 |
| 2-3 | 0.0258 | 0.0209 | 0.0049 |
| 0-4 | 0.0235 | 0.0244 | 0.0008 |
| 1-4 | 0.0195 | 0.0195 | 0.0000 |
| 3-1 | 0.0143 | 0.0127 | 0.0016 |
| **Sum (top 15)** | **0.9334** | **0.9454** | — |
- High-score mass (total ≥9 goals): 1.41e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Paraguay vs France
- CS outcomes: 25  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 0-2 | 0.1509 | 0.1539 | 0.0031 |
| 0-3 | 0.1253 | 0.1303 | 0.0050 |
| 0-1 | 0.1164 | 0.1230 | 0.0066 |
| 0-4 | 0.0776 | 0.0832 | 0.0056 |
| 1-2 | 0.0741 | 0.0822 | 0.0082 |
| 1-3 | 0.0627 | 0.0696 | 0.0070 |
| 1-1 | 0.0582 | 0.0619 | 0.0037 |
| 0-0 | 0.0509 | 0.0510 | 0.0000 |
| 1-4 | 0.0429 | 0.0450 | 0.0022 |
| 0-5 | 0.0429 | 0.0435 | 0.0006 |
| 1-0 | 0.0263 | 0.0263 | 0.0000 |
| 2-2 | 0.0226 | 0.0214 | 0.0012 |
| 1-5 | 0.0226 | 0.0220 | 0.0007 |
| 2-3 | 0.0199 | 0.0194 | 0.0005 |
| 0-6 | 0.0199 | 0.0183 | 0.0016 |
| **Sum (top 15)** | **0.9130** | **0.9509** | — |
- High-score mass (total ≥9 goals): 2.30e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Brazil vs Norway
- CS outcomes: 30  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-1 | 0.1128 | 0.1177 | 0.0049 |
| 2-1 | 0.0987 | 0.1002 | 0.0015 |
| 1-0 | 0.0929 | 0.0908 | 0.0021 |
| 2-0 | 0.0752 | 0.0871 | 0.0119 |
| 2-2 | 0.0658 | 0.0603 | 0.0055 |
| 1-2 | 0.0607 | 0.0614 | 0.0006 |
| 0-1 | 0.0564 | 0.0580 | 0.0016 |
| 3-1 | 0.0526 | 0.0584 | 0.0058 |
| 0-0 | 0.0526 | 0.0683 | 0.0156 |
| 3-0 | 0.0439 | 0.0533 | 0.0094 |
| 3-2 | 0.0376 | 0.0346 | 0.0030 |
| 0-2 | 0.0304 | 0.0346 | 0.0042 |
| 4-1 | 0.0255 | 0.0270 | 0.0015 |
| 1-3 | 0.0255 | 0.0231 | 0.0024 |
| 2-3 | 0.0255 | 0.0207 | 0.0048 |
| **Sum (top 15)** | **0.8560** | **0.8953** | — |
- High-score mass (total ≥9 goals): 2.44e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Mexico vs England
- CS outcomes: 25  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-1 | 0.1324 | 0.1370 | 0.0046 |
| 0-1 | 0.1222 | 0.1220 | 0.0002 |
| 1-0 | 0.0993 | 0.1024 | 0.0031 |
| 0-0 | 0.0993 | 0.1138 | 0.0145 |
| 1-2 | 0.0794 | 0.0799 | 0.0005 |
| 2-1 | 0.0722 | 0.0691 | 0.0031 |
| 0-2 | 0.0722 | 0.0782 | 0.0060 |
| 2-0 | 0.0529 | 0.0567 | 0.0037 |
| 2-2 | 0.0441 | 0.0448 | 0.0007 |
| 0-3 | 0.0345 | 0.0330 | 0.0015 |
| 1-3 | 0.0305 | 0.0328 | 0.0022 |
| 3-1 | 0.0256 | 0.0239 | 0.0017 |
| 3-0 | 0.0221 | 0.0198 | 0.0022 |
| 2-3 | 0.0221 | 0.0178 | 0.0043 |
| 3-2 | 0.0173 | 0.0147 | 0.0026 |
| **Sum (top 15)** | **0.9261** | **0.9456** | — |
- High-score mass (total ≥9 goals): 1.25e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Portugal vs Spain
- CS outcomes: 28  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-1 | 0.1217 | 0.1236 | 0.0019 |
| 0-1 | 0.1130 | 0.1065 | 0.0065 |
| 1-2 | 0.0989 | 0.0971 | 0.0018 |
| 0-2 | 0.0879 | 0.0915 | 0.0037 |
| 0-0 | 0.0659 | 0.0790 | 0.0131 |
| 1-0 | 0.0608 | 0.0674 | 0.0065 |
| 2-1 | 0.0565 | 0.0613 | 0.0048 |
| 2-2 | 0.0527 | 0.0535 | 0.0008 |
| 1-3 | 0.0494 | 0.0523 | 0.0028 |
| 0-3 | 0.0465 | 0.0509 | 0.0044 |
| 2-0 | 0.0304 | 0.0374 | 0.0070 |
| 2-3 | 0.0304 | 0.0284 | 0.0021 |
| 0-4 | 0.0233 | 0.0216 | 0.0016 |
| 1-4 | 0.0233 | 0.0220 | 0.0012 |
| 3-1 | 0.0220 | 0.0221 | 0.0001 |
| **Sum (top 15)** | **0.8826** | **0.9145** | — |
- High-score mass (total ≥9 goals): 1.99e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### USA vs Belgium
- CS outcomes: 31  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-1 | 0.1297 | 0.1297 | 0.0000 |
| 2-1 | 0.0819 | 0.0851 | 0.0032 |
| 1-2 | 0.0819 | 0.0842 | 0.0023 |
| 1-0 | 0.0778 | 0.0718 | 0.0060 |
| 0-1 | 0.0741 | 0.0700 | 0.0041 |
| 2-2 | 0.0707 | 0.0673 | 0.0035 |
| 0-0 | 0.0556 | 0.0718 | 0.0163 |
| 2-0 | 0.0486 | 0.0577 | 0.0091 |
| 0-2 | 0.0458 | 0.0555 | 0.0097 |
| 3-1 | 0.0370 | 0.0414 | 0.0043 |
| 1-3 | 0.0370 | 0.0404 | 0.0033 |
| 3-2 | 0.0338 | 0.0312 | 0.0026 |
| 2-3 | 0.0338 | 0.0308 | 0.0030 |
| 3-0 | 0.0251 | 0.0296 | 0.0045 |
| 0-3 | 0.0251 | 0.0285 | 0.0034 |
| **Sum (top 15)** | **0.8579** | **0.8949** | — |
- High-score mass (total ≥9 goals): 2.60e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS
