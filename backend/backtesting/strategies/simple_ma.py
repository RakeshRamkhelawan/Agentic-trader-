from datetime import datetime
from typing import Dict, Any, List, Optional
from backend.backtesting.strategy import Strategy
from backend.backtesting.models import OrderSide
from backend.backtesting.position_sizing import PositionSizer
from backend.backtesting.fill_models import FillModel
from backend.backtesting.slippage_models import SlippageModel


class MovingAverageStrategy(Strategy):
    """
    Simple Moving Average Crossover Strategy.

    - Golden Cross (short MA > long MA): BUY signal
    - Death Cross (short MA < long MA): SELL signal
    - Uses configurable position sizers for adaptive position sizing
    """

    def __init__(
        self,
        exchange,
        short_window: int = 10,
        long_window: int = 30,
        position_sizer: Optional[PositionSizer] = None,
        slippage_model: Optional[SlippageModel] = None,
        fill_model: Optional[FillModel] = None,
    ):
        """Initialize MA strategy with advanced models.

        Args:
            exchange: SimulatedExchange instance
            short_window: Window for fast MA (default 10)
            long_window: Window for slow MA (default 30)
            position_sizer: Custom position sizer (defaults to FixedQuantitySizer)
            slippage_model: Custom slippage model
            fill_model: Custom fill model
        """
        super().__init__(
            exchange,
            position_sizer=position_sizer,
            slippage_model=slippage_model,
            fill_model=fill_model,
        )
        self.short_window = short_window
        self.long_window = long_window
        self.prices: Dict[str, List[float]] = {}
        self.trades_count = 0

    async def on_start(self):
        """Initialize strategy."""
        print(
            f"MA Strategy Started: short_window={self.short_window}, long_window={self.long_window}"
        )
        print(f"Position Sizer: {self.position_sizer.__class__.__name__}")
        print(f"Slippage Model: {self.slippage_model.__class__.__name__}")
        print(f"Fill Model: {self.fill_model.__class__.__name__}")

    async def on_stop(self):
        """Cleanup strategy."""
        print(f"MA Strategy Stopped. Total trades: {self.trades_count}")

    async def on_bar(self, symbol: str, bar: Dict[str, Any]):
        """Process new OHLCV bar.

        Args:
            symbol: Trading pair (e.g., 'BTC/USD')
            bar: OHLCV data with 'close', 'timestamp', 'volume' keys
        """
        close_price = bar["close"]
        timestamp = bar.get("timestamp")
        if timestamp is None:
            timestamp = datetime.now()
        bar_volume = bar.get("volume", 1000.0)

        if symbol not in self.prices:
            self.prices[symbol] = []

        self.prices[symbol].append(close_price)

        # Need enough data for both MAs
        if len(self.prices[symbol]) < self.long_window:
            return

        # Calculate Moving Averages
        short_ma = sum(self.prices[symbol][-self.short_window :]) / self.short_window
        long_ma = sum(self.prices[symbol][-self.long_window :]) / self.long_window

        # Calculate signal strength (normalized MA diff)
        ma_diff = short_ma - long_ma
        signal_strength = abs(ma_diff) / long_ma  # 0.0-1.0+
        signal_strength = min(1.0, signal_strength)  # Cap at 1.0

        # Get current position
        position = self.exchange.positions.get(symbol)
        current_qty = position.quantity if position else 0.0

        # Calculate dynamic position size using configured sizer
        position_size = self.calculate_position_size(
            price=close_price,
            signal_strength=signal_strength,
            risk_per_trade=0.01,  # 1% risk per trade
        )

        # Golden Cross (Buy Signal)
        if short_ma > long_ma and current_qty == 0:
            trade = self.execute_order(
                symbol=symbol,
                side=OrderSide.BUY,
                quantity=position_size,
                current_price=close_price,
                timestamp=timestamp,
                available_volume=bar_volume,
            )
            if trade:
                self.trades_count += 1
                print(
                    f"BUY {symbol}: {trade.quantity:.4f} @ {trade.price} "
                    f"(short_ma={short_ma:.2f} > long_ma={long_ma:.2f})"
                )

        # Death Cross (Sell Signal)
        elif short_ma < long_ma and current_qty > 0:
            trade = self.execute_order(
                symbol=symbol,
                side=OrderSide.SELL,
                quantity=current_qty,
                current_price=close_price,
                timestamp=timestamp,
                available_volume=bar_volume,
            )
            if trade:
                self.trades_count += 1
                print(
                    f"SELL {symbol}: {trade.quantity:.4f} @ {trade.price} "
                    f"(short_ma={short_ma:.2f} < long_ma={long_ma:.2f})"
                )

        # Update portfolio value for position sizing
        portfolio_value = self.exchange.cash + sum(
            position.quantity * (self.prices[sym][-1] if sym in self.prices and self.prices[sym] else position.current_price)
            for sym, position in self.exchange.positions.items()
        )
        self.update_portfolio_value(portfolio_value)
