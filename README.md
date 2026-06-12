# worldcup2026-model

**2026 FIFA World Cup — Joint Final-Score PMF Engine.**

Produces the calibrated joint probability mass function `P(home=h, away=a)` for every
possible regulation-time final score for every 2026 World Cup match, every day.
All other markets (1X2, totals, BTTS, spreads, exact score) are derived from this single PMF.

> **Current status**: Real BDL data pipeline active. `market_reconciled` is the publish
> champion for all matches with BDL odds. Composite team prior integrates market odds,
> FIFA rankings, qualifying performance, penaltyblog ratings, and confederation strength.
> Live in-game predictions are **implemented and validated** on 64 WC 2022 matches
> (real BDL events, NLL decreasing 3.31→0.40 over 90 minutes).

---

## Core product

For each scheduled 2026 World Cup match, the system produces:

| Output | Description |
|--------|-------------|
| `regulation_score_pmf_grid[h][a]` | Full 15×15 probability grid for regulation time |
| `tail_mass` | Explicit probability mass for scores beyond max_goals=15 |
| `top_scorelines` | Top 20 scorelines by probability |
| `derived_markets` | 1X2, totals (0.5–6.5), BTTS, from the single PMF |
| `market_implied_markets` | Direct BDL no-vig consensus (separate from model) |
| `model_vs_market_differences` | Comparison for auditability |

All probabilities are **regulation-time only** (90 minutes + stoppage time).
Extra time and penalty shootouts are explicitly excluded.

---

## Publish modes

Three modes are computed for every match:

| Mode | Description | Publish? |
|------|-------------|---------|
| `pure_model` | Best statistical model (negative_binomial for known teams, elo_prior_blend for new teams). No odds. | Diagnostics only |
| `market_implied` | Direct BDL no-vig PMF via `goal_expectancy_extended`. | Fallback |
| `market_reconciled` | Market-implied prior + minimum-KL reconciliation using all available BDL constraints (1X2, totals, BTTS, correct-score, spread, DNB). | **Default publish** |

**`publish_champion` = `market_reconciled` when BDL odds are available.**

---

## Champion policy

| Champion | Model | Use |
|----------|-------|-----|
| `diagnostic_champion` | `equal_probability` (Poisson λ=1.35) | Audit only. NOT used for publish. |
| `parametric_champion` | `negative_binomial` | Feeds composite prior |
| `rating_champion` | `composite_rating_pmf` | All-source team prior (market + FIFA + qualifying + Elo + Pi) |
| `market_implied_champion` | market PMF | Direct market inference |
| **`publish_champion`** | **`market_reconciled`** | **Published prediction** |

**Plain Elo is no longer a publish fallback.** Every team's prior combines market-implied
lambdas, FIFA March 2026 rankings, WC 2026 qualifying performance, and penaltyblog ratings.
No team defaults to Elo=1500.

**Why `equal_probability` wins on diagnostic NLL (3.02)**: it is Poisson(λ=1.35, λ=1.35) —
the WC average — not a uniform distribution. It wins on 128-match OOF NLL due to
James-Stein shrinkage (small-sample overfitting of team-specific parameters). It assigns
**identical predictions to all teams** and is useless as a published forecast.

---

## Current real-data metrics (walk-forward OOF on 2018+2022, 128 matches)

| Model | N OOF | NLL | Use |
|-------|-------|-----|-----|
| equal_probability (Poisson λ=1.35) | 118 | 3.0219 | Diagnostic baseline only |
| elo | 118 | 3.1493 | New-team fallback |
| historical_base_rate | 118 | 4.0844 | Diagnostic baseline only |
| **negative_binomial** | 106 | **4.5159** | **Parametric prior** |
| dixon_coles | 86 | 4.8898 | Candidate model |
| zero_inflated_poisson | 106 | 5.1683 | Candidate model |
| poisson | 106 | 5.1734 | Candidate model |

The parametric models (NLL 4.5–7.3) underperform the WC average prior on 128-match OOF
because WC sample size is too small for reliable team-parameter estimation. This is expected
and well-documented. Market odds from 6 BDL vendors subsume this uncertainty.

---

## Data

All data from **[BallDontLie FIFA World Cup API](https://fifa.balldontlie.io)** (2018, 2022, 2026).
GOAT-tier subscription required.

| Table | Rows |
|-------|------|
| matches | 232 (128 completed, 104 scheduled 2026) |
| odds | 315 (6 vendors: fanduel, draftkings, betmgm, betrivers, caesars, fanatics) |
| markets | 37,262 (correct_score, BTTS, total, spread, DNB, double_chance) |
| correct_score_odds | 5,047 rows → used in PMF reconciliation |

---

## Quickstart

```bash
git clone https://github.com/Risky-Scout/worldcup2026-model
cd worldcup2026-model
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

cp .env.example .env
# Add: BDL_API_KEY=your_key_here

# Run full pipeline: fetch → backtest → predict → reports
python scripts/run_real_pipeline.py

# Outputs:
#   data/published/2026-06-11.json         (opening day: Mexico+SA, Korea+Czechia)
#   data/published/all_scheduled_2026.json (72 named matches)
#   reports/                               (all audit reports)
```

---

## Project structure

```
worldcup2026-model/
├── src/wc2026/
│   ├── data/
│   │   ├── providers/bdl.py          BDL API client (rate-limited, paginated, snapshot)
│   │   ├── dataset.py                Normalized parquet tables + markets parsing
│   │   └── storage.py                Versioned data storage
│   ├── models/
│   │   ├── joint_pmf.py              JointScorePMF, FiniteGridPMF, tail handling
│   │   ├── baselines.py              equal_probability, historical_base_rate, elo
│   │   ├── ladder.py                 All 6 penaltyblog goal models
│   │   └── prediction.py             ScorePMFPrediction schema
│   ├── markets/
│   │   ├── exact_score_reconcile.py  THREE PUBLISH MODES + min-KL reconciliation
│   │   ├── core_grid_reconcile.py    CoreGridSLSQPReconciler (8×8, soft constraints)
│   │   ├── no_vig.py                 Vig removal (multiplicative, additive, Shin)
│   │   ├── consensus.py              Multi-vendor aggregation
│   │   ├── market_pmf.py             goal_expectancy_extended wrapper
│   │   ├── edge.py                   Pre-game edge: fair odds, half-Kelly, 90% CI
│   │   └── clv.py                    CLV tracking: closing line value store + summary
│   ├── ratings/
│   │   └── composite.py              CompositeTeamPrior (market + FIFA + qualifying + Elo + Pi + Massey)
│   ├── live/
│   │   ├── state.py                  MatchState, MatchEvent, EventType
│   │   ├── features.py               LiveFeatureVector extraction
│   │   ├── hazard.py                 Non-homogeneous minute-level goal hazard
│   │   ├── predictor.py              LivePMFPredictor (Poisson convolution)
│   │   ├── replay.py                 MatchReplayer (2022 replay, real BDL events)
│   │   └── validation.py             NLL/RPS/Brier metrics + report generation
│   ├── backtest/
│   │   └── walkforward.py            Strict time-ordered OOF with temperature fitting
│   └── calibration/
│       └── score_pmf.py              Temperature scaling on exact-score NLL
├── scripts/
│   ├── run_real_pipeline.py          Full pipeline: fetch→backtest→predict→reports
│   └── daily_update.py               Daily ops: fetch→build→pipeline→CLV→validate
├── reports/
│   ├── champion_selection.md         6 champion types defined
│   ├── composite_rating_methodology.md  CompositeTeamPrior design
│   ├── team_prior_table.md           All 48 teams: FIFA + qualifying + market + Elo
│   ├── core_grid_slsqp_methodology.md   8×8 SLSQP design + prior audit
│   ├── correct_score_reconciliation_audit.md  CS usage per match
│   ├── live_replay_validation.md     Live NLL by checkpoint (0→90 min)
│   ├── production_readiness.md       20 ✅ capabilities, 6 remaining gaps
│   └── ...                          (15 total reports)
├── data/
│   ├── published/2026-06-11.json     Opening day PMFs + edge_report
│   ├── published/all_scheduled_2026.json
│   ├── predictions/live_replay_2022.parquet  640 checkpoints × 64 matches
│   └── clv/2026/records.jsonl        433 CLV records seeded at prediction time
├── .github/workflows/
│   ├── ci.yml                        test + validate-published + validate-live on PR
│   └── daily.yml                     04:00 UTC daily update + auto-commit
├── Dockerfile                        Production image (python:3.10-slim, HEALTHCHECK)
├── docker-compose.yml                wc2026, daily-update, predict services
└── limitations.md
```

---

## Live prediction engine

| Component | Status |
|-----------|--------|
| `MatchState` | Score, clock, cards, subs, xG, momentum |
| `LiveFeatureVector` | Clock, score-state, pregame λ, live performance, cards |
| Non-homogeneous hazard model | Baseline × score-state × red-card multipliers |
| `LivePMFPredictor` | Poisson convolution + temperature scaling |
| `MatchReplayer` | Minute-by-minute 2022 replay (real BDL events, 0 synthetic) |
| Validation | 640 checkpoints × 64 matches — NLL 3.31→0.40 as match progresses |

---

## Pre-game edge screening

Every published JSON includes an `edge_report` with:
- Fair odds (1/model_p) vs market odds (1/market_p)
- Edge % = (model_p − market_p) / market_p
- Half-Kelly bet fraction (capped at 5%)
- 90% CI via ±12% λ perturbation
- Value flag: edge ≥ 4% AND CI lower > market_p AND market_p ≥ 2%

---

## CLV tracking

CLV records seeded at prediction time in `data/clv/2026/records.jsonl`.
After each matchday:
```bash
make post-match DATE=2026-06-11   # record actual outcomes
make clv-summary                   # print beat-close rate and log-score
```

---

## Daily operations

```bash
make update DATE=2026-06-12       # fetch + build + pipeline + validate (~25s)
make post-match DATE=2026-06-11   # record CLV outcomes
make clv-summary                   # print CLV report
make pipeline                      # full run_real_pipeline.py
```

---

## Limitations

See [`limitations.md`](limitations.md) for full detail.

Key current limitations:
- WC-only historical data (128 matches) is too small for reliable team-specific parameter estimation
- Parametric champion (negative_binomial) loses to Poisson(1.35) on OOF NLL; market odds subsume this
- Correct-score reconciliation not walk-forward backtested (no historical CS odds from 2018/2022 BDL)
- Temperature calibration T≈3.0 for parametric models — expected with 128 OOF matches
- Live betting edge screening requires BDL live odds endpoint (not yet available)

---

## License

MIT
