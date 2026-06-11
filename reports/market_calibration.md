# Market Calibration Report (Real BDL Data)

**Generated**: 2026-06-11T17:09:36Z

## Publish mode distribution

| Mode | Count | Description |
|------|-------|-------------|
| market_reconciled | 72 | Market + model blend (default publish) |
| market_implied | 0 | Pure market PMF, no model |
| pure_model | 0 | Model only, no odds available |

**Matches with correct-score odds**: 72

## Reconciliation method

For each match with BDL odds:
1. Strip vig from 1X2 (multiplicative method, 6 vendors)
2. Strip vig from O/U 0.5–6.5 lines (all available)
3. Strip vig from BTTS, DNB, double chance where available
4. Build market_implied PMF via `penaltyblog.goal_expectancy_extended`
5. Parse correct-score outcomes (type=correct_score, period=match)
6. Apply minimum-KL reconciliation with correct-score constraints
7. Blend: α × market_implied + (1-α) × pure_model

Market quality score (0-1) determines α:
- 6 vendors + correct score → quality ≈ 0.82 → α ≈ 0.82
- 6 vendors, no correct score → quality ≈ 0.62 → α ≈ 0.62

## Vendors
fanduel, draftkings, betmgm, betrivers, caesars, fanatics (315 total rows)

## Mexico vs South Africa — Three modes

| Mode | HW | D | AW | Over2.5 | expG home | expG away |
|------|----|----|-----|---------|----------|----------|
| pure_model (elo_prior_blend) | 0.23358 | 0.28798 | 0.47844 | 0.39306 | 0.8739 | 1.3831 |
| market_implied | 0.67508 | 0.21113 | 0.11378 | 0.44026 | 1.8413 | 0.5973 |
| **market_reconciled (PUBLISHED)** | **0.67508** | **0.21113** | **0.11378** | **?** | **1.8987** | **0.781** |

## South Korea vs Czechia — Three modes

| Mode | HW | D | AW | Over2.5 | expG home | expG away |
|------|----|----|-----|---------|----------|----------|
| pure_model (elo_prior_blend) | 0.26488 | 0.27056 | 0.46457 | 0.47474 | 1.0675 | 1.504 |
| market_implied | 0.36171 | 0.31403 | 0.32426 | 0.42274 | 1.2253 | 1.1459 |
| **market_reconciled (PUBLISHED)** | **0.36172** | **0.31401** | **0.32426** | **?** | **1.1356** | **1.4235** |