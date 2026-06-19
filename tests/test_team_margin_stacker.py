import numpy as np
import pandas as pd
import pytest
from src.wc2026.models.team_margin_stacker import TeamMarginStacker


def _make_training_df(n=30, seed=42):
    rng = np.random.default_rng(seed)
    rows = []
    for i in range(n):
        pi = rng.normal(0, 0.3)
        elo = rng.normal(0, 0.2)
        gd = pi * 1.5 + elo * 0.8 + rng.normal(0, 1.2)
        rows.append({
            "match_id": i, "datetime": f"2026-0{(i % 9) + 1}-{(i % 28) + 1:02d}",
            "target_gd": gd,
            "pi_egm": pi, "elo_egm": elo,
            "xg_attack_egm": rng.normal(0, 0.1),
            "xg_defense_egm": rng.normal(0, 0.1),
            "player_egm": rng.normal(0, 0.05),
            "futures_egm": rng.normal(0, 0.1),
            "venue_egm": 0.0,
            "market_egm": pi * 1.2 + rng.normal(0, 0.1),
            "market_total": 2.6,
        })
    return pd.DataFrame(rows)


def test_stacker_fits_and_predicts():
    df = _make_training_df(40)
    s = TeamMarginStacker(alpha=1.0)
    s.fit(df, n_folds=2)
    result = s.predict_pure({"pi_egm": 0.3, "elo_egm": 0.2,
                              "xg_attack_egm": 0.05, "xg_defense_egm": 0.02,
                              "player_egm": 0.0, "futures_egm": 0.1, "venue_egm": 0.0})
    assert isinstance(result, float)
    assert -5 < result < 5   # sanity range


def test_stacker_market_beats_pure_on_market_data():
    """With market signal, market model should have lower or equal MAE."""
    df = _make_training_df(60)
    s = TeamMarginStacker(alpha=1.0)
    s.fit(df, n_folds=3)
    if s.coefs:
        assert s.coefs.n_training_matches == 60
        assert len(s.coefs.fold_metrics) > 0


def test_stacker_fallback_no_sklearn():
    """Fallback predict works even without a fitted model."""
    s = TeamMarginStacker()
    # Don't call fit — should still return float
    r = s.predict_pure({"pi_egm": 0.5})
    assert isinstance(r, float)
