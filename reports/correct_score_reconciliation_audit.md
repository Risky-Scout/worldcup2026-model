# Correct-Score Reconciliation Audit

**Generated**: 2026-07-09T10:47:25Z

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
- CS outcomes: 25  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-0 | 0.1366 | 0.1281 | 0.0085 |
| 1-1 | 0.1152 | 0.1140 | 0.0012 |
| 2-0 | 0.1075 | 0.1189 | 0.0114 |
| 2-1 | 0.1008 | 0.0991 | 0.0017 |
| 0-0 | 0.0733 | 0.0848 | 0.0115 |
| 3-0 | 0.0672 | 0.0753 | 0.0081 |
| 3-1 | 0.0576 | 0.0597 | 0.0021 |
| 0-1 | 0.0537 | 0.0556 | 0.0018 |
| 2-2 | 0.0448 | 0.0400 | 0.0047 |
| 1-2 | 0.0403 | 0.0405 | 0.0002 |
| 3-2 | 0.0288 | 0.0242 | 0.0045 |
| 4-0 | 0.0288 | 0.0351 | 0.0063 |
| 4-1 | 0.0260 | 0.0274 | 0.0014 |
| 0-2 | 0.0224 | 0.0226 | 0.0002 |
| 4-2 | 0.0132 | 0.0107 | 0.0026 |
| **Sum (top 15)** | **0.9162** | **0.9359** | — |
- High-score mass (total ≥9 goals): 1.70e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Spain vs Belgium
- CS outcomes: 28  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-0 | 0.1134 | 0.1038 | 0.0096 |
| 2-1 | 0.1058 | 0.1034 | 0.0025 |
| 1-1 | 0.1058 | 0.1113 | 0.0055 |
| 2-0 | 0.0934 | 0.1035 | 0.0101 |
| 3-1 | 0.0610 | 0.0643 | 0.0032 |
| 3-0 | 0.0567 | 0.0671 | 0.0104 |
| 0-0 | 0.0567 | 0.0705 | 0.0138 |
| 2-2 | 0.0567 | 0.0518 | 0.0049 |
| 0-1 | 0.0496 | 0.0520 | 0.0024 |
| 1-2 | 0.0496 | 0.0497 | 0.0001 |
| 3-2 | 0.0345 | 0.0316 | 0.0029 |
| 4-0 | 0.0283 | 0.0332 | 0.0049 |
| 4-1 | 0.0283 | 0.0308 | 0.0025 |
| 0-2 | 0.0233 | 0.0259 | 0.0026 |
| 4-2 | 0.0173 | 0.0148 | 0.0025 |
| **Sum (top 15)** | **0.8804** | **0.9136** | — |
- High-score mass (total ≥9 goals): 2.27e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Norway vs England
- CS outcomes: 31  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-1 | 0.1115 | 0.1167 | 0.0052 |
| 1-2 | 0.0976 | 0.0998 | 0.0022 |
| 0-1 | 0.0918 | 0.0922 | 0.0003 |
| 0-2 | 0.0781 | 0.0890 | 0.0109 |
| 2-2 | 0.0651 | 0.0596 | 0.0055 |
| 2-1 | 0.0601 | 0.0609 | 0.0009 |
| 1-0 | 0.0558 | 0.0584 | 0.0026 |
| 0-0 | 0.0520 | 0.0677 | 0.0156 |
| 1-3 | 0.0520 | 0.0585 | 0.0064 |
| 0-3 | 0.0459 | 0.0542 | 0.0083 |
| 2-3 | 0.0372 | 0.0344 | 0.0028 |
| 2-0 | 0.0300 | 0.0345 | 0.0044 |
| 3-2 | 0.0252 | 0.0205 | 0.0047 |
| 1-4 | 0.0252 | 0.0269 | 0.0017 |
| 3-1 | 0.0230 | 0.0224 | 0.0005 |
| **Sum (top 15)** | **0.8505** | **0.8956** | — |
- High-score mass (total ≥9 goals): 2.43e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Argentina vs Switzerland
- CS outcomes: 24  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-0 | 0.1428 | 0.1386 | 0.0042 |
| 1-1 | 0.1162 | 0.1219 | 0.0057 |
| 2-0 | 0.1085 | 0.1177 | 0.0092 |
| 2-1 | 0.1017 | 0.0959 | 0.0058 |
| 0-0 | 0.0857 | 0.1022 | 0.0165 |
| 0-1 | 0.0626 | 0.0676 | 0.0050 |
| 3-0 | 0.0581 | 0.0642 | 0.0061 |
| 3-1 | 0.0479 | 0.0499 | 0.0021 |
| 2-2 | 0.0452 | 0.0392 | 0.0060 |
| 1-2 | 0.0452 | 0.0436 | 0.0016 |
| 3-2 | 0.0262 | 0.0203 | 0.0060 |
| 4-0 | 0.0262 | 0.0271 | 0.0009 |
| 0-2 | 0.0262 | 0.0278 | 0.0015 |
| 4-1 | 0.0226 | 0.0208 | 0.0018 |
| 1-3 | 0.0123 | 0.0109 | 0.0014 |
| **Sum (top 15)** | **0.9275** | **0.9478** | — |
- High-score mass (total ≥9 goals): 1.38e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS
