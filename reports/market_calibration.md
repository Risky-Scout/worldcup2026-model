# Market Calibration Report (Real BDL Data)

**Generated**: 2026-06-11T16:08:25Z

## Market coverage (2026 predictions)

| Metric | Value |
|--------|-------|
| 2026 predictions generated | 88 |
| Matches with 1X2 odds | 72 |
| Matches with correct-score odds | 72 |
| Mean vendors per match | 4.4 |
| Min vendors per match | 3 |
| Max vendors per match | 6 |

## Vig removal method

Using `penaltyblog.implied.calculate_implied` MULTIPLICATIVE method (default).
All 7 methods available: multiplicative, additive, power, Shin, differential_margin_weighting, odds_ratio, logarithmic.

## Market PMF construction

1. Strip vig from BDL 1X2 odds (penaltyblog.implied, multiplicative)
2. Strip vig from O/U 2.5 odds
3. Call `penaltyblog.goal_expectancy_extended(hw, dr, aw, ov25, un25)` → (μ_h, μ_a, ρ)
4. `create_dixon_coles_grid(μ_h, μ_a, ρ)` → full joint PMF
5. Correct-score odds also available per match for additional calibration

## Stale odds detection

Odds rows include `updated_at` timestamp. Odds older than 24h before match kickoff
are flagged as stale in the prediction JSON `warnings[]` field.

## Model vs market comparison

For each 2026 prediction, `model_vs_market_differences` shows signed edge.
Positive = model higher than market. Negative = market higher than model.

## Sample: Mexico vs South Africa

| Market | Model | Market-Implied | Edge |
|--------|-------|---------------|------|
| Home win | 0.2350 | 0.675083 | -0.4401 |
| Draw | 0.2435 | 0.211134 | 0.0323 |
| Away win | 0.5216 | 0.113783 | 0.4078 |
| Over 2.5 | 0.5064 | 0.440258 | 0.0661 |
| Vendors used | 6 | | |