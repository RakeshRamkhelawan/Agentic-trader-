import uuid

from sqlalchemy import Column, DateTime, Float, Integer, String
from sqlalchemy.dialects.postgresql import UUID

from backend.core.database import Base


class MarketCandle(Base):
    """
    OHLCV Candle data.
    Intended to be a TimescaleDB hypertable partitioned by timestamp.
    """

    __tablename__ = "market_candles"

    # Composite Primary Key for standard SQL (Symbol + Timeframe + Time)
    # Note: TimescaleDB recommends including time in the primary key.
    symbol = Column(String, primary_key=True, index=True)
    timeframe = Column(String, primary_key=True)  # e.g. "1m", "1h"
    timestamp = Column(DateTime(timezone=True), primary_key=True, index=True)

    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    volume = Column(Float, nullable=False)

    # Optional: Aggregation info or provider
    provider = Column(String, nullable=True)


class MarketTick(Base):
    """
    High-frequency tick data.
    Intended to be a TimescaleDB hypertable.
    """

    __tablename__ = "market_ticks"

    # Use UUID for row uniqueness, but strictly we query by time/symbol
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    symbol = Column(String, nullable=False, index=True)
    timestamp = Column(
        DateTime(timezone=True), primary_key=True, nullable=False, index=True
    )
    price = Column(Float, nullable=False)
    volume = Column(Float, nullable=False)
    side = Column(String, nullable=True)  # "buy" or "sell"

    # Metadata like sequence ID from exchange
    exchange_sequence = Column(Integer, nullable=True)
