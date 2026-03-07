import logging
import uuid
from typing import Any, Dict

from backend.schemas.orders import OrderRequest, OrderSide, OrderStatus

logger = logging.getLogger(__name__)


class OrderResult:
    """Mock order result for paper trading."""

    def __init__(
        self,
        order_id: str,
        status: OrderStatus,
        filled_qty: float = 0.0,
        avg_price: float = 0.0,
        error_message: str = "",
    ):
        self.order_id = order_id
        self.status = status
        self.filled_qty = filled_qty
        self.avg_price = avg_price
        self.error_message = error_message


class ShadowPortfolioManager:
    """
    In-memory portfolio manager for paper trading.
    Provides a simple ledger to track simulated balances and positions.
    """

    def __init__(self, initial_cash: float = 10000.0, cash_asset: str = "EUR"):
        self.cash_asset = cash_asset
        self.balances: Dict[str, float] = {cash_asset: initial_cash}
        self.market_prices: Dict[str, float] = {}
        logger.info(f"[ShadowPortfolio] Initialized with {initial_cash} {cash_asset}")

    def update_price(self, symbol: str, price: float):
        """Update stored price for an asset."""
        self.market_prices[symbol] = price

    async def get_balance(self) -> Dict[str, float]:
        """Get current balances."""
        return self.balances

    async def submit_order(self, order: OrderRequest) -> OrderResult:
        """
        Simulate a market order fill.
        """
        symbol = order.symbol
        side = order.side
        qty = order.qty

        price = self.market_prices.get(symbol)
        if not price:
            # Handle symbols like BTC-EUR or BTC/EUR
            base_symbol = symbol.split("-")[0].split("/")[0]
            price = self.market_prices.get(base_symbol, self.market_prices.get(symbol))

        if not price:
            # Emergency default for tests if no bridge is active
            price = 50000.0 if "BTC" in symbol else 2500.0 if "ETH" in symbol else 1.0

        if side == OrderSide.BUY:
            cost = qty * price
            cash = self.balances.get(self.cash_asset, 0)
            if cash < cost:
                return OrderResult(
                    str(uuid.uuid4()), OrderStatus.REJECTED, error_message="Insufficient EUR"
                )

            self.balances[self.cash_asset] = cash - cost
            self.balances[symbol] = self.balances.get(symbol, 0) + qty
        else:
            pos = self.balances.get(symbol, 0)
            if pos < qty:
                return OrderResult(
                    str(uuid.uuid4()), OrderStatus.REJECTED, error_message=f"Insufficient {symbol}"
                )

            self.balances[symbol] = pos - qty
            self.balances[self.cash_asset] = self.balances.get(self.cash_asset, 0) + (qty * price)

        logger.info(f"[ShadowPortfolio] {side.value} {qty} {symbol} filled @ {price:.2f}")
        return OrderResult(str(uuid.uuid4()), OrderStatus.FILLED, filled_qty=qty, avg_price=price)
