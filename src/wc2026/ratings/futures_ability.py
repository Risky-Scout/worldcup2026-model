"""
Futures-implied team ability from /fifa/worldcup/v1/odds/futures.

Process: de-vig futures market → infer latent strength as slow-moving prior.
Do not directly multiply match lambdas by raw title probability.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass
class FuturesAbility:
    team_id: int
    team_name: str
    market_type: str
    no_vig_probability: float
    log_strength_proxy: float   # log(no_vig_prob) - log(1/N) normalized
    vendor_count: int
    observed_at: str


def compute_futures_ability(
    futures_df: pd.DataFrame,
    market_type: str = "tournament_winner",
) -> dict[int, FuturesAbility]:
    """
    futures_df: from /odds/futures, columns: subject.id, subject.name,
    vendor, american_odds, decimal_odds, market_type, updated_at

    Returns dict: team_id -> FuturesAbility
    """
    if futures_df.empty:
        return {}

    # Filter to market type
    if "market_type" in futures_df.columns:
        df = futures_df[futures_df["market_type"] == market_type].copy()
    else:
        df = futures_df.copy()

    if df.empty:
        return {}

    # Get team IDs
    id_col = "subject_id" if "subject_id" in df.columns else None
    if id_col is None and "subject" in df.columns:
        # nested dict
        df["_tid"] = df["subject"].apply(lambda x: int(x.get("id", 0)) if isinstance(x, dict) else 0)
        df["_tname"] = df["subject"].apply(lambda x: str(x.get("name", "")) if isinstance(x, dict) else "")
    else:
        df["_tid"] = pd.to_numeric(df.get("subject_id", 0), errors="coerce").fillna(0).astype(int)
        df["_tname"] = df.get("subject_name", "")

    # De-vig per vendor per market_type
    results = {}
    for tid, grp in df.groupby("_tid"):
        if tid == 0:
            continue
        tname = grp["_tname"].iloc[0]
        vendors = grp.get("vendor", pd.Series(["unknown"] * len(grp)))

        per_vendor_probs = []
        for vendor, vgrp in grp.groupby(vendors):
            if "decimal_odds" in vgrp.columns:
                odds = pd.to_numeric(vgrp["decimal_odds"], errors="coerce").dropna()
                all_odds = pd.to_numeric(df[df["vendor"] == vendor]["decimal_odds"], errors="coerce").dropna()
            else:
                continue
            if len(odds) < 1 or len(all_odds) < 2:
                continue
            raw_probs = 1.0 / all_odds.values
            total = raw_probs.sum()
            if total < 1e-9:
                continue
            raw_this = (1.0 / odds.values).mean()
            no_vig_this = raw_this / total
            per_vendor_probs.append(float(no_vig_this))

        if not per_vendor_probs:
            continue

        avg_prob = float(np.mean(per_vendor_probs))
        n_teams = len(df["_tid"].unique())
        log_strength = float(np.log(max(avg_prob, 1e-6)) - np.log(1.0 / max(n_teams, 1)))

        results[int(tid)] = FuturesAbility(
            team_id=int(tid),
            team_name=str(tname),
            market_type=market_type,
            no_vig_probability=avg_prob,
            log_strength_proxy=log_strength,
            vendor_count=len(per_vendor_probs),
            observed_at=str(grp.get("updated_at", pd.Series([""])).iloc[0]) if "updated_at" in grp.columns else "",
        )

    return results
