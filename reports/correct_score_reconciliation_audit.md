# Correct-Score Reconciliation Audit

**Generated**: 2026-06-28T03:56:14Z

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

### South Africa vs Canada
- CS outcomes: 25  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 0-1 | 0.1369 | 0.1358 | 0.0011 |
| 1-1 | 0.1243 | 0.1239 | 0.0004 |
| 0-2 | 0.1010 | 0.1149 | 0.0139 |
| 1-2 | 0.1010 | 0.0967 | 0.0043 |
| 0-0 | 0.0769 | 0.0953 | 0.0183 |
| 1-0 | 0.0621 | 0.0671 | 0.0049 |
| 0-3 | 0.0577 | 0.0645 | 0.0067 |
| 2-2 | 0.0505 | 0.0406 | 0.0099 |
| 1-3 | 0.0505 | 0.0519 | 0.0014 |
| 2-1 | 0.0449 | 0.0442 | 0.0007 |
| 2-0 | 0.0261 | 0.0281 | 0.0020 |
| 2-3 | 0.0261 | 0.0213 | 0.0047 |
| 0-4 | 0.0261 | 0.0276 | 0.0015 |
| 1-4 | 0.0238 | 0.0218 | 0.0019 |
| 3-2 | 0.0144 | 0.0095 | 0.0049 |
| **Sum (top 15)** | **0.9222** | **0.9431** | — |
- High-score mass (total ≥9 goals): 1.45e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Brazil vs Japan
- CS outcomes: 27  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-0 | 0.1231 | 0.1252 | 0.0021 |
| 2-0 | 0.1067 | 0.1120 | 0.0054 |
| 1-1 | 0.1067 | 0.1137 | 0.0070 |
| 2-1 | 0.0941 | 0.0962 | 0.0021 |
| 0-0 | 0.0727 | 0.0842 | 0.0115 |
| 3-0 | 0.0616 | 0.0651 | 0.0035 |
| 0-1 | 0.0616 | 0.0654 | 0.0038 |
| 3-1 | 0.0533 | 0.0557 | 0.0024 |
| 1-2 | 0.0471 | 0.0485 | 0.0014 |
| 2-2 | 0.0445 | 0.0443 | 0.0002 |
| 0-2 | 0.0308 | 0.0300 | 0.0007 |
| 4-0 | 0.0286 | 0.0285 | 0.0001 |
| 3-2 | 0.0258 | 0.0248 | 0.0010 |
| 4-1 | 0.0258 | 0.0245 | 0.0014 |
| 1-3 | 0.0174 | 0.0144 | 0.0030 |
| **Sum (top 15)** | **0.8997** | **0.9325** | — |
- High-score mass (total ≥9 goals): 1.73e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Germany vs Paraguay
- CS outcomes: 27  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 2-0 | 0.1223 | 0.1294 | 0.0070 |
| 1-0 | 0.1136 | 0.1136 | 0.0000 |
| 2-1 | 0.0935 | 0.0974 | 0.0038 |
| 3-0 | 0.0883 | 0.0970 | 0.0087 |
| 1-1 | 0.0837 | 0.0875 | 0.0038 |
| 3-1 | 0.0723 | 0.0736 | 0.0014 |
| 0-0 | 0.0530 | 0.0597 | 0.0067 |
| 4-0 | 0.0468 | 0.0545 | 0.0077 |
| 4-1 | 0.0379 | 0.0404 | 0.0026 |
| 2-2 | 0.0379 | 0.0364 | 0.0014 |
| 0-1 | 0.0379 | 0.0387 | 0.0008 |
| 1-2 | 0.0346 | 0.0320 | 0.0025 |
| 3-2 | 0.0284 | 0.0276 | 0.0008 |
| 5-0 | 0.0256 | 0.0254 | 0.0003 |
| 5-1 | 0.0194 | 0.0181 | 0.0012 |
| **Sum (top 15)** | **0.8952** | **0.9313** | — |
- High-score mass (total ≥9 goals): 2.22e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Netherlands vs Morocco
- CS outcomes: 26  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-1 | 0.1331 | 0.1377 | 0.0046 |
| 1-0 | 0.1229 | 0.1199 | 0.0030 |
| 2-1 | 0.0940 | 0.0902 | 0.0038 |
| 0-0 | 0.0841 | 0.1045 | 0.0204 |
| 0-1 | 0.0799 | 0.0839 | 0.0040 |
| 2-0 | 0.0761 | 0.0881 | 0.0121 |
| 1-2 | 0.0666 | 0.0626 | 0.0039 |
| 2-2 | 0.0570 | 0.0491 | 0.0079 |
| 3-1 | 0.0399 | 0.0413 | 0.0014 |
| 0-2 | 0.0380 | 0.0443 | 0.0062 |
| 3-0 | 0.0347 | 0.0414 | 0.0067 |
| 3-2 | 0.0285 | 0.0215 | 0.0070 |
| 1-3 | 0.0222 | 0.0201 | 0.0021 |
| 2-3 | 0.0195 | 0.0144 | 0.0051 |
| 4-1 | 0.0157 | 0.0147 | 0.0010 |
| **Sum (top 15)** | **0.9120** | **0.9337** | — |
- High-score mass (total ≥9 goals): 1.45e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Côte d'Ivoire vs Norway
- CS outcomes: 27  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-1 | 0.1220 | 0.1247 | 0.0027 |
| 0-1 | 0.1058 | 0.0989 | 0.0068 |
| 1-2 | 0.0933 | 0.0946 | 0.0012 |
| 0-2 | 0.0793 | 0.0833 | 0.0040 |
| 1-0 | 0.0721 | 0.0705 | 0.0016 |
| 2-1 | 0.0661 | 0.0671 | 0.0010 |
| 0-0 | 0.0661 | 0.0782 | 0.0121 |
| 2-2 | 0.0567 | 0.0574 | 0.0007 |
| 1-3 | 0.0467 | 0.0503 | 0.0036 |
| 0-3 | 0.0417 | 0.0458 | 0.0040 |
| 2-0 | 0.0378 | 0.0416 | 0.0038 |
| 2-3 | 0.0283 | 0.0290 | 0.0006 |
| 3-1 | 0.0256 | 0.0255 | 0.0001 |
| 3-2 | 0.0220 | 0.0204 | 0.0016 |
| 1-4 | 0.0220 | 0.0207 | 0.0013 |
| **Sum (top 15)** | **0.8855** | **0.9079** | — |
- High-score mass (total ≥9 goals): 2.15e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### France vs Sweden
- CS outcomes: 28  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 2-0 | 0.1221 | 0.1277 | 0.0055 |
| 1-0 | 0.0992 | 0.1057 | 0.0065 |
| 3-0 | 0.0992 | 0.1047 | 0.0054 |
| 2-1 | 0.0934 | 0.0967 | 0.0033 |
| 3-1 | 0.0722 | 0.0771 | 0.0049 |
| 1-1 | 0.0722 | 0.0765 | 0.0043 |
| 4-0 | 0.0611 | 0.0643 | 0.0033 |
| 4-1 | 0.0441 | 0.0469 | 0.0027 |
| 0-0 | 0.0418 | 0.0468 | 0.0050 |
| 2-2 | 0.0345 | 0.0355 | 0.0009 |
| 5-0 | 0.0305 | 0.0313 | 0.0008 |
| 3-2 | 0.0284 | 0.0295 | 0.0012 |
| 0-1 | 0.0284 | 0.0330 | 0.0046 |
| 1-2 | 0.0256 | 0.0290 | 0.0034 |
| 5-1 | 0.0234 | 0.0220 | 0.0014 |
| **Sum (top 15)** | **0.8761** | **0.9266** | — |
- High-score mass (total ≥9 goals): 2.51e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### USA vs Bosnia & Herzegovina
- CS outcomes: 26  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-0 | 0.1320 | 0.1293 | 0.0027 |
| 2-0 | 0.1320 | 0.1359 | 0.0039 |
| 2-1 | 0.0932 | 0.0957 | 0.0025 |
| 3-0 | 0.0880 | 0.0957 | 0.0077 |
| 1-1 | 0.0834 | 0.0888 | 0.0054 |
| 3-1 | 0.0609 | 0.0665 | 0.0056 |
| 0-0 | 0.0609 | 0.0670 | 0.0061 |
| 4-0 | 0.0528 | 0.0535 | 0.0007 |
| 0-1 | 0.0377 | 0.0421 | 0.0044 |
| 4-1 | 0.0344 | 0.0360 | 0.0016 |
| 2-2 | 0.0344 | 0.0338 | 0.0006 |
| 1-2 | 0.0305 | 0.0309 | 0.0005 |
| 3-2 | 0.0256 | 0.0242 | 0.0013 |
| 5-0 | 0.0233 | 0.0227 | 0.0006 |
| 5-1 | 0.0172 | 0.0153 | 0.0019 |
| **Sum (top 15)** | **0.9064** | **0.9375** | — |
- High-score mass (total ≥9 goals): 2.02e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Australia vs Egypt
- CS outcomes: 22  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-1 | 0.1462 | 0.1457 | 0.0005 |
| 0-1 | 0.1364 | 0.1404 | 0.0039 |
| 0-0 | 0.1170 | 0.1369 | 0.0200 |
| 1-0 | 0.1092 | 0.1162 | 0.0070 |
| 1-2 | 0.0780 | 0.0757 | 0.0022 |
| 2-1 | 0.0682 | 0.0640 | 0.0043 |
| 0-2 | 0.0682 | 0.0814 | 0.0131 |
| 2-0 | 0.0482 | 0.0578 | 0.0097 |
| 2-2 | 0.0455 | 0.0365 | 0.0090 |
| 0-3 | 0.0292 | 0.0303 | 0.0010 |
| 1-3 | 0.0292 | 0.0260 | 0.0033 |
| 3-1 | 0.0227 | 0.0180 | 0.0048 |
| 3-0 | 0.0178 | 0.0174 | 0.0004 |
| 2-3 | 0.0178 | 0.0111 | 0.0067 |
| 3-2 | 0.0161 | 0.0091 | 0.0069 |
| **Sum (top 15)** | **0.9497** | **0.9665** | — |
- High-score mass (total ≥9 goals): 5.40e-06
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Argentina vs Cabo Verde
- CS outcomes: 25  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 2-0 | 0.1581 | 0.1601 | 0.0020 |
| 3-0 | 0.1344 | 0.1356 | 0.0012 |
| 1-0 | 0.1152 | 0.1306 | 0.0154 |
| 4-0 | 0.0949 | 0.0914 | 0.0035 |
| 2-1 | 0.0672 | 0.0770 | 0.0098 |
| 3-1 | 0.0576 | 0.0663 | 0.0087 |
| 5-0 | 0.0504 | 0.0472 | 0.0032 |
| 1-1 | 0.0474 | 0.0550 | 0.0076 |
| 0-0 | 0.0448 | 0.0467 | 0.0019 |
| 4-1 | 0.0403 | 0.0438 | 0.0035 |
| 5-1 | 0.0260 | 0.0220 | 0.0040 |
| 6-0 | 0.0260 | 0.0202 | 0.0058 |
| 0-1 | 0.0224 | 0.0249 | 0.0025 |
| 2-2 | 0.0175 | 0.0186 | 0.0011 |
| 3-2 | 0.0144 | 0.0172 | 0.0028 |
| **Sum (top 15)** | **0.9167** | **0.9565** | — |
- High-score mass (total ≥9 goals): 2.31e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS
