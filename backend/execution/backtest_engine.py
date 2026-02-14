from typing import AsyncGenerator, Optional
from datetime import datetime
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from backend.core.database import AsyncSessionLocal
from backend.models.market_data import MarketTick
from backend.execution.simulated_clock import SimulatedClock
from backend.schemas.market_data import TickerUpdate


class BacktestEngine:
    """
    Replays historical market data for backtesting agents.
    """

    def __init__(self, start_date: datetime, end_date: datetime, speed: float = 1.0):
        self.start_date = start_date
        self.end_date = end_date
        self.clock = SimulatedClock(start_date, speed)
        self.current_tick: Optional[TickerUpdate] = None

    async def stream_ticks(self, symbol: str) -> AsyncGenerator[TickerUpdate, None]:
        """
        Streams market ticks from the database as TickerUpdate events.
        """
        async with AsyncSessionLocal() as session:
            # Query ticks within the window, ordered by time
            # Note: For very large datasets, we should use server-side cursors or chunking.
            # For MVP, we'll fetch in batches or use stream().

            stmt = (
                select(MarketTick)
                .where(
                    and_(
                        MarketTick.symbol == symbol,
                        MarketTick.timestamp >= self.start_date,
                        MarketTick.timestamp <= self.end_date,
                    )
                )
                .order_by(MarketTick.timestamp.asc())
            )

            # Using stream() for memory efficiency
            result = await session.stream(stmt)

            async for row in result:
                tick: MarketTick = row[0]

                # Fast forward clock to tick time
                await self.clock.sleep_until(tick.timestamp)

                # Convert to TickerUpdate
                # Note: MarketTick in DB might not have bid/ask if it's just a trade.
                # For MVP we simulate bid/ask around the price.
                spread = tick.price * 0.0005  # 5 bps spread

                tick_update = TickerUpdate(
                    symbol=tick.symbol,
                    bid=tick.price - (spread / 2),
                    ask=tick.price + (spread / 2),
                    last=tick.price,
                    volume_24h=0,
                    timestamp=tick.timestamp,
                )
                self.current_tick = tick_update
                yield tick_update
