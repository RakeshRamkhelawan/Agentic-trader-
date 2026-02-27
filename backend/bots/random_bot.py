"""Random bot implementation for baseline testing."""

import random
from typing import Dict, List, Any

from .base_bot import BaseTradingBot, BotConfig, TradeDecision


class RandomBot(BaseTradingBot):
    """
    Bot that makes random decisions.
    
    Used for:
    - Baseline comparison
    - Testing tournament systems
    - Easy difficulty for beginners
    """
    
    def __init__(self, config: BotConfig = None):
        if config is None:
            from .base_bot import BotDifficulty, BotPersonality
            config = BotConfig(
                name="RandomBot",
                difficulty=BotDifficulty.EASY,
                personality=BotPersonality.BALANCED,
                trade_frequency=3,  # Lower frequency
            )
        super().__init__(config)
    
    async def analyze_market(self, symbol: str, price_data: List[float]) -> Dict[str, Any]:
        """No real analysis - just return random signal."""
        # Random signal weighted towards hold
        rand = random.random()
        
        if rand < 0.2:
            signal = "buy"
            confidence = random.uniform(0.3, 0.6)
        elif rand < 0.4:
            signal = "sell"
            confidence = random.uniform(0.3, 0.6)
        else:
            signal = "hold"
            confidence = random.uniform(0.1, 0.3)
        
        return {
            "signal": signal,
            "confidence": confidence,
            "random": True,
        }
    
    async def make_trade_decision(
        self,
        symbol: str,
        current_price: float,
        analysis: Dict[str, Any],
    ) -> TradeDecision:
        """Make random trade decision."""
        signal = analysis.get("signal", "hold")
        confidence = analysis.get("confidence", 0)
        
        has_position = symbol in self.positions
        
        if signal == "buy" and not has_position:
            return TradeDecision(
                action="buy",
                symbol=symbol,
                quantity=current_price,
                confidence=confidence,
                reason="Random buy signal",
            )
        elif signal == "sell" and has_position:
            return TradeDecision(
                action="sell",
                symbol=symbol,
                quantity=self.positions[symbol].get("quantity", 0),
                confidence=confidence,
                reason="Random sell signal",
            )
        
        return TradeDecision(
            action="hold",
            symbol=symbol,
            quantity=0,
            confidence=0.1,
            reason="Random hold",
        )
    
    def should_trade_now(self) -> bool:
        """Override with lower probability."""
        # Random bots trade less frequently
        return random.random() < 0.1  # 10% chance per check
