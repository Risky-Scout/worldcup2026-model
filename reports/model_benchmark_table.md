# Model Benchmark Table (Real BDL Data)

**Generated**: 2026-06-13T16:03:23Z
**Parametric champion**: negative_binomial (NLL=4.5159)
**Publish champion**: market_reconciled (market_implied as prior)

| Rank | Model | N | NLL | vs. Parametric | RPS | Brier | ECE | T |
|------|-------|---|-----|---------------|-----|-------|-----|---|
| 1 | equal_probability | 118 | 3.0219 | -1.4940 | 0.1588 | 0.6497 | 0.0698 | 1.077 |
| 2 | elo | 118 | 3.1493 | -1.3665 | 0.1782 | 0.7073 | 0.1969 | 1.255 |
| 3 | historical_base_rate | 118 | 4.0844 | -0.4314 | 0.1615 | 0.6734 | 0.0260 | 0.492 |
| 4 | negative_binomial | 106 | 4.5159 | +0.0000 | 0.1967 | 0.7914 | 0.2418 | 2.997 |
| 5 | dixon_coles | 86 | 4.8898 | +0.3740 | 0.2000 | 0.8257 | 0.2690 | 3.000 |
| 6 | bivariate_poisson | 106 | 4.9446 | +0.4287 | 0.2088 | 0.8572 | 0.3161 | 3.000 |
| 7 | poisson | 106 | 5.1645 | +0.6486 | 0.2061 | 0.8450 | 0.3049 | 3.000 |
| 8 | zero_inflated_poisson | 106 | 5.1683 | +0.6525 | 0.2057 | 0.8407 | 0.2706 | 3.000 |
| 9 | weibull_copula | 106 | 6.5785 | +2.0626 | 0.2173 | 0.8847 | 0.3381 | 3.000 |