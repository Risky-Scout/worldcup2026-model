# Correct-Score Reconciliation Audit

**Generated**: 2026-06-27T04:18:42Z

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
- CS outcomes: 29  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 0-2 | 0.1305 | 0.1356 | 0.0051 |
| 0-3 | 0.1118 | 0.1226 | 0.0108 |
| 0-4 | 0.0824 | 0.0870 | 0.0046 |
| 0-1 | 0.0783 | 0.0931 | 0.0148 |
| 1-2 | 0.0712 | 0.0863 | 0.0151 |
| 1-3 | 0.0712 | 0.0806 | 0.0094 |
| 1-4 | 0.0522 | 0.0576 | 0.0054 |
| 1-1 | 0.0489 | 0.0583 | 0.0093 |
| 0-5 | 0.0489 | 0.0498 | 0.0008 |
| 0-0 | 0.0340 | 0.0348 | 0.0008 |
| 1-5 | 0.0301 | 0.0222 | 0.0079 |
| 0-6 | 0.0280 | 0.0222 | 0.0058 |
| 2-2 | 0.0253 | 0.0278 | 0.0026 |
| 1-0 | 0.0230 | 0.0227 | 0.0003 |
| 2-3 | 0.0230 | 0.0282 | 0.0051 |
| **Sum (top 15)** | **0.8589** | **0.9288** | — |
- High-score mass (total ≥9 goals): 2.97e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Croatia vs Ghana
- CS outcomes: 22  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-0 | 0.1537 | 0.1276 | 0.0262 |
| 1-1 | 0.1381 | 0.1507 | 0.0126 |
| 2-1 | 0.1018 | 0.0916 | 0.0103 |
| 2-0 | 0.0959 | 0.1050 | 0.0092 |
| 0-0 | 0.0959 | 0.1258 | 0.0299 |
| 0-1 | 0.0679 | 0.0641 | 0.0038 |
| 3-0 | 0.0479 | 0.0572 | 0.0092 |
| 2-2 | 0.0479 | 0.0446 | 0.0034 |
| 1-2 | 0.0479 | 0.0428 | 0.0051 |
| 3-1 | 0.0429 | 0.0453 | 0.0024 |
| 3-2 | 0.0263 | 0.0187 | 0.0076 |
| 0-2 | 0.0240 | 0.0260 | 0.0020 |
| 4-0 | 0.0199 | 0.0238 | 0.0039 |
| 4-1 | 0.0177 | 0.0182 | 0.0005 |
| 2-3 | 0.0134 | 0.0083 | 0.0050 |
| **Sum (top 15)** | **0.9412** | **0.9496** | — |
- High-score mass (total ≥9 goals): 1.28e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Colombia vs Portugal
- CS outcomes: 28  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-1 | 0.1051 | 0.1302 | 0.0251 |
| 0-1 | 0.0986 | 0.0992 | 0.0007 |
| 1-2 | 0.0928 | 0.0915 | 0.0013 |
| 0-2 | 0.0876 | 0.0880 | 0.0004 |
| 1-0 | 0.0657 | 0.0667 | 0.0010 |
| 2-1 | 0.0607 | 0.0597 | 0.0010 |
| 0-0 | 0.0607 | 0.0839 | 0.0232 |
| 1-3 | 0.0563 | 0.0526 | 0.0037 |
| 2-2 | 0.0493 | 0.0605 | 0.0113 |
| 0-3 | 0.0464 | 0.0486 | 0.0022 |
| 2-0 | 0.0394 | 0.0382 | 0.0012 |
| 2-3 | 0.0303 | 0.0283 | 0.0021 |
| 3-1 | 0.0254 | 0.0221 | 0.0034 |
| 0-4 | 0.0254 | 0.0210 | 0.0044 |
| 1-4 | 0.0254 | 0.0219 | 0.0035 |
| **Sum (top 15)** | **0.8691** | **0.9124** | — |
- High-score mass (total ≥9 goals): 2.00e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### DR Congo vs Uzbekistan
- CS outcomes: 28  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-0 | 0.1136 | 0.1233 | 0.0098 |
| 2-0 | 0.1060 | 0.1086 | 0.0026 |
| 1-1 | 0.0994 | 0.1076 | 0.0082 |
| 2-1 | 0.0883 | 0.0946 | 0.0063 |
| 0-0 | 0.0723 | 0.0771 | 0.0048 |
| 0-1 | 0.0662 | 0.0696 | 0.0033 |
| 3-0 | 0.0611 | 0.0626 | 0.0014 |
| 3-1 | 0.0568 | 0.0570 | 0.0002 |
| 1-2 | 0.0497 | 0.0520 | 0.0023 |
| 2-2 | 0.0397 | 0.0451 | 0.0053 |
| 0-2 | 0.0379 | 0.0337 | 0.0041 |
| 4-0 | 0.0306 | 0.0274 | 0.0032 |
| 4-1 | 0.0284 | 0.0249 | 0.0034 |
| 3-2 | 0.0256 | 0.0265 | 0.0008 |
| 1-3 | 0.0194 | 0.0167 | 0.0027 |
| **Sum (top 15)** | **0.8950** | **0.9267** | — |
- High-score mass (total ≥9 goals): 1.84e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Jordan vs Argentina
- CS outcomes: 26  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 0-2 | 0.1456 | 0.1440 | 0.0016 |
| 0-3 | 0.1335 | 0.1344 | 0.0009 |
| 0-1 | 0.1001 | 0.1016 | 0.0015 |
| 0-4 | 0.0942 | 0.0901 | 0.0042 |
| 1-2 | 0.0616 | 0.0821 | 0.0205 |
| 1-3 | 0.0616 | 0.0739 | 0.0123 |
| 1-1 | 0.0501 | 0.0567 | 0.0066 |
| 0-5 | 0.0501 | 0.0496 | 0.0004 |
| 0-0 | 0.0445 | 0.0358 | 0.0087 |
| 1-4 | 0.0421 | 0.0525 | 0.0104 |
| 0-6 | 0.0286 | 0.0222 | 0.0064 |
| 1-0 | 0.0258 | 0.0221 | 0.0037 |
| 1-5 | 0.0258 | 0.0222 | 0.0037 |
| 2-2 | 0.0195 | 0.0238 | 0.0043 |
| 2-1 | 0.0174 | 0.0193 | 0.0019 |
| **Sum (top 15)** | **0.9006** | **0.9302** | — |
- High-score mass (total ≥9 goals): 3.02e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Algeria vs Austria
- CS outcomes: 19  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 0-0 | 0.1792 | 0.2102 | 0.0309 |
| 0-1 | 0.1640 | 0.1339 | 0.0301 |
| 1-1 | 0.1606 | 0.1919 | 0.0314 |
| 1-0 | 0.1028 | 0.1013 | 0.0014 |
| 0-2 | 0.0734 | 0.0910 | 0.0176 |
| 1-2 | 0.0701 | 0.0600 | 0.0101 |
| 2-1 | 0.0482 | 0.0500 | 0.0019 |
| 2-2 | 0.0428 | 0.0273 | 0.0155 |
| 2-0 | 0.0335 | 0.0612 | 0.0277 |
| 0-3 | 0.0296 | 0.0240 | 0.0056 |
| 1-3 | 0.0249 | 0.0124 | 0.0125 |
| 3-1 | 0.0126 | 0.0082 | 0.0044 |
| 2-3 | 0.0126 | 0.0029 | 0.0097 |
| 3-0 | 0.0095 | 0.0125 | 0.0030 |
| 3-2 | 0.0095 | 0.0026 | 0.0069 |
| **Sum (top 15)** | **0.9734** | **0.9895** | — |
- High-score mass (total ≥9 goals): 2.22e-07
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### South Africa vs Canada
- CS outcomes: 24  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 0-1 | 0.1399 | 0.1402 | 0.0003 |
| 1-1 | 0.1159 | 0.1197 | 0.0038 |
| 0-2 | 0.1082 | 0.1169 | 0.0087 |
| 1-2 | 0.0954 | 0.0942 | 0.0013 |
| 0-0 | 0.0854 | 0.0991 | 0.0137 |
| 1-0 | 0.0676 | 0.0707 | 0.0031 |
| 0-3 | 0.0541 | 0.0622 | 0.0081 |
| 1-3 | 0.0507 | 0.0508 | 0.0001 |
| 2-1 | 0.0451 | 0.0446 | 0.0005 |
| 2-2 | 0.0451 | 0.0394 | 0.0057 |
| 2-0 | 0.0290 | 0.0292 | 0.0002 |
| 2-3 | 0.0262 | 0.0208 | 0.0054 |
| 0-4 | 0.0262 | 0.0265 | 0.0003 |
| 1-4 | 0.0225 | 0.0207 | 0.0018 |
| 3-1 | 0.0133 | 0.0116 | 0.0017 |
| **Sum (top 15)** | **0.9245** | **0.9465** | — |
- High-score mass (total ≥9 goals): 1.39e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Brazil vs Japan
- CS outcomes: 27  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-0 | 0.1231 | 0.1249 | 0.0018 |
| 2-0 | 0.1067 | 0.1125 | 0.0058 |
| 1-1 | 0.1067 | 0.1148 | 0.0081 |
| 2-1 | 0.0941 | 0.0959 | 0.0018 |
| 0-0 | 0.0727 | 0.0858 | 0.0131 |
| 3-0 | 0.0615 | 0.0650 | 0.0035 |
| 0-1 | 0.0615 | 0.0653 | 0.0038 |
| 3-1 | 0.0533 | 0.0554 | 0.0020 |
| 1-2 | 0.0471 | 0.0481 | 0.0011 |
| 2-2 | 0.0444 | 0.0441 | 0.0003 |
| 4-0 | 0.0308 | 0.0288 | 0.0019 |
| 3-2 | 0.0286 | 0.0249 | 0.0036 |
| 0-2 | 0.0286 | 0.0296 | 0.0010 |
| 4-1 | 0.0258 | 0.0242 | 0.0016 |
| 1-3 | 0.0157 | 0.0139 | 0.0017 |
| **Sum (top 15)** | **0.9005** | **0.9335** | — |
- High-score mass (total ≥9 goals): 1.70e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Netherlands vs Morocco
- CS outcomes: 26  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-1 | 0.1374 | 0.1357 | 0.0017 |
| 1-0 | 0.1226 | 0.1217 | 0.0009 |
| 2-1 | 0.0938 | 0.0902 | 0.0036 |
| 0-0 | 0.0839 | 0.0993 | 0.0154 |
| 0-1 | 0.0839 | 0.0877 | 0.0038 |
| 2-0 | 0.0724 | 0.0855 | 0.0131 |
| 1-2 | 0.0664 | 0.0641 | 0.0023 |
| 2-2 | 0.0569 | 0.0485 | 0.0084 |
| 3-1 | 0.0379 | 0.0407 | 0.0028 |
| 0-2 | 0.0379 | 0.0458 | 0.0078 |
| 3-0 | 0.0347 | 0.0405 | 0.0058 |
| 3-2 | 0.0257 | 0.0215 | 0.0042 |
| 1-3 | 0.0221 | 0.0212 | 0.0009 |
| 2-3 | 0.0194 | 0.0151 | 0.0044 |
| 0-3 | 0.0156 | 0.0154 | 0.0002 |
| **Sum (top 15)** | **0.9108** | **0.9330** | — |
- High-score mass (total ≥9 goals): 1.47e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### USA vs Bosnia & Herzegovina
- CS outcomes: 26  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-0 | 0.1331 | 0.1319 | 0.0012 |
| 2-0 | 0.1331 | 0.1363 | 0.0032 |
| 2-1 | 0.0940 | 0.0960 | 0.0021 |
| 1-1 | 0.0887 | 0.0927 | 0.0040 |
| 3-0 | 0.0841 | 0.0919 | 0.0079 |
| 0-0 | 0.0665 | 0.0720 | 0.0054 |
| 3-1 | 0.0614 | 0.0650 | 0.0036 |
| 4-0 | 0.0470 | 0.0490 | 0.0021 |
| 0-1 | 0.0420 | 0.0457 | 0.0036 |
| 2-2 | 0.0347 | 0.0339 | 0.0008 |
| 4-1 | 0.0307 | 0.0333 | 0.0026 |
| 1-2 | 0.0307 | 0.0321 | 0.0014 |
| 3-2 | 0.0258 | 0.0236 | 0.0021 |
| 5-0 | 0.0222 | 0.0204 | 0.0018 |
| 0-2 | 0.0157 | 0.0161 | 0.0005 |
| **Sum (top 15)** | **0.9097** | **0.9401** | — |
- High-score mass (total ≥9 goals): 1.89e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS
