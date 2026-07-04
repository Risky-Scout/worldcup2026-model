# Correct-Score Reconciliation Audit

**Generated**: 2026-07-04T07:50:54Z

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
| 2-2 | 0.0505 | 0.0443 | 0.0063 |
| 1-3 | 0.0475 | 0.0469 | 0.0006 |
| 0-3 | 0.0449 | 0.0516 | 0.0067 |
| 2-0 | 0.0289 | 0.0353 | 0.0065 |
| 2-3 | 0.0289 | 0.0216 | 0.0073 |
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
| 0-3 | 0.1225 | 0.1299 | 0.0075 |
| 0-1 | 0.1137 | 0.1258 | 0.0121 |
| 0-4 | 0.0796 | 0.0848 | 0.0052 |
| 1-2 | 0.0758 | 0.0822 | 0.0064 |
| 1-3 | 0.0663 | 0.0704 | 0.0040 |
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
| 0-0 | 0.0936 | 0.1111 | 0.0175 |
| 1-2 | 0.0796 | 0.0797 | 0.0002 |
| 2-1 | 0.0723 | 0.0696 | 0.0028 |
| 0-2 | 0.0723 | 0.0782 | 0.0058 |
| 2-0 | 0.0531 | 0.0583 | 0.0053 |
| 2-2 | 0.0468 | 0.0453 | 0.0015 |
| 1-3 | 0.0346 | 0.0331 | 0.0015 |
| 0-3 | 0.0306 | 0.0315 | 0.0009 |
| 3-1 | 0.0284 | 0.0247 | 0.0037 |
| 3-0 | 0.0221 | 0.0204 | 0.0017 |
| 2-3 | 0.0221 | 0.0178 | 0.0043 |
| 3-2 | 0.0194 | 0.0151 | 0.0043 |
| **Sum (top 15)** | **0.9208** | **0.9455** | — |
- High-score mass (total ≥9 goals): 1.26e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Portugal vs Spain
- CS outcomes: 27  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-1 | 0.1209 | 0.1208 | 0.0001 |
| 0-1 | 0.1048 | 0.1028 | 0.0019 |
| 1-2 | 0.0982 | 0.0984 | 0.0002 |
| 0-2 | 0.0786 | 0.0888 | 0.0102 |
| 1-0 | 0.0655 | 0.0664 | 0.0010 |
| 0-0 | 0.0655 | 0.0758 | 0.0103 |
| 2-1 | 0.0604 | 0.0626 | 0.0021 |
| 2-2 | 0.0604 | 0.0557 | 0.0047 |
| 0-3 | 0.0462 | 0.0515 | 0.0053 |
| 1-3 | 0.0462 | 0.0529 | 0.0067 |
| 2-0 | 0.0342 | 0.0374 | 0.0032 |
| 2-3 | 0.0342 | 0.0307 | 0.0035 |
| 3-1 | 0.0218 | 0.0216 | 0.0002 |
| 3-2 | 0.0218 | 0.0188 | 0.0031 |
| 0-4 | 0.0218 | 0.0226 | 0.0007 |
| **Sum (top 15)** | **0.8804** | **0.9067** | — |
- High-score mass (total ≥9 goals): 2.13e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### USA vs Belgium
- CS outcomes: 30  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-1 | 0.1223 | 0.1280 | 0.0056 |
| 1-2 | 0.0884 | 0.0874 | 0.0009 |
| 2-1 | 0.0837 | 0.0835 | 0.0002 |
| 0-1 | 0.0757 | 0.0730 | 0.0027 |
| 1-0 | 0.0723 | 0.0703 | 0.0020 |
| 2-2 | 0.0723 | 0.0677 | 0.0046 |
| 0-0 | 0.0530 | 0.0721 | 0.0191 |
| 0-2 | 0.0497 | 0.0596 | 0.0099 |
| 2-0 | 0.0468 | 0.0554 | 0.0086 |
| 1-3 | 0.0379 | 0.0419 | 0.0040 |
| 3-1 | 0.0346 | 0.0386 | 0.0040 |
| 3-2 | 0.0346 | 0.0301 | 0.0045 |
| 2-3 | 0.0346 | 0.0311 | 0.0034 |
| 3-0 | 0.0256 | 0.0274 | 0.0017 |
| 0-3 | 0.0256 | 0.0303 | 0.0047 |
| **Sum (top 15)** | **0.8571** | **0.8963** | — |
- High-score mass (total ≥9 goals): 2.57e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Argentina vs Egypt
- CS outcomes: 24  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-0 | 0.1529 | 0.1544 | 0.0014 |
| 2-0 | 0.1422 | 0.1477 | 0.0054 |
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
- High-score mass (total ≥9 goals): 1.66e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Switzerland vs Colombia
- CS outcomes: 25  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-1 | 0.1232 | 0.1291 | 0.0059 |
| 0-1 | 0.1144 | 0.1257 | 0.0113 |
| 1-0 | 0.0890 | 0.1022 | 0.0132 |
| 0-0 | 0.0890 | 0.1071 | 0.0181 |
| 1-2 | 0.0843 | 0.0836 | 0.0007 |
| 0-2 | 0.0763 | 0.0824 | 0.0061 |
| 2-1 | 0.0667 | 0.0675 | 0.0007 |
| 2-0 | 0.0501 | 0.0550 | 0.0049 |
| 2-2 | 0.0501 | 0.0456 | 0.0045 |
| 0-3 | 0.0381 | 0.0361 | 0.0020 |
| 1-3 | 0.0381 | 0.0354 | 0.0027 |
| 3-1 | 0.0286 | 0.0236 | 0.0050 |
| 2-3 | 0.0236 | 0.0180 | 0.0056 |
| 3-0 | 0.0222 | 0.0192 | 0.0030 |
| 3-2 | 0.0195 | 0.0144 | 0.0051 |
| **Sum (top 15)** | **0.9132** | **0.9448** | — |
- High-score mass (total ≥9 goals): 1.15e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS
