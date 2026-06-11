# Market Calibration Report (Real BDL Data)

**Generated**: 2026-06-11T20:06:56Z

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
| composite (composite_rating_pmf) | 0.37319 | 0.26523 | 0.36158 | ? | 1.4083 | 1.3822 |
| market_implied | 0.67508 | 0.21113 | 0.11378 | 0.44026 | 1.8413 | 0.5973 |
| **market_reconciled (PUBLISHED)** | **0.67508** | **0.21113** | **0.11378** | **?** | **1.8987** | **0.781** |

## South Korea vs Czechia — Three modes

| Mode | HW | D | AW | Over2.5 | expG home | expG away |
|------|----|----|-----|---------|----------|----------|
| composite (composite_rating_pmf) | 0.36926 | 0.27891 | 0.35183 | ? | 1.299 | 1.2612 |
| market_implied | 0.36171 | 0.31403 | 0.32426 | 0.42274 | 1.2253 | 1.1459 |
| **market_reconciled (PUBLISHED)** | **0.36172** | **0.31401** | **0.32426** | **?** | **1.1356** | **1.4235** |