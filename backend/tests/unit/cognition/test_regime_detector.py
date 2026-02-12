import pytest
from backend.services.cognitive_orchestrator import RegimeDetector, MarketRegime

def test_detect_bull_market():
    """Happy Path: Price > SMA = Bull."""
    detector = RegimeDetector()
    # Price 110, SMA 100
    regime = detector.detect(price=110.0, sma_50=100.0, volatility=0.01)
    assert regime == MarketRegime.BULL

def test_detect_bear_market():
    """Happy Path: Price < SMA = Bear."""
    detector = RegimeDetector()
    regime = detector.detect(price=90.0, sma_50=100.0, volatility=0.01)
    assert regime == MarketRegime.BEAR

def test_detect_high_volatility():
    """Happy Path: High Volatility = CRASH/VOLATILE."""
    detector = RegimeDetector()
    # Prijs is hoog, maar volatiliteit is enorm (10%)
    regime = detector.detect(price=110.0, sma_50=100.0, volatility=0.10)
    assert regime == MarketRegime.VOLATILE
