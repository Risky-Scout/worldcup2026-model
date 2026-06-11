"""BallDontLie FIFA World Cup API client with rate-limiting and automatic pagination."""
from __future__ import annotations

import os
import time
from typing import Any, Generator

import requests
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "https://api.balldontlie.io/fifa/worldcup/v1"
_DEFAULT_PER_PAGE = 100


class BDLClient:
    """
    Thread-safe client for the BallDontLie FIFA World Cup API.

    Handles authentication, pagination via cursor, and a configurable
    per-request delay to stay within the GOAT tier's 600 req/min limit.

    Parameters
    ----------
    api_key : str, optional
        BDL API key. Falls back to the ``BDL_API_KEY`` environment variable.
    req_delay : float
        Minimum seconds between requests. Default 0.15 s ≈ 400 req/min,
        leaving headroom under the 600 req/min GOAT ceiling.
    """

    def __init__(self, api_key: str | None = None, req_delay: float = 0.15) -> None:
        self._api_key = api_key or os.environ.get("BDL_API_KEY")
        if not self._api_key:
            raise ValueError(
                "BDL API key is required. Set BDL_API_KEY env var or pass api_key=."
            )
        self._session = requests.Session()
        self._session.headers.update({"Authorization": self._api_key})
        self._req_delay = req_delay
        self._last_call: float = 0.0

    # ------------------------------------------------------------------
    # Public paginated resource methods
    # ------------------------------------------------------------------

    def teams(self, seasons: list[int] | None = None) -> list[dict]:
        return list(self._get_all("teams", seasons=seasons))

    def stadiums(self, seasons: list[int] | None = None) -> list[dict]:
        return list(self._get_all("stadiums", seasons=seasons))

    def group_standings(self, seasons: list[int] | None = None) -> list[dict]:
        return list(self._get_all("group_standings", seasons=seasons))

    def matches(
        self,
        seasons: list[int] | None = None,
        match_ids: list[int] | None = None,
        team_ids: list[int] | None = None,
    ) -> list[dict]:
        return list(
            self._get_all(
                "matches",
                seasons=seasons,
                match_ids=match_ids,
                team_ids=team_ids,
            )
        )

    def odds(
        self,
        seasons: list[int] | None = None,
        match_ids: list[int] | None = None,
    ) -> list[dict]:
        return list(self._get_all("odds", seasons=seasons, match_ids=match_ids))

    def players(
        self,
        seasons: list[int] | None = None,
        team_ids: list[int] | None = None,
        search: str | None = None,
    ) -> list[dict]:
        return list(
            self._get_all("players", seasons=seasons, team_ids=team_ids, search=search)
        )

    def rosters(
        self,
        seasons: list[int] | None = None,
        team_ids: list[int] | None = None,
    ) -> list[dict]:
        return list(self._get_all("rosters", seasons=seasons, team_ids=team_ids))

    def match_lineups(
        self,
        match_ids: list[int] | None = None,
        team_ids: list[int] | None = None,
    ) -> list[dict]:
        return list(
            self._get_all("match_lineups", match_ids=match_ids, team_ids=team_ids)
        )

    def match_events(self, match_ids: list[int] | None = None) -> list[dict]:
        return list(self._get_all("match_events", match_ids=match_ids))

    def player_match_stats(
        self,
        match_ids: list[int] | None = None,
        team_ids: list[int] | None = None,
    ) -> list[dict]:
        return list(
            self._get_all(
                "player_match_stats", match_ids=match_ids, team_ids=team_ids
            )
        )

    def team_match_stats(self, match_ids: list[int] | None = None) -> list[dict]:
        return list(self._get_all("team_match_stats", match_ids=match_ids))

    def match_shots(self, match_ids: list[int] | None = None) -> list[dict]:
        return list(self._get_all("match_shots", match_ids=match_ids))

    def match_momentum(self, match_ids: list[int] | None = None) -> list[dict]:
        return list(self._get_all("match_momentum", match_ids=match_ids))

    def match_team_form(self, match_ids: list[int] | None = None) -> list[dict]:
        return list(self._get_all("match_team_form", match_ids=match_ids))

    def futures(self, seasons: list[int] | None = None) -> list[dict]:
        return list(self._get_all("odds/futures", seasons=seasons))

    # ------------------------------------------------------------------
    # Single-match convenience fetchers (used by live engine)
    # ------------------------------------------------------------------

    def get_match(self, match_id: int) -> dict:
        matches = self.matches(match_ids=[match_id])
        if not matches:
            raise ValueError(f"Match {match_id} not found")
        return matches[0]

    def get_live_events(self, match_id: int) -> list[dict]:
        return self.match_events(match_ids=[match_id])

    def get_live_shots(self, match_id: int) -> list[dict]:
        return self.match_shots(match_ids=[match_id])

    def get_live_momentum(self, match_id: int) -> list[dict]:
        return self.match_momentum(match_ids=[match_id])

    def get_team_stats(self, match_id: int) -> list[dict]:
        return self.team_match_stats(match_ids=[match_id])

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_all(
        self,
        endpoint: str,
        seasons: list[int] | None = None,
        match_ids: list[int] | None = None,
        team_ids: list[int] | None = None,
        player_ids: list[int] | None = None,
        search: str | None = None,
    ) -> Generator[dict, None, None]:
        """Yield every record from a paginated endpoint."""
        params: dict[str, Any] = {"per_page": _DEFAULT_PER_PAGE}
        if seasons:
            params["seasons[]"] = seasons
        if match_ids:
            params["match_ids[]"] = match_ids
        if team_ids:
            params["team_ids[]"] = team_ids
        if player_ids:
            params["player_ids[]"] = player_ids
        if search:
            params["search"] = search

        cursor: int | None = None
        while True:
            if cursor is not None:
                params["cursor"] = cursor
            data = self._get(endpoint, params)
            records = data.get("data", [])
            yield from records
            meta = data.get("meta", {})
            cursor = meta.get("next_cursor")
            if cursor is None:
                break

    def _get(self, endpoint: str, params: dict) -> dict:
        elapsed = time.monotonic() - self._last_call
        if elapsed < self._req_delay:
            time.sleep(self._req_delay - elapsed)

        url = f"{BASE_URL}/{endpoint}"
        resp = self._session.get(url, params=params, timeout=30)
        self._last_call = time.monotonic()

        if resp.status_code == 429:
            retry_after = int(resp.headers.get("Retry-After", 5))
            time.sleep(retry_after)
            return self._get(endpoint, params)

        resp.raise_for_status()
        return resp.json()
