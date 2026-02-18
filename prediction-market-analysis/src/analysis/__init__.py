"""
Analysis module for prediction market intelligence.

Provides analytical tools for:
- Maker/Taker spread analysis
- Volume trend detection
- Statistical hypothesis testing
"""

from src.analysis.maker_taker import MakerTakerAnalyzer, SpreadMetrics
from src.analysis.statistical_tests import StatisticalTestsFramework, TestResult
from src.analysis.volume_trends import VolumeMetrics, VolumeTrendsAnalyzer

__all__ = [
    "MakerTakerAnalyzer",
    "VolumeTrendsAnalyzer",
    "StatisticalTestsFramework",
    "SpreadMetrics",
    "VolumeMetrics",
    "TestResult",
]
