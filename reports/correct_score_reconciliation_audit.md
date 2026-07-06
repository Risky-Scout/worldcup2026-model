# Correct-Score Reconciliation Audit

**Generated**: 2026-07-06T00:03:54Z

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
| Total 2026 matches predicted | 6 |
| Matches with any CS data | 6 |
| Matches with 1 CS vendor | 6 |
| Matches with 2+ CS vendors | 0 |

## Per-match correct-score audit

### Mexico vs England
- CS outcomes: 26  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-1 | 0.1321 | 0.1410 | 0.0088 |
| 0-1 | 0.1220 | 0.1172 | 0.0048 |
| 1-0 | 0.1057 | 0.1043 | 0.0014 |
| 0-0 | 0.0991 | 0.1185 | 0.0194 |
| 1-2 | 0.0755 | 0.0769 | 0.0014 |
| 2-1 | 0.0721 | 0.0705 | 0.0016 |
| 0-2 | 0.0721 | 0.0746 | 0.0025 |
| 2-0 | 0.0528 | 0.0585 | 0.0056 |
| 2-2 | 0.0466 | 0.0468 | 0.0001 |
| 1-3 | 0.0305 | 0.0309 | 0.0004 |
| 0-3 | 0.0283 | 0.0295 | 0.0012 |
| 3-1 | 0.0256 | 0.0249 | 0.0007 |
| 3-0 | 0.0220 | 0.0213 | 0.0008 |
| 2-3 | 0.0220 | 0.0171 | 0.0049 |
| 3-2 | 0.0193 | 0.0151 | 0.0042 |
| **Sum (top 15)** | **0.9257** | **0.9470** | — |
- High-score mass (total ≥9 goals): 1.24e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Portugal vs Spain
- CS outcomes: 29  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-1 | 0.1118 | 0.1191 | 0.0073 |
| 0-1 | 0.0979 | 0.0926 | 0.0053 |
| 1-2 | 0.0979 | 0.0983 | 0.0004 |
| 0-2 | 0.0746 | 0.0845 | 0.0100 |
| 2-2 | 0.0652 | 0.0608 | 0.0045 |
| 1-0 | 0.0602 | 0.0615 | 0.0013 |
| 2-1 | 0.0602 | 0.0632 | 0.0030 |
| 0-0 | 0.0559 | 0.0713 | 0.0154 |
| 1-3 | 0.0522 | 0.0560 | 0.0038 |
| 0-3 | 0.0460 | 0.0509 | 0.0049 |
| 2-0 | 0.0340 | 0.0376 | 0.0035 |
| 2-3 | 0.0340 | 0.0328 | 0.0012 |
| 3-1 | 0.0253 | 0.0244 | 0.0009 |
| 3-2 | 0.0253 | 0.0213 | 0.0040 |
| 1-4 | 0.0253 | 0.0248 | 0.0004 |
| **Sum (top 15)** | **0.8658** | **0.8991** | — |
- High-score mass (total ≥9 goals): 2.36e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### USA vs Belgium
- CS outcomes: 31  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-1 | 0.1200 | 0.1249 | 0.0049 |
| 2-1 | 0.0821 | 0.0854 | 0.0033 |
| 1-2 | 0.0821 | 0.0845 | 0.0024 |
| 1-0 | 0.0709 | 0.0672 | 0.0038 |
| 2-2 | 0.0709 | 0.0695 | 0.0014 |
| 0-1 | 0.0709 | 0.0665 | 0.0044 |
| 0-0 | 0.0487 | 0.0672 | 0.0184 |
| 2-0 | 0.0459 | 0.0560 | 0.0101 |
| 0-2 | 0.0459 | 0.0550 | 0.0092 |
| 3-1 | 0.0390 | 0.0429 | 0.0039 |
| 1-3 | 0.0390 | 0.0422 | 0.0032 |
| 3-2 | 0.0371 | 0.0335 | 0.0037 |
| 2-3 | 0.0371 | 0.0331 | 0.0040 |
| 3-0 | 0.0252 | 0.0296 | 0.0045 |
| 0-3 | 0.0252 | 0.0289 | 0.0037 |
| **Sum (top 15)** | **0.8400** | **0.8864** | — |
- High-score mass (total ≥9 goals): 2.85e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Argentina vs Egypt
- CS outcomes: 26  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-0 | 0.1376 | 0.1479 | 0.0103 |
| 2-0 | 0.1376 | 0.1471 | 0.0096 |
| 2-1 | 0.0939 | 0.0933 | 0.0006 |
| 3-0 | 0.0887 | 0.0949 | 0.0062 |
| 1-1 | 0.0887 | 0.0923 | 0.0036 |
| 0-0 | 0.0665 | 0.0777 | 0.0112 |
| 3-1 | 0.0614 | 0.0614 | 0.0000 |
| 4-0 | 0.0443 | 0.0479 | 0.0036 |
| 0-1 | 0.0399 | 0.0480 | 0.0081 |
| 2-2 | 0.0347 | 0.0286 | 0.0061 |
| 4-1 | 0.0307 | 0.0302 | 0.0005 |
| 1-2 | 0.0285 | 0.0280 | 0.0005 |
| 3-2 | 0.0235 | 0.0196 | 0.0038 |
| 5-0 | 0.0235 | 0.0198 | 0.0037 |
| 5-1 | 0.0142 | 0.0119 | 0.0024 |
| **Sum (top 15)** | **0.9135** | **0.9485** | — |
- High-score mass (total ≥9 goals): 1.65e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Switzerland vs Colombia
- CS outcomes: 25  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-1 | 0.1358 | 0.1407 | 0.0048 |
| 0-1 | 0.1233 | 0.1208 | 0.0025 |
| 1-0 | 0.0943 | 0.0932 | 0.0011 |
| 0-0 | 0.0943 | 0.1135 | 0.0192 |
| 1-2 | 0.0844 | 0.0844 | 0.0001 |
| 0-2 | 0.0763 | 0.0844 | 0.0080 |
| 2-1 | 0.0668 | 0.0641 | 0.0027 |
| 2-2 | 0.0501 | 0.0469 | 0.0032 |
| 2-0 | 0.0445 | 0.0488 | 0.0043 |
| 0-3 | 0.0348 | 0.0376 | 0.0028 |
| 1-3 | 0.0348 | 0.0368 | 0.0019 |
| 2-3 | 0.0236 | 0.0190 | 0.0045 |
| 3-1 | 0.0223 | 0.0209 | 0.0014 |
| 3-2 | 0.0195 | 0.0140 | 0.0055 |
| 3-0 | 0.0174 | 0.0161 | 0.0013 |
| **Sum (top 15)** | **0.9224** | **0.9413** | — |
- High-score mass (total ≥9 goals): 1.28e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### France vs Morocco
- CS outcomes: 26  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-0 | 0.1339 | 0.1248 | 0.0091 |
| 2-0 | 0.1071 | 0.1178 | 0.0107 |
| 1-1 | 0.1071 | 0.1119 | 0.0048 |
| 2-1 | 0.1004 | 0.0992 | 0.0012 |
| 0-0 | 0.0669 | 0.0819 | 0.0149 |
| 3-0 | 0.0618 | 0.0731 | 0.0113 |
| 3-1 | 0.0574 | 0.0603 | 0.0029 |
| 2-2 | 0.0502 | 0.0430 | 0.0072 |
| 0-1 | 0.0472 | 0.0536 | 0.0064 |
| 1-2 | 0.0423 | 0.0420 | 0.0003 |
| 4-0 | 0.0349 | 0.0363 | 0.0014 |
| 3-2 | 0.0309 | 0.0255 | 0.0054 |
| 4-1 | 0.0287 | 0.0285 | 0.0001 |
| 0-2 | 0.0223 | 0.0231 | 0.0008 |
| 2-3 | 0.0157 | 0.0104 | 0.0054 |
| **Sum (top 15)** | **0.9068** | **0.9313** | — |
- High-score mass (total ≥9 goals): 1.78e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS
