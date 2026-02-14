"""
Data ingestion module for prediction market intelligence.

Provides clients for fetching data from multiple prediction markets:
- Kalshi
- Polymarket
"""

from src.ingestion.kalshi_client import KalshiClient, KalshiMarket, KalshiTrade
from src.ingestion.polymarket_client import (
    PolymarketClient,
    PolymarketMarket,
    PolymarketTrade,
)

__all__ = [
    "KalshiClient",
    "KalshiMarket",
    "KalshiTrade",
    "PolymarketClient",
    "PolymarketMarket",
    "PolymarketTrade",
]
