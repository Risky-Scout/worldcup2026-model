WIZARDOFODDS.COM
How the 2026 World Cup Prediction Model Works
A complete guide to the mathematical methods behind the joint score probability engine.

---

INTRODUCTION

This model produces a Probability Mass Function (PMF) for the final score of every 2026 FIFA World Cup match. For each match, it computes P(Home goals = h, Away goals = a) across every possible regulation-time scoreline, where regulation time means 90 minutes plus stoppage time. Extra time and penalty shootouts are explicitly excluded from every probability shown.

Every derived number — match result probabilities (1X2), over/under totals, both teams to score (BTTS), draw no bet, double chance, win to nil, Asian handicap, correct scores, and team-level totals — is obtained by summing the appropriate cells of this single joint distribution. There is no separate model per market type; the PMF is the entire model, and every market price flows from it mechanically.

The full grid, including an explicit tail-mass bucket for extreme scores beyond the grid, sums to exactly 1.0. This constraint is enforced at every pipeline stage.

The model is trained on completed World Cup matches from 2018 and 2022 (128 matches combined) and, as the 2026 tournament progresses, on completed 2026 matches with significantly higher recency weighting. As of the current date, 8 completed 2026 World Cup matches are included in the training data.

---

STEP 1: RATING EVERY TEAM — THE COMPOSITE PRIOR

The first task is assigning each of the 48 World Cup teams an attack lambda (λ_att) and a defense lambda (λ_def). These represent expected goals scored and conceded against an average opponent on a neutral pitch. The World Cup-calibrated global average is 1.30 goals per team per match, derived from 2018 and 2022 results.

Rather than relying on a single rating source, the model blends six independent information streams. This reflects a core conviction in quantitative forecasting: no individual rating system is complete, and a diversified composite is more stable than any single source.

The six sources and how they are weighted when a full market is available:

  1. Market-implied strength (20%)
     Extracted from bookmaker odds for each team's group-stage matches via the BallDontLie API. Up to six separate sportsbooks are consulted per match (FanDuel, DraftKings, BetMGM, BetRivers, Caesars, Fanatics). The bookmaker margin is removed from all odds using SHIN normalization before any probability is read — this is critical, as raw quoted odds include a built-in margin of roughly 5–8% and cannot be treated as fair probabilities. From the no-vig 1X2 probabilities, the model reverse-engineers what attack and defense lambdas would produce exactly those market probabilities via goal expectancy decomposition. These market-implied lambdas carry 20% of the blending weight. The 20% figure is empirically backed: analysis of completed matches showed that using zero market weight produced a mean absolute difference of 18.3 percentage points between model PMF-derived probabilities and the market's no-vig 1X2, while 20% weight reduced that gap to 15.1 percentage points with better CLV positioning than higher weights.

  2. FIFA World Ranking (March 2026) (~12%)
     FIFA's official points system, converted to an attack lambda through a calibrated sigmoid mapping. The FIFA ranking captures long-run international performance across all competitions and provides a reliable signal for teams with sparse recent competitive data.

  3. Qualifying record (~10%)
     Each team's attack and defense efficiency from their qualifying campaign, Bayesian-shrunk toward confederation averages based on the number of competitive matches played. This captures tournament-specific form: a team that steamrolled its region to qualification is genuinely more dangerous than one that scraped through.

  4. Pi rating (penaltyblog, ~30% of remainder)
     The Pi rating is a goal-margin-sensitive Elo variant that updates after every international match. Because it incorporates the score of each match — not just the result — it is more responsive to genuine performance shifts than win/loss-only systems. Pi ratings are favored over Elo in this blend specifically because the model's primary objective is predicting scores, not results.

  5. Elo rating (penaltyblog, ~55% of remaining weight after Pi)
     Classic win/loss-based international Elo. More stable over long periods than Pi but less sensitive to recent form shifts. Included as a stabilizing floor that prevents the prior from reacting too sharply to a single unusual result.

  6. Confederation baseline (soft floor, ~5%)
     Historical World Cup attack averages by confederation: CONMEBOL 1.45, UEFA 1.35, CONCACAF 1.20, CAF 1.10, AFC 1.10, OFC 0.90. Defense baselines are the mirror image. This floor prevents any team from receiving a lambda estimate that is wildly inconsistent with its confederation's historical World Cup scoring environment. It carries more weight for teams where other rating sources are absent or sparse.

When no market odds are available for a team (as may occur early in the tournament before lines are posted, or for certain group-stage matches), the market-implied source is excluded and the remaining sources expand proportionally to fill its 20% share.

Co-host advantage: USA, Canada, and Mexico each receive +0.10 to attack lambda and −0.10 to defense lambda as the joint 2026 hosts. All other matches are treated as fully neutral venue.

Altitude adjustment: Three venues carry measurable altitude effects that reduce scoring rates for unacclimated teams. Both teams' lambdas are scaled equally since neither side enjoys a familiarity advantage at these venues during a World Cup:
 • Estadio Azteca (Mexico City, 2,230m): 0.93× multiplier — approximately 7% scoring reduction
 • Estadio Akron (Guadalajara, 1,560m): 0.97× multiplier — approximately 3% reduction
 • Estadio BBVA (Monterrey, 530m): no adjustment (negligible elevation)

Tournament adjustment: Once 2026 World Cup matches are completed, the model incorporates their results into each team's composite rating through a Bayesian shrinkage mechanism. For each team that has played n World Cup matches, the tournament adjustment factor is shrunk toward 1.0 with weight n / (n + 3), where 3 is the prior strength (equivalent to believing three prior matches are as informative as one actual World Cup match). This prevents overreaction to a single game — a team that conceded three goals in one match is not immediately penalized as if their entire defense collapsed, but a team that has scored freely in multiple games earns a genuine upward revision. Adjustments are capped at ±30% in either direction. Currently, 16 teams have active tournament adjustments applied from 8 completed 2026 World Cup matches.

---

STEP 2: THE PARAMETRIC MODEL COMPETITION

With the composite prior providing team lambdas, the model does not stop at a simple Poisson calculation. Instead, it runs a competition among six distinct parametric goal models, all fitted on the combined historical and 2026 training data, and selects the model that best fits the available World Cup evidence. The six models are:

 1. Independent Poisson — the classical baseline. Goals for each team are independent Poisson random variables with means λ_home and λ_away.
 2. Dixon-Coles — extends the Poisson model with a correlation parameter ρ (rho) that adjusts the joint probability of low-scoring outcomes (0–0, 1–0, 0–1, 1–1). Calibrated rho from World Cup data currently sits at 0.0, indicating that the goal-independence assumption holds reasonably well in high-stakes international matches.
 3. Bivariate Poisson — explicitly models positive correlation between home and away goals through a shared latent Poisson component.
 4. Weibull Copula — models the marginal goal distributions as Weibull rather than Poisson, capturing the heavier tails of the observed goal distribution.
 5. Negative Binomial — relaxes the Poisson variance assumption, allowing the goal variance to exceed the mean (overdispersion), which is observed in some football datasets.
 6. Zero-Inflated Poisson — adds an explicit probability mass at zero to account for the higher frequency of goalless halves and matches than strict Poisson predicts.

Each model is fitted on the full training dataset: 128 historical World Cup matches (2018 + 2022) combined with all completed 2026 World Cup matches. Critically, the 2026 matches receive a much higher training weight than the historical data. The Dixon-Coles time-decay parameter ξ (xi) is set to 0.010 for 2026 matches versus 0.0018 for historical matches — this ensures the model's parametric structure adapts quickly to the specific scoring patterns of the 2026 tournament rather than being anchored to patterns from four and eight years ago.

The competition is run on out-of-sample World Cup data using a walkforward backtest. The model with the lowest negative log-likelihood on held-out matches is selected as the daily champion and used to generate PMF grids for all upcoming fixtures. The champion model can change from day to day as more 2026 matches accumulate, which means the model naturally becomes more specialized to the 2026 tournament as the group stage progresses.

---

STEP 3: MARKET RECONCILIATION

The composite prior provides strong fundamental ratings. The bookmaker market provides real-time information that no rating system has access to: late team news, undisclosed injuries, tactical signals, line-movement driven by sharp money. Market reconciliation incorporates this information without discarding the prior's structural advantage.

For each match, fair market probabilities are extracted from all available bookmakers (after SHIN normalization to remove their margin) for as many market types as BallDontLie carries: match result (1X2), correct score lines, over/under total goals at all available lines, both teams to score, draw no bet, and double chance. Up to six bookmakers are consulted; their no-vig probabilities are averaged to produce consensus fair probabilities for each market.

A constrained optimization (SLSQP algorithm) then adjusts the initial parametric PMF grid to simultaneously satisfy all these market constraints while minimizing the Kullback-Leibler divergence from the original distribution. The optimization operates on the full PMF grid subject to two hard constraints: all cell values must be non-negative, and they must sum to 1.0. The result — the market-reconciled PMF — is a distribution that respects both the model's fundamental structural estimates and the market's current real-time pricing.

When market odds are unavailable for a match (which can occur for distant knockout-stage matches with no lines posted yet), the unreconciled parametric PMF is used directly.

The reconciliation method is labeled in each prediction (blend or slsqp). When the SLSQP optimizer converges to a better solution than a weighted-average blend, SLSQP is selected; otherwise the blend is used. In practice, SLSQP dominates for matches where the market's implied probabilities differ materially from the pure parametric prior — exactly the matches where market information is most valuable.

---

STEP 4: CALIBRATION

A well-calibrated model is one where outcomes assigned 30% probability occur approximately 30% of the time, outcomes assigned 70% probability occur approximately 70% of the time, and so on across every probability level. Calibration is distinct from accuracy — a model can assign correct average probabilities while being systematically overconfident or underconfident about specific outcomes.

The model uses temperature scaling: a single parameter T is fitted by minimizing exact-score log loss on out-of-sample predictions from the 2018 and 2022 World Cups. The adjusted probability for each cell is:

  p_calibrated[h, a]  =  p_raw[h, a] ^ (1 / T)  (renormalized to sum to 1.0)

T greater than 1 indicates overconfidence — the raw distribution is too peaked — and the exponent flattens it. T less than 1 indicates underconfidence and sharpens the distribution. T equal to 1 leaves the distribution unchanged. The current calibrated temperature is T = 1.127, indicating mild overconfidence in the raw parametric output, consistent with football models trained on limited World Cup data.

The Dixon-Coles rho parameter is also calibrated from actual World Cup match data rather than using the league-football default of −0.05. The current calibrated rho is 0.0, meaning that the independence assumption for home and away goals performs adequately on World Cup data and no explicit low-score correction is applied.

Calibration is evaluated across five metrics, all computed on out-of-sample predictions only:

 Exact-score log loss: The primary metric. Measures how surprised the model was, on average, by actual final scores. Lower is strictly better; a perfect model would achieve a score of 0 (though any real model will be far above this on football data).

 Ranked Probability Score (RPS): Standard metric for ordered categorical outcomes, applied to the 1X2 market. RPS penalizes probability mass placed far from the correct outcome more heavily than mass placed close to it.

 Multiclass Brier score: Mean squared error across the three match result categories. A simpler alternative to RPS that weights all errors equally regardless of distance.

 Expected Calibration Error (ECE): A direct measure of the gap between stated probabilities and observed frequencies, computed by binning all predictions into probability bands and measuring the gap within each band.

 Ignorance score: The log score for probabilistic forecasts — identical to log loss, applied here to the 1X2 market specifically.

Important caveat: the combined 2018 and 2022 dataset contains only 128 matches. These metrics carry substantial statistical uncertainty at this sample size. The temperature correction is a useful coarse adjustment, but it should not be interpreted as a guarantee of statistical accuracy at any specific probability level.

---

STEP 5: EDGE SCREENING

Once the calibrated PMF is available for a match, the model compares every available market probability against the corresponding no-vig bookmaker probability. The edge on any outcome is:

  Edge = (Model probability − Market implied probability) / Market implied probability

An edge of 0.08 means the model believes the outcome is 8% more likely than the market is pricing it, relative to the market price. A market is flagged as a potential value opportunity only when all three conditions hold simultaneously:

 • Edge ≥ 4% (minimum threshold for meaningful signal over estimation noise)
 • The lower bound of the model's 90% confidence interval exceeds the market implied probability. The CI is computed by perturbing each team's λ by ±12% — a conservative fixed assumption about uncertainty in the lambda estimates — and taking the resulting range of PMF-derived probabilities. Only markets where even the pessimistic lambda scenario still shows model edge pass this filter.
 • Market implied probability > 2% (markets with under 2% implied probability are excluded due to thin liquidity and high variance in the edge estimate)

Markets passing all three filters are displayed as value opportunities. Kelly sizing is applied to each:

  Full Kelly fraction = Edge / (Decimal odds − 1)
  Half Kelly = Full Kelly / 2
  All stakes capped at 5% of bankroll

Half Kelly is the default because the ±12% lambda uncertainty assumption is a fixed prior, not an empirically derived estimate. When the true lambda uncertainty is higher than assumed — as is likely early in a tournament with limited completed matches — Full Kelly overbets. The 5% cap provides a hard upper limit regardless of the computed fraction.

---

STEP 6: CLOSING LINE VALUE TRACKING

The model tracks its performance against the betting market using a metric called Closing Line Value (CLV). For every scheduled match, the model records its predicted probabilities at the time of prediction (opening odds from the market at that time). Approximately three minutes before each match kicks off, the model captures the final closing odds from the market. After the match, outcomes are settled.

