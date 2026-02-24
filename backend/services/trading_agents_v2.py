"""
Trading Agents V2 - Optimized for Live Performance

Based on paper trading results:
- Reduced position sizes for better risk management
- Improved signal quality with additional filters
- Balanced BUY/SELL ratio
- Added volatility filtering
"""

import logging
import os
import sys
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.services.data_prefetch_agent import DataPreFetchAgent, PriceData

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
    confidence: float
    reason: str
    position_size: float
    timestamp: datetime
    price_data: PriceData | None = None
    executed: bool = False
    execution_result: str | None = None


@dataclass
class AgentPerformance:
    """Track agent performance."""

    total_decisions: int = 0
    trades_executed: int = 0
    successful_trades: int = 0
    total_pnl: float = 0.0
    avg_confidence: float = 0.0
    last_trade_time: datetime | None = None


class BaseTradingAgent:
    """Base class for all trading agents."""

    def __init__(
        self,
        name: str,
        strategy: str,
        risk_per_trade: float = 0.02,  # Reduced from 0.05 for better risk management
        min_confidence: float = 0.35,  # Increased from 0.3 for better signal quality
        max_positions: int = 5,  # Reduced from 10
        paper_trading_mode: bool = True,
        cooldown_seconds: int = 10,  # Minimum time between trades
    ):
        self.name = name
        self.strategy = strategy
        self.risk_per_trade = risk_per_trade
        self.min_confidence = min_confidence
        self.max_positions = max_positions
        self.paper_trading_mode = paper_trading_mode
        self.cooldown_seconds = cooldown_seconds

        self.performance = AgentPerformance()
        self.price_history: dict[str, list[PriceData]] = {}
        self.active_positions: dict[str, dict] = {}
        self.last_trade_time: dict[str, datetime] = {}  # Track last trade per symbol

    def _check_cooldown(self, symbol: str) -> bool:
        """Check if enough time has passed since last trade."""
        if symbol not in self.last_trade_time:
            return True
        elapsed = (datetime.now() - self.last_trade_time[symbol]).total_seconds()
        return elapsed >= self.cooldown_seconds

    async def decide(
        self,
        symbol: str,
        price_data: PriceData,
        portfolio_value: float,
        data_agent: DataPreFetchAgent,
    ) -> AgentDecision | None:
        """Make trading decision based on cached price data."""
        # Check cooldown
        if not self._check_cooldown(symbol):
            return None

        # Update price history
        if symbol not in self.price_history:
            self.price_history[symbol] = []
        self.price_history[symbol].append(price_data)
        if len(self.price_history[symbol]) > 100:
            self.price_history[symbol] = self.price_history[symbol][-100:]

        # Check data freshness
        if not price_data.is_fresh(max_age_seconds=60.0):
            logger.debug(f"[{self.name}] Stale data for {symbol}, skipping")
            return None

        # Strategy-specific analysis
        decision = await self._analyze(
            symbol, price_data, self.price_history[symbol], portfolio_value
        )

        if decision and decision.confidence >= self.min_confidence:
            self.performance.total_decisions += 1
            self.last_trade_time[symbol] = datetime.now()
            return decision

        return None

    async def _analyze(
        self, symbol: str, price_data: PriceData, history: list[PriceData], portfolio_value: float
    ) -> AgentDecision | None:
        """Override in subclass."""
        raise NotImplementedError

    def _calculate_position_size(
        self, confidence: float, portfolio_value: float, current_price: float
    ) -> float:
        """Calculate position size with Kelly criterion approximation."""
        # Kelly fraction: f = (p*b - q) / b
        # Simplified: use confidence as edge estimate
        kelly_fraction = confidence * 2 - 1  # Scale confidence to [-1, 1]
        kelly_fraction = max(0.1, min(0.5, kelly_fraction))  # Cap at half-Kelly

        position_eur = portfolio_value * self.risk_per_trade * kelly_fraction

        # Max 10% per trade (reduced from 15%)
        return min(position_eur, portfolio_value * 0.10)

    def update_performance(self, pnl: float):
        """Update performance metrics after trade closes."""
        self.performance.trades_executed += 1
        self.performance.total_pnl += pnl
        if pnl > 0:
            self.performance.successful_trades += 1
        self.performance.last_trade_time = datetime.now()


class SpreadMomentumAgent(BaseTradingAgent):
    """
    Optimized spread-based strategy.

    Improvements:
    - Added volatility filter (avoid choppy markets)
    - Balanced BUY/SELL signals
    - Reduced trade frequency with cooldown
    """

    def __init__(self):
        super().__init__(
            name="SpreadMomentum",
            strategy="spread_momentum",
            risk_per_trade=0.03,  # Conservative
            min_confidence=0.40,  # Higher quality signals
            cooldown_seconds=15,  # Don't overtrade
        )
        self.buy_signals = 0
        self.sell_signals = 0

    async def _analyze(
        self, symbol: str, price_data: PriceData, history: list[PriceData], portfolio_value: float
    ) -> AgentDecision | None:

        current = price_data.price

        # Need at least 3 points for volatility calc
        if len(history) < 3:
            return None

        recent_prices = [h.price for h in history[-10:]]
        price_range = max(recent_prices) - min(recent_prices)
        spread_pct = price_range / current if current > 0 else 0

        # Volatility filter: skip if market is too choppy
        if spread_pct > 0.05:  # >5% range is too volatile
            return None

        # Balanced signal generation
        # If we've generated more BUY than SELL, bias toward SELL
        signal_bias = 0
        if self.buy_signals > self.sell_signals + 5:
            signal_bias = 0.001  # Make SELL more likely
        elif self.sell_signals > self.buy_signals + 5:
            signal_bias = -0.001  # Make BUY more likely

        # Tight spread = bullish
        if spread_pct < 0.003 + signal_bias:
            confidence = 0.5 + (0.003 - spread_pct) * 100
            self.buy_signals += 1
            return AgentDecision(
                agent_name=self.name,
                strategy=self.strategy,
                symbol=symbol,
                action=DecisionAction.BUY,
                confidence=min(confidence, 0.75),
                reason=f"Low volatility, tight spread ({spread_pct*100:.2f}%)",
                position_size=self._calculate_position_size(confidence, portfolio_value, current),
                timestamp=datetime.now(),
                price_data=price_data,
            )

        # Wide spread after uptrend = bearish
        elif spread_pct > 0.008 + signal_bias:
            # Check if we had an uptrend
            if len(history) >= 5:
                recent_return = (current - history[-5].price) / history[-5].price
                if recent_return > 0.01:  # Was up >1%
                    confidence = 0.5 + min(0.3, spread_pct * 20)
                    self.sell_signals += 1
                    return AgentDecision(
                        agent_name=self.name,
                        strategy=self.strategy,
                        symbol=symbol,
                        action=DecisionAction.SELL,
                        confidence=min(confidence, 0.75),
                        reason=f"Wide spread ({spread_pct*100:.2f}%) after +{recent_return*100:.1f}%",
                        position_size=self._calculate_position_size(
                            confidence, portfolio_value, current
                        ),
                        timestamp=datetime.now(),
                        price_data=price_data,
                    )

        return None


class MomentumAgent(BaseTradingAgent):
    """Trend-following with mean reversion protection."""

    def __init__(self):
        super().__init__(
            name="Momentum",
            strategy="momentum",
            risk_per_trade=0.04,
            min_confidence=0.45,
            cooldown_seconds=20,
        )

    async def _analyze(
        self, symbol: str, price_data: PriceData, history: list[PriceData], portfolio_value: float
    ) -> AgentDecision | None:

        min_history = 5 if self.paper_trading_mode else 10
        if len(history) < min_history:
            return None

        prices = [h.price for h in history[-15:]]  # Longer lookback
        current = price_data.price

        # Multiple timeframe MAs
        short_ma = sum(prices[-3:]) / 3
        medium_ma = sum(prices[-8:]) / 8
        long_ma = sum(prices) / len(prices)

        # Trend strength
        trend_strength = abs(current - long_ma) / long_ma

        # Avoid weak trends
        if trend_strength < 0.005:  # < 0.5% from MA
            return None

        # Uptrend confirmation (all MAs aligned)
        if current > short_ma > medium_ma > long_ma:
            # Check for pullback entry
            pullback = (current - prices[-1]) / prices[-1] if prices[-1] > 0 else 0
            if pullback > -0.02:  # Not in freefall
                confidence = 0.5 + min(0.4, trend_strength * 20)
                return AgentDecision(
                    agent_name=self.name,
                    strategy=self.strategy,
                    symbol=symbol,
                    action=DecisionAction.BUY,
                    confidence=min(confidence, 0.85),
                    reason=f"Uptrend +{trend_strength*100:.1f}%, MAs aligned",
                    position_size=self._calculate_position_size(
                        confidence, portfolio_value, current
                    ),
                    timestamp=datetime.now(),
                    price_data=price_data,
                )

        # Downtrend confirmation
        elif current < short_ma < medium_ma < long_ma:
            bounce = (current - prices[-1]) / prices[-1] if prices[-1] > 0 else 0
            if bounce < 0.02:  # Not bouncing back hard
                confidence = 0.5 + min(0.4, trend_strength * 20)
                return AgentDecision(
                    agent_name=self.name,
                    strategy=self.strategy,
                    symbol=symbol,
                    action=DecisionAction.SELL,
                    confidence=min(confidence, 0.85),
                    reason=f"Downtrend -{trend_strength*100:.1f}%, MAs aligned",
                    position_size=self._calculate_position_size(
                        confidence, portfolio_value, current
                    ),
                    timestamp=datetime.now(),
                    price_data=price_data,
                )

        return None


class MeanReversionAgent(BaseTradingAgent):
    """Mean reversion with Bollinger Bands style bands."""

    def __init__(self):
        super().__init__(
            name="MeanReversion",
            strategy="mean_reversion",
            risk_per_trade=0.03,
            min_confidence=0.40,
            cooldown_seconds=30,  # Longer cooldown for mean reversion
        )

    async def _analyze(
        self, symbol: str, price_data: PriceData, history: list[PriceData], portfolio_value: float
    ) -> AgentDecision | None:

        min_history = 10 if self.paper_trading_mode else 20
        if len(history) < min_history:
            return None

        prices = [h.price for h in history[-20:]]
        current = price_data.price

        # Calculate MA and standard deviation
        ma = sum(prices) / len(prices)
        variance = sum((p - ma) ** 2 for p in prices) / len(prices)
        std_dev = variance**0.5

        # Bollinger Bands style
        upper_band = ma + 2 * std_dev
        lower_band = ma - 2 * std_dev

        # Price below lower band = buy (oversold)
        if current < lower_band:
            confidence = 0.5 + min(0.4, (lower_band - current) / std_dev * 0.2)
            return AgentDecision(
                agent_name=self.name,
                strategy=self.strategy,
                symbol=symbol,
                action=DecisionAction.BUY,
                confidence=min(confidence, 0.80),
                reason=f"Oversold: {((current/ma-1)*100):+.1f}% vs MA",
                position_size=self._calculate_position_size(confidence, portfolio_value, current),
                timestamp=datetime.now(),
                price_data=price_data,
            )

        # Price above upper band = sell (overbought)
        elif current > upper_band:
            confidence = 0.5 + min(0.4, (current - upper_band) / std_dev * 0.2)
            return AgentDecision(
                agent_name=self.name,
                strategy=self.strategy,
                symbol=symbol,
                action=DecisionAction.SELL,
                confidence=min(confidence, 0.80),
                reason=f"Overbought: {((current/ma-1)*100):+.1f}% vs MA",
                position_size=self._calculate_position_size(confidence, portfolio_value, current),
                timestamp=datetime.now(),
                price_data=price_data,
            )

        return None


class BreakoutAgent(BaseTradingAgent):
    """Breakout with volume confirmation simulation."""

    def __init__(self):
        super().__init__(
            name="Breakout",
            strategy="breakout",
            risk_per_trade=0.05,
            min_confidence=0.50,  # Higher threshold for breakouts
            cooldown_seconds=25,
        )

    async def _analyze(
        self, symbol: str, price_data: PriceData, history: list[PriceData], portfolio_value: float
    ) -> AgentDecision | None:

        min_history = 10 if self.paper_trading_mode else 15
        if len(history) < min_history:
            return None

        prices = [h.price for h in history[-15:]]
        current = price_data.price

        # Calculate support/resistance
        resistance = max(prices[:-3]) if len(prices) > 3 else max(prices)
        support = min(prices[:-3]) if len(prices) > 3 else min(prices)

        # Volume simulation: check if recent price moves were decisive
        recent_volatility = (
            sum(abs(prices[i] - prices[i - 1]) for i in range(1, len(prices[-5:]))) / 4
        )

        # Breakout above resistance
        if current > resistance * 1.005:  # 0.5% breakout
            breakout_strength = (current - resistance) / resistance
            if breakout_strength > recent_volatility / resistance * 2:  # Strong move
                confidence = 0.55 + min(0.35, breakout_strength * 50)
                return AgentDecision(
                    agent_name=self.name,
                    strategy=self.strategy,
                    symbol=symbol,
                    action=DecisionAction.BUY,
                    confidence=min(confidence, 0.85),
                    reason=f"Breakout +{breakout_strength*100:.2f}% above resistance",
                    position_size=self._calculate_position_size(
                        confidence, portfolio_value, current
                    ),
                    timestamp=datetime.now(),
                    price_data=price_data,
                )

        # Breakdown below support
        elif current < support * 0.995:  # 0.5% breakdown
            breakdown_strength = (support - current) / support
            if breakdown_strength > recent_volatility / support * 2:
                confidence = 0.55 + min(0.35, breakdown_strength * 50)
                return AgentDecision(
                    agent_name=self.name,
                    strategy=self.strategy,
                    symbol=symbol,
                    action=DecisionAction.SELL,
                    confidence=min(confidence, 0.85),
                    reason=f"Breakdown -{breakdown_strength*100:.2f}% below support",
                    position_size=self._calculate_position_size(
                        confidence, portfolio_value, current
                    ),
                    timestamp=datetime.now(),
                    price_data=price_data,
                )

        return None


