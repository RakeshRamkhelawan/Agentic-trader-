import uuid
from typing import Any, Dict

from backend.execution.broker_interface import (ExecutionInterface,
                                                OrderRequest, OrderResult,
                                                OrderSide, OrderStatus)


class ShadowPortfolioManager(ExecutionInterface):
    """
    Simulates a broker for Paper Trading / Backtesting.
    Tracks cash and positions in memory.
    """

    def __init__(self, initial_cash: float = 100000.0):
        self.cash_balance = initial_cash
        self.positions: Dict[str, float] = {}  # Symbol -> Qty
        self.market_prices: Dict[str, float] = {}  # Symbol -> Last Price

    def update_price(self, symbol: str, price: float):
        """Update internal price book for simulation."""
        self.market_prices[symbol] = price

    async def submit_order(self, order: OrderRequest) -> OrderResult:
        # 1. Get Price
        current_price = self.market_prices.get(order.symbol)
        if not current_price:
            return OrderResult(
                order_id=str(uuid.uuid4()),
                client_order_id=str(order.client_order_id),
                status=OrderStatus.REJECTED,
                error_message=f"No market price known for {order.symbol}",
            )

        # 2. Check Funds / Inventory
        cost = order.qty * current_price

        if order.side == OrderSide.BUY:
            if self.cash_balance < cost:
                return OrderResult(
                    order_id=str(uuid.uuid4()),
                    client_order_id=str(order.client_order_id),
                    status=OrderStatus.REJECTED,
                    error_message=f"Insufficient funds: Have {self.cash_balance}, need {cost}",
                )
            # Execute Buy
            self.cash_balance -= cost
            self.positions[order.symbol] = (
                self.positions.get(order.symbol, 0.0) + order.qty
            )

        elif order.side == OrderSide.SELL:
            current_qty = self.positions.get(order.symbol, 0.0)
            if current_qty < order.qty:
                return OrderResult(
                    order_id=str(uuid.uuid4()),
                    client_order_id=str(order.client_order_id),
                    status=OrderStatus.REJECTED,
                    error_message=f"Insufficient positions: Have {current_qty}, need {order.qty}",
                )
            # Execute Sell
            self.cash_balance += cost
            self.positions[order.symbol] -= order.qty

        # 3. Return Success
        return OrderResult(
            order_id=str(uuid.uuid4()),
            client_order_id=str(order.client_order_id),
            status=OrderStatus.FILLED,
            filled_qty=order.qty,
            avg_price=current_price,
        )

    async def get_order_status(self, order_id: str) -> OrderResult:
        # TODO: Implement simulation tracking if needed
        return OrderResult(
            order_id=order_id, status=OrderStatus.FILLED, client_order_id="mock"
        )

    async def get_balance(self) -> Dict[str, float]:
        return {"EUR": self.cash_balance, **self.positions}

    async def get_ticker(self, symbol: str) -> Dict[str, float]:
        price = self.market_prices.get(symbol, 0.0)
        return {"last_price": price}

    async def cancel_all_orders(self):
        pass  # Immediate execution means nothing to cancel
