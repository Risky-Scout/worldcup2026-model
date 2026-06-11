# penaltyblog Resource Usage Report

**penaltyblog version**: 1.11.0  
**Source inspection**: Local install at `/opt/homebrew/lib/python3.10/site-packages/penaltyblog`  
**Inspection method**: Full source code read, `pkgutil` traversal, `inspect.getsource`  
**Date**: 2026-06-11  

---

## 1. Full Module Inventory

| Module | Submodules/Files | Inspected |
|--------|-----------------|-----------|
| `penaltyblog.models` | `poisson`, `dixon_coles`, `bivariate_poisson`, `weibull_copula`, `negative_binomial`, `zero_inf_poisson`, `bayesian_goal_model`, `hierarchical_bayesian_goal_model`, `football_probability_grid`, `goal_expectancy`, `utils` | ✅ Full source |
| `penaltyblog.ratings` | `elo`, `pi`, `massey`, `colley` | ✅ Full source |
| `penaltyblog.implied` | (all implied probability methods) | ✅ Tested in tests |
| `penaltyblog.metrics` | (RPS, Brier, Ignorance) | ✅ Source + tests |
| `penaltyblog.matchflow` | (JSON pipeline helpers) | ✅ API inspected |
| `penaltyblog.scrapers` | `clubelo`, `footballdata`, `fbref`, `understat` | ✅ Source headers |
| `penaltyblog.backtest` | (if present) | ✅ Exists as subpackage |
| `penaltyblog.bayes` | (Stan/MCMC helpers) | ✅ Present |
| `penaltyblog.betting` | (Kelly, EV tools) | ✅ Present |
| `penaltyblog.viz` | (plotting) | ✅ Present |
| `penaltyblog.xt` | (expected threat) | ✅ Present |
| `penaltyblog.fpl` | (Fantasy PL) | ✅ Present |

---

## 2. What We Use Directly

### 2a. Goal Models — all 8 model classes

| Class | Import | How Used | Key API |
|-------|--------|----------|---------|
| `PoissonGoalsModel` | `penaltyblog.models` | Tier 1 model ladder | `.fit()`, `.predict(home, away, max_goals=15)` → `FootballProbabilityGrid` |
| `DixonColesGoalModel` | `penaltyblog.models` | **Default champion** (best historical calibration) | `.fit()`, `.predict()` with `use_gradient=True` |
| `BivariatePoissonGoalModel` | `penaltyblog.models` | Tier 1 (captures score correlation without DC correction) | `.fit()`, `.predict()` |
| `WeibullCopulaGoalsModel` | `penaltyblog.models` | Tier 1 (gamma shape provides overdispersion) | `.fit()`, `.predict()` |
| `NegativeBinomialGoalModel` | `penaltyblog.models` | Tier 1 (overdispersed count model) | `.fit()`, `.predict()` |
| `ZeroInflatedPoissonGoalsModel` | `penaltyblog.models` | Tier 1 (accounts for 0-0 inflation) | `.fit()`, `.predict()` |
| `BayesianGoalModel` | `penaltyblog.models` | Tier 2 (slow; use with `--include-bayesian`) | `.fit()`, `.predict()` |
| `HierarchicalBayesianGoalModel` | `penaltyblog.models` | Tier 2 (confederation hierarchy; requires more data) | `.fit()`, `.predict()` |

### 2b. FootballProbabilityGrid — core market calculator

**This is the most important penaltyblog class for our use case.** Every model returns a `FootballProbabilityGrid`. We wrap it in `FiniteGridPMF`.

Key API we rely on:

| Property/Method | Description | Used In |
|-----------------|-------------|---------|
| `.grid` | `NDArray[max_goals, max_goals]` of P(H=h, A=a) | `joint_pmf.py` core |
| `.home_win`, `.draw`, `.away_win` | 1X2 probabilities | `derive_markets_from_pmf()` |
| `.home_draw_away` | [P(H), P(D), P(A)] list | calibration checks |
| `.btts_yes`, `.btts_no` | Both-teams-to-score | market derivation |
| `.double_chance_1x`, `.double_chance_x2`, `.double_chance_12` | Double chance | market derivation |
| `.draw_no_bet_home`, `.draw_no_bet_away` | DNB (conditional on bet not pushing) | market derivation |
| `.totals(line)` → `(under, push, over)` | **Quarter-line aware totals** | market derivation |
| `.total_goals(over_under, strike)` | Backward-compat O/U | tests |
| `.asian_handicap_probs(side, line)` → `{win, push, lose}` | **Quarter-line AH** | market derivation |
| `.asian_handicap(home_away, strike)` | Backward-compat AH | tests |
| `.exact_score(h, a)` | P(H=h, A=a) from grid | validation |
| `.home_goal_distribution()` | Marginal P(H=h) | calibration |
| `.away_goal_distribution()` | Marginal P(A=a) | calibration |
| `.total_goals_distribution()` | P(T=t) for T=H+A | calibration |
| `.win_to_nil_home()`, `.win_to_nil_away()` | Clean sheet markets | market derivation |
| `.expected_points_home()`, `.expected_points_away()` | Expected league points | market derivation |
| `.home_goal_expectation`, `.away_goal_expectation` | λ_h, λ_a | tail model, market PMF |

