from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from backend.market_data.models import UnifiedMarketEvent


class BaseStrategy(ABC):
    """
    Abstract Base Class for all trading strategies.

    A strategy receives market events (ticks) and optionally returns a Signal dictionary.
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config

    @abstractmethod
    async def on_tick(self, tick: UnifiedMarketEvent) -> Optional[Dict[str, Any]]:
        """
        Process a new market tick and return a signal payload if a condition is met.

        Args:
            tick: The standardized market event.

        Returns:
            Optional[Dict]: Signal payload if triggered, None otherwise.
            The payload should contain keys: 'signal', 'symbol', 'price', 'strategy', etc.
        """
        pass
