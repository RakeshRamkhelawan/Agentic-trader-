
import logging
import time
from typing import Dict, Any, Tuple
from backend.market_data.interfaces import DataNormalizer
from backend.market_data.models import UnifiedMarketEvent, EventType

logger = logging.getLogger(__name__)

class StandardNormalizer(DataNormalizer):
    """
    Standard implementation of DataNormalizer.
    """
    def __init__(self, symbol_map: Dict[Tuple[str, str], str]):
        super().__init__(symbol_map)

    def normalize(self, venue: str, raw: Dict[str, Any]) -> UnifiedMarketEvent:
        """
        Convert raw dict to UnifiedMarketEvent.
        """
        raw_type = raw.get("type")
        raw_symbol = raw.get("symbol")
        
        # 1. Symbol Mapping
        unified_symbol = self.symbol_map.get((venue, raw_symbol))
        if not unified_symbol:
            raise KeyError(f"Unknown symbol mapping: {venue} {raw_symbol}")

        # 2. Event Type Mapping
        if raw_type == "trade":
            event_type = EventType.TRADE
            # Required fields for TRADE
            price = raw.get("price")
            size = raw.get("size")
            side = raw.get("side")
            
            event = UnifiedMarketEvent(
                event_type=event_type,
                venue=venue,
                symbol=unified_symbol,
                ts_exchange=raw.get("ts", time.time()),
                ts_received=time.time(),
                price=price,
                size=size,
                side=side
            )
            
        elif raw_type == "ticker":
            event_type = EventType.TICKER
            bid = raw.get("bid")
            ask = raw.get("ask")
            
            event = UnifiedMarketEvent(
                event_type=event_type,
                venue=venue,
                symbol=unified_symbol,
                ts_exchange=raw.get("ts", time.time()),
                ts_received=time.time(),
                bid=bid,
                ask=ask
            )
        else:
            raise ValueError(f"Unknown event type: {raw_type}")

        # 3. Validation
        event.validate()
        return event
