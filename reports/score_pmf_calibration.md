# Score PMF Calibration Report (Real BDL Data)

**Generated**: 2026-06-11T16:08:25Z
**Calibration method**: Temperature scaling T fitted on OOF exact-score log loss
**Primary metric**: Exact-score negative log likelihood (lower is better)

| Model | T | OOF NLL | Calib Slope | ECE | Sharpness | Overconfident? |
|-------|---|---------|-------------|-----|-----------|----------------|
| equal_probability | 1.000 | 3.0219 | nan | 0.0698 | 0.0028 | Neutral |
| elo | 1.000 | 3.1493 | 2.2766 | 0.1969 | 0.0167 | Neutral |
| historical_base_rate | 1.000 | 4.0844 | -1.5960 | 0.0260 | 0.0251 | Neutral |
| negative_binomial | 1.000 | 4.5159 | 0.0580 | 0.2418 | 0.0631 | Neutral |
| dixon_coles | 1.000 | 4.8898 | 0.0028 | 0.2690 | 0.0650 | Neutral |
| zero_inflated_poisson | 1.000 | 5.1683 | 0.0832 | 0.2706 | 0.0761 | Neutral |
| poisson | 1.000 | 5.1734 | 0.0437 | 0.2974 | 0.0769 | Neutral |
| bivariate_poisson | 1.000 | 5.2690 | -0.0159 | 0.3447 | 0.0970 | Neutral |
| weibull_copula | 1.000 | 7.1012 | 0.0773 | 0.3436 | 0.0928 | Neutral |

## Interpretation
- T > 1: model overconfident (sharpened to uniform to improve NLL)
- T < 1: model underconfident (sharpened toward mode)
- Calibration slope ≈ 1.0, intercept ≈ 0.0 = perfectly calibrated
- ECE < 0.05 = well-calibrated expected calibration error