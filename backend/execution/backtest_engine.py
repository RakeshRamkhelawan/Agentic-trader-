"""
Backtest Engine for Historical Data Replay.

Provides infrastructure for replaying historical market data
through agents for strategy validation and performance testing.
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import AsyncGenerator, Optional, Dict, List, Any
from dataclasses import dataclass, field

from backend.execution.simulated_clock import SimulatedClock
from backend.schemas.market_data import TickerUpdate, OrderBook

logger = logging.getLogger(__name__)


@dataclass
class HistoricalTick:
    """Single historical data point."""
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    symbol: str


class BacktestEngine:
    """
    Historical data replay engine for backtesting.
    
    Features:
    - Stream historical data at configurable speed
    - Simulated clock for time control
    - Support for multiple symbols
    - ClickHouse integration (optional)
    """
    
    def __init__(
        self,
        start_date: datetime,
        end_date: datetime,
        speed: float = 1.0,
        clickhouse_client: Optional[Any] = None
    ):
        """
        Initialize backtest engine.
        
        Args:
            start_date: Backtest start date
            end_date: Backtest end date
            speed: Replay speed multiplier
            clickhouse_client: Optional ClickHouse client for data
        """
        self.start_date = start_date
        self.end_date = end_date
        self.speed = speed
        self.clickhouse = clickhouse_client
        
        # Initialize clock
        self.clock = SimulatedClock(start_time=start_date, speed=speed)
        
        # Data cache
        self._data_cache: Dict[str, List[HistoricalTick]] = {}
        self._current_indices: Dict[str, int] = {}
    
    @property
    def current_time(self) -> datetime:
        """Get current simulation time."""
        return self.clock.current_time
    
    async def load_data(
        self,
        symbol: str,
        data: Optional[List[Dict[str, Any]]] = None
    ) -> int:
        """
        Load historical data for a symbol.
        
        Args:
            symbol: Trading pair
            data: Optional pre-loaded data (for testing)
            
        Returns:
            Number of data points loaded
        """
        if data:
            # Use provided data
            self._data_cache[symbol] = [
                HistoricalTick(
                    timestamp=d['timestamp'],
                    open=d['open'],
                    high=d['high'],
                    low=d['low'],
                    close=d['close'],
                    volume=d['volume'],
                    symbol=symbol
                )
                for d in data
            ]
        elif self.clickhouse:
            # Load from ClickHouse
            query = f"""
                SELECT timestamp, open, high, low, close, volume
                FROM historical_ohlcv
                WHERE symbol = '{symbol}'
                  AND timestamp BETWEEN '{self.start_date}' AND '{self.end_date}'
                ORDER BY timestamp ASC
            """
            result = await self.clickhouse.execute(query)
            self._data_cache[symbol] = [
                HistoricalTick(
                    timestamp=row['timestamp'],
                    open=row['open'],
                    high=row['high'],
                    low=row['low'],
                    close=row['close'],
                    volume=row['volume'],
                    symbol=symbol
                )
                for row in result
            ]
        else:
            # Generate mock data for testing
            self._data_cache[symbol] = self._generate_mock_data(symbol)
        
        self._current_indices[symbol] = 0
        return len(self._data_cache[symbol])
    
    def _generate_mock_data(self, symbol: str) -> List[HistoricalTick]:
        """Generate mock historical data for testing."""
        data = []
        current = self.start_date
        price = 45000.0  # Starting price
        
        while current <= self.end_date:
            import random
            # Random walk
            change = random.uniform(-0.01, 0.01) * price
            price += change
            
            data.append(HistoricalTick(
                timestamp=current,
                open=price * 0.999,
                high=price * 1.002,
                low=price * 0.998,
                close=price,
                volume=random.uniform(100, 1000),
                symbol=symbol
            ))
            current += timedelta(minutes=1)
        
        return data
    
    async def stream_ticks(
        self,
        symbol: str,
        realtime: bool = True
    ) -> AsyncGenerator[TickerUpdate, None]:
        """
        Stream historical ticks for a symbol.
        
        Args:
            symbol: Trading pair
            realtime: If True, simulate real-time delays
            
        Yields:
            TickerUpdate objects
        """
        # Ensure data is loaded
        if symbol not in self._data_cache:
            await self.load_data(symbol)
        
        data = self._data_cache[symbol]
        
        for tick in data:
            if tick.timestamp < self.start_date:
                continue
            if tick.timestamp > self.end_date:
                break
            
            # Simulate real-time delay if enabled
            if realtime:
                await self.clock.sleep_until(tick.timestamp)
            
            yield TickerUpdate(
                symbol=tick.symbol,
                bid=tick.low,  # Pessimistic assumption
                ask=tick.high,
                last=tick.close,
                volume_24h=tick.volume,
                timestamp=tick.timestamp,
                source="backtest"
            )
    
    async def get_current_tick(self, symbol: str) -> Optional[TickerUpdate]:
        """
        Get the current tick for a symbol at simulated time.
        
        Args:
            symbol: Trading pair
            
        Returns:
            Current TickerUpdate or None
        """
        if symbol not in self._data_cache:
            await self.load_data(symbol)
        
        data = self._data_cache[symbol]
        current_time = self.clock.current_time
        
        # Find the most recent tick
        for i in range(len(data) - 1, -1, -1):
            if data[i].timestamp <= current_time:
                tick = data[i]
                return TickerUpdate(
                    symbol=tick.symbol,
                    bid=tick.low,
                    ask=tick.high,
                    last=tick.close,
                    volume_24h=tick.volume,
                    timestamp=tick.timestamp,
                    source="backtest"
                )
        
        return None
    
    def reset(self) -> None:
        """Reset engine to start state."""
        self.clock.reset()
        self._current_indices = {k: 0 for k in self._current_indices}
