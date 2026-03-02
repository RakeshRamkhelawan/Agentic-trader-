"""
Machine Learning module for trading intelligence.

Features:
- Trade prediction models
- Pattern recognition
- Feature engineering
- Model training and inference
"""

from .features import FeatureEngineer
from .models import ModelManager
from .predictor import (
    ConfidenceLevel,
    PredictionResult,
    SignalDirection,
    TradePredictor,
    trade_predictor,
)

__all__ = [
    "TradePredictor",
    "PredictionResult",
    "SignalDirection",
    "ConfidenceLevel",
    "trade_predictor",
    "FeatureEngineer",
    "ModelManager",
]
