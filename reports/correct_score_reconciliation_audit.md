# Correct-Score Reconciliation Audit

**Generated**: 2026-06-27T16:10:26Z

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
- CS outcomes: 32  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 0-2 | 0.1289 | 0.1299 | 0.0010 |
| 0-3 | 0.1190 | 0.1257 | 0.0067 |
| 0-4 | 0.0910 | 0.0923 | 0.0012 |
| 0-1 | 0.0737 | 0.0833 | 0.0096 |
| 1-3 | 0.0645 | 0.0815 | 0.0170 |
| 1-2 | 0.0595 | 0.0832 | 0.0237 |
| 0-5 | 0.0553 | 0.0552 | 0.0000 |
| 1-4 | 0.0516 | 0.0627 | 0.0112 |
| 1-1 | 0.0455 | 0.0541 | 0.0086 |
| 0-0 | 0.0336 | 0.0279 | 0.0057 |
| 1-5 | 0.0336 | 0.0224 | 0.0112 |
| 0-6 | 0.0298 | 0.0224 | 0.0073 |
| 1-0 | 0.0215 | 0.0199 | 0.0016 |
| 2-2 | 0.0215 | 0.0287 | 0.0072 |
| 2-3 | 0.0215 | 0.0318 | 0.0104 |
| **Sum (top 15)** | **0.8504** | **0.9210** | — |
- High-score mass (total ≥9 goals): 3.50e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Croatia vs Ghana
- CS outcomes: 22  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-0 | 0.1484 | 0.1264 | 0.0220 |
| 1-1 | 0.1407 | 0.1542 | 0.0135 |
| 2-1 | 0.1020 | 0.0901 | 0.0120 |
| 0-0 | 0.0960 | 0.1273 | 0.0313 |
| 2-0 | 0.0907 | 0.0986 | 0.0079 |
| 0-1 | 0.0742 | 0.0708 | 0.0034 |
| 2-2 | 0.0510 | 0.0468 | 0.0043 |
| 1-2 | 0.0510 | 0.0470 | 0.0041 |
| 3-0 | 0.0453 | 0.0509 | 0.0056 |
| 3-1 | 0.0408 | 0.0421 | 0.0013 |
| 0-2 | 0.0291 | 0.0309 | 0.0018 |
| 3-2 | 0.0263 | 0.0183 | 0.0080 |
| 4-0 | 0.0177 | 0.0197 | 0.0020 |
| 4-1 | 0.0160 | 0.0159 | 0.0001 |
| 2-3 | 0.0134 | 0.0093 | 0.0041 |
| **Sum (top 15)** | **0.9428** | **0.9483** | — |
- High-score mass (total ≥9 goals): 1.24e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Colombia vs Portugal
- CS outcomes: 28  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-1 | 0.1057 | 0.1266 | 0.0209 |
| 1-2 | 0.0933 | 0.0921 | 0.0012 |
| 0-1 | 0.0881 | 0.0921 | 0.0040 |
| 0-2 | 0.0755 | 0.0799 | 0.0044 |
| 1-0 | 0.0661 | 0.0666 | 0.0006 |
| 2-1 | 0.0661 | 0.0644 | 0.0016 |
| 2-2 | 0.0610 | 0.0663 | 0.0054 |
| 0-0 | 0.0566 | 0.0743 | 0.0177 |
| 1-3 | 0.0528 | 0.0522 | 0.0006 |
| 2-0 | 0.0440 | 0.0414 | 0.0026 |
| 0-3 | 0.0417 | 0.0450 | 0.0032 |
| 2-3 | 0.0305 | 0.0307 | 0.0002 |
| 3-1 | 0.0283 | 0.0258 | 0.0025 |
| 3-2 | 0.0256 | 0.0214 | 0.0041 |
| 1-4 | 0.0233 | 0.0220 | 0.0014 |
| **Sum (top 15)** | **0.8586** | **0.9009** | — |
- High-score mass (total ≥9 goals): 2.30e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### DR Congo vs Uzbekistan
- CS outcomes: 26  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-0 | 0.1318 | 0.1375 | 0.0057 |
| 2-0 | 0.1217 | 0.1224 | 0.0007 |
| 1-1 | 0.0989 | 0.1039 | 0.0051 |
| 2-1 | 0.0833 | 0.0923 | 0.0090 |
| 0-0 | 0.0833 | 0.0838 | 0.0005 |
| 3-0 | 0.0719 | 0.0726 | 0.0007 |
| 0-1 | 0.0659 | 0.0660 | 0.0001 |
| 3-1 | 0.0527 | 0.0564 | 0.0036 |
| 1-2 | 0.0416 | 0.0437 | 0.0021 |
| 4-0 | 0.0344 | 0.0323 | 0.0021 |
| 2-2 | 0.0344 | 0.0385 | 0.0041 |
| 0-2 | 0.0304 | 0.0270 | 0.0034 |
| 4-1 | 0.0255 | 0.0252 | 0.0003 |
| 3-2 | 0.0220 | 0.0233 | 0.0013 |
| 5-0 | 0.0155 | 0.0112 | 0.0043 |
| **Sum (top 15)** | **0.9133** | **0.9361** | — |
- High-score mass (total ≥9 goals): 1.62e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Jordan vs Argentina
- CS outcomes: 27  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 0-2 | 0.1422 | 0.1413 | 0.0010 |
| 0-3 | 0.1328 | 0.1350 | 0.0023 |
| 0-1 | 0.0937 | 0.0964 | 0.0027 |
| 0-4 | 0.0937 | 0.0914 | 0.0023 |
| 1-3 | 0.0664 | 0.0768 | 0.0104 |
| 1-2 | 0.0613 | 0.0825 | 0.0212 |
| 0-5 | 0.0531 | 0.0524 | 0.0007 |
| 1-1 | 0.0469 | 0.0545 | 0.0076 |
| 0-0 | 0.0443 | 0.0333 | 0.0110 |
| 1-4 | 0.0443 | 0.0551 | 0.0109 |
| 0-6 | 0.0284 | 0.0222 | 0.0062 |
| 1-0 | 0.0257 | 0.0209 | 0.0048 |
| 1-5 | 0.0257 | 0.0222 | 0.0035 |
| 2-1 | 0.0173 | 0.0191 | 0.0018 |
| 2-2 | 0.0173 | 0.0237 | 0.0064 |
| **Sum (top 15)** | **0.8930** | **0.9269** | — |
- High-score mass (total ≥9 goals): 3.20e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Algeria vs Austria
- CS outcomes: 19  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 0-0 | 0.1827 | 0.2254 | 0.0427 |
| 1-1 | 0.1633 | 0.1911 | 0.0278 |
| 0-1 | 0.1599 | 0.1400 | 0.0199 |
| 1-0 | 0.1023 | 0.1052 | 0.0028 |
| 0-2 | 0.0731 | 0.0900 | 0.0170 |
| 1-2 | 0.0698 | 0.0567 | 0.0131 |
| 2-1 | 0.0480 | 0.0453 | 0.0027 |
| 2-2 | 0.0426 | 0.0244 | 0.0182 |
| 2-0 | 0.0334 | 0.0571 | 0.0237 |
| 0-3 | 0.0295 | 0.0230 | 0.0066 |
| 1-3 | 0.0248 | 0.0111 | 0.0137 |
| 3-1 | 0.0126 | 0.0068 | 0.0058 |
| 2-3 | 0.0126 | 0.0024 | 0.0101 |
| 3-0 | 0.0095 | 0.0106 | 0.0012 |
| 3-2 | 0.0095 | 0.0021 | 0.0074 |
| **Sum (top 15)** | **0.9735** | **0.9911** | — |
- High-score mass (total ≥9 goals): 1.26e-07
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### South Africa vs Canada
- CS outcomes: 24  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 0-1 | 0.1399 | 0.1406 | 0.0007 |
| 1-1 | 0.1159 | 0.1201 | 0.0042 |
| 0-2 | 0.1082 | 0.1169 | 0.0087 |
| 1-2 | 0.0954 | 0.0939 | 0.0015 |
| 0-0 | 0.0854 | 0.0997 | 0.0143 |
| 1-0 | 0.0676 | 0.0712 | 0.0036 |
| 0-3 | 0.0541 | 0.0619 | 0.0078 |
| 1-3 | 0.0507 | 0.0505 | 0.0002 |
| 2-1 | 0.0451 | 0.0446 | 0.0004 |
| 2-2 | 0.0451 | 0.0393 | 0.0058 |
| 2-0 | 0.0290 | 0.0294 | 0.0004 |
| 2-3 | 0.0262 | 0.0206 | 0.0056 |
| 0-4 | 0.0262 | 0.0262 | 0.0000 |
| 1-4 | 0.0225 | 0.0205 | 0.0020 |
| 3-1 | 0.0133 | 0.0116 | 0.0017 |
| **Sum (top 15)** | **0.9245** | **0.9470** | — |
- High-score mass (total ≥9 goals): 1.38e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Brazil vs Japan
- CS outcomes: 28  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-0 | 0.1226 | 0.1262 | 0.0035 |
| 2-0 | 0.1063 | 0.1129 | 0.0067 |
| 1-1 | 0.1063 | 0.1144 | 0.0081 |
| 2-1 | 0.0938 | 0.0958 | 0.0020 |
| 0-0 | 0.0725 | 0.0857 | 0.0132 |
| 3-0 | 0.0613 | 0.0650 | 0.0037 |
| 0-1 | 0.0613 | 0.0659 | 0.0046 |
| 3-1 | 0.0531 | 0.0552 | 0.0021 |
| 1-2 | 0.0469 | 0.0479 | 0.0010 |
| 2-2 | 0.0443 | 0.0437 | 0.0006 |
| 4-0 | 0.0307 | 0.0288 | 0.0019 |
| 3-2 | 0.0285 | 0.0248 | 0.0037 |
| 0-2 | 0.0285 | 0.0297 | 0.0012 |
| 4-1 | 0.0257 | 0.0241 | 0.0016 |
| 1-3 | 0.0156 | 0.0138 | 0.0018 |
| **Sum (top 15)** | **0.8973** | **0.9340** | — |
- High-score mass (total ≥9 goals): 1.69e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Netherlands vs Morocco
- CS outcomes: 26  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-1 | 0.1392 | 0.1387 | 0.0005 |
| 1-0 | 0.1221 | 0.1210 | 0.0011 |
| 2-1 | 0.0933 | 0.0899 | 0.0034 |
| 0-0 | 0.0835 | 0.1025 | 0.0190 |
| 0-1 | 0.0835 | 0.0868 | 0.0032 |
| 2-0 | 0.0721 | 0.0860 | 0.0139 |
| 1-2 | 0.0661 | 0.0632 | 0.0029 |
| 2-2 | 0.0567 | 0.0484 | 0.0083 |
| 0-2 | 0.0397 | 0.0457 | 0.0060 |
| 3-1 | 0.0378 | 0.0404 | 0.0026 |
| 3-0 | 0.0345 | 0.0406 | 0.0061 |
| 3-2 | 0.0256 | 0.0211 | 0.0045 |
| 1-3 | 0.0220 | 0.0205 | 0.0015 |
| 2-3 | 0.0220 | 0.0148 | 0.0073 |
| 0-3 | 0.0156 | 0.0149 | 0.0006 |
| **Sum (top 15)** | **0.9137** | **0.9345** | — |
- High-score mass (total ≥9 goals): 1.43e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### USA vs Bosnia & Herzegovina
- CS outcomes: 26  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-0 | 0.1331 | 0.1308 | 0.0023 |
| 2-0 | 0.1331 | 0.1365 | 0.0034 |
| 2-1 | 0.0940 | 0.0962 | 0.0022 |
| 1-1 | 0.0887 | 0.0912 | 0.0025 |
| 3-0 | 0.0841 | 0.0934 | 0.0094 |
| 0-0 | 0.0665 | 0.0704 | 0.0039 |
| 3-1 | 0.0614 | 0.0660 | 0.0045 |
| 4-0 | 0.0470 | 0.0506 | 0.0036 |
| 0-1 | 0.0420 | 0.0442 | 0.0021 |
| 2-2 | 0.0347 | 0.0336 | 0.0011 |
| 4-1 | 0.0307 | 0.0343 | 0.0035 |
| 1-2 | 0.0307 | 0.0314 | 0.0007 |
| 3-2 | 0.0258 | 0.0239 | 0.0019 |
| 5-0 | 0.0222 | 0.0214 | 0.0007 |
| 0-2 | 0.0157 | 0.0154 | 0.0003 |
| **Sum (top 15)** | **0.9097** | **0.9392** | — |
- High-score mass (total ≥9 goals): 1.94e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS
