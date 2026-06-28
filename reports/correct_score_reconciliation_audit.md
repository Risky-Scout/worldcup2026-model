# Correct-Score Reconciliation Audit

**Generated**: 2026-06-28T20:15:51Z

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
- CS outcomes: 26  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 0-1 | 0.1341 | 0.1313 | 0.0028 |
| 1-1 | 0.1150 | 0.1179 | 0.0029 |
| 0-2 | 0.1150 | 0.1206 | 0.0056 |
| 1-2 | 0.0947 | 0.0955 | 0.0008 |
| 0-0 | 0.0766 | 0.0917 | 0.0151 |
| 0-3 | 0.0619 | 0.0689 | 0.0070 |
| 1-0 | 0.0575 | 0.0620 | 0.0045 |
| 1-3 | 0.0537 | 0.0551 | 0.0014 |
| 2-1 | 0.0447 | 0.0435 | 0.0012 |
| 2-2 | 0.0447 | 0.0405 | 0.0042 |
| 0-4 | 0.0287 | 0.0307 | 0.0020 |
| 2-3 | 0.0260 | 0.0224 | 0.0036 |
| 1-4 | 0.0260 | 0.0242 | 0.0018 |
| 2-0 | 0.0237 | 0.0256 | 0.0020 |
| 3-1 | 0.0132 | 0.0112 | 0.0020 |
| **Sum (top 15)** | **0.9153** | **0.9410** | — |
- High-score mass (total ≥9 goals): 1.55e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Brazil vs Japan
- CS outcomes: 27  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-0 | 0.1229 | 0.1186 | 0.0044 |
| 1-1 | 0.1141 | 0.1169 | 0.0028 |
| 2-0 | 0.0999 | 0.1073 | 0.0075 |
| 2-1 | 0.0940 | 0.0970 | 0.0030 |
| 0-0 | 0.0666 | 0.0805 | 0.0139 |
| 3-0 | 0.0615 | 0.0653 | 0.0039 |
| 0-1 | 0.0615 | 0.0622 | 0.0007 |
| 3-1 | 0.0571 | 0.0583 | 0.0013 |
| 2-2 | 0.0470 | 0.0468 | 0.0002 |
| 1-2 | 0.0470 | 0.0493 | 0.0023 |
| 3-2 | 0.0285 | 0.0268 | 0.0018 |
| 0-2 | 0.0285 | 0.0290 | 0.0005 |
| 4-0 | 0.0258 | 0.0288 | 0.0030 |
| 4-1 | 0.0258 | 0.0257 | 0.0001 |
| 1-3 | 0.0174 | 0.0150 | 0.0024 |
| **Sum (top 15)** | **0.8975** | **0.9275** | — |
- High-score mass (total ≥9 goals): 1.88e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Germany vs Paraguay
- CS outcomes: 27  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 2-0 | 0.1223 | 0.1309 | 0.0086 |
| 1-0 | 0.1136 | 0.1174 | 0.0038 |
| 2-1 | 0.0935 | 0.0971 | 0.0036 |
| 3-0 | 0.0883 | 0.0974 | 0.0090 |
| 1-1 | 0.0837 | 0.0865 | 0.0028 |
| 3-1 | 0.0723 | 0.0733 | 0.0010 |
| 0-0 | 0.0530 | 0.0591 | 0.0061 |
| 4-0 | 0.0468 | 0.0546 | 0.0078 |
| 4-1 | 0.0379 | 0.0401 | 0.0023 |
| 2-2 | 0.0379 | 0.0353 | 0.0025 |
| 0-1 | 0.0379 | 0.0393 | 0.0014 |
| 1-2 | 0.0346 | 0.0315 | 0.0031 |
| 3-2 | 0.0284 | 0.0271 | 0.0013 |
| 5-0 | 0.0256 | 0.0254 | 0.0003 |
| 5-1 | 0.0194 | 0.0179 | 0.0014 |
| **Sum (top 15)** | **0.8952** | **0.9329** | — |
- High-score mass (total ≥9 goals): 2.20e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Netherlands vs Morocco
- CS outcomes: 26  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-1 | 0.1384 | 0.1395 | 0.0012 |
| 1-0 | 0.1235 | 0.1146 | 0.0089 |
| 2-1 | 0.1003 | 0.0930 | 0.0073 |
| 0-0 | 0.0845 | 0.1020 | 0.0176 |
| 0-1 | 0.0802 | 0.0815 | 0.0012 |
| 2-0 | 0.0730 | 0.0843 | 0.0114 |
| 1-2 | 0.0669 | 0.0645 | 0.0024 |
| 2-2 | 0.0573 | 0.0507 | 0.0067 |
| 3-1 | 0.0382 | 0.0417 | 0.0035 |
| 3-0 | 0.0349 | 0.0411 | 0.0063 |
| 0-2 | 0.0349 | 0.0435 | 0.0086 |
| 3-2 | 0.0287 | 0.0226 | 0.0061 |
| 1-3 | 0.0196 | 0.0210 | 0.0014 |
| 2-3 | 0.0196 | 0.0155 | 0.0041 |
| 4-1 | 0.0143 | 0.0150 | 0.0007 |
| **Sum (top 15)** | **0.9141** | **0.9305** | — |
- High-score mass (total ≥9 goals): 1.57e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Côte d'Ivoire vs Norway
- CS outcomes: 27  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-1 | 0.1220 | 0.1244 | 0.0024 |
| 0-1 | 0.1058 | 0.0991 | 0.0066 |
| 1-2 | 0.0933 | 0.0946 | 0.0012 |
| 0-2 | 0.0793 | 0.0832 | 0.0039 |
| 1-0 | 0.0721 | 0.0708 | 0.0013 |
| 2-1 | 0.0661 | 0.0673 | 0.0012 |
| 0-0 | 0.0661 | 0.0780 | 0.0119 |
| 2-2 | 0.0567 | 0.0573 | 0.0007 |
| 1-3 | 0.0467 | 0.0502 | 0.0036 |
| 0-3 | 0.0417 | 0.0457 | 0.0040 |
| 2-0 | 0.0378 | 0.0417 | 0.0040 |
| 2-3 | 0.0283 | 0.0289 | 0.0006 |
| 3-1 | 0.0256 | 0.0255 | 0.0001 |
| 3-2 | 0.0220 | 0.0204 | 0.0016 |
| 1-4 | 0.0220 | 0.0207 | 0.0014 |
| **Sum (top 15)** | **0.8855** | **0.9079** | — |
- High-score mass (total ≥9 goals): 2.15e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### France vs Sweden
- CS outcomes: 29  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 2-0 | 0.1125 | 0.1103 | 0.0021 |
| 1-0 | 0.0984 | 0.0956 | 0.0028 |
| 2-1 | 0.0926 | 0.0909 | 0.0017 |
| 3-0 | 0.0926 | 0.0914 | 0.0012 |
| 3-1 | 0.0716 | 0.0716 | 0.0000 |
| 1-1 | 0.0716 | 0.0713 | 0.0003 |
| 4-0 | 0.0606 | 0.0603 | 0.0003 |
| 4-1 | 0.0437 | 0.0403 | 0.0034 |
| 0-0 | 0.0375 | 0.0371 | 0.0004 |
| 2-2 | 0.0375 | 0.0382 | 0.0007 |
| 3-2 | 0.0342 | 0.0308 | 0.0034 |
| 5-0 | 0.0342 | 0.0309 | 0.0033 |
| 1-2 | 0.0281 | 0.0281 | 0.0000 |
| 5-1 | 0.0254 | 0.0239 | 0.0015 |
| 0-1 | 0.0254 | 0.0255 | 0.0001 |
| **Sum (top 15)** | **0.8660** | **0.8462** | — |
- High-score mass (total ≥9 goals): 1.20e-04
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### USA vs Bosnia & Herzegovina
- CS outcomes: 26  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-0 | 0.1320 | 0.1305 | 0.0015 |
| 2-0 | 0.1320 | 0.1364 | 0.0044 |
| 2-1 | 0.0932 | 0.0956 | 0.0024 |
| 3-0 | 0.0880 | 0.0957 | 0.0077 |
| 1-1 | 0.0834 | 0.0884 | 0.0050 |
| 3-1 | 0.0609 | 0.0664 | 0.0055 |
| 0-0 | 0.0609 | 0.0669 | 0.0059 |
| 4-0 | 0.0528 | 0.0535 | 0.0007 |
| 0-1 | 0.0377 | 0.0424 | 0.0047 |
| 4-1 | 0.0344 | 0.0359 | 0.0015 |
| 2-2 | 0.0344 | 0.0335 | 0.0009 |
| 1-2 | 0.0305 | 0.0309 | 0.0005 |
| 3-2 | 0.0256 | 0.0241 | 0.0015 |
| 5-0 | 0.0233 | 0.0226 | 0.0007 |
| 5-1 | 0.0172 | 0.0153 | 0.0019 |
| **Sum (top 15)** | **0.9064** | **0.9381** | — |
- High-score mass (total ≥9 goals): 2.00e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Australia vs Egypt
- CS outcomes: 22  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-1 | 0.1462 | 0.1444 | 0.0018 |
| 0-1 | 0.1364 | 0.1424 | 0.0059 |
| 0-0 | 0.1170 | 0.1377 | 0.0207 |
| 1-0 | 0.1092 | 0.1170 | 0.0078 |
| 1-2 | 0.0780 | 0.0757 | 0.0023 |
| 2-1 | 0.0682 | 0.0632 | 0.0050 |
| 0-2 | 0.0682 | 0.0814 | 0.0132 |
| 2-0 | 0.0482 | 0.0569 | 0.0087 |
| 2-2 | 0.0455 | 0.0361 | 0.0094 |
| 0-3 | 0.0292 | 0.0305 | 0.0013 |
| 1-3 | 0.0292 | 0.0261 | 0.0031 |
| 3-1 | 0.0227 | 0.0177 | 0.0050 |
| 3-0 | 0.0178 | 0.0170 | 0.0008 |
| 2-3 | 0.0178 | 0.0112 | 0.0066 |
| 3-2 | 0.0161 | 0.0091 | 0.0070 |
| **Sum (top 15)** | **0.9497** | **0.9663** | — |
- High-score mass (total ≥9 goals): 5.52e-06
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Argentina vs Cabo Verde
- CS outcomes: 25  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 2-0 | 0.1581 | 0.1573 | 0.0008 |
| 3-0 | 0.1344 | 0.1364 | 0.0020 |
| 1-0 | 0.1152 | 0.1256 | 0.0104 |
| 4-0 | 0.0949 | 0.0930 | 0.0019 |
| 2-1 | 0.0672 | 0.0775 | 0.0103 |
| 3-1 | 0.0576 | 0.0676 | 0.0100 |
| 5-0 | 0.0504 | 0.0488 | 0.0016 |
| 1-1 | 0.0474 | 0.0543 | 0.0069 |
| 0-0 | 0.0448 | 0.0450 | 0.0002 |
| 4-1 | 0.0403 | 0.0453 | 0.0050 |
| 5-1 | 0.0260 | 0.0220 | 0.0040 |
| 6-0 | 0.0260 | 0.0214 | 0.0046 |
| 0-1 | 0.0224 | 0.0237 | 0.0013 |
| 2-2 | 0.0175 | 0.0193 | 0.0018 |
| 3-2 | 0.0144 | 0.0179 | 0.0035 |
| **Sum (top 15)** | **0.9167** | **0.9550** | — |
- High-score mass (total ≥9 goals): 2.40e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS
