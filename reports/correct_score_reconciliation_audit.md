# Correct-Score Reconciliation Audit

**Generated**: 2026-07-04T16:08:36Z

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
| 0-1 | 0.1357 | 0.1285 | 0.0072 |
| 1-1 | 0.1335 | 0.1307 | 0.0028 |
| 0-2 | 0.1001 | 0.1089 | 0.0088 |
| 1-2 | 0.1001 | 0.0963 | 0.0039 |
| 0-0 | 0.0843 | 0.1000 | 0.0157 |
| 1-0 | 0.0667 | 0.0691 | 0.0024 |
| 2-1 | 0.0501 | 0.0488 | 0.0012 |
| 0-3 | 0.0501 | 0.0586 | 0.0085 |
| 2-2 | 0.0471 | 0.0424 | 0.0047 |
| 1-3 | 0.0471 | 0.0497 | 0.0026 |
| 2-0 | 0.0258 | 0.0302 | 0.0043 |
| 2-3 | 0.0258 | 0.0216 | 0.0042 |
| 0-4 | 0.0222 | 0.0245 | 0.0022 |
| 1-4 | 0.0222 | 0.0205 | 0.0018 |
| 3-2 | 0.0143 | 0.0107 | 0.0036 |
| **Sum (top 15)** | **0.9253** | **0.9405** | — |
- High-score mass (total ≥9 goals): 1.46e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Paraguay vs France
- CS outcomes: 27  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 0-2 | 0.1400 | 0.1488 | 0.0088 |
| 0-3 | 0.1228 | 0.1282 | 0.0054 |
| 0-1 | 0.1140 | 0.1205 | 0.0065 |
| 1-2 | 0.0840 | 0.0864 | 0.0024 |
| 0-4 | 0.0760 | 0.0821 | 0.0061 |
| 1-3 | 0.0665 | 0.0717 | 0.0052 |
| 1-1 | 0.0614 | 0.0645 | 0.0032 |
| 1-4 | 0.0420 | 0.0455 | 0.0035 |
| 0-0 | 0.0399 | 0.0482 | 0.0083 |
| 0-5 | 0.0399 | 0.0426 | 0.0027 |
| 2-2 | 0.0257 | 0.0228 | 0.0030 |
| 2-3 | 0.0235 | 0.0207 | 0.0028 |
| 1-5 | 0.0235 | 0.0220 | 0.0015 |
| 1-0 | 0.0222 | 0.0260 | 0.0039 |
| 0-6 | 0.0195 | 0.0182 | 0.0012 |
| **Sum (top 15)** | **0.9008** | **0.9481** | — |
- High-score mass (total ≥9 goals): 2.37e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Brazil vs Norway
- CS outcomes: 29  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-1 | 0.1120 | 0.1156 | 0.0035 |
| 2-1 | 0.1045 | 0.1024 | 0.0022 |
| 1-0 | 0.0980 | 0.0914 | 0.0066 |
| 2-0 | 0.0784 | 0.0881 | 0.0097 |
| 2-2 | 0.0653 | 0.0600 | 0.0053 |
| 3-1 | 0.0560 | 0.0604 | 0.0044 |
| 0-1 | 0.0560 | 0.0566 | 0.0006 |
| 1-2 | 0.0560 | 0.0596 | 0.0036 |
| 0-0 | 0.0523 | 0.0662 | 0.0139 |
| 3-0 | 0.0461 | 0.0550 | 0.0089 |
| 3-2 | 0.0373 | 0.0349 | 0.0024 |
| 0-2 | 0.0280 | 0.0329 | 0.0049 |
| 4-1 | 0.0253 | 0.0278 | 0.0025 |
| 2-3 | 0.0231 | 0.0205 | 0.0026 |
| 4-0 | 0.0218 | 0.0258 | 0.0040 |
| **Sum (top 15)** | **0.8602** | **0.8971** | — |
- High-score mass (total ≥9 goals): 2.49e-05
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
| 1-1 | 0.1138 | 0.1197 | 0.0059 |
| 0-1 | 0.1062 | 0.1017 | 0.0046 |
| 1-2 | 0.0996 | 0.0989 | 0.0006 |
| 0-2 | 0.0797 | 0.0894 | 0.0098 |
| 1-0 | 0.0613 | 0.0640 | 0.0027 |
| 2-1 | 0.0613 | 0.0617 | 0.0004 |
| 0-0 | 0.0613 | 0.0751 | 0.0138 |
| 2-2 | 0.0613 | 0.0570 | 0.0043 |
| 1-3 | 0.0498 | 0.0546 | 0.0048 |
| 0-3 | 0.0443 | 0.0515 | 0.0072 |
| 2-0 | 0.0346 | 0.0368 | 0.0021 |
| 2-3 | 0.0346 | 0.0310 | 0.0037 |
| 3-1 | 0.0234 | 0.0221 | 0.0013 |
| 3-2 | 0.0234 | 0.0191 | 0.0043 |
| 0-4 | 0.0221 | 0.0229 | 0.0008 |
| **Sum (top 15)** | **0.8767** | **0.9054** | — |
- High-score mass (total ≥9 goals): 2.16e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### USA vs Belgium
- CS outcomes: 30  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-1 | 0.1223 | 0.1283 | 0.0060 |
| 1-2 | 0.0884 | 0.0873 | 0.0010 |
| 2-1 | 0.0837 | 0.0836 | 0.0001 |
| 0-1 | 0.0757 | 0.0728 | 0.0029 |
| 1-0 | 0.0723 | 0.0704 | 0.0019 |
| 2-2 | 0.0723 | 0.0677 | 0.0046 |
| 0-0 | 0.0530 | 0.0727 | 0.0197 |
| 0-2 | 0.0497 | 0.0594 | 0.0097 |
| 2-0 | 0.0468 | 0.0557 | 0.0089 |
| 1-3 | 0.0379 | 0.0417 | 0.0038 |
| 3-1 | 0.0346 | 0.0385 | 0.0040 |
| 3-2 | 0.0346 | 0.0299 | 0.0046 |
| 2-3 | 0.0346 | 0.0310 | 0.0036 |
| 3-0 | 0.0256 | 0.0276 | 0.0019 |
| 0-3 | 0.0256 | 0.0301 | 0.0044 |
| **Sum (top 15)** | **0.8571** | **0.8967** | — |
- High-score mass (total ≥9 goals): 2.56e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Argentina vs Egypt
- CS outcomes: 24  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-0 | 0.1529 | 0.1528 | 0.0002 |
| 2-0 | 0.1422 | 0.1488 | 0.0066 |
| 2-1 | 0.0954 | 0.0921 | 0.0033 |
| 3-0 | 0.0954 | 0.0987 | 0.0034 |
| 1-1 | 0.0853 | 0.0898 | 0.0045 |
| 0-0 | 0.0737 | 0.0813 | 0.0076 |
| 3-1 | 0.0579 | 0.0594 | 0.0015 |
| 4-0 | 0.0507 | 0.0507 | 0.0000 |
| 0-1 | 0.0352 | 0.0455 | 0.0103 |
| 4-1 | 0.0312 | 0.0298 | 0.0013 |
| 2-2 | 0.0312 | 0.0268 | 0.0043 |
| 3-2 | 0.0238 | 0.0184 | 0.0054 |
| 5-0 | 0.0238 | 0.0205 | 0.0034 |
| 1-2 | 0.0238 | 0.0261 | 0.0023 |
| 5-1 | 0.0133 | 0.0117 | 0.0016 |
| **Sum (top 15)** | **0.9358** | **0.9524** | — |
- High-score mass (total ≥9 goals): 1.63e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Switzerland vs Colombia
- CS outcomes: 25  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-1 | 0.1232 | 0.1338 | 0.0106 |
| 0-1 | 0.1144 | 0.1184 | 0.0040 |
| 1-0 | 0.0890 | 0.0917 | 0.0027 |
| 0-0 | 0.0890 | 0.1073 | 0.0183 |
| 1-2 | 0.0843 | 0.0853 | 0.0010 |
| 0-2 | 0.0763 | 0.0850 | 0.0087 |
| 2-1 | 0.0667 | 0.0646 | 0.0021 |
| 2-0 | 0.0501 | 0.0508 | 0.0008 |
| 2-2 | 0.0501 | 0.0480 | 0.0020 |
| 0-3 | 0.0381 | 0.0389 | 0.0007 |
| 1-3 | 0.0381 | 0.0387 | 0.0005 |
| 3-1 | 0.0286 | 0.0225 | 0.0061 |
| 2-3 | 0.0236 | 0.0202 | 0.0033 |
| 3-0 | 0.0222 | 0.0170 | 0.0052 |
| 3-2 | 0.0195 | 0.0148 | 0.0047 |
| **Sum (top 15)** | **0.9132** | **0.9371** | — |
- High-score mass (total ≥9 goals): 1.39e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS
