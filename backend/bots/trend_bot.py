"""Trend following bot implementation."""

from typing import Dict, List, Any

from .base_bot import BaseTradingBot, BotConfig, TradeDecision


class TrendFollowerBot(BaseTradingBot):
    """
    Bot that follows moving average trends.
    
    Strategy:
    - Buy when price crosses above MA(20)
    - Sell when price crosses below MA(20)
    - Uses RSI for confirmation
    """
    
    def __init__(self, config: BotConfig = None):
        if config is None:
            from .base_bot import BotDifficulty, BotPersonality
            config = BotConfig(
                name="TrendBot",
                difficulty=BotDifficulty.MEDIUM,
                personality=BotPersonality.BALANCED,
            )
        super().__init__(config)
    
    async def analyze_market(self, symbol: str, price_data: List[float]) -> Dict[str, Any]:
        """Analyze trend using moving averages."""
        if len(price_data) < 20:
            return {"signal": "hold", "confidence": 0}
        
        # Calculate moving averages
        ma_short = sum(price_data[-5:]) / 5   # 5-period MA
        ma_long = sum(price_data[-20:]) / 20  # 20-period MA
        
        current_price = price_data[-1]
        prev_price = price_data[-2] if len(price_data) > 1 else current_price
        
        # Determine trend
        trend_up = ma_short > ma_long
        trend_down = ma_short < ma_long
        
        # Calculate RSI
        rsi = self._calculate_rsi(price_data)
        
        # Generate signal
        if trend_up and current_price > ma_short:
            signal = "buy"
            confidence = min(0.9, 0.5 + (rsi - 50) / 100)
        elif trend_down and current_price < ma_short:
            signal = "sell"
            confidence = min(0.9, 0.5 + (50 - rsi) / 100)
        else:
            signal = "hold"
            confidence = 0.3
        
        return {
            "signal": signal,
            "confidence": confidence,
            "ma_short": ma_short,
            "ma_long": ma_long,
            "rsi": rsi,
            "trend_up": trend_up,
            "trend_down": trend_down,
        }
    
    async def make_trade_decision(
        self,
        symbol: str,
        current_price: float,
        analysis: Dict[str, Any],
    ) -> TradeDecision:
        """Make trade decision based on trend analysis."""
        signal = analysis.get("signal", "hold")
        confidence = analysis.get("confidence", 0)
        
        # Check if we have position
        has_position = symbol in self.positions
        
        if signal == "buy" and not has_position:
            return TradeDecision(
                action="buy",
                symbol=symbol,
                quantity=current_price,
                confidence=confidence,
                reason=f"Uptrend confirmed. MA5({analysis['ma_short']:.2f}) > MA20({analysis['ma_long']:.2f})",
            )
        elif signal == "sell" and has_position:
            return TradeDecision(
                action="sell",
                symbol=symbol,
                quantity=self.positions[symbol].get("quantity", 0),
                confidence=confidence,
                reason=f"Downtrend confirmed. MA5({analysis['ma_short']:.2f}) < MA20({analysis['ma_long']:.2f})",
            )
        
        return TradeDecision(
            action="hold",
            symbol=symbol,
            quantity=0,
            confidence=0.1,
            reason="No clear trend signal",
        )
    
    def _calculate_rsi(self, prices: List[float], period: int = 14) -> float:
        """Calculate Relative Strength Index."""
        if len(prices) < period + 1:
            return 50.0
        
        gains = []
        losses = []
        
        for i in range(1, period + 1):
            change = prices[-i] - prices[-i - 1]
            if change > 0:
                gains.append(change)
                losses.append(0)
            else:
                gains.append(0)
                losses.append(abs(change))
        
        avg_gain = sum(gains) / period
        avg_loss = sum(losses) / period
        
        if avg_loss == 0:
            return 100.0
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
