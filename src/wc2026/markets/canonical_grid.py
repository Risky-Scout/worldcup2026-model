"""Canonical market derivation engine — single source of truth for all PMF-derived markets."""
from __future__ import annotations

import numpy as np

_DEFAULT_AH_LINES = [round(x * 0.25, 2) for x in range(-12, 13)]  # -3.0 to +3.0
_DEFAULT_TOTAL_LINES = [0.5, 1.0, 1.25, 1.5, 1.75, 2.0, 2.25, 2.5, 2.75, 3.0, 3.25, 3.5, 3.75, 4.0, 4.5, 5.0, 5.5, 6.0, 6.5]

class CanonicalGrid:
    def __init__(self, pmf: np.ndarray, home_lambda: float | None = None, away_lambda: float | None = None, rho: float | None = None, period: str = "match"):
        self.pmf = np.array(pmf, dtype=np.float64)
        total = self.pmf.sum()
        if total > 0:
            self.pmf = self.pmf / total
        self.home_lambda = home_lambda
        self.away_lambda = away_lambda
        self.rho = rho
        self.period = period
        self._h = self.pmf.shape[0]
        self._a = self.pmf.shape[1]

    def moneyline(self) -> dict:
        hw = float(np.sum(np.tril(self.pmf, -1)))
        aw = float(np.sum(np.triu(self.pmf, 1)))
        dr = float(np.trace(self.pmf))  # diagonal sum
        total = hw + aw + dr
        if total > 0:
            hw, dr, aw = hw/total, dr/total, aw/total
        return {"home_win": hw, "draw": dr, "away_win": aw}

    def btts(self) -> dict:
        yes = float(self.pmf[1:, 1:].sum())
        return {"btts_yes": yes, "btts_no": 1.0 - yes}

    def win_to_nil(self) -> dict:
        home = float(self.pmf[1:, 0].sum())
        away = float(self.pmf[0, 1:].sum())
        return {"win_to_nil_home": home, "win_to_nil_away": away}

    def clean_sheet(self) -> dict:
        home = float(self.pmf[:, 0].sum())   # home concedes 0
        away = float(self.pmf[0, :].sum())   # away concedes 0
        return {"clean_sheet_home": home, "clean_sheet_away": away}

    def double_chance(self) -> dict:
        ml = self.moneyline()
        return {
            "double_chance_1x": ml["home_win"] + ml["draw"],
            "double_chance_x2": ml["draw"] + ml["away_win"],
            "double_chance_12": ml["home_win"] + ml["away_win"],
        }

    def draw_no_bet(self) -> dict:
        ml = self.moneyline()
        denom = ml["home_win"] + ml["away_win"]
        if denom < 1e-12:
            return {"draw_no_bet_home": 0.5, "draw_no_bet_away": 0.5}
        return {
            "draw_no_bet_home": ml["home_win"] / denom,
            "draw_no_bet_away": ml["away_win"] / denom,
        }

    def expected_points(self) -> dict:
        ml = self.moneyline()
        return {
            "expected_points_home": 3.0 * ml["home_win"] + ml["draw"],
            "expected_points_away": 3.0 * ml["away_win"] + ml["draw"],
        }

    def totals(self, lines: list[float] | None = None) -> dict:
        if lines is None:
            lines = _DEFAULT_TOTAL_LINES
        result = {}
        h_idx, a_idx = np.arange(self._h), np.arange(self._a)
        score_totals = h_idx[:, None] + a_idx[None, :]  # (h, a) matrix of total goals
        for line in lines:
            # Quarter-line settlement: split into floor and ceiling half-lines
            floor_line = np.floor(line * 2) / 2
            ceil_line = floor_line + 0.5
            is_quarter = abs(line - floor_line - 0.25) < 1e-9 or abs(line - floor_line - 0.75) < 1e-9
            if is_quarter:
                # Half win/loss: average of two half-lines
                o_floor = float(np.sum(self.pmf[score_totals > floor_line]))
                o_ceil = float(np.sum(self.pmf[score_totals > ceil_line]))
                key = _fmt_line(line)
                result[f"over_{key}"] = (o_floor + o_ceil) / 2.0
                result[f"under_{key}"] = 1.0 - result[f"over_{key}"]
                result[f"push_{key}"] = 0.0
            else:
                o = float(np.sum(self.pmf[score_totals > line]))
                u = float(np.sum(self.pmf[score_totals < line]))
                p = 1.0 - o - u
                key = _fmt_line(line)
                result[f"over_{key}"] = o
                result[f"under_{key}"] = u
                result[f"push_{key}"] = p
        return result

    def team_totals(self, side: str, lines: list[float] | None = None) -> dict:
        if lines is None:
            lines = [0.5, 1.5, 2.5]
        result = {}
        if side == "home":
            goals = np.arange(self._h)
            marginal = self.pmf.sum(axis=1)  # sum over away
        else:
            goals = np.arange(self._a)
            marginal = self.pmf.sum(axis=0)
        for line in lines:
            o = float(np.sum(marginal[goals > line]))
            key = _fmt_line(line)
            result[f"{side}_over_{key}"] = o
            result[f"{side}_under_{key}"] = 1.0 - o
        return result

    def asian_handicap(self, lines: list[float] | None = None) -> dict:
        if lines is None:
            lines = _DEFAULT_AH_LINES
        result = {}
        h_idx = np.arange(self._h)
        a_idx = np.arange(self._a)
        goal_diff = h_idx[:, None] - a_idx[None, :]  # home - away
        for line in lines:
            # For home team at handicap `line`:
            # effective: home_goals - away_goals + line vs 0
            # line > 0 means home giving goals, line < 0 means home receiving
            # Quarter-line handling
            floor_line = np.floor(line * 2) / 2
            ceil_line = floor_line + 0.5
            is_quarter = abs(abs(line - floor_line) - 0.25) < 1e-9
            key = _fmt_ah_line(line)
            if is_quarter:
                # Split bet: half on floor, half on ceil
                hw_f = float(np.sum(self.pmf[goal_diff > -floor_line]))
                hw_c = float(np.sum(self.pmf[goal_diff > -ceil_line]))
                aw_f = float(np.sum(self.pmf[goal_diff < -floor_line]))
                aw_c = float(np.sum(self.pmf[goal_diff < -ceil_line]))
                push_f = 1.0 - hw_f - aw_f
                push_c = 1.0 - hw_c - aw_c
                result[f"asian_handicap_home_{key}"] = (hw_f + hw_c) / 2.0
                result[f"asian_handicap_away_{key}"] = (aw_f + aw_c) / 2.0
                result[f"asian_handicap_push_{key}"] = (push_f + push_c) / 2.0
            else:
                hw = float(np.sum(self.pmf[goal_diff > -line]))
                aw = float(np.sum(self.pmf[goal_diff < -line]))
                push = 1.0 - hw - aw
                result[f"asian_handicap_home_{key}"] = hw
                result[f"asian_handicap_away_{key}"] = aw
                result[f"asian_handicap_push_{key}"] = push
        return result

    def correct_score(self, top_n: int = 20) -> dict:
        flat = [(self.pmf[h, a], h, a) for h in range(self._h) for a in range(self._a)]
        flat.sort(reverse=True)
        return {f"{h}-{a}": float(p) for p, h, a in flat[:top_n]}

    def other_score_probability(self, top_n: int = 20) -> float:
        return 1.0 - sum(self.correct_score(top_n).values())

    def winning_margin(self, margins: list[int] | None = None) -> dict:
        if margins is None:
            margins = list(range(-5, 6))
        h_idx = np.arange(self._h)
        a_idx = np.arange(self._a)
        gd = h_idx[:, None] - a_idx[None, :]
        return {f"margin_{m}": float(np.sum(self.pmf[gd == m])) for m in margins}

    def all_markets(self, ah_lines: list[float] | None = None, total_lines: list[float] | None = None) -> dict:
        result = {}
        result.update(self.moneyline())
        result.update(self.btts())
        result.update(self.win_to_nil())
        result.update(self.clean_sheet())
        result.update(self.double_chance())
        result.update(self.draw_no_bet())
        result.update(self.expected_points())
        result.update(self.totals(total_lines))
        result.update(self.team_totals("home"))
        result.update(self.team_totals("away"))
        result.update(self.asian_handicap(ah_lines))
        result["correct_score_top_20"] = self.correct_score(20)
        result["other_score_probability"] = self.other_score_probability(20)
        result.update(self.winning_margin())
        return result


def _fmt_line(line: float) -> str:
    """Format a line value for use as a dict key, e.g. 2.5 -> '2_5', 2.25 -> '2_25'."""
    s = f"{line:.2f}".rstrip("0").rstrip(".")
    return s.replace(".", "_").replace("-", "neg")

def _fmt_ah_line(line: float) -> str:
    """Format AH line preserving sign, e.g. -1.5 -> 'neg1_5', 1.5 -> '1_5', 0.0 -> '0'."""
    if line < 0:
        return f"neg{_fmt_line(abs(line))}"
    return _fmt_line(line)
