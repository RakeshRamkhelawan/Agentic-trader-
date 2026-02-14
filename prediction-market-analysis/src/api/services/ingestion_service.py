"""
Ingestion Service
Fetches market data from various sources.
"""

import logging
from typing import Dict, Optional, Tuple

import pandas as pd

from src.ingestion import KalshiClient, PolymarketClient

logger = logging.getLogger(__name__)


class IngestionService:
    """
    Orchestrates data ingestion from market sources.

    Supports:
    - Kalshi
    - Polymarket
    - Mock data for testing

    Usage:
        service = IngestionService()
        trades_df = await service.fetch_market_data(
            market="kalshi",
            symbol="TRUMP25"
        )
    """

    def __init__(self):
        """Initialize ingestion service with clients."""
        self.kalshi = KalshiClient()
        self.polymarket = PolymarketClient()

    async def fetch_market_data(
        self,
        market: str,
        symbol: str,
        category: Optional[str] = None,
        limit: int = 1000,
    ) -> Tuple[pd.DataFrame, Dict]:
        """
        Fetch market trades for symbol.

        Args:
            market: Market name (kalshi, polymarket)
            symbol: Trading symbol
            category: Market category
            limit: Max trades to fetch

        Returns:
            Tuple of (trades_df, metadata)
        """
        market_lower = market.lower().strip()
        logger.info(f"Fetching {market} data for {symbol}")

        if market_lower == "kalshi":
            return await self._fetch_kalshi(symbol, category, limit)
        elif market_lower == "polymarket":
            return await self._fetch_polymarket(symbol, limit)
        else:
            raise ValueError(f"Unknown market: {market}")

    async def _fetch_kalshi(
        self, symbol: str, category: Optional[str], limit: int
    ) -> Tuple[pd.DataFrame, Dict]:
        """Fetch Kalshi market data."""
        try:
            # List markets
            markets = self.kalshi.list_markets(category=category)
            market_data = None

            for m in markets:
                if symbol.upper() in m.get("symbol", "").upper():
                    market_data = m
                    break

            if not market_data:
                logger.warning(f"Symbol {symbol} not found in Kalshi")
                return pd.DataFrame(), {
                    "market": "kalshi",
                    "symbol": symbol,
                    "status": "not_found",
                    "trades_count": 0,
                }

            # Get trades
            trades = self.kalshi.get_trade_history(
                market_id=market_data["market_id"], limit=limit
            )

            if not trades:
                logger.warning(f"No trades found for Kalshi {symbol}")
                return pd.DataFrame(), {
                    "market": "kalshi",
                    "symbol": symbol,
                    "status": "no_trades",
                    "trades_count": 0,
                }

            # Convert to DataFrame
            trades_df = self.kalshi.to_dataframe(trades)

            metadata = {
                "market": "kalshi",
                "symbol": symbol,
                "market_id": market_data.get("market_id"),
                "trades_count": len(trades_df),
                "status": "success",
            }

            logger.info(f"Fetched {len(trades_df)} Kalshi trades for {symbol}")
            return trades_df, metadata

        except Exception as e:
            logger.error(f"Kalshi fetch failed: {e}")
            return pd.DataFrame(), {
                "market": "kalshi",
                "symbol": symbol,
                "status": "error",
                "error": str(e),
                "trades_count": 0,
            }

    async def _fetch_polymarket(
        self, symbol: str, limit: int
    ) -> Tuple[pd.DataFrame, Dict]:
        """Fetch Polymarket data."""
        try:
            # List markets
            markets = self.polymarket.list_markets()
            market_data = None

            for m in markets:
                if symbol.lower() in m.get("symbol", "").lower():
                    market_data = m
                    break

            if not market_data:
                logger.warning(f"Symbol {symbol} not found in Polymarket")
                return pd.DataFrame(), {
                    "market": "polymarket",
                    "symbol": symbol,
                    "status": "not_found",
                    "trades_count": 0,
                }

            # Get order book and trades
            order_book = self.polymarket.get_order_book(market_data["market_id"])
            trades = self.polymarket.get_trade_history(
                market_id=market_data["market_id"], limit=limit
            )

            if not trades:
                logger.warning(f"No trades found for Polymarket {symbol}")
                return pd.DataFrame(), {
                    "market": "polymarket",
                    "symbol": symbol,
                    "status": "no_trades",
                    "trades_count": 0,
                }

            # Convert to DataFrame
            trades_df = self.polymarket.to_dataframe(trades)

            metadata = {
                "market": "polymarket",
                "symbol": symbol,
                "market_id": market_data.get("market_id"),
                "trades_count": len(trades_df),
                "order_book_count": len(order_book) if order_book else 0,
                "status": "success",
            }

            logger.info(f"Fetched {len(trades_df)} Polymarket trades for {symbol}")
            return trades_df, metadata

        except Exception as e:
            logger.error(f"Polymarket fetch failed: {e}")
            return pd.DataFrame(), {
                "market": "polymarket",
                "symbol": symbol,
                "status": "error",
                "error": str(e),
                "trades_count": 0,
            }

    async def search_symbols(
        self, market: str, query: str, category: Optional[str] = None, limit: int = 50
    ) -> Dict:
        """
        Search for symbols across market.

        Args:
            market: Market name
            query: Search query
            category: Optional category filter
            limit: Max results

        Returns:
            Dict with search results
        """
        market_lower = market.lower().strip()

        try:
            if market_lower == "kalshi":
                results = self.kalshi.search_markets(query=query, category=category)
            elif market_lower == "polymarket":
                results = self.polymarket.search_markets(query=query)
            else:
                return {
                    "market": market,
                    "query": query,
                    "results": [],
                    "status": "unknown_market",
                }

            # Limit results
            results = results[:limit]

            return {
                "market": market,
                "query": query,
                "results_count": len(results),
                "results": results,
                "status": "success",
            }

        except Exception as e:
            logger.error(f"Search failed: {e}")
            return {
                "market": market,
                "query": query,
                "results": [],
                "status": "error",
                "error": str(e),
            }
