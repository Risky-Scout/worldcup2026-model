# Correct-Score Reconciliation Audit

**Generated**: 2026-07-04T01:36:21Z

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
| Total 2026 matches predicted | 7 |
| Matches with any CS data | 7 |
| Matches with 1 CS vendor | 7 |
| Matches with 2+ CS vendors | 0 |

## Per-match correct-score audit

### Canada vs Morocco
- CS outcomes: 25  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-1 | 0.1338 | 0.1337 | 0.0001 |
| 0-1 | 0.1338 | 0.1278 | 0.0060 |
| 0-2 | 0.0945 | 0.1027 | 0.0082 |
| 1-2 | 0.0945 | 0.0929 | 0.0016 |
| 0-0 | 0.0845 | 0.1027 | 0.0181 |
| 1-0 | 0.0730 | 0.0754 | 0.0024 |
| 2-1 | 0.0535 | 0.0529 | 0.0007 |
| 2-2 | 0.0502 | 0.0446 | 0.0056 |
| 1-3 | 0.0472 | 0.0471 | 0.0001 |
| 0-3 | 0.0446 | 0.0522 | 0.0076 |
| 2-0 | 0.0309 | 0.0349 | 0.0040 |
| 2-3 | 0.0259 | 0.0213 | 0.0046 |
| 0-4 | 0.0196 | 0.0207 | 0.0011 |
| 1-4 | 0.0196 | 0.0180 | 0.0015 |
| 3-2 | 0.0175 | 0.0118 | 0.0056 |
| **Sum (top 15)** | **0.9231** | **0.9386** | — |
- High-score mass (total ≥9 goals): 1.46e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Paraguay vs France
- CS outcomes: 28  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 0-2 | 0.1399 | 0.1524 | 0.0125 |
| 0-1 | 0.1227 | 0.1298 | 0.0071 |
| 0-3 | 0.1139 | 0.1256 | 0.0117 |
| 1-2 | 0.0886 | 0.0871 | 0.0015 |
| 0-4 | 0.0725 | 0.0813 | 0.0087 |
| 1-3 | 0.0665 | 0.0702 | 0.0037 |
| 1-1 | 0.0614 | 0.0634 | 0.0021 |
| 0-0 | 0.0443 | 0.0509 | 0.0065 |
| 1-4 | 0.0399 | 0.0435 | 0.0036 |
| 0-5 | 0.0380 | 0.0421 | 0.0041 |
| 2-2 | 0.0257 | 0.0208 | 0.0049 |
| 2-3 | 0.0257 | 0.0194 | 0.0063 |
| 1-5 | 0.0235 | 0.0220 | 0.0015 |
| 1-0 | 0.0222 | 0.0263 | 0.0042 |
| 0-6 | 0.0195 | 0.0180 | 0.0015 |
| **Sum (top 15)** | **0.9042** | **0.9528** | — |
- High-score mass (total ≥9 goals): 2.24e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Brazil vs Norway
- CS outcomes: 28  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-1 | 0.1131 | 0.1162 | 0.0031 |
| 2-1 | 0.1056 | 0.1018 | 0.0038 |
| 1-0 | 0.0990 | 0.0941 | 0.0049 |
| 2-0 | 0.0754 | 0.0870 | 0.0116 |
| 2-2 | 0.0660 | 0.0594 | 0.0066 |
| 1-2 | 0.0609 | 0.0619 | 0.0009 |
| 3-1 | 0.0566 | 0.0592 | 0.0027 |
| 0-0 | 0.0528 | 0.0663 | 0.0135 |
| 0-1 | 0.0495 | 0.0572 | 0.0077 |
| 3-0 | 0.0466 | 0.0536 | 0.0070 |
| 3-2 | 0.0396 | 0.0347 | 0.0049 |
| 4-1 | 0.0255 | 0.0267 | 0.0012 |
| 0-2 | 0.0255 | 0.0340 | 0.0085 |
| 2-3 | 0.0255 | 0.0210 | 0.0045 |
| 4-0 | 0.0220 | 0.0246 | 0.0026 |
| **Sum (top 15)** | **0.8638** | **0.8978** | — |
- High-score mass (total ≥9 goals): 2.45e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Mexico vs England
- CS outcomes: 26  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-1 | 0.1326 | 0.1372 | 0.0046 |
| 0-1 | 0.1137 | 0.1193 | 0.0056 |
| 1-0 | 0.0995 | 0.1042 | 0.0048 |
| 0-0 | 0.0936 | 0.1110 | 0.0174 |
| 1-2 | 0.0796 | 0.0797 | 0.0001 |
| 2-1 | 0.0723 | 0.0696 | 0.0027 |
| 0-2 | 0.0723 | 0.0782 | 0.0058 |
| 2-0 | 0.0531 | 0.0583 | 0.0052 |
| 2-2 | 0.0468 | 0.0453 | 0.0016 |
| 1-3 | 0.0346 | 0.0331 | 0.0015 |
| 0-3 | 0.0306 | 0.0315 | 0.0009 |
| 3-1 | 0.0284 | 0.0247 | 0.0037 |
| 3-0 | 0.0221 | 0.0204 | 0.0017 |
| 2-3 | 0.0221 | 0.0177 | 0.0044 |
| 3-2 | 0.0194 | 0.0150 | 0.0044 |
| **Sum (top 15)** | **0.9208** | **0.9454** | — |
- High-score mass (total ≥9 goals): 1.26e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Portugal vs Spain
- CS outcomes: 27  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-1 | 0.1136 | 0.1188 | 0.0052 |
| 0-1 | 0.1060 | 0.1019 | 0.0041 |
| 1-2 | 0.0935 | 0.0966 | 0.0030 |
| 0-2 | 0.0837 | 0.0901 | 0.0064 |
| 0-0 | 0.0723 | 0.0789 | 0.0066 |
| 1-0 | 0.0663 | 0.0658 | 0.0005 |
| 2-1 | 0.0612 | 0.0617 | 0.0006 |
| 2-2 | 0.0568 | 0.0555 | 0.0013 |
| 1-3 | 0.0497 | 0.0543 | 0.0046 |
| 0-3 | 0.0468 | 0.0523 | 0.0055 |
| 2-0 | 0.0346 | 0.0369 | 0.0023 |
| 2-3 | 0.0306 | 0.0301 | 0.0005 |
| 1-4 | 0.0234 | 0.0235 | 0.0001 |
| 3-1 | 0.0221 | 0.0220 | 0.0001 |
| 3-2 | 0.0221 | 0.0187 | 0.0034 |
| **Sum (top 15)** | **0.8825** | **0.9069** | — |
- High-score mass (total ≥9 goals): 2.12e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### USA vs Belgium
- CS outcomes: 32  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-1 | 0.1305 | 0.1299 | 0.0006 |
| 1-2 | 0.0870 | 0.0872 | 0.0001 |
| 2-1 | 0.0783 | 0.0824 | 0.0041 |
| 2-2 | 0.0746 | 0.0676 | 0.0070 |
| 0-1 | 0.0746 | 0.0726 | 0.0020 |
| 1-0 | 0.0712 | 0.0705 | 0.0007 |
| 0-0 | 0.0522 | 0.0705 | 0.0183 |
| 0-2 | 0.0522 | 0.0603 | 0.0081 |
| 2-0 | 0.0435 | 0.0548 | 0.0113 |
| 1-3 | 0.0392 | 0.0423 | 0.0032 |
| 3-1 | 0.0341 | 0.0389 | 0.0048 |
| 3-2 | 0.0341 | 0.0304 | 0.0037 |
| 2-3 | 0.0341 | 0.0311 | 0.0029 |
| 0-3 | 0.0253 | 0.0304 | 0.0051 |
| 3-0 | 0.0230 | 0.0273 | 0.0042 |
| **Sum (top 15)** | **0.8538** | **0.8960** | — |
- High-score mass (total ≥9 goals): 2.58e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Argentina vs Egypt
- CS outcomes: 24  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-0 | 0.1529 | 0.1524 | 0.0006 |
| 2-0 | 0.1422 | 0.1462 | 0.0040 |
| 2-1 | 0.0954 | 0.0929 | 0.0025 |
| 3-0 | 0.0954 | 0.0973 | 0.0019 |
| 1-1 | 0.0853 | 0.0886 | 0.0033 |
| 0-0 | 0.0737 | 0.0776 | 0.0039 |
| 3-1 | 0.0579 | 0.0601 | 0.0022 |
| 4-0 | 0.0507 | 0.0498 | 0.0009 |
| 0-1 | 0.0352 | 0.0463 | 0.0110 |
| 4-1 | 0.0312 | 0.0304 | 0.0008 |
| 2-2 | 0.0312 | 0.0281 | 0.0031 |
| 3-2 | 0.0238 | 0.0195 | 0.0044 |
| 5-0 | 0.0238 | 0.0201 | 0.0038 |
| 1-2 | 0.0238 | 0.0277 | 0.0039 |
| 5-1 | 0.0133 | 0.0119 | 0.0014 |
| **Sum (top 15)** | **0.9358** | **0.9488** | — |
- High-score mass (total ≥9 goals): 1.67e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS
