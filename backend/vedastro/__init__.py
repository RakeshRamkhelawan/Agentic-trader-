"""
VedAstro Integration Module - Complete Vedic Astrology for Trading

Provides comprehensive Vedic astrology calculations using Swiss Ephemeris:

BASIC FEATURES:
- Planet positions (D1 Rasi)
- Nakshatras (27 lunar mansions)
- Vargas (D9 Navamsa)
- Transits (Gochara)

ADVANCED FEATURES:
- Ashtakavarga (Bindu scoring)
- Vimshottari Dasha (Time periods)
- Yogas (Planetary combinations)
- Avastas (Planetary states)
- Sahams (Financial points)
- Pancha Pakshi (Activity cycles)
- Muhurtha (Electional timing)
- Vargas D1-D60 (Divisional charts)

TRADING INTEGRATION:
- TradingSignalGenerator (Converts astrology to signals)
- AgentPromptBuilder (Creates LLM prompts)
- EnhancedAstroOrchestrator (Complete analysis pipeline)

Usage:
    from backend.vedastro import EnhancedAstroOrchestrator

    orchestrator = EnhancedAstroOrchestrator()
    analysis = await orchestrator.analyze_asset("BTC", 65000)

    print(analysis.trading_signal.signal)
    print(analysis.trading_prompt)  # For LLM agents
"""

# Advanced features
from .advanced_features import (
    AdvancedVedAstroFeatures,
    Avasta,
    MuhurthaData,
    PanchaPakshiData,
    PlanetState,
    VargaChart,
    Yoga,
)

# Core connectors
from .connector import VedAstroConfig, VedAstroConnector
from .enhanced_connector import DashaInfo, EnhancedVedAstroConnector

# Orchestration
from .enhanced_orchestrator import (
    CompleteAstroAnalysis,
    EnhancedAstroOrchestrator,
    get_trading_recommendation,
)

# Legacy components (kept for compatibility)
from .features import AstroFeatures, FeatureEngine
from .oracle import XGBoostOracle
from .orchestrator import TattvaOrchestrator

# Trading integration
from .trading_signals import (
    AgentPromptBuilder,
    SignalStrength,
    TimeFrame,
    TradingSignal,
    TradingSignalGenerator,
)

__version__ = "2.0.0"
__author__ = "VedAstro Trading Integration"

__all__ = [
    # Core
    "VedAstroConfig",
    "VedAstroConnector",
    "EnhancedVedAstroConnector",
    "DashaInfo",
    # Advanced features
    "AdvancedVedAstroFeatures",
    "Yoga",
    "Avasta",
    "PlanetState",
    "PanchaPakshiData",
    "MuhurthaData",
    "VargaChart",
    # Trading signals
    "TradingSignalGenerator",
    "AgentPromptBuilder",
    "TradingSignal",
    "SignalStrength",
    "TimeFrame",
    # Orchestration
    "EnhancedAstroOrchestrator",
    "CompleteAstroAnalysis",
    "get_trading_recommendation",
    # Legacy
    "AstroFeatures",
    "FeatureEngine",
    "XGBoostOracle",
    "TattvaOrchestrator",
]


def get_version():
    """Get module version."""
    return __version__


def list_features():
    """List all available features."""
    return {
        "Basic": [
            "Planet positions (D1 Rasi)",
            "Nakshatras (27 lunar mansions)",
            "Vargas (D9 Navamsa)",
            "Transits (Gochara)",
        ],
        "Advanced": [
            "Ashtakavarga (Bindu scoring)",
            "Vimshottari Dasha (Time periods)",
            "Yogas (Planetary combinations)",
            "Avastas (Planetary states)",
            "Sahams (Financial points)",
            "Pancha Pakshi (Activity cycles)",
            "Muhurtha (Electional timing)",
            "Vargas D10-D60 (Divisional charts)",
        ],
        "Trading": [
            "Trading signal generation",
            "Agent prompt building",
            "Complete analysis pipeline",
            "Multi-asset comparison",
            "Market timing analysis",
        ],
    }
