# Correct-Score Reconciliation Audit

**Generated**: 2026-07-11T02:21:09Z

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
| Total 2026 matches predicted | 3 |
| Matches with any CS data | 3 |
| Matches with 1 CS vendor | 3 |
| Matches with 2+ CS vendors | 0 |

## Per-match correct-score audit

### Norway vs England
- CS outcomes: 30  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-1 | 0.1119 | 0.1174 | 0.0055 |
| 1-2 | 0.0979 | 0.0995 | 0.0015 |
| 0-1 | 0.0922 | 0.0883 | 0.0038 |
| 0-2 | 0.0746 | 0.0845 | 0.0099 |
| 2-1 | 0.0603 | 0.0630 | 0.0028 |
| 2-2 | 0.0603 | 0.0604 | 0.0002 |
| 1-0 | 0.0560 | 0.0581 | 0.0021 |
| 1-3 | 0.0560 | 0.0591 | 0.0032 |
| 0-0 | 0.0522 | 0.0679 | 0.0156 |
| 0-3 | 0.0412 | 0.0509 | 0.0096 |
| 2-3 | 0.0392 | 0.0354 | 0.0037 |
| 2-0 | 0.0341 | 0.0363 | 0.0023 |
| 3-1 | 0.0253 | 0.0244 | 0.0008 |
| 3-2 | 0.0253 | 0.0220 | 0.0033 |
| 1-4 | 0.0253 | 0.0263 | 0.0011 |
| **Sum (top 15)** | **0.8516** | **0.8937** | — |
- High-score mass (total ≥9 goals): 2.50e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Argentina vs Switzerland
- CS outcomes: 23  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-0 | 0.1431 | 0.1394 | 0.0038 |
| 1-1 | 0.1255 | 0.1243 | 0.0012 |
| 2-0 | 0.1088 | 0.1187 | 0.0099 |
| 2-1 | 0.0960 | 0.0942 | 0.0018 |
| 0-0 | 0.0859 | 0.1014 | 0.0155 |
| 0-1 | 0.0628 | 0.0669 | 0.0041 |
| 3-0 | 0.0583 | 0.0654 | 0.0071 |
| 3-1 | 0.0510 | 0.0511 | 0.0001 |
| 1-2 | 0.0453 | 0.0430 | 0.0023 |
| 2-2 | 0.0429 | 0.0378 | 0.0052 |
| 4-0 | 0.0263 | 0.0278 | 0.0014 |
| 0-2 | 0.0263 | 0.0270 | 0.0007 |
| 3-2 | 0.0240 | 0.0199 | 0.0041 |
| 4-1 | 0.0227 | 0.0211 | 0.0016 |
| 1-3 | 0.0134 | 0.0106 | 0.0028 |
| **Sum (top 15)** | **0.9323** | **0.9484** | — |
- High-score mass (total ≥9 goals): 1.38e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### France vs Spain
- CS outcomes: 27  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-1 | 0.1315 | 0.1337 | 0.0022 |
| 1-0 | 0.0986 | 0.0954 | 0.0032 |
| 2-1 | 0.0928 | 0.0903 | 0.0026 |
| 0-1 | 0.0789 | 0.0794 | 0.0005 |
| 0-0 | 0.0717 | 0.0870 | 0.0153 |
| 1-2 | 0.0717 | 0.0730 | 0.0012 |
| 2-0 | 0.0657 | 0.0737 | 0.0080 |
| 2-2 | 0.0607 | 0.0577 | 0.0030 |
| 0-2 | 0.0438 | 0.0505 | 0.0067 |
| 3-1 | 0.0415 | 0.0428 | 0.0013 |
| 3-0 | 0.0343 | 0.0368 | 0.0025 |
| 3-2 | 0.0282 | 0.0260 | 0.0022 |
| 1-3 | 0.0282 | 0.0290 | 0.0008 |
| 2-3 | 0.0255 | 0.0215 | 0.0039 |
| 0-3 | 0.0192 | 0.0205 | 0.0013 |
| **Sum (top 15)** | **0.8924** | **0.9174** | — |
- High-score mass (total ≥9 goals): 2.00e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS
