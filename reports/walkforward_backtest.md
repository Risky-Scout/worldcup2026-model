# Walk-Forward Backtest (Real BDL Data)

**Generated**: 2026-07-01T02:42:33Z
**Training data**: 2018 (64) + 2022 (64) = 128 total
**Method**: Strict time-ordered OOF — train only on matches before prediction date

**Primary metric**: 1X2 Log Loss (Ignorance Score) — penaltyblog's recommended
scoring rule (proven optimal at 25 matches; 70.4% correct model ID vs 67.7% RPS).
**Secondary metrics**: RPS (diagnostic), Multiclass Brier (diagnostic).

## Results

| Model | N OOF | 1X2_LogLoss | 1X2_Brier_Multi | RPS | NLL | ECE | T | Publish? |
|-------|-------|------------|-----------------|-----|-----|-----|---|---------|
| pi_rating | 118 | 1.5323 | 0.6424 | 0.2347 | 3.0046 | 0.0628 | 1.057 | elo fallback |
| equal_probability | 118 | 1.5460 | 0.6497 | 0.2382 | 3.0219 | 0.0698 | 1.077 | diagnostic only |
| historical_base_rate | 118 | 1.6468 | 0.6734 | 0.2422 | 4.0844 | 0.0260 | 0.492 | diagnostic only |
| elo | 118 | 1.6653 | 0.7073 | 0.2673 | 3.1493 | 0.1969 | 1.255 | diagnostic only |
| negative_binomial | 106 | 2.3102 | 0.7731 | 0.2841 | 4.4369 | 0.2252 | 2.923 | parametric prior |
| dixon_coles | 106 | 2.5551 | 0.8222 | 0.3015 | 4.8542 | 0.2467 | 3.000 | parametric prior |
| zero_inflated_poisson | 106 | 2.7635 | 0.8397 | 0.3081 | 5.1658 | 0.2702 | 3.000 | parametric prior |
| poisson | 106 | 2.7671 | 0.8441 | 0.3089 | 5.1621 | 0.2991 | 3.000 | parametric prior |
| weibull_copula | 106 | 2.9547 | 0.8965 | 0.3362 | 7.1519 | 0.3571 | 3.000 | parametric prior |
| bivariate_poisson | 106 | 3.0932 | 0.8554 | 0.3122 | 4.9404 | 0.3180 | 3.000 | parametric prior |