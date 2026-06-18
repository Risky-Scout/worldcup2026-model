"""Abstract DataProvider interface."""
from __future__ import annotations

from abc import ABC, abstractmethod


class DataProvider(ABC):
    """
    Canonical interface for all data sources.

    All providers must return **raw dicts** (as returned by the API).
    Schema validation (pydantic) is applied by the dataset builder, not here.
    """

    @abstractmethod
    def fetch_matches(self, seasons: list[int]) -> list[dict]: ...

    @abstractmethod
    def fetch_odds(self, match_ids: list[int]) -> list[dict]: ...

    @abstractmethod
    def fetch_team_stats(self, match_ids: list[int]) -> list[dict]: ...

    @abstractmethod
    def fetch_player_stats(self, match_ids: list[int]) -> list[dict]: ...

    @abstractmethod
    def fetch_events(self, match_ids: list[int]) -> list[dict]: ...

    @abstractmethod
    def fetch_shots(self, match_ids: list[int]) -> list[dict]: ...

    @abstractmethod
    def fetch_lineups(self, match_ids: list[int]) -> list[dict]: ...

    @abstractmethod
    def fetch_momentum(self, match_ids: list[int]) -> list[dict]: ...

    @abstractmethod
    def fetch_group_standings(self, seasons: list[int]) -> list[dict]: ...

    @abstractmethod
    def fetch_team_form(self, match_ids: list[int]) -> list[dict]: ...

    def fetch_injuries(self, statuses: list[str] | None = None) -> list[dict]:
        """Fetch player injuries. Optional — providers may override."""
        return []

    def fetch_futures(self) -> list[dict]:
        """Fetch tournament futures odds. Optional — providers may override."""
        return []

    def fetch_rosters(self, seasons: list[int] | None = None) -> list[dict]:
        """Fetch player rosters. Optional — providers may override."""
        return []

    def fetch_player_props(
        self,
        match_id: int,
        prop_type: str | None = None,
        vendors: list[str] | None = None,
    ) -> list[dict]:
        """Fetch player props for a match. Optional — providers may override."""
        return []

    def fetch_avg_positions(
        self,
        match_ids: list[int] | None = None,
        team_ids: list[int] | None = None,
    ) -> list[dict]:
        """Fetch average player positions. Optional — providers may override."""
        return []

    def fetch_best_players(self, match_ids: list[int] | None = None) -> list[dict]:
        """Fetch match best players. Optional — providers may override."""
        return []
