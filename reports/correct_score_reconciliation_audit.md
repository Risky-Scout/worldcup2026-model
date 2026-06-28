# Correct-Score Reconciliation Audit

**Generated**: 2026-06-28T02:06:26Z

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

### South Africa vs Canada
- CS outcomes: 24  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 0-1 | 0.1405 | 0.1359 | 0.0046 |
| 1-1 | 0.1164 | 0.1205 | 0.0041 |
| 0-2 | 0.1086 | 0.1171 | 0.0084 |
| 1-2 | 0.1019 | 0.0969 | 0.0049 |
| 0-0 | 0.0776 | 0.0952 | 0.0176 |
| 1-0 | 0.0627 | 0.0662 | 0.0035 |
| 0-3 | 0.0582 | 0.0649 | 0.0067 |
| 1-3 | 0.0509 | 0.0522 | 0.0013 |
| 2-2 | 0.0479 | 0.0409 | 0.0070 |
| 2-1 | 0.0453 | 0.0442 | 0.0011 |
| 2-0 | 0.0263 | 0.0275 | 0.0012 |
| 2-3 | 0.0263 | 0.0214 | 0.0048 |
| 0-4 | 0.0263 | 0.0280 | 0.0017 |
| 1-4 | 0.0226 | 0.0219 | 0.0007 |
| 3-2 | 0.0146 | 0.0096 | 0.0049 |
| **Sum (top 15)** | **0.9260** | **0.9424** | — |
- High-score mass (total ≥9 goals): 1.47e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Brazil vs Japan
- CS outcomes: 27  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-0 | 0.1231 | 0.1240 | 0.0009 |
| 2-0 | 0.1067 | 0.1122 | 0.0055 |
| 1-1 | 0.1067 | 0.1128 | 0.0061 |
| 2-1 | 0.0941 | 0.0968 | 0.0026 |
| 0-0 | 0.0727 | 0.0829 | 0.0101 |
| 3-0 | 0.0616 | 0.0661 | 0.0046 |
| 0-1 | 0.0616 | 0.0637 | 0.0022 |
| 3-1 | 0.0533 | 0.0566 | 0.0033 |
| 1-2 | 0.0471 | 0.0480 | 0.0010 |
| 2-2 | 0.0445 | 0.0444 | 0.0000 |
| 0-2 | 0.0308 | 0.0292 | 0.0016 |
| 4-0 | 0.0286 | 0.0294 | 0.0008 |
| 3-2 | 0.0258 | 0.0253 | 0.0005 |
| 4-1 | 0.0258 | 0.0253 | 0.0005 |
| 1-3 | 0.0174 | 0.0142 | 0.0032 |
| **Sum (top 15)** | **0.8997** | **0.9310** | — |
- High-score mass (total ≥9 goals): 1.77e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Germany vs Paraguay
- CS outcomes: 27  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 2-0 | 0.1223 | 0.1299 | 0.0076 |
| 1-0 | 0.1136 | 0.1152 | 0.0016 |
| 2-1 | 0.0935 | 0.0972 | 0.0036 |
| 3-0 | 0.0883 | 0.0963 | 0.0080 |
| 1-1 | 0.0837 | 0.0884 | 0.0047 |
| 3-1 | 0.0723 | 0.0730 | 0.0007 |
| 0-0 | 0.0530 | 0.0608 | 0.0078 |
| 4-0 | 0.0468 | 0.0536 | 0.0068 |
| 4-1 | 0.0379 | 0.0397 | 0.0018 |
| 2-2 | 0.0379 | 0.0363 | 0.0015 |
| 0-1 | 0.0379 | 0.0397 | 0.0018 |
| 1-2 | 0.0346 | 0.0322 | 0.0023 |
| 3-2 | 0.0284 | 0.0272 | 0.0012 |
| 5-0 | 0.0256 | 0.0247 | 0.0010 |
| 5-1 | 0.0194 | 0.0176 | 0.0018 |
| **Sum (top 15)** | **0.8952** | **0.9317** | — |
- High-score mass (total ≥9 goals): 2.19e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Netherlands vs Morocco
- CS outcomes: 25  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-1 | 0.1342 | 0.1385 | 0.0043 |
| 1-0 | 0.1150 | 0.1167 | 0.0016 |
| 2-1 | 0.0895 | 0.0888 | 0.0007 |
| 0-0 | 0.0848 | 0.1050 | 0.0203 |
| 2-0 | 0.0805 | 0.0897 | 0.0092 |
| 0-1 | 0.0805 | 0.0838 | 0.0033 |
| 1-2 | 0.0671 | 0.0626 | 0.0045 |
| 2-2 | 0.0503 | 0.0478 | 0.0026 |
| 3-1 | 0.0424 | 0.0420 | 0.0004 |
| 3-0 | 0.0403 | 0.0428 | 0.0026 |
| 0-2 | 0.0403 | 0.0447 | 0.0044 |
| 3-2 | 0.0260 | 0.0213 | 0.0047 |
| 1-3 | 0.0260 | 0.0205 | 0.0054 |
| 2-3 | 0.0196 | 0.0143 | 0.0053 |
| 4-1 | 0.0158 | 0.0147 | 0.0010 |
| **Sum (top 15)** | **0.9122** | **0.9333** | — |
- High-score mass (total ≥9 goals): 1.45e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Côte d'Ivoire vs Norway
- CS outcomes: 27  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-1 | 0.1313 | 0.1284 | 0.0029 |
| 0-1 | 0.1050 | 0.1009 | 0.0042 |
| 1-2 | 0.0927 | 0.0944 | 0.0017 |
| 1-0 | 0.0716 | 0.0720 | 0.0004 |
| 0-2 | 0.0716 | 0.0816 | 0.0100 |
| 2-1 | 0.0657 | 0.0669 | 0.0013 |
| 0-0 | 0.0657 | 0.0786 | 0.0129 |
| 2-2 | 0.0606 | 0.0568 | 0.0038 |
| 1-3 | 0.0463 | 0.0496 | 0.0033 |
| 2-0 | 0.0394 | 0.0429 | 0.0035 |
| 0-3 | 0.0375 | 0.0444 | 0.0069 |
| 2-3 | 0.0281 | 0.0284 | 0.0003 |
| 3-1 | 0.0254 | 0.0253 | 0.0001 |
| 3-2 | 0.0254 | 0.0204 | 0.0050 |
| 1-4 | 0.0192 | 0.0198 | 0.0006 |
| **Sum (top 15)** | **0.8856** | **0.9105** | — |
- High-score mass (total ≥9 goals): 2.08e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### France vs Sweden
- CS outcomes: 28  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 2-0 | 0.1221 | 0.1276 | 0.0054 |
| 1-0 | 0.0992 | 0.1031 | 0.0038 |
| 3-0 | 0.0992 | 0.1060 | 0.0068 |
| 2-1 | 0.0934 | 0.0968 | 0.0033 |
| 3-1 | 0.0722 | 0.0778 | 0.0056 |
| 1-1 | 0.0722 | 0.0761 | 0.0039 |
| 4-0 | 0.0611 | 0.0659 | 0.0048 |
| 4-1 | 0.0441 | 0.0477 | 0.0036 |
| 0-0 | 0.0418 | 0.0468 | 0.0050 |
| 2-2 | 0.0345 | 0.0353 | 0.0008 |
| 5-0 | 0.0305 | 0.0324 | 0.0019 |
| 3-2 | 0.0284 | 0.0296 | 0.0013 |
| 0-1 | 0.0284 | 0.0316 | 0.0033 |
| 1-2 | 0.0256 | 0.0283 | 0.0027 |
| 5-1 | 0.0234 | 0.0220 | 0.0013 |
| **Sum (top 15)** | **0.8761** | **0.9270** | — |
- High-score mass (total ≥9 goals): 2.55e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### USA vs Bosnia & Herzegovina
- CS outcomes: 26  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 2-0 | 0.1351 | 0.1359 | 0.0007 |
| 1-0 | 0.1329 | 0.1277 | 0.0052 |
| 2-1 | 0.0938 | 0.0964 | 0.0026 |
| 3-0 | 0.0886 | 0.0959 | 0.0073 |
| 1-1 | 0.0886 | 0.0898 | 0.0012 |
| 0-0 | 0.0664 | 0.0680 | 0.0016 |
| 3-1 | 0.0613 | 0.0669 | 0.0055 |
| 4-0 | 0.0469 | 0.0518 | 0.0049 |
| 0-1 | 0.0399 | 0.0423 | 0.0025 |
| 2-2 | 0.0347 | 0.0340 | 0.0006 |
| 4-1 | 0.0307 | 0.0353 | 0.0047 |
| 1-2 | 0.0285 | 0.0313 | 0.0028 |
| 3-2 | 0.0235 | 0.0241 | 0.0007 |
| 5-0 | 0.0235 | 0.0226 | 0.0009 |
| 5-1 | 0.0156 | 0.0152 | 0.0004 |
| **Sum (top 15)** | **0.9100** | **0.9372** | — |
- High-score mass (total ≥9 goals): 2.00e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Australia vs Egypt
- CS outcomes: 23  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-1 | 0.1474 | 0.1461 | 0.0013 |
| 0-1 | 0.1247 | 0.1392 | 0.0144 |
| 1-0 | 0.1081 | 0.1182 | 0.0101 |
| 0-0 | 0.1013 | 0.1337 | 0.0324 |
| 1-2 | 0.0853 | 0.0783 | 0.0071 |
| 2-1 | 0.0737 | 0.0646 | 0.0091 |
| 0-2 | 0.0676 | 0.0810 | 0.0135 |
| 2-2 | 0.0507 | 0.0378 | 0.0128 |
| 2-0 | 0.0450 | 0.0558 | 0.0107 |
| 0-3 | 0.0290 | 0.0303 | 0.0014 |
| 1-3 | 0.0290 | 0.0261 | 0.0029 |
| 3-1 | 0.0225 | 0.0176 | 0.0049 |
| 2-3 | 0.0225 | 0.0116 | 0.0109 |
| 3-0 | 0.0176 | 0.0169 | 0.0007 |
| 3-2 | 0.0176 | 0.0091 | 0.0085 |
| **Sum (top 15)** | **0.9420** | **0.9662** | — |
- High-score mass (total ≥9 goals): 5.61e-06
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Argentina vs Cabo Verde
- CS outcomes: 28  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 2-0 | 0.1384 | 0.1548 | 0.0164 |
| 3-0 | 0.1213 | 0.1313 | 0.0099 |
| 1-0 | 0.1127 | 0.1308 | 0.0181 |
| 2-1 | 0.0789 | 0.0825 | 0.0036 |
| 4-0 | 0.0751 | 0.0853 | 0.0102 |
| 3-1 | 0.0657 | 0.0701 | 0.0043 |
| 1-1 | 0.0607 | 0.0593 | 0.0014 |
| 4-1 | 0.0438 | 0.0453 | 0.0015 |
| 5-0 | 0.0438 | 0.0463 | 0.0025 |
| 0-0 | 0.0415 | 0.0467 | 0.0052 |
| 5-1 | 0.0254 | 0.0220 | 0.0034 |
| 2-2 | 0.0254 | 0.0187 | 0.0067 |
| 3-2 | 0.0219 | 0.0184 | 0.0035 |
| 6-0 | 0.0219 | 0.0201 | 0.0018 |
| 0-1 | 0.0219 | 0.0250 | 0.0031 |
| **Sum (top 15)** | **0.8984** | **0.9563** | — |
- High-score mass (total ≥9 goals): 2.30e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS
