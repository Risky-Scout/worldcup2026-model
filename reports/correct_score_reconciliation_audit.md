# Correct-Score Reconciliation Audit

**Generated**: 2026-06-27T10:01:56Z

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
- CS outcomes: 31  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 0-2 | 0.1198 | 0.1265 | 0.0066 |
| 0-3 | 0.1198 | 0.1262 | 0.0064 |
| 0-4 | 0.0916 | 0.0932 | 0.0016 |
| 0-1 | 0.0779 | 0.0853 | 0.0074 |
| 1-2 | 0.0649 | 0.0847 | 0.0198 |
| 1-3 | 0.0649 | 0.0817 | 0.0168 |
| 1-4 | 0.0519 | 0.0628 | 0.0109 |
| 0-5 | 0.0519 | 0.0547 | 0.0028 |
| 1-1 | 0.0458 | 0.0538 | 0.0080 |
| 0-0 | 0.0339 | 0.0282 | 0.0056 |
| 1-5 | 0.0339 | 0.0224 | 0.0114 |
| 0-6 | 0.0278 | 0.0224 | 0.0054 |
| 2-2 | 0.0251 | 0.0289 | 0.0038 |
| 1-0 | 0.0216 | 0.0198 | 0.0018 |
| 2-3 | 0.0216 | 0.0315 | 0.0099 |
| **Sum (top 15)** | **0.8525** | **0.9223** | — |
- High-score mass (total ≥9 goals): 3.45e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Croatia vs Ghana
- CS outcomes: 22  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-0 | 0.1483 | 0.1282 | 0.0201 |
| 1-1 | 0.1407 | 0.1531 | 0.0124 |
| 2-1 | 0.0960 | 0.0887 | 0.0073 |
| 0-0 | 0.0960 | 0.1266 | 0.0306 |
| 2-0 | 0.0907 | 0.1004 | 0.0097 |
| 0-1 | 0.0742 | 0.0700 | 0.0042 |
| 1-2 | 0.0544 | 0.0466 | 0.0078 |
| 2-2 | 0.0510 | 0.0460 | 0.0050 |
| 3-0 | 0.0429 | 0.0517 | 0.0088 |
| 3-1 | 0.0429 | 0.0433 | 0.0004 |
| 0-2 | 0.0291 | 0.0299 | 0.0008 |
| 3-2 | 0.0263 | 0.0185 | 0.0078 |
| 4-0 | 0.0177 | 0.0206 | 0.0028 |
| 4-1 | 0.0160 | 0.0164 | 0.0004 |
| 2-3 | 0.0146 | 0.0090 | 0.0055 |
| **Sum (top 15)** | **0.9409** | **0.9491** | — |
- High-score mass (total ≥9 goals): 1.23e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Colombia vs Portugal
- CS outcomes: 30  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-1 | 0.1048 | 0.1267 | 0.0220 |
| 0-1 | 0.0873 | 0.0917 | 0.0044 |
| 1-2 | 0.0873 | 0.0901 | 0.0027 |
| 0-2 | 0.0786 | 0.0805 | 0.0020 |
| 1-0 | 0.0655 | 0.0666 | 0.0011 |
| 2-1 | 0.0655 | 0.0647 | 0.0008 |
| 0-0 | 0.0561 | 0.0744 | 0.0182 |
| 2-2 | 0.0561 | 0.0656 | 0.0095 |
| 1-3 | 0.0524 | 0.0522 | 0.0002 |
| 2-0 | 0.0437 | 0.0414 | 0.0022 |
| 0-3 | 0.0437 | 0.0454 | 0.0018 |
| 2-3 | 0.0302 | 0.0308 | 0.0005 |
| 3-1 | 0.0281 | 0.0260 | 0.0020 |
| 3-2 | 0.0254 | 0.0216 | 0.0037 |
| 1-4 | 0.0254 | 0.0223 | 0.0031 |
| **Sum (top 15)** | **0.8500** | **0.9000** | — |
- High-score mass (total ≥9 goals): 2.30e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### DR Congo vs Uzbekistan
- CS outcomes: 28  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-0 | 0.1308 | 0.1388 | 0.0080 |
| 2-0 | 0.1208 | 0.1225 | 0.0017 |
| 1-1 | 0.0981 | 0.1041 | 0.0059 |
| 2-1 | 0.0872 | 0.0935 | 0.0063 |
| 0-0 | 0.0785 | 0.0822 | 0.0037 |
| 3-0 | 0.0714 | 0.0718 | 0.0004 |
| 0-1 | 0.0654 | 0.0672 | 0.0018 |
| 3-1 | 0.0523 | 0.0558 | 0.0035 |
| 1-2 | 0.0413 | 0.0439 | 0.0025 |
| 4-0 | 0.0341 | 0.0317 | 0.0025 |
| 2-2 | 0.0341 | 0.0384 | 0.0043 |
| 0-2 | 0.0280 | 0.0273 | 0.0008 |
| 4-1 | 0.0253 | 0.0248 | 0.0005 |
| 3-2 | 0.0218 | 0.0231 | 0.0013 |
| 1-3 | 0.0154 | 0.0123 | 0.0031 |
| **Sum (top 15)** | **0.9048** | **0.9374** | — |
- High-score mass (total ≥9 goals): 1.61e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Jordan vs Argentina
- CS outcomes: 27  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 0-2 | 0.1422 | 0.1424 | 0.0002 |
| 0-3 | 0.1328 | 0.1359 | 0.0032 |
| 0-1 | 0.0937 | 0.0975 | 0.0038 |
| 0-4 | 0.0937 | 0.0910 | 0.0027 |
| 1-3 | 0.0664 | 0.0761 | 0.0098 |
| 1-2 | 0.0613 | 0.0829 | 0.0216 |
| 0-5 | 0.0531 | 0.0521 | 0.0010 |
| 1-1 | 0.0469 | 0.0547 | 0.0079 |
| 0-0 | 0.0443 | 0.0337 | 0.0105 |
| 1-4 | 0.0443 | 0.0545 | 0.0102 |
| 0-6 | 0.0284 | 0.0222 | 0.0062 |
| 1-0 | 0.0257 | 0.0210 | 0.0047 |
| 1-5 | 0.0257 | 0.0222 | 0.0035 |
| 2-1 | 0.0173 | 0.0190 | 0.0017 |
| 2-2 | 0.0173 | 0.0232 | 0.0059 |
| **Sum (top 15)** | **0.8930** | **0.9286** | — |
- High-score mass (total ≥9 goals): 3.18e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Algeria vs Austria
- CS outcomes: 19  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 0-0 | 0.1780 | 0.2229 | 0.0449 |
| 1-1 | 0.1664 | 0.1925 | 0.0261 |
| 0-1 | 0.1629 | 0.1414 | 0.0215 |
| 1-0 | 0.1021 | 0.1053 | 0.0033 |
| 0-2 | 0.0729 | 0.0897 | 0.0168 |
| 1-2 | 0.0696 | 0.0565 | 0.0130 |
| 2-1 | 0.0478 | 0.0453 | 0.0025 |
| 2-2 | 0.0425 | 0.0245 | 0.0181 |
| 2-0 | 0.0333 | 0.0570 | 0.0237 |
| 0-3 | 0.0294 | 0.0229 | 0.0065 |
| 1-3 | 0.0247 | 0.0111 | 0.0136 |
| 3-1 | 0.0125 | 0.0068 | 0.0058 |
| 2-3 | 0.0125 | 0.0024 | 0.0101 |
| 3-0 | 0.0095 | 0.0106 | 0.0012 |
| 3-2 | 0.0095 | 0.0021 | 0.0074 |
| **Sum (top 15)** | **0.9736** | **0.9911** | — |
- High-score mass (total ≥9 goals): 1.25e-07
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### South Africa vs Canada
- CS outcomes: 24  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 0-1 | 0.1399 | 0.1403 | 0.0004 |
| 1-1 | 0.1159 | 0.1204 | 0.0045 |
| 0-2 | 0.1082 | 0.1173 | 0.0091 |
| 1-2 | 0.0954 | 0.0940 | 0.0014 |
| 0-0 | 0.0854 | 0.1003 | 0.0149 |
| 1-0 | 0.0676 | 0.0706 | 0.0030 |
| 0-3 | 0.0541 | 0.0623 | 0.0083 |
| 1-3 | 0.0507 | 0.0506 | 0.0001 |
| 2-1 | 0.0451 | 0.0442 | 0.0009 |
| 2-2 | 0.0451 | 0.0392 | 0.0059 |
| 2-0 | 0.0290 | 0.0290 | 0.0000 |
| 2-3 | 0.0262 | 0.0205 | 0.0056 |
| 0-4 | 0.0262 | 0.0265 | 0.0003 |
| 1-4 | 0.0225 | 0.0206 | 0.0019 |
| 3-1 | 0.0133 | 0.0113 | 0.0020 |
| **Sum (top 15)** | **0.9245** | **0.9473** | — |
- High-score mass (total ≥9 goals): 1.38e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Brazil vs Japan
- CS outcomes: 28  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-0 | 0.1226 | 0.1249 | 0.0023 |
| 2-0 | 0.1063 | 0.1125 | 0.0062 |
| 1-1 | 0.1063 | 0.1147 | 0.0084 |
| 2-1 | 0.0938 | 0.0959 | 0.0021 |
| 0-0 | 0.0725 | 0.0858 | 0.0134 |
| 3-0 | 0.0613 | 0.0651 | 0.0038 |
| 0-1 | 0.0613 | 0.0654 | 0.0040 |
| 3-1 | 0.0531 | 0.0554 | 0.0022 |
| 1-2 | 0.0469 | 0.0481 | 0.0012 |
| 2-2 | 0.0443 | 0.0441 | 0.0002 |
| 4-0 | 0.0307 | 0.0289 | 0.0018 |
| 3-2 | 0.0285 | 0.0250 | 0.0035 |
| 0-2 | 0.0285 | 0.0296 | 0.0011 |
| 4-1 | 0.0257 | 0.0243 | 0.0014 |
| 1-3 | 0.0156 | 0.0139 | 0.0017 |
| **Sum (top 15)** | **0.8973** | **0.9334** | — |
- High-score mass (total ≥9 goals): 1.70e-05
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
