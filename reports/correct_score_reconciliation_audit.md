# Correct-Score Reconciliation Audit

**Generated**: 2026-07-05T13:51:58Z

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

### Brazil vs Norway
- CS outcomes: 30  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-1 | 0.1113 | 0.1159 | 0.0047 |
| 2-1 | 0.1038 | 0.1030 | 0.0008 |
| 1-0 | 0.0916 | 0.0845 | 0.0071 |
| 2-0 | 0.0742 | 0.0876 | 0.0134 |
| 2-2 | 0.0649 | 0.0606 | 0.0043 |
| 3-1 | 0.0599 | 0.0637 | 0.0038 |
| 1-2 | 0.0599 | 0.0592 | 0.0007 |
| 0-0 | 0.0487 | 0.0653 | 0.0166 |
| 0-1 | 0.0487 | 0.0507 | 0.0021 |
| 3-0 | 0.0458 | 0.0569 | 0.0111 |
| 3-2 | 0.0410 | 0.0371 | 0.0039 |
| 4-1 | 0.0278 | 0.0303 | 0.0025 |
| 0-2 | 0.0278 | 0.0311 | 0.0033 |
| 2-3 | 0.0251 | 0.0206 | 0.0045 |
| 4-0 | 0.0229 | 0.0279 | 0.0050 |
| **Sum (top 15)** | **0.8535** | **0.8945** | — |
- High-score mass (total ≥9 goals): 2.60e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Mexico vs England
- CS outcomes: 26  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-1 | 0.1331 | 0.1374 | 0.0044 |
| 0-1 | 0.1141 | 0.1164 | 0.0023 |
| 1-0 | 0.0998 | 0.1010 | 0.0012 |
| 0-0 | 0.0998 | 0.1131 | 0.0133 |
| 1-2 | 0.0798 | 0.0809 | 0.0010 |
| 0-2 | 0.0726 | 0.0780 | 0.0054 |
| 2-1 | 0.0665 | 0.0680 | 0.0015 |
| 2-0 | 0.0532 | 0.0568 | 0.0036 |
| 2-2 | 0.0499 | 0.0469 | 0.0030 |
| 1-3 | 0.0347 | 0.0342 | 0.0005 |
| 0-3 | 0.0285 | 0.0321 | 0.0036 |
| 3-1 | 0.0258 | 0.0244 | 0.0013 |
| 3-0 | 0.0222 | 0.0202 | 0.0020 |
| 2-3 | 0.0222 | 0.0184 | 0.0037 |
| 3-2 | 0.0195 | 0.0154 | 0.0041 |
| **Sum (top 15)** | **0.9216** | **0.9432** | — |
- High-score mass (total ≥9 goals): 1.30e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Portugal vs Spain
- CS outcomes: 30  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-1 | 0.1117 | 0.1194 | 0.0077 |
| 1-2 | 0.0977 | 0.0983 | 0.0006 |
| 0-1 | 0.0920 | 0.0979 | 0.0059 |
| 0-2 | 0.0745 | 0.0886 | 0.0142 |
| 2-1 | 0.0651 | 0.0628 | 0.0024 |
| 2-2 | 0.0651 | 0.0579 | 0.0072 |
| 1-0 | 0.0601 | 0.0649 | 0.0047 |
| 0-0 | 0.0558 | 0.0728 | 0.0170 |
| 1-3 | 0.0521 | 0.0554 | 0.0033 |
| 0-3 | 0.0434 | 0.0510 | 0.0076 |
| 2-3 | 0.0372 | 0.0321 | 0.0051 |
| 2-0 | 0.0340 | 0.0380 | 0.0040 |
| 3-2 | 0.0252 | 0.0195 | 0.0057 |
| 1-4 | 0.0252 | 0.0242 | 0.0010 |
| 3-1 | 0.0230 | 0.0224 | 0.0006 |
| **Sum (top 15)** | **0.8622** | **0.9052** | — |
- High-score mass (total ≥9 goals): 2.22e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### USA vs Belgium
- CS outcomes: 32  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-1 | 0.1207 | 0.1283 | 0.0076 |
| 1-2 | 0.0826 | 0.0846 | 0.0020 |
| 2-1 | 0.0784 | 0.0833 | 0.0049 |
| 2-2 | 0.0747 | 0.0694 | 0.0053 |
| 1-0 | 0.0713 | 0.0699 | 0.0014 |
| 0-1 | 0.0713 | 0.0697 | 0.0016 |
| 0-2 | 0.0490 | 0.0579 | 0.0089 |
| 2-0 | 0.0461 | 0.0570 | 0.0109 |
| 0-0 | 0.0461 | 0.0705 | 0.0244 |
| 3-1 | 0.0374 | 0.0409 | 0.0036 |
| 1-3 | 0.0374 | 0.0409 | 0.0036 |
| 2-3 | 0.0374 | 0.0317 | 0.0057 |
| 3-2 | 0.0341 | 0.0312 | 0.0029 |
| 3-0 | 0.0253 | 0.0289 | 0.0036 |
| 0-3 | 0.0253 | 0.0290 | 0.0037 |
| **Sum (top 15)** | **0.8371** | **0.8933** | — |
- High-score mass (total ≥9 goals): 2.62e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Argentina vs Egypt
- CS outcomes: 26  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-0 | 0.1378 | 0.1469 | 0.0091 |
| 2-0 | 0.1355 | 0.1453 | 0.0098 |
| 2-1 | 0.0940 | 0.0935 | 0.0005 |
| 3-0 | 0.0888 | 0.0949 | 0.0061 |
| 1-1 | 0.0888 | 0.0917 | 0.0029 |
| 0-0 | 0.0727 | 0.0789 | 0.0063 |
| 3-1 | 0.0615 | 0.0617 | 0.0003 |
| 4-0 | 0.0470 | 0.0487 | 0.0016 |
| 0-1 | 0.0421 | 0.0481 | 0.0060 |
| 4-1 | 0.0307 | 0.0305 | 0.0003 |
| 2-2 | 0.0307 | 0.0281 | 0.0027 |
| 1-2 | 0.0285 | 0.0281 | 0.0004 |
| 5-0 | 0.0235 | 0.0198 | 0.0037 |
| 3-2 | 0.0222 | 0.0197 | 0.0025 |
| 0-2 | 0.0157 | 0.0155 | 0.0002 |
| **Sum (top 15)** | **0.9196** | **0.9514** | — |
- High-score mass (total ≥9 goals): 1.66e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Switzerland vs Colombia
- CS outcomes: 26  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-1 | 0.1340 | 0.1400 | 0.0060 |
| 0-1 | 0.1237 | 0.1215 | 0.0022 |
| 0-0 | 0.0946 | 0.1137 | 0.0191 |
| 1-0 | 0.0893 | 0.0923 | 0.0029 |
| 1-2 | 0.0893 | 0.0857 | 0.0036 |
| 0-2 | 0.0766 | 0.0849 | 0.0083 |
| 2-1 | 0.0670 | 0.0642 | 0.0028 |
| 2-2 | 0.0503 | 0.0466 | 0.0037 |
| 2-0 | 0.0423 | 0.0487 | 0.0063 |
| 1-3 | 0.0383 | 0.0373 | 0.0010 |
| 0-3 | 0.0350 | 0.0376 | 0.0026 |
| 2-3 | 0.0237 | 0.0189 | 0.0048 |
| 3-1 | 0.0223 | 0.0208 | 0.0015 |
| 3-2 | 0.0175 | 0.0138 | 0.0037 |
| 3-0 | 0.0144 | 0.0157 | 0.0014 |
| **Sum (top 15)** | **0.9183** | **0.9416** | — |
- High-score mass (total ≥9 goals): 1.27e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### France vs Morocco
- CS outcomes: 28  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-0 | 0.1058 | 0.1166 | 0.0109 |
| 2-0 | 0.0992 | 0.1192 | 0.0200 |
| 2-1 | 0.0992 | 0.0988 | 0.0003 |
| 1-1 | 0.0992 | 0.1131 | 0.0140 |
| 3-0 | 0.0661 | 0.0749 | 0.0088 |
| 3-1 | 0.0661 | 0.0632 | 0.0029 |
| 0-0 | 0.0529 | 0.0807 | 0.0278 |
| 2-2 | 0.0467 | 0.0421 | 0.0046 |
| 0-1 | 0.0467 | 0.0545 | 0.0078 |
| 1-2 | 0.0441 | 0.0408 | 0.0033 |
| 3-2 | 0.0345 | 0.0262 | 0.0083 |
| 4-0 | 0.0345 | 0.0366 | 0.0021 |
| 4-1 | 0.0345 | 0.0298 | 0.0047 |
| 0-2 | 0.0233 | 0.0239 | 0.0006 |
| 4-2 | 0.0193 | 0.0119 | 0.0075 |
| **Sum (top 15)** | **0.8720** | **0.9323** | — |
- High-score mass (total ≥9 goals): 1.79e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS
