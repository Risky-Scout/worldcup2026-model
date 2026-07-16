# Core-Grid SLSQP Methodology

**Generated**: 2026-07-16T04:10:30Z

## Why 8×8?

In World Cup matches, P(total goals ≥ 8) < 1e-4 for any plausible
expected-goals pair. An 8×8 grid covers 99.99%+ of all probability.

The key failure of 15×15 SLSQP was 225 degrees of freedom with hard
equality constraints — SLSQP found constraint-feasible solutions that
deposited mass in cells like [4,9] and [11,5]. With 64 variables and
only ONE hard equality constraint (sum = target), the optimization is
well-conditioned.

## Objective function

```
L = w_kl * KL(p || prior)
  + w_1x2 * [ (P_hw - target_hw)² + (P_dr - target_dr)² + (P_aw - target_aw)² ]
  + w_ou  * Σ_k (P_over_k - target_k)²
  + w_btts * (P_btts - target_btts)²
  + w_cs  * Σ_{h,a} (p[h,a] - cs_target[h,a])²   (cs_1v=4, cs_mv=14)
  + w_smooth * Σ_adjacent (p[i] - p[j])²
  + w_high7 * Σ_{total=7} p[h,a]
  + w_high8 * Σ_{total>=8} p[h,a]
```

**Why soft penalties?** No-vig market probabilities from different vendors
and market types are never perfectly mutually consistent. Using them as
hard equality constraints forces SLSQP into an infeasible region. Soft
penalties let the optimizer find the best feasible compromise.

## Per-cell upper bounds

| Total goals | Absolute cap | Description |
|-------------|-------------|-------------|
| 0 | 0.50 | 0-0 common in tight games |
| 1 | 0.38 | 1-0, 0-1 most common WC scores |
| 2 | 0.38 | 2-0, 1-1, 0-2 |
| 3 | 0.28 | 2-1, 3-0, etc. |
| 4 | 0.22 | |
| 5 | 0.08 | 3-2, 4-1 — rare |
| 6 | 0.022 | 4-2, 3-3 — very rare |
| 7 | 0.005 | 5-2, 4-3 — once-in-WC |
| 8 | 0.0008 | effectively zero |
| ≥9 | <1e-4 | impossible |

## Tail model

Scores outside the 8×8 core come from the market_implied PMF (unoptimized).
tail_mass = 1 - sum(core) ≈ 1e-4 to 1e-12 depending on expected goals.

The tail is partitioned into event buckets:
- home_8plus_away_0_7
- home_0_7_away_8plus
- both_8plus
- other_home_win / other_draw / other_away_win

## Selection rule

SLSQP result is used only if:
1. validate() returns no errors
2. validation_loss(slsqp) ≤ validation_loss(blend)
3. If SLSQP did not converge: its score must be >5% better than blend

Otherwise, the safe blend/IPF result is used.