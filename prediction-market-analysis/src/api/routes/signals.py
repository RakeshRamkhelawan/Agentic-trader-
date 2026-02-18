"""
Signals Router
Provides endpoints for retrieving market intelligence signals.
"""

import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException, Query, status

from src.api.schemas.signal import MarketSignal, MarketSource, SignalCategory, SignalsResponse, SignalType

router = APIRouter()


@router.get(
    "/signals",
    response_model=SignalsResponse,
    summary="Get Market Signals",
    description="Retrieve market intelligence signals from prediction markets",
)
async def get_signals(
    market: Optional[MarketSource] = Query(None, description="Filter by market"),
    category: Optional[SignalCategory] = Query(None, description="Filter by category"),
    signal_type: Optional[SignalType] = Query(
        None, description="Filter by signal type"
    ),
    min_confidence: float = Query(
        0.0, ge=0.0, le=1.0, description="Minimum confidence"
    ),
    symbol: Optional[str] = Query(None, description="Filter by symbol"),
    limit: int = Query(10, ge=1, le=100, description="Max results"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
) -> SignalsResponse:
    """
    Get market intelligence signals.

    Signals are derived from prediction market data and can be used by
    OODA agents for decision making.

    Args:
        market: Filter by prediction market source
        category: Filter by market category
        signal_type: Filter by bullish/bearish/neutral
        min_confidence: Minimum confidence threshold
        symbol: Filter by related trading symbol
        limit: Maximum number of results
        offset: Pagination offset

    Returns:
        SignalsResponse with list of matching signals
    """
    signals = _generate_mock_signals(
        market=market,
        category=category,
        signal_type=signal_type,
        min_confidence=min_confidence,
        symbol=symbol,
        limit=limit,
        offset=offset,
    )

    return SignalsResponse(
        signals=signals, total=len(signals), limit=limit, offset=offset
    )


@router.get(
    "/signals/{signal_id}",
    response_model=MarketSignal,
    summary="Get Signal by ID",
    description="Retrieve a specific signal by its ID",
)
async def get_signal_by_id(signal_id: str) -> MarketSignal:
    """
    Get a specific signal by ID.

    Args:
        signal_id: Unique signal identifier

    Returns:
        MarketSignal if found

    Raises:
        HTTPException 404 if signal not found
    """
    if not signal_id.startswith("sig_"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Signal {signal_id} not found",
        )

    return MarketSignal(
        id=signal_id,
        market=MarketSource.KALSHI,
        category=SignalCategory.CRYPTO,
        signal_type=SignalType.BULLISH,
        confidence=0.75,
        symbol="BTC",
        indicators={"maker_advantage": 0.02, "volume_change_24h": 1.5},
        timestamp=datetime.now(timezone.utc),
        metadata={"source": "mock"},
    )


def _generate_mock_signals(
    market: Optional[MarketSource],
    category: Optional[SignalCategory],
    signal_type: Optional[SignalType],
    min_confidence: float,
    symbol: Optional[str],
    limit: int,
    offset: int,
) -> list[MarketSignal]:
    """Generate mock signals for API development."""

    mock_signals = [
        MarketSignal(
            id=f"sig_{uuid.uuid4().hex[:8]}",
            market=MarketSource.KALSHI,
            category=SignalCategory.CRYPTO,
            signal_type=SignalType.BULLISH,
            confidence=0.82,
            symbol="BTC",
            indicators={
                "maker_advantage": 0.025,
                "volume_change_24h": 2.1,
                "sentiment_score": 0.85,
            },
            timestamp=datetime.now(timezone.utc) - timedelta(minutes=5),
            metadata={
                "source_market": "Will Bitcoin exceed $100k by March 2026?",
                "current_price": 0.72,
            },
        ),
        MarketSignal(
            id=f"sig_{uuid.uuid4().hex[:8]}",
            market=MarketSource.POLYMARKET,
            category=SignalCategory.FINANCE,
            signal_type=SignalType.BEARISH,
            confidence=0.65,
            symbol="SPY",
            indicators={
                "maker_advantage": -0.01,
                "volume_change_24h": 0.8,
                "sentiment_score": 0.35,
            },
            timestamp=datetime.now(timezone.utc) - timedelta(minutes=15),
            metadata={
                "source_market": "Will S&P 500 drop 10% in Q1 2026?",
                "current_price": 0.28,
            },
        ),
        MarketSignal(
            id=f"sig_{uuid.uuid4().hex[:8]}",
            market=MarketSource.KALSHI,
            category=SignalCategory.ECONOMICS,
            signal_type=SignalType.NEUTRAL,
            confidence=0.55,
            symbol=None,
            indicators={"maker_advantage": 0.001, "volume_change_24h": 1.0},
            timestamp=datetime.now(timezone.utc) - timedelta(hours=1),
            metadata={
                "source_market": "Will Fed raise rates in March?",
                "current_price": 0.50,
            },
        ),
    ]

    # Apply filters
    filtered = mock_signals

    if market:
        filtered = [s for s in filtered if s.market == market]
    if category:
        filtered = [s for s in filtered if s.category == category]
    if signal_type:
        filtered = [s for s in filtered if s.signal_type == signal_type]
    if min_confidence > 0:
        filtered = [s for s in filtered if s.confidence >= min_confidence]
    if symbol:
        filtered = [
            s for s in filtered if s.symbol and symbol.upper() in s.symbol.upper()
        ]

    # Apply pagination
    return filtered[offset : offset + limit]