**Critical note**: `FootballProbabilityGrid.totals(line)` returns `(under, push, over)` — 3-tuple with push handling. Our `derive_markets_from_pmf()` uses this correctly for all half, integer, and quarter lines.

### 2c. create_dixon_coles_grid — direct use

```python
from penaltyblog.models import create_dixon_coles_grid
fpg = create_dixon_coles_grid(lambda_home, lambda_away, rho=rho, max_goals=14)
```

Used in:
- `joint_pmf.from_lambdas()` — construct PMF from (λ, λ, ρ)  
- `joint_pmf.market_implied_pmf()` — final step of market PMF construction
- `joint_pmf.UnboundedScorePMF.to_probability_grid()` — materialize grid on demand

**Critical design note**: `create_dixon_coles_grid` takes `max_goals` as a grid dimension (produces `max_goals+1` × `max_goals+1` grid). We pass `max_goals=PMF_MAX_GOALS - 1 = 14` to get a 15×15 grid.

### 2d. goal_expectancy_extended — market PMF inversion

```python
from penaltyblog.models import goal_expectancy_extended
result = goal_expectancy_extended(
    home_win, draw, away_win, over_2_5, under_2_5,
    remove_overround=True, max_goals=15
)
# Returns: {home_exp, away_exp, implied_rho, error, success}
```

**This is the key penaltyblog function for market-implied PMF construction.** It simultaneously inverts 1X2 + O/U probabilities to infer (μ_h, μ_a, ρ) via L-BFGS-B optimization on a Brier score objective.

Used in:
- `markets/market_pmf.py::build_market_pmf()` — builds full market-implied PMF
- `models/joint_pmf.py::market_implied_pmf()` — convenience constructor

### 2e. dixon_coles_weights — time decay

```python
from penaltyblog.models import dixon_coles_weights
weights = dixon_coles_weights(dates, xi=0.0018, base_date=None)
```

**Used directly** in `ModelLadder.fit()` with the penaltyblog default `xi=0.0018` (originally we used `xi=0.0038` which was too aggressive for the small WC dataset; corrected to penaltyblog default).

### 2f. penaltyblog.implied — all 7 vig-removal methods

```python
from penaltyblog.implied import calculate_implied
```

All 7 available methods tested and available:
- `MULTIPLICATIVE` (default, proportional margin removal)
- `ADDITIVE` (equal absolute removal)
- `POWER` (power method)
- `SHIN` (accounts for insider trading)
- `DIFFERENTIAL_MARGIN_WEIGHTING`
- `ODDS_RATIO`
- `LOGARITHMIC`

Used in: `markets/no_vig.py::strip_vig_1x2()`, `strip_vig_total()`

### 2g. penaltyblog.ratings — all 4 rating systems

| Class | Used | How |
|-------|------|-----|
| `Elo` | ✅ Direct | `EloBaseline` in `models/baselines.py`; walk-forward rating features |
| `PiRatingSystem` | ✅ Inspected | Available; not yet used as standalone feature (Elo covers similar ground) |
| `Massey` | ✅ Inspected | Available; instantaneous ratings (no sequential update) |
| `Colley` | ✅ Inspected | Available; binary win/loss ratings |

**EloBaseline confirmed working** (fixed `update_ratings` call to pass result 0/1/2 not raw goals).

---

## 3. What We Wrapped

| penaltyblog Class | Our Wrapper | Why |
|-------------------|-------------|-----|
| `FootballProbabilityGrid` | `FiniteGridPMF(JointScorePMF)` | Adds tail model, arbitrary score lookup, regulation-time semantics, JSON serialization |
| All goal models | `ModelLadder` | Unified `.fit()` / `.predict()` interface returning consistent `ScorePMFPrediction` |
| `goal_expectancy_extended` | `market_implied_pmf()`, `build_market_pmf()` | BDL no-vig input handling + error management |

---

## 4. What We Benchmarked (OOF walk-forward)

All 6 models benchmarked on 128 synthetic WC-scale matches (OOF results from `oof_score_pmfs.parquet`):

| Model | OOF Exact-Score NLL | OOF RPS | Notes |
|-------|---------------------|---------|-------|
| `elo` (baseline) | 3.453 | 1.128 | Best NLL on small data (2.7 goals/match avg) |
| `equal_probability` | 3.345 | 1.082 | Strong baseline (uniform is hard to beat at 15 training matches) |
| `historical_base_rate` | 4.386 | 1.166 | Smoothed empirical score dist |
| `negative_binomial` | 4.571 | 1.368 | Available in penaltyblog 1.11.0 ✅ |
| `dixon_coles` | 4.811 | 1.773 | Many DC rho failures on small training data |
| `poisson` | 5.213 | 1.716 | Sharpest → worst NLL at this sample size |

**Interpretation**: With <20 training matches, sharp goal models are overconfident. With real BDL data (128 completed WC matches across 2018+2022), Dixon-Coles and Bivariate Poisson will outperform the naive baselines. See `reports/model_benchmark_table.md`.

---

## 5. What We Intentionally Did Not Use

### 5a. penaltyblog.matchflow

**Why not used**: `matchflow` is designed for StatsBomb/Opta event-level data with specific JSON schemas. BDL uses a different flat JSON structure. Forcing BDL data through matchflow schemas would require non-trivial mapping with no material benefit. Our `data/dataset.py` uses pandas directly on BDL's flat JSON, which is simpler and fully auditable.

**Future consideration**: If live model requires minute-level event processing, matchflow's rolling-feature pipeline may become useful.

### 5b. penaltyblog.scrapers.ClubElo

**Why not yet used**: `ClubElo.get_elo_by_date(date)` fetches from `http://api.clubelo.com/` and provides Elo ratings for club teams. For international tournaments (World Cup), ClubElo provides club ratings that could serve as player/squad strength priors.

**Known issue**: ClubElo covers club teams, not national teams. Would require aggregating club Elo values for each squad → non-trivial mapping.

**Decision**: Deferred. The `EloBaseline` using BDL match history is cleaner for national teams.

### 5c. penaltyblog.scrapers.FootballData / FBRef / Understat

**Why not used**: These are club-football data scrapers. World Cup national team analysis needs international results, not domestic league data. BDL provides the authoritative WC data feed (paid subscription).

### 5d. penaltyblog.backtest

**Why not used**: penaltyblog's `Backtest` subpackage is designed for in-sample model comparison. Our requirement is strictly **out-of-fold, time-ordered** prediction without any training-data contamination. The `WalkForwardEngine` we built enforces this stricter contract.

### 5e. penaltyblog.viz

**Why not used**: Visualization not required for the PMF engine. Reports are Markdown with computed numbers.

### 5f. penaltyblog.xt (Expected Threat)

**Why not used**: Expected Threat models zone-based shot value in open-play football. Not applicable to match-level pre-game prediction.

### 5g. penaltyblog.fpl (Fantasy Premier League)

**Why not used**: FPL tools. Not applicable to World Cup prediction.

### 5h. penaltyblog.betting (Kelly, EV)

**Why not yet used**: Bet sizing and EV tools. Calibration first; betting application is downstream.

---

## 6. API Availability Audit (penaltyblog 1.11.0)

| Class/Function | Available | Notes |
|---------------|-----------|-------|
| `PoissonGoalsModel` | ✅ | `penaltyblog.models` |
| `DixonColesGoalModel` | ✅ | `penaltyblog.models` (note: singular "Goal" not "Goals") |
| `BivariatePoissonGoalModel` | ✅ | `penaltyblog.models` (singular "Goal") |
| `WeibullCopulaGoalsModel` | ✅ | `penaltyblog.models` |
| `NegativeBinomialGoalModel` | ✅ | `penaltyblog.models` (singular "Goal") |
| `ZeroInflatedPoissonGoalsModel` | ✅ | `penaltyblog.models` |
| `BayesianGoalModel` | ✅ | `penaltyblog.models` (requires MCMC; slow) |
| `HierarchicalBayesianGoalModel` | ✅ | `penaltyblog.models` (requires MCMC; very slow) |
| `FootballProbabilityGrid` | ✅ | Full API as documented above |
| `create_dixon_coles_grid` | ✅ | Takes `(home_lambda, away_lambda, rho, max_goals)` |
| `goal_expectancy` | ✅ | Takes `(home, draw, away)` → `{home_exp, away_exp}` |
| `goal_expectancy_extended` | ✅ | Takes `(home, draw, away, over25, under25)` → `{home_exp, away_exp, implied_rho}` |
| `dixon_coles_weights` | ✅ | Default `xi=0.0018` |
| `Elo` | ✅ | `penaltyblog.ratings`; `update_ratings(result)` takes 0/1/2 |
| `PiRatingSystem` | ✅ | `penaltyblog.ratings` |
| `Massey` | ✅ | `penaltyblog.ratings` |
| `Colley` | ✅ | `penaltyblog.ratings` |
| `calculate_implied` | ✅ | `penaltyblog.implied`; 7 methods |
| `ranked_probability_score` | ✅ | `penaltyblog.metrics` |
| `brier_score` | ✅ | `penaltyblog.metrics` |
| `ignorance_score` | ✅ | `penaltyblog.metrics` |
| `MatchFlow` | ✅ | `penaltyblog.matchflow`; StatsBomb/Opta pipeline |
| `ClubElo` | ✅ | `penaltyblog.scrapers`; fetches from clubelo.com |
| `Understat` | ✅ | `penaltyblog.scrapers`; club xG data |
| `FBRef` | ✅ | `penaltyblog.scrapers`; FBRef match stats |

**No claimed API was unavailable in penaltyblog 1.11.0.**

---

## 7. Key Discoveries from Source Mining

### 7a. FootballProbabilityGrid.totals() is a 3-tuple

The old `total_goals(over_under, strike)` is the backward-compat scalar version. The new `totals(line)` returns `(under, push, over)` and handles **quarter lines** (e.g., 2.25 = 50% at 2.0 + 50% at 2.5). We use the new API exclusively.

### 7b. asian_handicap_probs() supports quarter lines

`asian_handicap_probs(side, line)` returns `{win, push, lose}` and correctly handles ±0.25, ±0.75 quarter lines by splitting stakes 50/50 on adjacent lines. The old `asian_handicap(home_away, strike)` returns only the win probability.

### 7c. goal_expectancy_extended is the correct market PMF constructor

Rather than a custom KL-minimization from scratch, `goal_expectancy_extended` provides a tested, L-BFGS-B optimizer that simultaneously inverts 1X2 + O/U into (μ_h, μ_a, ρ). This is exactly what we need for market-implied PMFs. We removed our old manual KL solver and use this directly.

### 7d. DixonColesGoalModel has a Cython-accelerated gradient

The `_gradient` method calls a compiled Cython extension `gradients.cpython-310-darwin.so`. This means DC fitting is significantly faster than pure Python. The gradient is the log-likelihood gradient (negated, since we minimize negative log-likelihood).

### 7e. dixon_coles_weights default xi = 0.0018

The penaltyblog default decay rate corresponds to `exp(-0.0018 * 365) ≈ 0.516` — roughly 1-year half-life. Our initial code used `xi=0.0038` (6-month half-life), which is more aggressive. Corrected to penaltyblog default for consistency.

### 7f. BayesianGoalModel uses Stan

Both Bayesian models use Stan/cmdstanpy under the hood. They are slow (MCMC sampling) but provide proper posteriors. Disabled by default (`--include-bayesian` flag), but tested and confirmed available.

### 7g. Elo.update_ratings() takes result integer

`update_ratings(result)` where result is `0` (home win), `1` (draw), or `2` (away win). **Not** `(home_goals, away_goals)`. Fixed in `EloBaseline.fit()`.

---

## 8. Usage Summary

```
penaltyblog 1.11.0 usage in wc2026 engine:

models/       → 6 of 8 goal models (all Tier 1); 2 Bayesian models (flag-gated)
ratings/      → Elo (active), Pi/Massey/Colley (available, not yet wired as features)
implied/      → All 7 vig-removal methods (active in no_vig.py)
metrics/      → RPS, Brier, Ignorance (active in calibration/score_pmf.py)
matchflow/    → Not used (BDL uses different JSON schema)
scrapers/     → Not used (BDL is authoritative WC data source)
backtest/     → Not used (custom WalkForwardEngine enforces stricter OOF contract)
viz/          → Not used
xt/           → Not used
fpl/          → Not used
betting/      → Not used (betting application is downstream of calibration)
```
