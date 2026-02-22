"""
VedAstro Integration Module

Provides Vedic astrology calculations via C# interop (pythonnet)
with HTTP fallback for containerized deployments.
"""

from .connector import VedAstroConfig, VedAstroConnector
from .features import AstroFeatures, FeatureEngine
from .oracle import XGBoostOracle
from .orchestrator import TattvaOrchestrator

__all__ = [
    "VedAstroConnector",
    "VedAstroConfig",
    "FeatureEngine",
    "AstroFeatures",
    "XGBoostOracle",
    "TattvaOrchestrator",
]
