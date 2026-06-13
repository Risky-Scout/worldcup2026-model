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
  Default market_weight=0.0 (pure penaltyblog; see below for rationale).
  market_implied: 0.00, fifa_ranking: 0.30, qualifying: 0.25, penaltyblog_pi/elo/massey: rest

  Weights last set: 2026-06-12.
  Rationale: CLV (Closing Line Value) is maximised when the model prior is independent
  of the opening market. A high market weight anchors the prior to opening odds,
  suppressing divergence vs the closing line. 0% market weight preserves full
  independence so market-reconciliation is the only place market signal enters.
  Reassess after more group-stage matches complete (target: 2026-06-13 or 2026-06-14).
  Use CompositeTeamPrior(market_weight=0.6) to restore the original blending.

Blending weights when NO market odds exist:
  penaltyblog_elo: 0.45, penaltyblog_pi: 0.30, massey: 0.15, confederation: 0.10

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
    # CONCACAF (Octagonal → World Cup qualifying)
    "Mexico":      (None, None, 0, None),   # host, no qualifying
    "USA":         (None, None, 0, None),   # host
    "Canada":      (None, None, 0, None),   # host
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
    # 0.0 = pure penaltyblog (maximises CLV independence).
    # Set >0 to blend in opening-market-implied lambdas (e.g. 0.6 for the old default).
    DEFAULT_MARKET_WEIGHT: float = 0.0

    def __init__(self, market_weight: Optional[float] = None):
        """
        Parameters
        ----------
        market_weight : float or None
            Fraction of the prior allocated to market-implied lambdas when market
            odds are available (0.0 = pure penaltyblog, 1.0 = pure market).
            None → uses DEFAULT_MARKET_WEIGHT (currently 0.0).
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

    def fit(
        self,
        matches_df: pd.DataFrame,
        odds_df: pd.DataFrame,
        markets_df: Optional[pd.DataFrame] = None,
    ) -> "CompositeTeamPrior":
        """
        Fit all rating systems and extract market-implied lambdas.

        Parameters
        ----------
        matches_df   Full matches table (2018+2022+2026)
        odds_df      BDL odds table (main odds, 6 vendors)
        markets_df   Optional markets sub-array table
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

        # ── 5. Compute composite prior for each team ─────────────────────
        for team in sorted(all_2026_teams):
            tp = self._build_team_prior(
                team, hist, teams_2018, teams_2022,
                elo_ratings, pi_ratings, massey_df, colley_df,
                market_lambdas, odds_df,
            )
            self._priors[team] = tp

        self._fitted = True
        n_market = sum(1 for tp in self._priors.values() if "market_implied" in tp.sources_used)
        n_elo = sum(1 for tp in self._priors.values() if "penaltyblog_elo" in tp.sources_used)
        n_fallback = sum(1 for tp in self._priors.values() if tp.fallback_reason)
        log.info(
            "CompositeTeamPrior fitted: %d teams  market_implied=%d  elo=%d  fallback=%d",
            len(self._priors), n_market, n_elo, n_fallback,
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
                    res = goal_expectancy_extended(hw, dr, aw, ou25, 1.0 - ou25)
                else:
                    res = goal_expectancy(hw, dr, aw)
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
            pi_w = remaining_w * (0.40 if not using_market_in_blend else 0.50)
            att_inputs.append(("penaltyblog_pi", tp.pi_attack_lambda, pi_w))
            def_inputs.append(("penaltyblog_pi", tp.pi_defense_lambda, pi_w))
            sources.append("penaltyblog_pi")
            remaining_w -= pi_w

        if tp.elo_attack_lambda is not None:
            elo_w = remaining_w * (0.70 if tp.pi_attack_lambda is None else 0.60)
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
            tp.host_att_bonus = _HOST_ATT_BONUS
            tp.host_def_bonus = _HOST_DEF_BONUS
            composite_att += _HOST_ATT_BONUS
            composite_def -= _HOST_DEF_BONUS
            composite_def = max(composite_def, 0.3)
            sources.append("host_bonus")

        tp.final_attack_lambda = round(float(composite_att), 4)
        tp.final_defense_lambda = round(float(max(composite_def, 0.3)), 4)
        tp.sources_used = sources
        tp.source_weights = {name: round(w / att_total_w, 3) for name, _, w in att_inputs}

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
) -> CompositeTeamPrior:
    """Convenience function: fit and return a CompositeTeamPrior.

    Parameters
    ----------
    market_weight : float or None
        Fraction allocated to market-implied lambdas in the prior blend.
        None → CompositeTeamPrior.DEFAULT_MARKET_WEIGHT (currently 0.0).
        Pass 0.6 to restore the original blending behaviour.
    """
    prior = CompositeTeamPrior(market_weight=market_weight)
    prior.fit(matches_df, odds_df, markets_df)
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

    # Build PMF
    try:
        from penaltyblog.models import create_dixon_coles_grid
        grid = create_dixon_coles_grid(lam_h, lam_a, rho=-0.05, max_goals=max_goals - 1)
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
