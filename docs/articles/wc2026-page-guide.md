---
title: "A Guide to the World Cup 2026 Prediction Pages"
subtitle: "What every number, chart, and indicator means — and why it matters"
author: "WizardOfOdds.com"
date: "June 2026"
---

# A Guide to the World Cup 2026 Prediction Pages

Most football prediction tools give you a win probability and call it a day. This one gives you the entire joint probability distribution over every possible scoreline — the probability that the match ends 0-0, that it ends 2-1, that it ends 4-3 — and derives every betting market mechanically from that single distribution.

That architecture is not a cosmetic difference. It means every number on every page is internally consistent by construction. When you see an edge on this site, you are looking at a discrepancy between a coherent probability system and the bookmaker's price — not an artifact of mismatched models.

Five pages build on this foundation. Each draws from the same 12-signal composite rating system and joint score PMF engine.

---

## The Foundation: One PMF, All Markets

Every page draws from the same underlying joint score probability grid. Each cell (h, a) holds P(Home = h, Away = a) — the probability the home team scores exactly h goals and the away team scores exactly a goals in regulation time. The grid sums to exactly 1.0, enforced at every pipeline stage.

Every betting market is a different arithmetic operation on this one grid:

- **Over 2.5:** Sum all cells where h + a >= 3
- **BTTS:** Sum all cells except first row and first column
- **Home Win:** Sum all cells where h > a
- **Correct score 2-1:** The single cell at (h=2, a=1)

This is not a collection of separate models. It is one model, and all markets flow from it.

---

## Page 1 — Pre-Match Predictions

**URL:** pre-match.html

This is the command center. Every World Cup match scheduled for today appears in the main table with the model's probability estimates, expected goals, and edge analysis against live bookmaker prices. Data refreshes automatically. A red banner appears if the underlying prediction file is more than four hours old — a signal the automated pipeline may have encountered an issue.

### The KPI Cards

Four summary numbers compress the entire day's modeling output into a single glance.

**Matches Today:** The number of regulation kickoffs scheduled for today's date in Eastern Time.

**Value Bets:** The count of individual betting markets across today's matches that pass all three edge filters simultaneously: raw edge >= 4%, 90% CI lower bound still exceeds the no-vig market price, and market-implied probability > 2%. This is a strict filter. The count is frequently zero or a very small number — that is correct behavior. A well-calibrated model should not be finding edge everywhere, because the market for World Cup games is well-supplied with sharp money.

**Best Edge:** The single largest edge percentage found across all today's markets, with the specific match and market identified. An edge of +12% means the model estimates that outcome is 12% more likely than the bookmaker's no-vig price implies. Odds move between prediction time and kickoff — always confirm the current number before acting.

**Avg xG / Match:** The average total expected goals (lambda_home + lambda_away) across today's fixtures, after market reconciliation.

### The Bankroll Sizing Tool

Enter a bankroll amount and select a Kelly fraction. For every market passing all three edge filters, the tool computes a recommended dollar stake.

**Full Kelly** is theoretically optimal when edge estimates are perfectly accurate — which they never are. Use it only when you have high confidence in the specific edge signal.

**Half Kelly** (default) divides the computed stake by two. This is the standard recommendation in the sports modeling literature when working with a model that has non-negligible parameter uncertainty.

**Quarter Kelly** is appropriate when you are early in the tournament with limited completed-match calibration data, or when spreading capital across several simultaneous positions.

All three fractions are hard-capped at 5% of your entered bankroll regardless of what the formula computes.

### The Match Table

Each row is one match. Working left to right:

**Match:** Home team vs. away team. Most WC2026 matches are far from any team's natural home base. All fixtures are treated as neutral venue by default. The three host nations — USA, Canada, Mexico — each receive a co-host adjustment of +0.10 attack lambda and -0.10 defense lambda.

**1X2 Probability Bars:** Three colored segments proportional to regulation-time probabilities: Home Win (gold), Draw (gray), Away Win (blue). These come directly from summing the joint PMF grid.

**O/U 2.5:** The probability the match produces 3 or more total goals — the sum of all grid cells where h + a >= 3. Above 55% means the model leans toward higher scoring. Below 45% suggests a tight match.

**BTTS:** Both Teams to Score — the probability each team scores at least once. A BTTS probability of 35% means there is a meaningful chance one team gets shut out.

**Top Score:** The single most probable final scoreline and its probability — the peak cell of the joint PMF grid. For most group-stage matches this is 1-0 or 1-1, typically carrying 12–18% probability.

**xG (H-A):** The model's expected goals for each team separately — lambda_home and lambda_away after market reconciliation and all per-match calibration adjustments.

**Best Edge / Fair Odds:** The highest-edge market for this specific match passing all three filters. If no market passes, the cell is empty.

### The Expanded Row

Click any match row to reveal three additional panels.

**Full Scoreline Distribution:** All non-trivial scorelines ranked from most to least likely, with proportion bars. These are raw joint PMF values.

**All Markets:** Every market the engine has priced from the joint grid — 1X2, BTTS, Over/Under at every standard line from 0.5 through 6.5 goals, Draw No Bet, Double Chance, Win to Nil, Asian Handicap, and team-level totals.

**Edge Report:** For each market: model probability, market no-vig implied probability (averaged across up to 6 bookmakers after SHIN normalization), edge percentage, fair odds, and current market odds. Rows highlighted in gold have passed all three value filters.

---

## Page 2 — PMF Distributions

**URL:** pmf-distributions.html

Where Page 1 compresses model output into a single row per match, this page opens it completely. Select a match using the navigation chips at the top and every chart updates immediately to show the full probability landscape.

### Chart 1 — Joint Score PMF Heatmap

The heatmap is the model in its purest form. Every cell (h, a) shows the probability the home team scores exactly h goals and the away team scores exactly a goals. Home goals on the vertical axis, away goals on the horizontal.

The color scale uses the **square root** of each cell's probability relative to the grid maximum. This is deliberate: without the square root transformation, cells with probabilities above 8% would appear bright and everything else would look uniformly dark. The square root separates moderate-probability cells from near-zero ones.

Every betting market is readable directly from this heatmap. Over 2.5 is the upper-right region where h + a >= 3. A home clean sheet is the entire first column (a = 0). BTTS is everything except that first column and first row.

### Chart 2 — Marginal Goal Distributions

Two bar charts side by side. The left shows the probability the home team scores exactly k goals. The right shows the same for the away team. These marginals are computed by collapsing the heatmap along each axis:

    P(Home = h) = SUM over all a of P(Home = h, Away = a)

### Chart 3 — Total Goals Distribution

The probability of each possible total goal count, computed by summing all cells along each anti-diagonal (all cells where h + a = k contribute to the bar at k total goals).

Standard over/under lines (0.5, 1.5, 2.5, 3.5, 4.5, 5.5) appear as vertical dividers. The probability to the right of any divider is the Over probability for that line.

### Chart 4 — Goal Difference Distribution

Centered on zero, this bar chart shows the probability of each possible goal difference (home goals minus away goals). Gold bars indicate home wins, gray indicates draws, blue indicates away wins.

### Chart 5 — Top 20 Most Likely Scorelines

A ranked bar chart of the 20 most probable individual final scores with exact percentages and fair American odds. The top cell in most group-stage matches carries 12–20% probability.

### Model vs Market Comparison Panel

A side-by-side table comparing model probabilities to BDL market no-vig prices for all standard markets: 1X2, BTTS, O/U lines from 0.5 through 6.5. Each row shows model probability, market-implied probability, edge, and fair odds. This is the same data surfaced in more detail on the Market X-Ray page.

### O/U Lines Table

A simple table listing Over and Under probabilities for every standard total line from 0.5 through 6.5. All computed directly from the joint PMF.

---

## Page 3 — Live In-Play PMF

**URL:** live-pmf.html

This page activates when a World Cup match is in progress. When no match is live, it shows the next scheduled kickoff. All probabilities are regulation time only — 90 minutes plus stoppage time. Data updates approximately every 5 minutes during live matches.

### How the Live Model Differs from Pre-Game

The pre-game model asks: what will the final score be from kickoff? The live model asks something more specific: **given that the current score is H-A at minute t, what will the final score be?**

Once a match is in progress, some final scores have become impossible. Those grid cells are locked at zero probability. The remaining probability redistributes entirely across the reachable scores — this is conditional probability.

The live model uses a **non-homogeneous hazard model** — goal rates vary by match minute, calibrated from 2018 and 2022 World Cup data. Rates are below average early, rise through the mid-half, spike just after half-time, and peak in the final minutes.

On top of the temporal baseline, multiple live enhancements are active:

- **Score-state multipliers** adjust each team's rate based on the current scoreline
- **xG blend:** live xG rate (60%) blended with pre-game prior (40%) from minute 15 onward
- **Momentum scaling:** `passes_final_third` wired into the hazard at ±3% attack
- **momentum_df:** BDL match momentum API at ±8%/5% hazard scaling (home/away)

### Score-State Multipliers

| Score State | Home Rate | Away Rate |
|---|---|---|
| Draw at minute 60 or later | ×1.10 | ×1.10 |
| Home team losing by 1 | ×1.25 | ×1.05 |
| Home team losing by 2 or more | ×1.40 | ×1.10 |
| Home team winning by 1 | ×0.90 | ×1.10 |
| Home team winning by 2 or more | ×0.80 | ×1.15 |

### Connection Badge

**WebSocket (green):** The browser has an active push connection. When a goal or status change is reported, the server recomputes the full conditional PMF and pushes it to all connected browsers — typically within 200 milliseconds.

**Polling (yellow):** Push connection unavailable. The page fetches updated data from a static JSON file every 60 seconds. This is the automatic fallback mode.

### Live KPI Cards

**Matches Live:** Number of World Cup matches currently in progress.

**Next Kickoff:** Next scheduled match with its Eastern Time kickoff.

**Goals Today:** Total goals scored across all live and recently completed matches in the current matchday.

**Data Age:** Time elapsed since the last live snapshot. Under 2 minutes is normal. Above 10 minutes triggers a health warning banner.

### Win Probability Bar and Shift Table

The same three-segment bar as on Page 1 — Home Win (gold), Draw (gray), Away Win (blue) — but now conditional on the current score and minute. Directly below the bar, the Pre-Game to Live Shift table shows, for each main market, the pre-game probability, current live probability, and arithmetic difference.

### Win Probability Sparkline

A compact line chart showing the home team's win probability from kickoff to the current minute. Sharp upward jumps correspond to home goals; sharp downward drops correspond to away goals. This history accumulates in your browser session and resets on page reload.

### Live Joint Score PMF Heatmap

The same heatmap structure as on Page 2, updated with every live snapshot. The cell corresponding to the current live score is **outlined in red**. All unreachable cells are forced to zero and appear dark. As the match progresses, the dark region grows and probability concentrates into fewer and fewer bright cells.

In stoppage time of a 1-0 match, the heatmap may assign 85–90% probability to the single 1-0 cell.

### Next Goal Probabilities

Three values derived from the remaining expected goals lambda_h_rem and lambda_a_rem:

    Home scores next:  lambda_h_rem / (lambda_h_rem + lambda_a_rem)
    Away scores next:  lambda_a_rem / (lambda_h_rem + lambda_a_rem)
    No more goals:     e^(-lambda_h_rem) × e^(-lambda_a_rem)

As the match enters stoppage time with small remaining expected goals, the "No more goals" value typically climbs above 80–90%.

### Top 10 Most Likely Final Scores (Live)

The same ranked list as on Page 2, restricted to reachable outcomes only. The current live score is marked. As the match approaches the final whistle, the probability on the leading score climbs rapidly — in an 88th-minute 1-0 match, the 1-0 cell may carry 8 or 9 times the probability it held before kickoff.

---

## Page 4 — Live Pitch

**URL:** live-pitch.html

The Live Pitch page provides a real-time animated shot map for any match currently in progress, rendered using BallDontLie player coordinate data. It is the most visually intensive page in the suite and is designed for in-play monitoring.

### Animated Shot Map

Each shot attempt in the live match is plotted on a scaled pitch diagram using the `player_x` and `player_y` coordinates from the BallDontLie live player data feed. Shot markers are color-coded by outcome:

- **Gold filled circle:** goal scored
- **White open circle:** shot on target, saved
- **Gray X:** shot off target or blocked

Markers animate onto the pitch at the minute they occurred. Older shots fade slightly to help distinguish recent activity from early match shots.

### Momentum KPIs

Below the pitch, a row of key performance indicators derived from the live stats feed shows each team's current in-match momentum. These same KPIs feed directly into the live hazard model:

**Passes Final Third:** Passes into the final third, updated each snapshot. The ratio between teams wires into the ±3% attack hazard adjustment.

**Match Momentum:** The BDL match momentum score for each team, displayed as a bar. When one team's momentum score exceeds the threshold, the +8% (home) or +5% (away) hazard scaling activates.

**Live xG:** Running xG for each team accumulated during the match, blended at 60% into the live hazard from minute 15 onward.

