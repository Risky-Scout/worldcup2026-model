# Correct-Score Reconciliation Audit

**Generated**: 2026-06-28T03:19:59Z

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
- CS outcomes: 25  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 0-1 | 0.1369 | 0.1362 | 0.0007 |
| 1-1 | 0.1243 | 0.1236 | 0.0007 |
| 0-2 | 0.1010 | 0.1152 | 0.0142 |
| 1-2 | 0.1010 | 0.0968 | 0.0042 |
| 0-0 | 0.0769 | 0.0950 | 0.0181 |
| 1-0 | 0.0621 | 0.0670 | 0.0049 |
| 0-3 | 0.0577 | 0.0647 | 0.0070 |
| 2-2 | 0.0505 | 0.0404 | 0.0101 |
| 1-3 | 0.0505 | 0.0519 | 0.0015 |
| 2-1 | 0.0449 | 0.0440 | 0.0009 |
| 2-0 | 0.0261 | 0.0280 | 0.0019 |
| 2-3 | 0.0261 | 0.0213 | 0.0047 |
| 0-4 | 0.0261 | 0.0277 | 0.0017 |
| 1-4 | 0.0238 | 0.0219 | 0.0019 |
| 3-2 | 0.0144 | 0.0095 | 0.0049 |
| **Sum (top 15)** | **0.9222** | **0.9432** | — |
- High-score mass (total ≥9 goals): 1.45e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Brazil vs Japan
- CS outcomes: 27  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-0 | 0.1231 | 0.1252 | 0.0021 |
| 2-0 | 0.1067 | 0.1121 | 0.0054 |
| 1-1 | 0.1067 | 0.1137 | 0.0071 |
| 2-1 | 0.0941 | 0.0962 | 0.0021 |
| 0-0 | 0.0727 | 0.0842 | 0.0114 |
| 3-0 | 0.0616 | 0.0650 | 0.0035 |
| 0-1 | 0.0616 | 0.0653 | 0.0038 |
| 3-1 | 0.0533 | 0.0557 | 0.0023 |
| 1-2 | 0.0471 | 0.0485 | 0.0014 |
| 2-2 | 0.0445 | 0.0443 | 0.0002 |
| 0-2 | 0.0308 | 0.0300 | 0.0007 |
| 4-0 | 0.0286 | 0.0285 | 0.0001 |
| 3-2 | 0.0258 | 0.0248 | 0.0010 |
| 4-1 | 0.0258 | 0.0245 | 0.0014 |
| 1-3 | 0.0174 | 0.0144 | 0.0030 |
| **Sum (top 15)** | **0.8997** | **0.9325** | — |
- High-score mass (total ≥9 goals): 1.73e-05
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
| 1-1 | 0.1342 | 0.1386 | 0.0044 |
| 1-0 | 0.1150 | 0.1165 | 0.0015 |
| 2-1 | 0.0895 | 0.0888 | 0.0007 |
| 0-0 | 0.0848 | 0.1051 | 0.0203 |
| 2-0 | 0.0805 | 0.0896 | 0.0091 |
| 0-1 | 0.0805 | 0.0838 | 0.0033 |
| 1-2 | 0.0671 | 0.0627 | 0.0044 |
| 2-2 | 0.0503 | 0.0478 | 0.0025 |
| 3-1 | 0.0424 | 0.0419 | 0.0004 |
| 3-0 | 0.0403 | 0.0427 | 0.0025 |
| 0-2 | 0.0403 | 0.0447 | 0.0045 |
| 3-2 | 0.0260 | 0.0213 | 0.0047 |
| 1-3 | 0.0260 | 0.0206 | 0.0054 |
| 2-3 | 0.0196 | 0.0143 | 0.0053 |
| 4-1 | 0.0158 | 0.0147 | 0.0011 |
| **Sum (top 15)** | **0.9122** | **0.9332** | — |
- High-score mass (total ≥9 goals): 1.45e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Côte d'Ivoire vs Norway
- CS outcomes: 27  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-1 | 0.1313 | 0.1278 | 0.0035 |
| 0-1 | 0.1050 | 0.0986 | 0.0065 |
| 1-2 | 0.0927 | 0.0948 | 0.0021 |
| 1-0 | 0.0716 | 0.0703 | 0.0013 |
| 0-2 | 0.0716 | 0.0808 | 0.0091 |
| 2-1 | 0.0657 | 0.0673 | 0.0016 |
| 0-0 | 0.0657 | 0.0774 | 0.0117 |
| 2-2 | 0.0606 | 0.0577 | 0.0029 |
| 1-3 | 0.0463 | 0.0503 | 0.0040 |
| 2-0 | 0.0394 | 0.0423 | 0.0029 |
| 0-3 | 0.0375 | 0.0447 | 0.0071 |
| 2-3 | 0.0281 | 0.0292 | 0.0010 |
| 3-1 | 0.0254 | 0.0257 | 0.0003 |
| 3-2 | 0.0254 | 0.0210 | 0.0044 |
| 1-4 | 0.0192 | 0.0204 | 0.0012 |
| **Sum (top 15)** | **0.8856** | **0.9079** | — |
- High-score mass (total ≥9 goals): 2.16e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### France vs Sweden
- CS outcomes: 28  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 2-0 | 0.1221 | 0.1277 | 0.0056 |
| 1-0 | 0.0992 | 0.1057 | 0.0065 |
| 3-0 | 0.0992 | 0.1047 | 0.0054 |
| 2-1 | 0.0934 | 0.0967 | 0.0033 |
| 3-1 | 0.0722 | 0.0771 | 0.0049 |
| 1-1 | 0.0722 | 0.0765 | 0.0043 |
| 4-0 | 0.0611 | 0.0643 | 0.0033 |
| 4-1 | 0.0441 | 0.0469 | 0.0028 |
| 0-0 | 0.0418 | 0.0468 | 0.0050 |
| 2-2 | 0.0345 | 0.0355 | 0.0010 |
| 5-0 | 0.0305 | 0.0312 | 0.0007 |
| 3-2 | 0.0284 | 0.0296 | 0.0012 |
| 0-1 | 0.0284 | 0.0330 | 0.0046 |
| 1-2 | 0.0256 | 0.0290 | 0.0034 |
| 5-1 | 0.0234 | 0.0220 | 0.0014 |
| **Sum (top 15)** | **0.8761** | **0.9267** | — |
- High-score mass (total ≥9 goals): 2.51e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### USA vs Bosnia & Herzegovina
- CS outcomes: 26  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 2-0 | 0.1351 | 0.1364 | 0.0013 |
| 1-0 | 0.1329 | 0.1288 | 0.0041 |
| 2-1 | 0.0938 | 0.0964 | 0.0026 |
| 3-0 | 0.0886 | 0.0963 | 0.0077 |
| 1-1 | 0.0886 | 0.0890 | 0.0004 |
| 0-0 | 0.0664 | 0.0673 | 0.0009 |
| 3-1 | 0.0613 | 0.0670 | 0.0056 |
| 4-0 | 0.0469 | 0.0521 | 0.0052 |
| 0-1 | 0.0399 | 0.0422 | 0.0024 |
| 2-2 | 0.0347 | 0.0336 | 0.0010 |
| 4-1 | 0.0307 | 0.0355 | 0.0048 |
| 1-2 | 0.0285 | 0.0309 | 0.0025 |
| 3-2 | 0.0235 | 0.0241 | 0.0006 |
| 5-0 | 0.0235 | 0.0228 | 0.0006 |
| 5-1 | 0.0156 | 0.0153 | 0.0003 |
| **Sum (top 15)** | **0.9100** | **0.9378** | — |
- High-score mass (total ≥9 goals): 2.02e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Australia vs Egypt
- CS outcomes: 23  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-1 | 0.1474 | 0.1467 | 0.0007 |
| 0-1 | 0.1247 | 0.1388 | 0.0141 |
| 1-0 | 0.1081 | 0.1184 | 0.0103 |
| 0-0 | 0.1013 | 0.1342 | 0.0329 |
| 1-2 | 0.0853 | 0.0780 | 0.0073 |
| 2-1 | 0.0737 | 0.0647 | 0.0089 |
| 0-2 | 0.0676 | 0.0808 | 0.0133 |
| 2-2 | 0.0507 | 0.0378 | 0.0128 |
| 2-0 | 0.0450 | 0.0562 | 0.0112 |
| 0-3 | 0.0290 | 0.0301 | 0.0011 |
| 1-3 | 0.0290 | 0.0258 | 0.0031 |
| 3-1 | 0.0225 | 0.0176 | 0.0049 |
| 2-3 | 0.0225 | 0.0114 | 0.0111 |
| 3-0 | 0.0176 | 0.0170 | 0.0006 |
| 3-2 | 0.0176 | 0.0091 | 0.0085 |
| **Sum (top 15)** | **0.9420** | **0.9667** | — |
- High-score mass (total ≥9 goals): 5.49e-06
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Argentina vs Cabo Verde
- CS outcomes: 28  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 2-0 | 0.1384 | 0.1549 | 0.0165 |
| 3-0 | 0.1213 | 0.1310 | 0.0097 |
| 1-0 | 0.1127 | 0.1334 | 0.0207 |
| 2-1 | 0.0789 | 0.0824 | 0.0036 |
| 4-0 | 0.0751 | 0.0852 | 0.0101 |
| 3-1 | 0.0657 | 0.0702 | 0.0045 |
| 1-1 | 0.0607 | 0.0579 | 0.0027 |
| 4-1 | 0.0438 | 0.0455 | 0.0017 |
| 5-0 | 0.0438 | 0.0463 | 0.0025 |
| 0-0 | 0.0415 | 0.0450 | 0.0035 |
| 5-1 | 0.0254 | 0.0220 | 0.0034 |
| 2-2 | 0.0254 | 0.0185 | 0.0069 |
| 3-2 | 0.0219 | 0.0186 | 0.0034 |
| 6-0 | 0.0219 | 0.0202 | 0.0017 |
| 0-1 | 0.0219 | 0.0251 | 0.0032 |
| **Sum (top 15)** | **0.8984** | **0.9561** | — |
- High-score mass (total ≥9 goals): 2.31e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS
