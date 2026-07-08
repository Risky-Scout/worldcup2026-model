# Correct-Score Reconciliation Audit

**Generated**: 2026-07-08T10:07:46Z

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
| 1-0 | 0.1337 | 0.1231 | 0.0106 |
| 1-1 | 0.1146 | 0.1135 | 0.0011 |
| 2-0 | 0.1070 | 0.1163 | 0.0094 |
| 2-1 | 0.1003 | 0.0995 | 0.0008 |
| 0-0 | 0.0729 | 0.0825 | 0.0096 |
| 3-0 | 0.0669 | 0.0746 | 0.0077 |
| 3-1 | 0.0573 | 0.0605 | 0.0032 |
| 0-1 | 0.0501 | 0.0539 | 0.0037 |
| 2-2 | 0.0446 | 0.0417 | 0.0029 |
| 1-2 | 0.0422 | 0.0425 | 0.0002 |
| 4-0 | 0.0309 | 0.0354 | 0.0045 |
| 3-2 | 0.0287 | 0.0254 | 0.0033 |
| 4-1 | 0.0287 | 0.0286 | 0.0001 |
| 0-2 | 0.0223 | 0.0230 | 0.0007 |
| 2-3 | 0.0132 | 0.0104 | 0.0028 |
| **Sum (top 15)** | **0.9133** | **0.9309** | — |
- High-score mass (total ≥9 goals): 1.80e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Spain vs Belgium
- CS outcomes: 28  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-0 | 0.1132 | 0.1082 | 0.0051 |
| 1-1 | 0.1057 | 0.1106 | 0.0050 |
| 2-0 | 0.0991 | 0.1080 | 0.0089 |
| 2-1 | 0.0991 | 0.1009 | 0.0018 |
| 3-0 | 0.0610 | 0.0701 | 0.0092 |
| 0-0 | 0.0610 | 0.0730 | 0.0121 |
| 3-1 | 0.0566 | 0.0628 | 0.0062 |
| 0-1 | 0.0528 | 0.0533 | 0.0004 |
| 2-2 | 0.0495 | 0.0484 | 0.0012 |
| 1-2 | 0.0466 | 0.0473 | 0.0007 |
| 3-2 | 0.0345 | 0.0305 | 0.0040 |
| 4-0 | 0.0305 | 0.0345 | 0.0040 |
| 4-1 | 0.0283 | 0.0306 | 0.0023 |
| 0-2 | 0.0256 | 0.0254 | 0.0002 |
| 2-3 | 0.0172 | 0.0135 | 0.0037 |
| **Sum (top 15)** | **0.8807** | **0.9171** | — |
- High-score mass (total ≥9 goals): 2.18e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Norway vs England
- CS outcomes: 31  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-1 | 0.1105 | 0.1154 | 0.0048 |
| 1-2 | 0.0967 | 0.0996 | 0.0028 |
| 0-1 | 0.0910 | 0.0894 | 0.0016 |
| 0-2 | 0.0774 | 0.0871 | 0.0097 |
| 2-2 | 0.0645 | 0.0607 | 0.0038 |
| 2-1 | 0.0595 | 0.0616 | 0.0021 |
| 1-0 | 0.0553 | 0.0571 | 0.0018 |
| 1-3 | 0.0553 | 0.0601 | 0.0048 |
| 0-0 | 0.0484 | 0.0644 | 0.0160 |
| 0-3 | 0.0455 | 0.0539 | 0.0084 |
| 2-3 | 0.0387 | 0.0358 | 0.0029 |
| 2-0 | 0.0298 | 0.0343 | 0.0045 |
| 3-2 | 0.0250 | 0.0215 | 0.0035 |
| 1-4 | 0.0250 | 0.0275 | 0.0026 |
| 3-1 | 0.0228 | 0.0233 | 0.0005 |
| **Sum (top 15)** | **0.8452** | **0.8915** | — |
- High-score mass (total ≥9 goals): 2.53e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Argentina vs Switzerland
- CS outcomes: 27  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-0 | 0.1325 | 0.1361 | 0.0035 |
| 1-1 | 0.1136 | 0.1230 | 0.0094 |
| 2-0 | 0.1060 | 0.1175 | 0.0115 |
| 2-1 | 0.0936 | 0.0932 | 0.0003 |
| 0-0 | 0.0795 | 0.1018 | 0.0223 |
| 0-1 | 0.0663 | 0.0697 | 0.0034 |
| 3-0 | 0.0612 | 0.0646 | 0.0035 |
| 3-1 | 0.0497 | 0.0503 | 0.0006 |
| 1-2 | 0.0468 | 0.0440 | 0.0028 |
| 2-2 | 0.0419 | 0.0392 | 0.0026 |
| 0-2 | 0.0306 | 0.0292 | 0.0014 |
| 4-0 | 0.0284 | 0.0270 | 0.0014 |
| 3-2 | 0.0234 | 0.0201 | 0.0033 |
| 4-1 | 0.0234 | 0.0207 | 0.0027 |
| 1-3 | 0.0156 | 0.0113 | 0.0043 |
| **Sum (top 15)** | **0.9124** | **0.9477** | — |
- High-score mass (total ≥9 goals): 1.37e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS
