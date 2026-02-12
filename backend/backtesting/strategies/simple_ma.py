from datetime import datetime
from typing import Dict, Any, List
from backend.backtesting.strategy import Strategy
from backend.backtesting.models import OrderSide

class MovingAverageStrategy(Strategy):
    """
    Simple Moving Average Crossover Strategy.
    """
    
    def __init__(self, exchange, short_window=10, long_window=30):
        super().__init__(exchange)
        self.short_window = short_window
        self.long_window = long_window
        self.prices: Dict[str, List[float]] = {}
        
    async def on_start(self):
        print("MA Strategy Started")
        
    async def on_stop(self):
        print("MA Strategy Stopped")
        
    async def on_bar(self, symbol: str, bar: Dict[str, Any]):
        close_price = bar['close']
        
        if symbol not in self.prices:
            self.prices[symbol] = []
            
        self.prices[symbol].append(close_price)
        
        # Need enough data
        if len(self.prices[symbol]) < self.long_window:
            return
            
        # Calculate MA
        short_ma = sum(self.prices[symbol][-self.short_window:]) / self.short_window
        long_ma = sum(self.prices[symbol][-self.long_window:]) / self.long_window
        
        # Trading Logic
        position = self.exchange.positions.get(symbol)
        qty = position.quantity if position else 0
        
        # Golden Cross (Buy)
        if short_ma > long_ma and qty == 0:
            # Buy 1 unit (simplified)
            self.exchange.execute_market_order(
                symbol=symbol,
                side=OrderSide.BUY,
                quantity=1.0,
                current_price=close_price,
                timestamp=bar['timestamp'] # timestamp from data feed
            )
            
        # Death Cross (Sell)
        elif short_ma < long_ma and qty > 0:
            # Sell all
            self.exchange.execute_market_order(
                symbol=symbol,
                side=OrderSide.SELL,
                quantity=qty,
                current_price=close_price,
                timestamp=bar['timestamp']
            )
