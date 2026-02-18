from typing import Any, Dict, Protocol

from backend.core.zero_copy_bridge import TradingIntent


class TradingStrategy(Protocol):
    """
    Protocol for all trading strategies.
    Strategies must implement verify_entry_criteria (implicitly via analyze)
    to return a TradingIntent.
    """

    async def analyze(
        self, market_data: Dict[str, Any], soul_context: Dict[str, Any]
    ) -> TradingIntent:
        """
        Analyze market data and soul context to generate a trading intent.

        Args:
            market_data: Dictionary containing price, order book, etc.
            soul_context: Dictionary containing regime, guna, etc.

        Returns:
            TradingIntent: The decision (Buy/Sell/Hold) with size and confidence.
        """
        ...
