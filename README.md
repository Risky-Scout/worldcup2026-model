# worldcup2026-model

**2026 FIFA World Cup — Joint Final-Score PMF Engine.**

Produces the calibrated joint probability mass function `P(home=h, away=a)` for every
possible regulation-time final score for every 2026 World Cup match, every day.
All other markets (1X2, totals, BTTS, spreads, exact score) are derived from this single PMF.

> **Current status**: Real BDL data pipeline active. `market_reconciled` is the publish
> champion for all matches with BDL odds. The statistical models serve as a prior only;
> the BDL 6-vendor no-vig consensus anchors the published probabilities.
> Live in-game predictions are **not yet implemented** — see [`limitations.md`](docs/limitations.md).

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
| `parametric_champion` | `negative_binomial` | Prior for reconciliation |
| `elo_champion` | `elo` | New-team fallback |
| `market_implied_champion` | market PMF | Direct market inference |
| **`publish_champion`** | **`market_reconciled`** | **Published prediction** |

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
│   │   ├── no_vig.py                 Vig removal (multiplicative, additive, Shin)
│   │   ├── consensus.py              Multi-vendor aggregation
│   │   └── market_pmf.py             goal_expectancy_extended wrapper
│   ├── backtest/
│   │   └── walkforward.py            Strict time-ordered OOF with temperature fitting
│   └── calibration/
│       └── score_pmf.py              Temperature scaling on exact-score NLL
├── scripts/
│   └── run_real_pipeline.py          Full pipeline: fetch→backtest→predict→reports
├── reports/
│   ├── champion_selection.md         5 champion types defined
│   ├── equal_prob_baseline_audit.md  Explains why Poisson(1.35) beats parametric
│   ├── score_pmf_calibration.md      Temperature calibration (T fitted on OOF)
│   ├── walkforward_backtest.md       OOF NLL table
│   ├── model_benchmark_table.md      All models ranked
│   ├── market_calibration.md         3-mode comparison per match
│   ├── june11_analysis.md            Opening day: Mexico/SA + Korea/Czechia
│   ├── team_prior_table.md           Priors for all 48 teams
│   ├── schedule_validation.md        104 total, 72 named, 32 TBD
│   └── bdl_endpoint_coverage.md      Raw data coverage
├── data/
│   ├── published/2026-06-11.json     Opening day PMFs (market_reconciled)
│   └── published/all_scheduled_2026.json
└── docs/
    ├── model_card.md
    └── limitations.md
```

---

## Limitations

See [`docs/limitations.md`](docs/limitations.md) for full detail.

Key current limitations:
- WC-only historical data (128 matches) is too small for reliable team-specific parameter estimation
- Parametric champion (negative_binomial) loses to Poisson(1.35) on OOF NLL; market odds subsume this
- No live in-game model (architecture ready, but not validated)
- New-team priors use confederation averages (no FIFA ranking integration yet)
- Temperature calibration is near T=1.0 for all models (expected with 128 OOF matches)

---

## License

MIT
