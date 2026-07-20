# Equal-Probability Baseline Audit

**Generated**: 2026-07-20T03:32:49Z

## What equal_probability actually is

**It is NOT a uniform distribution over score cells.**

It is **Poisson(λ=1.35, λ=1.35)** — the hardcoded WC average goals per team.
Both home and away teams are assigned the same expected goals = 1.35.
The result is a symmetric Bivariate Poisson PMF that peaks at 1-1.

## Sample probabilities

| Score | P(h,a) | NLL |
|-------|--------|-----|
| 0-0 | 0.067206 | 2.7000 |
| 1-0 | 0.090727 | 2.3999 |
| 1-1 | 0.122482 | 2.0998 |

## Why it beats parametric models on 128-match OOF NLL

**OOF NLL: 3.0219** vs. negative_binomial 4.4369

This is a **James-Stein / small-sample phenomenon**:

1. WC score space has 15×15 = 225 possible cells
2. With only 128 training matches and 32+ teams, parametric models
   over-fit team-specific parameters (attack/defense coefficients)
3. The shrinkage toward the global mean (λ=1.35) provides better
   out-of-sample NLL than team-specific MLE estimates
4. The equal_probability model **cannot discriminate between teams**:
   Brazil and South Africa get identical predictions (23.5%/29.7%/46.8%*)
5. A published prediction must discriminate between teams, which requires
   either (a) more training data, (b) external priors (Elo, FIFA rankings),
   or (c) market-implied probabilities from BDL odds

(*) For a neutral-venue match where both lambdas = 1.35

## Action taken

- equal_probability renamed/clarified as 'wc_average_prior' in documentation
- It is used ONLY as a diagnostic baseline, NEVER as publish_champion
- publish_champion = market_reconciled when BDL odds are available
- parametric_champion = negative_binomial (best parametric model)