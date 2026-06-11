# Model Benchmark Table

**Source**: Walk-forward OOF backtest on synthetic WC-scale data (128 matches, 2018+2022 structure)
**Note**: Replace with `make backtest` on real BDL data for production metrics.

| Model | N OOF | Exact-Score NLL | 1X2 RPS | 1X2 Brier | ECE | Calib Slope |
|-------|-------|----------------|---------|-----------|-----|-------------|
| equal_probability              |   113 |         3.3452 |  0.1565 |    0.6559 | 0.0096 |         nan |
| elo                            |   113 |         3.4529 |  0.1673 |    0.6878 | 0.1391 |      1.7895 |
| historical_base_rate           |   113 |         4.3856 |  0.1602 |    0.6876 | 0.0749 |     -6.3169 |
| negative_binomial              |   102 |         4.5707 |  0.1851 |    0.7554 | 0.1994 |      0.3320 |
| dixon_coles                    |    60 |         4.8106 |  0.2047 |    0.8067 | 0.2566 |      0.0898 |
| poisson                        |   102 |         5.2134 |  0.2059 |    0.8275 | 0.2629 |      0.1938 |

## Notes
- Metrics are computed on OUT-OF-FOLD predictions only (no training data)
- Champion model selected by lowest Exact-Score NLL
- Bayesian models excluded from this run (use `--include-bayesian` to include)
- Market-implied model not run (requires BDL_API_KEY)