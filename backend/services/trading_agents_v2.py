"""
Trading Agents V2 - Cache-Based Decision Making

Agents read from PriceFetchAgent cache instead of fetching directly.
Features:
- Async decision making
- Position sizing based on confidence
- Circuit breaker for stale data
- Performance tracking
"""

import asyncio
import logging
import os
import random
import sys
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from enum import Enum

# Fix path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.schemas.orders import OrderSide
from backend.services.price_fetch_agent import PriceFetchAgent, PriceData

logger = logging.getLogger("TradingAgentsV2")


class DecisionAction(Enum):
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"


@dataclass
class AgentDecision:
    """Trading decision with metadata."""
    agent_name: str
    strategy: str
    symbol: str
    action: DecisionAction
    confidence: float  # 0.0 - 1.0
    reason: str
    position_size: float  # EUR amount
    timestamp: datetime
    price_data: Optional[PriceData] = None
    executed: bool = False
    execution_result: Optional[str] = None


@dataclass
class AgentPerformance:
    """Track agent performance."""
    total_decisions: int = 0
    trades_executed: int = 0
    successful_trades: int = 0  # P&L > 0
    total_pnl: float = 0.0
    avg_confidence: float = 0.0
    last_trade_time: Optional[datetime] = None


class BaseTradingAgent:
    """Base class for all trading agents."""
    
    def __init__(
        self,
        name: str,
        strategy: str,
        risk_per_trade: float = 0.05,
        min_confidence: float = 0.6,
        max_positions: int = 10
    ):
        self.name = name
        self.strategy = strategy
        self.risk_per_trade = risk_per_trade
        self.min_confidence = min_confidence
        self.max_positions = max_positions
        
        self.performance = AgentPerformance()
        self.price_history: Dict[str, List[PriceData]] = {}
        self.active_positions: Dict[str, Dict] = {}  # symbol -> position info
        
    async def decide(
        self,
        symbol: str,
        price_data: PriceData,
        portfolio_value: float,
        fetch_agent: PriceFetchAgent
    ) -> Optional[AgentDecision]:
        """
        Make trading decision based on cached price data.
        
        Args:
            symbol: Trading pair
            price_data: Current price from cache
            portfolio_value: Total portfolio value
            fetch_agent: Reference to fetch agent for additional data
        
        Returns:
            AgentDecision or None if no trade
        """
        # Update price history
        if symbol not in self.price_history:
            self.price_history[symbol] = []
        self.price_history[symbol].append(price_data)
        if len(self.price_history[symbol]) > 100:
            self.price_history[symbol] = self.price_history[symbol][-100:]
        
        # Check data freshness
        if not price_data.is_fresh(max_age_seconds=5.0):
            logger.warning(f"[{self.name}] Stale data for {symbol}, skipping")
            return None
        
        # Strategy-specific analysis
        decision = await self._analyze(
            symbol, 
            price_data, 
            self.price_history[symbol],
            portfolio_value
        )
        
        if decision and decision.confidence >= self.min_confidence:
            self.performance.total_decisions += 1
            return decision
        
        return None
    
    async def _analyze(
        self,
        symbol: str,
        price_data: PriceData,
        history: List[PriceData],
        portfolio_value: float
    ) -> Optional[AgentDecision]:
        """Override in subclass."""
        raise NotImplementedError
    
    def _calculate_position_size(
        self, 
        confidence: float, 
        portfolio_value: float,
        price: float
    ) -> float:
        """Calculate position size in EUR."""
        base_risk = portfolio_value * self.risk_per_trade
        confidence_multiplier = confidence  # Higher confidence = larger position
        position_eur = base_risk * confidence_multiplier
        return min(position_eur, portfolio_value * 0.15)  # Max 15% per trade
    
    def update_performance(self, pnl: float):
        """Update performance metrics after trade."""
        self.performance.trades_executed += 1
        self.performance.total_pnl += pnl
        if pnl > 0:
            self.performance.successful_trades += 1
        self.performance.last_trade_time = datetime.now()


