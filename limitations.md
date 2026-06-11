# Limitations

This document is honest about what the model does NOT do well.

---

## Small sample size

World Cup data contains ~128 completed matches (2018 + 2022). This is insufficient to reliably estimate team-specific parameters for 32+ teams from scratch. Mitigations:

- penaltyblog goal models use conjugate priors via hierarchical pooling
- Elo baseline provides a regularised team-strength prior
- Dixon-Coles rho parameter is global, not per-team
- Walk-forward OOF calibration uses all available history

Without broader international football data (friendly matches, qualifiers), team priors are based on limited evidence. New teams with no 2018/2022 data (e.g. first-time qualifiers) rely entirely on the global average.

---

## Odds coverage gaps

BDL odds coverage for historical 2018/2022 matches may be incomplete or missing for some vendors. In those cases:

- Market reconciliation is skipped
- The calibration_status field will be "uncalibrated" or "temperature_scaled" (not "market_calibrated")
- A warning is emitted in the prediction JSON

---

## Exact-score calibration limits

With 128 historical matches, the empirical frequency of any specific score (e.g. 2-1) is only a handful of observations. Temperature scaling calibrates the PMF shape globally but cannot reliably correct specific score-cell biases. The model applies a Dixon-Coles τ correction for low-scoring cells (0-0, 1-0, 0-1, 1-1) but has limited evidence to verify it at World Cup scale.

---

## Live model status

The live model is architecturally supported but **not validated**. Replay validation against 2022 matches has not been completed. Do not use live predictions in any betting context until `data/predictions/live_replay_2022.parquet` and `reports/live_replay_validation.md` are produced. These require running `make fetch-bdl && make build-dataset && wc2026 validate-live` after BDL data is loaded.

---

## Bayesian models

The Bayesian (`BayesianGoalModel`) and hierarchical Bayesian (`HierarchicalBayesianGoalModel`) models from penaltyblog are included in the model ladder but disabled by default due to MCMC runtime (~5–15 minutes per model fit). Enable with `--include-bayesian`. Their out-of-fold performance has not yet been benchmarked.

---

## Market reconciliation is a soft constraint

The KL minimisation reconciliation moves the model PMF towards market consensus, but does not guarantee the model matches market odds exactly. Large model-vs-market differences may indicate model errors, market error, or genuine edge. Treat reconciled predictions as a blend, not as market endorsement.

---

## Not validated against live odds

This model has not been validated against actual sportsbook closing lines. Expected Value (EV) and Closing Line Value (CLV) metrics are not yet available. These require producing predictions before line movement and recording them with timestamps.

---

## Known missing features

- First-half PMF (requires separate model trained on HT scores)
- Exact-score market reconciliation (BDL exact-score odds not yet parsed)
- Roster strength / injury adjustments (data not available in BDL)
- Non-homogeneous minute hazard for live model (flat scaling used as placeholder)
- Stoppage time modelling
