# Data Card — wc2026

**Data version**: v1  
**Primary source**: BallDontLie (BDL) World Cup API (paid subscription)

---

## Datasets used

| Table | Source | Seasons | Description |
|-------|--------|---------|-------------|
| matches | BDL `/matches` | 2018, 2022, 2026 | Match schedule, scores, stage, venue |
| odds | BDL `/odds` | 2018, 2022, 2026 | Moneyline, totals, spreads (American odds) |
| team_stats | BDL `/team_match_stats` | 2018, 2022, 2026 | xG, shots, possession, etc. |
| player_stats | BDL `/player_match_stats` | 2018, 2022, 2026 | Per-player stats |
| shots | BDL `/match_shots` | 2018, 2022, 2026 | Shot coordinates, xG, xGOT |
| events | BDL `/match_events` | 2018, 2022, 2026 | Goals, cards, substitutions |
| lineups | BDL `/match_lineups` | 2018, 2022, 2026 | Starting XI and subs |
| momentum | BDL `/match_momentum` | 2018, 2022, 2026 | Minute-by-minute momentum values |
| group_standings | BDL `/group_standings` | 2018, 2022, 2026 | Group table positions |
| team_form | BDL `/match_team_form` | 2018, 2022, 2026 | Pre-match form data |

---

## Storage

All raw API responses are snapshotted before transformation:

```
data/raw/bdl/{season}/{endpoint}/{YYYYMMDDTHHMMSSZ}.jsonl
```

Normalised tables are written to:

```
data/processed/{data_version}/{table}.parquet
```

---

## Schema validation

Every BDL record is validated against pydantic models in `src/wc2026/data/schemas.py` before insertion into any dataframe. Any field rename or type change by BDL will raise a `ValidationError` immediately.

---

## Sample sizes (approximate, after 2022 World Cup)

- Completed matches: 64 (2022) + 64 (2018) = 128 historical matches
- 2026 matches: 104 scheduled

128 matches is a small sample. The model uses penaltyblog ratings as a global prior and World Cup-specific calibration for the tournament adjustment. See `limitations.md`.

---

## Leakage controls

- Training data for match `i` contains only matches with `match_datetime < match_i.match_datetime`
- Odds timestamps are attached to every prediction; closing odds never used in standard prediction mode
- Post-match stats (final xG, lineups after kickoff) are excluded from pregame features
