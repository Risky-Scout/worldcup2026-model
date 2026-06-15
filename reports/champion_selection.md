# Champion Policy (Real BDL Data)

**Generated**: 2026-06-15T01:18:13Z

## Six champion tiers

| Champion Type | Model | NLL | Use Case |
|--------------|-------|-----|----------|
| diagnostic_champion | equal_probability | 3.0219 | Audit only — NEVER published |
| pure_model_champion | negative_binomial | 4.515852072380328 | Parametric model for matches without odds |
| rating_champion | negative_binomial | composite_rating_pmf | Market-implied priors for all 48 teams |
| parametric_champion | negative_binomial | 4.5159 | Alias for pure_model — parametric prior |
| market_champion | market_implied | N/A | Pure-market PMF from BDL consensus |
| **publish_champion** | **market_reconciled** | **N/A** | **Default publish when BDL odds exist** |

**Note**: Plain Elo is NOT a champion tier. It is a diagnostic baseline only.
New teams (no 2018/2022 WC history) use composite_rating_pmf, not Elo=1500.

## Why diagnostic_champion ≠ publish_champion

**equal_probability** wins on exact-score NLL (3.0219) because:
- It is **Poisson(λ=1.35, λ=1.35)** — the WC average goals prior — NOT uniform over all cells
- With only 128 historical WC matches and 32+ teams, James-Stein shrinkage toward the mean
  outperforms team-specific parameter estimation (classic small-sample overfitting)
- It CAN predict any score (never assigns zero probability)
- However, it assigns **identical probabilities** to all teams (no team discrimination)
- It is useless as a published prediction: Brazil = South Africa = every team

**publish_champion = market_reconciled** because:
- BDL provides 6-vendor odds with correct-score markets
- Market probabilities incorporate team quality, current form, injuries, etc.
- The model provides the PMF shape and structural constraints
- market_reconciled is the most calibrated PMF available for each match

## Publish mode selection

| BDL data available | Publish mode |
|-------------------|-------------|
| 6 vendors + correct score | market_reconciled (α≈0.82) |
| 6 vendors, no correct score | market_reconciled (α≈0.62) |
| Partial odds (< min_quality) | market_implied |
| No odds | composite_rating_pmf (market-implied priors for all 48 teams) |
| New teams, no WC history | composite_rating_pmf (NOT elo_prior_blend) |

## OOF ranking (all models)

| Rank | Model | N OOF | NLL | RPS | Brier | ECE | T | Publish-eligible? |
|------|-------|-------|-----|-----|-------|-----|---|------------------|
| 1 | equal_probability | 118 | 3.0219 | 0.2382 | 0.6497 | 0.0698 | 1.077 | diagnostic only |
| 2 | elo | 118 | 3.1493 | 0.2673 | 0.7073 | 0.1969 | 1.255 | diagnostic only |
| 3 | historical_base_rate | 118 | 4.0844 | 0.2422 | 0.6734 | 0.0260 | 0.492 | diagnostic only |
| 4 | negative_binomial | 106 | 4.5159 | 0.2951 | 0.7914 | 0.2418 | 2.997 | parametric prior |
| 5 | dixon_coles | 86 | 4.8898 | 0.2999 | 0.8257 | 0.2690 | 3.000 | parametric prior |
| 6 | bivariate_poisson | 106 | 4.9446 | 0.3131 | 0.8572 | 0.3161 | 3.000 | parametric prior |
| 7 | poisson | 106 | 5.1645 | 0.3092 | 0.8450 | 0.3049 | 3.000 | parametric prior |
| 8 | zero_inflated_poisson | 106 | 5.1683 | 0.3085 | 0.8407 | 0.2706 | 3.000 | parametric prior |
| 9 | weibull_copula | 106 | 6.4900 | 0.3415 | 0.9052 | 0.3670 | 3.000 | parametric prior |