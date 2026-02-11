from abc import ABC, abstractmethod
from typing import Dict, Any
from backend.backtesting.exchange import SimulatedExchange

class Strategy(ABC):
    """
    Base class for trading strategies.
    Users (agents) must implement on_bar.
    """
    
    def __init__(self, exchange: SimulatedExchange):
        self.exchange = exchange
        
    @abstractmethod
    async def on_bar(self, symbol: str, bar: Dict[str, Any]) -> None:
        """
        Called on every new data bar.
        :param symbol: Ticker symbol (e.g. BTC/USD)
        :param bar: Dictionary with OHLCV data
        """
        pass
    
    @abstractmethod
    async def on_start(self) -> None:
        """Called before backtest starts."""
        pass
        
    @abstractmethod
    async def on_stop(self) -> None:
        """Called after backtest ends."""
        pass
