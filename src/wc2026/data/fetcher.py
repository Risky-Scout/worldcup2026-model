"""
Fetches and disk-caches BDL data so repeated runs don't burn API quota.

Cache layout: one key per (resource, seasons_tuple, extra_ids_tuple).
TTL:
  - completed matches / shots / events: 30 days (immutable)
  - scheduled/live matches: 5 minutes
  - odds / momentum / team_form: 5 minutes
"""
from __future__ import annotations

import hashlib
import json
import os
import time
from pathlib import Path
from typing import Any

import diskcache

from wc2026.data.bdl_client import BDLClient

_CACHE_DIR = Path(os.environ.get("CACHE_DIR", Path.home() / ".cache" / "wc2026"))
_CACHE_DIR.mkdir(parents=True, exist_ok=True)

_TTL_STATIC = 60 * 60 * 24 * 30  # 30 days
_TTL_LIVE = 60 * 5               # 5 minutes


def _make_key(resource: str, **kwargs: Any) -> str:
    payload = json.dumps({"resource": resource, **kwargs}, sort_keys=True)
    return hashlib.sha1(payload.encode()).hexdigest()


class DataFetcher:
    """
    High-level data layer with transparent caching.

    All methods return plain Python lists of dicts exactly as the API
    returns them; serialization to DataFrames is handled by the preprocessor.

    Parameters
    ----------
    client : BDLClient
    cache_dir : Path, optional
    """

    def __init__(
        self,
        client: BDLClient | None = None,
        cache_dir: Path | None = None,
    ) -> None:
        self._client = client or BDLClient()
        self._cache = diskcache.Cache(str(cache_dir or _CACHE_DIR))

    # ------------------------------------------------------------------
    # Static / slow-changing resources
    # ------------------------------------------------------------------

    def teams(self, seasons: list[int] | None = None) -> list[dict]:
        key = _make_key("teams", seasons=seasons)
        return self._cached(key, _TTL_STATIC, lambda: self._client.teams(seasons))

    def stadiums(self, seasons: list[int] | None = None) -> list[dict]:
        key = _make_key("stadiums", seasons=seasons)
        return self._cached(key, _TTL_STATIC, lambda: self._client.stadiums(seasons))

    def rosters(self, seasons: list[int] | None = None) -> list[dict]:
        key = _make_key("rosters", seasons=seasons)
        return self._cached(key, _TTL_STATIC, lambda: self._client.rosters(seasons))

    # ------------------------------------------------------------------
    # Match data — TTL depends on status
    # ------------------------------------------------------------------

    def matches(
        self,
        seasons: list[int] | None = None,
        force_refresh: bool = False,
    ) -> list[dict]:
        key = _make_key("matches", seasons=seasons)
        ttl = _TTL_LIVE  # always refresh match list so statuses stay current
        if force_refresh:
            self._cache.delete(key)
        return self._cached(key, ttl, lambda: self._client.matches(seasons=seasons))

    def completed_matches(
        self, seasons: list[int] | None = None
    ) -> list[dict]:
        return [
            m for m in self.matches(seasons=seasons) if m.get("status") == "completed"
        ]

    def upcoming_matches(
        self, seasons: list[int] | None = None
    ) -> list[dict]:
        return [
            m for m in self.matches(seasons=seasons)
            if m.get("status") in ("scheduled", "in_progress")
        ]

    # ------------------------------------------------------------------
    # Per-match stats — cached forever once the match is complete
    # ------------------------------------------------------------------

    def team_match_stats(self, match_ids: list[int]) -> list[dict]:
        key = _make_key("team_match_stats", match_ids=sorted(match_ids))
        return self._cached(
            key, _TTL_STATIC, lambda: self._client.team_match_stats(match_ids)
        )

    def match_shots(self, match_ids: list[int]) -> list[dict]:
        key = _make_key("match_shots", match_ids=sorted(match_ids))
        return self._cached(
            key, _TTL_STATIC, lambda: self._client.match_shots(match_ids)
        )

    def match_events(self, match_ids: list[int]) -> list[dict]:
        key = _make_key("match_events", match_ids=sorted(match_ids))
        return self._cached(
            key, _TTL_STATIC, lambda: self._client.match_events(match_ids)
        )

    def group_standings(self, seasons: list[int] | None = None) -> list[dict]:
        key = _make_key("group_standings", seasons=seasons)
        return self._cached(
            key, _TTL_LIVE, lambda: self._client.group_standings(seasons)
        )

    def odds(
        self,
        match_ids: list[int] | None = None,
        seasons: list[int] | None = None,
    ) -> list[dict]:
        key = _make_key("odds", match_ids=match_ids, seasons=seasons)
        return self._cached(
            key,
            _TTL_LIVE,
            lambda: self._client.odds(seasons=seasons, match_ids=match_ids),
        )

    def futures(self, seasons: list[int] | None = None) -> list[dict]:
        key = _make_key("futures", seasons=seasons)
        return self._cached(key, _TTL_LIVE, lambda: self._client.futures(seasons))

    def match_team_form(self, match_ids: list[int]) -> list[dict]:
        key = _make_key("match_team_form", match_ids=sorted(match_ids))
        return self._cached(
            key, _TTL_STATIC, lambda: self._client.match_team_form(match_ids)
        )

    # Live resources — always fetch fresh
    def live_events(self, match_id: int) -> list[dict]:
        return self._client.get_live_events(match_id)

    def live_shots(self, match_id: int) -> list[dict]:
        return self._client.get_live_shots(match_id)

    def live_momentum(self, match_id: int) -> list[dict]:
        return self._client.get_live_momentum(match_id)

    def live_team_stats(self, match_id: int) -> list[dict]:
        return self._client.get_team_stats(match_id)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _cached(self, key: str, ttl: int, fetcher) -> Any:
        if key in self._cache:
            return self._cache[key]
        data = fetcher()
        self._cache.set(key, data, expire=ttl)
        return data

    def clear_cache(self) -> None:
        self._cache.clear()
