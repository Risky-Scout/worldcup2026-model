# Correct-Score Reconciliation Audit

**Generated**: 2026-07-09T06:16:12Z

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
| Total 2026 matches predicted | 4 |
| Matches with any CS data | 4 |
| Matches with 1 CS vendor | 4 |
| Matches with 2+ CS vendors | 0 |

## Per-match correct-score audit

### France vs Morocco
- CS outcomes: 26  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-0 | 0.1337 | 0.1233 | 0.0104 |
| 1-1 | 0.1146 | 0.1128 | 0.0018 |
| 2-0 | 0.1070 | 0.1172 | 0.0102 |
| 2-1 | 0.1003 | 0.0997 | 0.0006 |
| 0-0 | 0.0729 | 0.0821 | 0.0092 |
| 3-0 | 0.0669 | 0.0757 | 0.0088 |
| 3-1 | 0.0573 | 0.0610 | 0.0037 |
| 0-1 | 0.0501 | 0.0531 | 0.0029 |
| 2-2 | 0.0446 | 0.0412 | 0.0034 |
| 1-2 | 0.0422 | 0.0417 | 0.0006 |
| 4-0 | 0.0309 | 0.0363 | 0.0054 |
| 3-2 | 0.0287 | 0.0254 | 0.0033 |
| 4-1 | 0.0287 | 0.0291 | 0.0004 |
| 0-2 | 0.0223 | 0.0224 | 0.0001 |
| 2-3 | 0.0132 | 0.0101 | 0.0031 |
| **Sum (top 15)** | **0.9133** | **0.9309** | — |
- High-score mass (total ≥9 goals): 1.79e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Spain vs Belgium
- CS outcomes: 28  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-0 | 0.1131 | 0.1076 | 0.0055 |
| 1-1 | 0.1055 | 0.1101 | 0.0046 |
| 2-0 | 0.0989 | 0.1081 | 0.0091 |
| 2-1 | 0.0989 | 0.1009 | 0.0019 |
| 3-0 | 0.0609 | 0.0702 | 0.0093 |
| 3-1 | 0.0609 | 0.0643 | 0.0034 |
| 0-0 | 0.0609 | 0.0724 | 0.0115 |
| 2-2 | 0.0528 | 0.0490 | 0.0038 |
| 0-1 | 0.0495 | 0.0522 | 0.0027 |
| 1-2 | 0.0466 | 0.0473 | 0.0008 |
| 3-2 | 0.0344 | 0.0307 | 0.0037 |
| 4-0 | 0.0283 | 0.0342 | 0.0059 |
| 4-1 | 0.0283 | 0.0308 | 0.0025 |
| 0-2 | 0.0255 | 0.0254 | 0.0002 |
| 4-2 | 0.0172 | 0.0142 | 0.0030 |
| **Sum (top 15)** | **0.8816** | **0.9173** | — |
- High-score mass (total ≥9 goals): 2.19e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Norway vs England
- CS outcomes: 31  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-1 | 0.1105 | 0.1156 | 0.0051 |
| 1-2 | 0.0967 | 0.0995 | 0.0028 |
| 0-1 | 0.0910 | 0.0890 | 0.0020 |
| 0-2 | 0.0774 | 0.0870 | 0.0096 |
| 2-2 | 0.0645 | 0.0608 | 0.0036 |
| 2-1 | 0.0595 | 0.0616 | 0.0021 |
| 1-0 | 0.0553 | 0.0570 | 0.0017 |
| 1-3 | 0.0553 | 0.0600 | 0.0048 |
| 0-0 | 0.0484 | 0.0647 | 0.0163 |
| 0-3 | 0.0455 | 0.0539 | 0.0084 |
| 2-3 | 0.0387 | 0.0358 | 0.0029 |
| 2-0 | 0.0298 | 0.0343 | 0.0045 |
| 3-2 | 0.0250 | 0.0215 | 0.0035 |
| 1-4 | 0.0250 | 0.0275 | 0.0026 |
| 3-1 | 0.0228 | 0.0233 | 0.0005 |
| **Sum (top 15)** | **0.8452** | **0.8916** | — |
- High-score mass (total ≥9 goals): 2.53e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Argentina vs Switzerland
- CS outcomes: 25  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-0 | 0.1417 | 0.1384 | 0.0033 |
| 1-1 | 0.1243 | 0.1250 | 0.0007 |
| 2-0 | 0.1010 | 0.1147 | 0.0138 |
| 2-1 | 0.1010 | 0.0959 | 0.0050 |
| 0-0 | 0.0850 | 0.1013 | 0.0163 |
| 0-1 | 0.0621 | 0.0679 | 0.0058 |
| 3-0 | 0.0577 | 0.0639 | 0.0062 |
| 3-1 | 0.0475 | 0.0499 | 0.0024 |
| 2-2 | 0.0449 | 0.0388 | 0.0061 |
| 1-2 | 0.0449 | 0.0440 | 0.0009 |
| 3-2 | 0.0261 | 0.0204 | 0.0057 |
| 4-0 | 0.0261 | 0.0269 | 0.0008 |
| 0-2 | 0.0261 | 0.0282 | 0.0021 |
| 4-1 | 0.0224 | 0.0208 | 0.0017 |
| 1-3 | 0.0132 | 0.0112 | 0.0020 |
| **Sum (top 15)** | **0.9241** | **0.9474** | — |
- High-score mass (total ≥9 goals): 1.39e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS
