# Champion Model Selection (Real BDL Data)

**Generated**: 2026-06-11T16:08:25Z
**Selection criterion**: Lowest OOF exact-score negative log-likelihood

## OOF ranking

| Rank | Model | OOF NLL | vs. Equal-Prob | vs. Dixon-Coles | RPS | Brier |
|------|-------|---------|---------------|----------------|-----|-------|
| 1 | elo | 3.1493 | N/A | -1.7405 | 0.1782 | 0.7073 |
| 2 | negative_binomial | 4.5159 | N/A | -0.3740 | 0.1967 | 0.7914 |
| 3 | dixon_coles | 4.8898 | N/A | +0.0000 | 0.2000 | 0.8257 |
| 4 | zero_inflated_poisson | 5.1683 | N/A | +0.2785 | 0.2057 | 0.8407 |
| 5 | poisson | 5.1734 | N/A | +0.2836 | 0.2058 | 0.8440 |
| 6 | bivariate_poisson | 5.2690 | N/A | +0.3792 | 0.2237 | 0.8959 |
| 7 | weibull_copula | 7.1012 | N/A | +2.2113 | 0.2217 | 0.8691 |

## ✅ Champion: **elo**

- OOF exact-score NLL: **3.1493**
- OOF 1X2 RPS: 0.1782
- Beats Dixon-Coles: ✅ Yes (-1.7405)
- Temperature: 1.000
- N OOF predictions: 118

## Note on market-implied baseline

Full market-implied baseline benchmarking requires historical closing odds for
2018+2022 matches. BDL provides live odds for 2026 only. Market-implied NLL
on 2018+2022 is not computable from BDL. Recommend using CLV (closing-line
value) as market-comparison metric on 2026 live matches as results come in.