"""
Signals module for prediction market intelligence.

Generates and manages market signals from analysis results.
"""

from src.signals.generator import (
    MarketSignal,
    SignalCategory,
    SignalGenerator,
    SignalIndicator,
    SignalType,
)

__all__ = [
    "SignalGenerator",
    "MarketSignal",
    "SignalType",
    "SignalCategory",
    "SignalIndicator",
]
