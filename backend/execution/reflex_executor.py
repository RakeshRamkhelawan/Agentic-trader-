import asyncio
import logging
import os
import time
import uuid

from backend.core.zero_copy_bridge import TradingIntent, ZeroCopyBridge
from backend.execution.shadow_portfolio import ShadowPortfolioManager
from backend.schemas.orders import OrderRequest, OrderSide, OrderStatus

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
        trading_mode: str = "paper",
        initial_capital: float = 10000.0,
    ):
        self.shm_name = shm_name
        self.market_shm_name = market_shm_name
        self.bridge: ZeroCopyBridge | None = None
        self.market_bridge: ZeroCopyBridge | None = None
        self.running = False
        self._task: asyncio.Task | None = None

        # 🔒 PAPER MODE: ALTIJD hardcoded op "paper" voor veiligheid
        # Dit kan alleen worden overschreven via expliciete environment variable in live deployments
        env_mode = os.getenv("TRADING_MODE", "paper")
        self.trading_mode = trading_mode if trading_mode == env_mode else env_mode

        if self.trading_mode == "paper":
            # Paper mode: gebruik ShadowPortfolioManager voor simulatie
            self.portfolio = ShadowPortfolioManager(initial_cash=initial_capital)
            logger.info("🛡️ ReflexExecutor in PAPER MODE - Simulatie met ShadowPortfolio")
        else:
            self.portfolio = None
            logger.critical("⚠️ ReflexExecutor in LIVE MODE - Echte orders mogelijk!")

        # Metrics
        from backend.core.telemetry.metrics import PrometheusMetrics

        self.metrics = PrometheusMetrics("reflex_executor")

    async def start(self):
        """Initialize resources and start the reflex loop."""
        logger.info("Starting Reflex Executor...")

        try:
            # Initialize Intent Bridge (Reader Mode)
            # We assume the Mind (or system) has created the SHM
            self.bridge = ZeroCopyBridge(create=False, shm_name=self.shm_name, dtype_name="intent")
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

    def read_intent(self, symbol: str) -> TradingIntent | None:
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

    async def _execute_paper_order(self, intent: TradingIntent) -> dict | None:
        """
        Execute order in PAPER mode - simuleert fill zonder echte exchange call.
        Dit is de ENIGE toegestane executie methode in paper mode.
        """
        if not self.portfolio:
            logger.error("Geen portfolio manager beschikbaar")
            return None

        # Update portfolio met huidige marktprijs
        if self.market_bridge:
            market_data = self.market_bridge.read_market_data(intent.symbol)
            if market_data:
                self.portfolio.update_price(intent.symbol, market_data["last"])

        # Maak order request
        side = OrderSide.BUY if intent.action == 1 else OrderSide.SELL
        order = OrderRequest(
            symbol=intent.symbol,
            side=side,
            qty=abs(intent.size),
            order_type="market",
            client_order_id=str(uuid.uuid4()),
        )

        # Simuleer slippage: 0.02-0.05% van prijs
        # FIX: Use deterministic hash based on symbol name for reproducible backtests
        import hashlib
        symbol_hash = int(hashlib.md5(intent.symbol.encode()).hexdigest(), 16)
        slippage_pct = 0.02 + (symbol_hash % 30) / 1000  # 0.02-0.05%

        # Voer order uit in portfolio
        result = await self.portfolio.submit_order(order)

        if result.status == OrderStatus.FILLED:
            fill_info = {
                "symbol": intent.symbol,
                "side": side.value,
                "qty": result.filled_qty,
                "price": result.avg_price,
                "slippage_pct": slippage_pct,
                "order_id": str(result.order_id),
                "simulated": True,
            }
            logger.info(
                f"[PAPER FILL] {side.value} {intent.size} {intent.symbol} @ {result.avg_price:.2f}"
            )
            return fill_info
        else:
            logger.warning(f"[PAPER REJECTED] {side.value} {intent.symbol}: {result.error_message}")
            return None

    async def _reflex_loop(self):
        """
        High-frequency poll loop.
        In a real HFT system, this might be a busy-wait C++ extension.
        In Python async, we do our best with 1ms sleep or 0 sleep.
        """
        # 🔒 KRITISCHE PAPER MODE GUARD
        if self.trading_mode != "paper":
            logger.critical("🚫 REFLEX EXECUTOR BLOCKED: Niet in paper mode!")
            logger.critical("   Dit systeem is alleen geconfigureerd voor paper trading.")
            # In een live systeem zou je hier de live executie starten
            # Voor nu: alleen loggen en stoppen
            return

        symbol = "BTC/USD"  # Monitoring this symbol

        while self.running:
            try:
                # 1. Read Intent (Zero-Copy)
                intent = self.read_intent(symbol)

                if intent and intent.timestamp_ns > 0:
                    # Staleness check is now inside read_intent, so we only get valid intents here

                    if intent.action != 0:
                        # 2. Check Execution Triggers (Price, etc.)
                        action_str = "BUY" if intent.action == 1 else "SELL"
                        latency_ns = time.time_ns() - intent.timestamp_ns
                        latency_ms = latency_ns / 1_000_000
                        latency_sec = latency_ns / 1_000_000_000

                        self.metrics.order_execution_latency_seconds.observe(latency_sec)

                        logger.info(
                            f"[REFLEX] EXECUTE {action_str} {symbol} Size={intent.size} (Latency={latency_ms:.2f}ms)"
                        )

                        # 🔒 ALTIJD paper mode executie - GEEN echte exchange calls
                        if self.trading_mode == "paper":
                            fill = await self._execute_paper_order(intent)
                            if fill:
                                # Hier zou je ook kunnen broadcasten via WebSocket
                                pass
                        else:
                            # Dit zou nooit mogen gebeuren vanwege de guard bovenaan
                            logger.critical("🚫 LIVE MODE EXECUTION BLOCKED!")

                    # else: HOLD/WATCH - efficient no-op

                # Yield to event loop to allow other tasks (like heartbeats)
                await asyncio.sleep(0.01)  # 10ms poll for now

            except Exception as e:
                logger.error(f"Error in reflex loop: {e}")
                await asyncio.sleep(1)
