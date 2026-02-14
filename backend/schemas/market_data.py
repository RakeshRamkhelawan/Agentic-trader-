from datetime import datetime
from enum import Enum
from typing import Optional, List, Tuple
from dataclasses import dataclass, field
from pydantic import BaseModel, Field, ConfigDict


class OrderStatus(str, Enum):
    """Order status enum for execution updates."""

    PENDING = "pending"
    OPEN = "open"
    PARTIALLY_FILLED = "partially_filled"
    FILLED = "filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"
    EXPIRED = "expired"


class MarketTick(BaseModel):
    """
    Standardized Market Data Event.
    Represents a single trade or quote update.
    """

    symbol: str
    price: float = Field(gt=0, description="Price must be positive")
    volume: float = Field(ge=0, description="Volume cannot be negative")
    timestamp: datetime = Field(default_factory=datetime.now)
    source: str = "unknown"

    # Performance optimalisatie voor Pydantic V2
    model_config = ConfigDict(frozen=True)


@dataclass
class TickerUpdate:
    """Real-time price ticker update from WebSocket stream."""

    symbol: str
    bid: float
    ask: float
    last: float
    volume_24h: float
    timestamp: datetime = field(default_factory=datetime.utcnow)
    source: str = "unknown"

    @property
    def spread(self) -> float:
        """Calculate bid-ask spread."""
        return self.ask - self.bid

    @property
    def mid_price(self) -> float:
        """Calculate mid price."""
        return (self.bid + self.ask) / 2


@dataclass
class OrderBook:
    """Order book snapshot from WebSocket stream."""

    symbol: str
    bids: List[Tuple[float, float]]  # [(price, size), ...]
    asks: List[Tuple[float, float]]  # [(price, size), ...]
    timestamp: datetime = field(default_factory=datetime.utcnow)

    @property
    def best_bid(self) -> Optional[float]:
        """Get best bid price."""
        return self.bids[0][0] if self.bids else None

    @property
    def best_ask(self) -> Optional[float]:
        """Get best ask price."""
        return self.asks[0][0] if self.asks else None

    @property
    def spread(self) -> Optional[float]:
        """Calculate spread."""
        if self.best_bid and self.best_ask:
            return self.best_ask - self.best_bid
        return None


@dataclass
class OrderUpdate:
    """Order status update from WebSocket stream."""

    order_id: str
    status: OrderStatus
    filled_qty: float
    avg_price: float
    timestamp: datetime = field(default_factory=datetime.utcnow)
    remaining_qty: float = 0.0
    fee: float = 0.0
    fee_currency: str = ""
