# Correct-Score Reconciliation Audit

**Generated**: 2026-07-06T16:54:43Z

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
- CS outcomes: 31  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-1 | 0.1200 | 0.1246 | 0.0046 |
| 2-1 | 0.0866 | 0.0881 | 0.0014 |
| 1-2 | 0.0780 | 0.0819 | 0.0039 |
| 2-2 | 0.0743 | 0.0696 | 0.0046 |
| 1-0 | 0.0709 | 0.0688 | 0.0020 |
| 0-1 | 0.0650 | 0.0650 | 0.0001 |
| 2-0 | 0.0520 | 0.0602 | 0.0083 |
| 0-0 | 0.0487 | 0.0670 | 0.0183 |
| 0-2 | 0.0433 | 0.0529 | 0.0096 |
| 3-1 | 0.0410 | 0.0448 | 0.0038 |
| 3-2 | 0.0371 | 0.0338 | 0.0033 |
| 1-3 | 0.0371 | 0.0399 | 0.0028 |
| 2-3 | 0.0339 | 0.0317 | 0.0022 |
| 3-0 | 0.0278 | 0.0320 | 0.0042 |
| 3-3 | 0.0252 | 0.0174 | 0.0078 |
| **Sum (top 15)** | **0.8409** | **0.8778** | — |
- High-score mass (total ≥9 goals): 2.80e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Argentina vs Egypt
- CS outcomes: 25  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-0 | 0.1442 | 0.1493 | 0.0050 |
| 2-0 | 0.1417 | 0.1478 | 0.0061 |
| 2-1 | 0.0898 | 0.0915 | 0.0018 |
| 3-0 | 0.0898 | 0.0959 | 0.0062 |
| 1-1 | 0.0850 | 0.0901 | 0.0051 |
| 0-0 | 0.0734 | 0.0799 | 0.0065 |
| 3-1 | 0.0621 | 0.0616 | 0.0005 |
| 4-0 | 0.0475 | 0.0492 | 0.0017 |
| 0-1 | 0.0404 | 0.0471 | 0.0067 |
| 2-2 | 0.0311 | 0.0280 | 0.0031 |
| 4-1 | 0.0288 | 0.0300 | 0.0011 |
| 1-2 | 0.0288 | 0.0278 | 0.0010 |
| 3-2 | 0.0224 | 0.0193 | 0.0031 |
| 5-0 | 0.0224 | 0.0199 | 0.0025 |
| 0-2 | 0.0144 | 0.0148 | 0.0004 |
| **Sum (top 15)** | **0.9220** | **0.9523** | — |
- High-score mass (total ≥9 goals): 1.65e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Switzerland vs Colombia
- CS outcomes: 26  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-1 | 0.1413 | 0.1433 | 0.0020 |
| 0-1 | 0.1239 | 0.1202 | 0.0037 |
| 0-0 | 0.0947 | 0.1140 | 0.0193 |
| 1-0 | 0.0895 | 0.0935 | 0.0040 |
| 1-2 | 0.0895 | 0.0849 | 0.0046 |
| 0-2 | 0.0732 | 0.0822 | 0.0090 |
| 2-1 | 0.0671 | 0.0654 | 0.0017 |
| 2-2 | 0.0575 | 0.0479 | 0.0096 |
| 2-0 | 0.0383 | 0.0494 | 0.0110 |
| 1-3 | 0.0350 | 0.0356 | 0.0006 |
| 0-3 | 0.0310 | 0.0353 | 0.0043 |
| 2-3 | 0.0260 | 0.0188 | 0.0071 |
| 3-1 | 0.0224 | 0.0216 | 0.0008 |
| 3-2 | 0.0196 | 0.0144 | 0.0053 |
| 3-0 | 0.0158 | 0.0168 | 0.0010 |
| **Sum (top 15)** | **0.9247** | **0.9432** | — |
- High-score mass (total ≥9 goals): 1.27e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### France vs Morocco
- CS outcomes: 26  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-0 | 0.1231 | 0.1215 | 0.0016 |
| 2-0 | 0.1143 | 0.1211 | 0.0068 |
| 1-1 | 0.1067 | 0.1109 | 0.0042 |
| 2-1 | 0.1000 | 0.0991 | 0.0009 |
| 0-0 | 0.0727 | 0.0836 | 0.0109 |
| 3-0 | 0.0667 | 0.0748 | 0.0081 |
| 3-1 | 0.0571 | 0.0602 | 0.0030 |
| 0-1 | 0.0533 | 0.0555 | 0.0022 |
| 2-2 | 0.0444 | 0.0412 | 0.0032 |
| 1-2 | 0.0400 | 0.0412 | 0.0012 |
| 4-0 | 0.0348 | 0.0363 | 0.0015 |
| 3-2 | 0.0286 | 0.0250 | 0.0036 |
| 4-1 | 0.0286 | 0.0283 | 0.0002 |
| 0-2 | 0.0222 | 0.0230 | 0.0008 |
| 5-0 | 0.0157 | 0.0136 | 0.0021 |
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
