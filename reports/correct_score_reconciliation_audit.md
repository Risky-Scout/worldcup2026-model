# Correct-Score Reconciliation Audit

**Generated**: 2026-07-04T02:48:12Z

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
| 1-1 | 0.1347 | 0.1338 | 0.0009 |
| 0-1 | 0.1347 | 0.1283 | 0.0064 |
| 1-2 | 0.1010 | 0.0949 | 0.0061 |
| 0-2 | 0.0898 | 0.1010 | 0.0112 |
| 0-0 | 0.0851 | 0.1023 | 0.0172 |
| 1-0 | 0.0673 | 0.0743 | 0.0070 |
| 2-1 | 0.0539 | 0.0533 | 0.0006 |
| 2-2 | 0.0505 | 0.0443 | 0.0062 |
| 1-3 | 0.0475 | 0.0470 | 0.0005 |
| 0-3 | 0.0449 | 0.0519 | 0.0070 |
| 2-0 | 0.0289 | 0.0351 | 0.0062 |
| 2-3 | 0.0289 | 0.0216 | 0.0072 |
| 0-4 | 0.0197 | 0.0206 | 0.0008 |
| 1-4 | 0.0197 | 0.0180 | 0.0017 |
| 3-1 | 0.0158 | 0.0153 | 0.0005 |
| **Sum (top 15)** | **0.9224** | **0.9416** | — |
- High-score mass (total ≥9 goals): 1.48e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Paraguay vs France
- CS outcomes: 28  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 0-2 | 0.1399 | 0.1517 | 0.0117 |
| 0-1 | 0.1227 | 0.1290 | 0.0063 |
| 0-3 | 0.1139 | 0.1263 | 0.0124 |
| 1-2 | 0.0886 | 0.0872 | 0.0014 |
| 0-4 | 0.0725 | 0.0824 | 0.0099 |
| 1-3 | 0.0665 | 0.0708 | 0.0043 |
| 1-1 | 0.0614 | 0.0622 | 0.0008 |
| 0-0 | 0.0443 | 0.0491 | 0.0048 |
| 1-4 | 0.0399 | 0.0443 | 0.0044 |
| 0-5 | 0.0380 | 0.0431 | 0.0051 |
| 2-2 | 0.0257 | 0.0207 | 0.0050 |
| 2-3 | 0.0257 | 0.0197 | 0.0061 |
| 1-5 | 0.0235 | 0.0220 | 0.0015 |
| 1-0 | 0.0222 | 0.0257 | 0.0035 |
| 0-6 | 0.0195 | 0.0187 | 0.0007 |
| **Sum (top 15)** | **0.9042** | **0.9528** | — |
- High-score mass (total ≥9 goals): 2.29e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Brazil vs Norway
- CS outcomes: 28  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-1 | 0.1131 | 0.1176 | 0.0045 |
| 2-1 | 0.1056 | 0.1020 | 0.0036 |
| 1-0 | 0.0990 | 0.0923 | 0.0067 |
| 2-0 | 0.0754 | 0.0876 | 0.0122 |
| 2-2 | 0.0660 | 0.0596 | 0.0064 |
| 1-2 | 0.0609 | 0.0611 | 0.0002 |
| 3-1 | 0.0566 | 0.0596 | 0.0030 |
| 0-0 | 0.0528 | 0.0682 | 0.0154 |
| 0-1 | 0.0495 | 0.0558 | 0.0063 |
| 3-0 | 0.0466 | 0.0543 | 0.0077 |
| 3-2 | 0.0396 | 0.0346 | 0.0050 |
| 4-1 | 0.0255 | 0.0271 | 0.0015 |
| 0-2 | 0.0255 | 0.0333 | 0.0077 |
| 2-3 | 0.0255 | 0.0206 | 0.0050 |
| 4-0 | 0.0220 | 0.0251 | 0.0031 |
| **Sum (top 15)** | **0.8638** | **0.8989** | — |
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
| 0-0 | 0.0936 | 0.1111 | 0.0175 |
| 1-2 | 0.0796 | 0.0797 | 0.0002 |
| 2-1 | 0.0723 | 0.0696 | 0.0028 |
| 0-2 | 0.0723 | 0.0782 | 0.0058 |
| 2-0 | 0.0531 | 0.0583 | 0.0053 |
| 2-2 | 0.0468 | 0.0453 | 0.0015 |
| 1-3 | 0.0346 | 0.0331 | 0.0015 |
| 0-3 | 0.0306 | 0.0315 | 0.0009 |
| 3-1 | 0.0284 | 0.0247 | 0.0037 |
| 3-0 | 0.0221 | 0.0204 | 0.0017 |
| 2-3 | 0.0221 | 0.0178 | 0.0043 |
| 3-2 | 0.0194 | 0.0151 | 0.0043 |
| **Sum (top 15)** | **0.9208** | **0.9455** | — |
- High-score mass (total ≥9 goals): 1.26e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Portugal vs Spain
- CS outcomes: 27  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-1 | 0.1136 | 0.1183 | 0.0047 |
| 0-1 | 0.1060 | 0.1025 | 0.0036 |
| 1-2 | 0.0935 | 0.0965 | 0.0030 |
| 0-2 | 0.0837 | 0.0901 | 0.0064 |
| 0-0 | 0.0723 | 0.0782 | 0.0059 |
| 1-0 | 0.0663 | 0.0662 | 0.0001 |
| 2-1 | 0.0612 | 0.0619 | 0.0007 |
| 2-2 | 0.0568 | 0.0554 | 0.0014 |
| 1-3 | 0.0497 | 0.0543 | 0.0046 |
| 0-3 | 0.0468 | 0.0522 | 0.0054 |
| 2-0 | 0.0346 | 0.0370 | 0.0025 |
| 2-3 | 0.0306 | 0.0301 | 0.0005 |
| 1-4 | 0.0234 | 0.0235 | 0.0001 |
| 3-1 | 0.0221 | 0.0221 | 0.0000 |
| 3-2 | 0.0221 | 0.0188 | 0.0033 |
| **Sum (top 15)** | **0.8825** | **0.9069** | — |
- High-score mass (total ≥9 goals): 2.12e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### USA vs Belgium
- CS outcomes: 32  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-1 | 0.1305 | 0.1302 | 0.0003 |
| 1-2 | 0.0870 | 0.0870 | 0.0001 |
| 2-1 | 0.0783 | 0.0826 | 0.0042 |
| 2-2 | 0.0746 | 0.0677 | 0.0069 |
| 0-1 | 0.0746 | 0.0722 | 0.0024 |
| 1-0 | 0.0712 | 0.0704 | 0.0008 |
| 0-0 | 0.0522 | 0.0709 | 0.0187 |
| 0-2 | 0.0522 | 0.0600 | 0.0078 |
| 2-0 | 0.0435 | 0.0550 | 0.0115 |
| 1-3 | 0.0392 | 0.0421 | 0.0029 |
| 3-1 | 0.0341 | 0.0390 | 0.0050 |
| 3-2 | 0.0341 | 0.0304 | 0.0036 |
| 2-3 | 0.0341 | 0.0310 | 0.0030 |
| 0-3 | 0.0253 | 0.0302 | 0.0049 |
| 3-0 | 0.0230 | 0.0274 | 0.0044 |
| **Sum (top 15)** | **0.8538** | **0.8960** | — |
- High-score mass (total ≥9 goals): 2.57e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Argentina vs Egypt
- CS outcomes: 24  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-0 | 0.1529 | 0.1530 | 0.0001 |
| 2-0 | 0.1422 | 0.1466 | 0.0044 |
| 2-1 | 0.0954 | 0.0927 | 0.0026 |
| 3-0 | 0.0954 | 0.0972 | 0.0018 |
| 1-1 | 0.0853 | 0.0888 | 0.0035 |
| 0-0 | 0.0737 | 0.0781 | 0.0044 |
| 3-1 | 0.0579 | 0.0599 | 0.0020 |
| 4-0 | 0.0507 | 0.0497 | 0.0010 |
| 0-1 | 0.0352 | 0.0465 | 0.0112 |
| 4-1 | 0.0312 | 0.0302 | 0.0010 |
| 2-2 | 0.0312 | 0.0279 | 0.0033 |
| 3-2 | 0.0238 | 0.0194 | 0.0045 |
| 5-0 | 0.0238 | 0.0199 | 0.0039 |
| 1-2 | 0.0238 | 0.0277 | 0.0039 |
| 5-1 | 0.0133 | 0.0118 | 0.0015 |
| **Sum (top 15)** | **0.9358** | **0.9492** | — |
- High-score mass (total ≥9 goals): 1.66e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS
