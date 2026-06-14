WIZARDOFODDS.COM
A Guide to the WC 2026 Prediction Pages
What every number, chart, and indicator means — across all three pages.

---

There are three pages in the WC 2026 prediction section. Each draws from the same underlying joint score probability engine. This guide explains every element visible on each page, in the order it appears.

---

PAGE 1 — PRE-GAME PREDICTIONS
URL: sportsodds.wizardofodds.com/tools/odds-scanner/predictions/world cup/pre match.html

This page lists every World Cup match scheduled for the current day, with the model's pre-game probability estimates and edge analysis. Data loads automatically and refreshes every five minutes from the latest prediction JSON. A red banner appears if the underlying data is more than four hours old, indicating a potential pipeline issue.

KPI CARDS

Matches Today: The number of World Cup matches with regulation kickoffs scheduled for today's date in Eastern Time.

Value Bets: The count of individual betting markets — across all of today's matches — where the model's edge is at least 4% and the 90% confidence interval lower bound still exceeds the market's no-vig probability. Both conditions must hold simultaneously. This is a strict filter; the number is frequently zero or very small, which is the correct behavior of a well-calibrated model, not a malfunction.

Best Edge: The single largest edge found across all of today's markets, expressed as a percentage. The sub-label identifies the specific market and match. A positive edge means the model assigns meaningfully higher probability to that outcome than the market does after removing the bookmaker's margin. This does not guarantee a profitable bet — market odds move between prediction generation and kickoff, and edge estimates carry model uncertainty.

Avg xG / Match: The average of (λ_home + λ_away) across today's matches — the model's expected total goals per match. These expected-goals figures come from the composite team rating system after market reconciliation and reflect the best available blend of statistical ratings, FIFA rankings, qualifying records, and current bookmaker pricing.

BANKROLL SIZING TOOL

Enter a bankroll amount and select a Kelly fraction. The table will display a recommended dollar stake for every market that passes all three value filters. Three fractions are available:

Full Kelly: The theoretically optimal fraction under the Kelly criterion when edge estimates are perfect. In practice, edge estimates are never perfect — the model carries a fixed ±12% uncertainty on its lambda parameters — so Full Kelly tends to overbet and produces large swings. Use it only if your confidence in the edge signal is unusually high.

Half Kelly: Bet size divided by two. This is the engine's default and the standard recommendation in the sports modeling literature when model uncertainty is non-negligible. It retains most of the theoretical edge while substantially reducing drawdown risk.

Quarter Kelly: A conservative setting appropriate when acknowledging significant uncertainty in the model's probability estimates, or when sizing across a large number of simultaneous positions.

All computed Kelly stakes are hard-capped at 5% of the entered bankroll regardless of the computed fraction.

THE MATCH TABLE

Each row represents one match. Columns from left to right:

Match: Home team versus away team. Every World Cup 2026 match is treated as a neutral venue — the tournament is hosted jointly by the United States, Canada, and Mexico, and nearly all matches are played far from any team's home crowd. The three host nations (USA, Canada, Mexico) receive a co-host adjustment of +0.10 to attack lambda and −0.10 to defense lambda, reflecting a small but measurable advantage in familiarity, travel distance, and fan support. All other teams play as if on a fully neutral pitch.

1X2 Probability Bars: Three colored segments proportional to the regulation-time probabilities — Home Win (gold), Draw (gray), Away Win (blue). These are derived by summing the appropriate cells of the joint score probability grid: home win is the sum of all cells where home goals exceed away goals; draw is the main diagonal (0–0, 1–1, 2–2, etc.); away win is the sum of all cells where away goals exceed home goals. The three values sum to exactly 100%. Odds are displayed in American format next to each bar.

O/U 2.5: The probability that total regulation-time goals exceed 2.5 — that is, three or more goals are scored. Computed by summing all PMF cells where home goals + away goals ≥ 3.

BTTS: Both Teams to Score — the probability that both teams score at least one regulation-time goal. Computed by summing all cells in the joint PMF where home goals ≥ 1 and away goals ≥ 1.

Top Score: The single most probable final scoreline and its probability, read directly from the peak cell of the joint PMF grid. For most matches, this is 1–0 or 1–1. The model computes the full distribution across scores up to 15 goals per team; this column shows only the mode.

xG (H–A): The model's expected goals for home and away separately — the Poisson rate parameters λ_home and λ_away after market reconciliation. These are the numbers that feed the joint PMF. A match with xG of 2.1–0.6 is a heavy favorite-versus-underdog contest; a match with xG of 1.2–1.1 is nearly even.

Best Edge / Fair Odds: The highest-edge market for this specific match that passes all three value filters (≥4% edge, CI check, ≥2% market-implied probability). Fair odds represent what the model believes the true no-margin price should be. If no market passes all filters for this match, the cell is blank. Fair odds are displayed in American format.

EXPANDED ROW

Clicking any row reveals three additional sections:

Full Scoreline Distribution: All scored final-score probabilities from 0–0 through the grid maximum, ranked from most to least likely. The top 20 are displayed with proportion bars. These values are the raw joint PMF grid values — no transformation is applied. For correct-score betting: if a book is offering decimal odds D on scoreline S, the edge is (model_prob − 1/D_no_vig) / (1/D_no_vig), where D_no_vig adjusts for the bookmaker's margin.

All Markets: Every market the engine has priced from the joint PMF. This includes 1X2, Both Teams to Score (Yes/No), Over/Under at every standard line from 0.5 through 6.5 goals, Draw No Bet (Home/Away), Double Chance (1X, X2, 12), Win to Nil (Home/Away), Asian Handicap −0.5 (Home/Away), and team-level totals (Home Over/Under 0.5 and 1.5, Away Over/Under 0.5 and 1.5). Every number on this panel is computed from the same underlying joint PMF — there is no separate model per market type.

Edge Report: For each market: Model Probability, Market Implied probability (no-vig, averaged across available bookmakers via SHIN normalization), Edge %, Fair Odds, and Market Odds. Rows highlighted in gold have passed all three value filters. The Kelly Stake column reflects the bankroll and fraction you selected above the table.

---

PAGE 2 — PMF DISTRIBUTIONS
URL: sportsodds.wizardofodds.com/tools/odds-scanner/predictions/world-cup/pre-match/Probability Distributions.html

This page visualizes the complete probability distribution for every match. Select a match using the navigation chips at the top. All charts update immediately on selection and draw from the same joint PMF as Page 1. The fair odds displayed alongside each chart element are in American format.

CHART 1 — JOINT SCORE PMF HEATMAP

A color-coded grid where each cell (h, a) shows P(Home goals = h, Away goals = a). Home goals increase down the vertical axis; away goals increase across the horizontal axis.

Color scale: dark blue/black represents near-zero probability; warm orange/yellow marks moderate probability (roughly 3–8%); bright green identifies the highest-probability cells, typically above 8%. The mapping uses the square root of each cell's probability relative to the grid maximum, which opens up visual separation between low- and moderate-probability cells that would otherwise appear uniformly dark on a linear scale.

Every standard betting market can be read directly from this grid. Over 2.5 goals is the sum of all cells where h + a ≥ 3 (the upper-right region). A home clean sheet is the entire first column (a = 0). Both Teams to Score is all cells except the first row and first column. A specific correct score such as 2–1 is a single cell.

The tail mass shown below the heatmap is the probability mass assigned to scores beyond the grid boundary (more than 15 goals per team, a vanishingly small number). The explicit grid values plus this tail mass sum to exactly 100%.

CHART 2 — MARGINAL GOAL DISTRIBUTIONS

Two bar charts — one for home, one for away. Each bar shows P(team scores exactly k goals in regulation) for k = 0, 1, 2, 3, ... The home marginal is obtained by summing the joint PMF down each column: P(Home = h) = Σ_a P(Home = h, Away = a). A tall P(0) bar means the model expects the team to be frequently shut out. For most World Cup group matches, the tallest bar is at 1 goal.

CHART 3 — TOTAL GOALS DISTRIBUTION

A bar chart showing P(total regulation goals = k) for k = 0, 1, 2, 3, ... Computed by summing all joint PMF cells along each anti-diagonal where h + a = k. Standard over/under lines (0.5, 1.5, 2.5, 3.5, 4.5, 5.5) appear as vertical dividers. The probability to the right of any divider is the Over probability for that line; to the left is Under. This chart makes it easy to verify that the PMF-derived over/under probabilities are internally consistent.

CHART 4 — GOAL DIFFERENCE DISTRIBUTION

A bar chart centered on zero showing the probability of each possible goal difference (home goals minus away goals). Gold bars indicate home wins (positive difference), gray indicates a draw (zero difference), blue indicates away wins (negative difference). A symmetric distribution signals an even match; a heavily skewed distribution reflects a large favorite. This chart is the clearest visual representation of the match result probability — it aggregates all scorelines that produce each outcome into a single view.

CHART 5 — TOP 20 MOST LIKELY SCORELINES

A ranked bar chart of the 20 highest-probability individual final scores with exact percentages shown next to each bar. The fair American odds for each scoreline are also displayed, derived from the model probability alone (no margin). These are the raw joint PMF values for the top 20 cells sorted in descending order. As a general reference: any score with model probability above ~6% is appearing in the top two or three cells of the distribution.

O/U LINES TABLE

A table listing the Over and Under probability for every standard total line from 0.5 through 6.5, derived by summing the appropriate region of the joint PMF. This provides a complete view of the model's total-goals distribution across all commonly traded lines without requiring the reader to compute each sum from the heatmap manually.

---

PAGE 3 — LIVE IN-PLAY PMF
URL: sportsodds.wizardofodds.com/tools/odds-scanner/predictions/world-cup/live/Probability Distributions.html

This page activates when a World Cup match is in progress. When no matches are live, it displays the next scheduled kickoff time. All probabilities are regulation-time only — 90 minutes plus stoppage time. Extra time and penalty shootouts are not modeled.

HOW THE LIVE MODEL DIFFERS FROM THE PRE-GAME MODEL

The pre-game model asks: what will the final score be from kickoff? The live model asks: given that the current score is H–A at minute t, what will the final score be at the final whistle?

This is a conditional probability calculation. Once a match is in progress, every final score that is now unreachable from the current state carries zero probability. A match sitting at 2–1 in the 70th minute cannot end 1–0 or 0–0; those cells of the PMF grid are permanently zero, and all remaining probability redistributes across the reachable scores.

The live model computes expected remaining goals for each team using a non-homogeneous hazard model — meaning the goal-scoring rate varies across the 90 minutes rather than being fixed. The temporal baseline is calibrated from the minute-by-minute goal distribution across the 2018 and 2022 World Cups:

 • Minutes 1–10: below-average scoring rate (teams settling into the match)
 • Minutes 25–45: rising rate as play opens up and both teams take more risks
 • Minutes 45–50: elevated rate immediately following the second-half kickoff
 • Minutes 80–90+: above-average rate, especially when a team is chasing an equalizer or a winner

On top of the temporal baseline, score-state multipliers scale each team's rate depending on the current scoreline. These are calibrated from World Cup data and the football forecasting literature (Dixon & Robinson 1998):

 Score state                      Effect on goal rates
 Draw at minute 60+               Both teams ×1.10 (matches open up as the clock runs down)
 Home team losing by 1            Home ×1.25, Away ×1.05 (counter-attack risk increases for away team)
 Home team losing by 2+           Home ×1.40, Away ×1.10
 Home team winning by 1           Home ×0.90, Away ×1.10 (away team pushes forward)
 Home team winning by 2+          Home ×0.80, Away ×1.15

When live expected goals (xG) data is available from BallDontLie, the model blends the live xG-derived rate with the pre-game expected rate. This blending activates starting at the 15th minute — early in a match, live xG is too noisy from small samples to be reliable. After minute 15, the blend applies 60% weight to the live xG-derived intensity and 40% to the pre-game prior. By the 70th minute, this makes the live model meaningfully responsive to shot volume and quality actually observed in the match.

LIVE KPI CARDS

Matches Live: The number of World Cup matches currently in progress according to BallDontLie.

Next Kickoff: The next World Cup match starting today, with kickoff time in Eastern Time.

Goals Today: Total goals scored across all live and recently completed matches in the current matchday snapshot.

Data Age: Time elapsed since the last live snapshot was generated. Under two minutes is normal during live matches. A value above ten minutes during a match triggers a health warning banner on the page.

CONNECTION BADGE

A small indicator shows how the page is receiving data:

WebSocket (green): The browser has an active push connection to the live prediction server. When BallDontLie reports a goal or a status change, the server recomputes the full conditional PMF and pushes the update to all connected browsers. The target latency from BallDontLie event to browser update is under 200 milliseconds. No manual refresh is needed.

