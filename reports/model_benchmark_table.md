# Model Benchmark Table (Real BDL Data)

**Generated**: 2026-06-15T11:39:49Z
**Parametric champion**: negative_binomial (NLL=4.5158)
**Publish champion**: market_reconciled (market_implied as prior)

| Rank | Model | N | NLL | vs. Parametric | RPS | Brier | ECE | T |
|------|-------|---|-----|---------------|-----|-------|-----|---|
| 1 | equal_probability | 118 | 3.0219 | -1.4940 | 0.2382 | 0.6497 | 0.0698 | 1.077 |
| 2 | elo | 118 | 3.1493 | -1.3665 | 0.2673 | 0.7073 | 0.1969 | 1.255 |
| 3 | historical_base_rate | 118 | 4.0844 | -0.4314 | 0.2422 | 0.6734 | 0.0260 | 0.492 |
| 4 | negative_binomial | 106 | 4.5158 | +0.0000 | 0.2951 | 0.7914 | 0.2418 | 2.997 |
| 5 | dixon_coles | 86 | 4.8898 | +0.3740 | 0.2999 | 0.8257 | 0.2690 | 3.000 |
| 6 | bivariate_poisson | 106 | 4.9445 | +0.4287 | 0.3131 | 0.8572 | 0.3161 | 3.000 |
| 7 | poisson | 106 | 5.1645 | +0.6487 | 0.3092 | 0.8450 | 0.3049 | 3.000 |
| 8 | zero_inflated_poisson | 106 | 5.1683 | +0.6525 | 0.3085 | 0.8407 | 0.2706 | 3.000 |
| 9 | weibull_copula | 106 | 6.5069 | +1.9910 | 0.3394 | 0.9113 | 0.3691 | 3.000 |