---
title: "How the 2026 World Cup Prediction Model Works"
subtitle: "A complete guide to the mathematics behind the joint score probability engine"
author: "WizardOfOdds.com"
date: "June 2026"
---

# How the 2026 World Cup Prediction Model Works

Predicting football is an exercise in structured humility. A single match produces roughly two or three goals from a cascade of decisions, deflections, and individual moments of brilliance that no model can fully capture. Even the best football models in the world — the ones running inside sharp sportsbooks and professional syndicates — are wrong more often than they are right about any individual game.

What a good model can do is get the probabilities right over a large number of matches. Assign 30% to outcomes that happen 30% of the time. Be faster than the public at incorporating new information. Identify specific markets where the bookmaker's price doesn't reflect the available evidence. That is a narrower ambition than predicting winners — but it is the ambition that leads to long-run results.

This model produces a **full joint probability mass function (PMF) over every possible regulation-time final score** for every 2026 FIFA World Cup match. Every market you see on the site — Over/Under, Both Teams to Score, 1X2, correct score — is derived mechanically from this single grid. The architecture guarantees internal consistency: the numbers cannot contradict each other because they all flow from one source of truth. The following sections describe every stage of that process.

---

## What a Joint Score PMF Actually Is

Before describing the engine, it helps to understand precisely what it produces.

A PMF is a Probability Mass Function — a complete assignment of probability to every possible discrete outcome. For a football match, the **joint score PMF** is a two-dimensional grid. Each cell (h, a) holds P(Home = h, Away = a): the probability that the home team scores exactly h goals and the away team scores exactly a goals in regulation time.

The grid extends from (0,0) through whatever maximum makes sense (typically 8–9 goals per team), plus an explicit tail-mass bucket for extreme scores beyond the grid boundary. Every cell, including the tail, must sum to exactly 1.0 — a constraint enforced at every pipeline stage.

Here is why the grid architecture matters. Every betting market is simply a different question about this same distribution:

- **Over 2.5 goals:** Sum all cells where h + a >= 3
- **Both Teams to Score (BTTS):** Sum all cells except the first row (h = 0) and the first column (a = 0)
- **Home Win:** Sum all cells where h > a
- **Draw:** Sum all cells on the main diagonal (0-0, 1-1, 2-2, ...)
- **Correct score 2-1:** That is a single cell: P(h = 2, a = 1)

There is no separate model for each market type. The PMF is the entire model, and all markets are different questions about the same distribution. This guarantees that the model's Over 2.5 probability and its 1X2 probabilities are mathematically consistent with each other — a property that does not hold on sites that blend data from different sources.

---

## Step 1: The Composite Prior — Rating All 48 Teams

The first task is assigning each of the 48 teams an **attack lambda** (lambda_att) and a **defense lambda** (lambda_def): expected goals scored and conceded against an average opponent at a neutral venue. The 2026 global baseline is 1.30 goals per team per match, calibrated from 2018 and 2022 World Cup data.

No single rating system is reliable enough to trust alone. FIFA rankings can lag months behind a team's actual form. Bookmaker odds contain real information but can be biased by public betting flow. The solution is a **composite prior** blended from six independent data sources, each contributing information no other source has.

### Source 1: Market-Implied Strength (30% weight)

When bookmaker odds are available, they encode information that no rating system can access: late team news, undisclosed injuries, sharp money, and the aggregate view of every serious analyst who has looked at the match. The model reverse-engineers what team lambdas would produce the bookmaker's observed no-vig 1X2 probabilities.

Before doing this, the bookmaker margin must be removed. Raw quoted odds always include a margin of roughly 5–8% that inflates the implied probabilities. SHIN normalization is applied to all odds from all bookmakers to convert them to fair (no-margin) probabilities. Using raw odds as fair probabilities would consistently bias every market comparison — this step is not optional.

Up to 6 sportsbooks contribute to each match's market picture: FanDuel, DraftKings, BetMGM, BetRivers, Caesars, and Fanatics. Their no-vig probabilities are averaged to produce a consensus view.

The 30% weight for market-implied strength is empirically determined by minimizing log-loss on completed WC2026 matches. This is the single largest weight in the composite, reflecting the genuine information content of well-supplied sharp markets.

### Source 2: FIFA Ranking — March 2026 (~12% weight)

FIFA's official points system, converted to an attack lambda via a calibrated sigmoid mapping. FIFA rankings capture long-run international performance across all competitions and provide a useful signal particularly for teams with limited recent competitive data. Weakness: rankings update infrequently and can reflect results from years prior. The model uses the March 2026 snapshot — the last official pre-tournament update.

### Source 3: Qualifying Record (~10% weight)

Each team's attack and defense efficiency during their qualifying campaign, Bayesian-shrunk toward their confederation's average. The shrinkage scales with number of competitive matches: n / (n + 3), where 3 is the prior strength. A team with 18 qualifying matches gets treated very differently from one with 6. A nation that dominated its qualifying group is genuinely more dangerous than one that scraped through, and this source captures that signal.

### Source 4: Pi Rating (~30% of parametric weight)

The Pi rating, computed using the penaltyblog library, is a goal-margin-sensitive variant of Elo. Unlike standard Elo which updates only on match result (win/draw/loss), Pi updates on the actual score. A team that wins 4-0 earns a larger rating boost than one that wins 1-0. This makes Pi more responsive to genuine performance shifts — well-suited for a model whose primary target is predicting scores, not just results.

### Source 5: Elo Rating (~55% of parametric weight)

Classic international Elo, also from penaltyblog, based on win/loss/draw outcomes. Elo is more stable over long periods than Pi precisely because it does not react to score margins — a team cannot inflate its Elo by running up the score. It serves as a stabilizing anchor that prevents the prior from swinging too sharply on an unusual scoreline, and it is the dominant signal for teams where Pi and market data are sparse.

### Source 6: Confederation Baseline (~5% as a soft floor)

Historical World Cup attack averages by confederation: CONMEBOL 1.45, UEFA 1.35, CONCACAF 1.20, CAF 1.10, AFC 1.10, OFC 0.90. Defense baselines mirror these figures. This source acts as a soft floor — it prevents any team from receiving a lambda estimate wildly inconsistent with what teams from their region have historically produced at World Cups. For well-rated teams with extensive data, this source contributes almost nothing. For data-sparse teams, it prevents impossible extreme estimates.

When market odds are unavailable for a match, the market-implied source is excluded and the remaining five sources expand proportionally.

### Host and Altitude Adjustments

USA, Canada, and Mexico each receive a co-host adjustment of +0.10 attack lambda and -0.10 defense lambda. This reflects the measurable advantages of familiar geography, minimal travel, and genuine crowd support.

Three Mexican venues sit at elevations that materially reduce scoring rates for unacclimated players. Both teams' lambdas are scaled equally at these venues — neither side is acclimatized:

- **Estadio Azteca** (Mexico City, 2,230m): 0.93x multiplier — approximately 7% scoring reduction
- **Estadio Akron** (Guadalajara, 1,560m): 0.97x multiplier — approximately 3% reduction
- **Estadio BBVA** (Monterrey, 530m): no adjustment

### Tournament Adjustment: Learning from 2026 Results

Once WC2026 matches complete, results feed directly back into each team's rating via Bayesian shrinkage. For a team with n completed WC2026 matches, the tournament adjustment factor is shrunk toward 1.0 with weight n / (n + 3). The 3 is the prior strength — roughly equivalent to "three prior-data matches are worth about as much as one actual tournament match." Adjustments are capped at +/-30%.

As of June 2026: **22 teams** have active tournament adjustments from **11 completed WC2026 matches**.

When BallDontLie shot data is available, team tournament ratios blend 40% actual goals with 60% expected goals (xG). This xG blend is now active for all 22 adjusted teams — a less noisy signal than raw goals alone, particularly with small sample sizes.

### Dynamic WC_AVG Scaling

This World Cup is playing fast. Historical average: **1.30 goals per team per match**. Through 11 completed WC2026 matches, the observed rate is **1.455 goals per team per match**. The dynamic scale factor is 1.455 / 1.30 = **1.119**.

After the composite prior is built, all 52 team lambdas are multiplied by this factor. This ensures the model's global scoring expectations reflect the actual 2026 tournament environment rather than being anchored to 2018/2022 conditions. As more matches complete, this factor will stabilize at the true 2026 average.

---

## Step 2: The Bivariate Poisson — Where the Model Gets Clever

With composite team ratings in hand, the model computes the joint score distribution. This is where the standard approach falls short — and where this model goes beyond it.

### The Naive Approach: Independent Poisson

The textbook starting point is to model each team's goals as an independent Poisson random variable. Given the estimated lambdas, the joint probability is:

    P(H=h, A=a) = P(H=h) x P(A=a)
                = [e^(-lambda_h) x lambda_h^h / h!]
                  x [e^(-lambda_a) x lambda_a^a / a!]

This is the classical baseline, and it works reasonably well. But it contains a subtle and important error: **goals are not independent**.

When the first goal goes in at the 25th minute, everything changes. The losing team pushes forward, the winning team may sit deeper, more space opens up, and the tactical picture reshapes entirely. The correlation between home and away goals in football is small but real and positive — both teams tend to score more in high-intensity, open matches. Treating them as independent misses this.

### The Fix: Three Poisson Processes

The **Bivariate Poisson** model handles this properly. The mathematical intuition is elegant: instead of two independent processes, model the goals as arising from THREE independent Poisson processes:

- **Z_1 ~ Poisson(lambda_1):** Goals generated by the home team independently
- **Z_2 ~ Poisson(lambda_2):** Goals generated by the away team independently
- **Z_3 ~ Poisson(lambda_3):** A shared latent "match intensity" component — extra goals that tend to occur simultaneously in high-energy matches, attributed to both teams

Then: H = Z_1 + Z_3,  A = Z_2 + Z_3

The joint probability of observing h home goals and a away goals becomes:

    P(H=h, A=a) = e^(-(lambda_1+lambda_2+lambda_3))
                  x SUM{k=0 to min(h,a)} [lambda_1^(h-k) / (h-k)!]
                                         x [lambda_2^(a-k) / (a-k)!]
                                         x [lambda_3^k / k!]

When lambda_3 = 0, the sum has only one term (k = 0) and the formula reduces exactly to the independent Poisson product. The Bivariate Poisson IS the independent Poisson when the data doesn't support correlation — it never breaks, it only adds information when it's there.

The key quantity: **Cov(H, A) = lambda_3**. The covariance between home and away goals equals exactly the shared intensity parameter. When lambda_3 > 0, the model correctly captures the positive correlation between both teams' scoring rates that real football data consistently shows.

The calibrated value from 11 completed WC2026 matches is **lambda_3 = 0.170**. Positive — this World Cup is showing exactly the mutual intensity correlation the model was built to capture.

### The Six Parametric Competitors

The model doesn't just run the Bivariate Poisson and call it done. It runs **six competing parametric models daily** and selects the winner by negative log-likelihood on held-out WC2026 data:

1. **Independent Poisson** — The classical baseline. Goals independent, joint probability is the product of two Poisson PMFs.

2. **Dixon-Coles** — Extends the Poisson model with a correlation parameter rho that adjusts low-scoring joint probabilities: 0-0, 1-0, 0-1, and 1-1. When rho = 0, reduces to independent Poisson.

3. **Bivariate Poisson** — The current log-likelihood champion. Three-process model with shared latent intensity. lambda_3 = 0.170 through 11 WC2026 matches.

4. **Weibull Copula** — Models each team's goals using a Weibull distribution (heavier tails than Poisson) linked through a statistical copula. Can accommodate more high-scoring outliers than any Poisson variant.

5. **Negative Binomial** — Relaxes the Poisson constraint that variance equals the mean. Empirically, football goal data often shows overdispersion (variance > mean), which this model captures directly.