class ScalperAgent(BaseTradingAgent):
    """High-frequency scalping with improved risk management."""

    def __init__(self):
        super().__init__(
            name="Scalper",
            strategy="scalping",
            risk_per_trade=0.02,  # Very small positions
            min_confidence=0.50,
            cooldown_seconds=5,  # Very short cooldown
        )
        self.last_direction = {}  # Track last trade direction per symbol

    async def _analyze(
        self, symbol: str, price_data: PriceData, history: list[PriceData], portfolio_value: float
    ) -> AgentDecision | None:

        min_history = 3 if self.paper_trading_mode else 5
        if len(history) < min_history:
            return None

        current = price_data.price
        prev = history[-2].price
        prev2 = history[-3].price if len(history) >= 3 else prev

        # Calculate momentum
        delta_pct = (current - prev) / prev if prev > 0 else 0
        prev_delta_pct = (prev - prev2) / prev2 if prev2 > 0 else 0

        # Only trade in direction of momentum
        # And only if momentum is accelerating
        threshold = 0.0008  # 0.08% move

        # Long momentum
        if delta_pct > threshold and delta_pct > prev_delta_pct:
            # Check last direction - don't chase if already bought
            if self.last_direction.get(symbol) != "BUY":
                confidence = 0.55 + min(0.3, delta_pct * 100)
                self.last_direction[symbol] = "BUY"
                return AgentDecision(
                    agent_name=self.name,
                    strategy=self.strategy,
                    symbol=symbol,
                    action=DecisionAction.BUY,
                    confidence=min(confidence, 0.80),
                    reason=f"Momentum +{delta_pct*100:.3f}% (accel)",
                    position_size=self._calculate_position_size(
                        confidence, portfolio_value, current
                    ),
                    timestamp=datetime.now(),
                    price_data=price_data,
                )

        # Short momentum
        elif delta_pct < -threshold and delta_pct < prev_delta_pct:
            if self.last_direction.get(symbol) != "SELL":
                confidence = 0.55 + min(0.3, abs(delta_pct) * 100)
                self.last_direction[symbol] = "SELL"
                return AgentDecision(
                    agent_name=self.name,
                    strategy=self.strategy,
                    symbol=symbol,
                    action=DecisionAction.SELL,
                    confidence=min(confidence, 0.80),
                    reason=f"Momentum {delta_pct*100:.3f}% (accel)",
                    position_size=self._calculate_position_size(
                        confidence, portfolio_value, current
                    ),
                    timestamp=datetime.now(),
                    price_data=price_data,
                )

        return None


class PositionTraderAgent(BaseTradingAgent):
    """Long-term position trading with trend confirmation."""

    def __init__(self):
        super().__init__(
            name="PositionTrader",
            strategy="position",
            risk_per_trade=0.08,
            min_confidence=0.60,  # High confidence for big positions
            cooldown_seconds=60,  # Very long cooldown
        )

    async def _analyze(
        self, symbol: str, price_data: PriceData, history: list[PriceData], portfolio_value: float
    ) -> AgentDecision | None:

        min_history = 15 if self.paper_trading_mode else 25
        if len(history) < min_history:
            return None

        prices = [h.price for h in history[-25:]]
        current = price_data.price

        # Long-term MA
        ma = sum(prices) / len(prices)
        deviation = (current - ma) / ma

        # Only trade strong deviations
        if abs(deviation) < 0.05:  # Need >5% deviation
            return None

        # Check trend consistency
        uptrend_count = sum(1 for i in range(1, len(prices)) if prices[i] > prices[i - 1])
        trend_consistency = uptrend_count / (len(prices) - 1)

        if deviation > 0.05 and trend_consistency > 0.65:  # Strong uptrend
            confidence = 0.6 + min(0.35, deviation * 3)
            return AgentDecision(
                agent_name=self.name,
                strategy=self.strategy,
                symbol=symbol,
                action=DecisionAction.BUY,
                confidence=min(confidence, 0.90),
                reason=f"Strong uptrend +{deviation*100:.1f}% (consistency: {trend_consistency:.0%})",
                position_size=self._calculate_position_size(confidence, portfolio_value, current),
                timestamp=datetime.now(),
                price_data=price_data,
            )

        elif deviation < -0.05 and trend_consistency < 0.35:  # Strong downtrend
            confidence = 0.6 + min(0.35, abs(deviation) * 3)
            return AgentDecision(
                agent_name=self.name,
                strategy=self.strategy,
                symbol=symbol,
                action=DecisionAction.SELL,
                confidence=min(confidence, 0.90),
                reason=f"Strong downtrend {deviation*100:.1f}% (consistency: {1-trend_consistency:.0%})",
                position_size=self._calculate_position_size(confidence, portfolio_value, current),
                timestamp=datetime.now(),
                price_data=price_data,
            )

        return None


def create_all_agents() -> list[BaseTradingAgent]:
    """Create all trading agents."""
    return [
        SpreadMomentumAgent(),
        MomentumAgent(),
        MeanReversionAgent(),
        BreakoutAgent(),
        ScalperAgent(),
        PositionTraderAgent(),
    ]
