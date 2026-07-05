# Score PMF Calibration Report

**Generated**: 2026-07-05T04:55:37Z

## Temperature calibration methodology

Temperature scaling: `P_cal(h,a) ∝ P_raw(h,a)^(1/T)`

- T > 1: model is overconfident (sharper than reality), calibration spreads mass
- T < 1: model is underconfident (too diffuse), calibration sharpens mass
- T = 1: no correction needed

**Fitting procedure**: `ScorePMFCalibrator.fit()` is called on OOF predictions
after `WalkForwardEngine.run()`. The optimizer minimizes exact-score negative
log-loss over out-of-fold predictions only (never training data).

**Previous bug**: T=1.000 was reported for all models because `fit()` was never called.
**Status**: FIXED. Fitted T values shown below.

## Fitted temperatures (OOF exact-score NLL optimization)

| Model | N OOF | NLL (T=1) | T (fitted) | Calibration direction |
|-------|-------|-----------|-----------|----------------------|
| pi_rating | 118 | 3.0046 | **1.057** | near-neutral (T close to 1.0) |
| equal_probability | 118 | 3.0219 | **1.077** | near-neutral (T close to 1.0) |
| elo | 118 | 3.1493 | **1.255** | overconfident — calibration spreads probability mass |
| historical_base_rate | 118 | 4.0844 | **0.492** | underconfident — calibration sharpens probability mass |
| negative_binomial | 106 | 4.4369 | **2.923** | overconfident — calibration spreads probability mass |
| dixon_coles | 106 | 4.8542 | **3.000** | overconfident — calibration spreads probability mass |
| bivariate_poisson | 106 | 4.9404 | **3.000** | overconfident — calibration spreads probability mass |
| poisson | 106 | 5.1621 | **3.000** | overconfident — calibration spreads probability mass |
| zero_inflated_poisson | 106 | 5.1658 | **3.000** | overconfident — calibration spreads probability mass |
| weibull_copula | 106 | 6.9650 | **3.000** | overconfident — calibration spreads probability mass |

## Interpretation

Parametric models (NegBin, Dixon-Coles, etc.) show T≈3.0, indicating severe
overconfidence on the exact-score level. This is expected: 128 WC training matches
are insufficient for stable parametric estimation.

The equal_probability baseline (T=1.077) is nearly neutral because Poisson(1.35,1.35)
already represents the diffuse empirical distribution well.

The elo model (T=1.255) is moderately overconfident — it sharpens 1X2 probabilities
without enough data to justify that discrimination.

**Action**: Publish champion is market_reconciled (not any parametric model).
Parametric models serve only as priors for the blend.
As 2026 match results accumulate, T will be re-fitted with more OOF data.

## Calibration slope / intercept (1X2)

| Model | Slope | Intercept | Interpretation |
|-------|-------|-----------|---------------|
| pi_rating | 2.301 | -0.429 | underconfident |
| equal_probability | nan | nan | slightly off |
| elo | 2.277 | -0.114 | underconfident |
| historical_base_rate | -1.596 | 1.151 | overconfident |
| negative_binomial | 0.069 | 0.415 | overconfident |
| dixon_coles | 0.045 | 0.424 | overconfident |
| bivariate_poisson | 0.009 | 0.440 | overconfident |
| poisson | 0.046 | 0.424 | overconfident |
| zero_inflated_poisson | 0.085 | 0.408 | overconfident |
| weibull_copula | 0.092 | 0.403 | overconfident |