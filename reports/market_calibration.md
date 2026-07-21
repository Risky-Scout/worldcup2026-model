# Market Calibration Report (Real BDL Data)

**Generated**: 2026-07-21T21:39:26Z

## Publish mode distribution

| Mode | Count | Description |
|------|-------|-------------|
| market_reconciled | 0 | Market + model blend (default publish) |
| market_implied | 0 | Pure market PMF, no model |
| pure_model | 0 | Model only, no odds available |

**Matches with correct-score odds**: 0

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

**2026 predictions generated**: 0 named matches
  market_reconciled: 0
  with correct-score data: 0
  correct-score vendors breakdown: 1-vendor=0, 2+vendors=0

## Vendors
fanduel, draftkings, betmgm, betrivers, caesars, fanatics (610 total rows)