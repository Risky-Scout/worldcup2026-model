# Correct-Score Reconciliation Audit

**Generated**: 2026-07-08T01:29:29Z

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
- CS outcomes: 27  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-0 | 0.1331 | 0.1244 | 0.0086 |
| 2-0 | 0.1064 | 0.1164 | 0.0100 |
| 1-1 | 0.1064 | 0.1106 | 0.0042 |
| 2-1 | 0.0998 | 0.0991 | 0.0007 |
| 0-0 | 0.0726 | 0.0825 | 0.0099 |
| 3-0 | 0.0665 | 0.0742 | 0.0077 |
| 3-1 | 0.0570 | 0.0603 | 0.0033 |
| 0-1 | 0.0499 | 0.0546 | 0.0047 |
| 2-2 | 0.0444 | 0.0420 | 0.0024 |
| 1-2 | 0.0399 | 0.0421 | 0.0022 |
| 4-0 | 0.0347 | 0.0361 | 0.0013 |
| 3-2 | 0.0285 | 0.0254 | 0.0031 |
| 4-1 | 0.0285 | 0.0285 | 0.0000 |
| 0-2 | 0.0222 | 0.0234 | 0.0012 |
| 5-0 | 0.0143 | 0.0134 | 0.0009 |
| **Sum (top 15)** | **0.9042** | **0.9331** | — |
- High-score mass (total ≥9 goals): 1.80e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Spain vs Belgium
- CS outcomes: 27  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-0 | 0.1149 | 0.1087 | 0.0062 |
| 1-1 | 0.1149 | 0.1133 | 0.0016 |
| 2-0 | 0.1005 | 0.1087 | 0.0082 |
| 2-1 | 0.1005 | 0.1013 | 0.0007 |
| 3-0 | 0.0619 | 0.0705 | 0.0086 |
| 0-0 | 0.0619 | 0.0728 | 0.0109 |
| 3-1 | 0.0575 | 0.0627 | 0.0053 |
| 2-2 | 0.0503 | 0.0475 | 0.0028 |
| 0-1 | 0.0503 | 0.0527 | 0.0024 |
| 1-2 | 0.0473 | 0.0474 | 0.0001 |
| 3-2 | 0.0350 | 0.0302 | 0.0048 |
| 4-0 | 0.0309 | 0.0346 | 0.0037 |
| 4-1 | 0.0287 | 0.0304 | 0.0017 |
| 0-2 | 0.0223 | 0.0248 | 0.0024 |
| 2-3 | 0.0158 | 0.0132 | 0.0025 |
| **Sum (top 15)** | **0.8927** | **0.9188** | — |
- High-score mass (total ≥9 goals): 2.15e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Norway vs England
- CS outcomes: 28  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-1 | 0.1131 | 0.1162 | 0.0031 |
| 1-2 | 0.0989 | 0.1000 | 0.0011 |
| 0-1 | 0.0931 | 0.0912 | 0.0019 |
| 0-2 | 0.0754 | 0.0866 | 0.0112 |
| 2-2 | 0.0660 | 0.0602 | 0.0058 |
| 2-1 | 0.0609 | 0.0618 | 0.0009 |
| 1-0 | 0.0565 | 0.0582 | 0.0017 |
| 0-0 | 0.0528 | 0.0662 | 0.0134 |
| 1-3 | 0.0528 | 0.0587 | 0.0059 |
| 0-3 | 0.0466 | 0.0538 | 0.0072 |
| 2-3 | 0.0377 | 0.0350 | 0.0027 |
| 2-0 | 0.0304 | 0.0347 | 0.0042 |
| 3-2 | 0.0255 | 0.0211 | 0.0044 |
| 1-4 | 0.0255 | 0.0271 | 0.0015 |
| 3-1 | 0.0233 | 0.0231 | 0.0001 |
| **Sum (top 15)** | **0.8585** | **0.8940** | — |
- High-score mass (total ≥9 goals): 2.48e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Argentina vs Switzerland
- CS outcomes: 27  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-0 | 0.1325 | 0.1444 | 0.0119 |
| 1-1 | 0.1136 | 0.1151 | 0.0015 |
| 2-0 | 0.1060 | 0.1176 | 0.0115 |
| 2-1 | 0.0936 | 0.0949 | 0.0013 |
| 0-0 | 0.0795 | 0.0949 | 0.0154 |
| 0-1 | 0.0663 | 0.0721 | 0.0058 |
| 3-0 | 0.0612 | 0.0663 | 0.0052 |
| 3-1 | 0.0497 | 0.0512 | 0.0015 |
| 1-2 | 0.0468 | 0.0448 | 0.0020 |
| 2-2 | 0.0419 | 0.0379 | 0.0040 |
| 0-2 | 0.0306 | 0.0289 | 0.0017 |
| 4-0 | 0.0284 | 0.0275 | 0.0009 |
| 3-2 | 0.0234 | 0.0202 | 0.0032 |
| 4-1 | 0.0234 | 0.0208 | 0.0025 |
| 1-3 | 0.0156 | 0.0114 | 0.0042 |
| **Sum (top 15)** | **0.9124** | **0.9480** | — |
- High-score mass (total ≥9 goals): 1.32e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS
