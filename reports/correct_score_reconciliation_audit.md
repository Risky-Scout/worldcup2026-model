# Correct-Score Reconciliation Audit

**Generated**: 2026-06-28T00:53:20Z

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
- CS outcomes: 27  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 0-2 | 0.1430 | 0.1505 | 0.0075 |
| 0-3 | 0.1335 | 0.1296 | 0.0038 |
| 0-1 | 0.0942 | 0.1216 | 0.0273 |
| 0-4 | 0.0942 | 0.0964 | 0.0022 |
| 1-2 | 0.0616 | 0.0727 | 0.0111 |
| 1-3 | 0.0616 | 0.0736 | 0.0120 |
| 0-5 | 0.0572 | 0.0541 | 0.0031 |
| 1-1 | 0.0471 | 0.0515 | 0.0044 |
| 1-4 | 0.0445 | 0.0512 | 0.0067 |
| 0-0 | 0.0422 | 0.0381 | 0.0040 |
| 0-6 | 0.0308 | 0.0221 | 0.0087 |
| 1-5 | 0.0258 | 0.0221 | 0.0037 |
| 1-0 | 0.0222 | 0.0243 | 0.0020 |
| 2-2 | 0.0174 | 0.0207 | 0.0033 |
| 2-3 | 0.0174 | 0.0214 | 0.0040 |
| **Sum (top 15)** | **0.8929** | **0.9501** | — |
- High-score mass (total ≥9 goals): 2.56e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Algeria vs Austria
- CS outcomes: 19  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 0-0 | 0.1955 | 0.2348 | 0.0392 |
| 1-1 | 0.1769 | 0.1970 | 0.0201 |
| 0-1 | 0.1548 | 0.1256 | 0.0292 |
| 1-0 | 0.0991 | 0.1175 | 0.0185 |
| 0-2 | 0.0708 | 0.0719 | 0.0011 |
| 1-2 | 0.0675 | 0.0475 | 0.0201 |
| 2-1 | 0.0464 | 0.0518 | 0.0054 |
| 2-2 | 0.0413 | 0.0226 | 0.0186 |
| 2-0 | 0.0323 | 0.0727 | 0.0404 |
| 0-3 | 0.0240 | 0.0137 | 0.0103 |
| 1-3 | 0.0240 | 0.0073 | 0.0166 |
| 3-1 | 0.0122 | 0.0092 | 0.0030 |
| 2-3 | 0.0122 | 0.0018 | 0.0104 |
| 3-0 | 0.0092 | 0.0168 | 0.0076 |
| 3-2 | 0.0092 | 0.0023 | 0.0068 |
| **Sum (top 15)** | **0.9753** | **0.9924** | — |
- High-score mass (total ≥9 goals): 7.44e-08
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### South Africa vs Canada
- CS outcomes: 25  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 0-1 | 0.1429 | 0.1381 | 0.0047 |
| 1-1 | 0.1231 | 0.1213 | 0.0018 |
| 0-2 | 0.1067 | 0.1166 | 0.0100 |
| 1-2 | 0.1000 | 0.0966 | 0.0034 |
| 0-0 | 0.0842 | 0.0964 | 0.0122 |
| 1-0 | 0.0615 | 0.0661 | 0.0046 |
| 0-3 | 0.0571 | 0.0651 | 0.0079 |
| 2-2 | 0.0471 | 0.0396 | 0.0075 |
| 1-3 | 0.0471 | 0.0513 | 0.0042 |
| 2-1 | 0.0444 | 0.0440 | 0.0004 |
| 2-0 | 0.0258 | 0.0273 | 0.0015 |
| 2-3 | 0.0258 | 0.0213 | 0.0045 |
| 0-4 | 0.0258 | 0.0281 | 0.0023 |
| 1-4 | 0.0222 | 0.0219 | 0.0003 |
| 3-2 | 0.0131 | 0.0094 | 0.0037 |
| **Sum (top 15)** | **0.9268** | **0.9431** | — |
- High-score mass (total ≥9 goals): 1.45e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Brazil vs Japan
- CS outcomes: 27  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-0 | 0.1231 | 0.1244 | 0.0013 |
| 2-0 | 0.1067 | 0.1120 | 0.0053 |
| 1-1 | 0.1067 | 0.1134 | 0.0067 |
| 2-1 | 0.0941 | 0.0965 | 0.0023 |
| 0-0 | 0.0727 | 0.0836 | 0.0109 |
| 3-0 | 0.0616 | 0.0655 | 0.0040 |
| 0-1 | 0.0616 | 0.0646 | 0.0030 |
| 3-1 | 0.0533 | 0.0561 | 0.0028 |
| 1-2 | 0.0471 | 0.0483 | 0.0013 |
| 2-2 | 0.0445 | 0.0444 | 0.0000 |
| 0-2 | 0.0308 | 0.0297 | 0.0011 |
| 4-0 | 0.0286 | 0.0289 | 0.0004 |
| 3-2 | 0.0258 | 0.0251 | 0.0007 |
| 4-1 | 0.0258 | 0.0248 | 0.0010 |
| 1-3 | 0.0174 | 0.0143 | 0.0031 |
| **Sum (top 15)** | **0.8997** | **0.9318** | — |
- High-score mass (total ≥9 goals): 1.75e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Germany vs Paraguay
- CS outcomes: 27  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 2-0 | 0.1223 | 0.1301 | 0.0078 |
| 1-0 | 0.1136 | 0.1170 | 0.0035 |
| 2-1 | 0.0935 | 0.0970 | 0.0035 |
| 3-0 | 0.0883 | 0.0955 | 0.0071 |
| 1-1 | 0.0837 | 0.0892 | 0.0055 |
| 3-1 | 0.0723 | 0.0724 | 0.0001 |
| 0-0 | 0.0530 | 0.0617 | 0.0087 |
| 4-0 | 0.0468 | 0.0527 | 0.0059 |
| 4-1 | 0.0379 | 0.0389 | 0.0010 |
| 2-2 | 0.0379 | 0.0361 | 0.0017 |
| 0-1 | 0.0379 | 0.0410 | 0.0032 |
| 1-2 | 0.0346 | 0.0325 | 0.0020 |
| 3-2 | 0.0284 | 0.0269 | 0.0015 |
| 5-0 | 0.0256 | 0.0239 | 0.0017 |
| 5-1 | 0.0194 | 0.0172 | 0.0022 |
| **Sum (top 15)** | **0.8952** | **0.9322** | — |
- High-score mass (total ≥9 goals): 2.17e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Netherlands vs Morocco
- CS outcomes: 25  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-1 | 0.1342 | 0.1382 | 0.0040 |
| 1-0 | 0.1150 | 0.1167 | 0.0016 |
| 2-1 | 0.0895 | 0.0889 | 0.0005 |
| 0-0 | 0.0848 | 0.1045 | 0.0197 |
| 2-0 | 0.0805 | 0.0896 | 0.0091 |
| 0-1 | 0.0805 | 0.0837 | 0.0032 |
| 1-2 | 0.0671 | 0.0627 | 0.0044 |
| 2-2 | 0.0503 | 0.0478 | 0.0025 |
| 3-1 | 0.0424 | 0.0422 | 0.0002 |
| 3-0 | 0.0403 | 0.0429 | 0.0026 |
| 0-2 | 0.0403 | 0.0446 | 0.0044 |
| 3-2 | 0.0260 | 0.0214 | 0.0046 |
| 1-3 | 0.0260 | 0.0206 | 0.0054 |
| 2-3 | 0.0196 | 0.0144 | 0.0052 |
| 4-1 | 0.0158 | 0.0148 | 0.0010 |
| **Sum (top 15)** | **0.9122** | **0.9330** | — |
- High-score mass (total ≥9 goals): 1.46e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Côte d'Ivoire vs Norway
- CS outcomes: 27  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-1 | 0.1313 | 0.1284 | 0.0029 |
| 0-1 | 0.1050 | 0.1009 | 0.0042 |
| 1-2 | 0.0927 | 0.0944 | 0.0017 |
| 1-0 | 0.0716 | 0.0720 | 0.0004 |
| 0-2 | 0.0716 | 0.0816 | 0.0100 |
| 2-1 | 0.0657 | 0.0669 | 0.0013 |
| 0-0 | 0.0657 | 0.0786 | 0.0129 |
| 2-2 | 0.0606 | 0.0568 | 0.0038 |
| 1-3 | 0.0463 | 0.0496 | 0.0033 |
| 2-0 | 0.0394 | 0.0429 | 0.0035 |
| 0-3 | 0.0375 | 0.0444 | 0.0069 |
| 2-3 | 0.0281 | 0.0285 | 0.0003 |
| 3-1 | 0.0254 | 0.0253 | 0.0001 |
| 3-2 | 0.0254 | 0.0204 | 0.0050 |
| 1-4 | 0.0192 | 0.0198 | 0.0006 |
| **Sum (top 15)** | **0.8856** | **0.9104** | — |
- High-score mass (total ≥9 goals): 2.08e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### France vs Sweden
- CS outcomes: 29  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 2-0 | 0.1137 | 0.1250 | 0.0113 |
| 1-0 | 0.0995 | 0.1049 | 0.0053 |
| 2-1 | 0.0937 | 0.0975 | 0.0038 |
| 3-0 | 0.0937 | 0.1039 | 0.0102 |
| 1-1 | 0.0758 | 0.0768 | 0.0010 |
| 3-1 | 0.0724 | 0.0783 | 0.0059 |
| 4-0 | 0.0569 | 0.0647 | 0.0078 |
| 4-1 | 0.0442 | 0.0481 | 0.0039 |
| 0-0 | 0.0419 | 0.0461 | 0.0042 |
| 2-2 | 0.0379 | 0.0355 | 0.0024 |
| 3-2 | 0.0306 | 0.0305 | 0.0001 |
| 5-0 | 0.0306 | 0.0325 | 0.0019 |
| 0-1 | 0.0284 | 0.0319 | 0.0035 |
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
| 2-0 | 0.1351 | 0.1358 | 0.0006 |
| 1-0 | 0.1329 | 0.1271 | 0.0058 |
| 2-1 | 0.0938 | 0.0964 | 0.0026 |
| 3-0 | 0.0886 | 0.0959 | 0.0073 |
| 1-1 | 0.0886 | 0.0901 | 0.0015 |
| 0-0 | 0.0664 | 0.0684 | 0.0019 |
| 3-1 | 0.0613 | 0.0669 | 0.0055 |
| 4-0 | 0.0469 | 0.0517 | 0.0048 |
| 0-1 | 0.0399 | 0.0423 | 0.0024 |
| 2-2 | 0.0347 | 0.0342 | 0.0005 |
| 4-1 | 0.0307 | 0.0353 | 0.0046 |
| 1-2 | 0.0285 | 0.0313 | 0.0029 |
| 3-2 | 0.0235 | 0.0241 | 0.0007 |
| 5-0 | 0.0235 | 0.0225 | 0.0009 |
| 5-1 | 0.0156 | 0.0152 | 0.0005 |
| **Sum (top 15)** | **0.9100** | **0.9372** | — |
- High-score mass (total ≥9 goals): 2.01e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Australia vs Egypt
- CS outcomes: 23  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-1 | 0.1474 | 0.1461 | 0.0013 |
| 0-1 | 0.1247 | 0.1392 | 0.0145 |
| 1-0 | 0.1081 | 0.1182 | 0.0101 |
| 0-0 | 0.1013 | 0.1337 | 0.0324 |
| 1-2 | 0.0853 | 0.0782 | 0.0071 |
| 2-1 | 0.0737 | 0.0646 | 0.0091 |
| 0-2 | 0.0676 | 0.0810 | 0.0135 |
| 2-2 | 0.0507 | 0.0378 | 0.0128 |
| 2-0 | 0.0450 | 0.0558 | 0.0107 |
| 0-3 | 0.0290 | 0.0303 | 0.0014 |
| 1-3 | 0.0290 | 0.0261 | 0.0028 |
| 3-1 | 0.0225 | 0.0176 | 0.0049 |
| 2-3 | 0.0225 | 0.0116 | 0.0109 |
| 3-0 | 0.0176 | 0.0169 | 0.0007 |
| 3-2 | 0.0176 | 0.0091 | 0.0085 |
| **Sum (top 15)** | **0.9420** | **0.9663** | — |
- High-score mass (total ≥9 goals): 5.55e-06
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Argentina vs Cabo Verde
- CS outcomes: 28  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 2-0 | 0.1384 | 0.1542 | 0.0159 |
| 3-0 | 0.1213 | 0.1303 | 0.0090 |
| 1-0 | 0.1127 | 0.1328 | 0.0202 |
| 2-1 | 0.0789 | 0.0828 | 0.0039 |
| 4-0 | 0.0751 | 0.0845 | 0.0094 |
| 3-1 | 0.0657 | 0.0703 | 0.0046 |
| 1-1 | 0.0607 | 0.0585 | 0.0021 |
| 4-1 | 0.0438 | 0.0455 | 0.0017 |
| 5-0 | 0.0438 | 0.0457 | 0.0019 |
| 0-0 | 0.0415 | 0.0451 | 0.0036 |
| 5-1 | 0.0254 | 0.0220 | 0.0034 |
| 2-2 | 0.0254 | 0.0190 | 0.0064 |
| 3-2 | 0.0219 | 0.0189 | 0.0031 |
| 6-0 | 0.0219 | 0.0198 | 0.0021 |
| 0-1 | 0.0219 | 0.0254 | 0.0035 |
| **Sum (top 15)** | **0.8984** | **0.9550** | — |
- High-score mass (total ≥9 goals): 2.31e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS
