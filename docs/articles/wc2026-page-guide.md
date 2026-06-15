---
title: "A Guide to the World Cup 2026 Prediction Pages"
subtitle: "What every number, chart, and indicator means — and why it matters"
author: "WizardOfOdds.com"
date: "June 2026"
---

# A Guide to the World Cup 2026 Prediction Pages

Most football prediction tools give you a win probability and call it a day. This one gives you the entire joint probability distribution over every possible scoreline — the probability that the match ends 0-0, that it ends 2-1, that it ends 4-3 — and derives every betting market mechanically from that single distribution.

That architecture is not a cosmetic difference. It means every number on every page is internally consistent by construction. The Over 2.5 probability and the 1X2 probabilities cannot contradict each other the way they frequently do on aggregator sites that blend data from different sources. When you see an edge on this site, you are looking at a discrepancy between a coherent probability system and the bookmaker's price — not an artifact of mismatched models.

Three pages build on this foundation. Here is what each one shows and how to make the most of it.

---

## The Foundation: One PMF, All Markets

Every page draws from the same underlying joint score probability grid. Each cell (h, a) in that grid holds P(Home = h, Away = a) — the probability the home team scores exactly h goals and the away team scores exactly a goals in regulation time. The grid sums to exactly 1.0, enforced at every pipeline stage.

Every betting market is a different arithmetic operation on this one grid:

- **Over 2.5:** Sum all cells where h + a >= 3
- **BTTS:** Sum all cells except first row and first column
- **Home Win:** Sum all cells where h > a
- **Correct score 2-1:** The single cell at (h=2, a=1)

This is not a collection of separate models. It is one model, and all markets flow from it.

---

## Page 1 — Pre-Game Predictions

**URL:** sportsodds.wizardofodds.com/tools/odds-scanner/predictions/world%20cup/pre%20match.html

This is the command center. Every World Cup match scheduled for today appears in the main table with the model's probability estimates, expected goals, and edge analysis against live bookmaker prices. Data refreshes automatically. A red banner appears if the underlying prediction file is more than four hours old — a signal the automated pipeline may have encountered an issue.

### The KPI Cards

Four summary numbers compress the entire day's modeling output into a single glance.

**Matches Today:** The number of regulation kickoffs scheduled for today's date in Eastern Time.

**Value Bets:** The count of individual betting markets across today's matches that pass all three edge filters simultaneously: raw edge >= 4%, 90% CI lower bound still exceeds the no-vig market price, and market-implied probability > 2%. This is a strict filter. The count is frequently zero or a very small number — that is correct behavior. A well-calibrated model should not be finding edge everywhere, because the market for World Cup games is well-supplied with sharp money. When the number is zero, the model is telling you the market is fairly priced today.

**Best Edge:** The single largest edge percentage found across all today's markets, with the specific match and market identified in the sub-label. An edge of +12% on "Over 2.5, USA vs. Portugal" means the model estimates that outcome is 12% more likely than the bookmaker's no-vig price implies. This does not mean the bet will win. It means the price is favorable relative to the model's estimate. Odds move between prediction time and kickoff — always confirm the current number before acting.

**Avg xG / Match:** The average total expected goals (lambda_home + lambda_away) across today's fixtures, after market reconciliation. A figure of 2.6 means today's matches are, on average, expected to produce more than two goals per game. A figure of 2.2 reflects a slate of tighter matchups. It is a fast read on the overall goal-scoring environment before drilling into individual matches.

### The Bankroll Sizing Tool

Enter a bankroll amount and select a Kelly fraction. For every market passing all three edge filters, the tool computes a recommended dollar stake.

**Full Kelly** is theoretically optimal when edge estimates are perfectly accurate — which they never are. This model carries inherent uncertainty in its lambda estimates, so Full Kelly tends to overbet and produce large swings. Use it only when you have high confidence in the specific edge signal.

**Half Kelly** (default) divides the computed stake by two. This is the standard recommendation in the sports modeling literature when working with a model that has non-negligible parameter uncertainty. It retains most of the theoretical compounding advantage while substantially reducing drawdown risk.

**Quarter Kelly** is appropriate when you are early in the tournament with limited completed-match calibration data, or when you are spreading capital across several simultaneous positions.

All three fractions are hard-capped at 5% of your entered bankroll regardless of what the formula computes.

### The Match Table

Each row is one match. Working left to right:

**Match:** Home team vs. away team. Because WC2026 is jointly hosted, most matches are far from any team's natural home base. All fixtures are treated as neutral venue by default. The three host nations — USA, Canada, Mexico — each receive a co-host adjustment of +0.10 attack lambda and -0.10 defense lambda.

**1X2 Probability Bars:** Three colored segments proportional to regulation-time probabilities: Home Win (gold), Draw (gray), Away Win (blue). These come directly from summing the joint PMF grid — home win is all cells where home goals exceed away goals, draw is the main diagonal (0-0, 1-1, 2-2, ...), away win is all cells where away goals exceed home goals. The fair American odds next to each bar are derived from those probabilities with no bookmaker margin.

**O/U 2.5:** The probability the match produces 3 or more total goals — the sum of all grid cells where h + a >= 3. Above 55% means the model leans toward higher scoring. Below 45% suggests a tight match.

**BTTS:** Both Teams to Score — the probability each team scores at least once. It is everything in the joint grid except the first row (home team scores zero) and first column (away team scores zero). A BTTS probability of 35% means there is a meaningful chance one team gets shut out.

**Top Score:** The single most probable final scoreline and its probability — the peak cell of the joint PMF grid. For most group-stage matches this is 1-0 or 1-1, typically carrying 12–18% probability.

**xG (H-A):** The model's expected goals for each team separately — lambda_home and lambda_away after market reconciliation. These two numbers tell the entire story of the match. A line of 1.8-0.7 is a clear favorite-underdog situation. A line of 1.2-1.1 is near a coin flip. If you see 2.1-0.5, you are looking at a dominant favorite expected to control the match end-to-end.

**Best Edge / Fair Odds:** The highest-edge market for this specific match passing all three filters. If no market passes, the cell is empty. Fair odds are the model's no-margin American odds for that outcome.

### The Expanded Row

Click any match row to reveal three additional panels.

**Full Scoreline Distribution:** All non-trivial scorelines ranked from most to least likely, with proportion bars. These are raw joint PMF values. For correct-score betting: if a book is offering American odds on score S, convert to no-vig fair probability and compare to the model's probability for that cell.

**All Markets:** Every market the engine has priced from the joint grid — 1X2, BTTS, Over/Under at every standard line from 0.5 through 6.5 goals, Draw No Bet, Double Chance, Win to Nil, Asian Handicap -0.5, and team-level totals. Every single number here flows from the same underlying distribution.

**Edge Report:** For each market: model probability, market no-vig implied probability (averaged across up to 6 bookmakers after SHIN normalization), edge percentage, fair odds, and current market odds. Rows highlighted in gold have passed all three value filters. The Kelly Stake column reflects whatever bankroll and fraction you entered above.

**How to use this page:** Start with the KPI cards to calibrate expectations for the day. Scan the table for matches with a non-zero Best Edge. Expand any such match, read the full Edge Report, and verify current odds at your preferred book before placing anything.

---

## Page 2 — Probability Distributions

**URL:** sportsodds.wizardofodds.com/tools/odds-scanner/predictions/world-cup/pre-match/Probability%20Distributions.html

Where Page 1 compresses model output into a single row per match, this page opens it completely. Select a match using the navigation chips at the top and every chart updates immediately to show the full probability landscape — not just the most likely result, but the entire distribution.

### Chart 1 — Joint Score PMF Heatmap

The heatmap is the model in its purest form. Every cell (h, a) shows the probability the home team scores exactly h goals and the away team scores exactly a goals. Home goals on the vertical axis, away goals on the horizontal.

The color scale uses the **square root** of each cell's probability relative to the grid maximum. This is deliberate: without the square root transformation, cells with probabilities above 8% would appear bright and everything else would look uniformly dark. The square root separates moderate-probability cells (3–5%) from near-zero ones, giving a usable visual representation of the entire distribution.

Every betting market is readable directly from this heatmap. Over 2.5 is the upper-right region where h + a >= 3. A home clean sheet is the entire first column (a = 0). BTTS is everything except that first column and first row. A correct score bet on 2-1 is a single cell.

The **tail mass** shown below the heatmap is the probability assigned to scores beyond the grid boundary. In practice vanishingly small, but it must exist to ensure the grid sums to exactly 100%.

### Chart 2 — Marginal Goal Distributions

Two bar charts side by side. The left shows the probability the home team scores exactly k goals (k = 0, 1, 2, ...). The right shows the same for the away team. These marginals are computed by collapsing the heatmap along each axis:

    P(Home = h) = SUM over all a of P(Home = h, Away = a)

The shape tells you a lot quickly. A tall bar at k = 0 means this team is frequently shut out — the model sees a high probability of them failing to score. A relatively flat distribution across k = 1 and k = 2 reflects a strong attacking rate. In most World Cup group matches, the tallest bar sits at k = 1 for both teams.

### Chart 3 — Total Goals Distribution

The probability of each possible total goal count, computed by summing all cells along each anti-diagonal (all cells where h + a = k contribute to the bar at k total goals).

Standard over/under lines (0.5, 1.5, 2.5, 3.5, 4.5, 5.5) appear as vertical dividers. The probability to the right of any divider is the Over probability for that line; to the left is the Under. This chart makes the model's view of the entire total-goals market visible at once.

### Chart 4 — Goal Difference Distribution

Centered on zero, this bar chart shows the probability of each possible goal difference (home goals minus away goals). Gold bars indicate home wins, gray indicates draws, blue indicates away wins.

This is probably the most intuitive single chart on the page. A heavily gold-skewed distribution means the home team is a clear favorite. A roughly symmetric distribution means the match is genuinely even. High-scoring expected matches tend to have shorter gray bars because draws become less probable when both teams are expected to score frequently.

### Chart 5 — Top 20 Most Likely Scorelines

A ranked bar chart of the 20 most probable individual final scores with exact percentages and fair American odds next to each bar.

As a general reference: the top cell in most group-stage matches carries 12–20% probability. Any score showing above 6% is in the top tier of the distribution. The fair American odds shown here have no bookmaker margin — they represent what a perfectly calibrated market would offer for that score. If your sportsbook is offering better odds than shown, you may have found a value opportunity. If offering significantly worse, the book is priced tighter than the model.

### O/U Lines Table

A simple table listing Over and Under probabilities for every standard total line from 0.5 through 6.5. All computed directly from the joint PMF.

**How to use this page:** When you find an interesting match on Page 1, come here for the full picture. The heatmap shows where probability is concentrated. The goal difference chart shows how result probabilities break down. The top scorelines chart helps evaluate correct-score prices at your book. If a scoreline offered at +550 American shows a model probability of 12%, that is +550 against a fair price of around +733 — a meaningful gap worth investigating.

---

## Page 3 — Live In-Play PMF

**URL:** sportsodds.wizardofodds.com/tools/odds-scanner/predictions/world-cup/live/Probability%20Distributions.html

This page activates when a World Cup match is in progress. When no match is live, it shows the next scheduled kickoff. All probabilities are regulation time only — 90 minutes plus stoppage time.

### How the Live Model Differs from Pre-Game

The pre-game model asks: what will the final score be from kickoff? The live model asks something more specific: **given that the current score is H-A at minute t, what will the final score be?**

That distinction is fundamental. Once a match is in progress, some final scores have become impossible. If the match is 2-1 in the 70th minute, the final score cannot be 1-0, 0-0, or 2-0. Those grid cells are locked at zero probability. The remaining probability redistributes entirely across the reachable scores. This is conditional probability — it is what separates a proper live model from a pre-game model that simply gets refreshed on a timer.

The live model also changes how it estimates remaining goal-scoring rates. Rather than assuming a constant rate across 90 minutes, it uses a **non-homogeneous hazard model** — goal rates vary by match minute, calibrated from the minute-by-minute goal distribution across the 2018 and 2022 World Cups. Rates are below average in the first 10 minutes as teams settle in, rise through the mid-half, spike just after half-time, and peak in the final minutes when teams chasing a goal commit forward.

On top of the temporal baseline, **score-state multipliers** adjust each team's rate based on the current scoreline, calibrated from World Cup data and the football forecasting literature:

| Score State                  | Home Rate | Away Rate |
|------------------------------|-----------|-----------|
| Draw at minute 60 or later   | x1.10     | x1.10     |
| Home team losing by 1        | x1.25     | x1.05     |
| Home team losing by 2 or more| x1.40     | x1.10     |
| Home team winning by 1       | x0.90     | x1.10     |
| Home team winning by 2 or more| x0.80    | x1.15     |

When live expected goals (xG) data is available from BallDontLie, the model blends the live xG-derived rate (60% weight) with the pre-game prior (40% weight). This blend activates at minute 15 — before that, live xG from a small number of shots is too noisy to be useful. By minute 70, the live model is genuinely tracking the actual shot volumes and quality observed in the match, not just the pre-game forecast.

### Connection Badge

A small indicator shows how the page is receiving data.

**WebSocket (green):** The browser has an active push connection to the live prediction server. When a goal or status change is reported, the server recomputes the full conditional PMF and pushes it to all connected browsers — typically within 200 milliseconds. No manual refresh needed.

**Polling (yellow):** The push connection is unavailable. The page fetches updated data from a static JSON file every 60 seconds. Updates arrive with up to a one-minute delay. This is the automatic fallback mode.

### Live KPI Cards

**Matches Live:** Number of World Cup matches currently in progress.

**Next Kickoff:** Next scheduled match with its Eastern Time kickoff, useful when no match is currently live.

**Goals Today:** Total goals scored across all live and recently completed matches in the current matchday.

