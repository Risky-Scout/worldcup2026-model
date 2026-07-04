# Correct-Score Reconciliation Audit

**Generated**: 2026-07-04T03:24:43Z

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

### Canada vs Morocco
- CS outcomes: 25  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-1 | 0.1347 | 0.1336 | 0.0011 |
| 0-1 | 0.1347 | 0.1286 | 0.0061 |
| 1-2 | 0.1010 | 0.0948 | 0.0062 |
| 0-2 | 0.0898 | 0.1008 | 0.0110 |
| 0-0 | 0.0851 | 0.1020 | 0.0170 |
| 1-0 | 0.0673 | 0.0747 | 0.0074 |
| 2-1 | 0.0539 | 0.0535 | 0.0004 |
| 2-2 | 0.0505 | 0.0443 | 0.0062 |
| 1-3 | 0.0475 | 0.0469 | 0.0006 |
| 0-3 | 0.0449 | 0.0516 | 0.0067 |
| 2-0 | 0.0289 | 0.0353 | 0.0065 |
| 2-3 | 0.0289 | 0.0216 | 0.0072 |
| 0-4 | 0.0197 | 0.0204 | 0.0007 |
| 1-4 | 0.0197 | 0.0179 | 0.0018 |
| 3-1 | 0.0158 | 0.0154 | 0.0004 |
| **Sum (top 15)** | **0.9224** | **0.9415** | — |
- High-score mass (total ≥9 goals): 1.47e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Paraguay vs France
- CS outcomes: 28  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 0-2 | 0.1421 | 0.1534 | 0.0113 |
| 0-3 | 0.1225 | 0.1299 | 0.0074 |
| 0-1 | 0.1137 | 0.1258 | 0.0121 |
| 0-4 | 0.0796 | 0.0848 | 0.0052 |
| 1-2 | 0.0758 | 0.0822 | 0.0064 |
| 1-3 | 0.0663 | 0.0704 | 0.0041 |
| 1-1 | 0.0569 | 0.0615 | 0.0047 |
| 0-0 | 0.0442 | 0.0499 | 0.0057 |
| 0-5 | 0.0442 | 0.0445 | 0.0003 |
| 1-4 | 0.0419 | 0.0446 | 0.0027 |
| 1-0 | 0.0257 | 0.0262 | 0.0005 |
| 2-2 | 0.0234 | 0.0204 | 0.0030 |
| 1-5 | 0.0234 | 0.0220 | 0.0014 |
| 2-3 | 0.0221 | 0.0191 | 0.0030 |
| 0-6 | 0.0194 | 0.0186 | 0.0008 |
| **Sum (top 15)** | **0.9013** | **0.9533** | — |
- High-score mass (total ≥9 goals): 2.28e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Brazil vs Norway
- CS outcomes: 28  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-1 | 0.1131 | 0.1176 | 0.0045 |
| 2-1 | 0.1056 | 0.1020 | 0.0036 |
| 1-0 | 0.0990 | 0.0923 | 0.0067 |
| 2-0 | 0.0754 | 0.0876 | 0.0122 |
| 2-2 | 0.0660 | 0.0596 | 0.0064 |
| 1-2 | 0.0609 | 0.0611 | 0.0002 |
| 3-1 | 0.0566 | 0.0596 | 0.0030 |
| 0-0 | 0.0528 | 0.0682 | 0.0154 |
| 0-1 | 0.0495 | 0.0558 | 0.0063 |
| 3-0 | 0.0466 | 0.0543 | 0.0077 |
| 3-2 | 0.0396 | 0.0346 | 0.0050 |
| 4-1 | 0.0255 | 0.0271 | 0.0015 |
| 0-2 | 0.0255 | 0.0333 | 0.0077 |
| 2-3 | 0.0255 | 0.0206 | 0.0050 |
| 4-0 | 0.0220 | 0.0251 | 0.0031 |
| **Sum (top 15)** | **0.8638** | **0.8989** | — |
- High-score mass (total ≥9 goals): 2.45e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Mexico vs England
- CS outcomes: 26  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-1 | 0.1326 | 0.1372 | 0.0046 |
| 0-1 | 0.1137 | 0.1193 | 0.0056 |
| 1-0 | 0.0995 | 0.1042 | 0.0048 |
| 0-0 | 0.0936 | 0.1110 | 0.0174 |
| 1-2 | 0.0796 | 0.0797 | 0.0001 |
| 2-1 | 0.0723 | 0.0696 | 0.0027 |
| 0-2 | 0.0723 | 0.0782 | 0.0058 |
| 2-0 | 0.0531 | 0.0583 | 0.0052 |
| 2-2 | 0.0468 | 0.0453 | 0.0016 |
| 1-3 | 0.0346 | 0.0331 | 0.0015 |
| 0-3 | 0.0306 | 0.0315 | 0.0009 |
| 3-1 | 0.0284 | 0.0247 | 0.0037 |
| 3-0 | 0.0221 | 0.0204 | 0.0017 |
| 2-3 | 0.0221 | 0.0177 | 0.0044 |
| 3-2 | 0.0194 | 0.0150 | 0.0044 |
| **Sum (top 15)** | **0.9208** | **0.9454** | — |
- High-score mass (total ≥9 goals): 1.26e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Portugal vs Spain
- CS outcomes: 27  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-1 | 0.1209 | 0.1212 | 0.0003 |
| 0-1 | 0.1048 | 0.1026 | 0.0021 |
| 1-2 | 0.0982 | 0.0983 | 0.0001 |
| 0-2 | 0.0786 | 0.0888 | 0.0103 |
| 1-0 | 0.0655 | 0.0665 | 0.0010 |
| 0-0 | 0.0655 | 0.0755 | 0.0100 |
| 2-1 | 0.0604 | 0.0616 | 0.0012 |
| 2-2 | 0.0604 | 0.0557 | 0.0048 |
| 0-3 | 0.0462 | 0.0519 | 0.0057 |
| 1-3 | 0.0462 | 0.0533 | 0.0071 |
| 2-0 | 0.0342 | 0.0373 | 0.0031 |
| 2-3 | 0.0342 | 0.0307 | 0.0034 |
| 3-1 | 0.0218 | 0.0220 | 0.0002 |
| 3-2 | 0.0218 | 0.0187 | 0.0031 |
| 0-4 | 0.0218 | 0.0224 | 0.0006 |
| **Sum (top 15)** | **0.8804** | **0.9065** | — |
- High-score mass (total ≥9 goals): 2.12e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### USA vs Belgium
- CS outcomes: 32  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-1 | 0.1305 | 0.1301 | 0.0005 |
| 1-2 | 0.0870 | 0.0871 | 0.0000 |
| 2-1 | 0.0783 | 0.0825 | 0.0042 |
| 2-2 | 0.0746 | 0.0676 | 0.0070 |
| 0-1 | 0.0746 | 0.0724 | 0.0022 |
| 1-0 | 0.0712 | 0.0704 | 0.0008 |
| 0-0 | 0.0522 | 0.0707 | 0.0185 |
| 0-2 | 0.0522 | 0.0601 | 0.0079 |
| 2-0 | 0.0435 | 0.0549 | 0.0114 |
| 1-3 | 0.0392 | 0.0422 | 0.0031 |
| 3-1 | 0.0341 | 0.0390 | 0.0049 |
| 3-2 | 0.0341 | 0.0304 | 0.0036 |
| 2-3 | 0.0341 | 0.0311 | 0.0030 |
| 0-3 | 0.0253 | 0.0303 | 0.0050 |
| 3-0 | 0.0230 | 0.0273 | 0.0043 |
| **Sum (top 15)** | **0.8538** | **0.8961** | — |
- High-score mass (total ≥9 goals): 2.58e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Argentina vs Egypt
- CS outcomes: 24  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-0 | 0.1529 | 0.1544 | 0.0014 |
| 2-0 | 0.1422 | 0.1476 | 0.0054 |
| 2-1 | 0.0954 | 0.0926 | 0.0027 |
| 3-0 | 0.0954 | 0.0980 | 0.0027 |
| 1-1 | 0.0853 | 0.0877 | 0.0024 |
| 0-0 | 0.0737 | 0.0774 | 0.0037 |
| 3-1 | 0.0579 | 0.0600 | 0.0021 |
| 4-0 | 0.0507 | 0.0503 | 0.0003 |
| 0-1 | 0.0352 | 0.0461 | 0.0108 |
| 4-1 | 0.0312 | 0.0303 | 0.0008 |
| 2-2 | 0.0312 | 0.0273 | 0.0039 |
| 3-2 | 0.0238 | 0.0192 | 0.0047 |
| 5-0 | 0.0238 | 0.0204 | 0.0035 |
| 1-2 | 0.0238 | 0.0270 | 0.0031 |
| 5-1 | 0.0133 | 0.0119 | 0.0014 |
| **Sum (top 15)** | **0.9358** | **0.9502** | — |
- High-score mass (total ≥9 goals): 1.67e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS
