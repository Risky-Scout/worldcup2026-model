# Correct-Score Reconciliation Audit

**Generated**: 2026-07-04T00:31:47Z

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

### Colombia vs Ghana
- CS outcomes: 25  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-0 | 0.1444 | 0.1383 | 0.0062 |
| 2-0 | 0.1348 | 0.1383 | 0.0036 |
| 2-1 | 0.0951 | 0.0949 | 0.0002 |
| 1-1 | 0.0951 | 0.0996 | 0.0045 |
| 3-0 | 0.0851 | 0.0904 | 0.0052 |
| 0-0 | 0.0735 | 0.0833 | 0.0098 |
| 3-1 | 0.0578 | 0.0605 | 0.0027 |
| 0-1 | 0.0449 | 0.0489 | 0.0039 |
| 4-0 | 0.0404 | 0.0444 | 0.0040 |
| 2-2 | 0.0352 | 0.0328 | 0.0024 |
| 1-2 | 0.0311 | 0.0319 | 0.0008 |
| 4-1 | 0.0289 | 0.0296 | 0.0007 |
| 3-2 | 0.0225 | 0.0207 | 0.0018 |
| 5-0 | 0.0197 | 0.0178 | 0.0019 |
| 0-2 | 0.0159 | 0.0167 | 0.0009 |
| **Sum (top 15)** | **0.9245** | **0.9481** | — |
- High-score mass (total ≥9 goals): 1.67e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Canada vs Morocco
- CS outcomes: 25  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-1 | 0.1337 | 0.1330 | 0.0007 |
| 0-1 | 0.1337 | 0.1285 | 0.0052 |
| 0-2 | 0.0944 | 0.1039 | 0.0095 |
| 1-2 | 0.0944 | 0.0933 | 0.0011 |
| 0-0 | 0.0844 | 0.1022 | 0.0178 |
| 1-0 | 0.0729 | 0.0746 | 0.0017 |
| 2-1 | 0.0535 | 0.0520 | 0.0015 |
| 2-2 | 0.0501 | 0.0441 | 0.0060 |
| 0-3 | 0.0472 | 0.0540 | 0.0068 |
| 1-3 | 0.0446 | 0.0470 | 0.0025 |
| 2-0 | 0.0309 | 0.0341 | 0.0032 |
| 2-3 | 0.0259 | 0.0214 | 0.0045 |
| 0-4 | 0.0196 | 0.0214 | 0.0018 |
| 1-4 | 0.0196 | 0.0184 | 0.0011 |
| 3-1 | 0.0157 | 0.0147 | 0.0011 |
| **Sum (top 15)** | **0.9204** | **0.9425** | — |
- High-score mass (total ≥9 goals): 1.45e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Paraguay vs France
- CS outcomes: 26  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 0-2 | 0.1491 | 0.1550 | 0.0059 |
| 0-3 | 0.1239 | 0.1292 | 0.0053 |
| 0-1 | 0.1151 | 0.1234 | 0.0084 |
| 1-2 | 0.0767 | 0.0829 | 0.0062 |
| 0-4 | 0.0767 | 0.0818 | 0.0051 |
| 1-3 | 0.0671 | 0.0701 | 0.0030 |
| 1-1 | 0.0620 | 0.0649 | 0.0029 |
| 0-0 | 0.0474 | 0.0528 | 0.0054 |
| 1-4 | 0.0424 | 0.0438 | 0.0014 |
| 0-5 | 0.0424 | 0.0423 | 0.0001 |
| 1-0 | 0.0260 | 0.0270 | 0.0010 |
| 2-2 | 0.0224 | 0.0210 | 0.0013 |
| 1-5 | 0.0224 | 0.0217 | 0.0007 |
| 2-3 | 0.0196 | 0.0188 | 0.0009 |
| 0-6 | 0.0196 | 0.0175 | 0.0022 |
| **Sum (top 15)** | **0.9127** | **0.9520** | — |
- High-score mass (total ≥9 goals): 2.24e-05
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
| 1-1 | 0.1305 | 0.1301 | 0.0004 |
| 1-2 | 0.0870 | 0.0875 | 0.0004 |
| 2-1 | 0.0783 | 0.0822 | 0.0038 |
| 2-2 | 0.0746 | 0.0676 | 0.0070 |
| 0-1 | 0.0746 | 0.0726 | 0.0020 |
| 1-0 | 0.0712 | 0.0701 | 0.0011 |
| 0-0 | 0.0522 | 0.0707 | 0.0184 |
| 0-2 | 0.0522 | 0.0606 | 0.0084 |
| 2-0 | 0.0435 | 0.0544 | 0.0109 |
| 1-3 | 0.0392 | 0.0425 | 0.0034 |
| 3-1 | 0.0341 | 0.0386 | 0.0046 |
| 3-2 | 0.0341 | 0.0302 | 0.0038 |
| 2-3 | 0.0341 | 0.0312 | 0.0028 |
| 0-3 | 0.0253 | 0.0306 | 0.0054 |
| 3-0 | 0.0230 | 0.0270 | 0.0039 |
| **Sum (top 15)** | **0.8538** | **0.8960** | — |
- High-score mass (total ≥9 goals): 2.58e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS
