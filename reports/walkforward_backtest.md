# Walk-Forward Backtest (Real BDL Data)

**Generated**: 2026-06-14T08:59:35Z
**Training data**: 2018 (64) + 2022 (64) = 128 total
**Method**: Strict time-ordered OOF — train only on matches before prediction date

## Results

| Model | N OOF | NLL | RPS | Brier | ECE | T | Publish? |
|-------|-------|-----|-----|-------|-----|---|---------|
| equal_probability | 118 | 3.0219 | 0.1588 | 0.6497 | 0.0698 | 1.077 | diagnostic only |
| elo | 118 | 3.1493 | 0.1782 | 0.7073 | 0.1969 | 1.255 | diagnostic only |
| historical_base_rate | 118 | 4.0844 | 0.1615 | 0.6734 | 0.0260 | 0.492 | diagnostic only |
| negative_binomial | 106 | 4.5158 | 0.1967 | 0.7914 | 0.2418 | 2.997 | parametric prior |
| dixon_coles | 86 | 4.8898 | 0.2000 | 0.8257 | 0.2690 | 3.000 | parametric prior |
| bivariate_poisson | 106 | 4.9445 | 0.2088 | 0.8572 | 0.3161 | 3.000 | parametric prior |
| poisson | 106 | 5.1645 | 0.2061 | 0.8450 | 0.3049 | 3.000 | parametric prior |
| zero_inflated_poisson | 106 | 5.1683 | 0.2057 | 0.8407 | 0.2706 | 3.000 | parametric prior |
| weibull_copula | 106 | 6.4589 | 0.2141 | 0.8695 | 0.3409 | 3.000 | parametric prior |