import pandas as pd
from datetime import datetime, timezone
from src.wc2026.features.player_strength import build_player_ratings

def _make_stats(player_id, team_id, xg=0.3, xa=0.2, mp=270, sot=3, kp=2):
    return {
        "player_id": player_id, "player_name": f"Player{player_id}",
        "team_id": team_id, "minutes_played": mp,
        "expected_goals": xg, "expected_assists": xa,
        "shots_on_target": sot, "key_passes": kp,
        "big_chances_created": 1, "big_chances_missed": 0,
        "tackles_won": 2, "interceptions": 1, "clearances": 0, "blocked_shots": 0,
        "duels_won": 3, "duels_lost": 2, "aerial_duels_won": 1, "aerial_duels_lost": 1,
        "fouls_committed": 1, "saves": 0, "saves_inside_box": 0, "high_claims": 0,
        "ball_recoveries": 2, "passes_accurate": 50, "passes_total": 60,
        "long_balls_accurate": 5, "long_balls_total": 8,
    }

def test_build_returns_ratings():
    df = pd.DataFrame([_make_stats(1, 10), _make_stats(2, 10, xg=0.1)])
    ratings = build_player_ratings(df)
    assert 1 in ratings
    assert 2 in ratings
    assert ratings[1].overall_value_per90 >= 0

def test_shrinkage_low_minutes():
    df = pd.DataFrame([_make_stats(1, 10, mp=30)])
    ratings = build_player_ratings(df)
    assert ratings[1].shrinkage_weight < 0.5   # low minutes → high uncertainty

def test_point_in_time_filter():
    now = datetime.now(timezone.utc)
    import time
    time.sleep(0.01)
    future_ts = datetime.now(timezone.utc)
    df = pd.DataFrame([{**_make_stats(1, 10), "observed_at": future_ts.isoformat()}])
    ratings = build_player_ratings(df, prediction_timestamp=now)
    assert 1 not in ratings   # future stats excluded
