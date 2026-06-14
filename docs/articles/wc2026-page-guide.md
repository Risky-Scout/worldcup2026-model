---
title: "A Guide to the World Cup 2026 Prediction Pages"
subtitle: "What every number, chart, and indicator means -- and why it matters"
author: "WizardOfOdds.com"
date: "June 2026"
---

# A Guide to the World Cup 2026 Prediction Pages

Most football prediction tools give you a win probability and call it a day. This one gives you the entire joint probability distribution over every possible scoreline -- the probability that the match ends 0-0, that it ends 2-1, that it ends 4-3 -- and derives every betting market mechanically from that single distribution. There is no separate model for over/under. No separate model for BTTS. Every number you see on every page flows from one source of truth: a grid of probabilities over final scores.

That architecture matters because it means the numbers are internally consistent. The over 2.5 goals probability and the 1X2 probabilities cannot contradict each other the way they often do on aggregator sites that pull from different sources. When you see an edge on this site, you are seeing a discrepancy between a coherent probability system and the bookmaker's price -- not an artifact of mismatched models.

Three pages build on this foundation. Here is what each one shows, and how to make the most of it.

---

## Page 1 -- Pre-Game Predictions

**URL:** sportsodds.wizardofodds.com/tools/odds-scanner/predictions/world%20cup/pre%20match.html

This is the command center. Every World Cup match scheduled for today appears in the main table with the model's probability estimates, expected goals, and edge analysis against live bookmaker prices. The data refreshes automatically and a red banner appears if the underlying prediction file is more than four hours old -- a signal that the automated pipeline may have encountered an issue.

### The KPI Cards

Four summary numbers sit at the top of the page. They compress the entire day's modeling output into a single glance.

**Matches Today** is exactly what it says: the number of regulation kickoffs scheduled for today's date in Eastern Time.

**Value Bets** counts the individual betting markets across all of today's matches that pass all three of the model's edge filters simultaneously: a raw edge of at least 4%, a 90% confidence interval whose lower bound still exceeds the market's no-vig price, and a market-implied probability above 2%. This is a strict filter, and the count is frequently zero or a very small number. That is correct behavior. A well-calibrated model should not be finding edge everywhere, because the market for World Cup games is well-supplied with sharp money. When the number is zero, the model is telling you the market is fairly priced today. When it shows 3 or 4 markets, it is worth reading closely.

**Best Edge** is the single largest edge percentage found across all today's markets, with the specific market and match identified in the sub-label. An edge of, say, +12% on "Over 2.5 Goals, USA vs. Portugal" means the model estimates that outcome is 12% more likely than the bookmaker's no-vig price implies. It does not mean the bet will win -- it means the model believes the price is favorable. Odds move between prediction time and kickoff, so always confirm the current number before acting.

**Avg xG / Match** is the average total expected goals across today's fixtures. Expected goals here are the rate parameters that feed the joint score distribution -- the model's best estimate of how many goals each team will score against a neutral opponent under current conditions. A figure of 2.6 means today's matches are, on average, expected to produce more than two goals per game. A figure of 2.2 reflects a slate of tighter, defensive matchups. It is a fast read on the overall goal-scoring environment before you drill into individual matches.

### The Bankroll Sizing Tool

Enter a bankroll amount and select a Kelly fraction. For every market that passes all three edge filters, the tool computes a recommended dollar stake.

The **Kelly criterion** is a formula for sizing bets to maximize long-run bankroll growth given an edge. The formula is: f* = edge / (decimal odds - 1). If you have a 10% edge on a market paying +200 American odds (3.00 decimal), Full Kelly says bet 10% / (3.00 - 1) = 5% of your bankroll.

**Full Kelly** is theoretically optimal when edge estimates are perfectly accurate. They never are. This model carries inherent uncertainty in its lambda estimates, so Full Kelly tends to overbet and produce large swings. Use it only when you have high confidence in the edge signal for that specific market.

**Half Kelly** divides the computed stake by 2. This is the default and the standard recommendation in the sports modeling literature when working with a model that has non-negligible parameter uncertainty. It retains most of the theoretical compounding advantage while substantially reducing drawdown risk.

**Quarter Kelly** is appropriate when you are less certain about the model's edge -- either because you are early in the tournament with limited completed-match data, or because you are spreading capital across several simultaneous positions.

All three fractions are hard-capped at 5% of your entered bankroll regardless of what the formula computes.

### The Match Table

Each row is one match. Working left to right:

**Match** shows the two teams. Because World Cup 2026 is hosted jointly by the United States, Canada, and Mexico, nearly every match is played far from any team's natural home base. The model treats all fixtures as neutral-venue by default. The three host nations -- USA, Canada, and Mexico -- each receive a small co-host adjustment of +0.10 to attack lambda and -0.10 to defense lambda, reflecting the measurable advantages of familiar geography, minimal travel, and home crowd presence. Every other team plays as though on a neutral pitch.

**1X2 Probability Bars** show the three-segment distribution for regulation-time result: Home Win (gold), Draw (gray), Away Win (blue). These come directly from summing cells of the joint score grid -- home win is all cells where home goals exceed away goals, draw is all cells on the main diagonal (0-0, 1-1, 2-2, and so on), away win is all cells where away goals exceed home goals. The American odds next to each bar are the model's fair prices, derived from those probabilities with no margin added. If the bar is almost entirely gold with a small gray sliver and a thin blue edge, you are looking at a heavy favorite.

**O/U 2.5** is the probability that the match produces 3 or more total goals. It is the sum of all grid cells where home goals plus away goals is at least 3. A number above 55% means the model leans toward a higher-scoring game; below 45% suggests a tight match.

**BTTS** is Both Teams to Score -- the probability that each team scores at least once. It is everything in the joint grid except the first row (home team scores zero) and the first column (away team scores zero). A BTTS probability of 35% means there is a good chance one of these teams gets shut out.

**Top Score** is the single most probable final scoreline and its percentage -- the peak cell of the joint grid. For most World Cup group matches this is 1-0 or 1-1, each typically carrying somewhere between 12% and 18% probability. In a match with extreme expected goals asymmetry, you might see something like 2-0 at the top.

**xG (H-A)** shows the model's expected goals for each team separately -- the rate parameters lambda_home and lambda_away after market reconciliation. These two numbers tell you the entire story of the match. A line of 1.8 - 0.7 is a clear favorite-versus-underdog; the favorite is expected to score more than twice as much. A line of 1.2 - 1.1 is a near coin flip. If you see 2.1 - 0.5, you are looking at a dominant favorite that the model expects will control the match from start to finish -- games like that see heavy action on home win and over markets.

**Best Edge / Fair Odds** shows the highest-edge market for this specific match that passes all three filters. If no market passes, the cell is empty. Fair odds are the model's no-margin American odds for that outcome.

### The Expanded Row

Click any match row to reveal three additional panels.

The **Full Scoreline Distribution** ranks all non-trivial scorelines from most to least likely, with proportion bars showing each one. These are raw joint grid values. For correct-score betting: if a book is offering American odds on scoreline S, first convert to a no-vig fair probability (divide 1 by the decimal equivalent after removing the bookmaker margin), then compare to the model's probability for that cell.

**All Markets** displays every market the engine has priced from the joint grid: 1X2, Both Teams to Score, Over/Under at every standard line from 0.5 through 6.5 goals, Draw No Bet (home/away), Double Chance (1X, X2, 12), Win to Nil (home/away), Asian Handicap -0.5 (home/away), and team-level totals. Every single number here is computed from the same underlying distribution -- there is no separate model feeding any of these markets.

The **Edge Report** is the most actionable panel on the page. For each market it shows the model probability, the market's no-vig implied probability (averaged across up to 6 bookmakers after SHIN normalization), the edge percentage, fair odds, and current market odds. Rows highlighted in gold have passed all three value filters. The Kelly Stake column reflects whatever bankroll and fraction you entered above the table.

**How to use this page:** Start with the KPI cards to calibrate your expectations for the day. Then scan the table for matches where the xG spread is large -- those are the matches where the model has a strong view. Expand any match that shows a non-zero Best Edge, read the full Edge Report, and verify the current odds at your preferred book before placing anything.

---

## Page 2 -- PMF Distributions

**URL:** sportsodds.wizardofodds.com/tools/odds-scanner/predictions/world-cup/pre-match/Probability%20Distributions.html

Where Page 1 compresses the model output into a single row per match, this page opens it up completely. Select a match using the navigation chips at the top and every chart updates immediately to show the full distribution of outcomes -- not just the most likely result, but the entire probability landscape.

A PMF is a Probability Mass Function: a list of all possible outcomes with a probability assigned to each one. For a football match, the PMF is a grid -- rows for home goals scored (0 through 15+), columns for away goals scored (0 through 15+), and a probability in every cell. Everything on this page is a visualization of that grid from a different angle.

### Chart 1 -- Joint Score PMF Heatmap

The heatmap is the model in its purest form. Every cell (h, a) shows the probability that the home team scores exactly h goals and the away team scores exactly a goals. Home goals increase along the vertical axis, away goals along the horizontal.

The color scale uses the square root of each cell's probability relative to the grid maximum. This is deliberate -- without the square root, cells with probabilities above 8% would appear bright and everything else would look uniformly dark, because the distribution is so heavily concentrated in the top-left corner (low-scoring outcomes). The square root transformation separates moderate-probability cells (3-5%) from near-zero ones, giving you a usable visual representation of the entire grid.

Every betting market you can think of is readable directly from this heatmap. Over 2.5 goals is the upper-right region -- all cells where h + a is at least 3. A home clean sheet is the entire first column (a = 0). Both teams to score is everything except that first column and first row. A correct score bet on 2-1 is a single cell. The model's view of a specific scoreline is whatever shade of green sits in that cell.

The tail mass shown below the heatmap is the probability assigned to scores beyond the grid (more than 15 goals per team). In practice this is a vanishingly small number, but it must exist to ensure the grid sums to exactly 100%.

### Chart 2 -- Marginal Goal Distributions

Two bar charts sit side by side. The left one shows the probability the home team scores exactly k goals (for k = 0, 1, 2, 3, and so on). The right shows the same for the away team. These marginal distributions are derived by collapsing the heatmap -- to get the probability the home team scores 2 goals, you add up the entire row h = 2 across all possible away goal values.

The shape of each chart tells you a lot quickly. A team with a tall bar at k = 0 is frequently shut out; the model sees a high probability it fails to score. A relatively flat distribution across k = 1 and k = 2 reflects a team with a strong attacking rate. In most World Cup group matches, the tallest bar sits at k = 1 for both teams -- scoring once is more likely than any other individual outcome.

### Chart 3 -- Total Goals Distribution

This chart shows the probability of each possible total goal count, from 0 up through 8 or more. It is computed by summing all cells along each anti-diagonal of the joint grid -- all cells where h + a = k contribute to the bar at total goals = k.

Standard over/under lines (0.5, 1.5, 2.5, 3.5, 4.5, 5.5) appear as vertical dividers. The probability to the right of any divider is the Over probability for that line; the probability to the left is the Under. This chart makes the model's view of the entire total-goals market immediately visible. If the bar at 2 goals is nearly as tall as the bar at 1 goal, and the bar at 3 is not far behind, you are looking at a genuinely uncertain total-goals outcome -- a match where the model does not have high conviction on any specific line.

### Chart 4 -- Goal Difference Distribution

Centered on zero, this bar chart shows the probability of each possible goal difference (home goals minus away goals). Gold bars indicate home wins (positive difference), gray indicates a draw (zero), blue indicates away wins (negative difference).

This is probably the most intuitive single chart on the page. A heavily gold-skewed distribution means the model sees the home team as a clear favorite; a roughly symmetric distribution means the match is genuinely even. The height of the gray bar relative to the gold and blue bars tells you how likely a draw is given the specific offensive and defensive qualities of these two teams. High-scoring expected matches (large lambda values) tend to have shorter gray bars because draws become less probable when both teams are expected to score frequently.

### Chart 5 -- Top 20 Most Likely Scorelines

A ranked bar chart of the 20 most probable individual final scores, with exact percentages and fair American odds displayed next to each bar.

As a general reference: the top cell in most group-stage matches carries somewhere between 12% and 20% probability. Any score showing above 6% is appearing in the very top tier of the distribution. The fair American odds shown here have no bookmaker margin -- they represent what a perfectly calibrated market would offer for that score. If your sportsbook is offering better odds than those shown, you may have found a value opportunity. If they are offering significantly worse, the book is priced tighter (or more accurately) than the model.

### O/U Lines Table

A simple table listing Over and Under probabilities for every standard total line from 0.5 through 6.5. This lets you compare across lines without doing any arithmetic from the chart -- the Over 1.5 probability, the Over 2.5, the Over 3.5, and so on, all in one place.

**How to use this page:** When you find a match on Page 1 that looks interesting, come here for the full picture. The heatmap tells you where the probability is concentrated. The goal difference chart tells you how the result probabilities break down. The top scorelines chart helps you evaluate correct-score prices at your book. If a scoreline your book is offering at +550 American shows a model probability of 12%, that is +550 against a fair price of around +733 -- a meaningful gap worth investigating.

---

## Page 3 -- Live In-Play PMF

**URL:** sportsodds.wizardofodds.com/tools/odds-scanner/predictions/world-cup/live/Probability%20Distributions.html

This page activates when a World Cup match is in progress. When no match is live, it shows the next scheduled kickoff time. All probabilities are regulation time only -- 90 minutes plus stoppage time. Extra time and penalty shootouts are not in scope.

### How the Live Model Differs

The pre-game model asks: what will the final score be? The live model asks something more specific: given that the current score is H-A at minute t, what will the final score be?

That distinction matters enormously. Once a match is in progress, some final scores have become impossible. If the match is 2-1 in the 70th minute, the final score cannot be 1-0, 0-0, or 2-0. Those cells of the joint grid are locked at zero probability. The remaining probability -- 100% minus whatever was locked -- redistributes entirely across the reachable scores.

This is conditional probability in action. It is what separates a proper live model from a pre-game model that simply gets updated every few minutes.

The live model also changes how it estimates remaining goal-scoring rates. Rather than assuming a constant rate across 90 minutes, it uses a non-homogeneous hazard model -- one where the goal-scoring rate varies by minute, calibrated from the minute-by-minute goal distribution across 128 World Cup matches from 2018 and 2022. Scoring rates are below average in the first ten minutes as teams settle in, rise through the mid-half, spike just after half-time kicks off, and peak in the final ten minutes when teams chasing a goal commit more forward. The model knows where in the match it is and applies the appropriate baseline rate.

On top of that temporal baseline, score-state multipliers adjust each team's rate based on the current scoreline. A home team losing by one goal at the 70th minute is likely to push forward, increasing both its own attack rate and the away team's counter-attacking opportunities. These multipliers are calibrated from World Cup data and the academic football forecasting literature:

- Draw at minute 60 or later: both teams' rates increase by 10% (matches tend to open up as the clock runs down)
- Home team losing by 1: home rate x1.25, away rate x1.05
- Home team losing by 2 or more: home rate x1.40, away rate x1.10
- Home team winning by 1: home rate x0.90, away rate x1.10
- Home team winning by 2 or more: home rate x0.80, away rate x1.15

When live expected goals data is available, the model blends it with the pre-game prior. This blend activates at minute 15 -- before that, live xG is too noisy to be useful from a small number of shots. From minute 15 onward, the live xG-derived rate gets 60% weight and the pre-game prior gets 40%. By the 70th minute, that blend means the live model is genuinely tracking the actual shot volumes and quality observed in the match, not just the pre-game forecast.

### Live KPI Cards

**Matches Live** is the count of World Cup matches currently in progress.

**Next Kickoff** shows the next scheduled match with its Eastern Time kickoff, useful when no match is currently live.

**Goals Today** is the total goals scored across all live and recently completed matches in the current matchday.

**Data Age** shows how long ago the last live snapshot was generated. Under 2 minutes is normal during a live match. Above 10 minutes triggers a health warning banner, which may indicate a pipeline or API issue.

### Connection Badge

A small indicator in the top-right corner shows how the page is receiving data.

**WebSocket (green)** means the browser has an active push connection to the live prediction server. When a goal or status change is reported, the server recomputes the full conditional PMF and pushes it to all connected browsers. The target latency from the data source to your browser is under 200 milliseconds. No manual refresh is needed.

**Polling (yellow)** means the push connection is unavailable and the page is falling back to fetching a static JSON file every 60 seconds. Updates arrive with up to a one-minute delay. This is the automatic fallback mode and requires no user action.

### Win Probability Bar

The same three-segment bar as on Page 1 -- Home Win (gold), Draw (gray), Away Win (blue) -- but now conditional on the current score and minute. Watch this bar during a live match and you see the model's view of the contest shifting in real time. A home goal pushes the gold segment rightward immediately. A late away equalizer can collapse the home win probability from 80% to 30% in a single update.

These are conditional probabilities. They represent the probability of each regulation-time outcome given that the match is currently at score H-A at minute t. They are not the probabilities from kickoff -- those are shown in the table directly below.

