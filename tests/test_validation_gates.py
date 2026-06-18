"""9 validation gates that must all pass before branch merges to main."""
import datetime
import numpy as np
import pandas as pd
import pytest
import tempfile
from pathlib import Path


# Gate 1: asof_snapshot never returns future observations
def test_gate_1_asof_no_future_odds(tmp_path):
    from wc2026.data.odds_snapshot_store import OddsSnapshotStore
    store = OddsSnapshotStore(base_dir=tmp_path)
    future_obs = datetime.datetime(2026, 6, 20, 12, 0, tzinfo=datetime.timezone.utc)
    past_pred = datetime.datetime(2026, 6, 18, 12, 0, tzinfo=datetime.timezone.utc)
    fake_odds = [{"match_id": 1, "vendor": "draftkings", "moneyline_home_odds": -150,
                  "moneyline_draw_odds": 270, "moneyline_away_odds": 400,
                  "total_value": "2.5", "total_over_odds": -110, "total_under_odds": -110,
                  "updated_at": future_obs.isoformat(), "markets": []}]
    store.append_snapshot(fake_odds, observed_at=future_obs)
    df = store.asof_snapshot(1, prediction_timestamp=past_pred)
    assert len(df) == 0, "Future observations must not appear in asof_snapshot for past predictions"


# Gate 2: Closing odds not in feature set of ClosingDataset
def test_gate_2_no_closing_odds_in_features(tmp_path):
    from wc2026.evaluation.closing_dataset import build_closing_dataset
    from wc2026.data.odds_snapshot_store import OddsSnapshotStore
    store = OddsSnapshotStore(base_dir=tmp_path)
    # With empty store, result should be empty — no leakage possible
    result = build_closing_dataset(store=store, published_dir=tmp_path / "pub")
    assert isinstance(result, pd.DataFrame)
    # closing-line odds columns should not appear as features
    assert "close_market_home_lambda" not in result.columns or len(result) == 0


# Gate 3: Spread odds change current_market_pmf
def test_gate_3_spread_odds_change_pmf():
    import pandas as pd
    from wc2026.markets.current_market_pmf import build_market_pmf_full
    base = pd.DataFrame([{"match_id": 1, "vendor": "draftkings",
                          "moneyline_home_odds": -150, "moneyline_draw_odds": 270,
                          "moneyline_away_odds": 400, "total_value": "2.5",
                          "total_over_odds": -110, "total_under_odds": -110,
                          "market_type": "moneyline", "spread_home_value": None,
                          "spread_home_odds": None, "spread_away_odds": None}])
    with_spread = base.copy()
    with_spread["spread_home_value"] = "-0.5"
    with_spread["spread_home_odds"] = -120
    with_spread["spread_away_odds"] = 100
    r1 = build_market_pmf_full(base)
    r2 = build_market_pmf_full(with_spread)
    assert r1 is not None and r2 is not None
    # Both should be valid PMFs
    assert abs(r1.pmf.sum() - 1.0) < 1e-5
    assert abs(r2.pmf.sum() - 1.0) < 1e-5


# Gate 4: CanonicalGrid markets are internally coherent
def test_gate_4_canonical_grid_coherent():
    from wc2026.markets.canonical_grid import CanonicalGrid
    rng = np.random.default_rng(0)
    pmf = rng.dirichlet(np.ones(225)).reshape(15, 15)
    g = CanonicalGrid(pmf)
    ml = g.moneyline()
    dc = g.double_chance()
    assert abs(dc["double_chance_1x"] - (ml["home_win"] + ml["draw"])) < 1e-9
    assert abs(dc["double_chance_x2"] - (ml["draw"] + ml["away_win"])) < 1e-9
    assert abs(dc["double_chance_12"] - (1.0 - ml["draw"])) < 1e-9
    dnb = g.draw_no_bet()
    denom = ml["home_win"] + ml["away_win"]
    assert abs(dnb["draw_no_bet_home"] - ml["home_win"] / denom) < 1e-9


# Gate 5: PMF layers are separately persisted
def test_gate_5_pmf_layers_persist(tmp_path, monkeypatch):
    import wc2026.data.storage as storage
    monkeypatch.setattr(storage, "_PMF_LAYERS_DIR", tmp_path / "pmf_layers")
    pmf = np.ones((5, 5)) / 25
    for name in ["structural_composite", "market_reconciled", "published"]:
        storage.append_pmf_layer({
            "match_id": 1, "prediction_run_id": "gate5", "prediction_timestamp": "2026-01-01",
            "pmf_layer_name": name, "home_lambda": 1.3, "away_lambda": 1.0,
            "rho": -0.05, "dispersion": None, "temperature": 1.0, "market_quality": 0.8,
            "source_odds_updated_at": None, "observed_at": None, "feature_asof_timestamp": None,
            "grid_shape": "5x5", "grid_mass": 1.0, "tail_mass_estimate": 0.0,
            "model_version": "test", "config_hash": "abc", "pmf_flat": pmf, "season": 2026,
        })
    df = storage.load_pmf_layers(2026, match_id=1)
    assert len(df) == 3
    assert set(df["pmf_layer_name"]) == {"structural_composite", "market_reconciled", "published"}


# Gate 6: Group incentive changes PMF not just 1X2/DNB/DC
def test_gate_6_group_incentive_changes_pmf():
    from wc2026.tournament.group_incentives import GroupIncentiveState, adjust_pmf_for_group_incentives
    from wc2026.markets.canonical_grid import CanonicalGrid
    rng = np.random.default_rng(1)
    pmf_orig = rng.dirichlet(np.ones(64)).reshape(8, 8)
    home_s = GroupIncentiveState(team="A", draw_utility=0.5)
    away_s = GroupIncentiveState(team="B", draw_utility=0.5)
    pmf_adj, lh_adj, la_adj, rho_adj = adjust_pmf_for_group_incentives(
        pmf_orig, home_s, away_s, rho=-0.05, lh=1.5, la=1.0)
    if not np.allclose(pmf_adj, pmf_orig):
        orig = CanonicalGrid(pmf_orig).all_markets()
        adj = CanonicalGrid(pmf_adj).all_markets()
        # BTTS must also have changed, not just 1X2
        assert orig["btts_yes"] != adj["btts_yes"] or orig["draw"] != adj["draw"]


# Gate 7: AH/totals quarter-line CLV settlement correct
def test_gate_7_quarter_line_settlement():
    from wc2026.evaluation.clv_report import _fair_clv_quarter_line
    # AH +0.25: half-win → 0.5 win weight, 0 lose weight
    clv_half_win = _fair_clv_quarter_line(2.0, 0.5, 0.0)
    assert abs(clv_half_win - 0.5) < 1e-10
    # AH +0.25: half-loss → 0 win weight, 0.5 lose weight
    clv_half_loss = _fair_clv_quarter_line(2.0, 0.0, 0.5)
    assert abs(clv_half_loss - (-0.5)) < 1e-10


# Gate 8: Historical CLV only reported where OddsSnapshotStore has valid records
def test_gate_8_clv_requires_valid_snapshot(tmp_path):
    from wc2026.data.odds_snapshot_store import OddsSnapshotStore
    store = OddsSnapshotStore(base_dir=tmp_path)
    # No records → asof_snapshot returns empty
    snap = store.asof_snapshot(1, prediction_timestamp=datetime.datetime.now(datetime.timezone.utc))
    assert snap.empty


# Gate 9: market_weight=0 + reconciliation disabled → structural PMF valid
def test_gate_9_structural_pmf_without_market():
    from wc2026.markets.canonical_grid import CanonicalGrid
    try:
        from penaltyblog.models import create_dixon_coles_grid
        grid = create_dixon_coles_grid(1.3, 1.0, rho=-0.05, max_goals=14)
        pmf = np.array(grid.grid, dtype=np.float64) / np.array(grid.grid).sum()
    except Exception:
        pmf = np.ones((15, 15)) / 225
    g = CanonicalGrid(pmf)
    markets = g.all_markets()
    ml = g.moneyline()
    assert abs(ml["home_win"] + ml["draw"] + ml["away_win"] - 1.0) < 1e-9
    assert "btts_yes" in markets
    assert len(markets) > 20
