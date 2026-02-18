"""
Market Data Streamer - Connects to exchanges and streams data to WebSocket clients.

Features:
- Real-time orderbook streaming from exchanges via CCXT Pro
- Ticker updates
- Auto-reconnection with exponential backoff
"""

import asyncio
import logging
from dataclasses import dataclass
from typing import Any, Dict

from backend.core.zero_copy_bridge import ZeroCopyBridge

logger = logging.getLogger(__name__)


@dataclass
class StreamConfig:
    """Configuration for a market data stream."""

    symbol: str
    exchange_id: str = "binance"
    orderbook_depth: int = 25


class MarketDataStreamer:
    """
    Streams real-time market data from exchanges to WebSocket clients.

    Uses CCXT Pro for exchange connectivity when available,
    falls back to mock data for development.
    """

    def __init__(self):
        # Active symbol subscriptions: symbol -> set of connection_ids
        self.active_streams: Dict[str, asyncio.Task] = {}
        self.symbol_configs: Dict[str, StreamConfig] = {}
        # Reference to WebSocket manager (set externally)
        self.ws_manager = None
        # Exchange clients (lazy loaded)
        self._exchanges: Dict[str, Any] = {}
        self._use_mock = True  # Set to False in production

        # Zero-Copy Bridge (Writer)
        try:
            self.shm_bridge = ZeroCopyBridge(
                create=True, shm_name="market_data_v2", dtype_name="market"
            )
        except Exception as e:
            logger.error(f"Failed to initialize Shared Memory Bridge: {e}")
            self.shm_bridge = None

    def set_ws_manager(self, ws_manager) -> None:
        """Set the WebSocket manager for broadcasting."""
        self.ws_manager = ws_manager

    async def start_stream(self, symbol: str, exchange_id: str = "binance") -> bool:
        """Start streaming data for a symbol."""
        stream_key = f"{exchange_id}.{symbol}"

        if stream_key in self.active_streams:
            return True  # Already streaming

        config = StreamConfig(symbol=symbol, exchange_id=exchange_id)
        self.symbol_configs[stream_key] = config

        # Create stream task
        self.active_streams[stream_key] = asyncio.create_task(self._stream_loop(config))

        logger.info(f"Started market data stream: {stream_key}")
        return True

    async def stop_stream(self, symbol: str, exchange_id: str = "binance") -> bool:
        """Stop streaming data for a symbol."""
        stream_key = f"{exchange_id}.{symbol}"

        if stream_key not in self.active_streams:
            return False

        task = self.active_streams.pop(stream_key)
        task.cancel()

        try:
            await task
        except asyncio.CancelledError:
            pass

        logger.info(f"Stopped market data stream: {stream_key}")
        return True

    async def _stream_loop(self, config: StreamConfig) -> None:
        """Main streaming loop for a symbol."""
        while True:
            try:
                if self._use_mock:
                    await self._stream_mock_data(config)
                else:
                    await self._stream_exchange_data(config)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Stream error for {config.symbol}: {e}")
                await asyncio.sleep(5)  # Reconnect delay

    async def _stream_mock_data(self, config: StreamConfig) -> None:
        """Stream mock market data for development."""
        import random

        base_price = 45000.0  # BTC-like price
        if "ETH" in config.symbol:
            base_price = 2500.0
        elif "XRP" in config.symbol:
            base_price = 0.50

        last_price = base_price

        while True:
            # Generate mock orderbook
            bids = []
            asks = []

            # Mock BBO for SHM
            best_bid = 0.0
            best_ask = 0.0
            best_bid_size = 0.0
            best_ask_size = 0.0

            for i in range(config.orderbook_depth):
                bid_price = last_price - (i + 1) * random.uniform(0.5, 2.0)
                ask_price = last_price + (i + 1) * random.uniform(0.5, 2.0)
                bid_size = random.uniform(0.1, 5.0)
                ask_size = random.uniform(0.1, 5.0)

                bids.append([round(bid_price, 2), round(bid_size, 6)])
                asks.append([round(ask_price, 2), round(ask_size, 6)])

                if i == 0:
                    best_bid = bids[0][0]
                    best_bid_size = bids[0][1]
                    best_ask = asks[0][0]
                    best_ask_size = asks[0][1]

            # Broadcast orderbook
            if self.ws_manager:
                await self.ws_manager.broadcast_orderbook(
                    symbol=config.symbol, bids=bids, asks=asks, is_snapshot=False
                )

            # Generate mock ticker
            change = random.uniform(-0.5, 0.5)
            last_price = max(1, last_price + change * last_price * 0.001)

            # Write to Shared Memory
            if self.shm_bridge:
                self.shm_bridge.write_market_data(
                    symbol=config.symbol,
                    bid=best_bid,
                    ask=best_ask,
                    last=last_price,
                    bid_size=best_bid_size,
                    ask_size=best_ask_size,
                )

            ticker_data = {
                "symbol": config.symbol,
                "bid": round(last_price * 0.9999, 2),
                "ask": round(last_price * 1.0001, 2),
                "last": round(last_price, 2),
                "volume_24h": random.uniform(1000, 50000),
                "change_24h": round(change * 100, 2),
                "change_percent_24h": round(change * 0.1, 4),
                "high_24h": round(last_price * 1.05, 2),
                "low_24h": round(last_price * 0.95, 2),
            }

            if self.ws_manager:
                await self.ws_manager.broadcast_ticker(
                    symbol=config.symbol,
                    **{k: v for k, v in ticker_data.items() if k != "symbol"},
                )

            # Wait before next update (100ms for orderbook, 1s for ticker)
            await asyncio.sleep(0.1)

    async def _stream_exchange_data(self, config: StreamConfig) -> None:
        """Stream real market data from exchange via CCXT Pro."""
        exchange = await self._get_exchange(config.exchange_id)

        while True:
            try:
                # Watch orderbook
                orderbook = await exchange.watch_order_book(
                    config.symbol, limit=config.orderbook_depth
                )

                # Format bids and asks as [price, size] arrays
                bids = [
                    [bid[0], bid[1]]
                    for bid in orderbook["bids"][: config.orderbook_depth]
                ]
                asks = [
                    [ask[0], ask[1]]
                    for ask in orderbook["asks"][: config.orderbook_depth]
                ]

                # Update SHM with real BBO
                if self.shm_bridge and bids and asks:
                    self.shm_bridge.write_market_data(
                        symbol=config.symbol,
                        bid=bids[0][0],
                        ask=asks[0][0],
                        last=(bids[0][0] + asks[0][0])
                        / 2,  # Approx last if not available
                        bid_size=bids[0][1],
                        ask_size=asks[0][1],
                    )

                if self.ws_manager:
                    await self.ws_manager.broadcast_orderbook(
                        symbol=config.symbol, bids=bids, asks=asks, is_snapshot=False
                    )

            except Exception as e:
                logger.error(f"Exchange stream error: {e}")
                raise

    async def _get_exchange(self, exchange_id: str) -> Any:
        """Get or create exchange client."""
        if exchange_id not in self._exchanges:
            try:
                import ccxt.pro as ccxtpro

                exchange_class = getattr(ccxtpro, exchange_id)
                self._exchanges[exchange_id] = exchange_class(
                    {
                        "enableRateLimit": True,
                    }
                )
            except Exception as e:
                logger.error(f"Failed to create exchange {exchange_id}: {e}")
                raise

        return self._exchanges[exchange_id]

    async def close(self) -> None:
        """Close all streams and exchange connections."""
        # Cancel all stream tasks
        for task in self.active_streams.values():
            task.cancel()

        if self.active_streams:
            await asyncio.gather(*self.active_streams.values(), return_exceptions=True)

        self.active_streams.clear()

        # Close exchange connections
        for exchange in self._exchanges.values():
            try:
                await exchange.close()
            except Exception:
                pass

        # Close SHM Bridge
        if self.shm_bridge:
            self.shm_bridge.close()

        self._exchanges.clear()
        logger.info("Market data streamer closed")


# Global market data streamer singleton
market_streamer = MarketDataStreamer()
