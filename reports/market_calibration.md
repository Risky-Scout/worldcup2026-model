# Market Calibration Report

## Method

Market-implied PMF uses `penaltyblog.models.goal_expectancy_extended`
to simultaneously invert no-vig 1X2 + over/under 2.5 probabilities
into (mu_home, mu_away, rho), then creates a Dixon-Coles grid.

No-vig conversion: `penaltyblog.implied.calculate_implied` (7 methods available).

## Sample market inversion

Input: home_win=45%, draw=27%, away_win=28%, over_2.5=55%, under_2.5=45%

| Parameter | Value |
|-----------|-------|
| mu_home (implied) | 1.6392 |
| mu_away (implied) | 1.2409 |
| rho (implied) | -0.1158 |
| Optimizer success | True |
| Fit error | 0.000000 |

## No-vig methods (penaltyblog.implied)

| Method | Description |
|--------|-------------|
| MULTIPLICATIVE | Proportional margin removal (default) |
| ADDITIVE | Equal absolute removal |
| POWER | Power iteration |
| SHIN | Shin method (accounts for insider trading) |
| DIFFERENTIAL_MARGIN_WEIGHTING | Weights by odds |
| ODDS_RATIO | Odds-ratio method |
| LOGARITHMIC | Logarithmic method |

## BDL data availability

Full market calibration requires BDL API key and `make fetch-bdl`.
Run `wc2026 calibrate` after fetching data to produce calibrated predictions.