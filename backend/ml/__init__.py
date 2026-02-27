"""
Machine Learning module for trading intelligence.

Features:
- Trade prediction models
- Pattern recognition
- Feature engineering
- Model training and inference
"""

from .predictor import TradePredictor, PredictionResult, SignalDirection, ConfidenceLevel, trade_predictor
from .features import FeatureEngineer
from .models import ModelManager

__all__ = [
    "TradePredictor",
    "PredictionResult",
    "SignalDirection",
    "ConfidenceLevel",
    "trade_predictor",
    "FeatureEngineer",
    "ModelManager",
]
