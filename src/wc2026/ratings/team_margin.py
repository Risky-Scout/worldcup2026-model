"""
Team strength in Expected Goal Margin (EGM) units.

EGM = expected goals for team A minus expected goals against an average World Cup team
on a neutral field.

Positive EGM → stronger than average.
Negative EGM → weaker than average.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class TeamMarginRating:
    team_id: int
    team_name: str
    abbreviation: str | None
    confederation: str | None

    # Core EGM
    neutral_egm: float              # production-selected version
    attack_log: float               # centered: average WC team ≈ 0
    defense_log: float              # positive = better defense

    # Stacked model outputs
    pure_strength_egm: float        # excludes current-match /odds
    market_strength_egm: float      # includes de-vigged market ability

    # Individual EGM components (None if component not available)
    market_component_egm: float | None = None
    pi_component_egm: float | None = None
    elo_component_egm: float | None = None
    massey_component_egm: float | None = None
    colley_component_egm: float | None = None
    fifa_component_egm: float | None = None
    qualifying_component_egm: float | None = None
    xg_process_component_egm: float | None = None
    player_component_egm: float | None = None
    goalkeeper_component_egm: float | None = None
    form_component_egm: float | None = None
    futures_component_egm: float | None = None

    # Uncertainty and metadata
    uncertainty_egm: float = 0.0
    sample_size_effective: float = 0.0
    sources_used: list[str] = field(default_factory=list)
    asof_timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    model_version: str = "v0.1-shadow"

    def to_dict(self) -> dict:
        return {
            "team_id": self.team_id,
            "team_name": self.team_name,
            "abbreviation": self.abbreviation,
            "confederation": self.confederation,
            "neutral_egm": self.neutral_egm,
            "attack_log": self.attack_log,
            "defense_log": self.defense_log,
            "pure_strength_egm": self.pure_strength_egm,
            "market_strength_egm": self.market_strength_egm,
            "market_component_egm": self.market_component_egm,
            "pi_component_egm": self.pi_component_egm,
            "elo_component_egm": self.elo_component_egm,
            "massey_component_egm": self.massey_component_egm,
            "colley_component_egm": self.colley_component_egm,
            "fifa_component_egm": self.fifa_component_egm,
            "qualifying_component_egm": self.qualifying_component_egm,
            "xg_process_component_egm": self.xg_process_component_egm,
            "player_component_egm": self.player_component_egm,
            "goalkeeper_component_egm": self.goalkeeper_component_egm,
            "form_component_egm": self.form_component_egm,
            "futures_component_egm": self.futures_component_egm,
            "uncertainty_egm": self.uncertainty_egm,
            "sample_size_effective": self.sample_size_effective,
            "sources_used": self.sources_used,
            "asof_timestamp": self.asof_timestamp.isoformat() if self.asof_timestamp else None,
            "model_version": self.model_version,
        }

    @classmethod
    def stub(cls, team_id: int, team_name: str, confederation: str | None = None) -> TeamMarginRating:
        """
        Return a fallback rating for teams with insufficient data.
        Uses confederation prior if available, global fallback otherwise.
        uncertainty_egm = 1.0 means maximum uncertainty.
        """
        from src.wc2026.ratings.fallback_prior import confederation_prior_egm
        conf_egm = confederation_prior_egm(confederation)
        sources = ["confederation"] if confederation else ["global_fallback"]
        return cls(
            team_id=team_id,
            team_name=team_name,
            abbreviation=None,
            confederation=confederation,
            neutral_egm=conf_egm,
            attack_log=conf_egm / 2,
            defense_log=-conf_egm / 2,
            pure_strength_egm=conf_egm,
            market_strength_egm=conf_egm,
            uncertainty_egm=1.0 if not confederation else 0.7,
            sources_used=sources,
        )
