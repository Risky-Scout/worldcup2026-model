# Correct-Score Reconciliation Audit

**Generated**: 2026-07-05T18:23:30Z

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
| 1-1 | 0.1123 | 0.1152 | 0.0029 |
| 2-1 | 0.0983 | 0.1013 | 0.0030 |
| 1-0 | 0.0925 | 0.0801 | 0.0124 |
| 2-0 | 0.0786 | 0.0872 | 0.0086 |
| 2-2 | 0.0655 | 0.0621 | 0.0034 |
| 3-1 | 0.0605 | 0.0648 | 0.0044 |
| 1-2 | 0.0561 | 0.0589 | 0.0027 |
| 0-0 | 0.0491 | 0.0640 | 0.0149 |
| 0-1 | 0.0491 | 0.0485 | 0.0006 |
| 3-0 | 0.0462 | 0.0574 | 0.0112 |
| 3-2 | 0.0414 | 0.0384 | 0.0030 |
| 4-1 | 0.0281 | 0.0313 | 0.0033 |
| 4-0 | 0.0254 | 0.0289 | 0.0035 |
| 0-2 | 0.0254 | 0.0299 | 0.0046 |
| 2-3 | 0.0254 | 0.0216 | 0.0037 |
| **Sum (top 15)** | **0.8538** | **0.8896** | — |
- High-score mass (total ≥9 goals): 2.70e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Mexico vs England
- CS outcomes: 25  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-1 | 0.1323 | 0.1384 | 0.0061 |
| 0-1 | 0.1221 | 0.1173 | 0.0048 |
| 1-0 | 0.0992 | 0.1003 | 0.0011 |
| 0-0 | 0.0934 | 0.1110 | 0.0176 |
| 1-2 | 0.0794 | 0.0798 | 0.0004 |
| 2-1 | 0.0722 | 0.0706 | 0.0015 |
| 0-2 | 0.0722 | 0.0758 | 0.0036 |
| 2-0 | 0.0529 | 0.0572 | 0.0043 |
| 2-2 | 0.0467 | 0.0474 | 0.0007 |
| 1-3 | 0.0345 | 0.0335 | 0.0010 |
| 0-3 | 0.0305 | 0.0315 | 0.0009 |
| 3-1 | 0.0256 | 0.0252 | 0.0005 |
| 3-0 | 0.0221 | 0.0208 | 0.0012 |
| 2-3 | 0.0221 | 0.0183 | 0.0038 |
| 3-2 | 0.0194 | 0.0158 | 0.0035 |
| **Sum (top 15)** | **0.9245** | **0.9429** | — |
- High-score mass (total ≥9 goals): 1.33e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Portugal vs Spain
- CS outcomes: 31  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-1 | 0.1113 | 0.1191 | 0.0078 |
| 0-1 | 0.0917 | 0.0918 | 0.0002 |
| 1-2 | 0.0917 | 0.0964 | 0.0047 |
| 0-2 | 0.0742 | 0.0853 | 0.0111 |
| 2-2 | 0.0649 | 0.0606 | 0.0043 |
| 1-0 | 0.0599 | 0.0621 | 0.0022 |
| 2-1 | 0.0599 | 0.0631 | 0.0031 |
| 1-3 | 0.0557 | 0.0573 | 0.0016 |
| 0-0 | 0.0519 | 0.0700 | 0.0181 |
| 0-3 | 0.0433 | 0.0505 | 0.0072 |
| 2-3 | 0.0371 | 0.0336 | 0.0035 |
| 2-0 | 0.0339 | 0.0379 | 0.0040 |
| 3-1 | 0.0251 | 0.0243 | 0.0008 |
| 3-2 | 0.0251 | 0.0212 | 0.0039 |
| 1-4 | 0.0251 | 0.0250 | 0.0001 |
| **Sum (top 15)** | **0.8510** | **0.8983** | — |
- High-score mass (total ≥9 goals): 2.36e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### USA vs Belgium
- CS outcomes: 31  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-1 | 0.1206 | 0.1261 | 0.0054 |
| 2-1 | 0.0825 | 0.0873 | 0.0048 |
| 1-2 | 0.0825 | 0.0826 | 0.0001 |
| 2-2 | 0.0747 | 0.0705 | 0.0041 |
| 1-0 | 0.0713 | 0.0682 | 0.0031 |
| 0-1 | 0.0713 | 0.0649 | 0.0064 |
| 0-2 | 0.0490 | 0.0535 | 0.0045 |
| 2-0 | 0.0461 | 0.0587 | 0.0126 |
| 0-0 | 0.0461 | 0.0674 | 0.0213 |
| 3-1 | 0.0373 | 0.0443 | 0.0069 |
| 3-2 | 0.0373 | 0.0343 | 0.0031 |
| 1-3 | 0.0373 | 0.0394 | 0.0021 |
| 2-3 | 0.0373 | 0.0318 | 0.0056 |
| 3-0 | 0.0253 | 0.0318 | 0.0065 |
| 0-3 | 0.0253 | 0.0267 | 0.0014 |
| **Sum (top 15)** | **0.8442** | **0.8875** | — |
- High-score mass (total ≥9 goals): 2.81e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Argentina vs Egypt
- CS outcomes: 26  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-0 | 0.1387 | 0.1480 | 0.0093 |
| 2-0 | 0.1341 | 0.1453 | 0.0112 |
| 2-1 | 0.0947 | 0.0932 | 0.0015 |
| 3-0 | 0.0894 | 0.0948 | 0.0054 |
| 1-1 | 0.0894 | 0.0929 | 0.0035 |
| 0-0 | 0.0671 | 0.0783 | 0.0112 |
| 3-1 | 0.0619 | 0.0614 | 0.0005 |
| 4-0 | 0.0503 | 0.0492 | 0.0011 |
| 0-1 | 0.0402 | 0.0479 | 0.0077 |
| 4-1 | 0.0309 | 0.0302 | 0.0007 |
| 2-2 | 0.0309 | 0.0281 | 0.0029 |
| 1-2 | 0.0287 | 0.0279 | 0.0008 |
| 3-2 | 0.0237 | 0.0196 | 0.0041 |
| 5-0 | 0.0224 | 0.0195 | 0.0029 |
| 0-2 | 0.0158 | 0.0156 | 0.0001 |
| **Sum (top 15)** | **0.9182** | **0.9519** | — |
- High-score mass (total ≥9 goals): 1.67e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Switzerland vs Colombia
- CS outcomes: 25  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-1 | 0.1358 | 0.1403 | 0.0044 |
| 0-1 | 0.1233 | 0.1210 | 0.0023 |
| 1-0 | 0.0943 | 0.0929 | 0.0014 |
| 0-0 | 0.0943 | 0.1131 | 0.0189 |
| 1-2 | 0.0844 | 0.0847 | 0.0003 |
| 0-2 | 0.0763 | 0.0847 | 0.0084 |
| 2-1 | 0.0668 | 0.0639 | 0.0029 |
| 2-2 | 0.0501 | 0.0469 | 0.0032 |
| 2-0 | 0.0445 | 0.0485 | 0.0039 |
| 0-3 | 0.0348 | 0.0380 | 0.0032 |
| 1-3 | 0.0348 | 0.0371 | 0.0022 |
| 2-3 | 0.0236 | 0.0192 | 0.0044 |
| 3-1 | 0.0223 | 0.0207 | 0.0015 |
| 3-2 | 0.0195 | 0.0140 | 0.0056 |
| 3-0 | 0.0174 | 0.0160 | 0.0014 |
| **Sum (top 15)** | **0.9224** | **0.9408** | — |
- High-score mass (total ≥9 goals): 1.28e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### France vs Morocco
- CS outcomes: 26  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-0 | 0.1339 | 0.1249 | 0.0090 |
| 2-0 | 0.1071 | 0.1179 | 0.0108 |
| 1-1 | 0.1071 | 0.1118 | 0.0047 |
| 2-1 | 0.1004 | 0.0993 | 0.0011 |
| 0-0 | 0.0669 | 0.0818 | 0.0149 |
| 3-0 | 0.0618 | 0.0731 | 0.0114 |
| 3-1 | 0.0574 | 0.0603 | 0.0030 |
| 2-2 | 0.0502 | 0.0429 | 0.0073 |
| 0-1 | 0.0472 | 0.0536 | 0.0063 |
| 1-2 | 0.0423 | 0.0419 | 0.0003 |
| 4-0 | 0.0349 | 0.0364 | 0.0015 |
| 3-2 | 0.0309 | 0.0255 | 0.0054 |
| 4-1 | 0.0287 | 0.0286 | 0.0001 |
| 0-2 | 0.0223 | 0.0231 | 0.0008 |
| 2-3 | 0.0157 | 0.0103 | 0.0054 |
| **Sum (top 15)** | **0.9068** | **0.9314** | — |
- High-score mass (total ≥9 goals): 1.78e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS
