# Demo Readiness — 2026-07-12T07:23:38Z

## Verdict: READY_WITH_LIMITATIONS

The pages and calculations are operational. The following limitations apply:

1. Published probabilities are market-reconciled (not independent model predictions)
2. First-half markets are suppressed (not validated)
3. Draw-boost heuristic is suppressed (was incorrectly assuming "top 3 advance" format)
4. Alphabetical tiebreaking replaced with seeded random (FIFA rule compliance)
5. Lambda sensitivity ranges are not labelled as confidence intervals
6. Kelly / betting edge output is blocked for market-reconciled PMFs (circular edge guard)
7. CLV history records model-vs-close disagreement, not ticket CLV
