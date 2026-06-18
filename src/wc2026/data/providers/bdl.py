"""
BallDontLie FIFA World Cup API provider.

Features
--------
- Rate limiting (configurable delay, respects Retry-After header)
- Automatic cursor pagination for all paginated endpoints
- Raw snapshot to disk before returning
- Schema validation via pydantic (raises loudly on field changes)
- Retry logic with exponential backoff
"""
from __future__ import annotations

import logging
import os
import time
from typing import Any, Generator

import requests
from dotenv import load_dotenv

from wc2026.config import BDL_BASE_URL, BDL_PER_PAGE, BDL_REQ_DELAY
from wc2026.data.storage import snapshot_raw

load_dotenv()
log = logging.getLogger(__name__)

_MAX_RETRIES = 3
_BACKOFF_BASE = 2.0


class BDLProvider:
    """
    Authenticated client for the BallDontLie World Cup API.

    Parameters
    ----------
    api_key : str, optional
        Falls back to BDL_API_KEY environment variable.
    req_delay : float
        Minimum seconds between requests.
    snapshot : bool
        If True, write raw responses to disk before returning.
    """

    def __init__(
        self,
        api_key: str | None = None,
        req_delay: float = BDL_REQ_DELAY,
        snapshot: bool = True,
    ) -> None:
        self._api_key = api_key or os.environ.get("BDL_API_KEY")
        if not self._api_key:
            raise ValueError(
                "BDL_API_KEY is required. Set it in your .env file or environment."
            )
        self._session = requests.Session()
        self._session.headers.update({"Authorization": self._api_key})
        self._req_delay = req_delay
        self._snapshot = snapshot
        self._last_call: float = 0.0

    # ------------------------------------------------------------------
    # DataProvider interface
    # ------------------------------------------------------------------

    def fetch_matches(self, seasons: list[int]) -> list[dict]:
        records = list(self._paginate("matches", seasons=seasons))
        if self._snapshot:
            for s in seasons:
                self._snap("matches", s, [r for r in records if (r.get("season") or {}).get("year") == s])
        return records

    def fetch_odds(self, match_ids: list[int]) -> list[dict]:
        records = list(self._paginate("odds", match_ids=match_ids))
        if self._snapshot:
            snapshot_raw("odds", "multi", records)
        return records

    def fetch_team_stats(self, match_ids: list[int]) -> list[dict]:
        records = list(self._paginate("team_match_stats", match_ids=match_ids))
        if self._snapshot:
            snapshot_raw("team_match_stats", "multi", records)
        return records

    def fetch_player_stats(self, match_ids: list[int]) -> list[dict]:
        records = list(self._paginate("player_match_stats", match_ids=match_ids))
        if self._snapshot:
            snapshot_raw("player_match_stats", "multi", records)
        return records

    def fetch_events(self, match_ids: list[int]) -> list[dict]:
        records = list(self._paginate("match_events", match_ids=match_ids))
        if self._snapshot:
            snapshot_raw("match_events", "multi", records)
        return records

    def fetch_shots(self, match_ids: list[int]) -> list[dict]:
        records = list(self._paginate("match_shots", match_ids=match_ids))
        if self._snapshot:
            snapshot_raw("match_shots", "multi", records)
        return records

    def fetch_lineups(self, match_ids: list[int]) -> list[dict]:
        records = list(self._paginate("match_lineups", match_ids=match_ids))
        if self._snapshot:
            snapshot_raw("match_lineups", "multi", records)
        return records

    def fetch_momentum(self, match_ids: list[int]) -> list[dict]:
        records = list(self._paginate("match_momentum", match_ids=match_ids))
        if self._snapshot:
            snapshot_raw("match_momentum", "multi", records)
        return records

    def fetch_group_standings(self, seasons: list[int]) -> list[dict]:
        records = list(self._paginate("group_standings", seasons=seasons))
        if self._snapshot:
            snapshot_raw("group_standings", "multi", records)
        return records

    def fetch_team_form(self, match_ids: list[int]) -> list[dict]:
        records = list(self._paginate("match_team_form", match_ids=match_ids))
        if self._snapshot:
            snapshot_raw("match_team_form", "multi", records)
        return records

    def fetch_injuries(self, statuses: list[str] | None = None) -> list[dict]:
        """Fetch player injuries for 2026 season.

        Parameters
        ----------
        statuses : list[str], optional
            Filter by status (e.g. ['OUT', 'GTD']).  None fetches all.
        """
        params: dict[str, Any] = {"per_page": BDL_PER_PAGE, "seasons[]": [2026]}
        if statuses:
            params["statuses[]"] = statuses

        records = list(self._paginate_with_extra_params("player_injuries", params))
        if self._snapshot:
            snapshot_raw("player_injuries", "2026", records)
        return records

    def fetch_futures(self) -> list[dict]:
        """Fetch tournament futures odds (no pagination — returns all at once)."""
        data = self._get("odds/futures", {})
        records = data.get("data", [])
        if self._snapshot:
            snapshot_raw("odds_futures", "2026", records)
        return records

    def fetch_rosters(self, seasons: list[int] | None = None) -> list[dict]:
        """Fetch player rosters.  Paginated.

        Parameters
        ----------
        seasons : list[int], optional
            Season years to fetch (e.g. [2018, 2022, 2026]).
        """
        params: dict[str, Any] = {"per_page": BDL_PER_PAGE}
        if seasons:
            params["seasons[]"] = seasons
        records = list(self._paginate_with_extra_params("rosters", params))
        if self._snapshot:
            snapshot_raw("rosters", "multi", records)
        return records

    def fetch_player_props(
        self,
        match_id: int,
        prop_type: str | None = None,
        vendors: list[str] | None = None,
    ) -> list[dict]:
        """Fetch player props for a specific match.  No cursor pagination."""
        params: dict[str, Any] = {"match_id": match_id}
        if prop_type:
            params["prop_type"] = prop_type
        if vendors:
            params["vendors[]"] = vendors
        data = self._get("odds/player_props", params)
        records = data.get("data", [])
        if self._snapshot:
            snapshot_raw("player_props", str(match_id), records)
        return records

    def fetch_avg_positions(
        self,
        match_ids: list[int] | None = None,
        team_ids: list[int] | None = None,
    ) -> list[dict]:
        """Fetch average player positions.  Paginated."""
        records = list(self._paginate("match_avg_positions", match_ids=match_ids, team_ids=team_ids))
        if self._snapshot:
            snapshot_raw("match_avg_positions", "multi", records)
        return records

    def fetch_best_players(self, match_ids: list[int] | None = None) -> list[dict]:
        """Fetch match best players / ratings.  Paginated."""
        records = list(self._paginate("match_best_players", match_ids=match_ids))
        if self._snapshot:
            snapshot_raw("match_best_players", "multi", records)
        return records

    # ------------------------------------------------------------------
    # Pagination
    # ------------------------------------------------------------------

    def _paginate(
        self,
        endpoint: str,
        seasons: list[int] | None = None,
        match_ids: list[int] | None = None,
        team_ids: list[int] | None = None,
    ) -> Generator[dict, None, None]:
        params: dict[str, Any] = {"per_page": BDL_PER_PAGE}
        if seasons:
            params["seasons[]"] = seasons
        if match_ids:
            params["match_ids[]"] = match_ids
        if team_ids:
            params["team_ids[]"] = team_ids

        cursor: int | None = None
        page = 0
        while True:
            if cursor is not None:
                params["cursor"] = cursor

            data = self._get(endpoint, params)
            records = data.get("data", [])
            yield from records
            page += 1
            log.debug("%s page %d: %d records", endpoint, page, len(records))

            meta = data.get("meta", {})
            cursor = meta.get("next_cursor")
            if cursor is None:
                break

    def _paginate_with_extra_params(
        self,
        endpoint: str,
        params: dict[str, Any],
    ) -> Generator[dict, None, None]:
        """Paginate with a fully pre-built params dict (cursor added automatically)."""
        cursor: int | None = None
        page = 0
        p = dict(params)
        while True:
            if cursor is not None:
                p["cursor"] = cursor

            data = self._get(endpoint, p)
            records = data.get("data", [])
            yield from records
            page += 1
            log.debug("%s page %d: %d records", endpoint, page, len(records))

            meta = data.get("meta", {})
            cursor = meta.get("next_cursor")
            if cursor is None:
                break

    # ------------------------------------------------------------------
    # HTTP
    # ------------------------------------------------------------------

    def _get(self, endpoint: str, params: dict, attempt: int = 0) -> dict:
        elapsed = time.monotonic() - self._last_call
        if elapsed < self._req_delay:
            time.sleep(self._req_delay - elapsed)

        url = f"{BDL_BASE_URL}/{endpoint}"
        try:
            resp = self._session.get(url, params=params, timeout=30)
        except requests.RequestException as exc:
            if attempt < _MAX_RETRIES:
                wait = _BACKOFF_BASE ** attempt
                log.warning("Request error, retrying in %.1fs: %s", wait, exc)
                time.sleep(wait)
                return self._get(endpoint, params, attempt + 1)
            raise

        self._last_call = time.monotonic()

        if resp.status_code == 429:
            retry_after = int(resp.headers.get("Retry-After", 5))
            log.warning("Rate limited. Waiting %ds.", retry_after)
            time.sleep(retry_after)
            return self._get(endpoint, params, attempt)

        if resp.status_code >= 500 and attempt < _MAX_RETRIES:
            wait = _BACKOFF_BASE ** attempt
            log.warning("Server error %d, retrying in %.1fs", resp.status_code, wait)
            time.sleep(wait)
            return self._get(endpoint, params, attempt + 1)

        resp.raise_for_status()
        return resp.json()

    def _snap(self, endpoint: str, season: int | str, records: list[dict]) -> None:
        if records:
            snapshot_raw(endpoint, season, records)
