# Model Card — wc2026 PMF Engine

**Version**: 0.5.0
**Date**: 2026-06-11
**Status**: Pre-game PMF ready. Live engine validated. Market-reconciled publish champion.
Pre-game probabilities and edge screening operational. Live betting requires live-odds API.

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
| elo | 3.15 | Diagnostic baseline (no longer used as publish fallback) |
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

## Team priors (CompositeTeamPrior)

For each of the 48 named WC teams, the prior blends:

| Source | Weight (with market odds) | Weight (no market odds) |
|--------|--------------------------|------------------------|
| Market-implied (BDL 3 group matches × 6 vendors) | 0.60 | — |
| FIFA March 2026 ranking points | 0.12 | 0.30 |
| WC 2026 qualifying goals/game | 0.10 | 0.25 |
| penaltyblog Pi rating | ~0.08 | ~0.20 |
| penaltyblog Elo | ~0.05 | ~0.15 |
| penaltyblog Massey | ~0.03 | ~0.07 |
| Confederation baseline | 0.02 (floor) | 0.03 (floor) |

No team defaults to Elo=1500. All 48 teams have FIFA ranking and qualifying data.

---

## Training data

- **Source**: BallDontLie FIFA World Cup API
- **Seasons**: 2018, 2022 (completed), 2026 (scheduled)
- **Matches used for training**: 128 completed matches (2018+2022)
- **Match features**: team identity, neutral venue, composite prior
- **External priors**: FIFA rankings, qualifying performance, confederation strength, host bonus

**NOT used for training**: xG, shots, lineup data (architecture ready, not integrated into fitting)

---

## Calibration

- **Method**: Strict time-ordered walk-forward OOF
- **Temperature scaling**: Fitted on OOF exact-score NLL. T=1.077 (equal_prob) to 3.000 (parametric)
- **Market calibration**: 6-vendor no-vig via multiplicative vig removal; `goal_expectancy_extended` for market PMF inference; 8×8 SLSQP core-grid or linear blend for market reconciliation; minimum-KL with correct-score constraints

---

## Live prediction engine

- **Architecture**: Non-homogeneous minute-level hazard × score-state × red-card multipliers
- **Validation**: 64 WC 2022 matches replayed minute-by-minute with real BDL events
- **NLL by checkpoint**: 3.31 (min 0) → 2.49 (HT) → 1.20 (min 85) → 0.40 (min 90)
- **Output**: `LivePMFResult` — regulation outcome PMF, next-goal, no-more-goals, BTTS, O/U

---

## Edge screening

Every published prediction includes `edge_report`:
- Fair odds, market odds, edge%, half-Kelly (capped 5%), 90% CI
- Value flag: edge ≥ 4% AND CI lower > market AND market ≥ 2%

---

## Known limitations

1. **Small WC-only training set**: 128 matches — parametric models underperform Poisson(1.35)
2. **Correct-score reconciliation not backtested**: No historical CS odds in BDL 2018/2022
3. **Temperature T≈3.0 for parametric**: Expected; will improve as 2026 results accumulate
4. **No live-odds integration**: Live betting edge requires BDL live-odds endpoint
5. **Opening vs. closing line drift not tracked**: Daily BDL snapshots needed

See `limitations.md` for the complete list.

---

## Intended use

- Pre-game joint final-score PMF for 2026 World Cup matches
- Market comparison, calibration diagnostics, edge screening
- Live in-game probability updates (regulation time only)
- CLV tracking for model validation against closing lines

**NOT intended for**: autonomous betting without human oversight; post-match forensics as pregame inputs