class MomentumAgent(BaseTradingAgent):
    """Trend-following momentum strategy."""
    
    def __init__(self):
        super().__init__(
            name="Momentum",
            strategy="momentum",
            risk_per_trade=0.08,
            min_confidence=0.65
        )
    
    async def _analyze(
        self,
        symbol: str,
        price_data: PriceData,
        history: List[PriceData],
        portfolio_value: float
    ) -> Optional[AgentDecision]:
        
        if len(history) < 10:
            return None
        
        prices = [h.price for h in history[-10:]]
        current = price_data.price
        
        # Calculate momentum
        short_ma = sum(prices[-3:]) / 3
        long_ma = sum(prices) / 10
        
        # Strong uptrend
        if current > short_ma > long_ma and prices[-1] > prices[-3] > prices[-5]:
            confidence = 0.7 + min(0.2, (current - long_ma) / long_ma)
            return AgentDecision(
                agent_name=self.name,
                strategy=self.strategy,
                symbol=symbol,
                action=DecisionAction.BUY,
                confidence=min(confidence, 0.95),
                reason=f"Strong uptrend: {((current/long_ma-1)*100):+.2f}% vs MA10",
                position_size=self._calculate_position_size(confidence, portfolio_value, current),
                timestamp=datetime.now(),
                price_data=price_data
            )
        
        # Strong downtrend
        elif current < short_ma < long_ma and prices[-1] < prices[-3] < prices[-5]:
            confidence = 0.7 + min(0.2, (long_ma - current) / long_ma)
            return AgentDecision(
                agent_name=self.name,
                strategy=self.strategy,
                symbol=symbol,
                action=DecisionAction.SELL,
                confidence=min(confidence, 0.95),
                reason=f"Strong downtrend: {((current/long_ma-1)*100):+.2f}% vs MA10",
                position_size=self._calculate_position_size(confidence, portfolio_value, current),
                timestamp=datetime.now(),
                price_data=price_data
            )
        
        return None


class MeanReversionAgent(BaseTradingAgent):
    """Mean reversion strategy."""
    
    def __init__(self):
        super().__init__(
            name="MeanReversion",
            strategy="mean_reversion",
            risk_per_trade=0.05,
            min_confidence=0.60
        )
    
    async def _analyze(
        self,
        symbol: str,
        price_data: PriceData,
        history: List[PriceData],
        portfolio_value: float
    ) -> Optional[AgentDecision]:
        
        if len(history) < 20:
            return None
        
        prices = [h.price for h in history]
        current = price_data.price
        ma20 = sum(prices[-20:]) / 20
        deviation = (current - ma20) / ma20
        
        # Price below average - buy opportunity
        if deviation < -0.02:  # 2% below MA
            confidence = 0.6 + min(0.3, abs(deviation) * 5)
            return AgentDecision(
                agent_name=self.name,
                strategy=self.strategy,
                symbol=symbol,
                action=DecisionAction.BUY,
                confidence=min(confidence, 0.90),
                reason=f"{deviation:.2%} below MA20 (mean reversion)",
                position_size=self._calculate_position_size(confidence, portfolio_value, current),
                timestamp=datetime.now(),
                price_data=price_data
            )
        
        # Price above average - sell opportunity
        elif deviation > 0.02:  # 2% above MA
            confidence = 0.6 + min(0.3, abs(deviation) * 5)
            return AgentDecision(
                agent_name=self.name,
                strategy=self.strategy,
                symbol=symbol,
                action=DecisionAction.SELL,
                confidence=min(confidence, 0.90),
                reason=f"{deviation:.2%} above MA20 (mean reversion)",
                position_size=self._calculate_position_size(confidence, portfolio_value, current),
                timestamp=datetime.now(),
                price_data=price_data
            )
        
        return None


class BreakoutAgent(BaseTradingAgent):
    """Breakout detection strategy."""
    
    def __init__(self):
        super().__init__(
            name="Breakout",
            strategy="breakout",
            risk_per_trade=0.10,
            min_confidence=0.70
        )
    
    async def _analyze(
        self,
        symbol: str,
        price_data: PriceData,
        history: List[PriceData],
        portfolio_value: float
    ) -> Optional[AgentDecision]:
        
        if len(history) < 20:
            return None
        
        prices = [h.price for h in history[-20:]]
        current = price_data.price
        high_20 = max(prices)
        low_20 = min(prices)
        
        # Breakout above resistance
        if current > high_20 * 0.995:  # Within 0.5% of 20-day high
            confidence = 0.75 + min(0.2, (current / high_20 - 1) * 10)
            return AgentDecision(
                agent_name=self.name,
                strategy=self.strategy,
                symbol=symbol,
                action=DecisionAction.BUY,
                confidence=min(confidence, 0.95),
                reason=f"Breakout: {current:.2f} > {high_20:.2f} (20d high)",
                position_size=self._calculate_position_size(confidence, portfolio_value, current),
                timestamp=datetime.now(),
                price_data=price_data
            )
        
        # Breakdown below support
        elif current < low_20 * 1.005:  # Within 0.5% of 20-day low
            confidence = 0.75 + min(0.2, (low_20 / current - 1) * 10)
            return AgentDecision(
                agent_name=self.name,
                strategy=self.strategy,
                symbol=symbol,
                action=DecisionAction.SELL,
                confidence=min(confidence, 0.95),
                reason=f"Breakdown: {current:.2f} < {low_20:.2f} (20d low)",
                position_size=self._calculate_position_size(confidence, portfolio_value, current),
                timestamp=datetime.now(),
                price_data=price_data
            )
        
        return None


