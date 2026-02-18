"""
Consciousness Strategy for the custom BacktestEngine.

Extends Strategy ABC to integrate the Triple-Layer Consciousness Architecture:
1. Regime Detection (Soul layer)
2. Regime-aware trade logic (Mind layer)
3. Karma Episode Memory (Learning layer)

Uses Kelly Criterion position sizing and records trade outcomes
as KarmaEpisodes for regime-weighted causal learning.
"""

import time
from datetime import datetime
from typing import Any, Dict, List, Optional

from backend.backtesting.exchange import SimulatedExchange
from backend.backtesting.models import OrderSide, Trade
from backend.backtesting.position_sizing import (KellyCriterionSizer,
                                                 PositionSizer)
from backend.backtesting.strategy import Strategy
from backend.core.karma.episode_memory import EpisodeMemory, KarmaEpisode
from backend.core.regime_detector import RegimeDetector
from backend.core.schemas.ooda_types import MarketRegime


class ConsciousnessStrategy(Strategy):
    """
    Consciousness-Aware Trading Strategy.

    Adapts trading behavior based on detected market regime and karma memory.
    - BULL / BEAR  -> Trend-following (SMA crossover)
    - SIDEWAYS     -> Mean-reversion (Bollinger band bounce)
    - VOLATILE     -> Defensive (no new entries)
    - Rahu Kala    -> Full defense (halts all trading)
    """

    def __init__(
        self,
        exchange: SimulatedExchange,
        force_rahu: bool = False,
        position_sizer: Optional[PositionSizer] = None,
        **kwargs,
    ):
        super().__init__(
            exchange,
            position_sizer=position_sizer
            or KellyCriterionSizer(
                win_rate=0.55, avg_win=1.5, avg_loss=1.0, fractional_kelly=0.25
            ),
            **kwargs,
        )
        self.regime_detector = RegimeDetector()
        self.episode_memory = EpisodeMemory()
        self.price_history: List[float] = []
        self.force_rahu = force_rahu
        self._last_trade_price: Optional[float] = None
        self._current_regime = MarketRegime.SIDEWAYS

    # ------------------------------------------------------------------
    # Lifecycle hooks called by BacktestEngine
    # ------------------------------------------------------------------

    async def on_start(self):
        """Called once before the backtest loop starts."""
        pass

    async def on_stop(self):
        """Called once after the backtest loop ends."""
        pass

    async def on_bar(self, symbol: str, bar: Dict[str, Any]):
        """Process a single OHLCV bar."""
        close = bar.get("close", 0.0)
        if close <= 0:
            return

        timestamp = bar.get("timestamp", bar.get("datetime", datetime.now()))
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)
        volume = bar.get("volume", 1000.0)

        self.price_history.append(close)

        # -- Soul Layer: Regime Detection --
        sma_50, sma_200, vol = self.regime_detector.calculate_indicators(
            self.price_history
        )
        self._current_regime = self.regime_detector.detect(close, sma_50, sma_200, vol)

        # -- Rahu Kala defense --
        if self.force_rahu:
            return

        # -- Mind Layer: Strategy Selection --
        position = self.exchange.positions.get(symbol)
        current_qty = position.quantity if position else 0.0

        if self._current_regime in (MarketRegime.BULL, MarketRegime.BEAR):
            self._trend_following_logic(symbol, close, current_qty, timestamp, volume)
        elif self._current_regime == MarketRegime.SIDEWAYS:
            self._mean_reversion_logic(symbol, close, current_qty, timestamp, volume)
        # VOLATILE -> no new entries (defensive)

        # Update portfolio value
        portfolio_value = self.exchange.cash
        for sym, pos in self.exchange.positions.items():
            portfolio_value += pos.quantity * pos.current_price
        self.update_portfolio_value(portfolio_value)

    # ------------------------------------------------------------------
    # Strategy logic
    # ------------------------------------------------------------------

    def _trend_following_logic(
        self,
        symbol: str,
        close: float,
        current_qty: float,
        timestamp: datetime,
        volume: float,
    ):
        """Simple SMA crossover trend logic."""
        if len(self.price_history) < 30:
            return

        short_ma = sum(self.price_history[-10:]) / 10
        long_ma = sum(self.price_history[-30:]) / 30
        signal_strength = min(1.0, abs(short_ma - long_ma) / long_ma)

        if short_ma > long_ma and current_qty == 0:
            size = self.calculate_position_size(close, signal_strength)
            if size > 0:
                trade = self.execute_order(
                    symbol=symbol,
                    side=OrderSide.BUY,
                    quantity=size,
                    current_price=close,
                    timestamp=timestamp,
                    available_volume=volume,
                )
                if trade:
                    self._last_trade_price = close
                    self._record_episode(trade)

        elif short_ma < long_ma and current_qty > 0:
            trade = self.execute_order(
                symbol=symbol,
                side=OrderSide.SELL,
                quantity=current_qty,
                current_price=close,
                timestamp=timestamp,
                available_volume=volume,
            )
            if trade:
                self._record_episode(trade)
                self._last_trade_price = None

    def _mean_reversion_logic(
        self,
        symbol: str,
        close: float,
        current_qty: float,
        timestamp: datetime,
        volume: float,
    ):
        """Bollinger-band-style mean reversion."""
        if len(self.price_history) < 20:
            return

        import numpy as np

        recent = self.price_history[-20:]
        mean = float(np.mean(recent))
        std = float(np.std(recent))
        if std == 0:
            return

        z_score = (close - mean) / std
        signal_strength = min(1.0, abs(z_score) / 2.0)

        # Buy when oversold (z < -1), sell when overbought (z > 1)
        if z_score < -1.0 and current_qty == 0:
            size = self.calculate_position_size(close, signal_strength)
            if size > 0:
                trade = self.execute_order(
                    symbol=symbol,
                    side=OrderSide.BUY,
                    quantity=size,
                    current_price=close,
                    timestamp=timestamp,
                    available_volume=volume,
                )
                if trade:
                    self._last_trade_price = close
                    self._record_episode(trade)

        elif z_score > 1.0 and current_qty > 0:
            trade = self.execute_order(
                symbol=symbol,
                side=OrderSide.SELL,
                quantity=current_qty,
                current_price=close,
                timestamp=timestamp,
                available_volume=volume,
            )
            if trade:
                self._record_episode(trade)
                self._last_trade_price = None

    # ------------------------------------------------------------------
    # Karma Recording
    # ------------------------------------------------------------------

    def _record_episode(self, trade: Trade):
        """Record trade outcome as a KarmaEpisode."""
        pnl = 0.0
        if self._last_trade_price and trade.side == OrderSide.SELL:
            pnl = (trade.price - self._last_trade_price) / self._last_trade_price

        self.episode_memory.record(
            KarmaEpisode(
                timestamp=time.time(),
                regime=self._current_regime.value,
                strategy="ConsciousnessStrategy",
                action=1 if trade.side == OrderSide.BUY else 2,
                pnl_percent=pnl,
                drawdown_percent=0.0,
                duration_ms=0,
                karma_score=min(1.0, max(-1.0, pnl * 10)) if pnl != 0 else 0.0,
            )
        )
