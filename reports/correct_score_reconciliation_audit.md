# Correct-Score Reconciliation Audit

**Generated**: 2026-07-04T10:02:23Z

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
| 0-1 | 0.1357 | 0.1283 | 0.0074 |
| 1-1 | 0.1335 | 0.1306 | 0.0028 |
| 0-2 | 0.1001 | 0.1088 | 0.0087 |
| 1-2 | 0.1001 | 0.0963 | 0.0038 |
| 0-0 | 0.0843 | 0.1000 | 0.0157 |
| 1-0 | 0.0667 | 0.0690 | 0.0022 |
| 2-1 | 0.0501 | 0.0488 | 0.0012 |
| 0-3 | 0.0501 | 0.0586 | 0.0085 |
| 2-2 | 0.0471 | 0.0425 | 0.0046 |
| 1-3 | 0.0471 | 0.0498 | 0.0027 |
| 2-0 | 0.0258 | 0.0302 | 0.0043 |
| 2-3 | 0.0258 | 0.0217 | 0.0041 |
| 0-4 | 0.0222 | 0.0245 | 0.0022 |
| 1-4 | 0.0222 | 0.0205 | 0.0017 |
| 3-2 | 0.0143 | 0.0107 | 0.0036 |
| **Sum (top 15)** | **0.9253** | **0.9403** | — |
- High-score mass (total ≥9 goals): 1.47e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Paraguay vs France
- CS outcomes: 27  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 0-2 | 0.1400 | 0.1503 | 0.0103 |
| 0-3 | 0.1228 | 0.1286 | 0.0059 |
| 0-1 | 0.1140 | 0.1229 | 0.0089 |
| 1-2 | 0.0840 | 0.0859 | 0.0019 |
| 0-4 | 0.0760 | 0.0824 | 0.0064 |
| 1-3 | 0.0665 | 0.0711 | 0.0046 |
| 1-1 | 0.0614 | 0.0639 | 0.0026 |
| 1-4 | 0.0420 | 0.0451 | 0.0031 |
| 0-0 | 0.0399 | 0.0484 | 0.0085 |
| 0-5 | 0.0399 | 0.0427 | 0.0028 |
| 2-2 | 0.0257 | 0.0220 | 0.0038 |
| 2-3 | 0.0235 | 0.0201 | 0.0033 |
| 1-5 | 0.0235 | 0.0220 | 0.0015 |
| 1-0 | 0.0222 | 0.0261 | 0.0039 |
| 0-6 | 0.0195 | 0.0183 | 0.0012 |
| **Sum (top 15)** | **0.9008** | **0.9498** | — |
- High-score mass (total ≥9 goals): 2.32e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Brazil vs Norway
- CS outcomes: 29  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-1 | 0.1120 | 0.1159 | 0.0039 |
| 2-1 | 0.1045 | 0.1024 | 0.0022 |
| 1-0 | 0.0980 | 0.0909 | 0.0071 |
| 2-0 | 0.0784 | 0.0881 | 0.0096 |
| 2-2 | 0.0653 | 0.0601 | 0.0052 |
| 3-1 | 0.0560 | 0.0604 | 0.0044 |
| 0-1 | 0.0560 | 0.0563 | 0.0003 |
| 1-2 | 0.0560 | 0.0596 | 0.0036 |
| 0-0 | 0.0523 | 0.0666 | 0.0143 |
| 3-0 | 0.0461 | 0.0550 | 0.0089 |
| 3-2 | 0.0373 | 0.0349 | 0.0024 |
| 0-2 | 0.0280 | 0.0329 | 0.0049 |
| 4-1 | 0.0253 | 0.0278 | 0.0025 |
| 2-3 | 0.0231 | 0.0205 | 0.0026 |
| 4-0 | 0.0218 | 0.0257 | 0.0040 |
| **Sum (top 15)** | **0.8602** | **0.8971** | — |
- High-score mass (total ≥9 goals): 2.50e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Mexico vs England
- CS outcomes: 25  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-1 | 0.1324 | 0.1352 | 0.0028 |
| 0-1 | 0.1222 | 0.1204 | 0.0018 |
| 1-0 | 0.0993 | 0.1024 | 0.0032 |
| 0-0 | 0.0993 | 0.1107 | 0.0114 |
| 1-2 | 0.0794 | 0.0802 | 0.0008 |
| 0-2 | 0.0722 | 0.0769 | 0.0047 |
| 2-1 | 0.0662 | 0.0687 | 0.0025 |
| 2-0 | 0.0530 | 0.0573 | 0.0044 |
| 2-2 | 0.0467 | 0.0459 | 0.0008 |
| 1-3 | 0.0345 | 0.0338 | 0.0007 |
| 0-3 | 0.0305 | 0.0320 | 0.0015 |
| 3-1 | 0.0256 | 0.0250 | 0.0007 |
| 3-0 | 0.0221 | 0.0207 | 0.0014 |
| 2-3 | 0.0221 | 0.0183 | 0.0038 |
| 3-2 | 0.0194 | 0.0157 | 0.0037 |
| **Sum (top 15)** | **0.9248** | **0.9433** | — |
- High-score mass (total ≥9 goals): 1.30e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Portugal vs Spain
- CS outcomes: 27  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-1 | 0.1138 | 0.1199 | 0.0061 |
| 0-1 | 0.1062 | 0.1024 | 0.0039 |
| 1-2 | 0.0996 | 0.0983 | 0.0012 |
| 0-2 | 0.0797 | 0.0891 | 0.0094 |
| 1-0 | 0.0613 | 0.0650 | 0.0038 |
| 2-1 | 0.0613 | 0.0619 | 0.0006 |
| 0-0 | 0.0613 | 0.0754 | 0.0141 |
| 2-2 | 0.0613 | 0.0569 | 0.0044 |
| 1-3 | 0.0498 | 0.0540 | 0.0042 |
| 0-3 | 0.0443 | 0.0510 | 0.0067 |
| 2-0 | 0.0346 | 0.0376 | 0.0030 |
| 2-3 | 0.0346 | 0.0307 | 0.0039 |
| 3-1 | 0.0234 | 0.0223 | 0.0011 |
| 3-2 | 0.0234 | 0.0191 | 0.0044 |
| 0-4 | 0.0221 | 0.0223 | 0.0002 |
| **Sum (top 15)** | **0.8767** | **0.9059** | — |
- High-score mass (total ≥9 goals): 2.14e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### USA vs Belgium
- CS outcomes: 30  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-1 | 0.1223 | 0.1281 | 0.0057 |
| 1-2 | 0.0884 | 0.0873 | 0.0010 |
| 2-1 | 0.0837 | 0.0836 | 0.0001 |
| 0-1 | 0.0757 | 0.0730 | 0.0028 |
| 1-0 | 0.0723 | 0.0704 | 0.0019 |
| 2-2 | 0.0723 | 0.0677 | 0.0046 |
| 0-0 | 0.0530 | 0.0723 | 0.0193 |
| 0-2 | 0.0497 | 0.0595 | 0.0098 |
| 2-0 | 0.0468 | 0.0556 | 0.0088 |
| 1-3 | 0.0379 | 0.0418 | 0.0039 |
| 3-1 | 0.0346 | 0.0386 | 0.0040 |
| 3-2 | 0.0346 | 0.0301 | 0.0045 |
| 2-3 | 0.0346 | 0.0311 | 0.0035 |
| 3-0 | 0.0256 | 0.0275 | 0.0018 |
| 0-3 | 0.0256 | 0.0302 | 0.0046 |
| **Sum (top 15)** | **0.8571** | **0.8965** | — |
- High-score mass (total ≥9 goals): 2.57e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Argentina vs Egypt
- CS outcomes: 24  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-0 | 0.1529 | 0.1552 | 0.0023 |
| 2-0 | 0.1422 | 0.1494 | 0.0072 |
| 2-1 | 0.0954 | 0.0920 | 0.0034 |
| 3-0 | 0.0954 | 0.0983 | 0.0030 |
| 1-1 | 0.0853 | 0.0891 | 0.0038 |
| 0-0 | 0.0737 | 0.0805 | 0.0069 |
| 3-1 | 0.0579 | 0.0592 | 0.0013 |
| 4-0 | 0.0507 | 0.0503 | 0.0004 |
| 0-1 | 0.0352 | 0.0462 | 0.0109 |
| 4-1 | 0.0312 | 0.0296 | 0.0016 |
| 2-2 | 0.0312 | 0.0265 | 0.0047 |
| 3-2 | 0.0238 | 0.0183 | 0.0055 |
| 5-0 | 0.0238 | 0.0202 | 0.0036 |
| 1-2 | 0.0238 | 0.0261 | 0.0023 |
| 5-1 | 0.0133 | 0.0115 | 0.0018 |
| **Sum (top 15)** | **0.9358** | **0.9524** | — |
- High-score mass (total ≥9 goals): 1.62e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Switzerland vs Colombia
- CS outcomes: 25  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-1 | 0.1232 | 0.1334 | 0.0102 |
| 0-1 | 0.1144 | 0.1186 | 0.0042 |
| 1-0 | 0.0890 | 0.0921 | 0.0031 |
| 0-0 | 0.0890 | 0.1069 | 0.0179 |
| 1-2 | 0.0843 | 0.0852 | 0.0009 |
| 0-2 | 0.0763 | 0.0848 | 0.0085 |
| 2-1 | 0.0667 | 0.0649 | 0.0019 |
| 2-0 | 0.0501 | 0.0511 | 0.0011 |
| 2-2 | 0.0501 | 0.0480 | 0.0021 |
| 0-3 | 0.0381 | 0.0386 | 0.0005 |
| 1-3 | 0.0381 | 0.0385 | 0.0004 |
| 3-1 | 0.0286 | 0.0227 | 0.0059 |
| 2-3 | 0.0236 | 0.0202 | 0.0034 |
| 3-0 | 0.0222 | 0.0172 | 0.0050 |
| 3-2 | 0.0195 | 0.0149 | 0.0046 |
| **Sum (top 15)** | **0.9132** | **0.9372** | — |
- High-score mass (total ≥9 goals): 1.39e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS
