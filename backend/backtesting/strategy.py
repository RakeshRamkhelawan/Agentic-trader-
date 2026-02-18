from abc import ABC
from datetime import datetime
from typing import Optional

from backend.backtesting.exchange import SimulatedExchange
from backend.backtesting.fill_models import FillModel, FullFillModel
from backend.backtesting.models import OrderSide, Trade
from backend.backtesting.position_sizing import (FixedQuantitySizer,
                                                 PositionSizer)
from backend.backtesting.slippage_models import (FixedSlippageModel,
                                                 SlippageModel)


class Strategy(ABC):
    """
    Base class for trading strategies.
    Supports advanced position sizing, slippage models, and fill models.
    """

    def __init__(
        self,
        exchange: SimulatedExchange,
        position_sizer: Optional[PositionSizer] = None,
        slippage_model: Optional[SlippageModel] = None,
        fill_model: Optional[FillModel] = None,
    ):
        self.exchange = exchange
        self.position_sizer = position_sizer or FixedQuantitySizer(base_quantity=1.0)
        self.slippage_model = slippage_model or FixedSlippageModel(basis_points=5.0)
        self.fill_model = fill_model or FullFillModel()
        self.portfolio_value = exchange.initial_capital

    def calculate_position_size(
        self, price: float, signal_strength: float = 1.0, risk_per_trade: float = 0.01
    ) -> float:
        """
        Calculate position size using the configured position sizer.

        Args:
            price: Current market price
            signal_strength: Signal strength (0.0-1.0+)
            risk_per_trade: Risk percentage per trade

        Returns:
            Quantity to trade
        """
        return self.position_sizer.calculate_quantity(
            signal_strength=signal_strength,
            price=price,
            portfolio_value=self.portfolio_value,
            risk_per_trade=risk_per_trade,
        )

    def update_portfolio_value(self, new_value: float) -> None:
        """Update portfolio value (called after each bar or trade)."""
        self.portfolio_value = new_value

    def execute_order(
        self,
        symbol: str,
        side: OrderSide,
        quantity: float,
        current_price: float,
        timestamp: datetime,
        available_volume: float = float("inf"),
    ) -> Optional[Trade]:
        """
        Execute an order with slippage and fill model simulation.

        Args:
            symbol: Trading symbol
            side: OrderSide.BUY or OrderSide.SELL
            quantity: Desired quantity to trade
            current_price: Current market price
            timestamp: Order timestamp
            available_volume: Available market volume (for fill simulation)

        Returns:
            Trade object if order was filled (fully or partially), None if unfilled
        """
        # Apply fill model to determine how much gets filled
        filled_quantity, unfilled_quantity = self.fill_model.compute_fill(
            order_quantity=quantity, available_volume=available_volume
        )

        # If nothing filled, return None
        if filled_quantity <= 0:
            return None

        # Apply slippage model to get execution price
        execution_price, slippage_cost = self.slippage_model.apply(
            price=current_price, quantity=filled_quantity, side=side
        )

        # Execute the filled portion at the slipped price
        trade = self.exchange.execute_market_order(
            symbol=symbol,
            side=side,
            quantity=filled_quantity,
            current_price=execution_price,
            timestamp=timestamp,
        )

        return trade
