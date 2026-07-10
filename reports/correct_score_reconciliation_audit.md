# Correct-Score Reconciliation Audit

**Generated**: 2026-07-10T17:01:46Z

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

### Spain vs Belgium
- CS outcomes: 29  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-0 | 0.1068 | 0.1015 | 0.0053 |
| 1-1 | 0.1068 | 0.1115 | 0.0047 |
| 2-1 | 0.1001 | 0.1017 | 0.0015 |
| 2-0 | 0.0942 | 0.1050 | 0.0108 |
| 3-0 | 0.0616 | 0.0700 | 0.0084 |
| 3-1 | 0.0616 | 0.0652 | 0.0035 |
| 0-0 | 0.0572 | 0.0709 | 0.0136 |
| 2-2 | 0.0534 | 0.0505 | 0.0029 |
| 0-1 | 0.0501 | 0.0513 | 0.0012 |
| 1-2 | 0.0471 | 0.0482 | 0.0011 |
| 3-2 | 0.0348 | 0.0318 | 0.0031 |
| 4-0 | 0.0286 | 0.0343 | 0.0057 |
| 4-1 | 0.0286 | 0.0315 | 0.0029 |
| 0-2 | 0.0236 | 0.0253 | 0.0017 |
| 4-2 | 0.0195 | 0.0151 | 0.0044 |
| **Sum (top 15)** | **0.8741** | **0.9136** | — |
- High-score mass (total ≥9 goals): 2.25e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Norway vs England
- CS outcomes: 29  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-1 | 0.1130 | 0.1180 | 0.0051 |
| 1-2 | 0.0988 | 0.0996 | 0.0008 |
| 0-1 | 0.0930 | 0.0906 | 0.0024 |
| 0-2 | 0.0753 | 0.0865 | 0.0112 |
| 2-2 | 0.0659 | 0.0606 | 0.0053 |
| 2-1 | 0.0608 | 0.0619 | 0.0011 |
| 1-0 | 0.0565 | 0.0585 | 0.0020 |
| 1-3 | 0.0565 | 0.0591 | 0.0027 |
| 0-0 | 0.0494 | 0.0670 | 0.0176 |
| 0-3 | 0.0439 | 0.0525 | 0.0085 |
| 2-3 | 0.0395 | 0.0350 | 0.0046 |
| 2-0 | 0.0304 | 0.0351 | 0.0047 |
| 3-1 | 0.0255 | 0.0235 | 0.0020 |
| 3-2 | 0.0255 | 0.0211 | 0.0044 |
| 1-4 | 0.0255 | 0.0266 | 0.0011 |
| **Sum (top 15)** | **0.8596** | **0.8956** | — |
- High-score mass (total ≥9 goals): 2.45e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Argentina vs Switzerland
- CS outcomes: 25  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-0 | 0.1430 | 0.1371 | 0.0059 |
| 1-1 | 0.1232 | 0.1233 | 0.0001 |
| 2-0 | 0.1068 | 0.1165 | 0.0097 |
| 2-1 | 0.1001 | 0.0961 | 0.0040 |
| 0-0 | 0.0890 | 0.1014 | 0.0124 |
| 0-1 | 0.0616 | 0.0663 | 0.0047 |
| 3-0 | 0.0572 | 0.0647 | 0.0075 |
| 3-1 | 0.0471 | 0.0506 | 0.0035 |
| 1-2 | 0.0445 | 0.0438 | 0.0006 |
| 2-2 | 0.0421 | 0.0386 | 0.0036 |
| 3-2 | 0.0258 | 0.0207 | 0.0051 |
| 4-0 | 0.0258 | 0.0276 | 0.0018 |
| 0-2 | 0.0258 | 0.0274 | 0.0016 |
| 4-1 | 0.0222 | 0.0213 | 0.0010 |
| 2-3 | 0.0121 | 0.0091 | 0.0030 |
| **Sum (top 15)** | **0.9265** | **0.9446** | — |
- High-score mass (total ≥9 goals): 1.41e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS
