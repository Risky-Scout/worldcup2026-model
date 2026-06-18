import numpy as np
import pytest
from wc2026.markets.canonical_grid import CanonicalGrid

@pytest.fixture
def simple_pmf():
    rng = np.random.default_rng(42)
    pmf = rng.dirichlet(np.ones(64)).reshape(8, 8)
    return pmf / pmf.sum()

def test_moneyline_identity_1x(simple_pmf):
    g = CanonicalGrid(simple_pmf)
    ml = g.moneyline()
    dc = g.double_chance()
    assert abs(dc["double_chance_1x"] - (ml["home_win"] + ml["draw"])) < 1e-10

def test_moneyline_identity_x2(simple_pmf):
    g = CanonicalGrid(simple_pmf)
    ml = g.moneyline()
    dc = g.double_chance()
    assert abs(dc["double_chance_x2"] - (ml["draw"] + ml["away_win"])) < 1e-10

def test_moneyline_identity_12(simple_pmf):
    g = CanonicalGrid(simple_pmf)
    ml = g.moneyline()
    dc = g.double_chance()
    assert abs(dc["double_chance_12"] - (1.0 - ml["draw"])) < 1e-10

def test_dnb_formula(simple_pmf):
    g = CanonicalGrid(simple_pmf)
    ml = g.moneyline()
    dnb = g.draw_no_bet()
    expected = ml["home_win"] / (ml["home_win"] + ml["away_win"])
    assert abs(dnb["draw_no_bet_home"] - expected) < 1e-10

def test_btts_formula(simple_pmf):
    g = CanonicalGrid(simple_pmf)
    btts = g.btts()
    expected = float(simple_pmf[1:, 1:].sum())
    assert abs(btts["btts_yes"] - expected) < 1e-10

def test_win_to_nil(simple_pmf):
    g = CanonicalGrid(simple_pmf)
    wtn = g.win_to_nil()
    expected = float(simple_pmf[1:, 0].sum())
    assert abs(wtn["win_to_nil_home"] - expected) < 1e-10

def test_expected_points(simple_pmf):
    g = CanonicalGrid(simple_pmf)
    ml = g.moneyline()
    ep = g.expected_points()
    assert abs(ep["expected_points_home"] - (3*ml["home_win"] + ml["draw"])) < 1e-10

def test_correct_score_not_renormalized(simple_pmf):
    g = CanonicalGrid(simple_pmf)
    cs = g.correct_score(20)
    total = sum(cs.values())
    assert total <= 1.0 + 1e-10  # not renormalized — may be less than 1

def test_other_score_probability(simple_pmf):
    g = CanonicalGrid(simple_pmf)
    cs = g.correct_score(20)
    osp = g.other_score_probability(20)
    assert abs(osp - (1.0 - sum(cs.values()))) < 1e-10

def test_ah_push_line_sums_to_one(simple_pmf):
    g = CanonicalGrid(simple_pmf)
    ah = g.asian_handicap([0.0])
    assert abs(ah["asian_handicap_home_0"] + ah["asian_handicap_away_0"] + ah["asian_handicap_push_0"] - 1.0) < 1e-10

def test_ah_quarter_line_settlement():
    # Artificial PMF where we know the outcome
    pmf = np.zeros((5, 5))
    pmf[2, 1] = 0.5  # home wins by 1
    pmf[1, 2] = 0.5  # away wins by 1
    g = CanonicalGrid(pmf)
    # AH +0.25 for home = half on AH 0.0, half on AH +0.5
    ah_025 = g.asian_handicap([0.25])
    ah_00 = g.asian_handicap([0.0])
    ah_05 = g.asian_handicap([0.5])
    # home at +0.25: avg of (home at 0.0) and (home at +0.5)
    expected = (ah_00["asian_handicap_home_0"] + ah_05["asian_handicap_home_0_5"]) / 2.0
    assert abs(ah_025["asian_handicap_home_0_25"] - expected) < 1e-10

def test_totals_sum():
    pmf = np.zeros((5, 5))
    pmf[1, 1] = 0.4   # 2 total goals
    pmf[2, 2] = 0.4   # 4 total goals
    pmf[0, 0] = 0.2   # 0 total goals
    g = CanonicalGrid(pmf)
    tots = g.totals([1.5, 2.5])
    assert abs(tots["over_1_5"] + tots["under_1_5"] + tots["push_1_5"] - 1.0) < 1e-9
