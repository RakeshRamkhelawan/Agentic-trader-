"""
Signal schemas for Prediction Market Intelligence API.
"""
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional, Any

from pydantic import BaseModel, Field, ConfigDict


class MarketSource(str, Enum):
    """Supported prediction market sources."""
    KALSHI = "kalshi"
    POLYMARKET = "polymarket"


class SignalType(str, Enum):
    """Signal type indicators."""
    BULLISH = "bullish"
    BEARISH = "bearish"
    NEUTRAL = "neutral"


class SignalCategory(str, Enum):
    """Market categories."""
    CRYPTO = "crypto"
    POLITICS = "politics"
    ECONOMICS = "economics"
    FINANCE = "finance"
    SPORTS = "sports"
    ENTERTAINMENT = "entertainment"
    OTHER = "other"


class MarketSignal(BaseModel):
    """
    Market intelligence signal from prediction markets.
    
    Represents a trading signal derived from prediction market data,
    including maker/taker analysis, volume patterns, and sentiment.
    """
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "sig_abc123",
                "market": "kalshi",
                "category": "crypto",
                "signal_type": "bullish",
                "confidence": 0.75,
                "symbol": "BTC",
                "indicators": {
                    "maker_advantage": 0.02,
                    "volume_change_24h": 1.5,
                    "sentiment_score": 0.8
                },
                "timestamp": "2026-02-13T10:00:00Z",
                "metadata": {
                    "source_market": "Will Bitcoin exceed $100k by March 2026?",
                    "current_price": 0.65
                }
            }
        }
    )
    
    id: str = Field(..., description="Unique signal identifier")
    market: MarketSource = Field(..., description="Source prediction market")
    category: SignalCategory = Field(..., description="Market category")
    signal_type: SignalType = Field(..., description="Signal direction")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score 0-1")
    symbol: Optional[str] = Field(None, description="Related trading symbol")
    indicators: Dict[str, float] = Field(default_factory=dict, description="Signal indicators")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Signal timestamp")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class SignalFilter(BaseModel):
    """Filter parameters for signals query."""
    market: Optional[MarketSource] = Field(None, description="Filter by market source")
    category: Optional[SignalCategory] = Field(None, description="Filter by category")
    signal_type: Optional[SignalType] = Field(None, description="Filter by signal type")
    min_confidence: float = Field(0.0, ge=0.0, le=1.0, description="Minimum confidence")
    symbol: Optional[str] = Field(None, description="Filter by symbol")
    limit: int = Field(10, ge=1, le=100, description="Max results")
    offset: int = Field(0, ge=0, description="Pagination offset")


class SignalsResponse(BaseModel):
    """Response for signals endpoint."""
    signals: List[MarketSignal] = Field(..., description="List of signals")
    total: int = Field(..., description="Total matching signals")
    limit: int = Field(..., description="Results limit")
    offset: int = Field(..., description="Results offset")
