"""
v10 Guardian - Quality over Quantity Trading System
Implements hard filters and dynamic position sizing based on audit insights
"""

from typing import Dict, Any, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class V10Config:
    """v10 Configuration based on audit analysis"""
    # Hard Filters (ADJUSTED for v8 agent capabilities)
    MIN_HARMONY: float = 0.50  # Lowered (v8 agents avg 0.693, but many below)
    MIN_CONFIDENCE: float = 0.25  # Lowered (v8 agents avg 0.368, need trades)
    MAX_TRADES_PER_HOUR: int = 50  # Increased for more opportunities
    MAX_MAYA_SCORE: float = 0.8  # More lenient
    
    # Dynamic Position Sizing
    BASE_RISK: float = 0.015  # 1.5% instead of 2.2%
    MAX_POSITION_PCT: float = 0.05  # 5% max per position
    MAX_TOTAL_POSITIONS: int = 5
    
    # Exit Optimization
    TRAILING_MULT_HIGH_HARMONY: float = 1.8
    TRAILING_MULT_LOW_HARMONY: float = 2.5
    TP_MULT_BASE: float = 3.5
    MAX_HOLD_TREND_ALIGNED: int = 12
    MAX_HOLD_TREND_MISALIGNED: int = 8
    
    # MCTS v10
    MCTS_ITERATIONS: int = 2000
    MCTS_LOOKAHEAD: int = 15
    MCTS_C: float = 1.2


