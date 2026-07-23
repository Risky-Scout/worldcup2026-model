# Composite Rating Methodology

**Generated**: 2026-07-23T23:28:59Z

## Why plain Elo is NOT the fallback

Plain Elo initialized to 1500 for unseen teams treats South Africa, Czechia,
Curaçao, etc. as 'average unknown teams.' This produced Mexico HW=23.5% when
the 6-vendor BDL market says 67.5%. Plain Elo is now a diagnostic baseline only.

## Composite prior sources (priority order)

| Priority | Source | Weight | Coverage |
|----------|--------|--------|----------|
| 1 | market_implied (BDL group-stage odds) | 0.70 | 48/48 teams |
| 2 | penaltyblog Pi rating (continuous update) | 0.15 | All teams with WC history |
| 3 | penaltyblog Elo (WC history) | 0.10 | All teams (1500 for new) |
| 4 | Massey offence component | 0.05 | Teams in 2018/2022 WC |
| 5 | confederation average (floor) | 0.05 | All teams |

## Market-implied lambda extraction

For each 2026 team with group-stage match odds in BDL:
1. Collect 1X2 and O/U 2.5 odds from all 6 vendors (fanduel, draftkings,
   betmgm, betrivers, caesars, fanatics)
2. Strip vig using multiplicative method, average across vendors
3. Call `penaltyblog.goal_expectancy_extended(hw, dr, aw, ou25)` to get
   (lambda_home, lambda_away) for each specific matchup
4. For each team: collect their lambda_scored and lambda_conceded across
   their 3 group matches (n=3 matches × 6 vendors = 18 odds observations)
5. Average to get team-level market_implied_attack and market_implied_defense

**Key insight**: Every 2026 team has 3 group-stage matches in the schedule.
With 6 BDL vendors, we have 18 independent market observations per team.
This completely replaces the need for Elo=1500 defaults.

## Rating-to-lambda conversion

For Elo: `lambda = WC_avg * exp((elo - 1500) / 300 * 0.5)`
- Elo 1500 → lambda 1.25 (global WC average)
- Elo 1600 → lambda 1.47
- Elo 1400 → lambda 1.06

For Pi: `lambda = WC_avg * exp(pi_rating * 0.25)`
- Pi 0.0 → lambda 1.25
- Pi +1.0 → lambda 1.61
- Pi -1.0 → lambda 0.97

For Massey: `lambda = WC_avg + massey_offence * 0.4`
- Massey is an offense/defense decomposition from the linear system

## Blending

When market odds are available (the common case for 2026):
```
composite_att = 0.70 * market_att + 0.15 * pi_att + 0.10 * elo_att + 0.05 * massey_att
                + 0.05 * confederation_att
```

When market odds are NOT available:
```
composite_att = 0.45 * pi_att + 0.30 * elo_att + 0.15 * massey_att + 0.10 * confederation_att
```

## Host-nation adjustment

USA, Canada, Mexico receive +0.10 attack, -0.10 defense (neutral venue assumption
with slight home-crowd advantage in home-region venues).

## Match prediction from composite prior

Given home team H and away team A with composite priors:
```
lambda_h = (att_H / WC_avg) * (WC_avg / def_A) * WC_avg
         = att_H * WC_avg / def_A
lambda_a = (att_A / WC_avg) * (WC_avg / def_H) * WC_avg
         = att_A * WC_avg / def_H
```
Then Dixon-Coles grid(lambda_h, lambda_a, rho=-0.05) gives the composite PMF.

## Example: Mexico vs South Africa

| Metric | Mexico | South Africa |
|--------|--------|--------------|
| market_implied_attack | 2.316 | 0.801 |
| market_implied_defense | 0.718 | 1.466 |
| final_attack_lambda | 2.027 | 1.010 |
| final_defense_lambda | 0.769 | 1.170 |
| composite lambda_h | **2.252** | — |
| composite lambda_a | — | **1.708** |
| composite PMF home_win | **0.504** | (was 0.234 with elo_prior_blend) |
| BDL market home_win | **0.675** | |
| composite vs market gap | 0.171 | (was 0.441 with elo) |