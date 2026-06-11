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
