"""
Tests for IntelligentRegimeDetector.
"""

import pytest
from backend.core.ml.regime_detector import IntelligentRegimeDetector
from backend.core.schemas.ooda_types import MarketRegime

class TestIntelligentRegimeDetector:

    def setup_method(self):
        self.detector = IntelligentRegimeDetector()

    def test_missing_features_defaults_to_sideways(self):
        """Testing normalization default values giving a SIDEWAYS regime."""
        features = {}  # Empty dict
        regime = self.detector.detect_regime(features)
        assert regime == MarketRegime.SIDEWAYS

    def test_strongly_bullish_features(self):
        """High price momentum and RSI over 50 should trigger BULLish regime."""
        features = {
            "volatility_20d": 0.5,
            "price_momentum_10d": 0.3,  # strong positive momentum
            "rsi_14": 75.0,             # Overbought, but indicates bullishness
            "adx_14": 40.0,             # Strong trend strength
            "bb_width_norm": 0.8        # Widening bands
        }
        regime = self.detector.detect_regime(features)
        assert regime == MarketRegime.BULL

    def test_strongly_bearish_features(self):
        """Negative price momentum and low RSI should trigger BEARish regime."""
        features = {
            "volatility_20d": 0.6,
            "price_momentum_10d": -0.4, # strong negative momentum
            "rsi_14": 25.0,             # Oversold, but indicates bearishness
            "adx_14": 45.0,             # Strong trend strength
            "bb_width_norm": 0.9        # Widening bands
        }
        regime = self.detector.detect_regime(features)
        assert regime == MarketRegime.BEAR

    def test_weak_trend_forces_sideways(self):
        """Even with directional momentum, weak ADX and volatility force SIDEWAYS."""
        features = {
            "volatility_20d": 0.2,      # low volatility
            "price_momentum_10d": 0.2,  # slight positive momentum
            "rsi_14": 55.0,             # Neutral
            "adx_14": 15.0,             # Weak trend
            "bb_width_norm": 0.2        # Tight bands
        }
        regime = self.detector.detect_regime(features)
        assert regime == MarketRegime.SIDEWAYS

    def test_feature_normalization(self):
        """Verify internal limits on RSI and ADX scales do not break math boundaries."""
        features = {
            "rsi_14": 100.0,
            "adx_14": 100.0,
            "price_momentum_10d": 1.0
        }
        norm = self.detector._normalize_features(features)
        assert norm["rsi_14"] == 1.0
        assert norm["adx_14"] == 1.0

        features_zero = {
            "rsi_14": 0.0,
            "adx_14": 0.0
        }
        norm_zero = self.detector._normalize_features(features_zero)
        assert norm_zero["rsi_14"] == -1.0
        assert norm_zero["adx_14"] == 0.0
