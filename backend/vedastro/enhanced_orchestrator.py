"""
Enhanced Tattva Orchestrator with Full VedAstro Integration

Integrates all Vedic astrology features:
- Ashtakavarga
- Vimshottari Dasha
- Yogas
- Avastas
- Sahams
- Pancha Pakshi
- Muhurtha
- Vargas
- Trading Signal Generation
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from .advanced_features import (
    AdvancedVedAstroFeatures,
    Avasta,
    MuhurthaData,
    PanchaPakshiData,
    Yoga,
)
from .connector import VedAstroConfig
from .enhanced_connector import EnhancedVedAstroConnector
from .trading_signals import AgentPromptBuilder, TradingSignal, TradingSignalGenerator

logger = logging.getLogger(__name__)


@dataclass
class CompleteAstroAnalysis:
    """Complete astrological analysis for trading."""

    symbol: str
    timestamp: str

    # Core data
    kundli: dict[str, Any]
    transits: dict[str, Any]

    # Advanced features
    dasha: Any
    ashtakavarga: dict[str, Any]
    yogas: list[Yoga]
    avastas: dict[str, Avasta]
    sahams: dict[str, float]
    pancha_pakshi: PanchaPakshiData | None
    muhurtha: MuhurthaData | None
    vargas: dict[str, Any]

    # Trading signal
    trading_signal: TradingSignal

    # Agent prompts
    trading_prompt: str
    consciousness_prompt: str

    # Quick stats
    overall_score: float
    primary_recommendation: str


class EnhancedAstroOrchestrator:
    """
    Full Vedic Astrology Trading Orchestrator.

    Provides complete analysis and actionable signals for agents.
    """

    # Asset birth dates
    ASSET_BIRTHDAYS = {
        "BTC": datetime(2009, 1, 3, 18, 15),
        "ETH": datetime(2015, 7, 30, 15, 26),
        "AAPL": datetime(1980, 12, 12, 9, 30),
        "TSLA": datetime(2010, 6, 29, 9, 30),
        "GOOGL": datetime(2004, 8, 19, 9, 30),
        "MSFT": datetime(1986, 3, 13, 9, 30),
        "AMZN": datetime(1997, 5, 15, 9, 30),
        "NVDA": datetime(1999, 1, 22, 9, 30),
        "SPY": datetime(1993, 1, 22, 9, 30),
        "QQQ": datetime(1999, 3, 10, 9, 30),
    }

    def __init__(self, config: VedAstroConfig | None = None):
        """Initialize orchestrator with all components."""
        self.config = config or VedAstroConfig()

        # Initialize all calculators
        self.vedastro = EnhancedVedAstroConnector(self.config)
        self.advanced = AdvancedVedAstroFeatures()
        self.signal_generator = TradingSignalGenerator()
        self.prompt_builder = AgentPromptBuilder()

        # Caches
        self._kundli_cache: dict[str, dict] = {}
        self._analysis_cache: dict[str, CompleteAstroAnalysis] = {}

        logger.info("Enhanced Astro Orchestrator initialized with full VedAstro features")

    async def analyze_asset(
        self,
        symbol: str,
        current_price: float | None = None,
        current_date: datetime | None = None,
    ) -> CompleteAstroAnalysis:
        """
        Perform complete astrological analysis of an asset.

        Returns complete analysis with trading signals and agent prompts.
        """
        symbol = symbol.upper()
        current_date = current_date or datetime.now()

        # Check cache
        cache_key = f"{symbol}:{current_date.strftime('%Y%m%d%H')}"
        if cache_key in self._analysis_cache:
            return self._analysis_cache[cache_key]

        # 1. Get or calculate Kundli
        kundli = await self._get_kundli(symbol)

        # 2. Calculate transits
        transits = await self.vedastro.calculate_transits(current_date, kundli)

        # 3. Calculate all advanced features
        dasha = self.vedastro.calculate_vimshottari_dasha(kundli, current_date)
        ashtaka = self.vedastro.calculate_ashtakavarga(kundli)

        # 4. Advanced calculations
        yogas = self.advanced.calculate_all_yogas(kundli)
        avastas = self.advanced.calculate_all_avastas(kundli)
        sahams = self.vedastro.calculate_all_sahams(kundli)

        # 5. Pancha Pakshi
        moon_nakshatra = kundli.get("planets", {}).get("Moon", {}).get("nakshatra", "Ashwini")
        pancha_pakshi = self.advanced.calculate_pancha_pakshi(moon_nakshatra, current_date)

        # 6. Muhurtha
        muhurtha = self.advanced.calculate_muhurtha(current_date, kundli)

        # 7. Vargas
        vargas = self.advanced.calculate_all_vargas(kundli)

        # 8. Generate trading signal
        trading_signal = self.signal_generator.generate_signal(
            symbol=symbol,
            kundli=kundli,
            dasha=dasha,
            ashtaka=ashtaka,
            yogas=yogas,
            avastas=avastas,
            sahams=sahams,
            transits=transits,
            pancha_pakshi=pancha_pakshi,
            muhurtha=muhurtha,
            current_price=current_price,
        )

        # 9. Generate prompts
        trading_prompt = self.prompt_builder.build_trading_prompt(trading_signal)
        consciousness_prompt = self.prompt_builder.build_consciousness_prompt(
            kundli, yogas, dasha, transits
        )

        # Create complete analysis
        analysis = CompleteAstroAnalysis(
            symbol=symbol,
            timestamp=current_date.isoformat(),
            kundli=kundli,
            transits=transits,
            dasha=dasha,
            ashtakavarga=ashtaka,
            yogas=yogas,
            avastas=avastas,
            sahams=sahams,
            pancha_pakshi=pancha_pakshi,
            muhurtha=muhurtha,
            vargas=vargas,
            trading_signal=trading_signal,
            trading_prompt=trading_prompt,
            consciousness_prompt=consciousness_prompt,
            overall_score=trading_signal.strength_score,
            primary_recommendation=trading_signal.recommended_action,
        )

        # Cache
        self._analysis_cache[cache_key] = analysis

        return analysis

    async def _get_kundli(self, symbol: str) -> dict[str, Any]:
        """Get Kundli from cache or calculate."""
        if symbol in self._kundli_cache:
            return self._kundli_cache[symbol]

        birth_date = self.ASSET_BIRTHDAYS.get(symbol)
        if not birth_date:
            # Default to BTC if unknown
            birth_date = self.ASSET_BIRTHDAYS["BTC"]

        kundli = await self.vedastro.calculate_kundli(
            symbol=symbol,
            birth_date=birth_date,
            lat=40.7128,  # Default NY
            lon=-74.0060,
        )

        self._kundli_cache[symbol] = kundli
        return kundli

    def get_quick_signal(self, symbol: str) -> dict[str, Any]:
        """
        Get quick trading signal without full analysis.
        Uses cached data if available.
        """
        symbol = symbol.upper()
        cache_key = f"{symbol}:{datetime.now().strftime('%Y%m%d%H')}"

        if cache_key in self._analysis_cache:
            analysis = self._analysis_cache[cache_key]
            return {
                "symbol": symbol,
                "signal": analysis.trading_signal.signal.value,
                "confidence": analysis.trading_signal.confidence,
                "score": analysis.overall_score,
                "recommendation": analysis.primary_recommendation,
                "timeframe": analysis.trading_signal.timeframe.value,
                "risk_level": analysis.trading_signal.risk_level,
            }

        return {"error": "No cached analysis. Run analyze_asset() first."}

    def compare_assets(self, symbols: list[str]) -> dict[str, Any]:
        """
        Compare multiple assets and rank by astrological strength.
        """
        results = []

        for symbol in symbols:
            symbol = symbol.upper()
            cache_key = f"{symbol}:{datetime.now().strftime('%Y%m%d%H')}"

            if cache_key in self._analysis_cache:
                analysis = self._analysis_cache[cache_key]
                results.append(
                    {
                        "symbol": symbol,
                        "score": analysis.overall_score,
                        "signal": analysis.trading_signal.signal.value,
                        "dasha_lord": (
                            analysis.dasha.mahadasha_lord if analysis.dasha else "Unknown"
                        ),
                        "top_yoga": analysis.yogas[0].name if analysis.yogas else "None",
                    }
                )

        # Sort by score
        results.sort(key=lambda x: x["score"], reverse=True)

        return {
            "rankings": results,
            "best_asset": results[0]["symbol"] if results else None,
            "best_score": results[0]["score"] if results else 0,
        }

    def get_market_timing(self, symbol: str) -> dict[str, Any]:
        """
        Get detailed market timing information.
        """
        symbol = symbol.upper()
        cache_key = f"{symbol}:{datetime.now().strftime('%Y%m%d%H')}"

        if cache_key not in self._analysis_cache:
            return {"error": "No analysis available. Run analyze_asset() first."}

        analysis = self._analysis_cache[cache_key]

        return {
            "symbol": symbol,
            "current_dasha": {
                "mahadasha": analysis.dasha.mahadasha_lord if analysis.dasha else None,
                "antardasha": analysis.dasha.antardasha_lord if analysis.dasha else None,
                "pratyantardasha": analysis.dasha.pratyantardasha_lord if analysis.dasha else None,
            },
            "favorable_periods": {
                "pancha_pakshi": {
                    "activity": (
                        analysis.pancha_pakshi.current_activity if analysis.pancha_pakshi else None
                    ),
                    "is_favorable": (
                        analysis.pancha_pakshi.is_favorable_period
                        if analysis.pancha_pakshi
                        else False
                    ),
                },
                "muhurtha": {
                    "tithi": analysis.muhurtha.tithi if analysis.muhurtha else None,
                    "rating": analysis.muhurtha.rating if analysis.muhurtha else 0,
                    "is_favorable": analysis.muhurtha.is_favorable if analysis.muhurtha else False,
                },
            },
            "ashtakavarga": {
                "total_bindu": analysis.ashtakavarga.get("total_bindu", 0),
                "average": analysis.ashtakavarga.get("total_bindu", 0) / 12,
            },
        }

    def get_yoga_report(self, symbol: str) -> dict[str, Any]:
        """
        Get detailed Yoga report for asset.
        """
        symbol = symbol.upper()
        cache_key = f"{symbol}:{datetime.now().strftime('%Y%m%d%H')}"

        if cache_key not in self._analysis_cache:
            return {"error": "No analysis available."}

        analysis = self._analysis_cache[cache_key]

        yoga_list = []
        for yoga in analysis.yogas:
            yoga_list.append(
                {
                    "name": yoga.name,
                    "strength": yoga.strength,
                    "planets": yoga.planets,
                    "description": yoga.description,
                    "trading_significance": yoga.trading_significance,
                }
            )

        return {
            "symbol": symbol,
            "total_yogas": len(analysis.yogas),
            "strong_yogas": len([y for y in analysis.yogas if y.strength > 0.7]),
            "yogas": yoga_list,
            "top_wealth_yogas": [
                y.name for y in analysis.yogas if "Dhana" in y.name or "Lakshmi" in y.name
            ],
        }

    def clear_cache(self):
        """Clear all caches."""
        self._kundli_cache.clear()
        self._analysis_cache.clear()
        logger.info("Orchestrator cache cleared")

    def get_stats(self) -> dict[str, int]:
        """Get orchestrator statistics."""
        return {
            "kundli_cached": len(self._kundli_cache),
            "analysis_cached": len(self._analysis_cache),
            "assets_supported": len(self.ASSET_BIRTHDAYS),
        }


# Convenience function for quick usage
async def get_trading_recommendation(symbol: str, current_price: float | None = None) -> str:
    """
    Quick function to get trading recommendation.

    Usage:
        recommendation = await get_trading_recommendation("BTC", 65000)
        print(recommendation)
    """
    orchestrator = EnhancedAstroOrchestrator()
    analysis = await orchestrator.analyze_asset(symbol, current_price)

    return f"""
{'='*70}
VEDIC ASTROLOGY TRADING RECOMMENDATION: {symbol}
{'='*70}

SIGNAL: {analysis.trading_signal.signal.value.upper()}
CONFIDENCE: {analysis.trading_signal.confidence:.1f}%
SCORE: {analysis.overall_score:.1f}/100

DASHA PERIOD:
• Mahadasha: {analysis.dasha.mahadasha_lord if analysis.dasha else 'N/A'}
• Antardasha: {analysis.dasha.antardasha_lord if analysis.dasha else 'N/A'}

TOP YOGAS:
{chr(10).join([f'• {y.name} (strength: {y.strength:.2f})' for y in analysis.yogas[:3]]) if analysis.yogas else 'None'}

SAHAMS:
• Artha (Wealth): {analysis.sahams.get("artha", 0):.1f}°
• Labha (Profit): {analysis.sahams.get("labha", 0):.1f}°

ASHTAKAVARGA:
• Total Bindu: {analysis.ashtakavarga.get("total_bindu", 0)}/168
• Average: {analysis.ashtakavarga.get("total_bindu", 0) / 12:.1f}

RECOMMENDATION:
{analysis.primary_recommendation}

RISK LEVEL: {analysis.trading_signal.risk_level.upper()}
POSITION SIZE: {analysis.trading_signal.position_size_suggestion.upper()}
{'='*70}
"""
