
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, List, Tuple, Dict, Any, Literal
import time

class EventType(str, Enum):
    TICKER = "ticker"
    TRADE = "trade"
    ORDERBOOK_SNAPSHOT = "orderbook_snapshot"
    ORDERBOOK_DELTA = "orderbook_delta"

@dataclass
class UnifiedMarketEvent:
    """
    Standardized Market Event for all exchanges.
    """
    event_type: EventType
    venue: str
    symbol: str          # Unified symbol: "BTC/USDT"
    ts_exchange: float   # Exchange timestamp (seconds, float)
    ts_received: float   # Receipt timestamp (seconds, float)
    
    # Payload fields (Optional based on event_type)
    price: Optional[float] = None
    size: Optional[float] = None
    side: Optional[Literal["buy", "sell"]] = None
    
    bid: Optional[float] = None
    ask: Optional[float] = None
    
    # OrderBook: List of (price, size) tuples
    bids: Optional[List[Tuple[float, float]]] = None
    asks: Optional[List[Tuple[float, float]]] = None
    
    checksum: Optional[int] = None

    def validate(self):
        """
        Validates the event fields.
        Raises ValueError if invalid.
        """
        if self.price is not None and self.price < 0:
            raise ValueError(f"Price must be positive: {self.price}")
        
        if self.size is not None and self.size < 0:
            raise ValueError(f"Size must be positive: {self.size}")
            
        if self.side is not None and self.side not in ("buy", "sell"):
            raise ValueError(f"Side must be 'buy' or 'sell': {self.side}")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "event_type": self.event_type.value,
            "venue": self.venue,
            "symbol": self.symbol,
            "ts_exchange": self.ts_exchange,
            "ts_received": self.ts_received,
            "price": self.price,
            "size": self.size,
            "side": self.side,
            "bid": self.bid,
            "ask": self.ask,
            "bids": self.bids,
            "asks": self.asks,
            "checksum": self.checksum
        }
