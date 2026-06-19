# EGM Elite Model — Promotion Status

**Branch:** feature/elite-clv-backbone  
**Clean Head:** 0a819c6  
**Date:** 2026-06-18  

## Current Verdict: SHADOW_READY

| Gate | Name | Status | Notes |
|------|------|--------|-------|
| 1 | Branch HEAD confirmed | ✅ PASS | HEAD is descendant of 0a819c6, 2038 tests pass |
| 2 | WC_USE_EGM_FOR_PUBLIC=false | ✅ PASS | Default OFF, enforced by contract tests |
| 3 | Shadow sanity (5+ matches, \|Δλ\|<0.15) | ⏳ PENDING | Pipeline not yet run with shadow data |
| 4 | Out-of-sample improvement (20+ matches, log-loss ≥0.5%) | ⏳ PENDING | Requires post-deployment data |

## What Each Gate Means

**Gate 3 is a SANITY CHECK, not a promotion threshold.**  
It proves the pipeline produces plausible shadow predictions.  
It does NOT prove the EGM model is better than the current live model.

**Gate 4 is the ONLY gate that approves public promotion.**  
It requires:
- ≥ 20 completed matches with immutable pre-match snapshots  
- Rolling-origin 1X2 log-loss improvement ≥ 0.5%, OR  
- Brier score improvement ≥ 0.003, OR  
- Calibration slope improvement ≥ 0.05 toward 1.0  

## Confederation Priors (Tier 6 Fallback)

Version: v1.0-manual-2026-06-18  
Status: **Informative prior, not fitted**  

| Confederation | EGM Prior | Basis |
|---|---|---|
| UEFA | +0.15 | Manual, 2006–2022 WC performance |
| CONMEBOL | +0.12 | Manual |
| CONCACAF | −0.05 | Manual |
| CAF | −0.10 | Manual |
| AFC | −0.08 | Manual |
| OFC | −0.20 | Manual |

These must be replaced by rolling-origin fitted values once ≥ 8 completed matches per confederation are available.

## CLV Superiority Claim

🔴 **NOT YET EVIDENCED**  
No immutable pre-match snapshots existed before 2026-06-18 deployment.  
CLV reports will populate at `reports/clv/` after the first shadow pipeline run.  
Do not describe the model as CLV-superior until post-deployment shadow data proves it.