**Shots:** Total shots attempted by each team in the match.

**Shots on Target:** Shots on target for each team — the most predictive single stat for in-play goal likelihood.

### Data Freshness

The Live Pitch updates on the same 2-minute snapshot cycle as the Live PMF page. Because BDL player coordinate data has slightly higher latency than score/clock data, the shot map may lag the Live PMF page by one snapshot cycle during fast-moving moments.

---

## Page 5 — Market X-Ray

**URL:** market-xray/index.html

The Market X-Ray is a trader-grade analysis tool providing the deepest level of model-vs-market comparison available on the site. It is designed for users who want to go beyond edge percentages and understand the full picture of value, confidence, and market movement for every active match.

### Fair Odds vs Market Comparison

For each match and each market, the X-Ray shows the model's fair (no-vig) odds alongside the current market odds from all available BDL bookmakers. The comparison is presented as both American odds and implied probability, making it easy to identify where the model and market diverge significantly.

### Edge, EV, and Confidence Grades

**Edge:** The percentage by which the model's probability exceeds the market's no-vig probability. Identical formula to the edge on Page 1.

**EV:** Expected Value — the dollar return per $100 wagered assuming the model's probability is the true probability.

    EV = (model_prob × net_payout) - (1 - model_prob) × 100

**Confidence Grade:** A letter grade (A through F) reflecting the combined strength of the edge, CI lower bound check, and number of bookmakers confirming the price. An A grade means the edge is large, robust to lambda uncertainty, and confirmed across multiple books.

### Trader Action Notes

Each market receives one of six action labels:

| Action | Meaning |
|---|---|
| **BET** | Edge >= 8%, Confidence A or B, CI lower bound clears market. Full signal — act at current price. |
| **SMALL BET** | Edge 4-8%, Confidence B or C. Positive signal but uncertainty warrants reduced size. |
| **LEAN** | Edge 2-4%, not quite threshold. Monitor — may develop into a BET as odds move. |
| **WAIT** | Edge present but line moving unfavorably. Do not act until line stabilizes. |
| **PASS** | Edge below threshold or CI check fails. No actionable value at current price. |
| **DO NOT CHASE** | Line has already moved significantly toward model fair value. CLV has been consumed. |

### Line Movement Tracking

The X-Ray records the opening line, current line, and direction and magnitude of movement for each market. A sparkline shows the price history from the model's first prediction through the current moment. Markets moving toward the model's fair value confirm the signal; markets moving away suggest new information the model has not yet incorporated.

### CLV Tracker

For matches that have already kicked off, the CLV Tracker shows the model's opening prediction probability versus the closing no-vig probability for all 15 tracked markets. Positive CLV (model was ahead of where the market closed) is highlighted in gold. Negative CLV is shown in muted gray. The aggregate CLV across all markets and all completed matches is displayed as the primary performance metric at the top of the tracker panel.

**How to use the Market X-Ray:** Start with the Trader Action Notes. BET and SMALL BET are the only actionable signals. LEAN is worth monitoring. WAIT means check back after the next pipeline run. PASS and DO NOT CHASE mean no action at this price. The CLV Tracker accumulates over the tournament and is the fairest measure of whether the model's edges have been genuine.

---

## Scope and Limitations — All Pages

**Regulation time only.** All probabilities on all five pages represent 90 minutes plus stoppage time. Extra time and penalty shootouts are not included.

**lambda_3 = 0.170 substantially reduces but does not eliminate the independence approximation.** The Bivariate Poisson captures positive correlation between home and away goals, but it represents an average across match types. Live score-state multipliers handle tactical dynamics in real time.

**Adaptive calibration.** Temperature weighting shifts from 30/70 to 60/40 (WC2026/historical) once 24 or more WC2026 matches complete. All parameters stabilize as the tournament progresses.

**Live pipeline latency.** The stated target of under 200 milliseconds for WebSocket updates applies under normal conditions. Network latency and server load can affect real-time delivery.

**Edge estimates are outputs of a probabilistic model.** Market odds move between the time predictions are generated and kickoff. Verify current prices at your book before acting on any signal shown here.

**Live Pitch coordinate data** (player_x/player_y) may lag the Live PMF score data by one snapshot cycle during fast-moving moments.

---

*All probabilities represent regulation time (90 minutes plus stoppage time) only. Extra time and penalties are excluded. This guide is for informational and educational purposes. Please gamble responsibly.*
