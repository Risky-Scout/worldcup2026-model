# Correct-Score Reconciliation Audit

**Generated**: 2026-07-04T22:18:30Z

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

### Paraguay vs France
- CS outcomes: 28  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 0-2 | 0.1377 | 0.1498 | 0.0121 |
| 0-1 | 0.1141 | 0.1202 | 0.0060 |
| 0-3 | 0.1141 | 0.1256 | 0.0115 |
| 1-2 | 0.0841 | 0.0864 | 0.0023 |
| 1-3 | 0.0726 | 0.0733 | 0.0007 |
| 0-4 | 0.0726 | 0.0816 | 0.0090 |
| 1-1 | 0.0615 | 0.0656 | 0.0041 |
| 1-4 | 0.0420 | 0.0451 | 0.0031 |
| 0-0 | 0.0399 | 0.0505 | 0.0106 |
| 0-5 | 0.0399 | 0.0429 | 0.0030 |
| 2-2 | 0.0285 | 0.0225 | 0.0060 |
| 2-3 | 0.0258 | 0.0204 | 0.0054 |
| 1-0 | 0.0222 | 0.0259 | 0.0037 |
| 1-5 | 0.0222 | 0.0220 | 0.0002 |
| 2-1 | 0.0195 | 0.0172 | 0.0023 |
| **Sum (top 15)** | **0.8969** | **0.9490** | — |
- High-score mass (total ≥9 goals): 2.30e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Brazil vs Norway
- CS outcomes: 31  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-1 | 0.1123 | 0.1165 | 0.0043 |
| 2-1 | 0.1048 | 0.1027 | 0.0021 |
| 1-0 | 0.0982 | 0.0882 | 0.0101 |
| 2-0 | 0.0786 | 0.0870 | 0.0084 |
| 2-2 | 0.0605 | 0.0598 | 0.0006 |
| 1-2 | 0.0605 | 0.0612 | 0.0007 |
| 0-0 | 0.0561 | 0.0681 | 0.0120 |
| 0-1 | 0.0561 | 0.0549 | 0.0013 |
| 3-1 | 0.0524 | 0.0597 | 0.0073 |
| 3-0 | 0.0462 | 0.0549 | 0.0087 |
| 3-2 | 0.0374 | 0.0354 | 0.0020 |
| 0-2 | 0.0281 | 0.0325 | 0.0045 |
| 4-1 | 0.0254 | 0.0281 | 0.0027 |
| 4-0 | 0.0218 | 0.0258 | 0.0040 |
| 1-3 | 0.0218 | 0.0225 | 0.0007 |
| **Sum (top 15)** | **0.8602** | **0.8973** | — |
- High-score mass (total ≥9 goals): 2.54e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Mexico vs England
- CS outcomes: 24  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-1 | 0.1345 | 0.1363 | 0.0018 |
| 0-1 | 0.1153 | 0.1180 | 0.0027 |
| 1-0 | 0.1009 | 0.1028 | 0.0019 |
| 0-0 | 0.1009 | 0.1116 | 0.0107 |
| 1-2 | 0.0807 | 0.0811 | 0.0003 |
| 0-2 | 0.0734 | 0.0781 | 0.0047 |
| 2-1 | 0.0673 | 0.0684 | 0.0011 |
| 2-0 | 0.0538 | 0.0574 | 0.0035 |
| 2-2 | 0.0475 | 0.0456 | 0.0019 |
| 1-3 | 0.0351 | 0.0341 | 0.0010 |
| 0-3 | 0.0310 | 0.0323 | 0.0012 |
| 3-1 | 0.0260 | 0.0245 | 0.0015 |
| 3-0 | 0.0224 | 0.0203 | 0.0021 |
| 3-2 | 0.0197 | 0.0154 | 0.0043 |
| 2-3 | 0.0197 | 0.0179 | 0.0018 |
| **Sum (top 15)** | **0.9283** | **0.9438** | — |
- High-score mass (total ≥9 goals): 1.30e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Portugal vs Spain
- CS outcomes: 27  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-1 | 0.1126 | 0.1198 | 0.0072 |
| 0-1 | 0.0985 | 0.0985 | 0.0000 |
| 1-2 | 0.0985 | 0.0981 | 0.0004 |
| 0-2 | 0.0829 | 0.0899 | 0.0070 |
| 1-0 | 0.0606 | 0.0645 | 0.0038 |
| 2-1 | 0.0606 | 0.0619 | 0.0013 |
| 0-0 | 0.0606 | 0.0751 | 0.0145 |
| 2-2 | 0.0606 | 0.0573 | 0.0033 |
| 1-3 | 0.0492 | 0.0540 | 0.0048 |
| 0-3 | 0.0464 | 0.0514 | 0.0051 |
| 2-0 | 0.0375 | 0.0383 | 0.0008 |
| 2-3 | 0.0343 | 0.0310 | 0.0033 |
| 3-1 | 0.0254 | 0.0229 | 0.0025 |
| 1-4 | 0.0254 | 0.0238 | 0.0016 |
| 3-2 | 0.0219 | 0.0191 | 0.0027 |
| **Sum (top 15)** | **0.8751** | **0.9056** | — |
- High-score mass (total ≥9 goals): 2.17e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### USA vs Belgium
- CS outcomes: 31  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-1 | 0.1202 | 0.1286 | 0.0083 |
| 1-2 | 0.0868 | 0.0861 | 0.0008 |
| 2-1 | 0.0823 | 0.0841 | 0.0018 |
| 1-0 | 0.0744 | 0.0704 | 0.0040 |
| 0-1 | 0.0744 | 0.0705 | 0.0039 |
| 2-2 | 0.0711 | 0.0683 | 0.0028 |
| 0-0 | 0.0521 | 0.0733 | 0.0212 |
| 0-2 | 0.0521 | 0.0587 | 0.0066 |
| 2-0 | 0.0488 | 0.0568 | 0.0080 |
| 1-3 | 0.0372 | 0.0408 | 0.0036 |
| 3-1 | 0.0340 | 0.0392 | 0.0052 |
| 3-2 | 0.0340 | 0.0305 | 0.0035 |
| 2-3 | 0.0340 | 0.0308 | 0.0032 |
| 0-3 | 0.0279 | 0.0297 | 0.0018 |
| 3-0 | 0.0252 | 0.0281 | 0.0029 |
| **Sum (top 15)** | **0.8547** | **0.8959** | — |
- High-score mass (total ≥9 goals): 2.58e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Argentina vs Egypt
- CS outcomes: 26  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-0 | 0.1417 | 0.1500 | 0.0083 |
| 2-0 | 0.1346 | 0.1480 | 0.0134 |
| 2-1 | 0.0950 | 0.0930 | 0.0021 |
| 3-0 | 0.0897 | 0.0974 | 0.0077 |
| 1-1 | 0.0897 | 0.0917 | 0.0019 |
| 0-0 | 0.0673 | 0.0787 | 0.0114 |
| 3-1 | 0.0621 | 0.0615 | 0.0006 |
| 4-0 | 0.0475 | 0.0505 | 0.0030 |
| 0-1 | 0.0385 | 0.0461 | 0.0076 |
| 2-2 | 0.0351 | 0.0271 | 0.0080 |
| 4-1 | 0.0311 | 0.0305 | 0.0006 |
| 1-2 | 0.0261 | 0.0258 | 0.0003 |
| 3-2 | 0.0224 | 0.0187 | 0.0037 |
| 5-0 | 0.0224 | 0.0207 | 0.0018 |
| 5-1 | 0.0144 | 0.0121 | 0.0024 |
| **Sum (top 15)** | **0.9178** | **0.9518** | — |
- High-score mass (total ≥9 goals): 1.65e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Switzerland vs Colombia
- CS outcomes: 26  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-1 | 0.1232 | 0.1355 | 0.0123 |
| 0-1 | 0.1232 | 0.1171 | 0.0061 |
| 1-0 | 0.0890 | 0.0886 | 0.0004 |
| 0-0 | 0.0890 | 0.1086 | 0.0196 |
| 1-2 | 0.0843 | 0.0853 | 0.0010 |
| 0-2 | 0.0801 | 0.0843 | 0.0042 |
| 2-1 | 0.0668 | 0.0654 | 0.0014 |
| 2-0 | 0.0471 | 0.0489 | 0.0018 |
| 2-2 | 0.0445 | 0.0487 | 0.0042 |
| 1-3 | 0.0401 | 0.0394 | 0.0007 |
| 0-3 | 0.0348 | 0.0382 | 0.0034 |
| 3-1 | 0.0258 | 0.0226 | 0.0033 |
| 2-3 | 0.0223 | 0.0203 | 0.0020 |
| 3-0 | 0.0195 | 0.0169 | 0.0026 |
| 3-2 | 0.0195 | 0.0153 | 0.0043 |
| **Sum (top 15)** | **0.9094** | **0.9351** | — |
- High-score mass (total ≥9 goals): 1.42e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS
