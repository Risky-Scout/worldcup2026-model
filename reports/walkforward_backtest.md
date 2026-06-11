# Walk-Forward Backtest Report (Real BDL Data)

**Generated**: 2026-06-11T16:08:25Z
**Training data**: 2018 (64 matches) + 2022 (64 matches) = 128 total
**Method**: Strict time-ordered out-of-fold — train only on matches BEFORE prediction date
**Minimum training matches**: 10
**Refit every**: 4 matches

## Results by model

| Model | N OOF | Exact-Score NLL | 1X2 RPS | 1X2 Brier | ECE | Calib Slope | T |
|-------|-------|----------------|---------|-----------|-----|-------------|---|
| equal_probability            |   118 |         3.0219 |  0.1588 |    0.6497 | 0.0698 |         nan | 1.000 |
| elo                          |   118 |         3.1493 |  0.1782 |    0.7073 | 0.1969 |      2.2766 | 1.000 |
| historical_base_rate         |   118 |         4.0844 |  0.1615 |    0.6734 | 0.0260 |     -1.5960 | 1.000 |
| negative_binomial            |   106 |         4.5159 |  0.1967 |    0.7914 | 0.2418 |      0.0580 | 1.000 |
| dixon_coles                  |    86 |         4.8898 |  0.2000 |    0.8257 | 0.2690 |      0.0028 | 1.000 |
| zero_inflated_poisson        |   106 |         5.1683 |  0.2057 |    0.8407 | 0.2706 |      0.0832 | 1.000 |
| poisson                      |   106 |         5.1734 |  0.2058 |    0.8440 | 0.2974 |      0.0437 | 1.000 |
| bivariate_poisson            |   106 |         5.2690 |  0.2237 |    0.8959 | 0.3447 |     -0.0159 | 1.000 |
| weibull_copula               |   106 |         7.1012 |  0.2217 |    0.8691 | 0.3436 |      0.0773 | 1.000 |

## Champion: **equal_probability**

- OOF exact-score NLL: **3.0219**
- OOF 1X2 RPS: 0.1588
- OOF Brier: 0.6497
- ECE: 0.0698
- Temperature: 1.000 (well-calibrated)
- N OOF predictions: 118

## Leakage controls

- No training data contamination: models only see matches before prediction date
- No closing odds used in pregame prediction mode
- No post-match xG or stats used as features
- Walk-forward engine verified by `tests/test_walkforward.py`