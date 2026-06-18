import numpy as np
import tempfile, pytest
from pathlib import Path

def test_pmf_flat_roundtrip(tmp_path, monkeypatch):
    """Test that PMF can be stored and retrieved correctly."""
    import wc2026.data.storage as storage
    monkeypatch.setattr(storage, "_PMF_LAYERS_DIR", tmp_path / "pmf_layers")

    pmf = np.random.dirichlet(np.ones(64)).reshape(8, 8).astype(np.float64)
    storage.append_pmf_layer({
        "match_id": 99, "prediction_run_id": "test-run", "prediction_timestamp": "2026-06-18T00:00:00",
        "pmf_layer_name": "structural_composite", "home_lambda": 1.5, "away_lambda": 1.0,
        "rho": -0.05, "dispersion": None, "temperature": 1.15, "market_quality": 0.8,
        "source_odds_updated_at": None, "observed_at": None, "feature_asof_timestamp": None,
        "grid_shape": "8x8", "grid_mass": 1.0, "tail_mass_estimate": 0.0,
        "model_version": "test", "config_hash": "abc123", "pmf_flat": pmf, "season": 2026,
    })
    df = storage.load_pmf_layers(2026, match_id=99)
    assert len(df) == 1
    raw_bytes = df.iloc[0]["pmf_flat"]
    pmf_recovered = np.frombuffer(raw_bytes, dtype=np.float64).reshape(8, 8)
    np.testing.assert_array_almost_equal(pmf, pmf_recovered)

def test_pmf_sums_to_one(tmp_path, monkeypatch):
    import wc2026.data.storage as storage
    monkeypatch.setattr(storage, "_PMF_LAYERS_DIR", tmp_path / "pmf_layers")

    for _ in range(3):
        pmf = np.random.dirichlet(np.ones(225)).reshape(15, 15)
        storage.append_pmf_layer({
            "match_id": 1, "prediction_run_id": "r1", "prediction_timestamp": "2026-01-01",
            "pmf_layer_name": "structural_composite", "home_lambda": 1.3, "away_lambda": 1.0,
            "rho": -0.05, "dispersion": None, "temperature": 1.0, "market_quality": None,
            "source_odds_updated_at": None, "observed_at": None, "feature_asof_timestamp": None,
            "grid_shape": "15x15", "grid_mass": float(pmf.sum()), "tail_mass_estimate": 0.0,
            "model_version": "test", "config_hash": "abc", "pmf_flat": pmf, "season": 2026,
        })
    df = storage.load_pmf_layers(2026, match_id=1)
    assert len(df) == 3
    for _, row in df.iterrows():
        pmf_rec = np.frombuffer(row["pmf_flat"], dtype=np.float64).reshape(15, 15)
        assert pmf_rec.min() >= -1e-10
        assert abs(pmf_rec.sum() - 1.0) < 1e-5

def test_multiple_runs_both_persist(tmp_path, monkeypatch):
    import wc2026.data.storage as storage
    monkeypatch.setattr(storage, "_PMF_LAYERS_DIR", tmp_path / "pmf_layers")

    pmf = np.ones((3, 3)) / 9
    for run_id in ["run-1", "run-2"]:
        storage.append_pmf_layer({
            "match_id": 5, "prediction_run_id": run_id, "prediction_timestamp": "2026-01-01",
            "pmf_layer_name": "published", "home_lambda": 1.3, "away_lambda": 1.0,
            "rho": -0.05, "dispersion": None, "temperature": 1.0, "market_quality": None,
            "source_odds_updated_at": None, "observed_at": None, "feature_asof_timestamp": None,
            "grid_shape": "3x3", "grid_mass": 1.0, "tail_mass_estimate": 0.0,
            "model_version": "test", "config_hash": "abc", "pmf_flat": pmf, "season": 2026,
        })
    df = storage.load_pmf_layers(2026, match_id=5)
    assert len(df) == 2
    assert set(df["prediction_run_id"]) == {"run-1", "run-2"}
