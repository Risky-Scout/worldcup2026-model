# Score PMF Calibration Report

**Method**: Temperature scaling (T fitted by minimising exact-score NLL on OOF predictions)

| Model | T | Exact-Score NLL (raw) | Calib Slope | ECE | Sharpness |
|-------|---|----------------------|-------------|-----|-----------|
| equal_probability | 1.000 | 3.3452 | nan | 0.0096 | 0.0028 |
| elo | 1.000 | 3.4529 | 1.7895 | 0.1391 | 0.0172 |
| historical_base_rate | 1.000 | 4.3856 | -6.3169 | 0.0749 | 0.0225 |
| negative_binomial | 1.000 | 4.5707 | 0.3320 | 0.1994 | 0.0713 |
| dixon_coles | 1.000 | 4.8106 | 0.0898 | 0.2566 | 0.0675 |
| poisson | 1.000 | 5.2134 | 0.1938 | 0.2629 | 0.0833 |

## Temperature interpretation
- T > 1.0: model is overconfident (sharpens toward uniform)
- T < 1.0: model is underconfident (sharpens toward peak)
- T = 1.0: no correction applied (< 5 OOF matches)

## Calibration slope interpretation
- Ideal: slope = 1.0, intercept = 0.0
- Slope > 1: model overestimates high probabilities
- Slope < 1: model underestimates high probabilities