### Pre-Game to Live Shift Table

This table is one of the most informative features on the live page. For each main market it shows three values side by side: the probability from before kickoff, the current live probability, and the arithmetic difference between them.

A large positive shift on Home Win combined with a large negative shift on Draw and Away Win tells you the home team has taken control of a match that was expected to be closer. A large negative shift on BTTS tells you one team has been completely shut out so far, reducing the probability that they score at all. Reading the shift table alongside the current score gives you a clear picture of how the match is deviating from the pre-game expectation.

### Win Probability Sparkline

A compact line chart showing the home team's win probability from kickoff to the current minute. This history accumulates within your browser session and resets on page reload -- it is not stored on the server. Sharp upward jumps are home goals; sharp downward drops are away goals. The sparkline makes visible what the current snapshot cannot: whether the home team earned their probability gradually or in a single dramatic moment, how volatile the match has been, and whether the current probability reflects a stable lead or a precarious one.

### Live Joint Score PMF Heatmap

The same heatmap structure as on Page 2, but updated with every live snapshot and annotated with two visual cues.

The cell corresponding to the current live score is outlined in red. All unreachable cells -- any score where home goals are below the current home tally or away goals are below the current away tally -- are forced to zero and appear dark. As the match progresses, the dark region of the grid grows and the probability concentrates into fewer and fewer bright cells.

In stoppage time of a 1-0 match, the heatmap may assign 85-90% probability to the single 1-0 cell. The rest is split between 1-1 (away team equalizes), 2-0 (home team extends the lead), and a handful of other reachable scores. That visual concentration of color into one or two cells in the final minutes is a clear picture of what is at stake.

### Next Goal Probabilities

Three numbers sit below the heatmap, derived from the remaining expected goals for each team.

**Home scores next** is lambda_home_remaining / (lambda_home_remaining + lambda_away_remaining) -- given that at least one more goal is scored, what is the probability it belongs to the home team?

**Away scores next** is the corresponding fraction for the away team.

**No more goals** is the joint probability that both teams produce zero additional goals -- the match ends exactly at the current score. Mathematically, it is the Poisson probability of zero events from two independent processes: e^(-lambda_home_remaining) times e^(-lambda_away_remaining). As the match enters stoppage time with small remaining expected goals, this value typically climbs above 80% or 90%.

### Top 10 Most Likely Final Scores (Live)

The same ranked scoreline list as on Page 2, restricted to reachable outcomes only. The current live score is marked. As the match approaches the final whistle, the probability on the leading score climbs rapidly -- in an 88th-minute 1-0 match, the 1-0 cell may carry 8 or 9 times the probability it held before kickoff. This list tells you not just what is most likely but how much more likely it is than the alternatives.

### Marginal Charts

Bar charts for each team showing the probability they score exactly k regulation-time goals, derived from the live PMF. Because goals already scored are facts rather than random events, values below each team's current goal count are zero. A team that has already scored twice sees bars only at k = 2, 3, 4, and so on.

**How to use this page:** The live page is most useful in two situations. First, during fast-moving matches where the pre-game expectation is being rapidly revised -- a live scoreline of 2-0 in the 30th minute will have completely reshaped the probability distribution relative to what Page 1 showed before kickoff. Second, when evaluating live betting markets: compare the No More Goals probability against your book's live Under line, or compare the Next Goal fractions against live next-scorer pricing. The model's conditional probabilities are updating every 90 seconds, giving you a continuously refreshed view of the match as it actually unfolds.

---

## Scope and Limitations

All probabilities across all three pages represent regulation time -- 90 minutes plus stoppage time. Extra time and penalty shootouts are not modeled.

The model's structural assumption of independence between home and away goals is an approximation. In reality, a goal changes the incentives for both teams and triggers tactical adjustments. Market reconciliation partially corrects for this, but the independence assumption remains at the core of the parametric structure.

Calibration rests on 128 World Cup matches from 2018 and 2022, augmented by completed 2026 matches as the tournament progresses. As more 2026 data accumulates, the model adapts its parameters to the specific conditions of this tournament.

Edge estimates are outputs of a probabilistic model. Market odds move between the time predictions are generated and kickoff. Verify current prices at your book before acting on any signal shown here.

*All probabilities represent regulation time (90 minutes plus stoppage time) only. Extra time and penalties are excluded. This guide is for informational and educational purposes. Please gamble responsibly.*
