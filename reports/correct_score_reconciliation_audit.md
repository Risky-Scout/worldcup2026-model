# Correct-Score Reconciliation Audit

**Generated**: 2026-07-09T19:10:58Z

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
| 1-0 | 0.1332 | 0.1277 | 0.0055 |
| 1-1 | 0.1142 | 0.1131 | 0.0011 |
| 2-0 | 0.1066 | 0.1183 | 0.0117 |
| 2-1 | 0.1066 | 0.1017 | 0.0049 |
| 0-0 | 0.0727 | 0.0848 | 0.0121 |
| 3-0 | 0.0615 | 0.0718 | 0.0103 |
| 3-1 | 0.0571 | 0.0589 | 0.0019 |
| 0-1 | 0.0533 | 0.0560 | 0.0028 |
| 2-2 | 0.0444 | 0.0408 | 0.0036 |
| 1-2 | 0.0421 | 0.0420 | 0.0000 |
| 3-2 | 0.0285 | 0.0241 | 0.0044 |
| 4-0 | 0.0285 | 0.0347 | 0.0061 |
| 4-1 | 0.0258 | 0.0274 | 0.0016 |
| 0-2 | 0.0222 | 0.0230 | 0.0008 |
| 4-2 | 0.0143 | 0.0112 | 0.0031 |
| **Sum (top 15)** | **0.9108** | **0.9354** | — |
- High-score mass (total ≥9 goals): 1.73e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Spain vs Belgium
- CS outcomes: 28  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-0 | 0.1139 | 0.1040 | 0.0099 |
| 2-1 | 0.1063 | 0.1035 | 0.0028 |
| 1-1 | 0.1063 | 0.1114 | 0.0051 |
| 2-0 | 0.0938 | 0.1035 | 0.0097 |
| 3-1 | 0.0613 | 0.0642 | 0.0029 |
| 3-0 | 0.0569 | 0.0671 | 0.0102 |
| 0-0 | 0.0569 | 0.0706 | 0.0137 |
| 2-2 | 0.0569 | 0.0517 | 0.0052 |
| 0-1 | 0.0469 | 0.0514 | 0.0045 |
| 1-2 | 0.0469 | 0.0492 | 0.0023 |
| 3-2 | 0.0347 | 0.0315 | 0.0031 |
| 4-0 | 0.0285 | 0.0332 | 0.0047 |
| 4-1 | 0.0285 | 0.0308 | 0.0023 |
| 0-2 | 0.0234 | 0.0261 | 0.0026 |
| 2-3 | 0.0194 | 0.0149 | 0.0045 |
| **Sum (top 15)** | **0.8806** | **0.9131** | — |
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
- CS outcomes: 25  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-0 | 0.1428 | 0.1386 | 0.0043 |
| 1-1 | 0.1163 | 0.1215 | 0.0052 |
| 2-0 | 0.1086 | 0.1176 | 0.0091 |
| 2-1 | 0.1018 | 0.0961 | 0.0056 |
| 0-0 | 0.0857 | 0.1015 | 0.0158 |
| 0-1 | 0.0626 | 0.0674 | 0.0048 |
| 3-0 | 0.0582 | 0.0644 | 0.0062 |
| 3-1 | 0.0479 | 0.0502 | 0.0023 |
| 2-2 | 0.0452 | 0.0393 | 0.0059 |
| 1-2 | 0.0452 | 0.0438 | 0.0015 |
| 3-2 | 0.0263 | 0.0205 | 0.0058 |
| 0-2 | 0.0263 | 0.0277 | 0.0015 |
| 4-0 | 0.0239 | 0.0269 | 0.0029 |
| 4-1 | 0.0226 | 0.0210 | 0.0017 |
| 2-3 | 0.0133 | 0.0091 | 0.0043 |
| **Sum (top 15)** | **0.9268** | **0.9455** | — |
- High-score mass (total ≥9 goals): 1.39e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS
