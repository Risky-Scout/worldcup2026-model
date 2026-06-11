# BDL Endpoint Coverage

**API**: BallDontLie FIFA World Cup API (paid subscription required)
**Base URL**: https://api.balldontlie.io/fifa/worldcup/v1

| Endpoint | Description | Fetched by | Processed Table | Status |
|----------|-------------|------------|-----------------|--------|
| `/matches` | Match schedule, scores, stage | `fetch_matches()` | `matches.parquet` | ✅ Implemented |
| `/odds` | Moneyline, totals, spreads (all vendors) | `fetch_odds()` | `odds.parquet` | ✅ Implemented |
| `/team_match_stats` | xG, shots, possession, corners, cards | `fetch_team_stats()` | `team_stats.parquet` | ✅ Implemented |
| `/player_match_stats` | Per-player ratings, goals, assists, xG | `fetch_player_stats()` | `player_stats.parquet` | ✅ Implemented |
| `/match_events` | Goals, cards, substitutions | `fetch_events()` | `events.parquet` | ✅ Implemented |
| `/match_shots` | Shot coordinates, xG, xGOT | `fetch_shots()` | `shots.parquet` | ✅ Implemented |
| `/match_lineups` | Starting XI, substitutes | `fetch_lineups()` | `lineups.parquet` | ✅ Implemented |
| `/match_momentum` | Minute-by-minute momentum | `fetch_momentum()` | `momentum.parquet` | ✅ Implemented |
| `/group_standings` | Group table positions | `fetch_group_standings()` | `group_standings.parquet` | ✅ Implemented |
| `/match_team_form` | Pre-match form data | `fetch_team_form()` | `team_form.parquet` | ✅ Implemented |

## Not yet parsed (in odds.markets sub-array)

| Market | Description | Status |
|--------|-------------|--------|
| Exact score odds | `markets[].type == 'exact_score'` | ⏳ Pending (will improve low-score calibration) |
| Double chance | `markets[].type == 'double_chance'` | ⏳ Pending |
| Draw no bet | `markets[].type == 'draw_no_bet'` | ⏳ Pending |
| BTTS | `markets[].type == 'both_teams_to_score'` | ⏳ Pending |
| Asian handicap (per-line) | `markets[].type == 'asian_handicap'` | ⏳ Pending |

## Raw snapshot format

```
data/raw/bdl/{season}/{endpoint}/{YYYYMMDDTHHMMSSZ}.jsonl
```

Each line is one API record (JSON). Timestamped for reproducibility.
Schema validated via pydantic before normalization.