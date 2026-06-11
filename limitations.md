# Known Limitations — wc2026 PMF Engine

**Last updated**: 2026-06-11

This document is the honest account of current limitations. It is intentionally non-promotional.

---

## 1. Small WC-only training set

**Impact**: HIGH

- Only 128 completed WC matches (2018+2022) are available for model training
- 32+ teams means each team appears in only ~4-8 training matches on average
- Team-specific attack/defense parameters estimated from 4-8 matches have very high uncertainty
- This is why `equal_probability` (Poisson λ=1.35, the WC average) beats all parametric models on OOF NLL: James-Stein shrinkage. It is NOT that parametric models are poorly coded; it is that the sample is too small for their advantages to materialize
- Mitigation: market odds from 6 BDL vendors provide team-quality signal that the model cannot replicate from 128 matches

---

## 2. Parametric models lose to Poisson(1.35) on OOF NLL

**Impact**: HIGH (for published predictions without odds)

- best parametric model is negative_binomial (NLL=4.52) vs. equal_probability (NLL=3.02)
- This is a factor of ~4x worse probability on any given correct score
- The gap closes as 2026 results accumulate
- Mitigation: market_reconciled mode replaces the model PMF with market-implied for all matches with odds

---

## 3. No live in-game model

**Impact**: MEDIUM

- The architecture (matchflow, BDL events, momentum) is defined but not yet implemented
- Live predictions are NOT available
- Pre-game PMFs should not be re-used for in-game applications
- Target: validate on 2022 minute-by-minute replay before deploying live

---

## 4. New-team priors use confederation averages

**Impact**: MEDIUM

- Teams with no 2018/2022 WC history (e.g., South Africa, Czechia, Curaçao) get:
  `attack_lambda = confederation_average` (CAF=1.10, UEFA=1.30, CONCACAF=1.20, etc.)
- This is better than flat Elo=1500 for all new teams but still imprecise
- No FIFA ranking, qualifying performance, or BDL team form is used yet
- Mitigation: market odds from BDL supersede these priors for matches with odds

---

## 5. Temperature calibration near T=1.0

**Impact**: LOW–MEDIUM

- After the fix (fitting `ScorePMFCalibrator` on OOF predictions), temperatures are:
  equal_probability: 1.077, elo: 1.255, negative_binomial: 2.997
- T≈3.0 for parametric models means they are overconfident (too peaked PMFs)
- With only 106 OOF predictions, temperature estimates have high variance
- Mitigation: temperature will be re-fitted as 2026 results accumulate; T=2.997 for negative_binomial means it is applying strong smoothing at publish time

---

## 6. Correct-score odds used in reconciliation but not backtested

**Impact**: MEDIUM

- 5,047 correct-score rows are parsed from BDL for 2026 matches
- They are used in minimum-KL reconciliation to constrain specific PMF cells
- This has NOT been backtested for calibration improvement on 2018/2022 data
  (correct-score odds were not captured for historical matches)
- Mitigation: correct-score constraint weight is set conservatively (α ≤ 0.85)

---

## 7. No opening-line vs. closing-line separation

**Impact**: LOW–MEDIUM

- BDL snapshots are point-in-time; we do not currently track how odds have moved
- The model uses current odds, not opening odds
- For a proper closing-line benchmark, historical BDL snapshots would need to be collected daily
- This is a backtest/CLV limitation, not a live-prediction limitation

---

## 8. Market reconciliation uses multiplicative vig removal

**Impact**: LOW

- Several vig-removal methods are available (multiplicative, additive, Shin, power, odds-ratio)
- We use multiplicative only (well-tested, conservative)
- Shin and power methods may give better results for correct-score markets with high overround
- TODO: compare methods in the market calibration report

---

## 9. 72/104 matches are predictable today

**Impact**: LOW

- 32 of 104 scheduled 2026 matches are knockout placeholders (W73 vs W75, etc.)
- These cannot be predicted until group stage completes
- 72 named group-stage matches are fully predicted
- All 72 use market_reconciled as the publish mode

---

## What is NOT a limitation

These items are working correctly:

- BDL real data ingestion (2018, 2022, 2026) ✅
- June 11 opening day: Mexico vs South Africa AND South Korea vs Czechia ✅
- Three publish modes (pure_model, market_implied, market_reconciled) ✅
- Market anchor: Mexico HW=67.5% (market) published, not 23.5% (pure model) ✅
- All markets derived from the single joint PMF ✅
- PMF sums to 1.0 ✅
- Tail mass explicit ✅
- Correct-score odds parsed (5,047 rows) and used in reconciliation ✅
- Temperature calibration now fitted (not defaulting to T=1.0 everywhere) ✅
- Champion policy defined with 5 explicit champion tiers ✅
- Walk-forward OOF (no data leakage) ✅
