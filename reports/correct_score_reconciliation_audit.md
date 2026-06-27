# Correct-Score Reconciliation Audit

**Generated**: 2026-06-27T07:52:54Z

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
- CS outcomes: 30  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 0-2 | 0.1199 | 0.1275 | 0.0076 |
| 0-3 | 0.1199 | 0.1264 | 0.0065 |
| 0-4 | 0.0866 | 0.0903 | 0.0037 |
| 0-1 | 0.0780 | 0.0871 | 0.0091 |
| 1-3 | 0.0709 | 0.0829 | 0.0120 |
| 1-2 | 0.0650 | 0.0848 | 0.0198 |
| 1-4 | 0.0520 | 0.0614 | 0.0095 |
| 0-5 | 0.0520 | 0.0535 | 0.0015 |
| 1-1 | 0.0487 | 0.0554 | 0.0067 |
| 0-0 | 0.0339 | 0.0295 | 0.0044 |
| 1-5 | 0.0339 | 0.0224 | 0.0115 |
| 0-6 | 0.0278 | 0.0224 | 0.0055 |
| 2-2 | 0.0251 | 0.0285 | 0.0034 |
| 1-0 | 0.0217 | 0.0205 | 0.0012 |
| 2-3 | 0.0217 | 0.0307 | 0.0090 |
| **Sum (top 15)** | **0.8570** | **0.9231** | — |
- High-score mass (total ≥9 goals): 3.36e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Croatia vs Ghana
- CS outcomes: 22  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-0 | 0.1483 | 0.1290 | 0.0193 |
| 1-1 | 0.1407 | 0.1524 | 0.0117 |
| 2-1 | 0.0960 | 0.0888 | 0.0072 |
| 0-0 | 0.0960 | 0.1258 | 0.0298 |
| 2-0 | 0.0907 | 0.1007 | 0.0101 |
| 0-1 | 0.0742 | 0.0700 | 0.0042 |
| 1-2 | 0.0544 | 0.0465 | 0.0079 |
| 2-2 | 0.0510 | 0.0457 | 0.0053 |
| 3-0 | 0.0429 | 0.0520 | 0.0091 |
| 3-1 | 0.0429 | 0.0435 | 0.0006 |
| 0-2 | 0.0291 | 0.0298 | 0.0007 |
| 3-2 | 0.0263 | 0.0186 | 0.0078 |
| 4-0 | 0.0177 | 0.0207 | 0.0030 |
| 4-1 | 0.0160 | 0.0165 | 0.0005 |
| 2-3 | 0.0146 | 0.0090 | 0.0056 |
| **Sum (top 15)** | **0.9409** | **0.9491** | — |
- High-score mass (total ≥9 goals): 1.23e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Colombia vs Portugal
- CS outcomes: 28  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-1 | 0.1049 | 0.1289 | 0.0240 |
| 0-1 | 0.0926 | 0.0942 | 0.0016 |
| 1-2 | 0.0874 | 0.0895 | 0.0021 |
| 0-2 | 0.0787 | 0.0811 | 0.0024 |
| 1-0 | 0.0656 | 0.0671 | 0.0015 |
| 2-1 | 0.0656 | 0.0641 | 0.0015 |
| 0-0 | 0.0562 | 0.0779 | 0.0217 |
| 2-2 | 0.0562 | 0.0650 | 0.0088 |
| 1-3 | 0.0525 | 0.0512 | 0.0012 |
| 2-0 | 0.0437 | 0.0416 | 0.0021 |
| 0-3 | 0.0414 | 0.0446 | 0.0032 |
| 2-3 | 0.0342 | 0.0304 | 0.0038 |
| 3-1 | 0.0303 | 0.0257 | 0.0046 |
| 3-2 | 0.0254 | 0.0208 | 0.0045 |
| 1-4 | 0.0231 | 0.0212 | 0.0019 |
| **Sum (top 15)** | **0.8579** | **0.9035** | — |
- High-score mass (total ≥9 goals): 2.21e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### DR Congo vs Uzbekistan
- CS outcomes: 27  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-0 | 0.1319 | 0.1383 | 0.0063 |
| 2-0 | 0.1131 | 0.1186 | 0.0056 |
| 1-1 | 0.0990 | 0.1054 | 0.0065 |
| 2-1 | 0.0880 | 0.0936 | 0.0057 |
| 0-0 | 0.0754 | 0.0816 | 0.0062 |
| 3-0 | 0.0720 | 0.0711 | 0.0008 |
| 0-1 | 0.0609 | 0.0664 | 0.0055 |
| 3-1 | 0.0528 | 0.0559 | 0.0031 |
| 1-2 | 0.0440 | 0.0451 | 0.0011 |
| 2-2 | 0.0377 | 0.0397 | 0.0020 |
| 4-0 | 0.0344 | 0.0313 | 0.0031 |
| 0-2 | 0.0304 | 0.0284 | 0.0020 |
| 4-1 | 0.0255 | 0.0247 | 0.0008 |
| 3-2 | 0.0233 | 0.0236 | 0.0003 |
| 1-3 | 0.0155 | 0.0127 | 0.0028 |
| **Sum (top 15)** | **0.9039** | **0.9366** | — |
- High-score mass (total ≥9 goals): 1.64e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Jordan vs Argentina
- CS outcomes: 27  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 0-2 | 0.1422 | 0.1415 | 0.0007 |
| 0-3 | 0.1328 | 0.1346 | 0.0018 |
| 0-1 | 0.0937 | 0.0973 | 0.0036 |
| 0-4 | 0.0937 | 0.0908 | 0.0029 |
| 1-3 | 0.0664 | 0.0764 | 0.0101 |
| 1-2 | 0.0613 | 0.0825 | 0.0212 |
| 0-5 | 0.0531 | 0.0517 | 0.0014 |
| 1-1 | 0.0469 | 0.0552 | 0.0083 |
| 0-0 | 0.0443 | 0.0342 | 0.0100 |
| 1-4 | 0.0443 | 0.0545 | 0.0102 |
| 0-6 | 0.0284 | 0.0222 | 0.0062 |
| 1-0 | 0.0257 | 0.0214 | 0.0043 |
| 1-5 | 0.0257 | 0.0222 | 0.0035 |
| 2-1 | 0.0173 | 0.0193 | 0.0020 |
| 2-2 | 0.0173 | 0.0239 | 0.0066 |
| **Sum (top 15)** | **0.8930** | **0.9277** | — |
- High-score mass (total ≥9 goals): 3.16e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Algeria vs Austria
- CS outcomes: 19  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 0-0 | 0.1780 | 0.2188 | 0.0408 |
| 1-1 | 0.1664 | 0.1925 | 0.0262 |
| 0-1 | 0.1629 | 0.1394 | 0.0235 |
| 1-0 | 0.1021 | 0.1048 | 0.0027 |
| 0-2 | 0.0729 | 0.0897 | 0.0168 |
| 1-2 | 0.0696 | 0.0574 | 0.0122 |
| 2-1 | 0.0478 | 0.0468 | 0.0011 |
| 2-2 | 0.0425 | 0.0251 | 0.0174 |
| 2-0 | 0.0333 | 0.0583 | 0.0251 |
| 0-3 | 0.0294 | 0.0231 | 0.0064 |
| 1-3 | 0.0247 | 0.0114 | 0.0133 |
| 3-1 | 0.0125 | 0.0073 | 0.0053 |
| 2-3 | 0.0125 | 0.0026 | 0.0100 |
| 3-0 | 0.0095 | 0.0112 | 0.0018 |
| 3-2 | 0.0095 | 0.0022 | 0.0072 |
| **Sum (top 15)** | **0.9736** | **0.9907** | — |
- High-score mass (total ≥9 goals): 1.64e-07
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### South Africa vs Canada
- CS outcomes: 24  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 0-1 | 0.1399 | 0.1401 | 0.0002 |
| 1-1 | 0.1159 | 0.1193 | 0.0034 |
| 0-2 | 0.1082 | 0.1172 | 0.0090 |
| 1-2 | 0.0954 | 0.0944 | 0.0011 |
| 0-0 | 0.0854 | 0.0986 | 0.0132 |
| 1-0 | 0.0676 | 0.0701 | 0.0025 |
| 0-3 | 0.0541 | 0.0627 | 0.0087 |
| 1-3 | 0.0507 | 0.0512 | 0.0005 |
| 2-1 | 0.0451 | 0.0443 | 0.0008 |
| 2-2 | 0.0451 | 0.0393 | 0.0058 |
| 2-0 | 0.0290 | 0.0288 | 0.0002 |
| 2-3 | 0.0262 | 0.0209 | 0.0052 |
| 0-4 | 0.0262 | 0.0269 | 0.0007 |
| 1-4 | 0.0225 | 0.0210 | 0.0015 |
| 3-1 | 0.0133 | 0.0115 | 0.0018 |
| **Sum (top 15)** | **0.9245** | **0.9462** | — |
- High-score mass (total ≥9 goals): 1.41e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Brazil vs Japan
- CS outcomes: 27  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-0 | 0.1231 | 0.1245 | 0.0014 |
| 1-1 | 0.1143 | 0.1160 | 0.0017 |
| 2-0 | 0.1067 | 0.1125 | 0.0059 |
| 2-1 | 0.0941 | 0.0967 | 0.0025 |
| 0-0 | 0.0727 | 0.0837 | 0.0109 |
| 0-1 | 0.0615 | 0.0645 | 0.0029 |
| 3-0 | 0.0571 | 0.0645 | 0.0073 |
| 3-1 | 0.0533 | 0.0561 | 0.0027 |
| 2-2 | 0.0471 | 0.0442 | 0.0029 |
| 1-2 | 0.0471 | 0.0481 | 0.0010 |
| 3-2 | 0.0286 | 0.0253 | 0.0032 |
| 4-0 | 0.0286 | 0.0290 | 0.0005 |
| 0-2 | 0.0286 | 0.0291 | 0.0005 |
| 4-1 | 0.0258 | 0.0248 | 0.0010 |
| 1-3 | 0.0157 | 0.0139 | 0.0018 |
| **Sum (top 15)** | **0.9043** | **0.9328** | — |
- High-score mass (total ≥9 goals): 1.73e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Netherlands vs Morocco
- CS outcomes: 27  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-1 | 0.1326 | 0.1366 | 0.0040 |
| 1-0 | 0.1137 | 0.1172 | 0.0035 |
| 2-1 | 0.0884 | 0.0888 | 0.0004 |
| 0-0 | 0.0838 | 0.1027 | 0.0189 |
| 0-1 | 0.0838 | 0.0860 | 0.0022 |
| 2-0 | 0.0758 | 0.0874 | 0.0116 |
| 1-2 | 0.0663 | 0.0632 | 0.0031 |
| 2-2 | 0.0497 | 0.0479 | 0.0019 |
| 0-2 | 0.0442 | 0.0464 | 0.0022 |
| 3-1 | 0.0398 | 0.0415 | 0.0017 |
| 3-0 | 0.0379 | 0.0418 | 0.0040 |
| 3-2 | 0.0257 | 0.0216 | 0.0041 |
| 1-3 | 0.0257 | 0.0212 | 0.0045 |
| 2-3 | 0.0194 | 0.0147 | 0.0047 |
| 0-3 | 0.0173 | 0.0151 | 0.0022 |
| **Sum (top 15)** | **0.9041** | **0.9322** | — |
- High-score mass (total ≥9 goals): 1.46e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### USA vs Bosnia & Herzegovina
- CS outcomes: 26  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-0 | 0.1331 | 0.1312 | 0.0019 |
| 2-0 | 0.1331 | 0.1367 | 0.0036 |
| 2-1 | 0.0940 | 0.0962 | 0.0022 |
| 1-1 | 0.0887 | 0.0913 | 0.0026 |
| 3-0 | 0.0841 | 0.0934 | 0.0093 |
| 0-0 | 0.0665 | 0.0705 | 0.0039 |
| 3-1 | 0.0614 | 0.0658 | 0.0044 |
| 4-0 | 0.0470 | 0.0505 | 0.0035 |
| 0-1 | 0.0420 | 0.0443 | 0.0022 |
| 2-2 | 0.0347 | 0.0335 | 0.0012 |
| 4-1 | 0.0307 | 0.0342 | 0.0034 |
| 1-2 | 0.0307 | 0.0314 | 0.0007 |
| 3-2 | 0.0258 | 0.0238 | 0.0020 |
| 5-0 | 0.0222 | 0.0214 | 0.0008 |
| 0-2 | 0.0157 | 0.0154 | 0.0002 |
| **Sum (top 15)** | **0.9097** | **0.9395** | — |
- High-score mass (total ≥9 goals): 1.93e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS
