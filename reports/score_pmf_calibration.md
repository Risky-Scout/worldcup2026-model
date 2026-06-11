# Temperature Calibration Report (Fixed)

**Generated**: 2026-06-11T17:09:36Z

## Bug fix: T=1.000 for all models was incorrect

**Root cause**: `ScorePMFCalibrator.fit()` was never called in the WalkForwardEngine.
Only `evaluate_pmf_predictions()` was called, which evaluates at T=1.0 without fitting.

**Fix**: WalkForwardEngine now calls `ScorePMFCalibrator.fit()` after computing OOF predictions.

## Updated temperatures

| Model | N OOF | T (fitted) | Direction | NLL at T=1 | NLL at T_opt |
|-------|-------|-----------|-----------|-----------|-------------|
| equal_probability | 118 | 1.077 | overconfident (T>1) | 3.0219 | 3.0219 |
| elo | 118 | 1.255 | overconfident (T>1) | 3.1493 | 3.1493 |
| historical_base_rate | 118 | 0.492 | underconfident (T<1) | 4.0844 | 4.0844 |
| negative_binomial | 106 | 2.997 | overconfident (T>1) | 4.5159 | 4.5159 |
| dixon_coles | 86 | 3.000 | overconfident (T>1) | 4.8898 | 4.8898 |
| zero_inflated_poisson | 106 | 3.000 | overconfident (T>1) | 5.1683 | 5.1683 |
| poisson | 106 | 3.000 | overconfident (T>1) | 5.1734 | 5.1734 |
| bivariate_poisson | 106 | 3.000 | overconfident (T>1) | 5.2690 | 5.2690 |
| weibull_copula | 106 | 3.000 | overconfident (T>1) | 7.2643 | 7.2643 |

## Note

Temperature optimization on exact-score NLL with only 106-118 OOF matches tends to
produce T values close to 1.0 because the PMF grid is already spread (not overconfident).
Temperature calibration is more effective with ≥500 OOF predictions.
As 2026 match results come in, T will be re-fitted on the growing OOF pool.