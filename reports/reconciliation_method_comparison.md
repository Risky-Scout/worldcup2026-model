# Reconciliation Method Comparison

**Generated**: 2026-06-14T08:59:35Z

## Methods compared

| Method | Description |
|--------|-------------|
| `market_implied` | Poisson PMF from `goal_expectancy_extended` (baseline) |
| `market_reconciled_blend` | α×market_implied + (1-α)×composite + gentle IPF |
| `market_reconciled_slsqp_core` | 8×8 core SLSQP with soft penalties + tail model |
| `market_reconciled_best` | Winner by validation loss (constraint error + plausibility) |

## Selection rule (CoreGridSLSQPReconciler)

SLSQP is selected over blend only when:
1. It passes all plausibility checks (no impossible scores)
2. Its validation loss ≤ blend validation loss
3. Either it converged, or its score is meaningfully better (>5%) than blend

This prevents SLSQP from being selected when it diverges or creates artifacts.

## Method selection counts (2026 matches)

| Method | Count |
|--------|-------|
| blend | 40 |
| slsqp_core | 24 |

## SLSQP core-grid design

- **Core grid**: 8×8 = 64 variables (h=0..7, a=0..7)
- **Tail**: parametric from market_implied, not optimized
- **Constraints**: 1 hard equality (sum = 1 - tail_mass), rest are soft penalties
- **Objective**: KL + weighted squared market errors + smoothness + high-score penalty
- **Bounds**: absolute caps by total_goals (e.g. total=7 → max 0.005)

This is categorically different from the old 15×15 SLSQP:
- Old: 225 vars, hard equality constraints, degenerate problem → artifacts
- New: 64 vars, 1 hard constraint, soft penalties, strict bounds → stable