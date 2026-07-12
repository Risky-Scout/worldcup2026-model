# Changes Made — Emergency Hardening 2026-07-12T07:23:38Z

## Branch
`emergency/presentation-hardening-2026-07-13`

## P0 Changes Implemented

### 1. `src/wc2026/config.py`
Added presentation safe mode flags:
- `PRESENTATION_SAFE_MODE` (env: `WC_PRESENTATION_SAFE_MODE`)
- `SUPPRESS_FIRST_HALF_MARKETS` (env: `WC_SUPPRESS_FIRST_HALF_MARKETS`)
- `SUPPRESS_DRAW_BOOST` (env: `WC_SUPPRESS_DRAW_BOOST`)
- `DISABLE_AUTO_MARKET_WEIGHT` (env: `WC_DISABLE_AUTO_MARKET_WEIGHT`)
- `DISABLE_CIRCULAR_EDGE` (env: `WC_DISABLE_CIRCULAR_EDGE`)

### 2. `scripts/run_real_pipeline.py` — `_group_stage_draw_adjustment`
- **Fixed false comment**: "top 3 advance" corrected to "top 2 advance automatically + 8 best third-place"
- **Added safe mode guard**: returns unadjusted probabilities when `PRESENTATION_SAFE_MODE=true`
- **Added suppression flag**: `SUPPRESS_DRAW_BOOST` disables heuristic independently

### 3. `src/wc2026/tournament/group_incentives.py`
- **Fixed module docstring**: Removed "top 3 advance" claim; corrected to 2026 WC format
- **Added safe mode guard**: `adjust_pmf_for_group_incentives` returns unchanged PMF in safe mode

### 4. `scripts/simulate_groups.py` — tiebreaking
- **`_rank_group`**: Final tiebreak changed from alphabetical (`t`) to seeded random lots
- **`_rank_third_place`**: Final tiebreak changed from alphabetical to seeded random lots
- **`run_simulation`**: Passes `sim_rng` (seeded per-simulation) to both ranking functions
- **`run_full_tournament_simulation`**: Same fix applied
- **`render_markdown`**: Updated methodology note to remove "alphabetical" label
- Now documents: "Format: 12 groups × 4 teams; top 2 advance automatically + best 8 third-place"

### 5. `src/wc2026/markets/edge.py` — circular edge guard and CI rename
- **Circular edge guard**: `compute_market_edges` now accepts `prediction_mode` parameter
  - When `market_reconciled` or `market_implied`: `value_flag=False`, `half_kelly=0.0`
  - Reason string includes `CIRCULAR_EDGE_SUPPRESSED: prediction_mode=...`
- **Lambda sensitivity rename**:
  - `ci_lower_90` → `lambda_sensitivity_lower`
  - `ci_upper_90` → `lambda_sensitivity_upper`
  - `to_dict()` keys: `ci_90_lower`/`ci_90_upper` → `lambda_sensitivity_lower`/`upper`
  - Field docstrings updated to clarify these are NOT statistical confidence intervals
- **`compute_edge_report`**: passes `prediction_mode` to `compute_market_edges`

### 6. `scripts/run_real_pipeline.py` — first-half suppression
- First-half PMF computation (`_first_half_pmf`) suppressed when `PRESENTATION_SAFE_MODE=true`
  or `SUPPRESS_FIRST_HALF_MARKETS=true`

### 7. `scripts/upload_predictions.py` — timestamp preservation
- **Bug fix**: `doc["generated_at"] = datetime.now(...)` was OVERWRITING the original
  probability-generation timestamp with the upload time
- **Fix**: `generated_at` is now preserved from the published JSON
- **Added**: `doc["uploaded_at"] = upload_ts` — separately records when the file was uploaded

### 8. `scripts/prepare_presentation_publish.py` (NEW)
- Reproducible presentation package generator
- Validates all published JSON files
- Generates all `reports/presentation_2026-07-13/` artifacts
- Produces `READY / READY_WITH_LIMITATIONS / NOT_READY` verdict

### 9. `tests/test_presentation_hardening.py` (NEW)
- 23 new tests covering all P0 hardening requirements
- All 23 tests pass (full suite: 1915 passed, 0 failed)