For each of 15 markets per match — 1X2, BTTS Yes/No, Over/Under at 0.5, 1.5, 2.5, 3.5, 4.5, 5.5, 6.5 goals, and Under at 1.5, 2.5, 3.5 — the model computes:

 Model vs. closing: (model probability at prediction time) − (market's closing fair probability). A positive number means the model was predicting a higher probability than where the market ultimately settled — a sign that the prediction was ahead of the market's information flow.

 Opening drift: (closing probability) − (opening probability). How much the market moved from the time of the original prediction to the moment before kickoff. Large opening drift indicates significant information was incorporated by the market between prediction and close.

A model that consistently beats the closing line on a large sample of markets is demonstrating genuine forecasting edge, not just lucky outcomes. The closing line is considered the market's best collective estimate of the fair probability immediately before the event, having absorbed all available public information. Beating it indicates the model's predictions contain information that the full-information market did not have — or correctly weighted information the market was slow to incorporate.

Currently 71 matches are tracked across all 15 markets, with 94% of records having opening market odds. Closing odds capture begins for each match approximately at the T-3 minute mark via an automated pre-match pipeline that runs specifically for this purpose.

---

THE AUTOMATED PIPELINE

Every stage above runs automatically every day without human intervention.

Daily retraining (8:00 AM UTC): The full pipeline runs once per day. It fetches fresh data from the BallDontLie API — match results, bookmaker odds from up to six vendors, team statistics, expected goals, shot data, match events, and group standings. The parametric models are retrained on the combined historical + 2026 dataset with the day's newly completed matches added. The composite prior is rebuilt. All predictions for upcoming matches are regenerated. Calibration metrics are logged. The updated prediction JSON files are deployed to the server. This daily retraining is what allows the model to incorporate yesterday's match results into today's predictions and to recalibrate continuously as the tournament provides new evidence.

Hourly updates (every hour, all 24): A lighter pipeline refresh runs every hour throughout the day. This captures odds movements from bookmakers, updates CLV tracking records, and reruns predictions if new completed matches are detected in the cache that were not present at the daily run time. The hourly pipeline ensures that the web pages reflect the latest market pricing even when the daily run has already completed.

Live snapshots (every 2 minutes during match hours, self-chaining): During match hours (approximately 9:00 AM to 3:00 AM Eastern Time), a live snapshot pipeline runs every two minutes. When a match is detected as in progress, the pipeline self-chains — each run triggers the next immediately upon completion — ensuring near-continuous updates rather than depending on GitHub's scheduled cron system, which can throttle runs during busy periods. The live snapshot fetches the current score and match clock from BallDontLie, computes the conditional PMF, and uploads the live JSON to the server. The live page updates automatically.

Closing odds capture (T-3 minutes before each kickoff): A separate pre-match pipeline watches the schedule every 15 minutes. When a match is detected within the next 15 minutes, the pipeline sleeps until exactly 3 minutes before kickoff, fetches the final market odds, applies SHIN normalization, records the closing probabilities across all 15 tracked markets, and commits the updated CLV records. It then bootstraps the live snapshot chain by triggering the first live run at kickoff, guaranteeing the live chain starts even if the regular cron is throttled.

---

LIMITATIONS AND SCOPE

All probabilities represent regulation time only (90 minutes plus stoppage time). Extra time and penalty shootouts are not modeled.

The Poisson independence assumption is an approximation. Teams adjust tactically after goals — a team going behind pushes forward, altering both teams' subsequent scoring rates. Market reconciliation captures some of this correlation implicitly, but the structural assumption of independence remains. The Dixon-Coles rho parameter corrects for this specifically at low-scoring outcomes, though its current calibrated value of 0.0 suggests the correction is minimal in World Cup data.

Calibration dataset limitations: 128 historical World Cup matches is a small sample by the standards of sports modeling. Calibration metrics at this sample size carry meaningful statistical uncertainty. As the 2026 tournament adds completed matches to the training set, this limitation diminishes.

Lambda uncertainty is fixed at ±12% for confidence interval calculations. This is a conservative prior assumption, not an empirically derived per-match estimate. The true uncertainty varies with the quality and recency of available data for each team and may be higher for teams with limited recent competitive history.

Odds used for edge calculations are sourced at the time the pipeline runs. Odds move between pipeline execution and kickoff. Always verify current market prices before acting on any signal in the edge report.

Edge estimates are outputs of a probabilistic model. They are not guaranteed profit signals. Positive long-run results depend on both the model's edge being real and odds being available at or near the predicted levels at the time of betting.

---

All probabilities represent regulation time (90 minutes + stoppage time) only. Extra time and penalties are excluded.
This article is for informational and educational purposes. Please gamble responsibly.
