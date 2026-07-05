# Correct-Score Reconciliation Audit

**Generated**: 2026-07-05T01:54:40Z

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
- CS outcomes: 31  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-1 | 0.1120 | 0.1172 | 0.0052 |
| 1-0 | 0.0980 | 0.0917 | 0.0064 |
| 2-1 | 0.0980 | 0.0998 | 0.0018 |
| 2-0 | 0.0784 | 0.0887 | 0.0102 |
| 2-2 | 0.0654 | 0.0600 | 0.0053 |
| 3-1 | 0.0560 | 0.0600 | 0.0040 |
| 1-2 | 0.0560 | 0.0598 | 0.0038 |
| 0-0 | 0.0523 | 0.0682 | 0.0160 |
| 0-1 | 0.0523 | 0.0561 | 0.0039 |
| 3-0 | 0.0461 | 0.0549 | 0.0088 |
| 3-2 | 0.0373 | 0.0345 | 0.0028 |
| 0-2 | 0.0280 | 0.0334 | 0.0054 |
| 4-1 | 0.0253 | 0.0274 | 0.0021 |
| 4-0 | 0.0231 | 0.0257 | 0.0027 |
| 2-3 | 0.0231 | 0.0203 | 0.0028 |
| **Sum (top 15)** | **0.8515** | **0.8979** | — |
- High-score mass (total ≥9 goals): 2.45e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Mexico vs England
- CS outcomes: 24  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-1 | 0.1345 | 0.1370 | 0.0025 |
| 0-1 | 0.1153 | 0.1173 | 0.0019 |
| 1-0 | 0.1009 | 0.1034 | 0.0025 |
| 0-0 | 0.1009 | 0.1111 | 0.0102 |
| 1-2 | 0.0807 | 0.0808 | 0.0001 |
| 0-2 | 0.0734 | 0.0773 | 0.0040 |
| 2-1 | 0.0673 | 0.0697 | 0.0024 |
| 2-0 | 0.0538 | 0.0576 | 0.0038 |
| 2-2 | 0.0475 | 0.0451 | 0.0024 |
| 1-3 | 0.0351 | 0.0344 | 0.0007 |
| 0-3 | 0.0310 | 0.0323 | 0.0012 |
| 3-1 | 0.0260 | 0.0244 | 0.0016 |
| 3-0 | 0.0224 | 0.0205 | 0.0019 |
| 3-2 | 0.0197 | 0.0152 | 0.0045 |
| 2-3 | 0.0197 | 0.0179 | 0.0018 |
| **Sum (top 15)** | **0.9283** | **0.9439** | — |
- High-score mass (total ≥9 goals): 1.31e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Portugal vs Spain
- CS outcomes: 27  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-1 | 0.1138 | 0.1199 | 0.0061 |
| 0-1 | 0.1062 | 0.1009 | 0.0053 |
| 1-2 | 0.0996 | 0.0982 | 0.0013 |
| 0-2 | 0.0797 | 0.0880 | 0.0083 |
| 1-0 | 0.0613 | 0.0647 | 0.0035 |
| 2-1 | 0.0613 | 0.0626 | 0.0013 |
| 0-0 | 0.0613 | 0.0749 | 0.0136 |
| 2-2 | 0.0613 | 0.0575 | 0.0038 |
| 1-3 | 0.0498 | 0.0539 | 0.0042 |
| 0-3 | 0.0443 | 0.0505 | 0.0062 |
| 2-0 | 0.0346 | 0.0379 | 0.0032 |
| 2-3 | 0.0346 | 0.0310 | 0.0036 |
| 3-1 | 0.0234 | 0.0229 | 0.0006 |
| 3-2 | 0.0234 | 0.0195 | 0.0039 |
| 0-4 | 0.0221 | 0.0221 | 0.0001 |
| **Sum (top 15)** | **0.8767** | **0.9046** | — |
- High-score mass (total ≥9 goals): 2.18e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### USA vs Belgium
- CS outcomes: 31  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-1 | 0.1209 | 0.1288 | 0.0079 |
| 1-2 | 0.0873 | 0.0861 | 0.0012 |
| 2-1 | 0.0827 | 0.0840 | 0.0013 |
| 0-1 | 0.0748 | 0.0709 | 0.0040 |
| 1-0 | 0.0714 | 0.0695 | 0.0019 |
| 2-2 | 0.0714 | 0.0683 | 0.0032 |
| 0-0 | 0.0524 | 0.0734 | 0.0210 |
| 0-2 | 0.0524 | 0.0589 | 0.0065 |
| 2-0 | 0.0491 | 0.0570 | 0.0079 |
| 3-1 | 0.0374 | 0.0401 | 0.0026 |
| 1-3 | 0.0374 | 0.0408 | 0.0034 |
| 3-2 | 0.0342 | 0.0304 | 0.0037 |
| 2-3 | 0.0342 | 0.0306 | 0.0035 |
| 3-0 | 0.0253 | 0.0283 | 0.0030 |
| 0-3 | 0.0253 | 0.0292 | 0.0039 |
| **Sum (top 15)** | **0.8564** | **0.8964** | — |
- High-score mass (total ≥9 goals): 2.57e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Argentina vs Egypt
- CS outcomes: 26  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-0 | 0.1408 | 0.1468 | 0.0060 |
| 2-0 | 0.1360 | 0.1464 | 0.0104 |
| 2-1 | 0.0891 | 0.0915 | 0.0024 |
| 3-0 | 0.0891 | 0.0968 | 0.0076 |
| 1-1 | 0.0891 | 0.0917 | 0.0025 |
| 0-0 | 0.0729 | 0.0799 | 0.0070 |
| 3-1 | 0.0617 | 0.0620 | 0.0002 |
| 4-0 | 0.0501 | 0.0510 | 0.0009 |
| 0-1 | 0.0401 | 0.0461 | 0.0060 |
| 4-1 | 0.0309 | 0.0308 | 0.0000 |
| 2-2 | 0.0309 | 0.0275 | 0.0034 |
| 1-2 | 0.0287 | 0.0272 | 0.0014 |
| 3-2 | 0.0223 | 0.0193 | 0.0029 |
| 5-0 | 0.0223 | 0.0206 | 0.0017 |
| 5-1 | 0.0143 | 0.0123 | 0.0021 |
| **Sum (top 15)** | **0.9184** | **0.9499** | — |
- High-score mass (total ≥9 goals): 1.67e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Switzerland vs Colombia
- CS outcomes: 26  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-1 | 0.1340 | 0.1397 | 0.0057 |
| 0-1 | 0.1237 | 0.1201 | 0.0036 |
| 1-0 | 0.0894 | 0.0908 | 0.0015 |
| 0-0 | 0.0894 | 0.1097 | 0.0203 |
| 1-2 | 0.0894 | 0.0865 | 0.0029 |
| 0-2 | 0.0731 | 0.0833 | 0.0102 |
| 2-1 | 0.0670 | 0.0646 | 0.0024 |
| 2-2 | 0.0503 | 0.0477 | 0.0025 |
| 2-0 | 0.0447 | 0.0489 | 0.0042 |
| 1-3 | 0.0383 | 0.0382 | 0.0001 |
| 0-3 | 0.0350 | 0.0380 | 0.0030 |
| 2-3 | 0.0237 | 0.0196 | 0.0040 |
| 3-1 | 0.0223 | 0.0212 | 0.0011 |
| 3-2 | 0.0196 | 0.0145 | 0.0051 |
| 3-0 | 0.0158 | 0.0160 | 0.0002 |
| **Sum (top 15)** | **0.9155** | **0.9388** | — |
- High-score mass (total ≥9 goals): 1.35e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### France vs Morocco
- CS outcomes: 28  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-0 | 0.1058 | 0.1006 | 0.0051 |
| 2-0 | 0.0992 | 0.0939 | 0.0052 |
| 2-1 | 0.0992 | 0.0936 | 0.0056 |
| 1-1 | 0.0992 | 0.0959 | 0.0032 |
| 3-0 | 0.0661 | 0.0627 | 0.0034 |
| 3-1 | 0.0661 | 0.0630 | 0.0031 |
| 0-0 | 0.0529 | 0.0530 | 0.0001 |
| 2-2 | 0.0467 | 0.0462 | 0.0004 |
| 0-1 | 0.0467 | 0.0456 | 0.0010 |
| 1-2 | 0.0441 | 0.0426 | 0.0015 |
| 3-2 | 0.0345 | 0.0321 | 0.0024 |
| 4-0 | 0.0345 | 0.0330 | 0.0015 |
| 4-1 | 0.0345 | 0.0320 | 0.0025 |
| 0-2 | 0.0233 | 0.0227 | 0.0006 |
| 4-2 | 0.0193 | 0.0186 | 0.0007 |
| **Sum (top 15)** | **0.8720** | **0.8358** | — |
- High-score mass (total ≥9 goals): 1.17e-04
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS
