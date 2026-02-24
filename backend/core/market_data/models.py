from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class EventType(str, Enum):
    TRADE = "TRADE"
    QUOTE = "QUOTE"
    TICKER = "TICKER"
    ORDER_BOOK = "ORDER_BOOK"
    CANDLE = "CANDLE"


class UnifiedMarketEvent(BaseModel):
    """
    Standardized market data event used across the platform.
    """

    event_type: EventType = Field(..., description="Type of event: TRADE, QUOTE, TICKER")
    symbol: str
    price: float
    volume: float | None = 0.0
    timestamp: datetime
    exchange: str = "unknown"
    metadata: dict | None = {}
