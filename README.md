# worldcup2026-model

**Elite-calibrated 2026 FIFA World Cup predictive model.**

Produces full scoreline probability distributions — P(home=i, away=j) for every possible final score — for both pre-game and live in-game predictions.

---

## Model Architecture

### Core Ensemble (4 component models)

| Model | Description | Ensemble weight (RPS-derived) |
|---|---|---|
| **Dixon-Coles** | Classic MLE Poisson with low-score correction (τ), time-decay weights, neutral-venue flag | ~40 % |
| **Bayesian Dixon-Coles** | Full MCMC posterior via `emcee`; propagates parameter uncertainty into predictions | ~30 % |
| **Bivariate Poisson** | Allows positive correlation between home and away goals | ~15 % |
| **Weibull Copula** | Heavy-tail goal distribution; best for matches with extreme outcomes | ~15 % |

Ensemble weights are calibrated at runtime via leave-one-out RPS (Ranked Probability Score) on the most recent 20% of training matches and re-derived each time the model is trained.

### Calibration

- **Brier Score** — overall and per 1X2 outcome
- **Log Loss** — both outcome and exact-score
- **RPS** — ordered 1X2 market
- **ECE** — Expected Calibration Error (reliability / over/under confidence)
- Reliability diagrams for all three 1X2 outcomes

### Live Engine

At minute *t* with current score (*g_h*, *g_a*):

1. **Time scaling** — remaining λ = pre-game λ × (90 − t)/90
2. **xG blend** — live accumulated xG is blended in with weight α = min(t/45, 1), so by minute 45 the model fully trusts the in-game xG rate
3. **Momentum adjustment** — per-minute BDL momentum signal (last 5 min avg) adjusts the λ ratio ±20% max
4. **Conditional shift** — P(final) = P(remaining goals shifted by current score)

---

## Data Source

All data is pulled from the **[BallDontLie FIFA World Cup API](https://fifa.balldontlie.io)** (2018, 2022, 2026 seasons). A GOAT-tier subscription ($39.99/mo) is required for full access to match stats, xG, shots, and live endpoints.

Endpoints used:

- `matches` — fixture list, scores, stage info
- `team_match_stats` — per-team xG, shots, possession
- `match_shots` — shot-level xG (2022+)
- `match_momentum` — per-minute attack momentum
- `match_events` — goals, cards, substitutions
- `odds` — bookmaker lines for validation

---

## Quickstart

```bash
# 1. Clone and install
git clone https://github.com/Risky-Scout/worldcup2026-model
cd worldcup2026-model
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

# 2. Set your BDL API key
cp .env.example .env
# Edit .env and add your BDL_API_KEY

# 3. Fetch data (cached to ~/.cache/wc2026/)
wc2026 fetch

# 4. Train the model (saves model.pkl)
wc2026 train

# 5. Pre-game prediction
wc2026 predict "Brazil" "France"

# 6. Live prediction
wc2026 live 42 "Brazil" "France"

# 7. Calibration report
wc2026 calibrate --plot
```

---

## Python API

```python
from dotenv import load_dotenv
load_dotenv()

from wc2026.data import DataFetcher, build_match_dataframe
from wc2026.models import EnsembleModel
from wc2026.predictions import pregame_predict, LivePredictor
from wc2026.calibration import CalibrationReport

# Load data
fetcher = DataFetcher()
matches = fetcher.completed_matches(seasons=[2018, 2022, 2026])
match_ids = [m["id"] for m in matches]
stats = fetcher.team_match_stats(match_ids=match_ids)
shots = fetcher.match_shots(match_ids=match_ids)

df = build_match_dataframe(matches, team_stats=stats, shots=shots)

# Train
model = EnsembleModel.from_dataframe(df, bayesian=True)
model.save("model.pkl")

# Pre-game prediction
grid = model.predict("Brazil", "France")
print(f"Brazil win: {grid.home_win:.1%}")
print(f"Draw:       {grid.draw:.1%}")
print(f"France win: {grid.away_win:.1%}")
print(f"Over 2.5:   {grid.total_goals('over', 2.5):.1%}")
print(f"1-0:        {grid.exact_score(1, 0):.2%}")

# Full scoreline table
print(model.score_probability_table("Brazil", "France"))

# Calibration
report = CalibrationReport(model, holdout_df)
report.evaluate()
print(report)
```

### Live prediction

```python
from wc2026.predictions import LivePredictor

predictor = LivePredictor(model, fetcher)
result = predictor.predict(match_id=42, home_team="Brazil", away_team="France")

print(f"Min {result['minute']}  Score: {result['home_score']}-{result['away_score']}")
print(f"Brazil win now: {result['home_win']:.1%}")
for s in result["top_scores"][:5]:
    print(f"  {s['home_goals']}-{s['away_goals']}: {s['probability']:.2%}")
```

---

## Project Structure

```
worldcup2026-model/
├── src/wc2026/
│   ├── data/
│   │   ├── bdl_client.py       BDL API client (rate-limited, paginated)
│   │   ├── fetcher.py          Disk-cached data layer
│   │   └── preprocessor.py     Match DataFrame + xG feature builder
│   ├── models/
│   │   ├── trainer.py          Fits all 4 component models + weight calibration
│   │   └── ensemble.py         Public prediction interface
│   ├── calibration/
│   │   ├── metrics.py          Brier, RPS, log-loss, ECE
│   │   └── plots.py            Reliability diagrams, score heatmaps
│   ├── predictions/
│   │   ├── pregame.py          Full pre-game prediction dict
│   │   └── live.py             Live in-game prediction engine
│   ├── utils/helpers.py        Odds conversion utilities
│   └── cli.py                  `wc2026` CLI
├── notebooks/                  Exploration & analysis notebooks
├── pyproject.toml
└── .env.example
```

---

## Calibration Notes

World Cup data has a very small sample size (64 matches in 2018/2022, 104 in 2026). To maximise calibration:

- **Time-decay weights** (half-life 180 days) down-weight 2018 data relative to 2022 and 2026
- **Neutral venue flag** is applied to all matches (all WC games are at neutral sites from both teams' perspectives, except host nations USA/CAN/MEX get a soft home advantage)
- **Bayesian posterior** averages over parameter uncertainty — critical when n is small
- **Ensemble weights** are derived from RPS rather than AIC/BIC to directly optimise predictive accuracy

For ongoing tournament calibration, re-run `wc2026 train` after each matchday to incorporate the latest results.

---

## License

MIT
