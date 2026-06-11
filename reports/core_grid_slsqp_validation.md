# Core-Grid SLSQP Validation Report

**Generated**: 2026-06-11
**Pipeline version**: v4 (core-grid SLSQP)
**Data snapshot**: BDL real data, 2018/2022/2026

## Summary

The `CoreGridSLSQPReconciler` was evaluated against the safe blend/IPF method across
all 72 named 2026 group-stage fixtures. SLSQP was selected when it passed plausibility
checks AND its validation loss (weighted squared market constraint errors) was lower
than or equal to the blend's loss.

## Selection results

| Metric | Value |
|--------|-------|
| Total named 2026 fixtures | 72 |
| Fixtures where SLSQP selected | 27 (37.5%) |
| Fixtures where blend selected | 45 (62.5%) |
| SLSQP plausibility failures (disqualified) | varies per match |
| Fixtures with impossible top-3 (total>6) | **0** |

## Plausibility checks

All 72 published fixtures pass:

| Check | SLSQP matches | Blend matches |
|-------|--------------|--------------|
| PMF sums to 1.0 (±5e-4) | 27/27 ✓ | 45/45 ✓ |
| Top-3 scorelines plausible (total≤6) | 27/27 ✓ | 45/45 ✓ |
| No cell with total_goals≥9, P>1e-4 | 27/27 ✓ | 45/45 ✓ |
| tail_mass_exact present | 72/72 ✓ | — |

## High-score mass comparison

| Method | Avg mass at total_goals≥8 |
|--------|--------------------------|
| SLSQP (27 matches) | **6.73e-05** |
| Blend (45 matches) | 9.28e-03 |
| Ratio | SLSQP 138× lower |

SLSQP's hard upper bounds (`_ABS_CAP_BY_TOTAL[8]` = 8e-4, `[9]` = 1e-4, `[10]` = 2e-5)
prevent high-score concentration that the unconstrained blend can accumulate for very
lopsided matches.

## Market constraint error comparison (June 11 matches)

### Mexico vs South Africa (blend selected)

| Market | Target | PMF-derived | Abs error |
|--------|--------|------------|-----------|
| Home win | 0.675 | 0.678 | 0.003 |
| Draw | 0.205 | 0.205 | <0.001 |
| Away win | 0.120 | 0.117 | 0.003 |
| O/U 2.5 | ~0.62 | ~0.62 | <0.01 |

### South Korea vs Czechia (SLSQP selected)

| Market | Target | PMF-derived | Abs error |
|--------|--------|------------|-----------|
| Home win | 0.36 | 0.362 | 0.002 |
| Draw | 0.31 | 0.313 | 0.003 |
| Away win | 0.33 | 0.325 | 0.005 |

## Convergence summary

SLSQP uses a single hard equality constraint (sum = 1 - tail_mass), making the
problem well-conditioned vs the previous 225-variable, multi-equality-constraint
design. Non-convergence ("Positive directional derivative for linesearch") is
treated as a soft failure: the result is still used if it passes plausibility checks,
otherwise blend is used automatically.

## Comparison with old 15×15 SLSQP

| Property | Old 15×15 | New 8×8 core |
|----------|-----------|-------------|
| Variables | 225 | 64 |
| Hard equality constraints | N (all markets) | 1 (sum = target) |
| Market constraints | Hard equalities | Soft squared-error penalties |
| Worst artifact observed | 4-9: P=0.0256 | None observed |
| Max P(total_goals≥9) | 0.0167 | <1e-6 |
| Top-3 plausibility | Failed | All pass |

## Tail model validation

```
tail_mass_exact for Mexico vs South Africa:  3.04e-04  (mass at h>=8 or a>=8)
tail_mass_exact for South Korea vs Czechia:  3.41e-05
```

Neither is zero. The tail distribution uses the parametric market_implied PMF for
cells outside the 8×8 core, preserving arbitrary score lookup while keeping the
optimized region small and well-conditioned.

## Acceptance criteria (all pass)

- [x] SLSQP passes or matches blend on validation loss
- [x] No impossible high-score artifacts (total_goals≥9, P>1e-4)
- [x] All top-3 scorelines have total_goals ≤ 6
- [x] Market constraints preserved within tolerance
- [x] artifact validation tests: 1104 passed, 0 failures
