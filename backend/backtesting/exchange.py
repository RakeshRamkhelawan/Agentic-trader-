from datetime import datetime

from backend.backtesting.models import OrderSide, Position, Trade


class SimulatedExchange:
    """
    Simulates a broker/exchange.
    Handles order matching, commission, and portfolio tracking.
    """

    def __init__(self, initial_capital: float = 10000.0, commission_rate: float = 0.001):
        self.cash = initial_capital
        self.initial_capital = initial_capital
        self.commission_rate = commission_rate
        self.positions: dict[str, Position] = {}  # symbol -> Position
        self.trades: list[Trade] = []
        self.equity_curve: list[dict] = []

    def get_equity(self, current_prices: dict[str, float]) -> float:
        """Calculate total account value (Cash + Market Value of positions)."""
        market_value = 0.0
        for symbol, pos in self.positions.items():
            price = current_prices.get(symbol, pos.current_price)
            market_value += pos.quantity * price

        return self.cash + market_value

    def execute_market_order(
        self,
        symbol: str,
        side: OrderSide,
        quantity: float,
        current_price: float,
        timestamp: datetime,
    ) -> Trade:
        """Execute a market order immediately at current_price."""

        # Calculate cost and commission
        gross_amount = quantity * current_price
        commission = gross_amount * self.commission_rate
        net_cost = gross_amount + commission if side == OrderSide.BUY else gross_amount - commission

        # Validation checks (Simplified)
        if side == OrderSide.BUY:
            if net_cost > self.cash:
                raise ValueError(f"Insufficient funds: Have {self.cash}, need {net_cost}")
            self.cash -= net_cost
            self._update_position(symbol, quantity, current_price, side)

        elif side == OrderSide.SELL:
            # Check if we have enough shares
            current_pos = self.positions.get(symbol)
            if not current_pos or current_pos.quantity < quantity:
                raise ValueError(
                    f"Insufficient shares: Have {current_pos.quantity if current_pos else 0}, need {quantity}"
                )

            self.cash += gross_amount - commission
            self._update_position(symbol, -quantity, current_price, side)

        trade = Trade(
            symbol=symbol,
            side=side,
            quantity=quantity,
            price=current_price,
            timestamp=timestamp,
            commission=commission,
        )
        self.trades.append(trade)
        return trade

    def _update_position(self, symbol: str, quantity_delta: float, price: float, side: OrderSide):
        """Update position tracking."""
        pos = self.positions.get(symbol)

        if not pos:
            if quantity_delta > 0:
                self.positions[symbol] = Position(
                    symbol=symbol,
                    quantity=quantity_delta,
                    average_price=price,
                    current_price=price,
                    unrealized_pnl=0.0,
                )
            return

        # Updating existing position
        new_quantity = pos.quantity + quantity_delta

        if new_quantity == 0:
            del self.positions[symbol]
        else:
            # Average price update (only on BUY)
            if quantity_delta > 0:
                total_cost = (pos.quantity * pos.average_price) + (quantity_delta * price)
                pos.average_price = total_cost / new_quantity

            pos.quantity = new_quantity
            pos.current_price = price
