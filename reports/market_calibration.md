# Market Calibration Report (Real BDL Data)

**Generated**: 2026-06-12T00:46:28Z

## Publish mode distribution

| Mode | Count | Description |
|------|-------|-------------|
| market_reconciled | 72 | Market + model blend (default publish) |
| market_implied | 0 | Pure market PMF, no model |
| pure_model | 0 | Model only, no odds available |

**Matches with correct-score odds**: 72

## Reconciliation method

For each match with BDL odds:
1. Strip vig from 1X2 (multiplicative method, 6 vendors)
2. Strip vig from O/U 0.5–6.5 lines (all available)
3. Strip vig from BTTS, DNB, double chance where available
4. Build market_implied PMF via `penaltyblog.goal_expectancy_extended`
5. Parse correct-score outcomes (type=correct_score, period=match)
6. **Stable linear blend**: reconciled = α × market_implied + (1-α) × composite_rating
   (SLSQP removed — caused impossible-score artifacts like P(4-9)=0.026)
7. Gentle IPF for correct-score cells (α=0.3 for 1 vendor, α=0.5 for 2+ vendors)
8. Sanity guard: cap any cell with total_goals≥9 to ≤1e-6

Market quality score (0-1) determines α:
- 6 vendors + correct score → quality ≈ 0.82 → α ≈ 0.82
- 6 vendors, no correct score → quality ≈ 0.62 → α ≈ 0.62

**2026 predictions generated**: 72 named matches
  market_reconciled: 72
  with correct-score data: 72
  correct-score vendors breakdown: 1-vendor=72, 2+vendors=0

## Vendors
fanduel, draftkings, betmgm, betrivers, caesars, fanatics (315 total rows)

## Mexico vs South Africa — Three modes

| Mode | HW | D | AW | Over2.5 | expG home | expG away |
|------|----|----|-----|---------|----------|----------|
| composite (composite_rating_pmf) | 0.624 | 0.23559 | 0.14042 | ? | 1.7937 | 0.7064 |
| market_implied | 0.67508 | 0.21113 | 0.11378 | 0.44026 | 1.8413 | 0.5973 |
| **market_reconciled (PUBLISHED)** | **0.67692** | **0.20542** | **0.11766** | **?** | **1.9272** | **0.6241** |

## South Korea vs Czechia — Three modes

| Mode | HW | D | AW | Over2.5 | expG home | expG away |
|------|----|----|-----|---------|----------|----------|
| composite (composite_rating_pmf) | 0.37739 | 0.29183 | 0.33078 | ? | 1.2307 | 1.133 |
| market_implied | 0.36171 | 0.31403 | 0.32426 | 0.42274 | 1.2253 | 1.1459 |
| **market_reconciled (PUBLISHED)** | **0.36245** | **0.31256** | **0.32499** | **?** | **1.205** | **1.1288** |