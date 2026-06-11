# Champion Model Selection

**Selection criterion**: Lowest exact-score negative log-likelihood on OOF predictions.

## Ranking by OOF exact-score NLL

| Rank | Model | OOF NLL | RPS | Brier | vs. Equal-Prob baseline |
|------|-------|---------|-----|-------|------------------------|
| 1 | equal_probability | 3.3452 | 0.1565 | 0.6559 |  |
| 2 | elo | 3.4529 | 0.1673 | 0.6878 | +0.1077 (worse) |
| 3 | historical_base_rate | 4.3856 | 0.1602 | 0.6876 | +1.0404 (worse) |
| 4 | negative_binomial | 4.5707 | 0.1851 | 0.7554 | +1.2254 (worse) |
| 5 | dixon_coles | 4.8106 | 0.2047 | 0.8067 | +1.4653 (worse) |
| 6 | poisson | 5.2134 | 0.2059 | 0.8275 | +1.8682 (worse) |

## Champion: equal_probability

Selected by: lowest OOF exact-score NLL

## Notes
- Metrics are on synthetic data; re-run with real BDL data for production champion
- Bayesian models not included in this run (add `--include-bayesian`)
- Market-implied model requires BDL API key
- Final champion will be selected after real data backtest