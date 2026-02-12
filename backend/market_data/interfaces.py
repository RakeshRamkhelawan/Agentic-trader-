
from abc import ABC, abstractmethod
import asyncio
from typing import Dict, Any, List
from backend.market_data.models import UnifiedMarketEvent

class ExchangeProvider(ABC):
    """
    Abstract Base Class for an Exchange WebSocket Provider.
    """
    def __init__(self, name: str, out_queue: asyncio.Queue):
        self.name = name
        self.out_queue = out_queue
        
    @abstractmethod
    async def run_forever(self):
        """
        Main loop: connect, subscribe, consume, parse, enqueue.
        Should handle reconnects internally.
        """
        pass
    
    @abstractmethod
    def stop(self):
        """
        Signal the provider to stop gracefully.
        """
        pass

class DataNormalizer(ABC):
    """
    Abstract Base Class for normalizing raw exchange data.
    """
    def __init__(self, symbol_map: Dict[Any, str]):
        self.symbol_map = symbol_map
        
    @abstractmethod
    def normalize(self, venue: str, raw: Dict[str, Any]) -> UnifiedMarketEvent:
        """
        Convert raw dict to UnifiedMarketEvent.
        """
        pass

class EventSink(ABC):
    """
    Abstract Base Class for a destination of Normalized Events.
    e.g., RedisPublisher, ClickHouseWriter.
    """
    @abstractmethod
    async def publish(self, event: UnifiedMarketEvent):
        """
        Publish/Persist the event.
        """
        pass
