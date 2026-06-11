# Joint Score PMF Validation Report

## Sample PMF (Dixon-Coles: λ_h=1.5, λ_a=1.2, ρ=-0.05, max_goals=15)

- Grid sum: 1.00000000
- Tail mass: 0.00000000
- Grid + tail: 1.00000000
- Consistency errors: []

## Invariant tests

| Check | Value | Pass |
|-------|-------|------|
| PMF + tail = 1.0 | 1.00000000 | ✅ |
| All values ≥ 0 | min=3.32e-20 | ✅ |
| 1X2 sum = 1.0 | 1.00000100 | ✅ |
| BTTS sum = 1.0 | 1.00000000 | ✅ |
| Tail mass < 0.5% | 0.000000 | ✅ |
| No consistency errors | 0 errors | ✅ |

## Arbitrary score lookup

- P(0,0) = 0.073276
- P(1,0) = 0.093276
- P(2,1) = 0.090755
- P(5,0) [in-grid] = 0.004254
- P(15,0) [out-of-grid, tail] = 0.00e+00
- P(20,3) [out-of-grid, tail] = 0.00e+00

## Top 10 scorelines

| Rank | Score | Probability |
|------|-------|-------------|
| 1 | 1-1 | 12.7057% |
| 2 | 1-0 | 9.3276% |
| 3 | 2-1 | 9.0755% |
| 4 | 0-1 | 7.5831% |
| 5 | 2-0 | 7.5629% |
| 6 | 0-0 | 7.3276% |
| 7 | 1-2 | 7.2604% |
| 8 | 2-2 | 5.4453% |
| 9 | 0-2 | 4.8403% |
| 10 | 3-1 | 4.5377% |

## OOF prediction summary (synthetic data)

| Model | N | Exact-Score NLL |
|-------|---|----------------|
| equal_probability | 113 | 3.3452 |
| elo | 113 | 3.4529 |
| historical_base_rate | 113 | 4.3856 |
| negative_binomial | 102 | 4.5707 |
| dixon_coles | 60 | 4.8106 |
| poisson | 102 | 5.2134 |