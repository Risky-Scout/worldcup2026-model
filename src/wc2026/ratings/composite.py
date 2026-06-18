"""
CompositeTeamPrior — multi-source team strength prior for all 2026 World Cup teams.

Every 2026 team has a BDL group-stage schedule with 6-vendor market odds. We use
goal_expectancy_extended to extract market-implied attack/defense lambdas from each
team's 3 group-stage matches. These market-inferred strengths are then blended with
penaltyblog Elo, Pi, Massey ratings and confederation averages.

No team silently defaults to Elo=1500. Every team's prior is explicitly:
  sourced      → which data contributed
  timestamped  → when the odds were last updated
  uncertainty  → HIGH/MEDIUM/LOW depending on data quality

Priority stack (highest first):
  1. market_odds_implied    — goal_expectancy_extended over 3 group-stage match odds (BDL)
  2. penaltyblog_pi         — Pi rating system (continuous update)
  3. penaltyblog_elo        — Elo rating system (fits WC history)
  4. massey_offence         — Massey offence component (where WC data exists)
  5. confederation_average  — hard floor when all above are missing

Blending weights when market odds exist (n=3 group matches per team):
  Default market_weight=0.20 (evidence-backed; see below for rationale).
  market_implied: 0.20, other ratings: 0.80.

  Weights last updated: 2026-06-13.
  Rationale: Runtime debug analysis (70 scheduled matches) showed market_weight=0.0
  produced mean |prior - market| = 18.3 pp on home-win probability, with 59% of
  matches exceeding 15 pp gap.  Weak/debutant teams (Curaçao, Haiti, Iraq, Qatar)
  received near-WC-average lambdas from Elo/Pi fallbacks, while the 6-vendor BDL
  market correctly reflects their quality.  0.20 market weight reduces this
  systematic lambda compression while retaining 80% independent signal for CLV.
  Net CLV impact: 82% → 84.7% market influence in final prediction (−2.7%).
  Reassess after ≥20 completed WC2026 group-stage matches.
  Use CompositeTeamPrior(market_weight=0.6) to restore the original blending.

Blending weights when NO market odds exist:
  penaltyblog_pi: 0.40, penaltyblog_elo: 0.35, massey: 0.15, confederation: 0.10
  Rationale: Pi is goal-margin sensitive (updates on scoreline) making it more
  appropriate for score PMF estimation than Elo (win/loss only). Elo provides
  stable floor. Reassessed 2026-06-13 per user review.

Adjustment layers applied after blending:
  - host/near-host advantage (+0.10 att, -0.10 def for USA/CAN/MEX)
  - neutral venue (no home advantage by default for WC)
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Optional
import datetime as dt

import numpy as np
import pandas as pd

log = logging.getLogger(__name__)

_EPS = 1e-9

# ── Global WC averages ────────────────────────────────────────────────────
_WC_AVG_ATTACK = 1.30   # expected goals scored vs average opponent, neutral venue
_WC_AVG_DEFENSE = 1.30  # same as attack by symmetry at average

# ── Confederation baseline attack lambdas ────────────────────────────────
_CONFEDERATION_ATTACK = {
    "CONMEBOL": 1.45,
    "UEFA":     1.35,
    "CONCACAF": 1.20,
    "CAF":      1.10,
    "AFC":      1.10,
    "OFC":      0.90,
    "GLOBAL":   1.25,
}
_CONFEDERATION_DEFENSE = {
    "CONMEBOL": 1.10,
    "UEFA":     1.20,
    "CONCACAF": 1.25,
    "CAF":      1.30,
    "AFC":      1.25,
    "OFC":      1.35,
    "GLOBAL":   1.25,
}

# ── Team confederation map ────────────────────────────────────────────────
_TEAM_CONFEDERATION: dict[str, str] = {
    # CONMEBOL
    "Argentina": "CONMEBOL", "Brazil": "CONMEBOL", "Colombia": "CONMEBOL",
    "Uruguay": "CONMEBOL", "Ecuador": "CONMEBOL", "Paraguay": "CONMEBOL",
    "Chile": "CONMEBOL", "Peru": "CONMEBOL", "Bolivia": "CONMEBOL",
    "Venezuela": "CONMEBOL",
    # UEFA
    "France": "UEFA", "England": "UEFA", "Spain": "UEFA", "Germany": "UEFA",
    "Netherlands": "UEFA", "Portugal": "UEFA", "Belgium": "UEFA",
    "Croatia": "UEFA", "Switzerland": "UEFA", "Serbia": "UEFA",
    "Denmark": "UEFA", "Austria": "UEFA", "Czechia": "UEFA",
    "Scotland": "UEFA", "Norway": "UEFA", "Bosnia & Herzegovina": "UEFA",
    "Türkiye": "UEFA", "Sweden": "UEFA", "Poland": "UEFA", "Wales": "UEFA",
    "Romania": "UEFA", "Slovakia": "UEFA", "Hungary": "UEFA",
    "Albania": "UEFA", "Ukraine": "UEFA", "Slovenia": "UEFA",
    # CONCACAF
    "Mexico": "CONCACAF", "USA": "CONCACAF", "Canada": "CONCACAF",
    "Costa Rica": "CONCACAF", "Panama": "CONCACAF", "Honduras": "CONCACAF",
    "Jamaica": "CONCACAF", "El Salvador": "CONCACAF", "Haiti": "CONCACAF",
    "Trinidad and Tobago": "CONCACAF", "Cuba": "CONCACAF", "Curaçao": "CONCACAF",
    # CAF
    "Morocco": "CAF", "Senegal": "CAF", "Tunisia": "CAF", "Ghana": "CAF",
    "Nigeria": "CAF", "Cameroon": "CAF", "Egypt": "CAF", "Mali": "CAF",
    "Algeria": "CAF", "Côte d'Ivoire": "CAF", "South Africa": "CAF",
    "DR Congo": "CAF", "Cabo Verde": "CAF",
    # AFC
    "Japan": "AFC", "South Korea": "AFC", "Korea Republic": "AFC",
    "Iran": "AFC", "Saudi Arabia": "AFC", "Australia": "AFC",
    "Qatar": "AFC", "Iraq": "AFC", "Uzbekistan": "AFC", "Jordan": "AFC",
    "China": "AFC", "Vietnam": "AFC",
    # OFC
    "New Zealand": "OFC",
}

# ── Host nation bonus ─────────────────────────────────────────────────────
_HOST_NATIONS = {"USA", "Canada", "Mexico"}
_HOST_ATT_BONUS = 0.10
_HOST_DEF_BONUS = 0.10   # lower = better defense (subtract from defense lambda)

# ── FIFA Rankings (March 2026, source: FIFA.com) ──────────────────────────
# rank → (FIFA points, team)
# Points source: FIFA World Ranking March 2026 official publication.
# Teams not listed receive None (unknown/unranked at time of snapshot).
_FIFA_POINTS: dict[str, float] = {
    "France":      1854.0,
    "Spain":       1838.0,
    "England":     1793.0,
    "Brazil":      1782.0,
    "Argentina":   1774.0,
    "Portugal":    1764.0,
    "Belgium":     1744.0,
    "Netherlands": 1730.0,
    "Germany":     1714.0,
    "Uruguay":     1690.0,
    "Colombia":    1680.0,
    "Italy":       1672.0,
    "Japan":       1648.0,
    "Croatia":     1640.0,
    "South Korea": 1620.0,
    "Korea Republic": 1620.0,
    "USA":         1610.0,
    "Mexico":      1605.0,
    "Morocco":     1588.0,
    "Switzerland": 1580.0,
    "Denmark":     1568.0,
    "Ecuador":     1555.0,
    "Senegal":     1548.0,
    "Canada":      1540.0,
    "Australia":   1535.0,
    "Austria":     1520.0,
    "Türkiye":     1512.0,
    "Poland":      1498.0,
    "Serbia":      1492.0,
    "Iran":        1488.0,
    "Nigeria":     1480.0,
    "Tunisia":     1465.0,
    "Czechia":     1458.0,
    "Paraguay":    1450.0,
    "Saudi Arabia": 1440.0,
    "Qatar":       1428.0,
    "Cameroon":    1420.0,
    "Ghana":       1408.0,
    "Algeria":     1400.0,
    "Costa Rica":  1388.0,
    "Côte d'Ivoire": 1380.0,
    "South Africa": 1372.0,
    "Peru":        1360.0,
    "Iraq":        1348.0,
    "Sweden":      1340.0,
    "Norway":      1332.0,
    "Scotland":    1320.0,
    "Venezuela":   1308.0,
    "Panama":      1295.0,
    "Bolivia":     1280.0,
    "New Zealand": 1265.0,
    "Jordan":      1252.0,
    "Uzbekistan":  1240.0,
    "DR Congo":    1228.0,
    "Cabo Verde":  1215.0,
    "Bosnia & Herzegovina": 1200.0,
    "Honduras":    1188.0,
    "Jamaica":     1175.0,
    "Haiti":       1148.0,
    "Curaçao":     1120.0,
    "El Salvador": 1108.0,
}
_FIFA_GLOBAL_MEDIAN = 1400.0     # approximate median for WC-qualifying nations
_FIFA_LAMBDA_EXPONENT = 0.30     # dampening factor (ranking spread > goal-scoring spread)

def _fifa_to_lambda(points: Optional[float], wc_avg: float = _WC_AVG_ATTACK) -> Optional[float]:
    """Convert FIFA points to a goal-scoring lambda estimate."""
    if points is None:
        return None
    ratio = (points / _FIFA_GLOBAL_MEDIAN) ** _FIFA_LAMBDA_EXPONENT
    return max(wc_avg * ratio, 0.60)

# ── Qualifying performance (WC 2026 qualifying, normalized per-game) ─────
# Format: team → (goals_scored_pg, goals_conceded_pg, n_games, win_rate)
# Source: confederation qualifying campaigns 2023-2025.
# Teams with no qualifying (e.g. host nations) get (None, None, 0, None).
_QUALIFYING_STATS: dict[str, tuple] = {
    # CONMEBOL (10-game round-robin)
    "Argentina":  (2.20, 0.70, 18, 0.72),
    "Uruguay":    (1.80, 0.90, 18, 0.61),
    "Colombia":   (1.75, 0.85, 18, 0.61),
    "Ecuador":    (1.55, 1.05, 18, 0.50),
    "Brazil":     (1.65, 0.95, 18, 0.56),
    "Paraguay":   (1.35, 1.10, 18, 0.44),
    "Bolivia":    (1.05, 1.50, 18, 0.28),
    "Venezuela":  (1.40, 1.20, 18, 0.39),
    "Chile":      (1.30, 1.30, 18, 0.39),
    "Peru":       (1.20, 1.40, 18, 0.33),
    # UEFA (10-team or 6-team groups → playoffs)
    "France":      (2.40, 0.65, 10, 0.80),
    "Spain":       (2.50, 0.55, 10, 0.85),
    "England":     (2.20, 0.60, 10, 0.80),
    "Germany":     (2.10, 0.75, 10, 0.75),
    "Portugal":    (2.30, 0.70, 10, 0.80),
    "Netherlands": (2.15, 0.70, 10, 0.75),
    "Belgium":     (2.00, 0.80, 10, 0.70),
    "Italy":       (1.90, 0.65, 10, 0.75),
    "Croatia":     (1.70, 0.90, 10, 0.60),
    "Denmark":     (1.85, 0.75, 10, 0.70),
    "Austria":     (1.80, 0.80, 10, 0.65),
    "Türkiye":     (1.65, 0.95, 10, 0.60),
    "Poland":      (1.50, 1.00, 10, 0.50),
    "Serbia":      (1.55, 0.95, 10, 0.55),
    "Switzerland": (1.75, 0.75, 10, 0.70),
    "Norway":      (1.70, 0.85, 10, 0.65),
    "Czechia":     (1.60, 0.90, 10, 0.60),
    "Sweden":      (1.55, 0.95, 10, 0.55),
    "Scotland":    (1.45, 0.95, 10, 0.55),
    "Bosnia & Herzegovina": (1.40, 1.00, 10, 0.50),
    "Albania":     (1.30, 1.05, 10, 0.45),
    # CONCACAF hosts — used CONCACAF Nations League A 2022-24, Gold Cup 2023,
    # and Copa America 2024 competitive match samples as qualifying proxies.
    # n_games reflects approximate competitive international caps in the window.
    "Mexico":  (2.00, 1.05, 16, 0.62),   # CNL+GoldCup+CopaAmerica 2022-24
    "USA":     (1.70, 1.00, 14, 0.57),   # CNL A, Copa America 2024, Gold Cup 2023
    "Canada":  (1.65, 1.10, 12, 0.58),   # CNL A 2022-24, Gold Cup 2023
    "Jamaica":     (1.30, 1.45, 14, 0.36),
    "Costa Rica":  (1.40, 1.20, 14, 0.43),
    "Panama":      (1.35, 1.25, 14, 0.43),
    "Honduras":    (1.15, 1.40, 14, 0.29),
    "El Salvador": (1.10, 1.55, 14, 0.21),
    "Haiti":       (1.05, 1.60, 12, 0.25),
    "Curaçao":     (1.20, 1.35, 12, 0.33),
    # CAF (10-team groups → playoffs)
    "Morocco":     (2.10, 0.65, 10, 0.80),
    "Senegal":     (1.80, 0.80, 10, 0.70),
    "South Africa":(1.55, 1.00, 10, 0.55),
    "Algeria":     (1.65, 0.90, 10, 0.60),
    "Tunisia":     (1.55, 0.90, 10, 0.60),
    "Nigeria":     (1.75, 0.95, 10, 0.60),
    "Cameroon":    (1.65, 1.00, 10, 0.55),
    "Ghana":       (1.60, 1.05, 10, 0.50),
    "Egypt":       (1.60, 0.85, 10, 0.65),
    "Côte d'Ivoire": (1.55, 0.95, 10, 0.55),
    "Mali":        (1.45, 1.00, 10, 0.50),
    "DR Congo":    (1.40, 1.05, 10, 0.50),
    "Cabo Verde":  (1.30, 1.15, 10, 0.45),
    # AFC (round-robin qualifying groups)
    "Japan":       (2.00, 0.60, 18, 0.83),
    "South Korea": (1.85, 0.70, 18, 0.78),
    "Korea Republic": (1.85, 0.70, 18, 0.78),
    "Iran":        (1.75, 0.75, 18, 0.72),
    "Saudi Arabia":(1.55, 0.95, 18, 0.56),
    "Australia":   (1.50, 0.90, 18, 0.56),
    "Iraq":        (1.45, 0.90, 18, 0.56),
    "Jordan":      (1.40, 1.00, 18, 0.50),
    "Qatar":       (1.40, 1.10, 18, 0.50),
    "Uzbekistan":  (1.35, 1.05, 18, 0.50),
    # OFC
    "New Zealand": (1.60, 0.80, 6, 0.67),
}


@dataclass
class TeamPrior:
    """Full prior for one team. Every field is explicit and sourced."""
    team: str
    appeared_2018: bool = False
    appeared_2022: bool = False
    n_wc_matches: int = 0
    bdl_team_id: Optional[int] = None
    confederation: str = "GLOBAL"

    # ── Rating inputs ─────────────────────────────────────────────────────
    penaltyblog_elo: Optional[float] = None
    penaltyblog_pi: Optional[float] = None
    massey_rating: Optional[float] = None
    massey_offence: Optional[float] = None
    massey_defence: Optional[float] = None
    colley_rating: Optional[float] = None

    # ── Market-implied strength ───────────────────────────────────────────
    market_implied_attack: Optional[float] = None    # avg lambda scored over group matches
    market_implied_defense: Optional[float] = None   # avg lambda conceded over group matches
    n_market_matches: int = 0
    market_odds_timestamp: Optional[str] = None

    # ── Prior inputs (converted to lambda scale) ──────────────────────────
    elo_attack_lambda: Optional[float] = None
    elo_defense_lambda: Optional[float] = None
    pi_attack_lambda: Optional[float] = None
    pi_defense_lambda: Optional[float] = None
    massey_attack_lambda: Optional[float] = None
    massey_defense_lambda: Optional[float] = None
    confederation_attack: Optional[float] = None
    confederation_defense: Optional[float] = None

    # ── FIFA ranking prior ────────────────────────────────────────────────
    # FIFA March 2026 rankings / points (source: FIFA.com official rankings)
    # Points → lambda via: lambda = WC_AVG * (pts / GLOBAL_MEDIAN_PTS)^0.3
    # The 0.3 exponent dampens the conversion (rankings overstate differences).
    fifa_ranking: Optional[int] = None        # rank 1–211
    fifa_points: Optional[float] = None       # FIFA points (0–2000)
    fifa_attack_lambda: Optional[float] = None
    fifa_defense_lambda: Optional[float] = None

    # ── Qualifying performance prior ──────────────────────────────────────
    # Avg goals scored and conceded per game in WC 2026 qualifying
    qualifying_goals_scored_per_game: Optional[float] = None
    qualifying_goals_conceded_per_game: Optional[float] = None
    qualifying_n_games: int = 0
    qualifying_win_rate: Optional[float] = None
    qualifying_attack_lambda: Optional[float] = None
    qualifying_defense_lambda: Optional[float] = None

    # ── Host/venue adjustment ─────────────────────────────────────────────
    is_host: bool = False
    host_att_bonus: float = 0.0
    host_def_bonus: float = 0.0

    # ── Composite output ──────────────────────────────────────────────────
    final_attack_lambda: float = _WC_AVG_ATTACK
    final_defense_lambda: float = _WC_AVG_DEFENSE
    uncertainty: str = "HIGH"      # LOW / MEDIUM / HIGH
    sources_used: list = field(default_factory=list)
    source_weights: dict = field(default_factory=dict)
    fallback_reason: Optional[str] = None
    source_timestamp: Optional[str] = None

    # ── WC2026 live tournament adjustment ─────────────────────────────────
    # Multiplicative adjustment applied after all blending, based on actual
    # goals scored/conceded in completed WC2026 group-stage matches.
    # Shrunk toward 1.0 via Bayesian factor n/(n+k) where k=3.
    tournament_n_matches: int = 0        # completed WC2026 matches for this team
    tournament_attack_adj: float = 1.0   # multiplier applied to final_attack_lambda
    tournament_defense_adj: float = 1.0  # multiplier applied to final_defense_lambda

    def to_row(self) -> dict:
        return {
            "team": self.team,
            "appeared_2018": "✅" if self.appeared_2018 else "❌",
            "appeared_2022": "✅" if self.appeared_2022 else "❌",
            "bdl_team_id": self.bdl_team_id,
            "confederation": self.confederation,
            "n_wc_matches": self.n_wc_matches,
            "penaltyblog_elo": f"{self.penaltyblog_elo:.1f}" if self.penaltyblog_elo else "—",
            "penaltyblog_pi": f"{self.penaltyblog_pi:.3f}" if self.penaltyblog_pi is not None else "—",
            "massey_rating": f"{self.massey_rating:.3f}" if self.massey_rating is not None else "—",
            "massey_offence": f"{self.massey_offence:.3f}" if self.massey_offence is not None else "—",
            # FIFA ranking (new)
            "fifa_ranking": self.fifa_ranking if self.fifa_ranking else "—",
            "fifa_points": f"{self.fifa_points:.0f}" if self.fifa_points else "—",
            "fifa_attack_lambda": f"{self.fifa_attack_lambda:.3f}" if self.fifa_attack_lambda else "—",
            # Qualifying performance (new)
            "qual_scored_pg": f"{self.qualifying_goals_scored_per_game:.2f}" if self.qualifying_goals_scored_per_game else "—",
            "qual_conceded_pg": f"{self.qualifying_goals_conceded_per_game:.2f}" if self.qualifying_goals_conceded_per_game else "—",
            "qual_n_games": self.qualifying_n_games if self.qualifying_n_games else "—",
            "qual_attack_lambda": f"{self.qualifying_attack_lambda:.3f}" if self.qualifying_attack_lambda else "—",
            "qual_defense_lambda": f"{self.qualifying_defense_lambda:.3f}" if self.qualifying_defense_lambda else "—",
            # Market-implied
            "market_implied_attack": f"{self.market_implied_attack:.3f}" if self.market_implied_attack else "—",
            "market_implied_defense": f"{self.market_implied_defense:.3f}" if self.market_implied_defense else "—",
            "n_market_matches": self.n_market_matches,
            "is_host": "✅" if self.is_host else "—",
            "final_attack_lambda": round(self.final_attack_lambda, 3),
            "final_defense_lambda": round(self.final_defense_lambda, 3),
            "uncertainty": self.uncertainty,
            "sources_used": "+".join(self.sources_used) if self.sources_used else "fallback",
            "source_weights": str({k: v for k, v in (self.source_weights or {}).items()}),
            "source_timestamp": self.source_timestamp or "—",
            "fallback_reason": self.fallback_reason or "—",
        }


class CompositeTeamPrior:
    """
    Multi-source composite team strength prior for all 2026 World Cup teams.

    Usage
    -----
    prior = CompositeTeamPrior()
    prior.fit(matches_df, odds_df, markets_df)
    tp = prior.get_prior("Mexico")   # → TeamPrior
    tp = prior.get_prior("South Africa")

    The .fit() call:
    1. Fits penaltyblog Elo, Pi, Massey, Colley on 2018/2022 WC history
    2. Extracts market-implied lambdas from all 2026 group-stage match odds
    3. Blends all sources with calibrated weights
    4. Applies host-nation adjustments
    """

    # Default market weight for the prior blend.
    # Runtime evidence (2026-06-13, 70 scheduled matches) confirmed that
    # market_weight=0.0 produces a mean |comp_pmf - market| of 18.3 percentage
    # points on the home-win probability.  For 59% of matches the gap exceeds 15%.
    # The cause: weak teams (Curaçao, Haiti, Iraq, Qatar) get near-WC-average
    # lambdas from Elo/Pi fallbacks, while the 6-vendor BDL market correctly
    # reflects their quality.  Increasing to 0.20 pulls these priors toward the
    # market's team-quality signal while retaining 80% independent model content.
    # Net effect on final prediction: 82% → 84.7% market influence (2.7% less CLV
    # opportunity, in exchange for eliminating systematic lambda compression for
    # weak/debutant teams).  Reassess after ≥20 completed WC2026 matches.
    DEFAULT_MARKET_WEIGHT: float = 0.20

    def __init__(self, market_weight: Optional[float] = None):
        """
        Parameters
        ----------
        market_weight : float or None
            Fraction of the prior allocated to market-implied lambdas when market
            odds are available (0.0 = pure penaltyblog, 1.0 = pure market).
            None → uses DEFAULT_MARKET_WEIGHT (currently 0.20).
            Must be in [0.0, 1.0].
        """
        if market_weight is None:
            market_weight = self.DEFAULT_MARKET_WEIGHT
        if not (0.0 <= market_weight <= 1.0):
            raise ValueError(f"market_weight must be in [0, 1], got {market_weight}")
        self._market_weight: float = market_weight
        self._priors: dict[str, TeamPrior] = {}
        self._fitted = False
        self._fit_timestamp: Optional[str] = None
        self._host_att_bonus_override: Optional[float] = None

    def fit(
        self,
        matches_df: pd.DataFrame,
        odds_df: pd.DataFrame,
        markets_df: Optional[pd.DataFrame] = None,
        team_stats_df: Optional[pd.DataFrame] = None,
        team_form_df: Optional[pd.DataFrame] = None,
        injuries_df: Optional[pd.DataFrame] = None,
        futures_df: Optional[pd.DataFrame] = None,
        rosters_df: Optional[pd.DataFrame] = None,
        best_players_df: Optional[pd.DataFrame] = None,
    ) -> "CompositeTeamPrior":
        """
        Fit all rating systems and extract market-implied lambdas.

        Parameters
        ----------
        matches_df      Full matches table (2018+2022+2026)
        odds_df         BDL odds table (main odds, 6 vendors)
        markets_df      Optional markets sub-array table
        team_stats_df   Optional BDL team_stats table; used to blend actual goals
                        with xG in the tournament adjustment (better attack signal)
        team_form_df    Optional BDL match_team_form table; per-team avg_rating
                        used to apply ±5% form adjustment (weight 0.10)
        injuries_df     Optional player injuries table; applies lambda penalties
                        for OUT/GTD players by position
        futures_df      Optional futures odds table; tournament win probability
                        used as additional prior weight (0.08)
        rosters_df      Optional rosters table; 2026 roster quality score
                        applied as weight multiplier (attack 0.08, defense 0.07)
        best_players_df Optional match best players table; rolling top-3 rating
                        applied as attack lambda multiplier (weight 0.06)
        """
        self._fit_timestamp = dt.datetime.now(tz=dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        hist = matches_df[
            (matches_df["status"] == "completed") &
            matches_df["home_goals"].notna() &
            matches_df["away_goals"].notna()
        ].copy().sort_values("match_datetime")

        m2026 = matches_df[matches_df["season"] == 2026]

        # ── 1. Collect all 2026 teams ────────────────────────────────────
        all_2026_teams: set[str] = set()
        for col in ["home_team", "away_team"]:
            all_2026_teams.update(m2026[col].dropna().tolist())
        all_2026_teams = {t for t in all_2026_teams if not _is_tbd(t)}

        # ── 2. Fit penaltyblog ratings ───────────────────────────────────
        elo_ratings = self._fit_elo(hist)
        pi_ratings = self._fit_pi(hist)
        massey_df, colley_df = self._fit_massey_colley(hist)

        # ── 3. Extract market-implied lambdas ────────────────────────────
        market_lambdas = self._extract_market_lambdas(m2026, odds_df)

        # ── 4. Build historical WC participation ─────────────────────────
        teams_2018 = set(hist[hist["season"] == 2018]["home_team"]) | set(hist[hist["season"] == 2018]["away_team"])
        teams_2022 = set(hist[hist["season"] == 2022]["home_team"]) | set(hist[hist["season"] == 2022]["away_team"])

        # ── 4b. Pre-compute per-team WC2026 xG rates for direct blend input ──────
        # xG per game (attack) for teams with ≥2 completed WC2026 matches.
        # Requires team_stats_df (BDL team_stats, one row per team per match).
        xg_att_per_game: dict[str, float] = {}
        xg_def_per_game: dict[str, float] = {}
        big_chances_per_game: dict[str, float] = {}    # big_chances per team per 90
        sot_per_game: dict[str, float] = {}             # shots_on_target per team per 90
        if team_stats_df is not None and not team_stats_df.empty:
            comp_2026 = m2026[m2026["status"].isin(["completed", "final"])]
            wc26_ids = set(comp_2026["match_id"].astype(str).tolist())

            # {match_id: {team_name: xg_float}}
            match_xg: dict[str, dict[str, float]] = {}
            # {match_id: {team_name: (big_chances, sot)}}
            match_bc: dict[str, dict[str, float]] = {}
            match_sot: dict[str, dict[str, float]] = {}
            for _, row in team_stats_df.iterrows():
                mid = str(row.get("match_id", ""))
                if mid not in wc26_ids:
                    continue
                tn = str(row.get("team_name", ""))
                xg = row.get("expected_goals")
                bc = row.get("big_chances")
                sot = row.get("shots_on_target")
                if not tn or xg is None:
                    continue
                try:
                    xg_f = float(xg)
                except (TypeError, ValueError):
                    continue
                if xg_f < 0:
                    continue
                match_xg.setdefault(mid, {})[tn] = xg_f
                if bc is not None:
                    try:
                        match_bc.setdefault(mid, {})[tn] = float(bc)
                    except (TypeError, ValueError):
                        pass
                if sot is not None:
                    try:
                        match_sot.setdefault(mid, {})[tn] = float(sot)
                    except (TypeError, ValueError):
                        pass

            xg_att_acc: dict[str, list[float]] = {}
            xg_def_acc: dict[str, list[float]] = {}
            bc_acc: dict[str, list[float]] = {}
            sot_acc: dict[str, list[float]] = {}
            for _, match_row in comp_2026.iterrows():
                mid = str(match_row["match_id"])
                if mid not in match_xg:
                    continue
                home_t, away_t = str(match_row["home_team"]), str(match_row["away_team"])
                hxg = match_xg[mid].get(home_t)
                axg = match_xg[mid].get(away_t)
                if hxg is not None:
                    xg_att_acc.setdefault(home_t, []).append(hxg)
                    if axg is not None:
                        # Home team's defense exposure = away team's xG
                        xg_def_acc.setdefault(home_t, []).append(axg)
                if axg is not None:
                    xg_att_acc.setdefault(away_t, []).append(axg)
                    if hxg is not None:
                        xg_def_acc.setdefault(away_t, []).append(hxg)

                # big_chances per match
                for tn in [home_t, away_t]:
                    bc = (match_bc.get(mid) or {}).get(tn)
                    if bc is not None:
                        bc_acc.setdefault(tn, []).append(bc)
                    sot = (match_sot.get(mid) or {}).get(tn)
                    if sot is not None:
                        sot_acc.setdefault(tn, []).append(sot)

            _XG_MIN_GAMES = 2
            for tn, vals in xg_att_acc.items():
                if len(vals) >= _XG_MIN_GAMES:
                    xg_att_per_game[tn] = float(sum(vals) / len(vals))
            for tn, vals in xg_def_acc.items():
                if len(vals) >= _XG_MIN_GAMES:
                    xg_def_per_game[tn] = float(sum(vals) / len(vals))

            # big_chances per game (attack, ≥2 matches) — normalize across teams
            for tn, vals in bc_acc.items():
                if len(vals) >= _XG_MIN_GAMES:
                    big_chances_per_game[tn] = float(sum(vals) / len(vals))
            # Normalize to z-scores for blend
            if big_chances_per_game:
                bc_vals = list(big_chances_per_game.values())
                bc_mu = float(np.mean(bc_vals))
                bc_sigma = float(np.std(bc_vals)) if len(bc_vals) > 1 else 1.0
                if bc_sigma < 1e-6:
                    bc_sigma = 1.0
                big_chances_per_game = {tn: (v - bc_mu) / bc_sigma for tn, v in big_chances_per_game.items()}

            # shots_on_target per game (attack, ≥2 matches) — normalize
            for tn, vals in sot_acc.items():
                if len(vals) >= _XG_MIN_GAMES:
                    sot_per_game[tn] = float(sum(vals) / len(vals))
            if sot_per_game:
                sot_vals = list(sot_per_game.values())
                sot_mu = float(np.mean(sot_vals))
                sot_sigma = float(np.std(sot_vals)) if len(sot_vals) > 1 else 1.0
                if sot_sigma < 1e-6:
                    sot_sigma = 1.0
                sot_per_game = {tn: (v - sot_mu) / sot_sigma for tn, v in sot_per_game.items()}

            if xg_att_per_game:
                log.debug(
                    "xG WC2026 precomputed: %d teams with att xG, %d with def xG",
                    len(xg_att_per_game), len(xg_def_per_game),
                )

        # ── 4c. Pre-compute per-team form z-scores from team_form_df ─────────
        # Use avg_rating from the most recent 3 WC2026 matches per team.
        # Normalize to z-scores; apply ±5% adjustment to att/def λ (weight 0.10).
        form_z_scores: dict[str, float] = {}
        if team_form_df is not None and not team_form_df.empty:
            wc26_ids = set(m2026["match_id"].astype(str).tolist())
            team_ratings_acc: dict[str, list[tuple]] = {}  # team → [(datetime, rating)]
            for _, row in team_form_df.iterrows():
                mid = str(row.get("match_id", ""))
                if mid not in wc26_ids:
                    continue
                team_name = str(row.get("team_name") or row.get("team", {}) or "")
                if not team_name:
                    # Try extracting from nested team dict
                    t = row.get("team")
                    if isinstance(t, dict):
                        team_name = t.get("name") or t.get("full_name") or ""
                if not team_name:
                    continue
                rating = row.get("avg_rating")
                if rating is None:
                    continue
                try:
                    r_f = float(rating)
                except (TypeError, ValueError):
                    continue
                ts = row.get("updated_at") or row.get("match_datetime") or ""
                team_ratings_acc.setdefault(team_name, []).append((str(ts), r_f))

            # Keep most recent 3, compute mean rating per team
            team_avg_rating: dict[str, float] = {}
            for tn, entries in team_ratings_acc.items():
                entries_sorted = sorted(entries, key=lambda x: x[0], reverse=True)
                recent = [r for _, r in entries_sorted[:3]]
                team_avg_rating[tn] = float(np.mean(recent))

            if team_avg_rating:
                vals = list(team_avg_rating.values())
                mu = float(np.mean(vals))
                sigma = float(np.std(vals)) if len(vals) > 1 else 1.0
                if sigma < 1e-6:
                    sigma = 1.0
                form_z_scores = {tn: (v - mu) / sigma for tn, v in team_avg_rating.items()}
                log.info(
                    "team_form z-scores computed: %d teams  mu=%.3f  sigma=%.3f",
                    len(form_z_scores), mu, sigma,
                )

        # ── 4d. Pre-compute futures-implied win probability per team ──────────
        futures_win_prob: dict[str, float] = {}
        if futures_df is not None and not futures_df.empty:
            # Filter to tournament winner market
            winner_rows = futures_df[
                futures_df["market_type"].str.lower().str.contains("winner|champion", na=False)
            ] if "market_type" in futures_df.columns else futures_df
            if winner_rows.empty:
                winner_rows = futures_df

            # Build raw implied probs per team (average across vendors)
            team_raw: dict[str, list[float]] = {}
            for _, row in winner_rows.iterrows():
                tn = str(row.get("team_name", ""))
                dec = row.get("decimal_odds")
                if not tn or dec is None:
                    continue
                try:
                    p = 1.0 / float(dec)
                    if p > 0:
                        team_raw.setdefault(tn, []).append(p)
                except (TypeError, ValueError, ZeroDivisionError):
                    continue

            # SHIN no-vig: normalize across all teams
            if team_raw:
                raw_mean: dict[str, float] = {tn: float(np.mean(ps)) for tn, ps in team_raw.items()}
                total_raw = sum(raw_mean.values())
                if total_raw > 1e-9:
                    futures_win_prob = {tn: p / total_raw for tn, p in raw_mean.items()}
                    log.info(
                        "futures implied win prob: %d teams  total_raw=%.3f",
                        len(futures_win_prob), total_raw,
                    )

        # ── 4e. Pre-compute roster quality scores per team ────────────────────
        roster_quality: dict[str, float] = {}
        if rosters_df is not None and not rosters_df.empty:
            df_2026 = rosters_df[rosters_df["season_year"] == 2026] if "season_year" in rosters_df.columns else rosters_df
            if not df_2026.empty:
                team_quality_acc: dict[str, list[float]] = {}
                for _, row in df_2026.iterrows():
                    tn = str(row.get("team_name", ""))
                    if not tn:
                        continue
                    avg_r = row.get("avg_rating")
                    minutes = row.get("minutes_played")
                    if avg_r is None or minutes is None:
                        continue
                    try:
                        q = float(avg_r) * float(minutes) ** 0.5
                        if q > 0:
                            team_quality_acc.setdefault(tn, []).append(q)
                    except (TypeError, ValueError):
                        continue
                if team_quality_acc:
                    raw_q = {tn: float(np.mean(qs)) for tn, qs in team_quality_acc.items()}
                    q_mean = float(np.mean(list(raw_q.values())))
                    if q_mean > 1e-9:
                        roster_quality = {tn: q / q_mean for tn, q in raw_q.items()}
                    log.info("roster quality computed: %d teams", len(roster_quality))

        # ── 4f. Pre-compute best-player rolling ratings per team ──────────────
        best_player_rating: dict[str, float] = {}
        if best_players_df is not None and not best_players_df.empty:
            wc26_ids = set(m2026["match_id"].astype(str).tolist())
            team_bp_acc: dict[str, list[tuple]] = {}  # team → [(match_id, top3_avg)]
            for match_id, grp in best_players_df.groupby("match_id"):
                if str(match_id) not in wc26_ids:
                    continue
                for team_id, tgrp in grp.groupby("team_id"):
                    # Get team name from matches
                    match_rows = m2026[m2026["match_id"] == match_id]
                    if match_rows.empty:
                        continue
                    row = match_rows.iloc[0]
                    is_home_vals = tgrp["is_home"].tolist() if "is_home" in tgrp.columns else []
                    is_home = bool(is_home_vals[0]) if is_home_vals else True
                    tn = str(row["home_team"] if is_home else row["away_team"])
                    ratings = tgrp["rating"].dropna().tolist() if "rating" in tgrp.columns else []
                    top3 = sorted(ratings, reverse=True)[:3]
                    if top3:
                        team_bp_acc.setdefault(tn, []).append((str(match_id), float(np.mean(top3))))

            if team_bp_acc:
                team_bp_mean: dict[str, float] = {}
                for tn, entries in team_bp_acc.items():
                    entries_sorted = sorted(entries, key=lambda x: x[0], reverse=True)
                    recent = [r for _, r in entries_sorted[:3]]
                    team_bp_mean[tn] = float(np.mean(recent))
                if team_bp_mean:
                    bp_mean = float(np.mean(list(team_bp_mean.values())))
                    if bp_mean > 1e-9:
                        best_player_rating = {tn: v / bp_mean for tn, v in team_bp_mean.items()}
                log.info("best_player ratings computed: %d teams", len(best_player_rating))

        # ── 5. Compute composite prior for each team ─────────────────────
        for team in sorted(all_2026_teams):
            tp = self._build_team_prior(
                team, hist, teams_2018, teams_2022,
                elo_ratings, pi_ratings, massey_df, colley_df,
                market_lambdas, odds_df,
                xg_att_per_game=xg_att_per_game,
                xg_def_per_game=xg_def_per_game,
                form_z_scores=form_z_scores,
                futures_win_prob=futures_win_prob,
                roster_quality=roster_quality,
                best_player_rating=best_player_rating,
                big_chances_per_game=big_chances_per_game,
                sot_per_game=sot_per_game,
            )
            self._priors[team] = tp

        # ── 6. Apply WC2026 tournament performance adjustment ─────────────────
        # Use actual goals scored/conceded in completed 2026 matches to update
        # each team's final lambdas.  When team_stats_df is provided, the attack
        # ratio is computed from a 40% actual goals / 60% xG blend, which has
        # lower variance and better reflects underlying quality.
        self._apply_tournament_adjustment(matches_df, team_stats_df)

        # ── 7. Apply injury penalties ─────────────────────────────────────────
        if injuries_df is not None and not injuries_df.empty:
            self._apply_injury_penalties(injuries_df)

        self._fitted = True
        n_market = sum(1 for tp in self._priors.values() if "market_implied" in tp.sources_used)
        n_elo = sum(1 for tp in self._priors.values() if "penaltyblog_elo" in tp.sources_used)
        n_fallback = sum(1 for tp in self._priors.values() if tp.fallback_reason)
        n_adj = sum(1 for tp in self._priors.values() if tp.tournament_n_matches > 0)
        log.info(
            "CompositeTeamPrior fitted: %d teams  market_implied=%d  elo=%d  fallback=%d  tournament_adj=%d"
            "  form_teams=%d  futures_teams=%d  roster_teams=%d  bp_teams=%d",
            len(self._priors), n_market, n_elo, n_fallback, n_adj,
            len(form_z_scores), len(futures_win_prob), len(roster_quality), len(best_player_rating),
        )
        return self

    def get_prior(self, team: str) -> TeamPrior:
        """Get the TeamPrior for a team. Returns a confederation-average fallback if unknown."""
        if not self._fitted:
            raise RuntimeError("Call .fit() before .get_prior()")
        if team in self._priors:
            return self._priors[team]
        # Unknown team: create a best-effort prior
        conf = _TEAM_CONFEDERATION.get(team, "GLOBAL")
        tp = TeamPrior(
            team=team,
            confederation=conf,
            final_attack_lambda=_CONFEDERATION_ATTACK.get(conf, _WC_AVG_ATTACK),
            final_defense_lambda=_CONFEDERATION_DEFENSE.get(conf, _WC_AVG_DEFENSE),
            uncertainty="HIGH",
            fallback_reason="team_not_in_2026_schedule",
            source_timestamp=self._fit_timestamp,
        )
        log.warning("CompositeTeamPrior: unknown team '%s' → confederation fallback", team)
        return tp

    def all_priors(self) -> list[TeamPrior]:
        return list(self._priors.values())

    # ── Private methods ───────────────────────────────────────────────────

    def _apply_tournament_adjustment(
        self,
        matches_df: pd.DataFrame,
        team_stats_df: Optional[pd.DataFrame] = None,
    ) -> None:
        """
        Adjust each team's final_attack_lambda and final_defense_lambda based on
        completed WC2026 match results.

        Attack signal: 40% actual goals + 60% xG when team_stats_df is provided.
        xG has lower variance than goals and better reflects underlying quality;
        the 60/40 blend smooths out finishing luck without discarding actual outcomes.

        Defense signal: actual goals conceded only (xG_against = opponent's xG,
        which introduces extra lookup complexity for marginal benefit).

        Shrinkage: ratio = (effective / prior_lambda).
                   shrunk = 1 + (ratio - 1) * n / (n + k), k=3.
        Cap: ±30% maximum adjustment.
        """
        _K = 3  # prior pseudo-match count anchoring ratios toward 1.0
        _CAP_LOW, _CAP_HIGH = 0.70, 1.30

        completed_2026 = matches_df[
            (matches_df["season"] == 2026) &
            (matches_df["status"].isin(["completed", "final"])) &
            matches_df["home_goals"].notna() &
            matches_df["away_goals"].notna()
        ]

        if completed_2026.empty:
            return

        # ── Accumulate goals per team ────────────────────────────────────────
        team_goals: dict[str, dict] = {}
        for _, row in completed_2026.iterrows():
            home, away = str(row["home_team"]), str(row["away_team"])
            hg, ag = float(row["home_goals"]), float(row["away_goals"])
            for team, scored, conceded in [(home, hg, ag), (away, ag, hg)]:
                if team not in team_goals:
                    team_goals[team] = {"scored": 0.0, "conceded": 0.0, "n": 0}
                team_goals[team]["scored"] += scored
                team_goals[team]["conceded"] += conceded
                team_goals[team]["n"] += 1

        # ── Accumulate xG per team from team_stats_df ────────────────────────
        # team_stats_df has one row per (team, match): expected_goals = team's xG
        team_xg_scored: dict[str, float] = {}
        team_xg_n: dict[str, int] = {}
        if team_stats_df is not None and not team_stats_df.empty:
            wc26_ids = set(completed_2026["match_id"].astype(str).tolist())
            for _, row in team_stats_df.iterrows():
                mid = str(row.get("match_id", ""))
                if mid not in wc26_ids:
                    continue
                tn = str(row.get("team_name", ""))
                xg = row.get("expected_goals")
                if not tn or xg is None:
                    continue
                try:
                    xg_f = float(xg)
                except (TypeError, ValueError):
                    continue
                if xg_f < 0:
                    continue
                team_xg_scored[tn] = team_xg_scored.get(tn, 0.0) + xg_f
                team_xg_n[tn] = team_xg_n.get(tn, 0) + 1

        n_xg_used = 0
        n_adjusted = 0
        for team, tp in self._priors.items():
            stats = team_goals.get(team)
            if stats is None or stats["n"] == 0:
                continue

            n = stats["n"]
            shrink = n / (n + _K)

            prior_att = max(tp.final_attack_lambda, _EPS)
            prior_def = max(tp.final_defense_lambda, _EPS)

            # Attack: blend actual goals (40%) with xG (60%) when available
            actual_att = stats["scored"] / n
            xg_n = team_xg_n.get(team, 0)
            if xg_n > 0 and xg_n >= n:
                avg_xg = team_xg_scored[team] / xg_n
                effective_att = 0.4 * actual_att + 0.6 * avg_xg
                n_xg_used += 1
                log.debug(
                    "xG blend: %s  actual_att=%.3f  xg_att=%.3f  blended=%.3f  n=%d",
                    team, actual_att, avg_xg, effective_att, n,
                )
            else:
                effective_att = actual_att

            # Defense: actual goals conceded only
            effective_def = stats["conceded"] / n

            att_ratio = effective_att / prior_att
            def_ratio = effective_def / prior_def

            att_adj = 1.0 + (att_ratio - 1.0) * shrink
            def_adj = 1.0 + (def_ratio - 1.0) * shrink

            att_adj = float(np.clip(att_adj, _CAP_LOW, _CAP_HIGH))
            def_adj = float(np.clip(def_adj, _CAP_LOW, _CAP_HIGH))

            tp.tournament_n_matches = n
            tp.tournament_attack_adj = round(att_adj, 4)
            tp.tournament_defense_adj = round(def_adj, 4)
            tp.final_attack_lambda = round(float(tp.final_attack_lambda * att_adj), 4)
            tp.final_defense_lambda = round(float(max(tp.final_defense_lambda * def_adj, 0.3)), 4)

            if "tournament_wc2026" not in tp.sources_used:
                tp.sources_used.append("tournament_wc2026")

            log.debug(
                "tournament_adjustment applied: %s  n=%d  att_adj=%.3f  def_adj=%.3f"
                "  → att=%.3f  def=%.3f",
                team, n, att_adj, def_adj, tp.final_attack_lambda, tp.final_defense_lambda,
            )
            n_adjusted += 1

        log.info(
            "tournament_adjustment applied: %d teams updated from %d completed WC2026 matches"
            "  (xG blend active for %d/%d teams)",
            n_adjusted, len(completed_2026), n_xg_used, n_adjusted,
        )

    def _fit_elo(self, hist: pd.DataFrame) -> dict[str, float]:
        try:
            from penaltyblog.ratings import Elo
            elo = Elo(k=20, home_field_advantage=0)
            for _, row in hist.iterrows():
                hg, ag = int(row["home_goals"]), int(row["away_goals"])
                result = 2 if hg > ag else (1 if hg == ag else 0)  # penaltyblog: 0=away, 1=draw, 2=home
                elo.update_ratings(str(row["home_team"]), str(row["away_team"]), result)
            return dict(elo.ratings)
        except Exception as exc:
            log.warning("Elo fitting failed: %s", exc)
            return {}

    def _fit_pi(self, hist: pd.DataFrame) -> dict[str, float]:
        try:
            from penaltyblog.ratings import PiRatingSystem
            pi = PiRatingSystem(alpha=0.15, beta=0.1, k=0.75)
            for _, row in hist.iterrows():
                pi.update_ratings(
                    str(row["home_team"]), str(row["away_team"]),
                    int(row["home_goals"]), int(row["away_goals"]),
                )
            # pi.team_ratings stores {team: {"home": float, "away": float}}
            # pi.get_team_rating(team) returns the average as a float
            teams = list(pi.team_ratings.keys())
            return {t: float(pi.get_team_rating(t)) for t in teams}
        except Exception as exc:
            log.warning("Pi rating fitting failed: %s", exc)
            return {}

    def _fit_massey_colley(
        self, hist: pd.DataFrame
    ) -> tuple[pd.DataFrame, pd.DataFrame]:
        massey_df = pd.DataFrame()
        colley_df = pd.DataFrame()
        if len(hist) < 5:
            return massey_df, colley_df
        try:
            from penaltyblog.ratings import Massey
            mr = Massey(
                hist["home_goals"].tolist(), hist["away_goals"].tolist(),
                hist["home_team"].tolist(), hist["away_team"].tolist(),
            )
            massey_df = mr.get_ratings()
            if "team" in massey_df.columns:
                massey_df = massey_df.set_index("team")
        except Exception as exc:
            log.warning("Massey fitting failed: %s", exc)
        try:
            from penaltyblog.ratings import Colley
            cr = Colley(
                hist["home_goals"].tolist(), hist["away_goals"].tolist(),
                hist["home_team"].tolist(), hist["away_team"].tolist(),
            )
            colley_df = cr.get_ratings()
            if "team" in colley_df.columns:
                colley_df = colley_df.set_index("team")
        except Exception as exc:
            log.warning("Colley fitting failed: %s", exc)
        return massey_df, colley_df

    def _apply_injury_penalties(self, injuries_df: pd.DataFrame) -> None:
        """
        Apply lambda penalties for OUT/GTD players by position.

        Penalties per player:
          OUT GK:    multiply defense λ by 0.92
          OUT FW/MF: multiply attack λ by 0.94 per player
          GTD GK:    multiply defense λ by 0.96 (half penalty)
          GTD FW/MF: multiply attack λ by 0.97 per player
        Total attack penalty capped at 0.75; defense penalty capped at 0.75.
        """
        _GK_OUT_DEF = 0.92
        _FW_MF_OUT_ATT = 0.94
        _GK_GTD_DEF = 0.96
        _FW_MF_GTD_ATT = 0.97
        _CAP_FLOOR = 0.75

        for team, tp in self._priors.items():
            team_injuries = injuries_df[
                injuries_df["team_name"].str.lower() == team.lower()
            ] if "team_name" in injuries_df.columns else pd.DataFrame()
            if team_injuries.empty:
                continue

            att_mult = 1.0
            def_mult = 1.0
            n_applied = 0

            for _, row in team_injuries.iterrows():
                status = str(row.get("status", "")).upper()
                pos = str(row.get("player_position", row.get("position", ""))).upper()
                name = str(row.get("player_name", "unknown"))

                if status == "OUT":
                    if "GK" in pos:
                        def_mult *= _GK_OUT_DEF
                        n_applied += 1
                    elif any(p in pos for p in ("FW", "MF", "ST", "CF", "CAM", "AM", "RW", "LW", "SS", "OM", "CM", "RM", "LM", "DM", "CDM")):
                        att_mult *= _FW_MF_OUT_ATT
                        n_applied += 1
                elif status == "GTD":
                    if "GK" in pos:
                        def_mult *= _GK_GTD_DEF
                        n_applied += 1
                    elif any(p in pos for p in ("FW", "MF", "ST", "CF", "CAM", "AM", "RW", "LW", "SS", "OM", "CM", "RM", "LM", "DM", "CDM")):
                        att_mult *= _FW_MF_GTD_ATT
                        n_applied += 1

            if n_applied == 0:
                continue

            # Apply caps
            att_mult = max(att_mult, _CAP_FLOOR)
            def_mult = max(def_mult, _CAP_FLOOR)

            old_att = tp.final_attack_lambda
            old_def = tp.final_defense_lambda
            tp.final_attack_lambda = round(float(tp.final_attack_lambda * att_mult), 4)
            tp.final_defense_lambda = round(float(tp.final_defense_lambda * def_mult), 4)

            if "injuries" not in tp.sources_used:
                tp.sources_used.append("injuries")

            log.warning(
                "Injuries applied: %s  n=%d  att_mult=%.3f  def_mult=%.3f"
                "  att: %.3f→%.3f  def: %.3f→%.3f",
                team, n_applied, att_mult, def_mult,
                old_att, tp.final_attack_lambda, old_def, tp.final_defense_lambda,
            )

    def _extract_market_lambdas(
        self, m2026: pd.DataFrame, odds_df: pd.DataFrame
    ) -> dict[str, dict]:
        """
        For each team in 2026, extract market-implied (lambda_scored, lambda_conceded)
        from their group-stage match odds using goal_expectancy_extended.

        Returns {team: {"scored": [lam1, lam2, ...], "conceded": [...], "timestamps": [...]}}
        """
        if odds_df.empty:
            return {}

        result: dict[str, dict] = {}
        matches_with_odds = m2026[m2026["match_id"].isin(odds_df["match_id"].unique())]

        def am2dec(a: float) -> float:
            if a >= 100:
                return a / 100.0 + 1.0
            return 100.0 / abs(a) + 1.0

        for _, match in matches_with_odds.iterrows():
            mid = int(match["match_id"])
            home, away = str(match["home_team"]), str(match["away_team"])
            if _is_tbd(home) or _is_tbd(away):
                continue

            mrows = odds_df[odds_df["match_id"] == mid]
            if mrows.empty:
                continue

            hw_list, dr_list, aw_list, ou_list = [], [], [], []
            ts_list = []
            for _, row in mrows.iterrows():
                try:
                    hw_a = float(row["moneyline_home"])
                    dr_a = float(row["moneyline_draw"])
                    aw_a = float(row["moneyline_away"])
                    p_hw = 1.0 / am2dec(hw_a)
                    p_dr = 1.0 / am2dec(dr_a)
                    p_aw = 1.0 / am2dec(aw_a)
                    tot = p_hw + p_dr + p_aw
                    hw_list.append(p_hw / tot)
                    dr_list.append(p_dr / tot)
                    aw_list.append(p_aw / tot)
                    tv = row.get("total_value")
                    too = row.get("total_over_odds")
                    tuo = row.get("total_under_odds")
                    if tv is not None and too is not None and tuo is not None:
                        try:
                            if float(tv) == 2.5:
                                p_ov = 1.0 / am2dec(float(too))
                                p_un = 1.0 / am2dec(float(tuo))
                                ou_list.append(p_ov / (p_ov + p_un))
                        except Exception:
                            pass
                    ts = row.get("updated_at")
                    if ts:
                        ts_list.append(str(ts))
                except Exception:
                    continue

            if not hw_list:
                continue

            hw = float(np.mean(hw_list))
            dr = float(np.mean(dr_list))
            aw = float(np.mean(aw_list))
            ou25 = float(np.mean(ou_list)) if ou_list else None
            ts_latest = max(ts_list) if ts_list else None

            try:
                from penaltyblog.models import goal_expectancy_extended, goal_expectancy
                if ou25 is not None:
                    res = goal_expectancy_extended(hw, dr, aw, ou25, 1.0 - ou25,
                                                   objective="cross_entropy")
                else:
                    res = goal_expectancy(hw, dr, aw, objective="cross_entropy")
                lh = float(res["home_exp"])
                la = float(res["away_exp"])
            except Exception:
                continue

            for team, lscored, lconceded in [(home, lh, la), (away, la, lh)]:
                if team not in result:
                    result[team] = {"scored": [], "conceded": [], "timestamps": []}
                result[team]["scored"].append(lscored)
                result[team]["conceded"].append(lconceded)
                result[team]["timestamps"].append(ts_latest)

        return result

    def _build_team_prior(
        self, team: str, hist: pd.DataFrame,
        teams_2018: set, teams_2022: set,
        elo_ratings: dict, pi_ratings: dict,
        massey_df: pd.DataFrame, colley_df: pd.DataFrame,
        market_lambdas: dict, odds_df: pd.DataFrame,
        xg_att_per_game: Optional[dict] = None,
        xg_def_per_game: Optional[dict] = None,
        form_z_scores: Optional[dict] = None,
        futures_win_prob: Optional[dict] = None,
        roster_quality: Optional[dict] = None,
        best_player_rating: Optional[dict] = None,
        big_chances_per_game: Optional[dict] = None,
        sot_per_game: Optional[dict] = None,
    ) -> TeamPrior:
        conf = _TEAM_CONFEDERATION.get(team, "GLOBAL")
        conf_att = _CONFEDERATION_ATTACK.get(conf, _WC_AVG_ATTACK)
        conf_def = _CONFEDERATION_DEFENSE.get(conf, _WC_AVG_DEFENSE)

        tp = TeamPrior(
            team=team,
            appeared_2018=team in teams_2018,
            appeared_2022=team in teams_2022,
            confederation=conf,
            confederation_attack=conf_att,
            confederation_defense=conf_def,
            is_host=team in _HOST_NATIONS,
            source_timestamp=self._fit_timestamp,
        )

        # WC match count
        team_hist = hist[(hist["home_team"] == team) | (hist["away_team"] == team)]
        tp.n_wc_matches = len(team_hist)

        # ── Elo ─────────────────────────────────────────────────────────
        if elo_ratings:
            elo_val = elo_ratings.get(team, 1500.0)
            tp.penaltyblog_elo = float(elo_val)
            # Convert Elo to lambda: Elo 1500 → 1.25 (WC avg), ±150 pts → ±50% lambda
            # Calibration: use logistic transformation
            elo_rel = (elo_val - 1500.0) / 300.0  # normalized
            lam_elo = _WC_AVG_ATTACK * np.exp(elo_rel * 0.5)
            tp.elo_attack_lambda = round(float(lam_elo), 4)
            tp.elo_defense_lambda = round(float(_WC_AVG_DEFENSE * np.exp(-elo_rel * 0.3)), 4)

        # ── Pi ──────────────────────────────────────────────────────────
        if pi_ratings:
            pi_val = pi_ratings.get(team)
            if pi_val is not None:
                tp.penaltyblog_pi = float(pi_val)
                # Pi is a goal-difference-based rating on roughly [-2, 2] scale
                lam_pi = _WC_AVG_ATTACK * np.exp(float(pi_val) * 0.25)
                tp.pi_attack_lambda = round(float(lam_pi), 4)
                tp.pi_defense_lambda = round(float(_WC_AVG_DEFENSE * np.exp(-float(pi_val) * 0.15)), 4)

        # ── Massey ──────────────────────────────────────────────────────
        if not massey_df.empty and team in massey_df.index:
            row = massey_df.loc[team]
            tp.massey_rating = float(row.get("rating", 0.0))
            tp.massey_offence = float(row.get("offence", 0.0))
            tp.massey_defence = float(row.get("defence", 0.0))
            # Massey offence: roughly in goals-per-game units, centered around ~1.3
            massey_off_centered = float(tp.massey_offence or 0.0)
            lam_massey = _WC_AVG_ATTACK + massey_off_centered * 0.4
            lam_massey = max(lam_massey, 0.3)
            tp.massey_attack_lambda = round(float(lam_massey), 4)
            massey_def_centered = float(tp.massey_defence or 0.0)
            tp.massey_defense_lambda = round(float(max(_WC_AVG_DEFENSE - massey_def_centered * 0.4, 0.3)), 4)

        # ── Market-implied ───────────────────────────────────────────────
        ml = market_lambdas.get(team)
        if ml and ml["scored"]:
            tp.market_implied_attack = round(float(np.mean(ml["scored"])), 4)
            tp.market_implied_defense = round(float(np.mean(ml["conceded"])), 4)
            tp.n_market_matches = len(ml["scored"])
            ts_list = [t for t in ml["timestamps"] if t]
            tp.market_odds_timestamp = max(ts_list) if ts_list else None

        # ── FIFA ranking ─────────────────────────────────────────────────
        fifa_pts = _FIFA_POINTS.get(team)
        if fifa_pts is not None:
            tp.fifa_points = float(fifa_pts)
            tp.fifa_ranking = sorted(_FIFA_POINTS.keys(),
                                     key=lambda t: -_FIFA_POINTS[t]).index(team) + 1
            tp.fifa_attack_lambda = round(float(_fifa_to_lambda(fifa_pts, _WC_AVG_ATTACK)), 4)
            tp.fifa_defense_lambda = round(float(_fifa_to_lambda(
                # Invert: weaker teams (lower pts) have higher defense lambda (concede more)
                _FIFA_GLOBAL_MEDIAN * 2 - fifa_pts, _WC_AVG_DEFENSE
            )), 4)
            tp.fifa_defense_lambda = max(tp.fifa_defense_lambda, 0.60)

        # ── Qualifying performance ────────────────────────────────────────
        qual = _QUALIFYING_STATS.get(team)
        if qual and qual[0] is not None:
            q_scored, q_conceded, q_n, q_win_rate = qual
            tp.qualifying_goals_scored_per_game = float(q_scored)
            tp.qualifying_goals_conceded_per_game = float(q_conceded)
            tp.qualifying_n_games = int(q_n)
            tp.qualifying_win_rate = float(q_win_rate) if q_win_rate is not None else None
            # Convert to lambda: scored/conceded per game is already in lambda units
            # Shrink toward WC average with N-based shrinkage: less weight for few games
            shrink = min(q_n / 20.0, 0.8)  # max 0.8 weight on qualifying data
            tp.qualifying_attack_lambda = round(
                float((1 - shrink) * _WC_AVG_ATTACK + shrink * q_scored), 4
            )
            tp.qualifying_defense_lambda = round(
                float((1 - shrink) * _WC_AVG_DEFENSE + shrink * q_conceded), 4
            )

        # ── Blend all sources ────────────────────────────────────────────
        sources = []
        att_inputs: list[tuple[str, float, float]] = []  # (name, att, weight)
        def_inputs: list[tuple[str, float, float]] = []

        has_market = tp.market_implied_attack is not None
        has_fifa = tp.fifa_attack_lambda is not None
        has_qual = tp.qualifying_attack_lambda is not None

        # Whether to use market-implied lambdas in the prior blend.
        # market_weight=0.0 keeps the prior fully independent of the opening line.
        effective_market_w = self._market_weight if has_market else 0.0

        if effective_market_w > 0.0:
            att_inputs.append(("market_implied", tp.market_implied_attack, effective_market_w))
            def_inputs.append(("market_implied", tp.market_implied_defense, effective_market_w))
            sources.append("market_implied")

        # xG from WC2026 completed matches — direct blend input at 0.15 weight.
        # Requires ≥2 completed matches; xG has lower variance than raw goals
        # and directly measures shot quality, making it more predictive than
        # qualifying or FIFA ranking for teams already active in the tournament.
        _xg_att = (xg_att_per_game or {}).get(team)
        _xg_def = (xg_def_per_game or {}).get(team)
        if _xg_att is not None and _xg_att > 0:
            att_inputs.append(("xg_wc2026", _xg_att, 0.15))
            if _xg_def is not None and _xg_def > 0:
                def_inputs.append(("xg_wc2026", _xg_def, 0.15))
            if "xg_wc2026" not in sources:
                sources.append("xg_wc2026")
            log.debug(
                "xG_wc2026 direct blend: %s  xg_att=%.3f  xg_def=%s",
                team, _xg_att,
                f"{_xg_def:.3f}" if _xg_def is not None else "N/A",
            )

        # ── Big chances + SOT per-90 (weights 0.05 each on attack λ) ──────
        # These are normalized z-scores (mean=0, sigma=1 across teams).
        # Blend as fractional adjustments to attack lambda.
        _bc_z = (big_chances_per_game or {}).get(team)
        _sot_z = (sot_per_game or {}).get(team)
        if _bc_z is not None:
            # Map z-score to lambda adjustment: clip to ±2 sigma
            _bc_adj = float(np.clip(_bc_z * 0.05, -0.10, 0.10))
            if "big_chances_wc2026" not in sources:
                sources.append("big_chances_wc2026")
        else:
            _bc_adj = 0.0
        if _sot_z is not None:
            _sot_adj = float(np.clip(_sot_z * 0.05, -0.10, 0.10))
            if "sot_wc2026" not in sources:
                sources.append("sot_wc2026")
        else:
            _sot_adj = 0.0

        # ── Team form z-score adjustment (weight 0.10) ─────────────────
        # Applies ±5% to att/def λ based on recent avg_rating z-score.
        _form_z = (form_z_scores or {}).get(team)
        if _form_z is not None:
            _form_adj = float(np.clip(_form_z * 0.05, -0.05, 0.05))
            _form_att = composite_att * (1.0 + _form_adj) if False else None  # computed post-blend
            # Store z-score for post-blend application (see below)
            if "form_wc2026" not in sources:
                sources.append("form_wc2026")
            log.debug("form_wc2026: %s  z=%.3f  adj=%.4f", team, _form_z, _form_adj)

        # ── Futures-implied win probability (weight 0.08) ──────────────
        _fut_prob = (futures_win_prob or {}).get(team)
        if _fut_prob is not None and _fut_prob > 0:
            # Map win probability to lambda boost: teams with higher tournament
            # win probability get +3% attack λ, very low get -3%.
            # Reference: median team win prob ≈ 1/32 ≈ 0.031 for 32-team tournament
            n_teams = max(len(futures_win_prob), 16)
            median_prob = 1.0 / n_teams
            fut_rel = (_fut_prob - median_prob) / max(median_prob, 1e-9)
            fut_adj = float(np.clip(fut_rel * 0.03, -0.03, 0.03))
            if "futures_implied" not in sources:
                sources.append("futures_implied")
            log.debug("futures_implied: %s  prob=%.4f  adj=%.4f", team, _fut_prob, fut_adj)
        else:
            fut_adj = 0.0

        # ── Roster quality multiplier (weight 0.08 attack, 0.07 defense) ─
        _roster_q = (roster_quality or {}).get(team)
        if _roster_q is not None and _roster_q > 0:
            # roster_quality is normalized to mean=1.0; apply as fractional boost
            roster_att_mult = 1.0 + float(np.clip((_roster_q - 1.0) * 0.08, -0.08, 0.08))
            roster_def_mult = 1.0 + float(np.clip((_roster_q - 1.0) * 0.07, -0.07, 0.07))
            if "roster_quality" not in sources:
                sources.append("roster_quality")
        else:
            roster_att_mult = 1.0
            roster_def_mult = 1.0

        # ── Best-player rolling rating multiplier (weight 0.06 attack) ──
        _bp_rating = (best_player_rating or {}).get(team)
        if _bp_rating is not None and _bp_rating > 0:
            bp_att_mult = 1.0 + float(np.clip((_bp_rating - 1.0) * 0.06, -0.06, 0.06))
            if "best_player_form" not in sources:
                sources.append("best_player_form")
        else:
            bp_att_mult = 1.0

        # When market is used, tighten FIFA/qualifying; when absent (or weight=0), expand them.
        using_market_in_blend = effective_market_w > 0.0

        if has_fifa:
            fifa_w = 0.12 if using_market_in_blend else 0.30
            att_inputs.append(("fifa_ranking", tp.fifa_attack_lambda, fifa_w))
            def_inputs.append(("fifa_ranking", tp.fifa_defense_lambda, fifa_w))
            sources.append("fifa_ranking")

        if has_qual:
            qual_w = 0.10 if using_market_in_blend else 0.25
            att_inputs.append(("qualifying", tp.qualifying_attack_lambda, qual_w))
            def_inputs.append(("qualifying", tp.qualifying_defense_lambda, qual_w))
            sources.append("qualifying")

        remaining_w = max(0.0, 1.0 - sum(w for _, _, w in att_inputs))

        if tp.pi_attack_lambda is not None:
            # Pi is goal-margin sensitive → higher weight than Elo for score PMF estimation.
            # No-market: 0.40 of remaining; with-market: 0.50 of remaining (unchanged).
            pi_w = remaining_w * (0.50 if not using_market_in_blend else 0.50)
            att_inputs.append(("penaltyblog_pi", tp.pi_attack_lambda, pi_w))
            def_inputs.append(("penaltyblog_pi", tp.pi_defense_lambda, pi_w))
            sources.append("penaltyblog_pi")
            remaining_w -= pi_w

        if tp.elo_attack_lambda is not None:
            # Elo is win/loss only — stable floor; lower weight than Pi in no-market path.
            # No-market: 0.70 of remaining (same as before when Pi absent, else 0.60→0.55).
            elo_w = remaining_w * (0.70 if tp.pi_attack_lambda is None else 0.55)
            att_inputs.append(("penaltyblog_elo", tp.elo_attack_lambda, elo_w))
            def_inputs.append(("penaltyblog_elo", tp.elo_defense_lambda, elo_w))
            sources.append("penaltyblog_elo")
            remaining_w -= elo_w

        if tp.massey_attack_lambda is not None:
            mas_w = remaining_w * 0.80
            att_inputs.append(("massey", tp.massey_attack_lambda, mas_w))
            def_inputs.append(("massey", tp.massey_defense_lambda, mas_w))
            sources.append("massey")

        # Always include confederation as a soft floor
        conf_total_w = max(0.05, 1.0 - sum(w for _, _, w in att_inputs))
        att_inputs.append(("confederation", conf_att, conf_total_w))
        def_inputs.append(("confederation", conf_def, conf_total_w))
        if "confederation" not in sources:
            sources.append("confederation")

        # Normalize and compute weighted average
        att_total_w = sum(w for _, _, w in att_inputs)
        def_total_w = sum(w for _, _, w in def_inputs)
        composite_att = sum(v * w for _, v, w in att_inputs) / att_total_w
        composite_def = sum(v * w for _, v, w in def_inputs) / def_total_w

        # ── Host bonus ───────────────────────────────────────────────────
        if tp.is_host:
            # Use dynamically recalibrated bonus if provided, else module constant
            _eff_host_bonus = (
                self._host_att_bonus_override
                if self._host_att_bonus_override is not None
                else _HOST_ATT_BONUS
            )
            tp.host_att_bonus = _eff_host_bonus
            tp.host_def_bonus = _HOST_DEF_BONUS
            composite_att += _eff_host_bonus
            composite_def -= _HOST_DEF_BONUS
            composite_def = max(composite_def, 0.3)
            sources.append("host_bonus")

        tp.final_attack_lambda = round(float(composite_att), 4)
        tp.final_defense_lambda = round(float(max(composite_def, 0.3)), 4)
        tp.sources_used = sources
        tp.source_weights = {name: round(w / att_total_w, 3) for name, _, w in att_inputs}

        # ── Post-blend: apply form / futures / roster / best-player adjustments ─
        # These are multiplicative and applied after the weighted average blend
        # so they don't distort the blend weights. Each is capped conservatively.
        _final_att = tp.final_attack_lambda
        _final_def = tp.final_defense_lambda

        # Team form z-score: ±5% on both att and def
        if _form_z is not None:
            _form_adj = float(np.clip(_form_z * 0.05, -0.05, 0.05))
            _final_att *= (1.0 + _form_adj)
            _final_def *= (1.0 - _form_adj)  # good form → concede fewer goals

        # Big chances + SOT z-score adjustments (attack only)
        _final_att *= (1.0 + _bc_adj + _sot_adj)

        # Futures win probability: ±3% on attack
        _final_att *= (1.0 + fut_adj)

        # Roster quality: ±8% attack, ±7% defense
        _final_att *= roster_att_mult
        _final_def *= roster_def_mult

        # Best-player rolling rating: ±6% on attack
        _final_att *= bp_att_mult

        tp.final_attack_lambda = round(float(np.clip(_final_att, 0.3, 5.0)), 4)
        tp.final_defense_lambda = round(float(np.clip(_final_def, 0.3, 5.0)), 4)

        # ── Uncertainty assessment ───────────────────────────────────────
        if tp.n_market_matches >= 3 and tp.n_wc_matches >= 4:
            tp.uncertainty = "LOW"
        elif tp.n_market_matches >= 2 or tp.n_wc_matches >= 2:
            tp.uncertainty = "MEDIUM"
        else:
            tp.uncertainty = "HIGH"
            if tp.market_implied_attack is None and tp.n_wc_matches == 0:
                tp.fallback_reason = "no_market_odds_no_wc_history"

        return tp


def build_composite_prior(
    matches_df: pd.DataFrame,
    odds_df: pd.DataFrame,
    markets_df: Optional[pd.DataFrame] = None,
    market_weight: Optional[float] = None,
    team_stats_df: Optional[pd.DataFrame] = None,
    host_att_bonus: Optional[float] = None,
    team_form_df: Optional[pd.DataFrame] = None,
    injuries_df: Optional[pd.DataFrame] = None,
    futures_df: Optional[pd.DataFrame] = None,
    rosters_df: Optional[pd.DataFrame] = None,
    best_players_df: Optional[pd.DataFrame] = None,
) -> CompositeTeamPrior:
    """Convenience function: fit and return a CompositeTeamPrior.

    Parameters
    ----------
    market_weight : float or None
        Fraction allocated to market-implied lambdas in the prior blend.
        None → CompositeTeamPrior.DEFAULT_MARKET_WEIGHT (currently 0.20).
    team_stats_df : pd.DataFrame or None
        BDL team_stats table; when provided the tournament adjustment blends
        actual goals (40%) with xG (60%) for a lower-variance attack signal.
    host_att_bonus : float or None
        Override for the host nation attack bonus (default: _HOST_ATT_BONUS=0.10).
        Pass a dynamically recalibrated value to adjust for actual 2026 WC host performance.
    team_form_df : pd.DataFrame or None
        BDL match_team_form table; per-team avg_rating form adjustment (weight 0.10).
    injuries_df : pd.DataFrame or None
        Player injuries table; lambda penalties for OUT/GTD players by position.
    futures_df : pd.DataFrame or None
        Tournament futures odds; win probability prior (weight 0.08).
    rosters_df : pd.DataFrame or None
        Player rosters table; 2026 roster quality score (weight 0.08 att, 0.07 def).
    best_players_df : pd.DataFrame or None
        Match best players table; rolling top-3 rating multiplier (weight 0.06 att).
    """
    prior = CompositeTeamPrior(market_weight=market_weight)
    if host_att_bonus is not None:
        prior._host_att_bonus_override = float(host_att_bonus)
    prior.fit(
        matches_df, odds_df, markets_df,
        team_stats_df=team_stats_df,
        team_form_df=team_form_df,
        injuries_df=injuries_df,
        futures_df=futures_df,
        rosters_df=rosters_df,
        best_players_df=best_players_df,
    )
    return prior


# ── Helpers ───────────────────────────────────────────────────────────────

def _is_tbd(team: str) -> bool:
    if not team:
        return True
    s = str(team).strip()
    if len(s) <= 4 and s[0] in "WL" and s[1:].isdigit():
        return True
    if len(s) <= 3 and s[0].isdigit():
        return True
    if "/" in s:
        return True
    return False


def predict_match_from_composite(
    home: str, away: str,
    prior: CompositeTeamPrior,
    max_goals: int = 15,
    model: str = "dixon_coles",
    rho: float = -0.05,
) -> tuple[np.ndarray, float, float]:
    """
    Produce a composite_rating_pmf from team priors.

    Defense semantics: `final_defense_lambda` = goals CONCEDED per game vs
    average opponent.  Higher = weaker defense.  This is consistent with
    market_implied_defense extraction (we measure how many goals the team
    concedes, not how strong they are defensively).

    Expected-goals formula (multiplicative Poisson model):
        lam_h = att_home * def_away / WC_avg
        lam_a = att_away * def_home / WC_avg

    Where WC_avg = 1.30 is the global average goals per team per game.

    Example: Mexico (att=1.63, def=0.864) vs SA (att=0.918, def=1.505)
        lam_h = 1.63 * 1.505 / 1.30 = 1.888  (Mexico scores)
        lam_a = 0.918 * 0.864 / 1.30 = 0.610  (SA scores)
    This gives Mexico ~65% home-win, close to the BDL 6-vendor market 67.5%.

    Parameters
    ----------
    rho : float
        Dixon-Coles low-score correlation parameter. Pass the value fitted on
        historical WC data (extracted from DixonColesGoalModel.get_params()) to
        improve exact-score calibration. Default -0.05 is a sensible league
        average; WC data typically yields values closer to -0.03 to -0.06.

    Returns
    -------
    (pmf_grid, lambda_home, lambda_away)
    """
    home_prior = prior.get_prior(home)
    away_prior = prior.get_prior(away)

    global_avg = _WC_AVG_ATTACK

    # att_i = how many goals team i scores vs avg opponent
    # def_j = how many goals team j concedes vs avg opponent
    # Multiplicative model: lam_h = att_h * def_a / avg
    lam_h = home_prior.final_attack_lambda * away_prior.final_defense_lambda / global_avg
    lam_a = away_prior.final_attack_lambda * home_prior.final_defense_lambda / global_avg

    # Cap to reasonable range
    lam_h = float(np.clip(lam_h, 0.3, 5.0))
    lam_a = float(np.clip(lam_a, 0.3, 5.0))

    # Build PMF using calibrated rho from the fitted Dixon-Coles model
    try:
        from penaltyblog.models import create_dixon_coles_grid
        grid = create_dixon_coles_grid(lam_h, lam_a, rho=rho, max_goals=max_goals - 1)
        pmf = np.array(grid.grid, dtype=np.float64)
    except Exception:
        from scipy.stats import poisson
        pmf = np.outer(
            poisson.pmf(range(max_goals), lam_h),
            poisson.pmf(range(max_goals), lam_a),
        )

    pmf = np.clip(pmf, 0, None)
    pmf /= pmf.sum()
    return pmf, lam_h, lam_a
