# Correct-Score Reconciliation Audit

**Generated**: 2026-06-28T10:22:35Z

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
| 0-1 | 0.1341 | 0.1311 | 0.0030 |
| 1-1 | 0.1150 | 0.1178 | 0.0029 |
| 0-2 | 0.1150 | 0.1202 | 0.0052 |
| 1-2 | 0.0947 | 0.0954 | 0.0008 |
| 0-0 | 0.0766 | 0.0915 | 0.0148 |
| 0-3 | 0.0619 | 0.0686 | 0.0067 |
| 1-0 | 0.0575 | 0.0621 | 0.0047 |
| 1-3 | 0.0537 | 0.0550 | 0.0013 |
| 2-1 | 0.0447 | 0.0438 | 0.0009 |
| 2-2 | 0.0447 | 0.0407 | 0.0040 |
| 0-4 | 0.0287 | 0.0305 | 0.0018 |
| 2-3 | 0.0260 | 0.0225 | 0.0035 |
| 1-4 | 0.0260 | 0.0242 | 0.0018 |
| 2-0 | 0.0237 | 0.0258 | 0.0021 |
| 3-1 | 0.0132 | 0.0113 | 0.0019 |
| **Sum (top 15)** | **0.9153** | **0.9406** | — |
- High-score mass (total ≥9 goals): 1.55e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Brazil vs Japan
- CS outcomes: 27  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-0 | 0.1229 | 0.1210 | 0.0019 |
| 1-1 | 0.1141 | 0.1165 | 0.0023 |
| 2-0 | 0.0999 | 0.1085 | 0.0086 |
| 2-1 | 0.0940 | 0.0970 | 0.0030 |
| 0-0 | 0.0666 | 0.0804 | 0.0138 |
| 3-0 | 0.0615 | 0.0658 | 0.0044 |
| 0-1 | 0.0615 | 0.0628 | 0.0014 |
| 3-1 | 0.0571 | 0.0581 | 0.0010 |
| 2-2 | 0.0470 | 0.0457 | 0.0013 |
| 1-2 | 0.0470 | 0.0486 | 0.0016 |
| 3-2 | 0.0285 | 0.0263 | 0.0022 |
| 0-2 | 0.0285 | 0.0290 | 0.0004 |
| 4-0 | 0.0258 | 0.0290 | 0.0032 |
| 4-1 | 0.0258 | 0.0256 | 0.0002 |
| 1-3 | 0.0174 | 0.0146 | 0.0028 |
| **Sum (top 15)** | **0.8975** | **0.9290** | — |
- High-score mass (total ≥9 goals): 1.84e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Germany vs Paraguay
- CS outcomes: 27  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 2-0 | 0.1223 | 0.1312 | 0.0089 |
| 1-0 | 0.1136 | 0.1187 | 0.0051 |
| 2-1 | 0.0935 | 0.0970 | 0.0034 |
| 3-0 | 0.0883 | 0.0965 | 0.0082 |
| 1-1 | 0.0837 | 0.0874 | 0.0037 |
| 3-1 | 0.0723 | 0.0727 | 0.0004 |
| 0-0 | 0.0530 | 0.0601 | 0.0071 |
| 4-0 | 0.0468 | 0.0536 | 0.0068 |
| 4-1 | 0.0379 | 0.0394 | 0.0015 |
| 2-2 | 0.0379 | 0.0354 | 0.0025 |
| 0-1 | 0.0379 | 0.0403 | 0.0024 |
| 1-2 | 0.0346 | 0.0318 | 0.0028 |
| 3-2 | 0.0284 | 0.0268 | 0.0016 |
| 5-0 | 0.0256 | 0.0246 | 0.0010 |
| 5-1 | 0.0194 | 0.0174 | 0.0020 |
| **Sum (top 15)** | **0.8952** | **0.9330** | — |
- High-score mass (total ≥9 goals): 2.17e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Netherlands vs Morocco
- CS outcomes: 26  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-1 | 0.1384 | 0.1402 | 0.0018 |
| 1-0 | 0.1235 | 0.1156 | 0.0079 |
| 2-1 | 0.1003 | 0.0925 | 0.0078 |
| 0-0 | 0.0845 | 0.1036 | 0.0191 |
| 0-1 | 0.0802 | 0.0822 | 0.0020 |
| 2-0 | 0.0730 | 0.0849 | 0.0120 |
| 1-2 | 0.0669 | 0.0640 | 0.0029 |
| 2-2 | 0.0573 | 0.0504 | 0.0069 |
| 3-1 | 0.0382 | 0.0411 | 0.0029 |
| 3-0 | 0.0349 | 0.0409 | 0.0060 |
| 0-2 | 0.0349 | 0.0437 | 0.0088 |
| 3-2 | 0.0287 | 0.0221 | 0.0066 |
| 1-3 | 0.0196 | 0.0206 | 0.0010 |
| 2-3 | 0.0196 | 0.0151 | 0.0044 |
| 4-1 | 0.0143 | 0.0147 | 0.0004 |
| **Sum (top 15)** | **0.9141** | **0.9316** | — |
- High-score mass (total ≥9 goals): 1.52e-05
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
| 2-0 | 0.1581 | 0.1591 | 0.0010 |
| 3-0 | 0.1344 | 0.1369 | 0.0025 |
| 1-0 | 0.1152 | 0.1294 | 0.0142 |
| 4-0 | 0.0949 | 0.0934 | 0.0015 |
| 2-1 | 0.0672 | 0.0769 | 0.0097 |
| 3-1 | 0.0576 | 0.0670 | 0.0094 |
| 5-0 | 0.0504 | 0.0491 | 0.0013 |
| 1-1 | 0.0474 | 0.0530 | 0.0056 |
| 0-0 | 0.0448 | 0.0443 | 0.0005 |
| 4-1 | 0.0403 | 0.0449 | 0.0046 |
| 5-1 | 0.0260 | 0.0220 | 0.0040 |
| 6-0 | 0.0260 | 0.0216 | 0.0045 |
| 0-1 | 0.0224 | 0.0237 | 0.0013 |
| 2-2 | 0.0175 | 0.0183 | 0.0008 |
| 3-2 | 0.0144 | 0.0174 | 0.0030 |
| **Sum (top 15)** | **0.9167** | **0.9569** | — |
- High-score mass (total ≥9 goals): 2.38e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS
