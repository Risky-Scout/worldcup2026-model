# Correct-Score Reconciliation Audit

**Generated**: 2026-07-06T22:09:43Z

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

### USA vs Belgium
- CS outcomes: 31  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-1 | 0.1205 | 0.1240 | 0.0035 |
| 2-1 | 0.0870 | 0.0886 | 0.0016 |
| 1-2 | 0.0824 | 0.0837 | 0.0012 |
| 1-0 | 0.0746 | 0.0652 | 0.0094 |
| 2-2 | 0.0746 | 0.0716 | 0.0030 |
| 0-1 | 0.0653 | 0.0604 | 0.0048 |
| 2-0 | 0.0489 | 0.0577 | 0.0087 |
| 0-0 | 0.0489 | 0.0658 | 0.0168 |
| 0-2 | 0.0461 | 0.0519 | 0.0058 |
| 3-1 | 0.0412 | 0.0458 | 0.0046 |
| 3-2 | 0.0373 | 0.0353 | 0.0020 |
| 1-3 | 0.0340 | 0.0400 | 0.0060 |
| 2-3 | 0.0340 | 0.0328 | 0.0012 |
| 3-0 | 0.0280 | 0.0322 | 0.0042 |
| 3-3 | 0.0230 | 0.0184 | 0.0046 |
| **Sum (top 15)** | **0.8459** | **0.8733** | — |
- High-score mass (total ≥9 goals): 2.97e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Argentina vs Egypt
- CS outcomes: 26  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-0 | 0.1466 | 0.1486 | 0.0020 |
| 2-0 | 0.1414 | 0.1474 | 0.0059 |
| 3-0 | 0.0949 | 0.0989 | 0.0040 |
| 2-1 | 0.0896 | 0.0913 | 0.0017 |
| 1-1 | 0.0849 | 0.0894 | 0.0045 |
| 0-0 | 0.0733 | 0.0791 | 0.0058 |
| 3-1 | 0.0620 | 0.0620 | 0.0000 |
| 4-0 | 0.0474 | 0.0503 | 0.0029 |
| 0-1 | 0.0424 | 0.0462 | 0.0038 |
| 4-1 | 0.0288 | 0.0305 | 0.0017 |
| 2-2 | 0.0288 | 0.0275 | 0.0013 |
| 1-2 | 0.0260 | 0.0268 | 0.0008 |
| 3-2 | 0.0224 | 0.0193 | 0.0031 |
| 5-0 | 0.0224 | 0.0207 | 0.0017 |
| 5-1 | 0.0144 | 0.0123 | 0.0021 |
| **Sum (top 15)** | **0.9253** | **0.9502** | — |
- High-score mass (total ≥9 goals): 1.68e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Switzerland vs Colombia
- CS outcomes: 25  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-1 | 0.1392 | 0.1427 | 0.0036 |
| 0-1 | 0.1242 | 0.1193 | 0.0049 |
| 0-0 | 0.0950 | 0.1140 | 0.0191 |
| 1-0 | 0.0897 | 0.0914 | 0.0017 |
| 1-2 | 0.0897 | 0.0856 | 0.0041 |
| 0-2 | 0.0734 | 0.0825 | 0.0092 |
| 2-1 | 0.0673 | 0.0649 | 0.0023 |
| 2-2 | 0.0538 | 0.0477 | 0.0061 |
| 2-0 | 0.0425 | 0.0491 | 0.0067 |
| 0-3 | 0.0351 | 0.0370 | 0.0019 |
| 1-3 | 0.0351 | 0.0363 | 0.0012 |
| 3-1 | 0.0237 | 0.0215 | 0.0023 |
| 2-3 | 0.0237 | 0.0189 | 0.0048 |
| 3-0 | 0.0175 | 0.0165 | 0.0010 |
| 3-2 | 0.0175 | 0.0141 | 0.0034 |
| **Sum (top 15)** | **0.9273** | **0.9417** | — |
- High-score mass (total ≥9 goals): 1.29e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### France vs Morocco
- CS outcomes: 26  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-0 | 0.1318 | 0.1262 | 0.0057 |
| 2-0 | 0.1130 | 0.1202 | 0.0072 |
| 1-1 | 0.1055 | 0.1111 | 0.0056 |
| 2-1 | 0.0989 | 0.0983 | 0.0006 |
| 0-0 | 0.0719 | 0.0844 | 0.0125 |
| 3-0 | 0.0659 | 0.0739 | 0.0080 |
| 3-1 | 0.0565 | 0.0592 | 0.0027 |
| 0-1 | 0.0527 | 0.0560 | 0.0033 |
| 2-2 | 0.0439 | 0.0412 | 0.0027 |
| 1-2 | 0.0416 | 0.0417 | 0.0001 |
| 4-0 | 0.0344 | 0.0355 | 0.0011 |
| 3-2 | 0.0283 | 0.0245 | 0.0038 |
| 4-1 | 0.0283 | 0.0277 | 0.0006 |
| 0-2 | 0.0233 | 0.0234 | 0.0001 |
| 5-0 | 0.0141 | 0.0130 | 0.0011 |
| **Sum (top 15)** | **0.9102** | **0.9364** | — |
- High-score mass (total ≥9 goals): 1.73e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Norway vs England
- CS outcomes: 28  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-1 | 0.1119 | 0.1169 | 0.0050 |
| 0-1 | 0.0979 | 0.0913 | 0.0066 |
| 1-2 | 0.0979 | 0.0987 | 0.0008 |
| 0-2 | 0.0824 | 0.0862 | 0.0038 |
| 1-0 | 0.0602 | 0.0603 | 0.0000 |
| 2-1 | 0.0602 | 0.0634 | 0.0032 |
| 0-0 | 0.0602 | 0.0702 | 0.0100 |
| 2-2 | 0.0602 | 0.0599 | 0.0004 |
| 1-3 | 0.0522 | 0.0568 | 0.0046 |
| 0-3 | 0.0461 | 0.0517 | 0.0056 |
| 2-0 | 0.0341 | 0.0365 | 0.0025 |
| 2-3 | 0.0341 | 0.0334 | 0.0006 |
| 1-4 | 0.0253 | 0.0256 | 0.0003 |
| 3-1 | 0.0230 | 0.0242 | 0.0012 |
| 0-4 | 0.0230 | 0.0233 | 0.0002 |
| **Sum (top 15)** | **0.8689** | **0.8984** | — |
- High-score mass (total ≥9 goals): 2.42e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS
