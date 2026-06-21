---
title: "How the 2026 World Cup Prediction Model Works"
subtitle: "A complete guide to the mathematics behind the joint score probability engine"
author: "WizardOfOdds.com"
date: "June 2026"
---

# How the 2026 World Cup Prediction Model Works

Predicting football is an exercise in structured humility. A single match produces roughly two or three goals from a cascade of decisions, deflections, and individual moments of brilliance that no model can fully capture. Even the best football models in the world — the ones running inside sharp sportsbooks and professional syndicates — are wrong more often than they are right about any individual game.

What a good model can do is get the probabilities right over a large number of matches. Assign 30% to outcomes that happen 30% of the time. Be faster than the public at incorporating new information. Identify specific markets where the bookmaker's price doesn't reflect the available evidence. That is a narrower ambition than predicting winners — but it is the ambition that leads to long-run results.

This model produces a **full joint probability mass function (PMF) over every possible regulation-time final score** for every 2026 FIFA World Cup match. It blends 12 independent signal sources into a composite team rating, runs six competing parametric models daily, anchors each match's goal totals against live bookmaker lines, reconciles the result against market probabilities, and applies a Hierarchical Bayesian blend before final calibration. The pipeline runs without human intervention 24 hours a day and FTP-uploads results to WizardOfOdds.com after every run.

---

## What a Joint Score PMF Actually Is

Before describing the engine, it helps to understand precisely what it produces.

A PMF is a Probability Mass Function — a complete assignment of probability to every possible discrete outcome. For a football match, the **joint score PMF** is a two-dimensional grid. Each cell (h, a) holds P(Home = h, Away = a): the probability that the home team scores exactly h goals and the away team scores exactly a goals in regulation time.

The grid extends from (0,0) through whatever maximum makes sense (typically 8–9 goals per team), plus an explicit tail-mass bucket for extreme scores beyond the grid boundary. Every cell, including the tail, must sum to exactly 1.0 — a constraint enforced at every pipeline stage.

Every betting market is simply a different question about this same distribution:

- **Over 2.5 goals:** Sum all cells where h + a >= 3
- **Both Teams to Score (BTTS):** Sum all cells except the first row (h = 0) and the first column (a = 0)
- **Home Win:** Sum all cells where h > a
- **Draw:** Sum all cells on the main diagonal (0-0, 1-1, 2-2, ...)
- **Correct score 2-1:** That is a single cell: P(h = 2, a = 1)

There is no separate model for each market type. The PMF is the entire model, and all markets are different questions about the same distribution. This guarantees internal consistency — a property that does not hold on sites that blend data from different sources.

---

## Step 1: The 12-Signal Composite Prior — Rating All 48 Teams

The first task is assigning each of the 48 teams an **attack lambda** and a **defense lambda**: expected goals scored and conceded against an average opponent at a neutral venue. No single rating system is reliable enough to trust alone. The solution is a **composite prior** blended from twelve independent signal sources.

### The Twelve Signal Sources

| # | Signal Source | Primary Data | Weight |
|---|---|---|---|
| 1 | market_implied | BDL consensus 1X2 odds, SHIN no-vig | ~20% |
| 2 | futures_implied | Tournament outright futures odds | ~5% |
| 3 | best_player_form | Top-player performance ratings per team | ~5% |
| 4 | fifa_ranking | March 2026 official FIFA ranking points | ~10% |
| 5 | qualifying | Attack/defense efficiency, Bayesian-shrunk | ~8% |
| 6 | penaltyblog_pi | Pi Ratings — goal-margin dynamic rating | ~15% |
| 7 | penaltyblog_elo | Elo rating, home_field_advantage=100 | ~12% |
| 8 | massey | Massey method ratings | ~5% |
| 9 | confederation | Confederation strength adjustment | ~5% |
| 10 | tournament_wc2026 | In-tournament Bayesian shrinkage on WC2026 results | ~5% |
| 11 | injuries | avg_rating × (OUT=1.0 / GTD=0.5) impact score | ~5% |
| 12 | intl_poisson | Bivariate Poisson on 49,433 Kaggle international matches | ~15% |

### Signal 1: market_implied (BDL Consensus Odds, ~20%)

When bookmaker odds are available, they encode information no rating system can access: late team news, undisclosed injuries, sharp money, and the aggregate view of every serious analyst who has looked at the match. The model reverse-engineers what team lambdas would produce the bookmaker's observed no-vig 1X2 probabilities.

SHIN normalization removes the bookmaker margin before any comparison. Up to 6 sportsbooks contribute: FanDuel, DraftKings, BetMGM, BetRivers, Caesars, and Fanatics. The `market_weight` parameter is fixed at 0.20 for CLV-independence mode — preventing the model from over-fitting to the very prices it is trying to beat.

### Signal 2: futures_implied (Tournament Outright Futures, ~5%)

Tournament outright futures odds (winner, top-4, group winner) are converted to team strength priors using a Bradley-Terry decomposition. These odds embed long-run tournament expectations and provide useful signal for teams where match-level 1X2 odds are thin or unavailable.

### Signal 3: best_player_form (Top-Player Performance, ~5%)

For each team, the performance rating of the top-rated player currently in the tournament squad is used as a proxy for the team's ceiling performance level. This captures the "superstar factor" that pure team-level ratings miss.

### Signal 4: fifa_ranking (~10%)

FIFA's official points system, converted to an attack lambda via a calibrated sigmoid mapping. Captures long-run international performance across all competitions. The model uses the March 2026 snapshot — the last official pre-tournament update.

### Signal 5: qualifying (~8%)

Each team's attack and defense efficiency during their qualifying campaign, Bayesian-shrunk toward the confederation average using the n/(n+3) formula. A team that dominated its qualifying group carries a meaningfully different expected output than one that scraped through.

### Signals 6–7: penaltyblog_pi and penaltyblog_elo (~27% combined)

**Pi Rating** (goal-margin-sensitive, ~15%) and **Elo** (~12%), both computed using the penaltyblog library. Pi updates on actual goal margins — a 4-0 win earns a larger boost than a 1-0 win — making it highly responsive to genuine form shifts. Elo updates only on match result (win/draw/loss), providing stability that prevents the prior from swinging sharply on an unusual scoreline. `penaltyblog_elo` is parameterized with `home_field_advantage=100`, calibrated to international data.

### Signal 8: massey (~5%)

Massey ratings solve a least-squares system over the full history of international results to assign each team a strength rating. Particularly useful for teams with limited recent match data, where Elo and Pi have small-sample noise.

### Signal 9: confederation (~5%)

Historical World Cup attack averages by confederation: CONMEBOL 1.45, UEFA 1.35, CONCACAF 1.20, CAF 1.10, AFC 1.10, OFC 0.90. Acts as a soft floor preventing any team from receiving a lambda wildly inconsistent with their region's historical output.

### Signal 10: tournament_wc2026 (In-Tournament Bayesian Shrinkage, ~5%)

Once WC2026 matches complete, results feed back into each team's rating via Bayesian shrinkage. For n completed WC2026 matches, the shrinkage weight is n/(n+3): one match contributes 25%, two matches 40%, three matches 50%. Adjustments are capped at ±30%. When BallDontLie shot data is available, tournament ratios blend 40% actual goals with 60% expected goals (xG) to reduce small-sample noise.

As of June 2026: **22 teams** have active adjustments from completed WC2026 matches.

### Signal 11: injuries (Blueprint Injury Impact Score, ~5%)

For each team, an injury impact score is computed from BallDontLie squad and injury report data:

    injury_impact = SUM over injured players of:
        player_avg_rating × status_weight

    Where status_weight = 1.0 for OUT, 0.5 for GTD (game-time decision)

A higher impact score applies a larger downward adjustment to attack/defense lambdas. This captures the effect of missing star players that no pre-tournament rating system can account for.

### Signal 12: intl_poisson (International Bivariate Poisson, 15% blend)

A dedicated Bivariate Poisson model fitted from scratch on **49,433 international football matches** sourced from the Kaggle international results dataset, spanning 1872 through 2026. A **3-year exponential half-life decay** weighting ensures recent results dominate while the full historical depth provides stable long-run team strength estimates for every nation.

The intl_poisson signal is particularly valuable for: (a) neutralizing home advantage effects — the historical dataset allows precise estimation of neutral-venue attack and defense rates for all 48 teams; (b) providing independent validation of live-market and Elo signals; and (c) anchoring predictions for low-data teams whose Elo and Pi ratings rest on thin sample bases. Blended at **15% weight** into the composite prior.

### Host and Altitude Adjustments

USA, Canada, and Mexico each receive a co-host adjustment of +0.10 attack lambda and -0.10 defense lambda. Three Mexican venues sit at elevations that materially reduce scoring rates:

- **Estadio Azteca** (Mexico City, 2,230m): 0.93× multiplier — approximately 7% scoring reduction
- **Estadio Akron** (Guadalajara, 1,560m): 0.97× multiplier — approximately 3% reduction
- **Estadio BBVA** (Monterrey, 530m): no adjustment

### Dynamic WC_AVG Scaling

Historical average from 2018 and 2022: **1.30 goals per team per match**. Through completed 2026 matches, the observed rate is **1.455 goals per team per match** (scale factor: **1.119×**). After the composite prior is built, all 52 team lambdas are multiplied by this factor so predictions reflect the actual 2026 tournament environment.

---

## Step 2: Per-Match Calibration Enhancements

After composite team lambdas are established, each individual match receives a set of per-match adjustments derived from live bookmaker data, group standings, and shot quality metrics.

### total_anchor: BDL Market Over/Under Line

For each match, the median BDL O/U line across all available vendors (clipped to 1.5–6.0) is used as a per-match expected total goals anchor, blended with the parametric estimate. Falls back to the tournament-wide average when no BDL data is available.

### home_team_total / away_team_total: Individual Team Totals

Where BDL markets carry individual team total lines, the implied team goal expectations are extracted and blended at **50% weight** into the composite lambda for each team.

### pts_diff / gd_diff: Group Standings Adjustments

In the group stage, each team's current points and goal differential are used to apply an attack multiplier:

    attack_mult = 1.0 + (pts_diff / max_pts_diff) × 0.08
                 + (gd_diff / max_gd_diff) × 0.08

Where diffs are computed as (team value − opponent value). This applies a ±8% attack range based on current group standing differential.

### WDL Form String

Each team's recent Win/Draw/Loss sequence is parsed and converted to a form score, then blended **50/50** with the rating z-score to produce a momentum-adjusted attack rating.

### confederation_diff: Cross-Confederation Adjustment

When two teams from different confederations meet, the stronger confederation's team receives a small attack multiplier of **±2–5%** based on historical confederation strength differential.

### venue_lambda_adj: Travel, Rest, and Stadium Capacity

Three venue-specific factors are combined into a single lambda adjustment (promoted from shadow mode to full production):

- **Haversine travel distance** from each team's base camp to the match venue
- **Rest days** since each team's last match
- **Stadium capacity** as a proxy for home-crowd atmosphere effects

All three factors are combined multiplicatively and applied to each team's attack and defense lambdas independently.

### Bayesian Blend: HierarchicalBayesianGoalModel at 20%

After the parametric PMF is generated, a `HierarchicalBayesianGoalModel` (penaltyblog) is computed and blended into the final PMF:

    final_PMF = 0.80 × parametric_PMF + 0.20 × bayesian_PMF

This Bayesian model uses partial pooling across all teams — a team with few completed matches borrows strength from teams with similar rating profiles.

### Adaptive Temperature: Dynamic Calibration Weighting

    If completed_matches >= 24:
        weight = 60% WC2026 data / 40% historical (2018+2022)

    If completed_matches < 24:
        weight = 30% WC2026 data / 70% historical

This prevents the calibration from over-weighting a small 2026 sample early in the tournament while transitioning to current-tournament calibration as data accumulates.

### xGOT: Shot Quality Correction

When BallDontLie shot quality data is available, each team's mean xGOT/xG ratio is computed as a measure of shot quality. A team generating more dangerous shot locations receives a multiplicative upward correction to their attack lambda:

    attack_lambda *= (team_mean_xGOT / team_mean_xG) / league_average_ratio

### calib_rho: Dixon-Coles Correlation Parameter

    calib_rho = 0.60 × prior_rho + 0.40 × market_implied_rho

    Current calibrated value: rho = -0.042
    (Negative rho slightly reduces the probability of 0-0 and 1-1 draws
     relative to independent Poisson)

---

## Step 3: The Bivariate Poisson — Where the Model Gets Clever

With composite team ratings and per-match adjustments in hand, the model computes the joint score distribution.

### The Naive Approach: Independent Poisson

The textbook starting point is to model each team's goals as an independent Poisson random variable:

    P(H=h, A=a) = P(H=h) × P(A=a)
                = [e^(-lambda_h) × lambda_h^h / h!]
                  × [e^(-lambda_a) × lambda_a^a / a!]

This is the classical baseline, and it contains a subtle error: **goals are not independent**. When the first goal goes in at the 25th minute, everything changes — tactics shift, intensity rises, and high-energy matches tend to produce more goals for both teams simultaneously.

### The Fix: Three Poisson Processes

The **Bivariate Poisson** model handles this properly:

- **Z_1 ~ Poisson(lambda_1):** Goals generated by the home team independently
- **Z_2 ~ Poisson(lambda_2):** Goals generated by the away team independently
- **Z_3 ~ Poisson(lambda_3):** A shared latent "match intensity" component — extra goals attributed to both teams in high-energy matches

Then: H = Z_1 + Z_3,  A = Z_2 + Z_3

The joint probability becomes:

    P(H=h, A=a) = e^(-(lambda_1+lambda_2+lambda_3))
                  × SUM{k=0 to min(h,a)} [lambda_1^(h-k) / (h-k)!]
                                         × [lambda_2^(a-k) / (a-k)!]
                                         × [lambda_3^k / k!]

When lambda_3 = 0, the formula reduces exactly to the independent Poisson product. **Cov(H, A) = lambda_3** — the covariance equals the shared intensity parameter.

The calibrated value from completed WC2026 matches is **lambda_3 = 0.170**. Positive — this World Cup is showing exactly the mutual intensity correlation the model was built to capture.

### The Six Parametric Competitors

The model runs **six competing parametric models daily** and selects the winner by negative log-likelihood on held-out WC2026 data:

1. **Independent Poisson** — Classical baseline. Goals independent.
2. **Dixon-Coles** — Low-score correction via rho = −0.042. Calibrated from WC2026 data.
3. **Bivariate Poisson** — Current log-likelihood champion. lambda_3 = 0.170.
4. **Weibull Copula** — Heavier tails than Poisson. More high-scoring outliers.
5. **Negative Binomial** — Overdispersion: variance > mean.
6. **Zero-Inflated Poisson** — Excess 0-0 draws beyond what Poisson predicts.

All six compete on the same held-out data. The winner is reselected daily as more matches accumulate.

---

## Step 4: Market Reconciliation (SLSQP)

Even the Bivariate Poisson cannot know about a goalkeeper injury announced 90 minutes before kickoff. Market reconciliation solves this.

For each match, the model extracts fair market probabilities from all available bookmakers (after SHIN normalization) across as many market types as the API carries: 1X2, Over/Under totals from 0.5 through 6.5, Both Teams to Score, Draw No Bet, Double Chance, and correct score lines.

A constrained optimization algorithm — **SLSQP (Sequential Least Squares Programming)** — then adjusts the parametric PMF grid to satisfy these market constraints while minimizing Kullback-Leibler divergence from the original distribution. Hard constraints: all cells >= 0, sum = 1.0.

After SLSQP convergence, the `HierarchicalBayesianGoalModel` is blended at 20% into the final PMF. Currently: **SLSQP dominates for virtually all matches** — only 1 non-convergence observed in 63 matches.

---

## Step 5: Calibration (Adaptive Temperature Scaling)

A model is calibrated when its stated probabilities match observed frequencies.

The model uses **adaptive temperature scaling**: a single parameter T fitted by minimizing exact-score log loss on out-of-sample predictions, with data weighting shifting from 30/70 (WC2026/historical) to 60/40 once 24 or more WC2026 matches complete. The calibrated probability for each grid cell is:

    p_calibrated[h,a]  proportional to  p_raw[h,a]^(1/T)
    [then renormalized to sum to 1.0]

**Current calibrated temperature: T = 1.089.** T > 1 flattens the distribution, correcting for mild overconfidence in the raw parametric output.

Five metrics are evaluated on out-of-sample data only:
- **Exact-score NLL** (primary metric)
- **Ranked Probability Score** for 1X2
- **Brier score** on binary markets
- **Expected Calibration Error (ECE)**
- **Ignorance score**

---

## Step 6: Edge Screening

With a calibrated PMF, the model compares its probability estimates against the bookmaker's no-vig prices:

    Edge = (Model probability - Market implied probability) / Market implied probability

