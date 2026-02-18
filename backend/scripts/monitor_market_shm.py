#!/usr/bin/env python
"""
Monitor Shared Memory Market Data and Trading Intents in Real-Time

Usage:
    python backend/scripts/monitor_market_shm.py

Displays:
- Market data updates (BBO, last price, timestamp)
- Trading intent updates from Mind
- Reflex Body reads
"""

import asyncio
import logging
import os
import sys
import time
from typing import Dict, Optional

# Add project root to path
sys.path.append(os.getcwd())

from backend.core.zero_copy_bridge import ZeroCopyBridge

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger("MarketSHMMonitor")


class MarketDataMonitor:
    """Monitor shared memory blocks for market data and trading intents."""

    def __init__(self):
        self.market_bridge: Optional[ZeroCopyBridge] = None
        self.intent_bridge: Optional[ZeroCopyBridge] = None
        self.last_market_ts: Dict[str, int] = {}
        self.last_intent_ts: Dict[str, int] = {}
        self.running = False

    async def initialize(self):
        """Initialize connections to shared memory blocks."""
        # Try to connect to market data SHM
        try:
            self.market_bridge = ZeroCopyBridge(
                create=False, shm_name="market_data_v2", dtype_name="market"
            )
            logger.info("[OK] Connected to market_data_v2 shared memory")
        except Exception as e:
            logger.warning(f"[WAIT] Could not connect to market_data_v2 SHM: {e}")
            logger.info("  (Ensure verification script is running first)")

        # Try to connect to intent SHM
        try:
            self.intent_bridge = ZeroCopyBridge(
                create=False, shm_name="trading_intents_v2", dtype_name="intent"
            )
            logger.info("[OK] Connected to trading_intents_v2 shared memory")
        except Exception as e:
            logger.warning(f"[WAIT] Could not connect to trading_intents_v2 SHM: {e}")
            logger.info("  (Ensure Cognitive Mind Service is running)")

        if not self.market_bridge and not self.intent_bridge:
            raise RuntimeError("Could not connect to any shared memory blocks!")

    async def monitor_loop(self):
        """Continuously monitor shared memory for updates."""
        symbols = ["BTC/USD", "ETH/USD", "SOL/USD"]  # Common symbols
        display_interval = 1.0  # Update display every second
        last_display = time.time()

        logger.info("\n" + "=" * 80)
        logger.info("MONITORING SHARED MEMORY - Press Ctrl+C to exit")
        logger.info("=" * 80)
        logger.info("")

        while self.running:
            try:
                current_time = time.time()
                should_display = (current_time - last_display) >= display_interval

                # Check market data
                if self.market_bridge:
                    for symbol in symbols:
                        market_data = self.market_bridge.read_market_data(symbol)
                        if market_data and market_data.get("timestamp_ns", 0) > 0:
                            ts_ns = market_data["timestamp_ns"]
                            if ts_ns != self.last_market_ts.get(symbol, 0):
                                latency_ms = (time.time_ns() - ts_ns) / 1_000_000
                                logger.info(
                                    f"[MARKET] {symbol:12} | "
                                    f"Bid: {market_data['bid']:8.2f} "
                                    f"Ask: {market_data['ask']:8.2f} "
                                    f"Last: {market_data['last']:8.2f} "
                                    f"| Latency: {latency_ms:6.2f}ms"
                                )
                                self.last_market_ts[symbol] = ts_ns

                # Check trading intents
                if self.intent_bridge:
                    for symbol in symbols:
                        intent = self.intent_bridge.read_intent(symbol)
                        if intent and intent.timestamp_ns > 0:
                            ts_ns = intent.timestamp_ns
                            if ts_ns != self.last_intent_ts.get(symbol, 0):
                                latency_ms = (time.time_ns() - ts_ns) / 1_000_000
                                action_str = (
                                    "BUY "
                                    if intent.action == 1
                                    else ("SELL" if intent.action == -1 else "HOLD")
                                )
                                logger.info(
                                    f"[MIND]   {symbol:12} | "
                                    f"Action: {action_str:4} "
                                    f"Size: {intent.size:8.4f} "
                                    f"Conf: {intent.confidence:6.2%} "
                                    f"| Latency: {latency_ms:6.2f}ms"
                                )
                                self.last_intent_ts[symbol] = ts_ns

                # Display header periodically
                if should_display:
                    logger.info("\n" + "-" * 80)
                    logger.info(
                        "[MARKET] = Market Data SHM | [MIND] = Trading Intent SHM | "
                        "Latency = Age of data"
                    )
                    logger.info("-" * 80)
                    last_display = current_time

                # Yield to event loop
                await asyncio.sleep(0.01)  # 10ms check interval

            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}", exc_info=True)
                await asyncio.sleep(1)

    async def run(self):
        """Main run method."""
        try:
            logger.info("Initializing Market Data Monitor...")
            await self.initialize()

            self.running = True
            await self.monitor_loop()

        except KeyboardInterrupt:
            logger.info("\nMonitoring stopped by user.")
        except Exception as e:
            logger.error(f"Fatal error: {e}", exc_info=True)
        finally:
            self.running = False
            if self.market_bridge:
                self.market_bridge.close()
            if self.intent_bridge:
                self.intent_bridge.close()
            logger.info("Monitor shutdown complete.")


async def main():
    """Entry point."""
    monitor = MarketDataMonitor()
    await monitor.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
