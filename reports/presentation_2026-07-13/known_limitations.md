# Known Limitations — 2026-07-12T07:23:38Z

## CRITICAL (must be disclosed in presentation)

1. **Probability source**: Published probabilities are market-reconciled distributions.
   They combine a structural prior with BDL sportsbook consensus. They are NOT
   independent forecasts and must not be compared against the same sportsbook inputs
   to generate betting edge signals.

2. **No validated first-half model**: First-half markets were approximated using
   λ×0.45, which is an arbitrary constant with no empirical validation.
   These are SUPPRESSED in presentation safe mode.

3. **No validated draw-boost**: The draw probability heuristic (+3pp) was based
   on an incorrect "top 3 advance" assumption about the 2026 WC format.
   The 2026 format is: top 2 advance automatically + 8 best third-place teams.
   This heuristic is SUPPRESSED in presentation safe mode.

4. **Lambda sensitivity ≠ confidence intervals**: The ±12% lambda perturbation
   produces a sensitivity range, not a frequentist confidence interval.
   Fields renamed from `ci_90_*` to `lambda_sensitivity_*`.

5. **CLV measurement**: The CLV pipeline records model_prob vs closing_prob.
   This is model-vs-close disagreement, not ticket CLV. No actual tickets
   were placed, so there is no realised-profit CLV to report.

6. **In-sample weight selection disabled**: The `_auto_select_market_weight`
   function was selecting market_weight by evaluating on the same completed
   matches used to generate predictions. This is in-sample overfitting.
   Weight fixed at 0.20 (pre-tournament default).

## HIGH (disclosed; not blocking)

7. **Extra-time and penalty model**: Advancement probabilities from knockout
   stage simulations use a 50/50 coin flip for draws, which is a simplification.
   Label: EXPERIMENTAL.

8. **Tiebreaking**: FIFA criteria include head-to-head and fair-play, which
   require full match log. After GF, seeded random lots are used in simulation.
   This is correct procedure but not the same as full FIFA evaluation.

9. **Sample size**: The 2026 WC has ~64 group-stage matches plus knockout matches.
   This is a small sample for calibration. Walk-forward relies primarily on
   2018 and 2022 data.

## MEDIUM

10. **Market data**: BDL provides sportsbook odds from a limited set of vendors.
    The no-vig consensus may not represent the full market.

11. **Live model**: Live predictions are not validated independently from
    replay accuracy. Latency and state management are not production-hardened.

12. **Roster/injury data**: Player strength and lineup adjustments use
    available BDL data which may be incomplete or delayed.