6. **Zero-Inflated Poisson** — Adds explicit probability mass at zero to handle scoreless outcomes occurring more frequently than strict Poisson predicts. Relevant for defensive matches or altitude venues.

All six compete on the same held-out data. The one with the lowest log-loss wins and feeds all upstream calculations. The winner is reselected daily as more matches accumulate — the model naturally specializes to 2026 conditions rather than being fixed to 2018/2022 patterns.

---

## Step 3: Market Reconciliation (SLSQP)

Even the Bivariate Poisson cannot know about a goalkeeper injury announced 90 minutes before kickoff. Market reconciliation solves this.

For each match, the model extracts fair market probabilities from all available bookmakers (after SHIN normalization) across as many market types as the API carries: 1X2, Over/Under totals from 0.5 through 6.5, Both Teams to Score, Draw No Bet, Double Chance, and correct score lines. Up to 6 bookmakers per market, averaged after normalization.

A constrained optimization algorithm — **SLSQP (Sequential Least Squares Programming)** — then adjusts the parametric PMF grid to satisfy these market constraints while minimizing Kullback-Leibler divergence from the original distribution. KL divergence measures how far the adjusted distribution has moved from the starting point — minimizing it ensures the optimizer moves only as far from the parametric prior as the market evidence requires. Hard constraints: all cells >= 0, sum = 1.0.

The result is a distribution that respects both the model's structural estimates and the market's current pricing. When SLSQP converges better than a simple weighted-average blend, SLSQP is used. Currently: **SLSQP dominates for virtually all matches** — only 1 non-convergence observed in 63 matches.

---

## Step 4: Calibration (Temperature Scaling)

A model is calibrated when its stated probabilities match observed frequencies. When it says 30%, outcomes should occur 30% of the time.

The model uses **temperature scaling**: a single parameter T is fitted by minimizing exact-score log loss on out-of-sample predictions from the 2018 and 2022 World Cups. The calibrated probability for each grid cell is:

    p_calibrated[h,a]  proportional to  p_raw[h,a]^(1/T)
    [then renormalized to sum to 1.0]

When T > 1, the exponent (1/T) < 1, which compresses the distribution — flattening high probabilities down and raising low ones up, correcting for overconfidence. When T < 1, it sharpens the distribution. T = 1 leaves everything unchanged.

**Current calibrated temperature: T = 1.089.** The raw parametric output is mildly overconfident — it assigns somewhat too much probability to the most likely outcomes. The correction is modest, indicating the raw model is reasonably well-calibrated before the adjustment.

Five metrics are evaluated on out-of-sample data only:
- **Exact-score NLL** (primary metric — how surprised was the model by actual final scores?)
- **Ranked Probability Score** for the 1X2 market
- **Brier score** on binary markets (BTTS, over/under)
- **Expected Calibration Error (ECE)** — direct measure of probability-to-frequency alignment
- **Ignorance score** — log score for probabilistic forecasts

---

## Step 5: Edge Screening

With a calibrated PMF, the model compares its probability estimates against the bookmaker's no-vig prices:

    Edge = (Model probability - Market implied probability) / Market implied probability

An edge of 0.08 means the model estimates the outcome is 8% more likely than the market implies, proportionally — not 8 percentage points, but 8% of the market's estimate. A 40% market-implied probability with 8% edge implies a model probability of 43.2%.

Three simultaneous filters must all pass for a market to be flagged as a value opportunity:

1. **Edge >= 4%** — minimum threshold for signal above estimation noise
2. **90% CI lower bound > market implied** — the lower bound of the model's confidence interval (computed by perturbing lambda by +/-12%) still exceeds the market price. If even the pessimistic scenario shows the model above market, the edge is real.
3. **Market implied > 2%** — thin-liquidity markets excluded due to high variance on edge estimates

Kelly sizing for flagged markets:

    f*  =  Edge / (Decimal odds - 1)
    Half-Kelly  =  f* / 2     [default]
    Hard cap: 5% of bankroll

Half Kelly is the default because the +/-12% lambda uncertainty is a fixed prior assumption, not a per-match empirical estimate. When true uncertainty exceeds the assumption, Full Kelly systematically overbets. The 5% cap is an additional hard backstop.

---

## Step 6: Closing Line Value (CLV)

Counting wins and losses is a poor way to evaluate a prediction model. A model that goes 60% on 1X2 bets might simply have been backing heavy favorites. A model that goes 48% might be consistently finding genuine value on underdogs and still be profitable.

**CLV is the industry-standard measure of whether a model has genuine edge.**

The closing line is the bookmaker's final no-vig probability immediately before kickoff — the market's best collective estimate, having absorbed every piece of publicly available information. A model that consistently predicts higher probability than where the market ultimately closes is providing information the market was slow to price in. Consistently losing to the closing line means the market was consistently smarter than the model.

**15 markets tracked per match:** The three 1X2 outcomes, BTTS Yes/No, Over/Under at 0.5, 1.5, 2.5, 3.5, 4.5, 5.5, 6.5, and Under at 1.5, 2.5, and 3.5.

Closing odds are captured automatically at **T-3 minutes before each kickoff** by a dedicated pre-match pipeline. The pipeline watches the match schedule every 15 minutes, sleeps until exactly 3 minutes before kickoff, fetches final market odds across all 15 markets, applies SHIN normalization, and records closing probabilities.

For each of the 15 markets, two numbers are tracked:
- **Model vs. closing:** Model probability minus closing fair probability. Positive = model was ahead of the market.
- **Opening drift:** Closing probability minus opening probability. A model that consistently calls the direction of market drift is demonstrating forward-looking accuracy.

---

## The Automated Pipeline

Every stage runs without human intervention, around the clock.

**Daily retraining at 8:00 AM UTC** is the full rebuild: fetch all API data, retrain all 6 parametric models on combined historical + 2026 data, rebuild composite prior, regenerate predictions for all upcoming fixtures, log calibration metrics, deploy updated JSONs. Yesterday's results are in today's predictions.

**Hourly updates** run a lighter refresh: capture odds movements, update CLV tracking, rerun predictions if newly completed matches have appeared since the daily run.

**Live snapshots every 2 minutes during match hours** (9 AM – 3 AM ET) keep the live in-play page current. When a match is detected in progress, the pipeline self-chains — each completed run immediately triggers the next — ensuring near-continuous updates. Each run fetches the current score and match clock, computes the conditional PMF, and uploads the live JSON.

**Closing odds at T-3 minutes** before each kickoff triggers the dedicated closing-line watcher, which also bootstraps the live snapshot chain at kickoff.

---

## Honest Limitations

**Regulation time only.** Extra time and penalty shootouts are not modeled. For knockout matches going to extra time, the regulation-time distribution is not the full story.

**The Bivariate Poisson substantially improves on independence but lambda_3 = 0.170 is an average.** A match in stoppage time with a team pressing for an equalizer has dramatically different dynamics than a settled 2-0 game. The live model's score-state multipliers handle this in real time, but the pre-game prior is still an approximation of match-level correlation.

**11 completed WC2026 matches is a small sample.** lambda_3, the calibration temperature T, and the dynamic WC_AVG scaling factor will all stabilize as the tournament progresses. Any parameter estimated from 11 data points carries meaningful uncertainty.

**Lambda uncertainty is a fixed prior.** The +/-12% used for confidence intervals is a conservative global assumption. For teams with extensive recent data, 12% may overstate uncertainty. For teams from data-sparse regions, it may understate it.

**Odds move between prediction and kickoff.** Edge estimates are calculated when the pipeline runs. Always verify current odds at your book before acting on any signal.

**Positive expected value does not guarantee positive returns in any finite sample.** The Kelly sizing and CI filter are designed to manage variance, not eliminate it. Football remains genuinely hard to predict. A good model makes you more informed, not omniscient.

---

*All probabilities represent regulation time (90 minutes plus stoppage time) only. Extra time and penalties are excluded. This article is for informational and educational purposes. Please gamble responsibly.*
