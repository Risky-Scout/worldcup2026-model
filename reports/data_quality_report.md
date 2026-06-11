# Data Quality Report

**Data version**: v1
**Generated**: 2026-06-11
**Source**: Synthetic data (mirrors BDL structure)

## Dataset overview

| Metric | Value |
|--------|-------|
| Total matches | 128 |
| Completed | 128 |
| Missing goals | 0 |
| Season 2018 | 64 matches |
| Season 2022 | 64 matches |

## Schema validation

All BDL records validated against pydantic schemas before normalization.
Any field rename or type change will raise `ValidationError` immediately.

## Goal statistics

| Stat | Home | Away |
|------|------|------|
| Mean goals | 1.750 | 1.617 |
| Median goals | 1.5 | 1.0 |
| Std goals | 1.425 | 1.409 |
| Max goals | 6 | 7 |

## Score distribution

| Score | Count | % |
|-------|-------|---|
| 1-1 | 13 | 10.2% |
| 0-1 | 13 | 10.2% |
| 1-2 | 11 | 8.6% |
| 0-0 | 8 | 6.2% |
| 3-0 | 8 | 6.2% |
| 2-1 | 8 | 6.2% |
| 3-1 | 6 | 4.7% |
| 3-3 | 5 | 3.9% |
| 3-2 | 5 | 3.9% |
| 4-2 | 5 | 3.9% |

## Limitations
- This is synthetic data for demonstration.
- Real data requires `BDL_API_KEY` in `.env` and `make fetch-bdl`.
- With real data: 128 completed matches (64×2018, 64×2022).