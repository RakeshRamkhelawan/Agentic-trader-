"""Mean reversion bot implementation."""

from typing import Dict, List, Any

from .base_bot import BaseTradingBot, BotConfig, TradeDecision


class MeanReversionBot(BaseTradingBot):
    """
    Bot that trades mean reversion.
    
    Strategy:
    - Buy when price is below lower Bollinger Band
    - Sell when price is above upper Bollinger Band
    - Assumes price will revert to mean
    """
    
    def __init__(self, config: BotConfig = None):
        if config is None:
            from .base_bot import BotDifficulty, BotPersonality
            config = BotConfig(
                name="ReversionBot",
                difficulty=BotDifficulty.MEDIUM,
                personality=BotPersonality.CONSERVATIVE,
            )
        super().__init__(config)
    
    async def analyze_market(self, symbol: str, price_data: List[float]) -> Dict[str, Any]:
        """Analyze mean reversion using Bollinger Bands."""
        if len(price_data) < 20:
            return {"signal": "hold", "confidence": 0}
        
        # Calculate Bollinger Bands
        sma = sum(price_data[-20:]) / 20
        variance = sum((p - sma) ** 2 for p in price_data[-20:]) / 20
        std_dev = variance ** 0.5
        
        upper_band = sma + (2 * std_dev)
        lower_band = sma - (2 * std_dev)
        
        current_price = price_data[-1]
        
        # Calculate how far from mean (z-score)
        z_score = (current_price - sma) / std_dev if std_dev > 0 else 0
        
        # Generate signal
        if current_price < lower_band and z_score < -2:
            signal = "buy"
            confidence = min(0.85, abs(z_score) / 3)
            reason = f"Price {current_price:.2f} below lower band {lower_band:.2f}"
        elif current_price > upper_band and z_score > 2:
            signal = "sell"
            confidence = min(0.85, abs(z_score) / 3)
            reason = f"Price {current_price:.2f} above upper band {upper_band:.2f}"
        else:
            signal = "hold"
            confidence = 0.2
            reason = "Price within normal range"
        
        return {
            "signal": signal,
            "confidence": confidence,
            "reason": reason,
            "sma": sma,
            "upper_band": upper_band,
            "lower_band": lower_band,
            "z_score": z_score,
        }
    
    async def make_trade_decision(
        self,
        symbol: str,
        current_price: float,
        analysis: Dict[str, Any],
    ) -> TradeDecision:
        """Make trade decision based on mean reversion."""
        signal = analysis.get("signal", "hold")
        confidence = analysis.get("confidence", 0)
        reason = analysis.get("reason", "")
        
        has_position = symbol in self.positions
        
        if signal == "buy" and not has_position:
            return TradeDecision(
                action="buy",
                symbol=symbol,
                quantity=current_price,
                confidence=confidence,
                reason=f"Mean reversion buy: {reason}",
            )
        elif signal == "sell" and has_position:
            return TradeDecision(
                action="sell",
                symbol=symbol,
                quantity=self.positions[symbol].get("quantity", 0),
                confidence=confidence,
                reason=f"Mean reversion sell: {reason}",
            )
        
        return TradeDecision(
            action="hold",
            symbol=symbol,
            quantity=0,
            confidence=0.1,
            reason="No mean reversion opportunity",
        )
