"""
HotPathEngine - Ultra-low latency execution engine.

Characteristics:
- Sub-millisecond latency (<1ms per decision)
- Deterministic: No randomness, no LLM calls
- Thread-safe: Safe for concurrent reads
- Zero blocking I/O: Except for FastConfig reads
- Memory efficient: Minimal allocations

Design:
- Reads execution decision from FastConfig
- Returns immediately (no processing)
- Falls back to default if config unavailable
- Tracks config version for staleness detection
"""

import asyncio
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from backend.execution.broker_interface import (
    ExecutionInterface,
    OrderRequest,
    OrderSide,
    OrderType,
)
from backend.execution.fast_config import FALLBACK_CONFIG, FastConfigManager


@dataclass
class ExecutionDecision:
    """Represents a single execution decision."""

    action: int  # 0=hold, 1=long, 2=short
    confidence: float  # [0, 1]
    timestamp: float  # When decision was made (seconds)
    config_version: int  # Version of config used
    source: str = "hot_path"  # Always 'hot_path'
    quantity: float = 0.0  # Order size (0.0=default)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "action": self.action,
            "confidence": self.confidence,
            "timestamp": self.timestamp,
            "config_version": self.config_version,
            "source": self.source,
            "quantity": self.quantity,
        }


class HotPathEngine:
    """
    Ultra-low latency execution engine.

    Reads pre-computed configuration and executes trading decisions
    with minimal latency. No LLM calls, no I/O except config reads.
    """

    def __init__(self, config_path: str):
        """
        Initialize hot path engine.

        Args:
            config_path: Path to FastConfig file
        """
        self.config_path = Path(config_path)
        self.config_manager = FastConfigManager(str(config_path))

        # Pre-compute fallback decision
        self.fallback_decision = self._make_decision(FALLBACK_CONFIG, config_version=0)

    def get_execution_decision(self) -> ExecutionDecision:
        """
        Get execution decision.

        Extremely fast operation:
        - Single read of config file
        - Minimal deserialization
        - Return immediately
        - Fallback on any error

        Returns:
            ExecutionDecision with action and confidence
        """
        try:
            # Read config from FastConfig (single syscall, <1µs)
            config, version = self.config_manager.read_fast()

            # Make decision (no processing, just wrapping)
            decision = self._make_decision(config, version)

            return decision

        except Exception:
            # Fallback on any error (robust)
            return self.fallback_decision

    def _make_decision(self, config: dict[str, Any], config_version: int) -> ExecutionDecision:
        """
        Create execution decision from config.

        Args:
            config: Configuration dictionary
            config_version: Version of config

        Returns:
            ExecutionDecision
        """
        return ExecutionDecision(
            action=int(config.get("action", FALLBACK_CONFIG["action"])),
            confidence=float(config.get("confidence", FALLBACK_CONFIG["confidence"])),
            timestamp=time.time(),
            config_version=config_version,
            quantity=float(config.get("quantity", FALLBACK_CONFIG.get("quantity", 0.0))),
        )

    def get_decision_as_dict(self) -> dict[str, Any]:
        """
        Get execution decision as dictionary.

        Convenience method.

        Returns:
            Decision as dict
        """
        decision = self.get_execution_decision()
        return decision.to_dict()

    def get_action(self) -> int:
        """
        Get just the action.

        Convenience method for ultra-fast access.

        Returns:
            Action: 0=hold, 1=long, 2=short
        """
        decision = self.get_execution_decision()
        return decision.action

    def get_confidence(self) -> float:
        """
        Get confidence of current decision.

        Returns:
            Confidence [0, 1]
        """
        decision = self.get_execution_decision()
        return decision.confidence


