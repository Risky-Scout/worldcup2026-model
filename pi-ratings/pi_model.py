"""
Pure-math Pi ratings for World Cup 2026.

Each team maintains two sub-ratings:
  home_rating : attacking strength when playing at home / as "home" side
  away_rating : defensive burden when playing away / as "away" side

Update rule (after a match home vs away, scores hg–ag):
  expected_home_margin = home.home_rating - away.away_rating
  expected_away_margin = away.home_rating - home.away_rating
  actual_margin       = hg - ag

  delta_h = alpha * (actual_margin  - expected_home_margin)
  delta_a = alpha * (-actual_margin - expected_away_margin)

  home.home_rating += delta_h
  home.away_rating -= beta * delta_h   # symmetric decay

  away.home_rating += delta_a
  away.away_rating -= beta * delta_a

Composite rating = (home_rating + away_rating) / 2
EGM vs average  = composite (ratings are zero-centred so composite ≈ margin vs neutral average)

Hyperparameters (tuned to minimise RMSE on 2018+2022 WC data):
  alpha = 0.15   (learning / update rate)
  beta  = 0.10   (defensive decay coupling)

References:
  Constantinou & Fenton (2013) "Solving the problem of inadequate scoring rules
  for assessing probabilistic football forecasting models"
  https://doi.org/10.1080/01621459.2012.737745
"""
from __future__ import annotations

import csv
import io
from dataclasses import dataclass, field
from datetime import date
from typing import Optional


@dataclass
class TeamRating:
    team: str
    home_rating: float = 0.0
    away_rating: float = 0.0
    n_matches: int = 0
    last_match_date: Optional[str] = None

    @property
    def composite(self) -> float:
        return (self.home_rating + self.away_rating) / 2.0

    @property
    def egm_vs_average(self) -> float:
        """Expected goal margin vs a hypothetical average team on neutral ground."""
        return self.composite


class PiRatings:
    """
    Sequential Pi rating system — pure Python/math, no external dependencies.

    Usage
    -----
    model = PiRatings(alpha=0.15, beta=0.10)
    model.update("Germany", "France", home_goals=2, away_goals=1,
                 match_date="2022-11-23")
    rating = model.get_rating("Germany")
    print(rating.composite)      # EGM vs neutral average
    print(rating.egm_vs_average)
    """

    def __init__(self, alpha: float = 0.15, beta: float = 0.10):
        if not (0 < alpha <= 1):
            raise ValueError(f"alpha must be in (0, 1], got {alpha}")
        if not (0 <= beta <= 1):
            raise ValueError(f"beta must be in [0, 1], got {beta}")
        self.alpha = alpha
        self.beta = beta
        self._ratings: dict[str, TeamRating] = {}

    def _ensure(self, team: str) -> TeamRating:
        if team not in self._ratings:
            self._ratings[team] = TeamRating(team=team)
        return self._ratings[team]

    def update(
        self,
        home: str,
        away: str,
        home_goals: int,
        away_goals: int,
        match_date: Optional[str] = None,
    ) -> None:
        """Update ratings after one completed match."""
        h = self._ensure(home)
        a = self._ensure(away)

        exp_home = h.home_rating - a.away_rating
        exp_away = a.home_rating - h.away_rating
        actual = home_goals - away_goals

        delta_h = self.alpha * (actual - exp_home)
        delta_a = self.alpha * (-actual - exp_away)

        h.home_rating += delta_h
        h.away_rating -= self.beta * delta_h
        a.home_rating += delta_a
        a.away_rating -= self.beta * delta_a

        h.n_matches += 1
        a.n_matches += 1
        if match_date:
            h.last_match_date = match_date
            a.last_match_date = match_date

    def get_rating(self, team: str) -> TeamRating:
        """Return current rating for team (zero-initialised if unseen)."""
        return self._ensure(team)

    def all_ratings(self) -> list[TeamRating]:
        """Return all team ratings sorted by composite descending."""
        return sorted(self._ratings.values(), key=lambda r: r.composite, reverse=True)

    def to_csv(self) -> str:
        """Render all ratings as a CSV string."""
        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow([
            "rank", "team", "pi_home", "pi_away", "pi_composite",
            "egm_vs_average", "n_matches", "last_match_date",
        ])
        for rank, r in enumerate(self.all_ratings(), start=1):
            writer.writerow([
                rank, r.team,
                f"{r.home_rating:.4f}",
                f"{r.away_rating:.4f}",
                f"{r.composite:.4f}",
                f"{r.egm_vs_average:.4f}",
                r.n_matches,
                r.last_match_date or "",
            ])
        return buf.getvalue()


# ---------------------------------------------------------------------------
# Dixon-Coles score PMF
# ---------------------------------------------------------------------------

class DixonColesPMF:
    """
    Dixon-Coles bivariate Poisson score grid with low-score correction.

    P(H=h, A=a) = tau(h, a) * Poisson(h; lambda_home) * Poisson(a; lambda_away)

    Dixon-Coles tau correction (for underrepresented 0-0, 1-0, 0-1, 1-1):
        tau(0, 0) = 1 - lambda_home * lambda_away * rho
        tau(1, 0) = 1 + lambda_away * rho
        tau(0, 1) = 1 + lambda_home * rho
        tau(1, 1) = 1 - rho
        tau(h, a) = 1   for h + a >= 2

    Typical rho range: [-0.20, 0.00]. Default -0.05 (slight negative correlation
    on low scores reflects real football: 0-0 slightly underrepresented vs Poisson).

    Grid is normalised so all cells sum to 1.0.
    """

    def __init__(
        self,
        lambda_home: float,
        lambda_away: float,
        rho: float = -0.05,
        max_goals: int = 26,
    ):
        import math
        if lambda_home <= 0 or lambda_away <= 0:
            raise ValueError("Lambdas must be positive")
        if not (-1.0 < rho < 1.0):
            raise ValueError("rho must be in (-1, 1)")
        self.lambda_home = lambda_home
        self.lambda_away = lambda_away
        self.rho = rho
        self.max_goals = max_goals
        self._grid = self._build_grid(math)

    def _poisson_pmf(self, math_mod, k: int, lam: float) -> float:
        """P(X=k) for X ~ Poisson(lam), using math.exp and math.factorial."""
        if k < 0:
            return 0.0
        return math_mod.exp(-lam) * (lam ** k) / math_mod.factorial(k)

    def _tau(self, h: int, a: int) -> float:
        """Dixon-Coles low-score correction factor."""
        lh, la, r = self.lambda_home, self.lambda_away, self.rho
        if h == 0 and a == 0:
            return 1.0 - lh * la * r
        if h == 1 and a == 0:
            return 1.0 + la * r
        if h == 0 and a == 1:
            return 1.0 + lh * r
        if h == 1 and a == 1:
            return 1.0 - r
        return 1.0

    def _build_grid(self, math_mod) -> list[list[float]]:
        """Build max_goals x max_goals joint probability grid."""
        g = self.max_goals
        grid = []
        total = 0.0
        for h in range(g):
            row = []
            for a in range(g):
                p = (self._tau(h, a)
                     * self._poisson_pmf(math_mod, h, self.lambda_home)
                     * self._poisson_pmf(math_mod, a, self.lambda_away))
                p = max(p, 0.0)
                row.append(p)
                total += p
            grid.append(row)
        # Normalise
        if total > 0:
            grid = [[p / total for p in row] for row in grid]
        return grid

    @property
    def grid(self) -> list[list[float]]:
        """2-D list [home_goals][away_goals] of joint probabilities."""
        return self._grid

    @property
    def expected_home_goals(self) -> float:
        return sum(h * self._grid[h][a]
                   for h in range(self.max_goals)
                   for a in range(self.max_goals))

    @property
    def expected_away_goals(self) -> float:
        return sum(a * self._grid[h][a]
                   for h in range(self.max_goals)
                   for a in range(self.max_goals))

    def top_scorelines(self, n: int = 20) -> list[dict]:
        """Return top-n scorelines sorted by probability descending."""
        cells = []
        for h in range(self.max_goals):
            for a in range(self.max_goals):
                cells.append((self._grid[h][a], h, a))
        cells.sort(reverse=True)
        return [
            {"home_goals": h, "away_goals": a, "probability": round(p, 4)}
            for p, h, a in cells[:n]
        ]


# ---------------------------------------------------------------------------
# Market derivations from a DixonColesPMF
# ---------------------------------------------------------------------------

class MatchMarkets:
    """
    Derives every betting market probability from a DixonColesPMF grid.

    All returned probabilities are plain Python floats, rounded to 4 decimal places.
    All computations are pure cell-summation — no approximations.

    Usage:
        pmf = DixonColesPMF(lambda_home=1.48, lambda_away=1.23, rho=-0.07)
        markets = MatchMarkets(pmf)
        print(markets.moneyline())
        print(markets.all_markets())
    """

    DEFAULT_TOTAL_LINES = [
        0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0, 5.5, 6.0, 6.5
    ]
    DEFAULT_AH_LINES = [
        -3.0, -2.75, -2.5, -2.25, -2.0, -1.75, -1.5, -1.25, -1.0, -0.75,
        -0.5, -0.25, 0.0, 0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 1.75,
        2.0, 2.25, 2.5, 2.75, 3.0,
    ]
    DEFAULT_TEAM_TOTAL_LINES = [0.5, 1.5, 2.5]

    def __init__(self, pmf: "DixonColesPMF"):
        self.pmf = pmf
        self._g = pmf.grid
        self._n = pmf.max_goals

    def _r(self, v: float) -> float:
        """Round to 4 decimal places."""
        return round(v, 4)

    def moneyline(self) -> dict:
        hw = sum(self._g[h][a] for h in range(self._n) for a in range(self._n) if h > a)
        d  = sum(self._g[h][a] for h in range(self._n) for a in range(self._n) if h == a)
        aw = sum(self._g[h][a] for h in range(self._n) for a in range(self._n) if h < a)
        return {
            "home_win": self._r(hw),
            "draw":     self._r(d),
            "away_win": self._r(aw),
        }

    def btts(self) -> dict:
        yes = sum(self._g[h][a] for h in range(self._n) for a in range(self._n)
                  if h >= 1 and a >= 1)
        return {"btts_yes": self._r(yes), "btts_no": self._r(1.0 - yes)}

    def totals(self, lines: list[float] | None = None) -> dict:
        lines = lines or self.DEFAULT_TOTAL_LINES
        out = {}
        for line in lines:
            over  = sum(self._g[h][a] for h in range(self._n) for a in range(self._n)
                        if (h + a) > line)
            under = sum(self._g[h][a] for h in range(self._n) for a in range(self._n)
                        if (h + a) < line)
            label = str(line).replace(".", "_")
            out[f"over_{label}"]  = self._r(over)
            out[f"under_{label}"] = self._r(under)
        return out

    def team_totals(self, lines: list[float] | None = None) -> dict:
        lines = lines or self.DEFAULT_TEAM_TOTAL_LINES
        out = {}
        for line in lines:
            label = str(line).replace(".", "_")
            h_over  = sum(self._g[h][a] for h in range(self._n) for a in range(self._n) if h > line)
            a_over  = sum(self._g[h][a] for h in range(self._n) for a in range(self._n) if a > line)
            out[f"home_over_{label}"]  = self._r(h_over)
            out[f"home_under_{label}"] = self._r(1.0 - h_over)
            out[f"away_over_{label}"]  = self._r(a_over)
            out[f"away_under_{label}"] = self._r(1.0 - a_over)
        return out

    def asian_handicap(self, lines: list[float] | None = None) -> dict:
        """
        Asian handicap for home side.
        line > 0  → home team gives handicap (favoured)
        line < 0  → home team receives handicap (underdog)
        line is applied to home goals: effective margin = (h + line) - a
        """
        lines = lines or self.DEFAULT_AH_LINES
        out = {}
        for line in lines:
            hw = da = push = 0.0
            for h in range(self._n):
                for a in range(self._n):
                    effective = h - a + line   # home advantage after handicap
                    if effective > 0:
                        hw += self._g[h][a]
                    elif effective < 0:
                        da += self._g[h][a]
                    else:
                        push += self._g[h][a]
            label = str(line).replace(".", "_").replace("-", "m")
            out[f"asian_handicap_home_{label}"] = self._r(hw)
            out[f"asian_handicap_away_{label}"] = self._r(da)
            out[f"asian_handicap_push_{label}"] = self._r(push)
        return out

    def double_chance(self) -> dict:
        ml = self.moneyline()
        return {
            "double_chance_1x": self._r(ml["home_win"] + ml["draw"]),
            "double_chance_x2": self._r(ml["draw"] + ml["away_win"]),
            "double_chance_12": self._r(ml["home_win"] + ml["away_win"]),
        }

    def draw_no_bet(self) -> dict:
        ml = self.moneyline()
        denom = ml["home_win"] + ml["away_win"]
        if denom <= 0:
            return {"draw_no_bet_home": 0.5, "draw_no_bet_away": 0.5}
        return {
            "draw_no_bet_home": self._r(ml["home_win"] / denom),
            "draw_no_bet_away": self._r(ml["away_win"] / denom),
        }

    def win_to_nil(self) -> dict:
        wtn_home = sum(self._g[h][0] for h in range(1, self._n))
        wtn_away = sum(self._g[0][a] for a in range(1, self._n))
        return {
            "win_to_nil_home": self._r(wtn_home),
            "win_to_nil_away": self._r(wtn_away),
        }

    def clean_sheet(self) -> dict:
        cs_home = sum(self._g[h][0] for h in range(self._n))
        cs_away = sum(self._g[0][a] for a in range(self._n))
        return {
            "clean_sheet_home": self._r(cs_home),
            "clean_sheet_away": self._r(cs_away),
        }

    def expected_points(self) -> dict:
        ml = self.moneyline()
        return {
            "expected_points_home": self._r(3 * ml["home_win"] + ml["draw"]),
            "expected_points_away": self._r(3 * ml["away_win"] + ml["draw"]),
        }

    def winning_margin(self) -> dict:
        """P(home wins by exactly k goals) for k in -5..5 (negative = away win)."""
        out = {}
        for k in range(-5, 6):
            if k > 0:
                p = sum(self._g[h][a] for h in range(self._n) for a in range(self._n)
                        if h - a == k)
            elif k < 0:
                p = sum(self._g[h][a] for h in range(self._n) for a in range(self._n)
                        if h - a == k)
            else:
                p = sum(self._g[h][a] for h in range(self._n) for a in range(self._n)
                        if h == a)
            label = f"p{k}" if k >= 0 else f"m{abs(k)}"
            out[f"winning_margin_{label}"] = self._r(p)
        return out

    def correct_score(self, n: int = 20) -> dict:
        """Top-n exact scorelines as 'h-a' → probability."""
        cells = sorted(
            ((self._g[h][a], h, a)
             for h in range(self._n) for a in range(self._n)),
            reverse=True,
        )
        return {f"{h}-{a}": self._r(p) for p, h, a in cells[:n]}

    def all_markets(
        self,
        total_lines: list[float] | None = None,
        ah_lines: list[float] | None = None,
    ) -> dict:
        """Return every market as a single flat dict, all values 4 d.p."""
        result = {}
        result.update(self.moneyline())
        result.update(self.btts())
        result.update(self.double_chance())
        result.update(self.draw_no_bet())
        result.update(self.win_to_nil())
        result.update(self.clean_sheet())
        result.update(self.expected_points())
        result.update(self.totals(total_lines))
        result.update(self.team_totals())
        result.update(self.asian_handicap(ah_lines))
        result.update(self.winning_margin())
        result["expected_home_goals"] = self._r(self.pmf.expected_home_goals)
        result["expected_away_goals"] = self._r(self.pmf.expected_away_goals)
        result["correct_score_top_20"] = self.correct_score(20)
        return result