Three simultaneous filters must all pass for a market to be flagged:

1. **Edge >= 4%** — minimum threshold for signal above estimation noise
2. **90% CI lower bound > market implied** — computed by perturbing lambda by ±12%
3. **Market implied > 2%** — thin-liquidity markets excluded

Kelly sizing for flagged markets:

    f*  =  Edge / (Decimal odds - 1)
    Half-Kelly  =  f* / 2     [default]
    Hard cap: 5% of bankroll

---

## Step 7: Closing Line Value (CLV)

**CLV is the industry-standard measure of whether a model has genuine edge.**

The closing line is the bookmaker's final no-vig probability immediately before kickoff — the market's best collective estimate. A model that consistently predicts higher probability than where the market ultimately closes is providing information the market was slow to price in.

**15 markets tracked per match:** The three 1X2 outcomes, BTTS Yes/No, Over/Under at 0.5, 1.5, 2.5, 3.5, 4.5, 5.5, 6.5, and Under at 1.5, 2.5, and 3.5.

Closing odds are captured automatically at **T-3 minutes before each kickoff**. The Market X-Ray page surfaces CLV tracking alongside real-time edge analysis for all active matches.

---

## The Live In-Play Model

During a live match, the model runs a **non-homogeneous hazard model** where goal-scoring rate varies by match minute, calibrated from 2018 and 2022 World Cup data. Goal rates are below average early, rise through the mid-half, spike just after half-time, and peak in the final minutes.

### Score-State Multipliers

| Score State | Home Rate | Away Rate |
|---|---|---|
| Draw at minute 60+ | ×1.10 | ×1.10 |
| Home team losing by 1 | ×1.25 | ×1.05 |
| Home team losing by 2+ | ×1.40 | ×1.10 |
| Home team winning by 1 | ×0.90 | ×1.10 |
| Home team winning by 2+ | ×0.80 | ×1.15 |

### xG Blend

When live xG data is available from BallDontLie, the model blends live xG rate (60% weight) with the pre-game prior (40% weight) starting from minute 15. Before minute 15, live xG from a small number of shots is too noisy to be useful.

### Momentum Scaling: passes_final_third

Live passes into the final third wire directly into the live hazard:

    hazard_mult = 1.0 + (team_passes_final_third - opponent_passes_final_third)
                  / normalizer × 0.03

    Range: approximately ±3% attack rate adjustment

### momentum_df: BDL Match Momentum API

The BallDontLie match momentum API is active in the live hazard:

    Home team momentum advantage: +8% hazard scaling
    Away team momentum advantage: +5% hazard scaling

---

## The Automated Pipeline

Every stage runs automatically, without human intervention, around the clock. Results are FTP-uploaded to WizardOfOdds.com after every run.

**Daily at 8:00 AM UTC (4:00 AM ET):** Full retraining. All 12 signals refreshed, all six parametric models retrained, composite prior rebuilt, per-match adjustments applied, predictions regenerated, calibration metrics logged.

**Hourly:** Pre-match odds refresh. Lighter refresh capturing odds movements, updating CLV records, re-running predictions if newly completed matches appeared.

**Every 2 minutes during match hours:** Live snapshot. The pipeline self-chains during active match windows. Current score, minute, xG, momentum, and passes_final_third wired into the live hazard model.

**T-3 minutes before kickoff:** Closing odds capture. A dedicated watcher fetches final market odds across all 15 tracked markets for CLV recording.

---

## Honest Limitations

**Regulation time only.** Extra time and penalty shootouts are not modeled.

**lambda_3 = 0.170 is an average.** A match in stoppage time with a team pressing for an equalizer has dramatically different dynamics than a settled 2-0 game. The live model's score-state multipliers handle this in real time.

**The calibration temperature T and dynamic WC_AVG scaling factor will stabilize as the tournament progresses.** Any parameter estimated from a small sample carries meaningful uncertainty.

**Lambda uncertainty is a fixed prior.** The ±12% used for confidence intervals is a conservative global assumption.

**Odds move between prediction and kickoff.** Always verify current odds at your book before acting on any signal.

**Positive expected value does not guarantee positive returns in any finite sample.** Football remains genuinely hard to predict.

---

*All probabilities represent regulation time (90 minutes plus stoppage time) only. Extra time and penalties are excluded. This article is for informational and educational purposes. Please gamble responsibly.*
