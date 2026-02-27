"""Base class for AI trading bots."""

import random
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any

from backend.competitions.models.competitor import Competitor, CompetitorStats, LeagueTier


class BotDifficulty(Enum):
    """Bot difficulty levels."""
    EASY = "easy"       # 40-50% win rate
    MEDIUM = "medium"   # 50-60% win rate
    HARD = "hard"       # 60-70% win rate
    EXPERT = "expert"   # 70-80% win rate


class BotPersonality(Enum):
    """Bot trading personalities."""
    AGGRESSIVE = "aggressive"    # High risk, high reward
    CONSERVATIVE = "conservative" # Low risk, steady gains
    BALANCED = "balanced"        # Moderate approach
    ADAPTIVE = "adaptive"        # Adjusts to market


@dataclass
class BotConfig:
    """Configuration for a trading bot."""
    name: str
    difficulty: BotDifficulty
    personality: BotPersonality
    max_position_pct: float = 0.2  # Max 20% of balance per trade
    stop_loss_pct: float = 0.02    # 2% stop loss
    take_profit_pct: float = 0.05  # 5% take profit
    trade_frequency: int = 5       # Trades per day average


@dataclass
class TradeDecision:
    """Trade decision from bot."""
    action: str  # "buy", "sell", "hold"
    symbol: str
    quantity: float
    confidence: float  # 0-1
    reason: str


class BaseTradingBot(ABC):
    """
    Abstract base class for AI trading bots.
    
    Bots participate in tournaments as simulated competitors,
    allowing solo users to still have competitive experiences.
    """
    
    def __init__(self, config: BotConfig):
        self.config = config
        self.competitor: Optional[Competitor] = None
        self.balance: float = 10000.0
        self.positions: Dict[str, Dict] = {}  # symbol -> position
        self.trade_history: List[Dict] = []
        self.total_trades: int = 0
        self.winning_trades: int = 0
        
        # Create competitor profile
        self._create_competitor()
    
    def _create_competitor(self) -> None:
        """Create competitor profile for this bot."""
        import uuid
        
        self.competitor = Competitor(
            id=f"bot_{uuid.uuid4().hex[:8]}",
            name=self.config.name,
            email=f"bot_{uuid.uuid4().hex[:8]}@ai.local",
            tier=LeagueTier.BRONZE,
            points=0,
            stats=CompetitorStats(),
        )
    
    @abstractmethod
    async def analyze_market(self, symbol: str, price_data: List[float]) -> Dict[str, Any]:
        """
        Analyze market data and return signals.
        
        Args:
            symbol: Trading pair symbol
            price_data: Recent price history
            
        Returns:
            Analysis result with signals
        """
        pass
    
    @abstractmethod
    async def make_trade_decision(
        self,
        symbol: str,
        current_price: float,
        analysis: Dict[str, Any],
    ) -> TradeDecision:
        """
        Make a trade decision based on analysis.
        
        Args:
            symbol: Trading pair
            current_price: Current market price
            analysis: Market analysis result
            
        Returns:
            Trade decision
        """
        pass
    
    async def execute_trade(self, decision: TradeDecision) -> Dict[str, Any]:
        """
        Execute a trade decision.
        
        Args:
            decision: Trade decision
            
        Returns:
            Trade result
        """
        if decision.action == "hold":
            return {"executed": False, "reason": "Hold decision"}
        
        # Calculate position size
        position_value = self.balance * self.config.max_position_pct
        quantity = position_value / decision.quantity if decision.quantity > 0 else 0
        
        trade = {
            "timestamp": datetime.utcnow().isoformat(),
            "symbol": decision.symbol,
            "action": decision.action,
            "quantity": quantity,
            "confidence": decision.confidence,
            "reason": decision.reason,
        }
        
        self.trade_history.append(trade)
        self.total_trades += 1
        
        return {
            "executed": True,
            "trade": trade,
            "balance_before": self.balance,
        }
    
    def update_balance(self, pnl: float) -> None:
        """Update balance after trade."""
        self.balance += pnl
        
        if self.competitor:
            self.competitor.stats.total_pnl += pnl
            is_win = pnl > 0
            self.competitor.update_stats(pnl, is_win)
            
            if is_win:
                self.winning_trades += 1
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get bot performance metrics."""
        win_rate = (self.winning_trades / self.total_trades * 100) if self.total_trades > 0 else 0
        
        return {
            "bot_name": self.config.name,
            "difficulty": self.config.difficulty.value,
            "personality": self.config.personality.value,
            "total_trades": self.total_trades,
            "winning_trades": self.winning_trades,
            "win_rate": win_rate,
            "current_balance": self.balance,
            "total_pnl": self.balance - 10000.0,
            "return_pct": ((self.balance - 10000.0) / 10000.0) * 100,
        }
    
    def should_trade_now(self) -> bool:
        """
        Determine if bot should trade now based on frequency.
        
        Returns:
            True if bot should make a trade decision
        """
        # Higher difficulty = more frequent trading
        difficulty_multiplier = {
            BotDifficulty.EASY: 0.7,
            BotDifficulty.MEDIUM: 1.0,
            BotDifficulty.HARD: 1.3,
            BotDifficulty.EXPERT: 1.5,
        }
        
        base_probability = self.config.trade_frequency / 24  # Per hour
        adjusted_probability = base_probability * difficulty_multiplier[self.config.difficulty]
        
        return random.random() < adjusted_probability
    
    def reset(self) -> None:
        """Reset bot for new tournament."""
        self.balance = 10000.0
        self.positions = {}
        self.trade_history = []
        self.total_trades = 0
        self.winning_trades = 0
        
        if self.competitor:
            self.competitor.stats = CompetitorStats()
    
    async def run_simulation_step(
        self,
        symbol: str,
        price_data: List[float],
        current_price: float,
    ) -> Optional[Dict]:
        """
        Run one simulation step.
        
        Args:
            symbol: Trading symbol
            price_data: Recent prices
            current_price: Current price
            
        Returns:
            Trade result if executed, None otherwise
        """
        if not self.should_trade_now():
            return None
        
        # Analyze market
        analysis = await self.analyze_market(symbol, price_data)
        
        # Make decision
        decision = await self.make_trade_decision(symbol, current_price, analysis)
        
        # Execute if not hold
        if decision.action != "hold":
            return await self.execute_trade(decision)
        
        return None
