# Model Card — wc2026 PMF Engine

**Version**: 0.2.0  
**Date**: 2026-06-11  
**Model version**: v1

---

## Purpose

This model produces calibrated exact-score probability mass functions (PMFs) for every 2026 FIFA World Cup match. The PMF represents 90-minute regulation time + stoppage time. All derived markets (1X2, totals, BTTS, handicap, double chance) are computed deterministically from the PMF — never separately.

---

## Model ladder

| Tier | Model | Implementation | Status |
|------|-------|----------------|--------|
| Naive | Equal Probability | Custom Poisson (λ=1.35 for both) | Baseline |
| Naive | Historical Base Rate | Empirical WC score distribution + Laplace smoothing | Baseline |
| Naive | Elo Baseline | penaltyblog.ratings.Elo | Baseline |
| Tier 1 | Poisson | penaltyblog.models.PoissonGoalsModel | Training |
| Tier 1 | Dixon-Coles | penaltyblog.models.DixonColesGoalModel | **Champion (default)** |
| Tier 1 | Bivariate Poisson | penaltyblog.models.BivariatePoissonGoalModel | Training |
| Tier 1 | Weibull Copula | penaltyblog.models.WeibullCopulaGoalsModel | Training |
| Tier 1 | Negative Binomial | penaltyblog.models.NegativeBinomialGoalModel | Training |
| Tier 1 | Zero-Inflated Poisson | penaltyblog.models.ZeroInflatedPoissonGoalsModel | Training |
| Tier 2 | Bayesian | penaltyblog.models.BayesianGoalModel | Optional (slow) |
| Tier 2 | Hierarchical Bayesian | penaltyblog.models.HierarchicalBayesianGoalModel | Optional (slow) |
| Market | Market-implied | BDL odds + penaltyblog.implied + KL reconciliation | Live |

---

## Champion selection

The champion model is selected by lowest exact-score log loss on **out-of-fold walk-forward predictions only**. No in-sample weighting. Until the OOF backtest has been run, Dixon-Coles is the default champion (well-validated in literature for low-scoring sports).

---

## Calibration pipeline

1. Time-decay weights: `exp(-xi * days_elapsed)`, `xi = 0.0038/day` (≈ 6-month half-life)
2. Walk-forward OOF predictions on 2018 + 2022 World Cup data
3. Temperature scaling: `p_cal ∝ p_raw^(1/T)`, T fitted to minimise exact-score log loss
4. Market reconciliation: KL-divergence minimisation subject to BDL consensus market constraints

---

## Features used (pregame, no leakage)

- Team attack/defense strength (from goal model parameters)
- Elo ratings (updated in walk-forward order)
- Confederation, neutral venue flag
- Tournament stage
- BDL time-decay match weights
- Market-implied prior (from BDL opening/current odds, not closing)

---

## Known limitations

See `limitations.md`.

---

## Data

See `data_card.md`.
