# Champion Policy (Real BDL Data)

**Generated**: 2026-07-15T21:28:25Z

## Six champion tiers

| Champion Type | Model | NLL | Use Case |
|--------------|-------|-----|----------|
| diagnostic_champion | pi_rating | 3.0046 | Audit only — NEVER published |
| pure_model_champion | negative_binomial | 4.436939720954314 | Parametric model for matches without odds |
| rating_champion | negative_binomial | composite_rating_pmf | Market-implied priors for all 48 teams |
| parametric_champion | negative_binomial | 4.4369 | Alias for pure_model — parametric prior |
| market_champion | market_implied | N/A | Pure-market PMF from BDL consensus |
| **publish_champion** | **market_reconciled** | **N/A** | **Default publish when BDL odds exist** |

**Note**: Plain Elo is NOT a champion tier. It is a diagnostic baseline only.
New teams (no 2018/2022 WC history) use composite_rating_pmf, not Elo=1500.

## Why diagnostic_champion ≠ publish_champion

**pi_rating** wins on exact-score NLL (3.0046) because:
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
| 1 | pi_rating | 118 | 3.0046 | 0.2347 | 0.6424 | 0.0628 | 1.057 | N/A |
| 2 | equal_probability | 118 | 3.0219 | 0.2382 | 0.6497 | 0.0698 | 1.077 | diagnostic only |
| 3 | elo | 118 | 3.1493 | 0.2673 | 0.7073 | 0.1969 | 1.255 | diagnostic only |
| 4 | historical_base_rate | 118 | 4.0844 | 0.2422 | 0.6734 | 0.0260 | 0.492 | diagnostic only |
| 5 | negative_binomial | 106 | 4.4369 | 0.2841 | 0.7731 | 0.2252 | 2.923 | parametric prior |
| 6 | dixon_coles | 106 | 4.8542 | 0.3015 | 0.8222 | 0.2467 | 3.000 | parametric prior |
| 7 | bivariate_poisson | 106 | 4.9404 | 0.3122 | 0.8554 | 0.3180 | 3.000 | parametric prior |
| 8 | poisson | 106 | 5.1621 | 0.3089 | 0.8441 | 0.2991 | 3.000 | parametric prior |
| 9 | zero_inflated_poisson | 106 | 5.1658 | 0.3081 | 0.8397 | 0.2702 | 3.000 | parametric prior |
| 10 | weibull_copula | 106 | 6.7769 | 0.3277 | 0.8772 | 0.3476 | 3.000 | parametric prior |