# Correct-Score Reconciliation Audit

**Generated**: 2026-07-03T22:02:51Z

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
| Total 2026 matches predicted | 8 |
| Matches with any CS data | 8 |
| Matches with 1 CS vendor | 8 |
| Matches with 2+ CS vendors | 0 |

## Per-match correct-score audit

### Argentina vs Cabo Verde
- CS outcomes: 24  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 2-0 | 0.1497 | 0.1566 | 0.0070 |
| 3-0 | 0.1347 | 0.1371 | 0.0024 |
| 1-0 | 0.1243 | 0.1340 | 0.0097 |
| 4-0 | 0.0851 | 0.0896 | 0.0045 |
| 2-1 | 0.0735 | 0.0786 | 0.0051 |
| 3-1 | 0.0622 | 0.0679 | 0.0057 |
| 1-1 | 0.0505 | 0.0543 | 0.0038 |
| 5-0 | 0.0475 | 0.0480 | 0.0005 |
| 4-1 | 0.0425 | 0.0447 | 0.0022 |
| 0-0 | 0.0425 | 0.0451 | 0.0026 |
| 5-1 | 0.0261 | 0.0220 | 0.0041 |
| 6-0 | 0.0261 | 0.0213 | 0.0047 |
| 2-2 | 0.0224 | 0.0183 | 0.0042 |
| 0-1 | 0.0197 | 0.0236 | 0.0039 |
| 3-2 | 0.0176 | 0.0172 | 0.0004 |
| **Sum (top 15)** | **0.9244** | **0.9583** | — |
- High-score mass (total ≥9 goals): 2.33e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Colombia vs Ghana
- CS outcomes: 25  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-0 | 0.1451 | 0.1398 | 0.0053 |
| 2-0 | 0.1330 | 0.1384 | 0.0054 |
| 1-1 | 0.0997 | 0.1018 | 0.0020 |
| 2-1 | 0.0939 | 0.0944 | 0.0005 |
| 3-0 | 0.0798 | 0.0883 | 0.0085 |
| 0-0 | 0.0725 | 0.0840 | 0.0115 |
| 3-1 | 0.0614 | 0.0612 | 0.0002 |
| 0-1 | 0.0443 | 0.0493 | 0.0049 |
| 4-0 | 0.0420 | 0.0445 | 0.0025 |
| 2-2 | 0.0347 | 0.0322 | 0.0025 |
| 1-2 | 0.0307 | 0.0316 | 0.0009 |
| 4-1 | 0.0285 | 0.0291 | 0.0006 |
| 3-2 | 0.0222 | 0.0203 | 0.0018 |
| 5-0 | 0.0195 | 0.0175 | 0.0019 |
| 0-2 | 0.0173 | 0.0170 | 0.0004 |
| **Sum (top 15)** | **0.9245** | **0.9493** | — |
- High-score mass (total ≥9 goals): 1.63e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Canada vs Morocco
- CS outcomes: 25  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 0-1 | 0.1346 | 0.1297 | 0.0049 |
| 1-1 | 0.1243 | 0.1309 | 0.0067 |
| 0-2 | 0.1010 | 0.1046 | 0.0037 |
| 1-2 | 0.0950 | 0.0917 | 0.0034 |
| 0-0 | 0.0850 | 0.1051 | 0.0201 |
| 1-0 | 0.0734 | 0.0780 | 0.0045 |
| 2-1 | 0.0505 | 0.0524 | 0.0020 |
| 0-3 | 0.0505 | 0.0524 | 0.0019 |
| 2-2 | 0.0475 | 0.0441 | 0.0034 |
| 1-3 | 0.0475 | 0.0458 | 0.0017 |
| 2-0 | 0.0288 | 0.0355 | 0.0067 |
| 2-3 | 0.0261 | 0.0205 | 0.0056 |
| 0-4 | 0.0224 | 0.0201 | 0.0023 |
| 1-4 | 0.0197 | 0.0172 | 0.0025 |
| 3-1 | 0.0158 | 0.0153 | 0.0006 |
| **Sum (top 15)** | **0.9221** | **0.9433** | — |
- High-score mass (total ≥9 goals): 1.43e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Paraguay vs France
- CS outcomes: 27  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 0-2 | 0.1484 | 0.1562 | 0.0078 |
| 0-1 | 0.1233 | 0.1316 | 0.0083 |
| 0-3 | 0.1233 | 0.1292 | 0.0059 |
| 1-2 | 0.0763 | 0.0824 | 0.0061 |
| 0-4 | 0.0763 | 0.0815 | 0.0052 |
| 1-1 | 0.0617 | 0.0637 | 0.0021 |
| 1-3 | 0.0617 | 0.0678 | 0.0061 |
| 0-0 | 0.0471 | 0.0526 | 0.0054 |
| 1-4 | 0.0422 | 0.0430 | 0.0008 |
| 0-5 | 0.0401 | 0.0414 | 0.0013 |
| 1-0 | 0.0259 | 0.0273 | 0.0015 |
| 2-2 | 0.0223 | 0.0202 | 0.0020 |
| 1-5 | 0.0223 | 0.0211 | 0.0011 |
| 2-3 | 0.0195 | 0.0182 | 0.0014 |
| 0-6 | 0.0195 | 0.0172 | 0.0023 |
| **Sum (top 15)** | **0.9099** | **0.9536** | — |
- High-score mass (total ≥9 goals): 2.19e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Brazil vs Norway
- CS outcomes: 28  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-1 | 0.1131 | 0.1179 | 0.0047 |
| 2-1 | 0.1056 | 0.1019 | 0.0037 |
| 1-0 | 0.0990 | 0.0936 | 0.0054 |
| 2-0 | 0.0754 | 0.0881 | 0.0127 |
| 2-2 | 0.0660 | 0.0592 | 0.0068 |
| 1-2 | 0.0609 | 0.0609 | 0.0000 |
| 3-1 | 0.0566 | 0.0593 | 0.0027 |
| 0-0 | 0.0528 | 0.0687 | 0.0159 |
| 0-1 | 0.0495 | 0.0565 | 0.0070 |
| 3-0 | 0.0466 | 0.0542 | 0.0077 |
| 3-2 | 0.0396 | 0.0343 | 0.0053 |
| 4-1 | 0.0255 | 0.0268 | 0.0012 |
| 0-2 | 0.0255 | 0.0335 | 0.0080 |
| 2-3 | 0.0255 | 0.0203 | 0.0052 |
| 4-0 | 0.0220 | 0.0250 | 0.0030 |
| **Sum (top 15)** | **0.8638** | **0.9002** | — |
- High-score mass (total ≥9 goals): 2.41e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Mexico vs England
- CS outcomes: 26  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-1 | 0.1320 | 0.1356 | 0.0036 |
| 0-1 | 0.1219 | 0.1230 | 0.0011 |
| 1-0 | 0.0990 | 0.1034 | 0.0044 |
| 0-0 | 0.0990 | 0.1124 | 0.0134 |
| 1-2 | 0.0792 | 0.0801 | 0.0009 |
| 0-2 | 0.0720 | 0.0785 | 0.0064 |
| 2-1 | 0.0660 | 0.0675 | 0.0015 |
| 2-0 | 0.0528 | 0.0571 | 0.0043 |
| 2-2 | 0.0466 | 0.0449 | 0.0017 |
| 1-3 | 0.0344 | 0.0336 | 0.0008 |
| 0-3 | 0.0305 | 0.0324 | 0.0019 |
| 3-1 | 0.0256 | 0.0240 | 0.0016 |
| 3-0 | 0.0220 | 0.0199 | 0.0021 |
| 2-3 | 0.0220 | 0.0178 | 0.0042 |
| 3-2 | 0.0193 | 0.0150 | 0.0044 |
| **Sum (top 15)** | **0.9224** | **0.9451** | — |
- High-score mass (total ≥9 goals): 1.25e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Portugal vs Spain
- CS outcomes: 28  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-1 | 0.1217 | 0.1207 | 0.0010 |
| 0-1 | 0.1130 | 0.1040 | 0.0090 |
| 1-2 | 0.0931 | 0.0965 | 0.0034 |
| 0-2 | 0.0833 | 0.0890 | 0.0057 |
| 0-0 | 0.0719 | 0.0773 | 0.0053 |
| 1-0 | 0.0659 | 0.0655 | 0.0004 |
| 2-1 | 0.0609 | 0.0622 | 0.0013 |
| 2-2 | 0.0528 | 0.0543 | 0.0015 |
| 1-3 | 0.0495 | 0.0543 | 0.0049 |
| 0-3 | 0.0465 | 0.0523 | 0.0057 |
| 2-0 | 0.0344 | 0.0366 | 0.0022 |
| 2-3 | 0.0304 | 0.0301 | 0.0003 |
| 0-4 | 0.0220 | 0.0226 | 0.0006 |
| 1-4 | 0.0220 | 0.0234 | 0.0014 |
| 3-1 | 0.0193 | 0.0219 | 0.0026 |
| **Sum (top 15)** | **0.8868** | **0.9106** | — |
- High-score mass (total ≥9 goals): 2.13e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### USA vs Belgium
- CS outcomes: 31  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-1 | 0.1304 | 0.1303 | 0.0001 |
| 2-1 | 0.0824 | 0.0840 | 0.0016 |
| 1-2 | 0.0824 | 0.0853 | 0.0029 |
| 1-0 | 0.0745 | 0.0704 | 0.0041 |
| 0-1 | 0.0745 | 0.0715 | 0.0030 |
| 2-2 | 0.0712 | 0.0671 | 0.0041 |
| 0-0 | 0.0559 | 0.0723 | 0.0164 |
| 2-0 | 0.0489 | 0.0563 | 0.0074 |
| 0-2 | 0.0489 | 0.0582 | 0.0092 |
| 3-1 | 0.0373 | 0.0401 | 0.0028 |
| 1-3 | 0.0373 | 0.0414 | 0.0042 |
| 3-2 | 0.0340 | 0.0304 | 0.0036 |
| 2-3 | 0.0340 | 0.0311 | 0.0029 |
| 3-0 | 0.0252 | 0.0283 | 0.0030 |
| 0-3 | 0.0252 | 0.0298 | 0.0045 |
| **Sum (top 15)** | **0.8623** | **0.8965** | — |
- High-score mass (total ≥9 goals): 2.58e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS
