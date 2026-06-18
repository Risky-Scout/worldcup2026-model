"""Tests for Pi rating system correctness."""
import numpy as np
import pandas as pd
import pytest


def _make_match_history():
    return pd.DataFrame([
        {
            "home_team": "Germany", "away_team": "Brazil",
            "home_goals": 7, "away_goals": 1,
            "match_datetime": "2014-07-08", "status": "completed",
        },
        {
            "home_team": "Argentina", "away_team": "Germany",
            "home_goals": 0, "away_goals": 1,
            "match_datetime": "2014-07-13", "status": "completed",
        },
        {
            "home_team": "Brazil", "away_team": "Argentina",
            "home_goals": 1, "away_goals": 0,
            "match_datetime": "2014-07-12", "status": "completed",
        },
    ])


def test_pi_api_correct_goal_difference():
    """PiRatingSystem receives goal_difference = home - away (single int)."""
    from penaltyblog.ratings import PiRatingSystem
    pi = PiRatingSystem()
    # Germany beats Brazil 7-1 → goal_diff = +6 for Germany
    pi.update_ratings("Germany", "Brazil", 6)
    assert pi.get_team_rating("Germany") > 0, "Germany should have positive rating after big win"
    assert pi.get_team_rating("Brazil") < 0, "Brazil should have negative rating after big loss"


def test_pi_team_ratings_structure():
    """team_ratings is Dict[str, Dict[str, float]] with 'home' and 'away' keys."""
    from penaltyblog.ratings import PiRatingSystem
    pi = PiRatingSystem()
    pi.update_ratings("Germany", "Brazil", 6)
    assert isinstance(pi.team_ratings, dict)
    for team, ratings in pi.team_ratings.items():
        assert isinstance(ratings, dict), f"Expected dict for {team}, got {type(ratings)}"
        assert "home" in ratings, f"Missing 'home' key for {team}"
        assert "away" in ratings, f"Missing 'away' key for {team}"


def test_pi_opponent_adjusted():
    """Beating a strong team gives more rating points than beating a weak team."""
    from penaltyblog.ratings import PiRatingSystem

    # System 1: Strong team is established; TeamA beats Strong barely
    pi1 = PiRatingSystem()
    pi1.update_ratings("Strong", "Weak", 10)   # establish Strong as very good
    pi1.update_ratings("TeamA", "Strong", 1)   # TeamA beats Strong by 1

    # System 2: TeamB beats Weak by same margin (no opponent history)
    pi2 = PiRatingSystem()
    pi2.update_ratings("TeamB", "Weak", 1)

    gain_vs_strong = pi1.get_team_rating("TeamA")
    gain_vs_weak = pi2.get_team_rating("TeamB")

    assert gain_vs_strong > gain_vs_weak, (
        f"Beating stronger team should give larger gain: "
        f"vs_strong={gain_vs_strong:.4f}, vs_weak={gain_vs_weak:.4f}"
    )


def test_pi_correct_gd_vs_broken_gd():
    """Demonstrate the bug: passing home_goals alone inflates Germany's rating."""
    from penaltyblog.ratings import PiRatingSystem

    # Correct: 7-1 → goal_diff = 6
    pi_correct = PiRatingSystem()
    pi_correct.update_ratings("Germany", "Brazil", 7 - 1)
    correct_rating = pi_correct.get_team_rating("Germany")

    # Broken: passes home_goals=7 as goal_diff (old bug)
    pi_broken = PiRatingSystem()
    pi_broken.update_ratings("Germany", "Brazil", 7)
    broken_rating = pi_broken.get_team_rating("Germany")

    assert broken_rating > correct_rating, "Broken code inflates Germany's rating"
    assert correct_rating > 0, "Correct code still gives Germany positive rating"


def test_pi_baseline_fit_predict():
    """PiRatingBaseline.predict_1x2 sums to 1.0."""
    from wc2026.models.baselines import PiRatingBaseline

    hist = _make_match_history()
    bl = PiRatingBaseline()
    bl.fit(hist)

    pred = bl.predict("Germany", "Argentina")
    pmf = pred.score_pmf
    assert abs(pmf.sum() - 1.0) < 1e-6, f"PMF should sum to 1, got {pmf.sum()}"

    hw = float(np.sum(np.tril(pmf, -1)))
    dr = float(np.trace(pmf))
    aw = float(np.sum(np.triu(pmf, 1)))
    total = hw + dr + aw
    assert abs(total - 1.0) < 1e-6, f"1X2 probs should sum to 1, got {total}"


def test_pi_baseline_pmf_valid():
    """PiRatingBaseline PMF has non-negative entries summing to 1."""
    from wc2026.models.baselines import PiRatingBaseline

    hist = _make_match_history()
    bl = PiRatingBaseline()
    bl.fit(hist)
    pred = bl.predict("Germany", "Brazil")
    pmf = pred.score_pmf

    assert pmf.min() >= -1e-10, f"PMF has negative entries: {pmf.min()}"
    assert abs(pmf.sum() - 1.0) < 1e-6, f"PMF sum is {pmf.sum()}"


def test_pi_baseline_model_name():
    """PiRatingBaseline has correct MODEL_NAME."""
    from wc2026.models.baselines import PiRatingBaseline
    bl = PiRatingBaseline()
    assert bl.MODEL_NAME == "pi_rating"


def test_composite_pi_correct_api():
    """_fit_pi returns positive composite rating for Germany after 7-1 win."""
    from wc2026.ratings.composite import CompositeTeamPrior

    hist = _make_match_history()
    hist["match_weight"] = 1.0
    hist["is_neutral"] = True

    # Use __new__ to avoid full __init__ (which requires data fetching)
    prior = CompositeTeamPrior.__new__(CompositeTeamPrior)
    result = prior._fit_pi(hist)

    assert "Germany" in result, "Germany should appear in Pi ratings"
    germany = result["Germany"]

    # Result should be a dict with composite/home/away/attack/defense
    assert isinstance(germany, dict), f"Expected dict, got {type(germany)}"
    for key in ("composite", "home", "away", "attack", "defense"):
        assert key in germany, f"Missing '{key}' in Germany Pi result"

    composite = germany["composite"]
    assert composite > 0, f"Germany should have positive Pi composite rating, got {composite}"


def test_composite_pi_richer_structure():
    """_fit_pi returns home/away keys that are floats."""
    from wc2026.ratings.composite import CompositeTeamPrior

    hist = _make_match_history()
    hist["match_weight"] = 1.0
    hist["is_neutral"] = True

    prior = CompositeTeamPrior.__new__(CompositeTeamPrior)
    result = prior._fit_pi(hist)

    for team, data in result.items():
        assert isinstance(data, dict), f"team_ratings[{team}] is not a dict"
        for key in ("composite", "home", "away"):
            assert isinstance(data[key], float), f"{team}[{key}] is not float: {data[key]}"
