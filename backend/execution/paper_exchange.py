import asyncio
import uuid
# Placeholder for OrderRequest until verified
from dataclasses import dataclass
from typing import Dict, Optional

from backend.execution.backtest_engine import BacktestEngine
from backend.execution.broker_interface import ExecutionInterface
from backend.schemas.market_data import OrderStatus, TickerUpdate


@dataclass
class OrderRequest:
    symbol: str
    side: str
    qty: float
    type: str = "market"
    price: Optional[float] = None
    client_order_id: Optional[str] = None


@dataclass
class OrderResult:
    order_id: str
    client_order_id: Optional[str]
    status: OrderStatus
    filled_qty: float
    avg_price: float


class PaperExchange(ExecutionInterface):
    """
    Simulates a crypto exchange with slippage and latency.
    """

    def __init__(
        self, backtest_engine: BacktestEngine, initial_balance_eur: float = 10000.0
    ):
        self.engine = backtest_engine
        self.balances = {"EUR": initial_balance_eur, "BTC": 0.0}
        self.orders: Dict[str, OrderResult] = {}
        self._last_tick: Dict[str, TickerUpdate] = {}

    async def submit_order(self, order: OrderRequest) -> OrderResult:
        # Simulate network latency
        await asyncio.sleep(0.05 / self.engine.clock.speed)  # Scale latency by speed

        current_tick = self.engine.current_tick
        if not current_tick or current_tick.symbol != order.symbol:
            raise ValueError(f"No market data available for {order.symbol}")

        # Basic Slippage Model: 0.05% fixed + impact
        # In real impl, impact = func(order_size, volume)
        slippage_pct = 0.0005

        if order.side.lower() == "buy":
            price = current_tick.ask * (1 + slippage_pct)
            cost = price * order.qty
            if self.balances.get("EUR", 0) < cost:
                return OrderResult(
                    order_id=str(uuid.uuid4()),
                    client_order_id=order.client_order_id,
                    status=OrderStatus.REJECTED,
                    filled_qty=0,
                    avg_price=0,
                )
            self.balances["EUR"] -= cost
            self.balances["BTC"] = self.balances.get("BTC", 0) + order.qty
        else:
            price = current_tick.bid * (1 - slippage_pct)
            if self.balances.get("BTC", 0) < order.qty:
                return OrderResult(
                    order_id=str(uuid.uuid4()),
                    client_order_id=order.client_order_id,
                    status=OrderStatus.REJECTED,
                    filled_qty=0,
                    avg_price=0,
                )
            self.balances["BTC"] -= order.qty
            self.balances["EUR"] = self.balances.get("EUR", 0) + (price * order.qty)

        return OrderResult(
            order_id=str(uuid.uuid4()),
            client_order_id=order.client_order_id,
            status=OrderStatus.FILLED,
            filled_qty=order.qty,
            avg_price=price,
        )

    async def get_balance(self):
        return self.balances
