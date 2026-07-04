# Correct-Score Reconciliation Audit

**Generated**: 2026-07-04T19:01:04Z

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
- CS outcomes: 27  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 0-2 | 0.1436 | 0.1492 | 0.0056 |
| 0-1 | 0.1237 | 0.1218 | 0.0019 |
| 0-3 | 0.1149 | 0.1258 | 0.0109 |
| 1-2 | 0.0804 | 0.0852 | 0.0048 |
| 0-4 | 0.0766 | 0.0832 | 0.0066 |
| 1-3 | 0.0670 | 0.0718 | 0.0048 |
| 1-1 | 0.0619 | 0.0643 | 0.0025 |
| 0-0 | 0.0423 | 0.0493 | 0.0070 |
| 1-4 | 0.0423 | 0.0457 | 0.0034 |
| 0-5 | 0.0402 | 0.0433 | 0.0031 |
| 2-2 | 0.0259 | 0.0228 | 0.0031 |
| 2-3 | 0.0237 | 0.0204 | 0.0032 |
| 1-5 | 0.0237 | 0.0220 | 0.0017 |
| 1-0 | 0.0223 | 0.0254 | 0.0031 |
| 0-6 | 0.0196 | 0.0186 | 0.0011 |
| **Sum (top 15)** | **0.9083** | **0.9490** | — |
- High-score mass (total ≥9 goals): 2.33e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Brazil vs Norway
- CS outcomes: 31  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-1 | 0.1123 | 0.1164 | 0.0042 |
| 2-1 | 0.1048 | 0.1028 | 0.0020 |
| 1-0 | 0.0982 | 0.0882 | 0.0100 |
| 2-0 | 0.0786 | 0.0873 | 0.0087 |
| 2-2 | 0.0605 | 0.0597 | 0.0007 |
| 1-2 | 0.0605 | 0.0609 | 0.0005 |
| 0-0 | 0.0561 | 0.0682 | 0.0120 |
| 0-1 | 0.0561 | 0.0547 | 0.0015 |
| 3-1 | 0.0524 | 0.0598 | 0.0074 |
| 3-0 | 0.0462 | 0.0553 | 0.0090 |
| 3-2 | 0.0374 | 0.0354 | 0.0020 |
| 0-2 | 0.0281 | 0.0323 | 0.0042 |
| 4-1 | 0.0254 | 0.0282 | 0.0028 |
| 4-0 | 0.0218 | 0.0260 | 0.0042 |
| 1-3 | 0.0218 | 0.0223 | 0.0005 |
| **Sum (top 15)** | **0.8602** | **0.8975** | — |
- High-score mass (total ≥9 goals): 2.53e-05
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
| 1-1 | 0.1126 | 0.1195 | 0.0069 |
| 0-1 | 0.0985 | 0.0983 | 0.0002 |
| 1-2 | 0.0985 | 0.0981 | 0.0004 |
| 0-2 | 0.0829 | 0.0898 | 0.0068 |
| 1-0 | 0.0606 | 0.0643 | 0.0037 |
| 2-1 | 0.0606 | 0.0620 | 0.0014 |
| 0-0 | 0.0606 | 0.0746 | 0.0140 |
| 2-2 | 0.0606 | 0.0574 | 0.0032 |
| 1-3 | 0.0492 | 0.0542 | 0.0049 |
| 0-3 | 0.0464 | 0.0515 | 0.0051 |
| 2-0 | 0.0375 | 0.0382 | 0.0007 |
| 2-3 | 0.0343 | 0.0311 | 0.0031 |
| 3-1 | 0.0254 | 0.0230 | 0.0025 |
| 1-4 | 0.0254 | 0.0239 | 0.0015 |
| 3-2 | 0.0219 | 0.0192 | 0.0026 |
| **Sum (top 15)** | **0.8751** | **0.9051** | — |
- High-score mass (total ≥9 goals): 2.19e-05
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
| 1-0 | 0.1417 | 0.1492 | 0.0075 |
| 2-0 | 0.1346 | 0.1481 | 0.0134 |
| 2-1 | 0.0950 | 0.0928 | 0.0022 |
| 3-0 | 0.0897 | 0.0977 | 0.0079 |
| 1-1 | 0.0897 | 0.0922 | 0.0024 |
| 0-0 | 0.0673 | 0.0793 | 0.0120 |
| 3-1 | 0.0621 | 0.0616 | 0.0005 |
| 4-0 | 0.0475 | 0.0507 | 0.0032 |
| 0-1 | 0.0385 | 0.0458 | 0.0074 |
| 2-2 | 0.0351 | 0.0270 | 0.0081 |
| 4-1 | 0.0311 | 0.0305 | 0.0006 |
| 1-2 | 0.0261 | 0.0257 | 0.0003 |
| 3-2 | 0.0224 | 0.0185 | 0.0039 |
| 5-0 | 0.0224 | 0.0208 | 0.0016 |
| 5-1 | 0.0144 | 0.0121 | 0.0023 |
| **Sum (top 15)** | **0.9178** | **0.9521** | — |
- High-score mass (total ≥9 goals): 1.66e-05
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