class V10Guardian:
    """
    v10 Guardian - Filters and optimizes trading decisions
    
    Based on audit findings:
    - Harmony < 0.70 leads to 60% failure rate
    - Overtrading (400+ trades) destroys profits via costs
    - Dynamic sizing based on harmony and volatility improves Sharpe
    """
    
    def __init__(self, config: Optional[V10Config] = None):
        self.config = config or V10Config()
        self.trade_history: list = []
        self.hourly_trade_count: int = 0
        self.last_hour: int = -1
        self.rejection_stats: Dict[str, int] = {
            'harmony_too_low': 0,
            'confidence_too_low': 0,
            'maya_detected': 0,
            'max_positions': 0,
            'rate_limit': 0,
            'passed': 0
        }
    
    def should_trade(
        self, 
        decision: Any, 
        market_state: Any,
        active_positions: int,
        current_time: Optional[datetime] = None
    ) -> Tuple[bool, str, float]:
        """
        Determine if trade should be executed
        
        Returns:
            (should_trade: bool, reason: str, quality_score: float)
        """
        if current_time is None:
            current_time = datetime.now()
        
        # Reset hourly counter
        current_hour = current_time.hour
        if current_hour != self.last_hour:
            self.hourly_trade_count = 0
            self.last_hour = current_hour
        
        # Check 1: Harmony filter (CRITICAL - audit shows 60% failure below 0.70)
        harmony = getattr(decision, 'harmony_score', 0.0)
        if harmony < self.config.MIN_HARMONY:
            self.rejection_stats['harmony_too_low'] += 1
            return False, f"Harmony {harmony:.2f} < {self.config.MIN_HARMONY}", 0.0
        
        # Check 2: Confidence filter
        confidence = getattr(decision, 'confidence', 0.0)
        if confidence < self.config.MIN_CONFIDENCE:
            self.rejection_stats['confidence_too_low'] += 1
            return False, f"Confidence {confidence:.2f} < {self.config.MIN_CONFIDENCE}", 0.0
        
        # Check 3: Maya detection
        is_maya = getattr(decision, 'is_maya', False)
        maya_score = getattr(decision, 'maya_score', 0.0)
        if is_maya or maya_score > self.config.MAX_MAYA_SCORE:
            self.rejection_stats['maya_detected'] += 1
            return False, f"Maya detected (score: {maya_score:.2f})", 0.0
        
        # Check 4: Max positions
        if active_positions >= self.config.MAX_TOTAL_POSITIONS:
            self.rejection_stats['max_positions'] += 1
            return False, f"Max positions ({self.config.MAX_TOTAL_POSITIONS}) reached", 0.0
        
        # Check 5: Rate limiting (max trades per hour)
        if self.hourly_trade_count >= self.config.MAX_TRADES_PER_HOUR:
            self.rejection_stats['rate_limit'] += 1
            return False, f"Rate limit ({self.config.MAX_TRADES_PER_HOUR}/hour)", 0.0
        
        # Calculate quality score (0-1)
        quality_score = self._calculate_quality_score(decision, market_state)
        
        self.rejection_stats['passed'] += 1
        self.hourly_trade_count += 1
        
        return True, f"Quality score: {quality_score:.2f}", quality_score
    
    def calculate_position_size(
        self,
        capital: float,
        decision: Any,
        market_state: Any,
        base_size: float
    ) -> float:
        """
        Calculate dynamic position size based on quality and market conditions
        
        Formula: risk = 0.015 * harmony * (1 - volatility) * quality_score
        """
        harmony = getattr(decision, 'harmony_score', 0.5)
        volatility = getattr(market_state, 'volatility', 0.02)
        
        # Dynamic risk calculation
        vol_factor = 1.0 / (1.0 + volatility * 10)  # Reduce size in high vol
        harmony_factor = harmony  # Higher harmony = larger size
        
        # Calculate risk percentage
        risk_pct = self.config.BASE_RISK * harmony_factor * vol_factor
        risk_pct = min(risk_pct, self.config.MAX_POSITION_PCT)  # Cap at 5%
        
        # Calculate position size from risk
        risk_amount = capital * risk_pct
        
        # Get stop distance
        atr = getattr(market_state, 'atr', 0)
        stop_distance = atr * self._get_trailing_mult(harmony) if atr > 0 else capital * 0.02
        
        price = getattr(market_state, 'price', 1)
        position_value = (risk_amount / stop_distance) * price if stop_distance > 0 else 0
        
        # Cap at max position
        max_position = capital * self.config.MAX_POSITION_PCT
        final_size = min(position_value, max_position, base_size)
        
        return max(0, final_size)
    
    def get_exit_params(self, decision: Any, market_state: Any) -> Dict[str, float]:
        """
        Get optimized exit parameters based on harmony and trend
        """
        harmony = getattr(decision, 'harmony_score', 0.5)
        trend_aligned = self._is_trend_aligned(decision, market_state)
        rsi = getattr(market_state, 'rsi', 50)
        
        # Trailing stop multiplier
        if harmony > 0.75:
            trailing_mult = self.config.TRAILING_MULT_HIGH_HARMONY
        else:
            trailing_mult = self.config.TRAILING_MULT_LOW_HARMONY
        
        # Take profit multiplier (dynamic based on RSI momentum)
        rsi_momentum = (rsi - 50) / 50  # -1 to 1
        tp_mult = self.config.TP_MULT_BASE * (1 + abs(rsi_momentum) * 0.5)
        
        # Max hold bars
        max_hold = self.config.MAX_HOLD_TREND_ALIGNED if trend_aligned else self.config.MAX_HOLD_TREND_MISALIGNED
        
        return {
            'trailing_mult': trailing_mult,
            'tp_mult': tp_mult,
            'max_hold': max_hold
        }
    
    def _calculate_quality_score(self, decision: Any, market_state: Any) -> float:
        """Calculate overall trade quality score (0-1)"""
        harmony = getattr(decision, 'harmony_score', 0.0)
        confidence = getattr(decision, 'confidence', 0.0)
        coherence = getattr(decision, 'coherence', 0.0)
        
        # Weighted average
        score = (harmony * 0.4 + confidence * 0.35 + coherence * 0.25)
        return min(1.0, max(0.0, score))
    
    def _get_trailing_mult(self, harmony: float) -> float:
        """Get trailing stop multiplier based on harmony"""
        if harmony > 0.75:
            return self.config.TRAILING_MULT_HIGH_HARMONY
        return self.config.TRAILING_MULT_LOW_HARMONY
    
    def _is_trend_aligned(self, decision: Any, market_state: Any) -> bool:
        """Check if trade aligns with trend"""
        action = getattr(decision, 'action', None)
        trend_1d = getattr(market_state, 'trend_1d', 0)
        
        if action and hasattr(action, 'name'):
            action_name = action.name
            if action_name == 'BUY' and trend_1d > 0:
                return True
            if action_name == 'SELL' and trend_1d < 0:
                return True
        return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get guardian statistics"""
        total = sum(self.rejection_stats.values())
        if total == 0:
            return self.rejection_stats
        
        return {
            **self.rejection_stats,
            'pass_rate': self.rejection_stats['passed'] / total,
            'rejection_rate': 1 - (self.rejection_stats['passed'] / total),
            'total_checked': total
        }


def create_v10_config(audit_insights: Optional[Dict] = None) -> V10Config:
    """Create v10 config optimized based on audit data"""
    if audit_insights is None:
        return V10Config()
    
    # Could adjust parameters based on actual audit findings
    return V10Config(
        MIN_HARMONY=audit_insights.get('optimal_harmony_threshold', 0.70),
        MIN_CONFIDENCE=audit_insights.get('optimal_confidence_threshold', 0.75)
    )
