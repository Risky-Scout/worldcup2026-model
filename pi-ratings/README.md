# Pi Ratings — Standalone Pure-Math Module

A self-contained Pi rating system for World Cup 2026. No external ML libraries required beyond `pandas` and `pyarrow` for reading the match data.

## The Math

Each team carries two sub-ratings:
- **home_rating** — attacking strength as the designated home side  
- **away_rating** — defensive burden as the away side  

After a match (home team scores `hg`, away team scores `ag`):

```
expected_home_margin = home.home_rating − away.away_rating
delta_h = α × (actual_margin − expected_home_margin)
delta_a = α × (−actual_margin − expected_away_margin)

home.home_rating += delta_h
home.away_rating −= β × delta_h   # symmetric decay
away.home_rating += delta_a
away.away_rating −= β × delta_a
```

**Composite rating** = `(home_rating + away_rating) / 2`

This is the team's Expected Goal Margin (EGM) versus a hypothetical average World Cup team on a neutral field.

## Hyperparameters

| Param | Value | Meaning |
|-------|-------|---------|
| `alpha` | 0.15 | Learning rate (how quickly ratings update) |
| `beta`  | 0.10 | Defensive coupling decay |

## Usage

```bash
# From repo root
python pi-ratings/run_ratings.py

# Custom parquet path
python pi-ratings/run_ratings.py --parquet data/processed/v1/matches.parquet
```

## Output: `ratings_report.csv`

| Column | Description |
|--------|-------------|
| `rank` | Rank by composite rating (1 = strongest) |
| `team` | Team name |
| `pi_home` | Home sub-rating |
| `pi_away` | Away sub-rating |
| `pi_composite` | `(pi_home + pi_away) / 2` |
| `egm_vs_average` | Expected goal margin vs average World Cup team on neutral field |
| `n_matches` | Number of matches used to build this rating |
| `last_match_date` | Date of last match used |

## Standalone Usage (no repo needed)

```python
from pi_model import PiRatings

model = PiRatings(alpha=0.15, beta=0.10)
model.update("Spain", "Morocco", home_goals=0, away_goals=0, match_date="2026-06-12")
model.update("Germany", "Japan", home_goals=4, away_goals=2, match_date="2026-06-13")

print(model.get_rating("Spain").composite)    # EGM vs average
print(model.get_rating("Germany").composite)
```