class ScalperAgent(BaseTradingAgent):
    """High-frequency scalping strategy."""
    
    def __init__(self):
        super().__init__(
            name="Scalper",
            strategy="scalping",
            risk_per_trade=0.03,
            min_confidence=0.55
        )
    
    async def _analyze(
        self,
        symbol: str,
        price_data: PriceData,
        history: List[PriceData],
        portfolio_value: float
    ) -> Optional[AgentDecision]:
        
        if len(history) < 5:
            return None
        
        prices = [h.price for h in history[-5:]]
        current = price_data.price
        
        # Quick momentum reversal
        recent_change = (current - prices[0]) / prices[0]
        
        if abs(recent_change) > 0.005:  # 0.5% move in last 5 ticks
            # Counter-trend scalping
            action = DecisionAction.SELL if recent_change > 0 else DecisionAction.BUY
            confidence = 0.55 + min(0.3, abs(recent_change) * 20)
            
            return AgentDecision(
                agent_name=self.name,
                strategy=self.strategy,
                symbol=symbol,
                action=action,
                confidence=min(confidence, 0.85),
                reason=f"Scalp: {recent_change:+.2%} move (counter-trend)",
                position_size=self._calculate_position_size(confidence, portfolio_value, current),
                timestamp=datetime.now(),
                price_data=price_data
            )
        
        return None


class PositionTraderAgent(BaseTradingAgent):
    """Long-term position trading."""
    
    def __init__(self):
        super().__init__(
            name="PositionTrader",
            strategy="position",
            risk_per_trade=0.15,
            min_confidence=0.75
        )
    
    async def _analyze(
        self,
        symbol: str,
        price_data: PriceData,
        history: List[PriceData],
        portfolio_value: float
    ) -> Optional[AgentDecision]:
        
        if len(history) < 50:
            return None
        
        prices = [h.price for h in history]
        current = price_data.price
        
        # Long-term trend analysis
        ma50 = sum(prices[-50:]) / 50
        ma20 = sum(prices[-20:]) / 20
        
        # Strong long-term uptrend with momentum
        if current > ma20 > ma50 and price_data.change_24h > 0.05:
            confidence = 0.75 + min(0.2, (current / ma50 - 1))
            return AgentDecision(
                agent_name=self.name,
                strategy=self.strategy,
                symbol=symbol,
                action=DecisionAction.BUY,
                confidence=min(confidence, 0.95),
                reason=f"Long-term uptrend: MA20>MA50, +{price_data.change_24h:.1%} 24h",
                position_size=self._calculate_position_size(confidence, portfolio_value, current),
                timestamp=datetime.now(),
                price_data=price_data
            )
        
        # Long-term downtrend
        elif current < ma20 < ma50 and price_data.change_24h < -0.05:
            confidence = 0.75 + min(0.2, (ma50 / current - 1))
            return AgentDecision(
                agent_name=self.name,
                strategy=self.strategy,
                symbol=symbol,
                action=DecisionAction.SELL,
                confidence=min(confidence, 0.95),
                reason=f"Long-term downtrend: MA20<MA50, {price_data.change_24h:.1%} 24h",
                position_size=self._calculate_position_size(confidence, portfolio_value, current),
                timestamp=datetime.now(),
                price_data=price_data
            )
        
        return None


def create_all_agents() -> List[BaseTradingAgent]:
    """Factory function to create all trading agents."""
    return [
        MomentumAgent(),
        MeanReversionAgent(),
        BreakoutAgent(),
        ScalperAgent(),
        PositionTraderAgent()
    ]
