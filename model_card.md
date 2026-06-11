# Model Card — wc2026 PMF Engine

**Version**: 0.3.0
**Date**: 2026-06-11
**Status**: Real BDL data pipeline active. Market-reconciled publish champion. NOT yet suitable for public publication as a standalone prediction tool.

---

## What this model does

Produces `P(home_goals=h, away_goals=a)` — the joint final-score probability mass function —
for every scheduled 2026 World Cup match, every day.

All other markets (1X2, totals, BTTS, exact score, spread) are derived from this single PMF.

Prediction is for **regulation time only** (90 minutes + stoppage time).
Extra time and penalty shootouts are handled separately and are NOT mixed into this PMF.

---

## Publish champion

**`market_reconciled`** is the default publish mode when BDL odds are available.

This means the published PMF is anchored to the 6-vendor BDL no-vig consensus, not the statistical model. The model serves as a prior that shapes the PMF grid; the market consensus determines the 1X2 probabilities.

| Publish mode | When used |
|-------------|-----------|
| `market_reconciled` | BDL odds available (72 of 72 named group-stage matches) |
| `market_implied` | Partial odds only |
| `pure_model` | No odds (diagnostic, or post-tournament simulation) |

---

## Statistical models

All 6 penaltyblog goal models are fitted on 2018+2022 WC data (128 completed matches) via strict time-ordered walk-forward OOF:

| Model | OOF NLL | Role |
|-------|---------|------|
| equal_probability (Poisson λ=1.35) | 3.02 | **Diagnostic baseline only** — NOT used for publish |
| elo | 3.15 | New-team fallback |
| historical_base_rate | 4.08 | Diagnostic baseline only |
| **negative_binomial** | **4.52** | **Parametric prior** (best among parametric models) |
| dixon_coles | 4.89 | Candidate |
| zero_inflated_poisson | 5.17 | Candidate |
| poisson | 5.17 | Candidate |

**Why `equal_probability` has the lowest NLL**: It is Poisson(λ=1.35, λ=1.35) — the WC
average goals prior. With 128 matches and 32+ teams, shrinking to the global mean
outperforms team-specific MLE (James-Stein effect). It assigns identical predictions
to all teams and is useless for published forecasts.

The real publish champion uses 6-vendor BDL odds, not the parametric NLL ranking.

---

## Training data

- **Source**: BallDontLie FIFA World Cup API
- **Seasons**: 2018, 2022 (completed), 2026 (scheduled)
- **Matches used for training**: 128 completed matches (2018+2022)
- **Match features**: team identity, neutral venue
- **External priors**: confederation average attack lambdas for teams with no WC history

**NOT used**: xG, shots, lineup data (architecture ready, not yet integrated into model fitting)

---

## Calibration

- **Method**: Strict time-ordered walk-forward OOF
- **Temperature scaling**: Fitted on OOF exact-score NLL. Currently T≈1.0–1.26 (near-neutral) because 128 OOF matches is too few for reliable temperature signal
- **Market calibration**: 6-vendor no-vig via multiplicative vig removal; `goal_expectancy_extended` for market PMF inference; minimum-KL reconciliation for correct-score constraints

---

## Known limitations

1. **Small WC-only training set**: 128 matches, 32+ teams — insufficient for reliable team-specific parameter estimation
2. **No FIFA ranking integration**: New teams use confederation averages
3. **No live model**: Architecture exists but is not validated
4. **Temperature calibration near 1.0**: Expected with 128 OOF matches; will improve as 2026 results accumulate
5. **Correct-score odds are available** (5,047 rows) and used in KL reconciliation
6. **No opening-line vs. closing-line separation** yet (current BDL snapshot is used)

See `limitations.md` for the complete list.

---

## Intended use

- Pre-game joint final-score PMF for 2026 World Cup matches
- Market comparison and calibration diagnostics
- Research into small-sample Bayesian calibration for soccer

**NOT intended for**: autonomous betting without additional human oversight; live in-game use
