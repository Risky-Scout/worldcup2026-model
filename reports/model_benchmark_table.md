# Model Benchmark Table (Real BDL Data)

**Generated**: 2026-06-23T21:57:08Z
**Parametric champion**: negative_binomial (NLL=4.4369)
**Publish champion**: market_reconciled (market_implied as prior)

| Rank | Model | N | NLL | vs. Parametric | RPS | Brier | ECE | T |
|------|-------|---|-----|---------------|-----|-------|-----|---|
| 1 | pi_rating | 118 | 3.0046 | -1.4324 | 0.2347 | 0.6424 | 0.0628 | 1.057 |
| 2 | equal_probability | 118 | 3.0219 | -1.4151 | 0.2382 | 0.6497 | 0.0698 | 1.077 |
| 3 | elo | 118 | 3.1493 | -1.2876 | 0.2673 | 0.7073 | 0.1969 | 1.255 |
| 4 | historical_base_rate | 118 | 4.0844 | -0.3525 | 0.2422 | 0.6734 | 0.0260 | 0.492 |
| 5 | negative_binomial | 106 | 4.4369 | +0.0000 | 0.2841 | 0.7731 | 0.2252 | 2.923 |
| 6 | dixon_coles | 106 | 4.8542 | +0.4172 | 0.3015 | 0.8222 | 0.2467 | 3.000 |
| 7 | bivariate_poisson | 106 | 4.9404 | +0.5034 | 0.3122 | 0.8554 | 0.3180 | 3.000 |
| 8 | poisson | 106 | 5.1621 | +0.7252 | 0.3089 | 0.8441 | 0.2991 | 3.000 |
| 9 | zero_inflated_poisson | 106 | 5.1658 | +0.7288 | 0.3081 | 0.8397 | 0.2702 | 3.000 |
| 10 | weibull_copula | 106 | 6.6677 | +2.2308 | 0.3252 | 0.8793 | 0.3619 | 3.000 |