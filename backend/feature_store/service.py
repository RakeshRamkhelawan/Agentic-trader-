from typing import List, Dict, Any
from datetime import datetime
from backend.feature_store.registry import FeatureRegistry

class FeatureService:
    """
    Service to retrieve feature values.
    Enforces 'Point-in-Time Correctness' to prevent data leakage.
    """
    
    def __init__(self, db_client: Any, registry: FeatureRegistry = None):
        self.db_client = db_client
        self.registry = registry or FeatureRegistry()

    def get_features(
        self, 
        symbols: List[str], 
        feature_names: List[str], 
        timestamp: datetime
    ) -> Dict[str, Dict[str, float]]:
        """
        Get feature values for a specific point in time.
        
        Args:
            symbols: List of symbols (e.g. ['BTC-EUR'])
            feature_names: List of features to retrieve
            timestamp: The cutoff time. ONLY data known before this time is used.
        """
        # Validate features exist
        for name in feature_names:
            if not self.registry.get_feature(name):
                raise ValueError(f"Unknown feature: {name}")

        # Delegate query to DB client with strict cutoff_time
        # This ensures we don't accidentally read future data during a backtest
        return self.db_client.query_features(
            symbols=symbols,
            features=feature_names,
            cutoff_time=timestamp
        )