Polling (yellow): The real-time push connection is unavailable. The page falls back to fetching a static JSON file every 60 seconds. Updates arrive with up to a one-minute delay. This is the automatic fallback mode and requires no action from the user.

WIN PROBABILITY BAR

The same three-segment bar as on Page 1 — Home Win (gold), Draw (gray), Away Win (blue) — but now conditional on the current live score and minute. As goals are scored, the bar shifts immediately. A goal for the home team pushes the gold segment rightward; a goal for the away team does the opposite. These probabilities represent the probability of each regulation-time outcome given that the match is at score H–A at minute t, not the probability from kickoff.

PRE-GAME TO LIVE SHIFT TABLE

Directly below the win probability bar, a table shows each main market with three values side by side: the probability the model assigned before kickoff, the current live probability, and the arithmetic difference between them. A large shift indicates that the match state has substantially moved the probability distribution away from the pre-game expectation. A home team leading 2–0 in the 70th minute will show a very large positive shift on Home Win; BTTS will show a large negative shift if the away team has not scored.

WIN PROBABILITY SPARKLINE

A small line chart showing the history of the home team's win probability from kickoff to the current minute. This history accumulates within the browser session and resets on page reload — it is not transmitted from the server. Sharp upward jumps correspond to home goals; sharp downward drops correspond to away goals. The sparkline makes visible patterns that are invisible from the current snapshot alone: whether a team's lead was earned early or late, how stable the probability has been, and whether the current state reflects a genuine change in match dynamics.

LIVE JOINT SCORE PMF HEATMAP

The same heatmap structure as on Page 2, updated with every snapshot. Two key visual differences from the pre-game version:

 • The cell corresponding to the current live score is outlined in red.
 • All cells representing scores that are now unreachable (home goals below current home score, or away goals below current away score) are forced to zero probability and appear dark. The remaining probability mass is distributed only over reachable final scores, ensuring the heatmap still sums to 100%.

As the match progresses toward the final whistle, the reachable region of the grid shrinks, concentrating probability into fewer and fewer cells. In stoppage time of a 1–0 match, the PMF may assign 85–90% probability to the 1–0 cell alone.

NEXT GOAL PROBABILITIES

Three values computed from the remaining expected goals for each team:

Home scores next: λ_h_rem / (λ_h_rem + λ_a_rem). Given that at least one more goal is scored before the final whistle, the probability it belongs to the home team.

Away scores next: λ_a_rem / (λ_h_rem + λ_a_rem). The corresponding probability for the away team.

No more goals: e^(−λ_h_rem) × e^(−λ_a_rem). The joint probability that both teams produce zero additional goals — that is, the current scoreline is the final result. This is the Poisson probability of zero events from both independent processes.

TOP 10 MOST LIKELY FINAL SCORES (LIVE)

The same ranked list as on Page 2, but restricted to reachable final scores only. The current live score is marked with an arrow. As the match approaches the final whistle, the most likely score's probability typically rises sharply because fewer reachable outcomes remain. In a 1–0 match at the 88th minute, the probability assigned to the 1–0 cell may be eight or nine times higher than it was before kickoff.

HOME AND AWAY MARGINAL CHARTS

Bar charts showing P(team scores exactly k regulation-time goals) derived from the live PMF. Only values at or above each team's current goal count are non-zero; goals already scored are facts, not random events.

---

SCOPE AND LIMITATIONS — ALL PAGES

All probabilities on all three pages represent regulation time (90 minutes plus stoppage time) only. Extra time and penalty shootouts are not included.

The Poisson independence assumption — that home and away goals are generated by two separate, uncorrelated random processes — is an approximation. In reality, a goal changes the incentives for both teams and triggers tactical adjustments. Market reconciliation partially corrects for this correlation, but does not eliminate it entirely.

Calibration is based on 128 World Cup matches from 2018 and 2022, augmented by completed 2026 matches as the tournament progresses. The 2026 results receive substantially higher weight in the training process — they are the most relevant data available and reflect the specific conditions of this tournament.

Edge estimates are outputs of a probabilistic model. They are not profit guarantees. Market odds move between the time predictions are generated and kickoff. Always verify current odds before acting on any signal.

All probabilities represent regulation time (90 minutes + stoppage time) only. Extra time and penalties are excluded.
This guide is for informational and educational purposes. Please gamble responsibly.
