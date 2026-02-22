"""
Online Learning Module - River-based adaptive learning with ADWIN drift detection.

Philosophy:
Just as the mind learns from experience (Chitta/Vasanas), the trading system
must adapt its strategies based on market regime changes. ADWIN serves as
the "alertness" mechanism - detecting when the market has fundamentally
shifted and old patterns no longer apply.
"""

from backend.core.learning.online_learner import OnlineLearner
from backend.core.learning.drift_detector import ADWINDriftDetector
from backend.core.learning.strategy_adapter import StrategyWeightAdapter

__all__ = ["OnlineLearner", "ADWINDriftDetector", "StrategyWeightAdapter"]
