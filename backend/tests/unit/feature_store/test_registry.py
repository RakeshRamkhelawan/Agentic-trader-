import os
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest
import yaml

# We importeren classes die nog niet bestaan (TDD)
from backend.feature_store.registry import FeatureDefinition, FeatureRegistry
from backend.feature_store.service import FeatureService

# --- FIXTURES ---

@pytest.fixture
def sample_feature_yaml(tmp_path):
    """Creates a temporary features.yaml file."""
    content = """
    features:
      - name: rsi_14
        description: Relative Strength Index (14 periods)
        category: technical
        window_seconds: 60
        
      - name: vol_5m
        description: Volatility over 5 minutes
        category: statistical
        window_seconds: 300
    """
    path = tmp_path / "features.yaml"
    path.write_text(content, encoding='utf-8')
    return str(path)

# --- TESTS: Feature Registry (A.3.1) ---

def test_load_feature_definitions(sample_feature_yaml):
    """Happy Path: Load features correctly from YAML."""
    registry = FeatureRegistry(config_path=sample_feature_yaml)
    
    assert len(registry.list_features()) == 2
    
    rsi = registry.get_feature("rsi_14")
    assert rsi.name == "rsi_14"
    assert rsi.category == "technical"
    assert rsi.window_seconds == 60

def test_load_invalid_yaml(tmp_path):
    """Unhappy Path: Invalid YAML format."""
    bad_yaml = tmp_path / "bad.yaml"
    bad_yaml.write_text("features: [broken", encoding='utf-8')
    
    with pytest.raises(Exception): # Specific exception later
        FeatureRegistry(config_path=str(bad_yaml))

def test_get_unknown_feature(sample_feature_yaml):
    """Unhappy Path: Requesting non-existent feature."""
    registry = FeatureRegistry(config_path=sample_feature_yaml)
    assert registry.get_feature("unknown_feature") is None

# --- TESTS: Feature Service (A.3.2 Point-in-Time) ---

def test_point_in_time_correctness():
    """
    Test dat we geen data uit de toekomst lekken.
    Als we vragen om features op T=10:00, mogen we geen data van 10:01 gebruiken.
    """
    mock_db = MagicMock()
    service = FeatureService(db_client=mock_db)
    
    query_time = datetime(2024, 1, 1, 10, 0, 0)
    
    # Simuleer een call
    service.get_features(
        symbols=["BTC-EUR"],
        feature_names=["rsi_14"],
        timestamp=query_time
    )
    
    # Check de arguments die naar de DB gaan
    # De query moet een WHERE timestamp <= query_time bevatten
    # Omdat we de DB client mocken, checken we de call args
    mock_db.query_features.assert_called_once()
    call_args = mock_db.query_features.call_args[1] # kwargs
    
    assert call_args['cutoff_time'] == query_time
