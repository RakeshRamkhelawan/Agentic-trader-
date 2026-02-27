"""Momentum bot implementation."""

from typing import Dict, List, Any

from .base_bot import BaseTradingBot, BotConfig, TradeDecision


class MomentumBot(BaseTradingBot):
    """
    Bot that rides momentum waves.
    
    Strategy:
    - Buy when momentum is accelerating up
    - Sell when momentum decelerates
    - Uses rate of change and volume
    """
    
    def __init__(self, config: BotConfig = None):
        if config is None:
            from .base_bot import BotDifficulty, BotPersonality
            config = BotConfig(
                name="MomentumBot",
                difficulty=BotDifficulty.HARD,
                personality=BotPersonality.AGGRESSIVE,
                max_position_pct=0.3,  # More aggressive position sizing
            )
        super().__init__(config)
    
    async def analyze_market(self, symbol: str, price_data: List[float]) -> Dict[str, Any]:
        """Analyze momentum using rate of change."""
        if len(price_data) < 10:
            return {"signal": "hold", "confidence": 0}
        
        current_price = price_data[-1]
        
        # Calculate rates of change
        roc_3 = ((current_price - price_data[-4]) / price_data[-4]) * 100 if len(price_data) >= 4 else 0
        roc_5 = ((current_price - price_data[-6]) / price_data[-6]) * 100 if len(price_data) >= 6 else 0
        roc_10 = ((current_price - price_data[-11]) / price_data[-11]) * 100 if len(price_data) >= 11 else 0
        
        # Calculate acceleration
        acceleration = roc_3 - (price_data[-2] - price_data[-5]) / price_data[-5] * 100 if len(price_data) >= 5 else 0
        
        # Volume proxy (using price movement magnitude)
        recent_volatility = sum(
            abs(price_data[i] - price_data[i-1]) / price_data[i-1]
            for i in range(-5, 0)
        ) / 5 * 100
        
        # Momentum score
        momentum_score = (roc_3 + roc_5 * 0.5 + acceleration) * (1 + recent_volatility / 100)
        
        # Generate signal
        if momentum_score > 3 and acceleration > 0.5:
            signal = "buy"
            confidence = min(0.9, 0.5 + momentum_score / 10)
            reason = f"Strong momentum: ROC3={roc_3:.2f}%, Accel={acceleration:.2f}"
        elif momentum_score < -3 or (roc_3 < 0 and acceleration < -0.5):
            signal = "sell"
            confidence = min(0.9, 0.5 + abs(momentum_score) / 10)
            reason = f"Momentum fading: ROC3={roc_3:.2f}%, Accel={acceleration:.2f}"
        else:
            signal = "hold"
            confidence = 0.2
            reason = "No strong momentum"
        
        return {
            "signal": signal,
            "confidence": confidence,
            "reason": reason,
            "roc_3": roc_3,
            "roc_5": roc_5,
            "roc_10": roc_10,
            "acceleration": acceleration,
            "momentum_score": momentum_score,
        }
    
    async def make_trade_decision(
        self,
        symbol: str,
        current_price: float,
        analysis: Dict[str, Any],
    ) -> TradeDecision:
        """Make trade decision based on momentum."""
        signal = analysis.get("signal", "hold")
        confidence = analysis.get("confidence", 0)
        reason = analysis.get("reason", "")
        momentum_score = analysis.get("momentum_score", 0)
        
        has_position = symbol in self.positions
        
        # Momentum bots can pyramid positions
        if signal == "buy":
            if not has_position:
                return TradeDecision(
                    action="buy",
                    symbol=symbol,
                    quantity=current_price,
                    confidence=confidence,
                    reason=f"Momentum entry: {reason}",
                )
            elif momentum_score > 5:  # Strong momentum, add to position
                return TradeDecision(
                    action="buy",
                    symbol=symbol,
                    quantity=current_price * 0.5,  # Half size add
                    confidence=confidence * 0.8,
                    reason=f"Momentum add: {reason}",
                )
        
        elif signal == "sell" and has_position:
            return TradeDecision(
                action="sell",
                symbol=symbol,
                quantity=self.positions[symbol].get("quantity", 0),
                confidence=confidence,
                reason=f"Momentum exit: {reason}",
            )
        
        return TradeDecision(
            action="hold",
            symbol=symbol,
            quantity=0,
            confidence=0.1,
            reason="No momentum signal",
        )
