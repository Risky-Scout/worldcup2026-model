# Correct-Score Reconciliation Audit

**Generated**: 2026-07-06T11:57:23Z

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

### Portugal vs Spain
- CS outcomes: 28  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-1 | 0.1123 | 0.1193 | 0.0070 |
| 0-1 | 0.0982 | 0.0936 | 0.0046 |
| 1-2 | 0.0982 | 0.0988 | 0.0006 |
| 0-2 | 0.0749 | 0.0860 | 0.0111 |
| 2-2 | 0.0655 | 0.0602 | 0.0053 |
| 1-0 | 0.0605 | 0.0613 | 0.0008 |
| 2-1 | 0.0605 | 0.0622 | 0.0017 |
| 0-0 | 0.0561 | 0.0717 | 0.0156 |
| 1-3 | 0.0524 | 0.0564 | 0.0040 |
| 0-3 | 0.0437 | 0.0514 | 0.0077 |
| 2-3 | 0.0374 | 0.0333 | 0.0041 |
| 2-0 | 0.0342 | 0.0368 | 0.0027 |
| 3-1 | 0.0254 | 0.0235 | 0.0018 |
| 3-2 | 0.0254 | 0.0207 | 0.0047 |
| 1-4 | 0.0231 | 0.0249 | 0.0017 |
| **Sum (top 15)** | **0.8676** | **0.9000** | — |
- High-score mass (total ≥9 goals): 2.33e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### USA vs Belgium
- CS outcomes: 32  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-1 | 0.1202 | 0.1249 | 0.0048 |
| 2-1 | 0.0868 | 0.0882 | 0.0014 |
| 1-2 | 0.0822 | 0.0831 | 0.0009 |
| 1-0 | 0.0710 | 0.0687 | 0.0023 |
| 2-2 | 0.0710 | 0.0692 | 0.0018 |
| 0-1 | 0.0651 | 0.0645 | 0.0005 |
| 2-0 | 0.0521 | 0.0601 | 0.0080 |
| 0-0 | 0.0459 | 0.0661 | 0.0202 |
| 0-2 | 0.0459 | 0.0532 | 0.0072 |
| 3-1 | 0.0411 | 0.0449 | 0.0038 |
| 3-2 | 0.0372 | 0.0340 | 0.0032 |
| 1-3 | 0.0372 | 0.0398 | 0.0027 |
| 2-3 | 0.0340 | 0.0316 | 0.0024 |
| 3-0 | 0.0279 | 0.0321 | 0.0042 |
| 3-3 | 0.0252 | 0.0176 | 0.0075 |
| **Sum (top 15)** | **0.8427** | **0.8780** | — |
- High-score mass (total ≥9 goals): 2.82e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Argentina vs Egypt
- CS outcomes: 25  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-0 | 0.1442 | 0.1499 | 0.0056 |
| 2-0 | 0.1417 | 0.1477 | 0.0060 |
| 2-1 | 0.0898 | 0.0916 | 0.0018 |
| 3-0 | 0.0898 | 0.0956 | 0.0059 |
| 1-1 | 0.0850 | 0.0898 | 0.0048 |
| 0-0 | 0.0734 | 0.0793 | 0.0059 |
| 3-1 | 0.0621 | 0.0616 | 0.0005 |
| 4-0 | 0.0475 | 0.0490 | 0.0015 |
| 0-1 | 0.0404 | 0.0474 | 0.0070 |
| 2-2 | 0.0311 | 0.0281 | 0.0030 |
| 4-1 | 0.0288 | 0.0300 | 0.0011 |
| 1-2 | 0.0288 | 0.0280 | 0.0008 |
| 3-2 | 0.0224 | 0.0194 | 0.0030 |
| 5-0 | 0.0224 | 0.0198 | 0.0026 |
| 0-2 | 0.0144 | 0.0150 | 0.0006 |
| **Sum (top 15)** | **0.9220** | **0.9520** | — |
- High-score mass (total ≥9 goals): 1.65e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Switzerland vs Colombia
- CS outcomes: 25  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-1 | 0.1360 | 0.1419 | 0.0059 |
| 0-1 | 0.1234 | 0.1193 | 0.0041 |
| 1-0 | 0.0944 | 0.0948 | 0.0004 |
| 0-0 | 0.0944 | 0.1148 | 0.0204 |
| 1-2 | 0.0891 | 0.0847 | 0.0045 |
| 0-2 | 0.0729 | 0.0813 | 0.0084 |
| 2-1 | 0.0669 | 0.0652 | 0.0016 |
| 2-2 | 0.0535 | 0.0478 | 0.0057 |
| 2-0 | 0.0446 | 0.0508 | 0.0062 |
| 0-3 | 0.0349 | 0.0358 | 0.0009 |
| 1-3 | 0.0349 | 0.0354 | 0.0005 |
| 2-3 | 0.0236 | 0.0185 | 0.0051 |
| 3-1 | 0.0223 | 0.0216 | 0.0006 |
| 3-0 | 0.0174 | 0.0170 | 0.0004 |
| 3-2 | 0.0174 | 0.0142 | 0.0033 |
| **Sum (top 15)** | **0.9258** | **0.9431** | — |
- High-score mass (total ≥9 goals): 1.27e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### France vs Morocco
- CS outcomes: 26  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-0 | 0.1231 | 0.1216 | 0.0015 |
| 2-0 | 0.1143 | 0.1212 | 0.0069 |
| 1-1 | 0.1067 | 0.1107 | 0.0040 |
| 2-1 | 0.1000 | 0.0992 | 0.0008 |
| 0-0 | 0.0727 | 0.0833 | 0.0106 |
| 3-0 | 0.0667 | 0.0750 | 0.0083 |
| 3-1 | 0.0571 | 0.0603 | 0.0031 |
| 0-1 | 0.0533 | 0.0554 | 0.0021 |
| 2-2 | 0.0444 | 0.0412 | 0.0033 |
| 1-2 | 0.0400 | 0.0411 | 0.0011 |
| 4-0 | 0.0348 | 0.0364 | 0.0016 |
| 3-2 | 0.0286 | 0.0250 | 0.0035 |
| 4-1 | 0.0286 | 0.0285 | 0.0001 |
| 0-2 | 0.0222 | 0.0229 | 0.0007 |
| 5-0 | 0.0157 | 0.0137 | 0.0020 |
| **Sum (top 15)** | **0.9082** | **0.9354** | — |
- High-score mass (total ≥9 goals): 1.77e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Norway vs England
- CS outcomes: 27  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-1 | 0.1214 | 0.1198 | 0.0015 |
| 0-1 | 0.1052 | 0.1002 | 0.0050 |
| 1-2 | 0.0877 | 0.0958 | 0.0081 |
| 0-2 | 0.0751 | 0.0854 | 0.0102 |
| 1-0 | 0.0717 | 0.0655 | 0.0062 |
| 0-0 | 0.0717 | 0.0752 | 0.0035 |
| 2-1 | 0.0657 | 0.0637 | 0.0021 |
| 2-2 | 0.0526 | 0.0554 | 0.0028 |
| 1-3 | 0.0464 | 0.0546 | 0.0082 |
| 2-0 | 0.0438 | 0.0383 | 0.0056 |
| 0-3 | 0.0415 | 0.0509 | 0.0094 |
| 3-1 | 0.0282 | 0.0237 | 0.0044 |
| 2-3 | 0.0282 | 0.0312 | 0.0030 |
| 3-2 | 0.0219 | 0.0195 | 0.0025 |
| 1-4 | 0.0219 | 0.0240 | 0.0021 |
| **Sum (top 15)** | **0.8831** | **0.9032** | — |
- High-score mass (total ≥9 goals): 2.22e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS
