# Correct-Score Reconciliation Audit

**Generated**: 2026-07-01T22:41:30Z

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

### USA vs Bosnia & Herzegovina
- CS outcomes: 29  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 2-0 | 0.1134 | 0.1236 | 0.0102 |
| 1-0 | 0.1058 | 0.1052 | 0.0006 |
| 2-1 | 0.0992 | 0.1006 | 0.0014 |
| 1-1 | 0.0835 | 0.0869 | 0.0034 |
| 3-0 | 0.0794 | 0.0939 | 0.0145 |
| 3-1 | 0.0721 | 0.0759 | 0.0038 |
| 4-0 | 0.0441 | 0.0551 | 0.0111 |
| 0-0 | 0.0441 | 0.0542 | 0.0102 |
| 4-1 | 0.0418 | 0.0438 | 0.0021 |
| 2-2 | 0.0418 | 0.0390 | 0.0028 |
| 3-2 | 0.0345 | 0.0309 | 0.0036 |
| 0-1 | 0.0345 | 0.0362 | 0.0017 |
| 1-2 | 0.0345 | 0.0328 | 0.0017 |
| 5-0 | 0.0256 | 0.0268 | 0.0012 |
| 5-1 | 0.0220 | 0.0203 | 0.0017 |
| **Sum (top 15)** | **0.8763** | **0.9252** | — |
- High-score mass (total ≥9 goals): 2.37e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Spain vs Austria
- CS outcomes: 26  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 2-0 | 0.1334 | 0.1432 | 0.0098 |
| 1-0 | 0.1232 | 0.1307 | 0.0076 |
| 2-1 | 0.0942 | 0.0946 | 0.0005 |
| 3-0 | 0.0942 | 0.1025 | 0.0083 |
| 1-1 | 0.0801 | 0.0847 | 0.0046 |
| 3-1 | 0.0667 | 0.0682 | 0.0015 |
| 0-0 | 0.0572 | 0.0656 | 0.0084 |
| 4-0 | 0.0534 | 0.0577 | 0.0043 |
| 4-1 | 0.0381 | 0.0374 | 0.0007 |
| 2-2 | 0.0348 | 0.0298 | 0.0050 |
| 0-1 | 0.0348 | 0.0396 | 0.0048 |
| 1-2 | 0.0286 | 0.0266 | 0.0020 |
| 3-2 | 0.0258 | 0.0225 | 0.0033 |
| 5-0 | 0.0258 | 0.0256 | 0.0002 |
| 5-1 | 0.0174 | 0.0160 | 0.0014 |
| **Sum (top 15)** | **0.9076** | **0.9448** | — |
- High-score mass (total ≥9 goals): 2.00e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Portugal vs Croatia
- CS outcomes: 25  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-0 | 0.1250 | 0.1167 | 0.0083 |
| 1-1 | 0.1250 | 0.1233 | 0.0017 |
| 2-1 | 0.1016 | 0.0995 | 0.0020 |
| 2-0 | 0.0956 | 0.1042 | 0.0086 |
| 0-0 | 0.0739 | 0.0857 | 0.0119 |
| 0-1 | 0.0625 | 0.0632 | 0.0007 |
| 2-2 | 0.0542 | 0.0481 | 0.0061 |
| 3-0 | 0.0508 | 0.0602 | 0.0094 |
| 3-1 | 0.0508 | 0.0551 | 0.0043 |
| 1-2 | 0.0508 | 0.0513 | 0.0005 |
| 3-2 | 0.0290 | 0.0262 | 0.0028 |
| 0-2 | 0.0262 | 0.0298 | 0.0036 |
| 4-0 | 0.0226 | 0.0267 | 0.0041 |
| 4-1 | 0.0226 | 0.0240 | 0.0014 |
| 1-3 | 0.0177 | 0.0155 | 0.0022 |
| **Sum (top 15)** | **0.9080** | **0.9293** | — |
- High-score mass (total ≥9 goals): 1.80e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Switzerland vs Algeria
- CS outcomes: 26  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-1 | 0.1331 | 0.1358 | 0.0027 |
| 1-0 | 0.1229 | 0.1169 | 0.0060 |
| 2-1 | 0.0940 | 0.0923 | 0.0017 |
| 2-0 | 0.0799 | 0.0908 | 0.0109 |
| 0-0 | 0.0799 | 0.0990 | 0.0191 |
| 0-1 | 0.0726 | 0.0769 | 0.0042 |
| 1-2 | 0.0615 | 0.0604 | 0.0010 |
| 2-2 | 0.0571 | 0.0503 | 0.0068 |
| 3-1 | 0.0420 | 0.0448 | 0.0027 |
| 3-0 | 0.0399 | 0.0459 | 0.0059 |
| 0-2 | 0.0380 | 0.0414 | 0.0034 |
| 3-2 | 0.0285 | 0.0232 | 0.0054 |
| 1-3 | 0.0222 | 0.0197 | 0.0025 |
| 2-3 | 0.0195 | 0.0147 | 0.0047 |
| 4-1 | 0.0174 | 0.0169 | 0.0005 |
| **Sum (top 15)** | **0.9085** | **0.9290** | — |
- High-score mass (total ≥9 goals): 1.60e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Australia vs Egypt
- CS outcomes: 22  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-1 | 0.1454 | 0.1472 | 0.0018 |
| 0-1 | 0.1380 | 0.1410 | 0.0031 |
| 0-0 | 0.1253 | 0.1432 | 0.0179 |
| 1-0 | 0.1086 | 0.1151 | 0.0066 |
| 1-2 | 0.0814 | 0.0765 | 0.0049 |
| 2-1 | 0.0678 | 0.0630 | 0.0049 |
| 0-2 | 0.0678 | 0.0828 | 0.0150 |
| 2-2 | 0.0479 | 0.0359 | 0.0120 |
| 2-0 | 0.0452 | 0.0572 | 0.0120 |
| 1-3 | 0.0291 | 0.0251 | 0.0039 |
| 0-3 | 0.0263 | 0.0299 | 0.0036 |
| 3-1 | 0.0226 | 0.0170 | 0.0057 |
| 3-0 | 0.0177 | 0.0168 | 0.0009 |
| 2-3 | 0.0177 | 0.0103 | 0.0074 |
| 3-2 | 0.0145 | 0.0083 | 0.0063 |
| **Sum (top 15)** | **0.9553** | **0.9692** | — |
- High-score mass (total ≥9 goals): 4.52e-06
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Argentina vs Cabo Verde
- CS outcomes: 24  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 2-0 | 0.1552 | 0.1595 | 0.0043 |
| 3-0 | 0.1345 | 0.1352 | 0.0007 |
| 1-0 | 0.1241 | 0.1349 | 0.0107 |
| 4-0 | 0.0849 | 0.0866 | 0.0017 |
| 2-1 | 0.0734 | 0.0791 | 0.0057 |
| 3-1 | 0.0621 | 0.0670 | 0.0049 |
| 1-1 | 0.0538 | 0.0573 | 0.0035 |
| 5-0 | 0.0475 | 0.0452 | 0.0023 |
| 0-0 | 0.0475 | 0.0490 | 0.0015 |
| 4-1 | 0.0384 | 0.0423 | 0.0038 |
| 5-1 | 0.0237 | 0.0219 | 0.0019 |
| 6-0 | 0.0237 | 0.0191 | 0.0046 |
| 0-1 | 0.0224 | 0.0254 | 0.0030 |
| 2-2 | 0.0197 | 0.0184 | 0.0013 |
| 3-2 | 0.0144 | 0.0167 | 0.0023 |
| **Sum (top 15)** | **0.9253** | **0.9575** | — |
- High-score mass (total ≥9 goals): 2.25e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Colombia vs Ghana
- CS outcomes: 23  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-0 | 0.1597 | 0.1558 | 0.0039 |
| 2-0 | 0.1331 | 0.1378 | 0.0047 |
| 1-1 | 0.1065 | 0.1075 | 0.0010 |
| 2-1 | 0.0939 | 0.0924 | 0.0015 |
| 0-0 | 0.0887 | 0.0984 | 0.0097 |
| 3-0 | 0.0726 | 0.0795 | 0.0069 |
| 0-1 | 0.0570 | 0.0595 | 0.0025 |
| 3-1 | 0.0499 | 0.0526 | 0.0027 |
| 4-0 | 0.0347 | 0.0362 | 0.0015 |
| 1-2 | 0.0347 | 0.0333 | 0.0014 |
| 2-2 | 0.0307 | 0.0300 | 0.0007 |
| 4-1 | 0.0258 | 0.0236 | 0.0021 |
| 3-2 | 0.0222 | 0.0178 | 0.0043 |
| 0-2 | 0.0195 | 0.0196 | 0.0001 |
| 5-0 | 0.0131 | 0.0127 | 0.0004 |
| **Sum (top 15)** | **0.9422** | **0.9569** | — |
- High-score mass (total ≥9 goals): 1.41e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Canada vs Morocco
- CS outcomes: 25  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 0-1 | 0.1347 | 0.1349 | 0.0002 |
| 1-1 | 0.1244 | 0.1272 | 0.0028 |
| 0-2 | 0.1011 | 0.1105 | 0.0094 |
| 1-2 | 0.0951 | 0.0932 | 0.0020 |
| 0-0 | 0.0898 | 0.1051 | 0.0152 |
| 1-0 | 0.0735 | 0.0751 | 0.0016 |
| 0-3 | 0.0539 | 0.0582 | 0.0043 |
| 2-1 | 0.0476 | 0.0475 | 0.0001 |
| 1-3 | 0.0476 | 0.0479 | 0.0004 |
| 2-2 | 0.0425 | 0.0401 | 0.0025 |
| 2-0 | 0.0311 | 0.0322 | 0.0011 |
| 2-3 | 0.0238 | 0.0201 | 0.0037 |
| 0-4 | 0.0238 | 0.0233 | 0.0005 |
| 1-4 | 0.0225 | 0.0190 | 0.0035 |
| 3-1 | 0.0159 | 0.0129 | 0.0029 |
| **Sum (top 15)** | **0.9271** | **0.9471** | — |
- High-score mass (total ≥9 goals): 1.36e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Paraguay vs France
- CS outcomes: 28  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 0-2 | 0.1419 | 0.1491 | 0.0072 |
| 0-3 | 0.1222 | 0.1303 | 0.0081 |
| 0-1 | 0.1135 | 0.1171 | 0.0036 |
| 1-2 | 0.0757 | 0.0834 | 0.0078 |
| 0-4 | 0.0757 | 0.0848 | 0.0091 |
| 1-3 | 0.0662 | 0.0724 | 0.0062 |
| 1-1 | 0.0611 | 0.0627 | 0.0016 |
| 0-0 | 0.0441 | 0.0481 | 0.0040 |
| 1-4 | 0.0441 | 0.0472 | 0.0031 |
| 0-5 | 0.0418 | 0.0454 | 0.0036 |
| 1-5 | 0.0256 | 0.0220 | 0.0036 |
| 2-2 | 0.0234 | 0.0220 | 0.0014 |
| 1-0 | 0.0221 | 0.0245 | 0.0024 |
| 2-3 | 0.0221 | 0.0205 | 0.0016 |
| 0-6 | 0.0221 | 0.0200 | 0.0020 |
| **Sum (top 15)** | **0.9015** | **0.9496** | — |
- High-score mass (total ≥9 goals): 2.40e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Brazil vs Norway
- CS outcomes: 27  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-1 | 0.1149 | 0.1203 | 0.0054 |
| 1-0 | 0.1072 | 0.0992 | 0.0081 |
| 2-1 | 0.0946 | 0.0972 | 0.0026 |
| 2-0 | 0.0847 | 0.0897 | 0.0050 |
| 0-0 | 0.0670 | 0.0775 | 0.0105 |
| 0-1 | 0.0670 | 0.0636 | 0.0034 |
| 1-2 | 0.0619 | 0.0617 | 0.0001 |
| 2-2 | 0.0536 | 0.0560 | 0.0024 |
| 3-1 | 0.0503 | 0.0551 | 0.0048 |
| 3-0 | 0.0473 | 0.0529 | 0.0056 |
| 0-2 | 0.0350 | 0.0359 | 0.0010 |
| 3-2 | 0.0309 | 0.0306 | 0.0003 |
| 1-3 | 0.0237 | 0.0221 | 0.0015 |
| 4-0 | 0.0223 | 0.0231 | 0.0008 |
| 4-1 | 0.0223 | 0.0239 | 0.0016 |
| **Sum (top 15)** | **0.8828** | **0.9090** | — |
- High-score mass (total ≥9 goals): 2.18e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Mexico vs England
- CS outcomes: 25  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-1 | 0.1339 | 0.1382 | 0.0043 |
| 0-1 | 0.1236 | 0.1266 | 0.0031 |
| 0-0 | 0.0945 | 0.1139 | 0.0194 |
| 1-0 | 0.0892 | 0.1008 | 0.0116 |
| 1-2 | 0.0892 | 0.0826 | 0.0066 |
| 0-2 | 0.0765 | 0.0835 | 0.0070 |
| 2-1 | 0.0669 | 0.0656 | 0.0013 |
| 2-2 | 0.0502 | 0.0440 | 0.0062 |
| 2-0 | 0.0423 | 0.0533 | 0.0110 |
| 0-3 | 0.0382 | 0.0349 | 0.0034 |
| 1-3 | 0.0382 | 0.0341 | 0.0041 |
| 2-3 | 0.0236 | 0.0172 | 0.0065 |
| 3-1 | 0.0223 | 0.0216 | 0.0007 |
| 3-2 | 0.0175 | 0.0137 | 0.0038 |
| 3-0 | 0.0157 | 0.0173 | 0.0016 |
| **Sum (top 15)** | **0.9219** | **0.9473** | — |
- High-score mass (total ≥9 goals): 1.18e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS
