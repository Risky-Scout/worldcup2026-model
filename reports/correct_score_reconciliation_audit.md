# Correct-Score Reconciliation Audit

**Generated**: 2026-07-03T08:14:12Z

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
| Total 2026 matches predicted | 9 |
| Matches with any CS data | 9 |
| Matches with 1 CS vendor | 9 |
| Matches with 2+ CS vendors | 0 |

## Per-match correct-score audit

### Australia vs Egypt
- CS outcomes: 22  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-1 | 0.1451 | 0.1475 | 0.0024 |
| 0-1 | 0.1426 | 0.1457 | 0.0031 |
| 0-0 | 0.1250 | 0.1455 | 0.0204 |
| 1-0 | 0.1084 | 0.1132 | 0.0049 |
| 1-2 | 0.0813 | 0.0770 | 0.0043 |
| 0-2 | 0.0739 | 0.0883 | 0.0144 |
| 2-1 | 0.0625 | 0.0589 | 0.0036 |
| 2-2 | 0.0478 | 0.0350 | 0.0128 |
| 2-0 | 0.0406 | 0.0530 | 0.0124 |
| 0-3 | 0.0313 | 0.0328 | 0.0015 |
| 1-3 | 0.0290 | 0.0256 | 0.0034 |
| 3-1 | 0.0198 | 0.0150 | 0.0048 |
| 2-3 | 0.0177 | 0.0100 | 0.0077 |
| 3-0 | 0.0145 | 0.0147 | 0.0002 |
| 3-2 | 0.0133 | 0.0075 | 0.0059 |
| **Sum (top 15)** | **0.9529** | **0.9696** | — |
- High-score mass (total ≥9 goals): 4.21e-06
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Argentina vs Cabo Verde
- CS outcomes: 25  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 2-0 | 0.1567 | 0.1603 | 0.0036 |
| 3-0 | 0.1358 | 0.1378 | 0.0020 |
| 1-0 | 0.1086 | 0.1259 | 0.0173 |
| 4-0 | 0.0959 | 0.0937 | 0.0022 |
| 2-1 | 0.0679 | 0.0765 | 0.0086 |
| 3-1 | 0.0627 | 0.0678 | 0.0051 |
| 5-0 | 0.0509 | 0.0491 | 0.0018 |
| 1-1 | 0.0479 | 0.0545 | 0.0066 |
| 4-1 | 0.0429 | 0.0448 | 0.0019 |
| 0-0 | 0.0429 | 0.0462 | 0.0033 |
| 6-0 | 0.0263 | 0.0215 | 0.0048 |
| 5-1 | 0.0240 | 0.0220 | 0.0020 |
| 0-1 | 0.0226 | 0.0238 | 0.0011 |
| 3-2 | 0.0177 | 0.0172 | 0.0005 |
| 2-2 | 0.0160 | 0.0176 | 0.0016 |
| **Sum (top 15)** | **0.9188** | **0.9587** | — |
- High-score mass (total ≥9 goals): 2.34e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Colombia vs Ghana
- CS outcomes: 25  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-0 | 0.1442 | 0.1461 | 0.0019 |
| 2-0 | 0.1346 | 0.1429 | 0.0084 |
| 2-1 | 0.0950 | 0.0935 | 0.0015 |
| 1-1 | 0.0950 | 0.1000 | 0.0050 |
| 3-0 | 0.0807 | 0.0887 | 0.0080 |
| 0-0 | 0.0769 | 0.0886 | 0.0117 |
| 3-1 | 0.0621 | 0.0596 | 0.0025 |
| 0-1 | 0.0449 | 0.0509 | 0.0061 |
| 4-0 | 0.0425 | 0.0440 | 0.0016 |
| 2-2 | 0.0351 | 0.0299 | 0.0052 |
| 1-2 | 0.0311 | 0.0299 | 0.0012 |
| 4-1 | 0.0288 | 0.0278 | 0.0011 |
| 3-2 | 0.0224 | 0.0188 | 0.0036 |
| 5-0 | 0.0197 | 0.0170 | 0.0027 |
| 0-2 | 0.0158 | 0.0166 | 0.0008 |
| **Sum (top 15)** | **0.9287** | **0.9543** | — |
- High-score mass (total ≥9 goals): 1.57e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Canada vs Morocco
- CS outcomes: 25  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 0-1 | 0.1369 | 0.1337 | 0.0033 |
| 1-1 | 0.1243 | 0.1263 | 0.0020 |
| 0-2 | 0.1077 | 0.1137 | 0.0059 |
| 1-2 | 0.0951 | 0.0937 | 0.0014 |
| 0-0 | 0.0898 | 0.1039 | 0.0141 |
| 1-0 | 0.0673 | 0.0708 | 0.0034 |
| 0-3 | 0.0539 | 0.0601 | 0.0063 |
| 2-1 | 0.0475 | 0.0469 | 0.0006 |
| 1-3 | 0.0475 | 0.0490 | 0.0015 |
| 2-2 | 0.0425 | 0.0402 | 0.0024 |
| 2-0 | 0.0289 | 0.0303 | 0.0015 |
| 2-3 | 0.0261 | 0.0207 | 0.0054 |
| 0-4 | 0.0238 | 0.0247 | 0.0009 |
| 1-4 | 0.0224 | 0.0199 | 0.0025 |
| 3-1 | 0.0144 | 0.0125 | 0.0020 |
| **Sum (top 15)** | **0.9282** | **0.9463** | — |
- High-score mass (total ≥9 goals): 1.38e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Paraguay vs France
- CS outcomes: 27  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 0-2 | 0.1460 | 0.1517 | 0.0057 |
| 0-3 | 0.1235 | 0.1295 | 0.0060 |
| 0-1 | 0.1147 | 0.1207 | 0.0060 |
| 0-4 | 0.0803 | 0.0844 | 0.0041 |
| 1-2 | 0.0730 | 0.0820 | 0.0090 |
| 1-3 | 0.0669 | 0.0713 | 0.0044 |
| 1-1 | 0.0573 | 0.0627 | 0.0053 |
| 0-0 | 0.0472 | 0.0507 | 0.0034 |
| 0-5 | 0.0446 | 0.0442 | 0.0004 |
| 1-4 | 0.0423 | 0.0453 | 0.0030 |
| 1-0 | 0.0236 | 0.0258 | 0.0022 |
| 2-2 | 0.0223 | 0.0217 | 0.0006 |
| 1-5 | 0.0223 | 0.0220 | 0.0003 |
| 0-6 | 0.0223 | 0.0188 | 0.0035 |
| 2-3 | 0.0196 | 0.0196 | 0.0000 |
| **Sum (top 15)** | **0.9059** | **0.9501** | — |
- High-score mass (total ≥9 goals): 2.32e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Brazil vs Norway
- CS outcomes: 30  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-1 | 0.1128 | 0.1187 | 0.0059 |
| 2-1 | 0.0987 | 0.0997 | 0.0010 |
| 1-0 | 0.0929 | 0.0904 | 0.0025 |
| 2-0 | 0.0752 | 0.0868 | 0.0116 |
| 2-2 | 0.0658 | 0.0605 | 0.0053 |
| 1-2 | 0.0607 | 0.0618 | 0.0011 |
| 0-1 | 0.0564 | 0.0584 | 0.0020 |
| 3-1 | 0.0526 | 0.0580 | 0.0054 |
| 0-0 | 0.0526 | 0.0693 | 0.0166 |
| 3-0 | 0.0439 | 0.0526 | 0.0088 |
| 3-2 | 0.0376 | 0.0344 | 0.0032 |
| 0-2 | 0.0304 | 0.0351 | 0.0048 |
| 4-1 | 0.0255 | 0.0264 | 0.0010 |
| 1-3 | 0.0255 | 0.0233 | 0.0021 |
| 2-3 | 0.0255 | 0.0208 | 0.0046 |
| **Sum (top 15)** | **0.8560** | **0.8964** | — |
- High-score mass (total ≥9 goals): 2.42e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Mexico vs England
- CS outcomes: 25  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-1 | 0.1324 | 0.1373 | 0.0049 |
| 0-1 | 0.1222 | 0.1239 | 0.0018 |
| 1-0 | 0.0993 | 0.1046 | 0.0053 |
| 0-0 | 0.0993 | 0.1154 | 0.0161 |
| 1-2 | 0.0794 | 0.0791 | 0.0003 |
| 2-1 | 0.0722 | 0.0687 | 0.0035 |
| 0-2 | 0.0722 | 0.0785 | 0.0063 |
| 2-0 | 0.0529 | 0.0576 | 0.0046 |
| 2-2 | 0.0441 | 0.0438 | 0.0004 |
| 0-3 | 0.0345 | 0.0324 | 0.0021 |
| 1-3 | 0.0305 | 0.0318 | 0.0013 |
| 3-1 | 0.0256 | 0.0235 | 0.0022 |
| 3-0 | 0.0221 | 0.0198 | 0.0023 |
| 2-3 | 0.0221 | 0.0171 | 0.0050 |
| 3-2 | 0.0173 | 0.0142 | 0.0031 |
| **Sum (top 15)** | **0.9261** | **0.9476** | — |
- High-score mass (total ≥9 goals): 1.19e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Portugal vs Spain
- CS outcomes: 28  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-1 | 0.1217 | 0.1234 | 0.0018 |
| 0-1 | 0.1130 | 0.1066 | 0.0064 |
| 1-2 | 0.0989 | 0.0970 | 0.0018 |
| 0-2 | 0.0879 | 0.0914 | 0.0035 |
| 0-0 | 0.0659 | 0.0789 | 0.0129 |
| 1-0 | 0.0608 | 0.0676 | 0.0067 |
| 2-1 | 0.0565 | 0.0614 | 0.0049 |
| 2-2 | 0.0527 | 0.0535 | 0.0008 |
| 1-3 | 0.0494 | 0.0522 | 0.0028 |
| 0-3 | 0.0465 | 0.0507 | 0.0042 |
| 2-0 | 0.0304 | 0.0376 | 0.0072 |
| 2-3 | 0.0304 | 0.0283 | 0.0021 |
| 0-4 | 0.0233 | 0.0215 | 0.0017 |
| 1-4 | 0.0233 | 0.0220 | 0.0013 |
| 3-1 | 0.0220 | 0.0222 | 0.0002 |
| **Sum (top 15)** | **0.8826** | **0.9143** | — |
- High-score mass (total ≥9 goals): 1.99e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### USA vs Belgium
- CS outcomes: 31  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-1 | 0.1297 | 0.1300 | 0.0004 |
| 2-1 | 0.0819 | 0.0850 | 0.0031 |
| 1-2 | 0.0819 | 0.0836 | 0.0018 |
| 1-0 | 0.0778 | 0.0747 | 0.0031 |
| 0-1 | 0.0741 | 0.0724 | 0.0017 |
| 2-2 | 0.0707 | 0.0662 | 0.0046 |
| 0-0 | 0.0556 | 0.0725 | 0.0170 |
| 2-0 | 0.0486 | 0.0588 | 0.0102 |
| 0-2 | 0.0458 | 0.0561 | 0.0103 |
| 3-1 | 0.0370 | 0.0411 | 0.0040 |
| 1-3 | 0.0370 | 0.0396 | 0.0025 |
| 3-2 | 0.0338 | 0.0305 | 0.0033 |
| 2-3 | 0.0338 | 0.0299 | 0.0039 |
| 3-0 | 0.0251 | 0.0297 | 0.0046 |
| 0-3 | 0.0251 | 0.0281 | 0.0030 |
| **Sum (top 15)** | **0.8579** | **0.8982** | — |
- High-score mass (total ≥9 goals): 2.51e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS
