# Correct-Score Reconciliation Audit

**Generated**: 2026-07-06T02:28:23Z

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

### Portugal vs Spain
- CS outcomes: 29  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-1 | 0.1124 | 0.1188 | 0.0064 |
| 0-1 | 0.0983 | 0.0932 | 0.0051 |
| 1-2 | 0.0983 | 0.0987 | 0.0004 |
| 0-2 | 0.0749 | 0.0851 | 0.0102 |
| 2-2 | 0.0656 | 0.0605 | 0.0050 |
| 1-0 | 0.0605 | 0.0614 | 0.0009 |
| 2-1 | 0.0605 | 0.0629 | 0.0024 |
| 0-0 | 0.0562 | 0.0710 | 0.0148 |
| 1-3 | 0.0524 | 0.0564 | 0.0040 |
| 0-3 | 0.0437 | 0.0508 | 0.0071 |
| 2-0 | 0.0342 | 0.0372 | 0.0030 |
| 2-3 | 0.0342 | 0.0329 | 0.0013 |
| 3-2 | 0.0254 | 0.0211 | 0.0043 |
| 1-4 | 0.0254 | 0.0251 | 0.0003 |
| 3-1 | 0.0231 | 0.0237 | 0.0006 |
| **Sum (top 15)** | **0.8651** | **0.8989** | — |
- High-score mass (total ≥9 goals): 2.36e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### USA vs Belgium
- CS outcomes: 31  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-1 | 0.1203 | 0.1244 | 0.0041 |
| 2-1 | 0.0823 | 0.0858 | 0.0035 |
| 1-2 | 0.0823 | 0.0844 | 0.0021 |
| 1-0 | 0.0711 | 0.0677 | 0.0034 |
| 2-2 | 0.0711 | 0.0694 | 0.0017 |
| 0-1 | 0.0711 | 0.0667 | 0.0044 |
| 0-0 | 0.0489 | 0.0665 | 0.0176 |
| 0-2 | 0.0489 | 0.0555 | 0.0066 |
| 2-0 | 0.0460 | 0.0562 | 0.0102 |
| 1-3 | 0.0411 | 0.0423 | 0.0012 |
| 3-1 | 0.0391 | 0.0432 | 0.0041 |
| 2-3 | 0.0372 | 0.0330 | 0.0043 |
| 3-2 | 0.0340 | 0.0330 | 0.0009 |
| 3-0 | 0.0252 | 0.0299 | 0.0047 |
| 0-3 | 0.0252 | 0.0286 | 0.0034 |
| **Sum (top 15)** | **0.8437** | **0.8866** | — |
- High-score mass (total ≥9 goals): 2.84e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Argentina vs Egypt
- CS outcomes: 26  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-0 | 0.1376 | 0.1480 | 0.0104 |
| 2-0 | 0.1376 | 0.1464 | 0.0088 |
| 2-1 | 0.0939 | 0.0934 | 0.0005 |
| 3-0 | 0.0887 | 0.0941 | 0.0054 |
| 1-1 | 0.0887 | 0.0924 | 0.0037 |
| 0-0 | 0.0665 | 0.0773 | 0.0108 |
| 3-1 | 0.0614 | 0.0613 | 0.0000 |
| 4-0 | 0.0443 | 0.0473 | 0.0030 |
| 0-1 | 0.0399 | 0.0486 | 0.0087 |
| 2-2 | 0.0347 | 0.0290 | 0.0057 |
| 4-1 | 0.0307 | 0.0301 | 0.0006 |
| 1-2 | 0.0285 | 0.0285 | 0.0000 |
| 3-2 | 0.0235 | 0.0198 | 0.0036 |
| 5-0 | 0.0235 | 0.0194 | 0.0040 |
| 5-1 | 0.0142 | 0.0118 | 0.0025 |
| **Sum (top 15)** | **0.9135** | **0.9474** | — |
- High-score mass (total ≥9 goals): 1.65e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### Switzerland vs Colombia
- CS outcomes: 25  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-1 | 0.1358 | 0.1407 | 0.0048 |
| 0-1 | 0.1233 | 0.1208 | 0.0025 |
| 1-0 | 0.0943 | 0.0932 | 0.0011 |
| 0-0 | 0.0943 | 0.1135 | 0.0192 |
| 1-2 | 0.0844 | 0.0844 | 0.0001 |
| 0-2 | 0.0763 | 0.0844 | 0.0080 |
| 2-1 | 0.0668 | 0.0641 | 0.0027 |
| 2-2 | 0.0501 | 0.0469 | 0.0032 |
| 2-0 | 0.0445 | 0.0488 | 0.0043 |
| 0-3 | 0.0348 | 0.0376 | 0.0028 |
| 1-3 | 0.0348 | 0.0367 | 0.0019 |
| 2-3 | 0.0236 | 0.0191 | 0.0045 |
| 3-1 | 0.0223 | 0.0209 | 0.0014 |
| 3-2 | 0.0195 | 0.0140 | 0.0055 |
| 3-0 | 0.0174 | 0.0161 | 0.0013 |
| **Sum (top 15)** | **0.9224** | **0.9413** | — |
- High-score mass (total ≥9 goals): 1.28e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS

### France vs Morocco
- CS outcomes: 27  |  CS vendors: 1  |  Publish mode: market_reconciled

| Score | Market P (no-vig) | Published PMF P | Abs Error |
|-------|------------------|-----------------|-----------|
| 1-0 | 0.1329 | 0.1238 | 0.0091 |
| 1-1 | 0.1140 | 0.1140 | 0.0001 |
| 2-0 | 0.1064 | 0.1169 | 0.0106 |
| 2-1 | 0.1064 | 0.1016 | 0.0048 |
| 3-0 | 0.0665 | 0.0745 | 0.0081 |
| 0-0 | 0.0665 | 0.0811 | 0.0146 |
| 3-1 | 0.0570 | 0.0602 | 0.0032 |
| 0-1 | 0.0499 | 0.0543 | 0.0045 |
| 2-2 | 0.0469 | 0.0421 | 0.0048 |
| 1-2 | 0.0420 | 0.0419 | 0.0001 |
| 4-0 | 0.0307 | 0.0354 | 0.0047 |
| 3-2 | 0.0285 | 0.0251 | 0.0034 |
| 4-1 | 0.0257 | 0.0280 | 0.0022 |
| 0-2 | 0.0222 | 0.0231 | 0.0009 |
| 4-2 | 0.0131 | 0.0112 | 0.0018 |
| **Sum (top 15)** | **0.9084** | **0.9334** | — |
- High-score mass (total ≥9 goals): 1.81e-05
- Impossible-score check (any cell ≥9 goals > 1e-3): ✅ PASS
- PMF validation: ✅ PASS
