# penaltyblog 1.11.0 API Surface

Inspected: 2026-06-11  
Python: 3.10 (`/opt/homebrew/bin/python3.10`)  
Package path: `/opt/homebrew/lib/python3.10/site-packages/penaltyblog`

---

## Available modules

### `penaltyblog.models`

| Class | Available | Notes |
|---|---|---|
| `PoissonGoalsModel` | YES | Standard independent Poisson |
| `DixonColesGoalModel` | YES | Low-score τ correction, weights, neutral_venue |
| `BivariatePoissonGoalModel` | YES | Correlated goals, weights |
| `WeibullCopulaGoalsModel` | YES | Heavy-tail, weights |
| `NegativeBinomialGoalModel` | YES | Overdispersion, weights, neutral_venue |
| `ZeroInflatedPoissonGoalsModel` | YES | Zero inflation, weights, neutral_venue |
| `BayesianGoalModel` | YES | MCMC via emcee; full posterior |
| `HierarchicalBayesianGoalModel` | YES | Partial pooling across teams |
| `FootballProbabilityGrid` | YES | P(h=i, a=j) matrix + all derived markets |
| `create_dixon_coles_grid` | YES | Standalone DC grid from lambdas + rho |
| `dixon_coles_weights` | YES | `weights = exp(-xi * days_elapsed)` |
| `goal_expectancy` | YES | Point estimate for expected goals |
| `goal_expectancy_extended` | YES | Extended version |

All goal models accept: `goals_home, goals_away, teams_home, teams_away, weights=None, neutral_venue=None`

All goal models expose `.fit()`, `.predict(home, away, max_goals, neutral_venue)` → `FootballProbabilityGrid`

`FootballProbabilityGrid` outputs: `home_win`, `draw`, `away_win`, `btts_yes`, `btts_no`, `total_goals(over_under, strike)`, `asian_handicap(side, line)`, `exact_score(h, a)`, `home_goal_distribution()`, `away_goal_distribution()`, `expected_points_home()`, `expected_points_away()`

### `penaltyblog.metrics`

| Function | Signature |
|---|---|
| `compute_average_rps(probs, outcomes, nSets, nOutcomes)` | Mean RPS over nSets |
| `compute_rps_array(probs, outcomes, nSets, nOutcomes, out)` | Per-row RPS into pre-allocated array |
| `compute_ignorance_score(y_true, y_prob)` | Negative log probability (scalar) |
| `compute_multiclass_brier_score(y_true, y_prob)` | Multiclass Brier (scalar) |

Note: these expect flat arrays, not DataFrames. No ECE, calibration slope, or exact-score log loss — those must be custom.

### `penaltyblog.implied`

| Function | Description |
|---|---|
| `calculate_implied(odds, method, odds_format, market_names)` | Returns `ImpliedProbabilities` |

**Methods available**: `MULTIPLICATIVE`, `ADDITIVE`, `POWER`, `SHIN`, `DIFFERENTIAL_MARGIN_WEIGHTING`, `ODDS_RATIO`, `LOGARITHMIC`

**Formats**: `DECIMAL`, `AMERICAN`

**Output** `ImpliedProbabilities` fields: `probabilities` (list), `method`, `margin`, `market_names`, `method_params`

This is the correct tool for stripping bookmaker margin. Use it for all no-vig conversions.

### `penaltyblog.ratings`

| Class | Description |
|---|---|
| `Elo(k=20.0, home_field_advantage=100.0)` | Standard Elo; `.update_ratings(home, away, home_score, away_score)`, `.calculate_match_probabilities(home, away)`, `.get_team_rating(team)` |
| `PiRatingSystem(k, alpha, beta, sigma, diminishing_error)` | Pi ratings; same interface + `.expected_goal_difference(home, away)` |
| `MasseyRatings` | Massey ratings |
| `ColleyRatings` | Colley ratings |

These are stateful objects — must be updated in walk-forward order.

### `penaltyblog.backtest`

The `Backtest` class is designed for **betting strategy simulation** (P&L, Kelly staking), not model walk-forward training. Interface:

```python
bt = Backtest(data: pd.DataFrame, start_date: str, end_date: str)
bt.start(callback: Callable[[Context], None])
```

`Context` provides `.lookback` (history), `.fixture` (current row), `.model`, `.account` (for staking).

**Decision**: Use penaltyblog `Backtest` only for betting strategy evaluation. Build a custom `WalkForwardEngine` for model training and OOF prediction generation, which penaltyblog does not provide.

### `penaltyblog.matchflow`

MatchFlow is a declarative data pipeline built around Opta and StatsBomb event data schemas. It expects `events` in Opta/StatsBomb format with specific field names.

**Decision**: MatchFlow is not directly applicable to BDL's flat JSON API responses. Use BDL provider's normalized parquet tables as the data layer. MatchFlow `Flow` and `Group` can be used for rolling window aggregations over BDL events and shots once normalized.

### `penaltyblog.scrapers`

Available scrapers: `ClubElo`, `FBRef`, `FootballData`, `Understat`

ClubElo and FootballData provide international results. These can supplement BDL as a **global international prior** for teams with limited World Cup history.

---

## Usage decisions for this repo

| penaltyblog component | How we use it |
|---|---|
| All 8 goal models | Model ladder candidates — all trained and compared |
| `dixon_coles_weights` | Time-decay weights for all models |
| `FootballProbabilityGrid` | Single source of truth for all derived markets |
| `create_dixon_coles_grid` | Live remaining-goals grid |
| `penaltyblog.metrics` | RPS, Brier, ignorance — never custom reimplementation |
| `penaltyblog.implied` | All no-vig conversions — all 7 methods available |
| `penaltyblog.ratings.Elo` | Elo rating baseline |
| `penaltyblog.ratings.PiRatingSystem` | Pi rating baseline |
| `penaltyblog.backtest.Backtest` | Betting strategy P&L evaluation only |
| `penaltyblog.matchflow` | Rolling aggregations over BDL event/shot tables |
| `penaltyblog.scrapers` | Optional: global prior data from FootballData/ClubElo |
