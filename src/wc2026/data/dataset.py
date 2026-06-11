"""
DatasetBuilder — fetches, validates, normalises, and stores all BDL data.

Produces versioned Parquet tables from raw BDL responses.
All transformations are deterministic and logged.
Schema validation via pydantic runs on every record before flattening.
"""
from __future__ import annotations

import logging
import math
from datetime import datetime, timezone
from typing import Optional

import numpy as np
import pandas as pd
from pydantic import ValidationError

from wc2026.config import DATA_VERSION, DC_WEIGHT_XI
from wc2026.data.providers.base import DataProvider
from wc2026.data.schemas import (
    Match,
    MatchEvent,
    MatchMomentum,
    MatchShot,
    MatchTeamForm,
    Odds,
    PlayerMatchStat,
    TeamMatchStat,
    parse_events,
    parse_matches,
    parse_momentum,
    parse_odds,
    parse_shots,
    parse_team_stats,
)
from wc2026.data.storage import write_table

log = logging.getLogger(__name__)

# These host nations get a soft home advantage in the neutral-venue flag
HOST_NATIONS = {"United States", "Canada", "Mexico"}


class DatasetBuilder:
    """
    Orchestrates fetching, validating, and storing all BDL data.

    Usage
    -----
    builder = DatasetBuilder(provider=BDLProvider())
    builder.run(seasons=[2018, 2022, 2026])
    """

    def __init__(
        self,
        provider: DataProvider,
        data_version: str = DATA_VERSION,
    ) -> None:
        self._provider = provider
        self._data_version = data_version

    def run(self, seasons: list[int]) -> dict[str, pd.DataFrame]:
        """Fetch everything, validate, flatten, write parquet. Return tables dict."""
        log.info("Starting dataset build for seasons %s, version=%s", seasons, self._data_version)

        # ── 1. Matches ──────────────────────────────────────────────────
        raw_matches = self._provider.fetch_matches(seasons)
        log.info("Fetched %d raw match records.", len(raw_matches))
        matches = self._validate_matches(raw_matches)
        match_ids = [m.id for m in matches if m.status == "completed"]
        all_match_ids = [m.id for m in matches]

        matches_df = self._flatten_matches(matches)
        write_table("matches", matches_df, self._data_version)
        log.info("Matches table: %d rows.", len(matches_df))

        # ── 2. Team stats ────────────────────────────────────────────────
        raw_stats = self._provider.fetch_team_stats(match_ids) if match_ids else []
        stats = self._validate_batch(raw_stats, TeamMatchStat, "team_stats")
        stats_df = self._flatten_team_stats(stats, matches_df)
        write_table("team_stats", stats_df, self._data_version)
        log.info("Team stats table: %d rows.", len(stats_df))

        # ── 3. Shots ─────────────────────────────────────────────────────
        raw_shots = self._provider.fetch_shots(match_ids) if match_ids else []
        shots = self._validate_batch(raw_shots, MatchShot, "shots")
        shots_df = self._flatten_shots(shots)
        write_table("shots", shots_df, self._data_version)

        # ── 4. Events ────────────────────────────────────────────────────
        raw_events = self._provider.fetch_events(match_ids) if match_ids else []
        events = self._validate_batch(raw_events, MatchEvent, "events")
        events_df = self._flatten_events(events)
        write_table("events", events_df, self._data_version)

        # ── 5. Momentum ──────────────────────────────────────────────────
        raw_mom = self._provider.fetch_momentum(match_ids) if match_ids else []
        mom = self._validate_batch(raw_mom, MatchMomentum, "momentum")
        mom_df = pd.DataFrame([m.model_dump() for m in mom]) if mom else pd.DataFrame()
        write_table("momentum", mom_df, self._data_version)

        # ── 6. Odds ──────────────────────────────────────────────────────
        raw_odds = self._provider.fetch_odds(all_match_ids) if all_match_ids else []
        odds = self._validate_batch(raw_odds, Odds, "odds")
        odds_df = self._flatten_odds(odds)
        write_table("odds", odds_df, self._data_version)

        # ── 6b. Markets sub-array (correct_score, BTTS, spread, DC, DNB, totals) ──
        markets_df = self._flatten_markets(raw_odds)
        write_table("markets", markets_df, self._data_version)
        correct_score_df = markets_df[markets_df["market_type"] == "correct_score"].copy() if not markets_df.empty else pd.DataFrame()
        write_table("correct_score_odds", correct_score_df, self._data_version)
        n_cs = len(correct_score_df)
        log.info("Markets table: %d rows. Correct-score rows: %d", len(markets_df), n_cs)

        # ── 7. Group standings ──────────────────────────────────────────
        raw_gs = self._provider.fetch_group_standings(seasons)
        gs_df = pd.DataFrame(raw_gs) if raw_gs else pd.DataFrame()
        write_table("group_standings", gs_df, self._data_version)

        # ── 8. Team form ─────────────────────────────────────────────────
        raw_form = self._provider.fetch_team_form(all_match_ids) if all_match_ids else []
        form_df = pd.DataFrame(raw_form) if raw_form else pd.DataFrame()
        write_table("team_form", form_df, self._data_version)

        log.info("Dataset build complete. Version=%s", self._data_version)
        return {
            "matches": matches_df,
            "team_stats": stats_df,
            "shots": shots_df,
            "events": events_df,
            "momentum": mom_df,
            "odds": odds_df,
            "markets": markets_df,
            "correct_score_odds": correct_score_df,
            "group_standings": gs_df,
            "team_form": form_df,
        }

    # -----------------------------------------------------------------------
    # Validation helpers
    # -----------------------------------------------------------------------

    def _validate_matches(self, records: list[dict]) -> list[Match]:
        valid, invalid = [], 0
        for r in records:
            try:
                valid.append(Match.model_validate(r))
            except ValidationError as exc:
                log.warning("Match validation failed (id=%s): %s", r.get("id"), exc)
                invalid += 1
        if invalid:
            log.warning("%d match records failed validation.", invalid)
        return valid

    def _validate_batch(self, records: list[dict], model_cls, name: str):
        valid, invalid = [], 0
        for r in records:
            try:
                valid.append(model_cls.model_validate(r))
            except ValidationError as exc:
                log.warning("%s validation failed: %s", name, exc)
                invalid += 1
        if invalid:
            log.warning("%d %s records failed validation.", invalid, name)
        return valid

    # -----------------------------------------------------------------------
    # Flattening helpers
    # -----------------------------------------------------------------------

    def _flatten_matches(self, matches: list[Match]) -> pd.DataFrame:
        now = datetime.now(timezone.utc)
        rows = []
        for m in matches:
            home_name = m.home_team.name if m.home_team else None
            away_name = m.away_team.name if m.away_team else None
            season_year = m.season.year if m.season else None
            stage_name = m.stage.name if m.stage else None
            group_name = m.group.name if m.group else None
            stadium_name = m.stadium.name if m.stadium else None
            stadium_country = m.stadium.country if m.stadium else None

            # Neutral venue: True unless home team is a host nation
            is_neutral = int(home_name not in HOST_NATIONS) if home_name else 1

            # Time-decay weight
            match_dt = _parse_dt(m.datetime)
            weight = _decay_weight(match_dt, now) if match_dt else 1.0

            rows.append({
                "match_id": m.id,
                "match_number": m.match_number,
                "match_datetime": m.datetime,
                "status": m.status,
                "season": season_year,
                "stage": stage_name,
                "group": group_name,
                "stadium": stadium_name,
                "stadium_country": stadium_country,
                "home_team": home_name,
                "away_team": away_name,
                "home_goals": m.home_score,
                "away_goals": m.away_score,
                "first_half_home": m.first_half_home_score,
                "first_half_away": m.first_half_away_score,
                "has_extra_time": m.has_extra_time or False,
                "has_penalty_shootout": m.has_penalty_shootout or False,
                "home_score_penalties": m.home_score_penalties,
                "away_score_penalties": m.away_score_penalties,
                "is_neutral": is_neutral,
                "match_weight": weight,
                "home_formation": m.home_formation,
                "away_formation": m.away_formation,
            })

        df = pd.DataFrame(rows)
        if not df.empty:
            df["match_datetime"] = pd.to_datetime(df["match_datetime"], utc=True, errors="coerce")
            df = df.sort_values("match_datetime").reset_index(drop=True)
        return df

    def _flatten_team_stats(
        self, stats: list[TeamMatchStat], matches_df: pd.DataFrame
    ) -> pd.DataFrame:
        if not stats:
            return pd.DataFrame()
        rows = [s.model_dump() for s in stats]
        df = pd.DataFrame(rows)
        # Join team names from matches
        if not matches_df.empty and "match_id" in df.columns:
            home_map = matches_df.set_index("match_id")["home_team"].to_dict()
            away_map = matches_df.set_index("match_id")["away_team"].to_dict()
            df["team_name"] = df.apply(
                lambda r: home_map.get(r["match_id"]) if r["is_home"] else away_map.get(r["match_id"]),
                axis=1,
            )
        return df

    def _flatten_shots(self, shots: list[MatchShot]) -> pd.DataFrame:
        if not shots:
            return pd.DataFrame()
        return pd.DataFrame([s.model_dump() for s in shots])

    def _flatten_events(self, events: list[MatchEvent]) -> pd.DataFrame:
        if not events:
            return pd.DataFrame()
        rows = []
        for e in events:
            d = e.model_dump(exclude={"player", "assist_player", "player_in", "player_out"})
            d["player_id"] = e.player.id if e.player else None
            d["player_name"] = e.player.name if e.player else None
            d["assist_player_id"] = e.assist_player.id if e.assist_player else None
            d["player_in_id"] = e.player_in.id if e.player_in else None
            d["player_out_id"] = e.player_out.id if e.player_out else None
            rows.append(d)
        return pd.DataFrame(rows)

    def _flatten_odds(self, odds: list[Odds]) -> pd.DataFrame:
        """Flatten to one row per (match_id, vendor) with core 1X2 and totals."""
        if not odds:
            return pd.DataFrame()
        rows = []
        for o in odds:
            rows.append({
                "odds_id": o.id,
                "match_id": o.match_id,
                "vendor": o.vendor,
                "moneyline_home": o.moneyline_home_odds,
                "moneyline_draw": o.moneyline_draw_odds,
                "moneyline_away": o.moneyline_away_odds,
                "total_value": o.total_value,
                "total_over_odds": o.total_over_odds,
                "total_under_odds": o.total_under_odds,
                "spread_home_value": o.spread_home_value,
                "spread_home_odds": o.spread_home_odds,
                "spread_away_value": o.spread_away_value,
                "spread_away_odds": o.spread_away_odds,
                "updated_at": o.updated_at,
            })
        return pd.DataFrame(rows)

    def _flatten_markets(self, raw_odds: list[dict]) -> pd.DataFrame:
        """
        Parse the nested markets[] sub-array from BDL odds records.

        Produces one row per (match_id, vendor, market_type, period, outcome).
        Captures: correct_score (type=correct_score), btts, spread, double_chance,
        draw_no_bet, and per-line totals.
        """
        rows = []
        for raw in raw_odds:
            match_id = raw.get("match_id")
            vendor = raw.get("vendor", "unknown")
            updated_at = raw.get("updated_at")
            for mkt in raw.get("markets", []):
                mkt_type = mkt.get("type", "")
                mkt_name = mkt.get("name", "")
                mkt_period = mkt.get("period", "match")
                mkt_scope = mkt.get("scope", "match")
                line_value = mkt.get("line_value")

                if mkt_period != "match":
                    continue  # Skip first-half, second-half markets for now

                for oc in mkt.get("outcomes", []):
                    oc_name = oc.get("name", "")
                    oc_type = oc.get("type", "")
                    american = oc.get("american_odds")
                    decimal = oc.get("decimal_odds")
                    oc_line = oc.get("line_value")

                    # Parse correct score: name like "1-0", "2-1"
                    h_goals, a_goals = None, None
                    if mkt_type == "correct_score" and oc_type == "score":
                        parts = oc_name.strip().split("-")
                        if len(parts) == 2:
                            try:
                                h_goals = int(parts[0])
                                a_goals = int(parts[1])
                            except (ValueError, TypeError):
                                pass

                    rows.append({
                        "match_id": match_id,
                        "vendor": vendor,
                        "market_type": mkt_type,
                        "market_name": mkt_name,
                        "period": mkt_period,
                        "scope": mkt_scope,
                        "line_value": line_value,
                        "outcome_name": oc_name,
                        "outcome_type": oc_type,
                        "outcome_line": oc_line,
                        "american_odds": american,
                        "decimal_odds": decimal,
                        "h_goals": h_goals,
                        "a_goals": a_goals,
                        "updated_at": updated_at,
                    })
        if not rows:
            return pd.DataFrame()
        df = pd.DataFrame(rows)
        df["match_id"] = pd.to_numeric(df["match_id"], errors="coerce").astype("Int64")
        return df


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _parse_dt(dt_str: str | None) -> datetime | None:
    if not dt_str:
        return None
    try:
        return datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return None


def _decay_weight(match_dt: datetime, reference: datetime) -> float:
    """Exponential time-decay: half-life controlled by DC_WEIGHT_XI (per day)."""
    days_ago = max((reference - match_dt).total_seconds() / 86400, 0.0)
    return math.exp(-DC_WEIGHT_XI * days_ago)
