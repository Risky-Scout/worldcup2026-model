"""
Team strength in Expected Goal Margin (EGM) units.

EGM = expected goals for team A minus expected goals against an average World Cup team
on a neutral field.

Positive EGM → stronger than average.
Negative EGM → weaker than average.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class TeamMarginRating:
    team_id: int
    team_name: str
    abbreviation: Optional[str]
    confederation: Optional[str]

    # Core EGM
    neutral_egm: float              # production-selected version
    attack_log: float               # centered: average WC team ≈ 0
    defense_log: float              # positive = better defense

    # Stacked model outputs
    pure_strength_egm: float        # excludes current-match /odds
    market_strength_egm: float      # includes de-vigged market ability

    # Individual EGM components (None if component not available)
    market_component_egm: Optional[float] = None
    pi_component_egm: Optional[float] = None
    elo_component_egm: Optional[float] = None
    massey_component_egm: Optional[float] = None
    colley_component_egm: Optional[float] = None
    fifa_component_egm: Optional[float] = None
    qualifying_component_egm: Optional[float] = None
    xg_process_component_egm: Optional[float] = None
    player_component_egm: Optional[float] = None
    goalkeeper_component_egm: Optional[float] = None
    form_component_egm: Optional[float] = None
    futures_component_egm: Optional[float] = None

    # Uncertainty and metadata
    uncertainty_egm: float = 0.0
    sample_size_effective: float = 0.0
    sources_used: list[str] = field(default_factory=list)
    asof_timestamp: datetime = field(default_factory=datetime.utcnow)
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
    def stub(cls, team_id: int, team_name: str) -> "TeamMarginRating":
        """Return a zero-information stub for teams with no data."""
        return cls(
            team_id=team_id,
            team_name=team_name,
            abbreviation=None,
            confederation=None,
            neutral_egm=0.0,
            attack_log=0.0,
            defense_log=0.0,
            pure_strength_egm=0.0,
            market_strength_egm=0.0,
            sources_used=["stub"],
        )
