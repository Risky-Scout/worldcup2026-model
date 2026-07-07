# Correct-Score Reconciliation Audit

**Generated**: 2026-07-07T10:47:19Z

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
| Total 2026 matches predicted | 5 |
| Matches with any CS data | 5 |
| Matches with 1 CS vendor | 5 |
| Matches with 2+ CS vendors | 0 |

## Per-match correct-score audit

### Argentina vs Egypt
- CS outcomes: 24  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-0 | 0.1424 | 0.1455 | 0.0031 |
| 2-0 | 0.1352 | 0.1484 | 0.0132 |
| 2-1 | 0.0955 | 0.0933 | 0.0021 |
| 3-0 | 0.0902 | 0.1016 | 0.0114 |
| 1-1 | 0.0902 | 0.0886 | 0.0016 |
| 0-0 | 0.0676 | 0.0754 | 0.0078 |
| 3-1 | 0.0624 | 0.0635 | 0.0011 |
| 4-0 | 0.0477 | 0.0548 | 0.0071 |
| 0-1 | 0.0386 | 0.0419 | 0.0033 |
| 4-1 | 0.0353 | 0.0334 | 0.0018 |
| 2-2 | 0.0353 | 0.0263 | 0.0090 |
| 1-2 | 0.0262 | 0.0242 | 0.0020 |
| 3-2 | 0.0239 | 0.0191 | 0.0048 |
| 5-0 | 0.0225 | 0.0236 | 0.0011 |
| 5-1 | 0.0145 | 0.0135 | 0.0010 |
| **Sum (top 15)** | **0.9275** | **0.9532** | — |
- High-score mass (total ≥9 goals): 1.76e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Switzerland vs Colombia
- CS outcomes: 26  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-1 | 0.1353 | 0.1400 | 0.0047 |
| 0-1 | 0.1228 | 0.1180 | 0.0049 |
| 0-0 | 0.0939 | 0.1112 | 0.0173 |
| 1-2 | 0.0887 | 0.0861 | 0.0026 |
| 1-0 | 0.0840 | 0.0885 | 0.0045 |
| 0-2 | 0.0760 | 0.0836 | 0.0076 |
| 2-1 | 0.0665 | 0.0652 | 0.0013 |
| 2-2 | 0.0532 | 0.0484 | 0.0048 |
| 2-0 | 0.0443 | 0.0492 | 0.0049 |
| 1-3 | 0.0380 | 0.0380 | 0.0000 |
| 0-3 | 0.0347 | 0.0377 | 0.0030 |
| 2-3 | 0.0258 | 0.0200 | 0.0058 |
| 3-1 | 0.0222 | 0.0217 | 0.0005 |
| 3-2 | 0.0195 | 0.0149 | 0.0046 |
| 3-0 | 0.0143 | 0.0162 | 0.0019 |
| **Sum (top 15)** | **0.9193** | **0.9387** | — |
- High-score mass (total ≥9 goals): 1.37e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### France vs Morocco
- CS outcomes: 27  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-0 | 0.1242 | 0.1247 | 0.0004 |
| 2-0 | 0.1077 | 0.1190 | 0.0114 |
| 1-1 | 0.1077 | 0.1129 | 0.0052 |
| 2-1 | 0.1009 | 0.0991 | 0.0018 |
| 3-0 | 0.0673 | 0.0739 | 0.0066 |
| 0-0 | 0.0673 | 0.0834 | 0.0161 |
| 3-1 | 0.0577 | 0.0588 | 0.0011 |
| 0-1 | 0.0505 | 0.0571 | 0.0066 |
| 2-2 | 0.0475 | 0.0419 | 0.0056 |
| 1-2 | 0.0425 | 0.0423 | 0.0002 |
| 4-0 | 0.0351 | 0.0348 | 0.0003 |
| 3-2 | 0.0288 | 0.0247 | 0.0042 |
| 4-1 | 0.0288 | 0.0271 | 0.0017 |
| 0-2 | 0.0224 | 0.0245 | 0.0021 |
| 4-2 | 0.0132 | 0.0112 | 0.0020 |
| **Sum (top 15)** | **0.9017** | **0.9354** | — |
- High-score mass (total ≥9 goals): 1.74e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Spain vs Belgium
- CS outcomes: 28  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-0 | 0.1053 | 0.1035 | 0.0018 |
| 1-1 | 0.1053 | 0.1101 | 0.0049 |
| 2-0 | 0.0987 | 0.1077 | 0.0090 |
| 2-1 | 0.0929 | 0.0993 | 0.0064 |
| 3-0 | 0.0607 | 0.0708 | 0.0101 |
| 3-1 | 0.0607 | 0.0652 | 0.0045 |
| 0-0 | 0.0607 | 0.0717 | 0.0110 |
| 0-1 | 0.0526 | 0.0519 | 0.0008 |
| 2-2 | 0.0464 | 0.0483 | 0.0019 |
| 1-2 | 0.0464 | 0.0472 | 0.0008 |
| 3-2 | 0.0343 | 0.0315 | 0.0028 |
| 4-0 | 0.0304 | 0.0353 | 0.0049 |
| 4-1 | 0.0304 | 0.0320 | 0.0016 |
| 0-2 | 0.0282 | 0.0254 | 0.0028 |
| 1-3 | 0.0193 | 0.0147 | 0.0046 |
| **Sum (top 15)** | **0.8723** | **0.9145** | — |
- High-score mass (total ≥9 goals): 2.22e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Norway vs England
- CS outcomes: 30  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-1 | 0.1194 | 0.1199 | 0.0004 |
| 0-1 | 0.0970 | 0.0898 | 0.0072 |
| 1-2 | 0.0970 | 0.0988 | 0.0018 |
| 0-2 | 0.0776 | 0.0849 | 0.0073 |
| 2-1 | 0.0597 | 0.0633 | 0.0036 |
| 2-2 | 0.0597 | 0.0596 | 0.0001 |
| 1-0 | 0.0554 | 0.0580 | 0.0026 |
| 0-0 | 0.0554 | 0.0682 | 0.0128 |
| 1-3 | 0.0518 | 0.0574 | 0.0057 |
| 0-3 | 0.0457 | 0.0521 | 0.0064 |
| 2-3 | 0.0370 | 0.0345 | 0.0024 |
| 2-0 | 0.0299 | 0.0355 | 0.0056 |
| 3-2 | 0.0250 | 0.0219 | 0.0031 |
| 1-4 | 0.0250 | 0.0261 | 0.0011 |
| 3-1 | 0.0228 | 0.0243 | 0.0014 |
| **Sum (top 15)** | **0.8586** | **0.8945** | — |
- High-score mass (total ≥9 goals): 2.48e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS
