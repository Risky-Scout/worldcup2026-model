# Correct-Score Reconciliation Audit

**Generated**: 2026-07-02T23:38:52Z

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

### Portugal vs Croatia
- CS outcomes: 28  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-1 | 0.1139 | 0.1193 | 0.0054 |
| 1-0 | 0.1063 | 0.0933 | 0.0130 |
| 2-1 | 0.1063 | 0.1036 | 0.0026 |
| 2-0 | 0.0886 | 0.1003 | 0.0117 |
| 3-1 | 0.0613 | 0.0639 | 0.0026 |
| 2-2 | 0.0613 | 0.0547 | 0.0066 |
| 3-0 | 0.0531 | 0.0646 | 0.0115 |
| 0-0 | 0.0531 | 0.0740 | 0.0208 |
| 1-2 | 0.0498 | 0.0509 | 0.0011 |
| 0-1 | 0.0469 | 0.0498 | 0.0029 |
| 3-2 | 0.0399 | 0.0329 | 0.0069 |
| 4-0 | 0.0257 | 0.0318 | 0.0061 |
| 4-1 | 0.0257 | 0.0299 | 0.0042 |
| 0-2 | 0.0221 | 0.0266 | 0.0045 |
| 4-2 | 0.0194 | 0.0150 | 0.0044 |
| **Sum (top 15)** | **0.8734** | **0.9107** | — |
- High-score mass (total ≥9 goals): 2.29e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Switzerland vs Algeria
- CS outcomes: 26  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-0 | 0.1333 | 0.1240 | 0.0092 |
| 1-1 | 0.1333 | 0.1358 | 0.0025 |
| 2-1 | 0.1000 | 0.0942 | 0.0057 |
| 2-0 | 0.0842 | 0.0954 | 0.0112 |
| 0-0 | 0.0842 | 0.1031 | 0.0190 |
| 0-1 | 0.0727 | 0.0761 | 0.0034 |
| 1-2 | 0.0615 | 0.0574 | 0.0041 |
| 2-2 | 0.0533 | 0.0472 | 0.0061 |
| 3-1 | 0.0421 | 0.0448 | 0.0027 |
| 3-0 | 0.0400 | 0.0479 | 0.0080 |
| 0-2 | 0.0348 | 0.0381 | 0.0034 |
| 3-2 | 0.0286 | 0.0220 | 0.0066 |
| 1-3 | 0.0195 | 0.0171 | 0.0024 |
| 4-0 | 0.0174 | 0.0187 | 0.0013 |
| 4-1 | 0.0157 | 0.0168 | 0.0011 |
| **Sum (top 15)** | **0.9203** | **0.9388** | — |
- High-score mass (total ≥9 goals): 1.51e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Australia vs Egypt
- CS outcomes: 22  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-1 | 0.1459 | 0.1474 | 0.0015 |
| 0-1 | 0.1409 | 0.1429 | 0.0020 |
| 0-0 | 0.1257 | 0.1442 | 0.0185 |
| 1-0 | 0.1089 | 0.1154 | 0.0065 |
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
- CS outcomes: 24  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 2-0 | 0.1590 | 0.1582 | 0.0008 |
| 3-0 | 0.1351 | 0.1367 | 0.0016 |
| 1-0 | 0.1158 | 0.1252 | 0.0094 |
| 4-0 | 0.0901 | 0.0907 | 0.0006 |
| 2-1 | 0.0676 | 0.0776 | 0.0100 |
| 3-1 | 0.0624 | 0.0686 | 0.0062 |
| 5-0 | 0.0507 | 0.0482 | 0.0025 |
| 1-1 | 0.0507 | 0.0558 | 0.0051 |
| 0-0 | 0.0477 | 0.0471 | 0.0006 |
| 4-1 | 0.0386 | 0.0442 | 0.0056 |
| 6-0 | 0.0262 | 0.0209 | 0.0052 |
| 5-1 | 0.0238 | 0.0220 | 0.0019 |
| 0-1 | 0.0238 | 0.0241 | 0.0003 |
| 2-2 | 0.0176 | 0.0191 | 0.0014 |
| 3-2 | 0.0133 | 0.0174 | 0.0041 |
| **Sum (top 15)** | **0.9225** | **0.9559** | — |
- High-score mass (total ≥9 goals): 2.35e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Colombia vs Ghana
- CS outcomes: 24  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-0 | 0.1502 | 0.1519 | 0.0017 |
| 2-0 | 0.1351 | 0.1426 | 0.0075 |
| 1-1 | 0.1014 | 0.1027 | 0.0013 |
| 2-1 | 0.0954 | 0.0932 | 0.0022 |
| 0-0 | 0.0811 | 0.0917 | 0.0106 |
| 3-0 | 0.0772 | 0.0853 | 0.0081 |
| 3-1 | 0.0579 | 0.0568 | 0.0011 |
| 0-1 | 0.0477 | 0.0541 | 0.0064 |
| 4-0 | 0.0386 | 0.0408 | 0.0022 |
| 2-2 | 0.0353 | 0.0295 | 0.0058 |
| 1-2 | 0.0312 | 0.0306 | 0.0006 |
| 4-1 | 0.0262 | 0.0257 | 0.0004 |
| 3-2 | 0.0238 | 0.0184 | 0.0055 |
| 5-0 | 0.0176 | 0.0153 | 0.0023 |
| 0-2 | 0.0159 | 0.0176 | 0.0017 |
| **Sum (top 15)** | **0.9346** | **0.9563** | — |
- High-score mass (total ≥9 goals): 1.50e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Canada vs Morocco
- CS outcomes: 25  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 0-1 | 0.1369 | 0.1353 | 0.0017 |
| 1-1 | 0.1243 | 0.1271 | 0.0027 |
| 0-2 | 0.1077 | 0.1134 | 0.0057 |
| 1-2 | 0.0951 | 0.0929 | 0.0022 |
| 0-0 | 0.0898 | 0.1052 | 0.0155 |
| 1-0 | 0.0673 | 0.0728 | 0.0055 |
| 0-3 | 0.0539 | 0.0588 | 0.0049 |
| 2-1 | 0.0475 | 0.0474 | 0.0002 |
| 1-3 | 0.0475 | 0.0479 | 0.0004 |
| 2-2 | 0.0425 | 0.0399 | 0.0027 |
| 2-0 | 0.0289 | 0.0314 | 0.0026 |
| 2-3 | 0.0261 | 0.0201 | 0.0059 |
| 0-4 | 0.0238 | 0.0236 | 0.0002 |
| 1-4 | 0.0224 | 0.0191 | 0.0034 |
| 3-1 | 0.0144 | 0.0126 | 0.0018 |
| **Sum (top 15)** | **0.9282** | **0.9474** | — |
- High-score mass (total ≥9 goals): 1.36e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Paraguay vs France
- CS outcomes: 27  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 0-2 | 0.1386 | 0.1488 | 0.0102 |
| 0-1 | 0.1237 | 0.1240 | 0.0003 |
| 0-3 | 0.1149 | 0.1271 | 0.0122 |
| 1-2 | 0.0846 | 0.0862 | 0.0016 |
| 0-4 | 0.0731 | 0.0833 | 0.0102 |
| 1-3 | 0.0670 | 0.0717 | 0.0047 |
| 1-1 | 0.0618 | 0.0633 | 0.0015 |
| 1-4 | 0.0423 | 0.0458 | 0.0035 |
| 0-0 | 0.0402 | 0.0484 | 0.0082 |
| 0-5 | 0.0402 | 0.0445 | 0.0043 |
| 2-2 | 0.0259 | 0.0217 | 0.0042 |
| 2-3 | 0.0259 | 0.0203 | 0.0056 |
| 1-5 | 0.0236 | 0.0220 | 0.0017 |
| 1-0 | 0.0223 | 0.0249 | 0.0026 |
| 2-1 | 0.0175 | 0.0166 | 0.0009 |
| **Sum (top 15)** | **0.9017** | **0.9488** | — |
- High-score mass (total ≥9 goals): 2.33e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Brazil vs Norway
- CS outcomes: 30  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-1 | 0.1124 | 0.1170 | 0.0046 |
| 1-0 | 0.0983 | 0.0924 | 0.0059 |
| 2-1 | 0.0983 | 0.0997 | 0.0014 |
| 2-0 | 0.0749 | 0.0863 | 0.0114 |
| 2-2 | 0.0655 | 0.0602 | 0.0053 |
| 1-2 | 0.0605 | 0.0619 | 0.0014 |
| 0-0 | 0.0562 | 0.0690 | 0.0128 |
| 0-1 | 0.0562 | 0.0581 | 0.0019 |
| 3-1 | 0.0524 | 0.0583 | 0.0059 |
| 3-0 | 0.0437 | 0.0529 | 0.0092 |
| 3-2 | 0.0375 | 0.0345 | 0.0029 |
| 0-2 | 0.0302 | 0.0348 | 0.0045 |
| 4-1 | 0.0254 | 0.0267 | 0.0014 |
| 2-3 | 0.0231 | 0.0207 | 0.0024 |
| 4-0 | 0.0218 | 0.0245 | 0.0027 |
| **Sum (top 15)** | **0.8564** | **0.8971** | — |
- High-score mass (total ≥9 goals): 2.43e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Mexico vs England
- CS outcomes: 24  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-1 | 0.1339 | 0.1373 | 0.0034 |
| 0-1 | 0.1148 | 0.1213 | 0.0065 |
| 1-0 | 0.1071 | 0.1086 | 0.0014 |
| 0-0 | 0.1004 | 0.1157 | 0.0152 |
| 1-2 | 0.0803 | 0.0794 | 0.0009 |
| 0-2 | 0.0730 | 0.0785 | 0.0055 |
| 2-1 | 0.0670 | 0.0671 | 0.0002 |
| 2-0 | 0.0536 | 0.0583 | 0.0047 |
| 2-2 | 0.0446 | 0.0435 | 0.0012 |
| 1-3 | 0.0349 | 0.0324 | 0.0025 |
| 0-3 | 0.0309 | 0.0313 | 0.0004 |
| 3-1 | 0.0259 | 0.0236 | 0.0023 |
| 3-0 | 0.0223 | 0.0201 | 0.0023 |
| 2-3 | 0.0223 | 0.0170 | 0.0053 |
| 3-2 | 0.0196 | 0.0143 | 0.0053 |
| **Sum (top 15)** | **0.9308** | **0.9483** | — |
- High-score mass (total ≥9 goals): 1.17e-05
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
| 0-1 | 0.0715 | 0.0738 | 0.0023 |
| 0-0 | 0.0562 | 0.0740 | 0.0178 |
| 2-0 | 0.0525 | 0.0596 | 0.0072 |
| 0-2 | 0.0492 | 0.0583 | 0.0091 |
| 3-1 | 0.0394 | 0.0405 | 0.0011 |
| 1-3 | 0.0375 | 0.0398 | 0.0024 |
| 3-2 | 0.0342 | 0.0298 | 0.0045 |
| 2-3 | 0.0342 | 0.0298 | 0.0044 |
| 3-0 | 0.0254 | 0.0290 | 0.0036 |
| 0-3 | 0.0254 | 0.0286 | 0.0032 |
| **Sum (top 15)** | **0.8583** | **0.9003** | — |
- High-score mass (total ≥9 goals): 2.46e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS
