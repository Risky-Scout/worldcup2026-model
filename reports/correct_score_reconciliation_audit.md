# Correct-Score Reconciliation Audit

**Generated**: 2026-07-02T01:15:14Z

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
| Total 2026 matches predicted | 11 |
| Matches with any CS data | 11 |
| Matches with 1 CS vendor | 11 |
| Matches with 2+ CS vendors | 0 |

## Per-match correct-score audit

### USA vs Bosnia & Herzegovina
- CS outcomes: 28  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 2-0 | 0.1125 | 0.1234 | 0.0108 |
| 1-0 | 0.1050 | 0.1057 | 0.0007 |
| 2-1 | 0.0985 | 0.1000 | 0.0016 |
| 3-0 | 0.0829 | 0.0952 | 0.0122 |
| 1-1 | 0.0829 | 0.0860 | 0.0031 |
| 3-1 | 0.0716 | 0.0757 | 0.0040 |
| 4-0 | 0.0492 | 0.0566 | 0.0074 |
| 0-0 | 0.0463 | 0.0542 | 0.0078 |
| 4-1 | 0.0415 | 0.0438 | 0.0023 |
| 2-2 | 0.0415 | 0.0385 | 0.0029 |
| 3-2 | 0.0343 | 0.0307 | 0.0035 |
| 0-1 | 0.0343 | 0.0363 | 0.0021 |
| 1-2 | 0.0343 | 0.0326 | 0.0016 |
| 5-0 | 0.0254 | 0.0268 | 0.0014 |
| 5-1 | 0.0219 | 0.0203 | 0.0016 |
| **Sum (top 15)** | **0.8821** | **0.9258** | — |
- High-score mass (total ≥9 goals): 2.37e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Spain vs Austria
- CS outcomes: 26  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 2-0 | 0.1334 | 0.1417 | 0.0083 |
| 1-0 | 0.1232 | 0.1286 | 0.0054 |
| 2-1 | 0.0942 | 0.0950 | 0.0008 |
| 3-0 | 0.0942 | 0.1024 | 0.0082 |
| 1-1 | 0.0801 | 0.0844 | 0.0044 |
| 3-1 | 0.0667 | 0.0688 | 0.0021 |
| 0-0 | 0.0572 | 0.0646 | 0.0074 |
| 4-0 | 0.0534 | 0.0577 | 0.0044 |
| 4-1 | 0.0381 | 0.0380 | 0.0001 |
| 2-2 | 0.0348 | 0.0305 | 0.0043 |
| 0-1 | 0.0348 | 0.0392 | 0.0044 |
| 1-2 | 0.0286 | 0.0271 | 0.0015 |
| 3-2 | 0.0258 | 0.0231 | 0.0027 |
| 5-0 | 0.0258 | 0.0258 | 0.0000 |
| 5-1 | 0.0174 | 0.0164 | 0.0010 |
| **Sum (top 15)** | **0.9076** | **0.9434** | — |
- High-score mass (total ≥9 goals): 2.03e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Portugal vs Croatia
- CS outcomes: 28  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-1 | 0.1221 | 0.1238 | 0.0017 |
| 1-0 | 0.1134 | 0.1140 | 0.0006 |
| 2-1 | 0.0992 | 0.0988 | 0.0003 |
| 2-0 | 0.0934 | 0.1052 | 0.0118 |
| 0-0 | 0.0661 | 0.0843 | 0.0182 |
| 0-1 | 0.0610 | 0.0637 | 0.0027 |
| 2-2 | 0.0567 | 0.0487 | 0.0080 |
| 3-1 | 0.0529 | 0.0558 | 0.0029 |
| 3-0 | 0.0496 | 0.0600 | 0.0104 |
| 1-2 | 0.0496 | 0.0507 | 0.0011 |
| 3-2 | 0.0345 | 0.0272 | 0.0073 |
| 0-2 | 0.0283 | 0.0308 | 0.0025 |
| 4-1 | 0.0233 | 0.0241 | 0.0008 |
| 4-0 | 0.0220 | 0.0266 | 0.0045 |
| 2-3 | 0.0194 | 0.0134 | 0.0060 |
| **Sum (top 15)** | **0.8915** | **0.9270** | — |
- High-score mass (total ≥9 goals): 1.80e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Switzerland vs Algeria
- CS outcomes: 26  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-1 | 0.1331 | 0.1358 | 0.0027 |
| 1-0 | 0.1229 | 0.1169 | 0.0060 |
| 2-1 | 0.0940 | 0.0923 | 0.0017 |
| 2-0 | 0.0799 | 0.0908 | 0.0109 |
| 0-0 | 0.0799 | 0.0990 | 0.0191 |
| 0-1 | 0.0726 | 0.0769 | 0.0042 |
| 1-2 | 0.0615 | 0.0604 | 0.0010 |
| 2-2 | 0.0571 | 0.0503 | 0.0068 |
| 3-1 | 0.0420 | 0.0448 | 0.0027 |
| 3-0 | 0.0399 | 0.0459 | 0.0059 |
| 0-2 | 0.0380 | 0.0414 | 0.0034 |
| 3-2 | 0.0285 | 0.0232 | 0.0054 |
| 1-3 | 0.0222 | 0.0197 | 0.0025 |
| 2-3 | 0.0195 | 0.0147 | 0.0047 |
| 4-1 | 0.0174 | 0.0169 | 0.0005 |
| **Sum (top 15)** | **0.9085** | **0.9290** | — |
- High-score mass (total ≥9 goals): 1.60e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Australia vs Egypt
- CS outcomes: 22  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-1 | 0.1454 | 0.1475 | 0.0021 |
| 0-1 | 0.1380 | 0.1410 | 0.0030 |
| 0-0 | 0.1253 | 0.1435 | 0.0183 |
| 1-0 | 0.1086 | 0.1150 | 0.0065 |
| 1-2 | 0.0814 | 0.0764 | 0.0050 |
| 2-1 | 0.0678 | 0.0629 | 0.0049 |
| 0-2 | 0.0678 | 0.0829 | 0.0150 |
| 2-2 | 0.0479 | 0.0359 | 0.0120 |
| 2-0 | 0.0452 | 0.0573 | 0.0120 |
| 1-3 | 0.0291 | 0.0250 | 0.0040 |
| 0-3 | 0.0263 | 0.0298 | 0.0036 |
| 3-1 | 0.0226 | 0.0169 | 0.0057 |
| 3-0 | 0.0177 | 0.0168 | 0.0009 |
| 2-3 | 0.0177 | 0.0102 | 0.0075 |
| 3-2 | 0.0145 | 0.0082 | 0.0063 |
| **Sum (top 15)** | **0.9553** | **0.9694** | — |
- High-score mass (total ≥9 goals): 4.45e-06
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Argentina vs Cabo Verde
- CS outcomes: 24  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 2-0 | 0.1552 | 0.1603 | 0.0052 |
| 3-0 | 0.1345 | 0.1346 | 0.0001 |
| 1-0 | 0.1241 | 0.1360 | 0.0118 |
| 4-0 | 0.0849 | 0.0860 | 0.0010 |
| 2-1 | 0.0734 | 0.0789 | 0.0056 |
| 3-1 | 0.0621 | 0.0668 | 0.0048 |
| 1-1 | 0.0538 | 0.0578 | 0.0040 |
| 5-0 | 0.0475 | 0.0449 | 0.0025 |
| 0-0 | 0.0475 | 0.0500 | 0.0025 |
| 4-1 | 0.0384 | 0.0414 | 0.0030 |
| 5-1 | 0.0237 | 0.0216 | 0.0021 |
| 6-0 | 0.0237 | 0.0186 | 0.0051 |
| 0-1 | 0.0224 | 0.0260 | 0.0036 |
| 2-2 | 0.0197 | 0.0183 | 0.0014 |
| 3-2 | 0.0144 | 0.0165 | 0.0021 |
| **Sum (top 15)** | **0.9253** | **0.9579** | — |
- High-score mass (total ≥9 goals): 2.22e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Colombia vs Ghana
- CS outcomes: 23  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-0 | 0.1597 | 0.1558 | 0.0039 |
| 2-0 | 0.1331 | 0.1378 | 0.0047 |
| 1-1 | 0.1065 | 0.1075 | 0.0010 |
| 2-1 | 0.0939 | 0.0924 | 0.0015 |
| 0-0 | 0.0887 | 0.0984 | 0.0097 |
| 3-0 | 0.0726 | 0.0795 | 0.0069 |
| 0-1 | 0.0570 | 0.0595 | 0.0025 |
| 3-1 | 0.0499 | 0.0526 | 0.0027 |
| 4-0 | 0.0347 | 0.0362 | 0.0015 |
| 1-2 | 0.0347 | 0.0333 | 0.0014 |
| 2-2 | 0.0307 | 0.0300 | 0.0007 |
| 4-1 | 0.0258 | 0.0236 | 0.0021 |
| 3-2 | 0.0222 | 0.0178 | 0.0043 |
| 0-2 | 0.0195 | 0.0196 | 0.0001 |
| 5-0 | 0.0131 | 0.0127 | 0.0004 |
| **Sum (top 15)** | **0.9422** | **0.9569** | — |
- High-score mass (total ≥9 goals): 1.41e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Canada vs Morocco
- CS outcomes: 25  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 0-1 | 0.1347 | 0.1347 | 0.0000 |
| 1-1 | 0.1244 | 0.1266 | 0.0023 |
| 0-2 | 0.1011 | 0.1111 | 0.0101 |
| 1-2 | 0.0951 | 0.0936 | 0.0015 |
| 0-0 | 0.0898 | 0.1044 | 0.0146 |
| 1-0 | 0.0735 | 0.0740 | 0.0005 |
| 0-3 | 0.0539 | 0.0592 | 0.0053 |
| 2-1 | 0.0476 | 0.0469 | 0.0006 |
| 1-3 | 0.0476 | 0.0486 | 0.0010 |
| 2-2 | 0.0425 | 0.0399 | 0.0026 |
| 2-0 | 0.0311 | 0.0314 | 0.0004 |
| 2-3 | 0.0238 | 0.0203 | 0.0035 |
| 0-4 | 0.0238 | 0.0239 | 0.0002 |
| 1-4 | 0.0225 | 0.0195 | 0.0030 |
| 3-1 | 0.0159 | 0.0127 | 0.0032 |
| **Sum (top 15)** | **0.9271** | **0.9469** | — |
- High-score mass (total ≥9 goals): 1.37e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Paraguay vs France
- CS outcomes: 28  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 0-2 | 0.1419 | 0.1491 | 0.0072 |
| 0-3 | 0.1222 | 0.1303 | 0.0081 |
| 0-1 | 0.1135 | 0.1171 | 0.0036 |
| 1-2 | 0.0757 | 0.0834 | 0.0078 |
| 0-4 | 0.0757 | 0.0848 | 0.0091 |
| 1-3 | 0.0662 | 0.0724 | 0.0062 |
| 1-1 | 0.0611 | 0.0627 | 0.0016 |
| 0-0 | 0.0441 | 0.0481 | 0.0040 |
| 1-4 | 0.0441 | 0.0472 | 0.0031 |
| 0-5 | 0.0418 | 0.0454 | 0.0036 |
| 1-5 | 0.0256 | 0.0220 | 0.0036 |
| 2-2 | 0.0234 | 0.0220 | 0.0014 |
| 1-0 | 0.0221 | 0.0245 | 0.0024 |
| 2-3 | 0.0221 | 0.0205 | 0.0016 |
| 0-6 | 0.0221 | 0.0200 | 0.0020 |
| **Sum (top 15)** | **0.9015** | **0.9496** | — |
- High-score mass (total ≥9 goals): 2.40e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Brazil vs Norway
- CS outcomes: 27  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-1 | 0.1149 | 0.1203 | 0.0054 |
| 1-0 | 0.1072 | 0.0992 | 0.0081 |
| 2-1 | 0.0946 | 0.0972 | 0.0026 |
| 2-0 | 0.0847 | 0.0897 | 0.0050 |
| 0-0 | 0.0670 | 0.0775 | 0.0105 |
| 0-1 | 0.0670 | 0.0636 | 0.0034 |
| 1-2 | 0.0619 | 0.0617 | 0.0001 |
| 2-2 | 0.0536 | 0.0560 | 0.0024 |
| 3-1 | 0.0503 | 0.0551 | 0.0048 |
| 3-0 | 0.0473 | 0.0529 | 0.0056 |
| 0-2 | 0.0350 | 0.0359 | 0.0010 |
| 3-2 | 0.0309 | 0.0306 | 0.0003 |
| 1-3 | 0.0237 | 0.0221 | 0.0015 |
| 4-0 | 0.0223 | 0.0231 | 0.0008 |
| 4-1 | 0.0223 | 0.0239 | 0.0016 |
| **Sum (top 15)** | **0.8828** | **0.9090** | — |
- High-score mass (total ≥9 goals): 2.18e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Mexico vs England
- CS outcomes: 25  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-1 | 0.1339 | 0.1386 | 0.0048 |
| 0-1 | 0.1236 | 0.1269 | 0.0033 |
| 0-0 | 0.0945 | 0.1147 | 0.0202 |
| 1-0 | 0.0892 | 0.1010 | 0.0117 |
| 1-2 | 0.0892 | 0.0825 | 0.0068 |
| 0-2 | 0.0765 | 0.0836 | 0.0071 |
| 2-1 | 0.0669 | 0.0654 | 0.0015 |
| 2-2 | 0.0502 | 0.0439 | 0.0063 |
| 2-0 | 0.0423 | 0.0533 | 0.0111 |
| 0-3 | 0.0382 | 0.0348 | 0.0034 |
| 1-3 | 0.0382 | 0.0339 | 0.0043 |
| 2-3 | 0.0236 | 0.0170 | 0.0066 |
| 3-1 | 0.0223 | 0.0214 | 0.0009 |
| 3-2 | 0.0175 | 0.0135 | 0.0039 |
| 3-0 | 0.0157 | 0.0172 | 0.0015 |
| **Sum (top 15)** | **0.9219** | **0.9478** | — |
- High-score mass (total ≥9 goals): 1.16e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS
