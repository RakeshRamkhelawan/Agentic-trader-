import asyncio
import logging
import time
from typing import Optional

from backend.core.zero_copy_bridge import TradingIntent, ZeroCopyBridge

logger = logging.getLogger(__name__)


class ReflexExecutor:
    """
    Layer 3: Reflex Body (The "Acting Body")
    - Operates at high frequency (<10ms polling or event-driven).
    - Reads 'TradingIntent' from Shared Memory (Zero-Copy).
    - Executes order if 'Action Trigger' conditions are met (Price, Volume).
    - NO heavy computation allowed here.
    """

    def __init__(
        self,
        shm_name: str = "trading_intents_v2",
        market_shm_name: str = "market_data_v2",
    ):
        self.shm_name = shm_name
        self.market_shm_name = market_shm_name
        self.bridge: Optional[ZeroCopyBridge] = None
        self.market_bridge: Optional[ZeroCopyBridge] = None
        self.running = False
        self._task: Optional[asyncio.Task] = None

        # Metrics
        from backend.core.telemetry.metrics import PrometheusMetrics

        self.metrics = PrometheusMetrics("reflex_executor")

    async def start(self):
        """Initialize resources and start the reflex loop."""
        logger.info("Starting Reflex Executor...")

        try:
            # Initialize Intent Bridge (Reader Mode)
            # We assume the Mind (or system) has created the SHM
            self.bridge = ZeroCopyBridge(
                create=False, shm_name=self.shm_name, dtype_name="intent"
            )
            if self.bridge.shm is None:
                self.bridge = None
            logger.info(f"Intent SHM connected: {self.shm_name}")
        except Exception as e:
            logger.error(f"Failed to connect to Intent SHM: {e}")
            # Don't fail startup completely - we can operate without market data

        try:
            # Initialize Market Data Bridge (Reader Mode)
            self.market_bridge = ZeroCopyBridge(
                create=False, shm_name=self.market_shm_name, dtype_name="market"
            )
            logger.info(f"Market Data SHM connected: {self.market_shm_name}")
        except Exception as e:
            logger.warning(f"Market Data SHM not available (optional): {e}")
            # Market data is optional for reflex

        self.running = True
        self._task = asyncio.create_task(self._reflex_loop())
        logger.info("Reflex Executor started.")

    async def stop(self):
        """Stop the executor."""
        logger.info("Stopping Reflex Executor...")
        self.running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

        if self.bridge:
            self.bridge.close()
        if self.market_bridge:
            self.market_bridge.close()
        logger.info("Reflex Executor stopped.")

    def read_intent(self, symbol: str) -> Optional[TradingIntent]:
        """
        Read intent from shared memory with minimal overhead.
        Also checks current market price if available.
        """
        if self.bridge is None:
            return None

        intent = self.bridge.read_intent(symbol)
        if not intent:
            return None

        # Check staleness
        latency_ns = time.time_ns() - intent.timestamp_ns
        if latency_ns / 1_000_000_000 > 0.5:  # 500ms stale
            return None

        # Validate against current market price (if available)
        if self.market_bridge:
            market_data = self.market_bridge.read_market_data(symbol)
            if market_data:
                # Example check: Verify price hasn't moved > 0.1% from entry_price
                current_price = market_data["last"]
                deviation = abs(current_price - intent.entry_price) / intent.entry_price
                if deviation > 0.001:
                    logger.warning(
                        f"Slippage protection: Price moved {deviation*100:.4f}% for {symbol}"
                    )
                    return None

        return intent

    async def _reflex_loop(self):
        """
        High-frequency poll loop.
        In a real HFT system, this might be a busy-wait C++ extension.
        In Python async, we do our best with 1ms sleep or 0 sleep.
        """
        symbol = "BTC/USD"  # Monitoring this symbol

        while self.running:
            try:
                # 1. Read Intent (Zero-Copy)
                intent = self.read_intent(symbol)

                if intent and intent.timestamp_ns > 0:
                    # Staleness check is now inside read_intent, so we only get valid intents here

                    if intent.action != 0:
                        # 2. Check Execution Triggers (Price, etc.)
                        # For Phase 1, we just LOG that we received a signal
                        action_str = "BUY" if intent.action == 1 else "SELL"
                        # Recalculate latency for logging purposes if needed, or pass from read_intent
                        latency_ns = time.time_ns() - intent.timestamp_ns
                        latency_ms = latency_ns / 1_000_000
                        latency_sec = latency_ns / 1_000_000_000

                        self.metrics.order_execution_latency_seconds.observe(
                            latency_sec
                        )

                        logger.info(
                            f"[REFLEX] EXECUTE {action_str} {symbol} Size={intent.size} (Latency={latency_ms:.2f}ms)"
                        )

                        # EXECUTE ORDER HERE (API Call)

                    # else: HOLD/WATCH - efficient no-op

                # Yield to event loop to allow other tasks (like heartbeats)
                await asyncio.sleep(0.01)  # 10ms poll for now

            except Exception as e:
                logger.error(f"Error in reflex loop: {e}")
                await asyncio.sleep(1)
