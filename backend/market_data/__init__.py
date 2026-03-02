"""
Market Data Module.

Features:
- Historical data fetching
- WebSocket market data providers
- Data sinks (ClickHouse, Redis, Redpanda)
"""

from .historical_data_fetcher import FetchConfig, HistoricalDataFetcher

__all__ = [
    "FetchConfig",
    "HistoricalDataFetcher",
]