**Data Age:** Time elapsed since the last live snapshot was generated. Under 2 minutes is normal during a live match. Above 10 minutes triggers a health warning banner.

### Win Probability Bar

The same three-segment bar as on Page 1 — Home Win (gold), Draw (gray), Away Win (blue) — but now conditional on the current score and minute. Watch this bar during a live match and you see the model's view shifting in real time. A home goal pushes the gold segment rightward immediately.

These are conditional probabilities: the probability of each regulation-time outcome given the match is currently H-A at minute t.

### Pre-Game to Live Shift Table

Directly below the win probability bar: for each main market, the pre-game probability, the current live probability, and the arithmetic difference. A large positive shift on Home Win combined with large negative shifts on Draw and Away Win tells you the home team has taken control of a match that was expected to be closer. Reading the shift table alongside the current score gives a clear picture of how the match is deviating from the pre-game expectation.

### Win Probability Sparkline

A compact line chart showing the home team's win probability from kickoff to the current minute. This history accumulates in your browser session and resets on page reload. Sharp upward jumps correspond to home goals; sharp downward drops correspond to away goals. The sparkline shows not just the current probability but whether the home team earned it gradually or in a single dramatic moment.

### Live Joint Score PMF Heatmap

The same heatmap structure as on Page 2, updated with every live snapshot and annotated with two visual cues.

The cell corresponding to the current live score is **outlined in red**. All unreachable cells — any score where home goals are below the current home tally or away goals are below the current away tally — are forced to zero and appear dark. As the match progresses, the dark region grows and probability concentrates into fewer and fewer bright cells.

In stoppage time of a 1-0 match, the heatmap may assign 85–90% probability to the single 1-0 cell. The rest is split between 1-1 (away team equalizes), 2-0 (home team extends the lead), and a handful of other reachable scores. That visual concentration of color into one or two cells in the final minutes is a powerful picture of what is at stake.

### Next Goal Probabilities

Three values derived from the remaining expected goals lambda_h_rem and lambda_a_rem:

    Home scores next:  lambda_h_rem / (lambda_h_rem + lambda_a_rem)
    Away scores next:  lambda_a_rem / (lambda_h_rem + lambda_a_rem)
    No more goals:     e^(-lambda_h_rem) x e^(-lambda_a_rem)

**Home scores next** and **Away scores next:** Given that at least one more goal is scored before the final whistle, what is the probability it belongs to each team?

**No more goals:** The joint probability that both teams produce zero additional goals and the match ends at the current score. This is the Poisson probability of zero events from two independent processes. As the match enters stoppage time with small remaining expected goals, this value typically climbs above 80–90%.

### Top 10 Most Likely Final Scores (Live)

The same ranked list as on Page 2, restricted to reachable outcomes only. The current live score is marked. As the match approaches the final whistle, the probability on the leading score climbs rapidly — in an 88th-minute 1-0 match, the 1-0 cell may carry 8 or 9 times the probability it held before kickoff.

### Marginal Charts

Bar charts for each team showing the probability they score exactly k regulation-time goals, derived from the live PMF. Values below each team's current goal count are zero — those are no longer possible outcomes.

**How to use this page:** The live page is most useful in two situations. First, during fast-moving matches where the pre-game expectation is being rapidly revised — a scoreline of 2-0 in the 30th minute will have completely reshaped the probability distribution. Second, when evaluating live betting markets: compare the No More Goals probability against your book's live Under line, or compare the Next Goal fractions against live next-scorer pricing. The model's conditional probabilities update every 90 seconds, giving you a continuously refreshed view.

---

## Scope and Limitations — All Pages

**Regulation time only.** All probabilities on all three pages represent 90 minutes plus stoppage time. Extra time and penalty shootouts are not included.

**lambda_3 = 0.170 substantially reduces but does not eliminate the independence approximation.** The Bivariate Poisson model captures the positive correlation between home and away goals, but it represents an average across match types. Live score-state multipliers handle the tactical dynamics in real time.

**Live pipeline latency.** The stated target of under 200 milliseconds for WebSocket updates applies under normal conditions. Network latency and server load can affect real-time delivery.

**Small calibration sample.** Calibration is based on 128 World Cup matches from 2018 and 2022, augmented by completed 2026 matches. As the 2026 tournament progresses, all parameters — lambda_3, calibration temperature T, and WC_AVG scaling — will stabilize with a larger sample.

**Edge estimates are outputs of a probabilistic model.** Market odds move between the time predictions are generated and kickoff. Verify current prices at your book before acting on any signal shown here.

---

*All probabilities represent regulation time (90 minutes plus stoppage time) only. Extra time and penalties are excluded. This guide is for informational and educational purposes. Please gamble responsibly.*