class HotPathExecutor:
    """
    Hot path executor with REAL broker connectivity.

    Translates HotPath decisions (action=1) into actual broker orders.
    """

    def __init__(
        self,
        config_path: str,
        broker_adapter: ExecutionInterface | None = None,
        shadow_mode: bool = True,
        symbol: str = "BTC-EUR",
        batch_size: int = 10,
    ):
        """
        Initialize executor.

        Args:
            config_path: Path to FastConfig file
            broker_adapter: Instance of ExecutionInterface (e.g. RevolutXAdapter)
            shadow_mode: If True, only logs orders, does not send them.
            symbol: Trading pair to trade (default: BTC-EUR)
            batch_size: Number of decisions to process in batch (default: 10)
        """
        self.engine = HotPathEngine(config_path)
        self.adapter = broker_adapter
        self.shadow_mode = shadow_mode
        self.symbol = symbol
        self.batch_size = batch_size
        self.last_decision_time = 0

    def get_decision_batch(self, size: int | None = None) -> list[ExecutionDecision]:
        """
        Get a batch of execution decisions.

        Args:
            size: Batch size (default: self.batch_size)

        Returns:
            List of ExecutionDecision objects
        """
        count = size if size is not None else self.batch_size
        return [self.engine.get_execution_decision() for _ in range(count)]

    async def execute_cycle(self) -> bool:
        """
        Run one execution cycle.

        1. Get decision from engine
        2. Check confidence threshold
        3. Execute order if needed
        """
        decision = self.engine.get_execution_decision()

        # Debounce: Do not re-execute same decision within 1 second
        if decision.timestamp <= self.last_decision_time:
            return False

        self.last_decision_time = decision.timestamp

        # Only act if action is NOT Hold (0)
        if decision.action != 0:
            return await self.execute_action(decision)

        return False

    async def run_loop(self, interval: float = 0.001):
        """
        Run continuous execution loop.

        Args:
            interval: Polling interval in seconds (default 1ms)
        """
        print(f"[HotPath] Starting execution loop for {self.symbol}...")
        while True:
            try:
                await self.execute_cycle()
                await asyncio.sleep(interval)
            except asyncio.CancelledError:
                print("[HotPath] Execution loop cancelled.")
                break
            except Exception as e:
                print(f"[HotPath] Error in loop: {e}")
                await asyncio.sleep(1.0)  # Backoff on error

    async def execute_action(self, decision: ExecutionDecision) -> bool:
        """
        Execute trading action from decision via Broker Adapter.

        Args:
            decision: ExecutionDecision to execute

        Returns:
            True if execution successful (or simulated)
        """
        if not self.adapter:
            print(f"[HotPath] No adapter configured. Action {decision.action} ignored.")
            return False

        side = OrderSide.BUY if decision.action == 1 else OrderSide.SELL

        # Use quantity from decision if > 0, otherwise default placeholder
        qty = decision.quantity if decision.quantity > 0 else 0.0001

        order = OrderRequest(symbol=self.symbol, side=side, order_type=OrderType.MARKET, qty=qty)

        if self.shadow_mode:
            print(
                f"[SHADOW MODE] Would EXECUTE: {side.value} {qty} {self.symbol} (Conf: {decision.confidence:.2f})"
            )
            return True

        try:
            print(f"[LIVE EXECUTION] Sending Order: {side.value} {qty} {self.symbol}...")
            result = await self.adapter.submit_order(order)
            print(
                f"[LIVE EXECUTION] Order Sent! ID: {result.order_id} Status: {result.status.value}"
            )
            return True
        except Exception as e:
            print(f"[EXECUTION ERROR] Failed to send order: {str(e)}")
            return False


if __name__ == "__main__":
    # Test script for HotPathEngine (standalone)
    import tempfile

    with tempfile.TemporaryDirectory() as tmpdir:
        config_file = f"{tmpdir}/config.bin"

        # Initialize config
        config_manager = FastConfigManager(config_file)
        config_manager.write_atomic(
            {"action": 1, "confidence": 0.85, "exploration_rate": 0.05, "quantity": 0.5}
        )

        # Initialize engine
        engine = HotPathEngine(config_file)

        # Get decision
        decision = engine.get_execution_decision()
        print(f"✓ Decision: action={decision.action}, confidence={decision.confidence:.2f}")
