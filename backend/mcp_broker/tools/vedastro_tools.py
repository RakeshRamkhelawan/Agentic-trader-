"""
VedAstro MCP Tools.

Exposeert V17 VedAstro functionaliteit als MCP tools.
"""

import logging
from typing import Any

from mcp.server.fastmcp import Context

from backend.mcp_broker.resilience import circuit_breaker, vedastro_retry

logger = logging.getLogger(__name__)

# Initialize VedAstro components (lazy loading)
_astro_orchestrator = None
_signal_generator = None


def _get_astro_orchestrator():
    """Lazy load VedAstro orchestrator."""
    global _astro_orchestrator
    if _astro_orchestrator is None:
        try:
            from backend.vedastro import EnhancedAstroOrchestrator

            _astro_orchestrator = EnhancedAstroOrchestrator()
            logger.info("VedAstro orchestrator initialized")
        except Exception as e:
            logger.error(f"Failed to initialize VedAstro orchestrator: {e}")
            raise
    return _astro_orchestrator


def _get_signal_generator():
    """Lazy load signal generator."""
    global _signal_generator
    if _signal_generator is None:
        try:
            from backend.vedastro import TradingSignalGenerator

            _signal_generator = TradingSignalGenerator()
            logger.info("Signal generator initialized")
        except Exception as e:
            logger.error(f"Failed to initialize signal generator: {e}")
            raise
    return _signal_generator


@circuit_breaker(failure_threshold=5, timeout_seconds=30)
@vedastro_retry
async def vedastro_generate_signal(
    symbol: str, current_price: float, ctx: Context = None
) -> dict[str, Any]:
    """
    Generate trading signal from astrological data.

    Args:
        symbol: Asset symbol (e.g., "AAPL", "BTC")
        current_price: Current market price
        ctx: MCP context for logging

    Returns:
        Trading signal with confidence and astrological context
    """
    if ctx:
        ctx.info(f"Generating VedAstro signal for {symbol} at ${current_price}")

    try:
        # Get VedAstro components
        orchestrator = _get_astro_orchestrator()

        # Get VedAstro analysis
        astro_analysis = await orchestrator.analyze_asset(
            symbol=symbol, current_price=current_price
        )

        signal = astro_analysis.trading_signal

        # Extract signal value (handle both enum and string)
        signal_value = signal.signal
        if hasattr(signal_value, "value"):
            signal_str = signal_value.value
        else:
            signal_str = str(signal_value).lower()

        # ============================================================
        # PAPER TRADING MODE: Generate some BUY signals for testing
        # ============================================================
        import os

        if os.getenv("PAPER_TRADING_GENERATE_BUYS", "true").lower() == "true":
            import hashlib
            import random

            # Deterministic "random" based on symbol + current minute
            minute = int(__import__("datetime").datetime.utcnow().timestamp() / 60)
            hash_val = int(hashlib.md5(f"{symbol}:{minute}".encode()).hexdigest(), 16)

            # 15% kans op BUY, 10% kans op STRONG_BUY
            signal_roll = hash_val % 100
            if signal_roll < 15:
                signal_str = "buy"
                signal.confidence = 65.0
                signal.strength_score = 55.0
                logger.info(f"[PAPER MODE] Generated BUY signal for {symbol}")
            elif signal_roll < 25:
                signal_str = "strong_buy"
                signal.confidence = 72.0
                signal.strength_score = 68.0
                logger.info(f"[PAPER MODE] Generated STRONG_BUY signal for {symbol}")
        # ============================================================

        if ctx:
            ctx.info(f"Signal generated: {signal_str} (confidence: {signal.confidence}%)")

        return {
            "signal": signal_str,
            "confidence": signal.confidence,
            "strength_score": signal.strength_score,
            "dasha_context": getattr(signal, "dasha_context", ""),
            "primary_factors": getattr(signal, "primary_factors", []),
            "supporting_factors": getattr(signal, "supporting_factors", []),
            "warning_factors": getattr(signal, "warning_factors", []),
            "risk_level": signal.risk_level,
            "recommended_action": signal.recommended_action,
            "timeframe": getattr(signal, "timeframe", "swing"),
            "entry_price_range": getattr(signal, "entry_price_range", None),
            "stop_loss": getattr(signal, "stop_loss", None),
            "take_profit": getattr(signal, "take_profit", None),
        }

    except Exception as e:
        logger.error(f"VedAstro signal generation failed: {e}")
        if ctx:
            ctx.error(f"Failed to generate signal: {e}")
        # Return a safe default instead of crashing
        return {
            "signal": "hold",
            "confidence": 0.0,
            "strength_score": 0.0,
            "dasha_context": "",
            "primary_factors": [],
            "risk_level": "high",
            "recommended_action": "Hold - insufficient astrological data",
            "error": str(e),
        }


@circuit_breaker(failure_threshold=3, timeout_seconds=20)
@vedastro_retry
async def vedastro_get_dasha(symbol: str, ctx: Context = None) -> dict[str, Any]:
    """
    Get current Dasha period for an asset.

    Args:
        symbol: Asset symbol
        ctx: MCP context

    Returns:
        Dasha information including Mahadasha, Antardasha, Pratyantardasha
    """
    if ctx:
        ctx.info(f"Fetching Dasha for {symbol}")

    try:
        orchestrator = _get_astro_orchestrator()

        # Get Kundli for asset
        birth_date = orchestrator.ASSET_BIRTHDAYS.get(symbol)
        if not birth_date:
            # Default to generic analysis
            return {
                "symbol": symbol,
                "mahadasha": "Unknown",
                "antardasha": "Unknown",
                "pratyantardasha": "Unknown",
                "note": "No birth data available for this asset",
            }

        # Calculate current Dasha
        kundli = await orchestrator.vedastro.calculate_kundli(symbol, birth_date)
        dasha = kundli.get("dasha", {})

        return {
            "symbol": symbol,
            "mahadasha": dasha.get("mahadasha_lord", "Unknown"),
            "antardasha": dasha.get("antardasha_lord", "Unknown"),
            "pratyantardasha": dasha.get("pratyantardasha_lord", "Unknown"),
            "mahadasha_start": (
                dasha.get("mahadasha_start", "").isoformat()
                if hasattr(dasha.get("mahadasha_start"), "isoformat")
                else str(dasha.get("mahadasha_start", ""))
            ),
            "mahadasha_end": (
                dasha.get("mahadasha_end", "").isoformat()
                if hasattr(dasha.get("mahadasha_end"), "isoformat")
                else str(dasha.get("mahadasha_end", ""))
            ),
            "interpretation": _get_dasha_interpretation(dasha.get("mahadasha_lord", "")),
        }

    except Exception as e:
        logger.error(f"Failed to get Dasha: {e}")
        if ctx:
            ctx.error(f"Failed to get Dasha: {e}")
        return {
            "symbol": symbol,
            "mahadasha": "Unknown",
            "antardasha": "Unknown",
            "pratyantardasha": "Unknown",
            "error": str(e),
        }


@circuit_breaker(failure_threshold=5, timeout_seconds=30)
@vedastro_retry
async def vedastro_get_transits(symbol: str, ctx: Context = None) -> dict[str, Any]:
    """
    Get current planetary transits for an asset.

    Args:
        symbol: Asset symbol
        ctx: MCP context

    Returns:
        Transit information including exalted, debilitated, and retrograde planets
    """
    if ctx:
        ctx.info(f"Fetching transits for {symbol}")

    try:
        orchestrator = _get_astro_orchestrator()

        # Get Kundli
        birth_date = orchestrator.ASSET_BIRTHDAYS.get(symbol)
        if not birth_date:
            return {
                "symbol": symbol,
                "exalted_planets": [],
                "debilitated_planets": [],
                "retrograde_planets": [],
                "transit_score": 0.5,
                "coherence": 0.5,
                "note": "No birth data available",
            }

        kundli = await orchestrator.vedastro.calculate_kundli(symbol, birth_date)
        transits = await orchestrator.vedastro.calculate_transits(datetime.now(), kundli)

        return {
            "symbol": symbol,
            "exalted_planets": transits.get("exalted_planets", []),
            "debilitated_planets": transits.get("debilitated_planets", []),
            "retrograde_planets": [
                p
                for p, pos in transits.get("current_positions", {}).items()
                if pos.get("retrograde", False)
            ],
            "transit_score": _calculate_transit_score(transits),
            "coherence": orchestrator._calculate_astro_coherence(transits),
            "retrograde_count": transits.get("retrograde_count", 0),
            "aspect_count": len(transits.get("aspects", [])),
        }

    except Exception as e:
        logger.error(f"Failed to get transits: {e}")
        if ctx:
            ctx.error(f"Failed to get transits: {e}")
        return {
            "symbol": symbol,
            "exalted_planets": [],
            "debilitated_planets": [],
            "retrograde_planets": [],
            "transit_score": 0.5,
            "coherence": 0.5,
            "error": str(e),
        }


def _get_dasha_interpretation(mahadasha_lord: str) -> str:
    """Get interpretation for Dasha lord."""
    interpretations = {
        "Jupiter": "Jupiter Mahadasha brings wisdom, expansion, and prosperity. Good for long-term investments.",
        "Venus": "Venus Mahadasha brings luxury, relationships, and financial growth. Favorable for trading.",
        "Mercury": "Mercury Mahadasha brings communication, analysis, and quick decisions. Good for day trading.",
        "Sun": "Sun Mahadasha brings authority and power. Moderate for trading, focus on large caps.",
        "Moon": "Moon Mahadasha brings emotions and fluctuations. Caution advised, volatile period.",
        "Mars": "Mars Mahadasha brings energy and aggression. Good for bold moves but manage risk.",
        "Saturn": "Saturn Mahadasha brings discipline and restrictions. Focus on long-term, conservative strategies.",
        "Rahu": "Rahu Mahadasha brings illusion and sudden changes. High volatility, unpredictable markets.",
        "Ketu": "Ketu Mahadasha brings detachment and spiritual growth. Not favorable for material gains.",
    }
    return interpretations.get(mahadasha_lord, "Mixed influences.")


def _calculate_transit_score(transits: dict) -> float:
    """Calculate overall transit score (0-1)."""
    score = 0.5

    # Exalted planets increase score
    exalted = len(transits.get("exalted_planets", []))
    score += exalted * 0.1

    # Debilitated planets decrease score
    debilitated = len(transits.get("debilitated_planets", []))
    score -= debilitated * 0.15

    # Retrogrades add uncertainty
    retrograde = transits.get("retrograde_count", 0)
    score -= retrograde * 0.02

    return max(0.0, min(1.0, score))
