# BDL Endpoint Coverage (Real Data)

**Generated**: 2026-06-11T16:08:25Z
**API**: BallDontLie FIFA World Cup API (paid subscription)

## Match counts

| Season | Matches | Status |
|--------|---------|--------|
| 2018 | 64 | ✅ All completed |
| 2022 | 64 | ✅ All completed |
| 2026 | 104 | 104 scheduled |
| **Total** | **232** | |

## Odds coverage

| Metric | Value |
|--------|-------|
| Odds rows | 315 |
| Vendors | 6 (betmgm, betrivers, caesars, draftkings, fanatics, fanduel) |
| Correct-score rows | 5047 |
| Market types | 12 |

## Market type breakdown

| Market Type | Rows |
|------------|------|
| total | 10243 |
| other | 7371 |
| correct_score | 5047 |
| team_total | 3566 |
| double_chance | 2154 |
| spread | 2144 |
| timing | 1728 |
| both_teams_to_score | 1613 |
| margin | 1579 |
| result_combo | 884 |
| moneyline | 648 |
| draw_no_bet | 285 |

## Endpoint status

| Endpoint | Status | Notes |
|----------|--------|-------|
| `/matches` | ✅ | Used for training and prediction |
| `/odds` | ✅ | 1X2 + totals + markets sub-array |
| `odds.markets[].type=correct_score` | ✅ | Parsed to correct_score_odds.parquet |
| `odds.markets[].type=total` | ✅ | Multiple O/U lines |
| `odds.markets[].type=spread` | ✅ | Asian handicap |
| `odds.markets[].type=double_chance` | ✅ | DC markets |
| `odds.markets[].type=draw_no_bet` | ✅ | DNB markets |
| `/team_match_stats` | ✅ | xG, shots, possession (for live model) |
| `/match_events` | ✅ | Goals, cards, subs |
| `/match_shots` | ✅ | Shot data |
| `/match_lineups` | ✅ | Starting XI |
| `/match_momentum` | ✅ | Minute momentum |
| `/group_standings` | ✅ | Current standings |
| `/match_team_form` | ✅ | Pre-match form |