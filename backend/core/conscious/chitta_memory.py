"""
Chitta Memory v2 - Persistent Trade Memory with Embeddings
Implements samskaras (mental impressions) for learning from past trades
"""

import hashlib
import json
import pickle
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np


@dataclass
class TradeExperience:
    """Individual trade experience stored in Chitta"""

    trade_id: str
    timestamp: str
    symbol: str
    side: str
    entry_price: float
    exit_price: float
    size: float
    net_pnl: float
    return_pct: float
    bars_held: int

    # Market context at entry
    market_regime: str
    trend_1d: float
    adx: float
    rsi: float
    volatility: float

    # Decision context
    harmony_score: float
    confidence: float
    coherence: float
    dominant_element: str
    guna_dominant: str
    is_maya: bool

    # Exit context
    exit_reason: str
    max_favorable_excursion: float = 0.0
    max_adverse_excursion: float = 0.0

    def to_embedding(self) -> np.ndarray:
        """Create numerical embedding for similarity search"""
        return np.array(
            [
                self.trend_1d,
                self.adx / 100.0,
                self.rsi / 100.0,
                self.volatility * 10,
                self.harmony_score,
                self.confidence,
                1.0 if self.is_maya else 0.0,
                1.0 if self.side == "buy" else -1.0,
                self.return_pct * 10,  # Scale for impact
            ]
        )

    def is_win(self) -> bool:
        return self.net_pnl > 0


@dataclass
class StrategyPerformance:
    """Performance tracking for each strategy pattern"""

    strategy_hash: str
    pattern_signature: Dict[str, Any]

    # Metrics
    total_trades: int = 0
    wins: int = 0
    losses: int = 0
    total_pnl: float = 0.0
    avg_return: float = 0.0
    max_drawdown: float = 0.0

    # Temporal tracking
    last_used: str = field(default_factory=lambda: datetime.now().isoformat())
    consecutive_losses: int = 0

    @property
    def win_rate(self) -> float:
        return self.wins / max(1, self.total_trades)

    @property
    def is_active(self) -> bool:
        """Strategy is active if not in loss streak"""
        return self.consecutive_losses < 3

    def update(self, trade: TradeExperience):
        """Update strategy with new trade result"""
        self.total_trades += 1
        self.total_pnl += trade.net_pnl

        if trade.is_win():
            self.wins += 1
            self.consecutive_losses = 0
        else:
            self.losses += 1
            self.consecutive_losses += 1

        # Recalculate average
        self.avg_return = self.total_pnl / self.total_trades
        self.last_used = datetime.now().isoformat()


class ChittaMemory:
    """
    Conscious Memory - Stores trade experiences and learns patterns

    Implements:
    - Samskaras (mental impressions from past trades)
    - Pattern recognition via embeddings
    - Strategy performance tracking
    - Reflection capabilities
    """

    def __init__(self, storage_path: str = "backend/data/conscious_memory"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)

        # Memory stores
        self.trades: List[TradeExperience] = []
        self.strategies: Dict[str, StrategyPerformance] = {}
        self.session_stats = {
            "total_pnl": 0.0,
            "current_drawdown": 0.0,
            "peak_capital": 0.0,
            "loss_streak": 0,
            "trades_today": 0,
        }

        # Load existing memory
        self._load_memory()

        print(
            f"[CHITTA] Memory initialized: {len(self.trades)} trades, {len(self.strategies)} strategies"
        )

    def store_trade(self, trade: TradeExperience):
        """Store trade in memory (samskara formation)"""
        self.trades.append(trade)

        # Update session stats
        self.session_stats["total_pnl"] += trade.net_pnl
        if trade.is_win():
            self.session_stats["loss_streak"] = 0
        else:
            self.session_stats["loss_streak"] += 1

        # Update strategy performance
        strategy_hash = self._hash_strategy(trade)
        if strategy_hash not in self.strategies:
            self.strategies[strategy_hash] = StrategyPerformance(
                strategy_hash=strategy_hash,
                pattern_signature=self._extract_pattern(trade),
            )

        self.strategies[strategy_hash].update(trade)

        # Persist
        self._save_memory()

    def reflect_recent(self, n_trades: int = 10) -> Dict[str, Any]:
        """
        Reflect on recent trades
        Returns insights for course correction
        """
        if len(self.trades) < n_trades:
            return {"insight": "Insufficient data", "action": "continue"}

        recent = self.trades[-n_trades:]

        # Calculate metrics
        wins = sum(1 for t in recent if t.is_win())
        total_pnl = sum(t.net_pnl for t in recent)
        avg_harmony = sum(t.harmony_score for t in recent) / len(recent)
        maya_count = sum(1 for t in recent if t.is_maya)

        # Detect patterns
        insights = []
        action = "continue"

        if wins < n_trades * 0.3:
            insights.append(f"Low win rate: {wins}/{n_trades}")
            action = "pause_and_reflect"

        if total_pnl < -1000:
            insights.append(f"Significant losses: ${total_pnl:.2f}")
            action = "reduce_size"

        if maya_count > n_trades * 0.3:
            insights.append(f"High Maya rate: {maya_count}/{n_trades}")
            action = "tighten_filters"

        if avg_harmony < 0.6:
            insights.append(f"Low avg harmony: {avg_harmony:.2f}")
            action = "wait_for_clarity"

        return {
            "n_trades": n_trades,
            "wins": wins,
            "win_rate": wins / n_trades,
            "total_pnl": total_pnl,
            "avg_harmony": avg_harmony,
            "maya_rate": maya_count / n_trades,
            "insights": insights,
            "recommended_action": action,
        }

    def retrieve_similar_setups(self, market_state: Any, top_k: int = 5) -> List[TradeExperience]:
        """
        RAG: Retrieve similar historical setups
        Uses embedding similarity
        """
        if len(self.trades) < 10:
            return []

        # Create embedding for current market
        current_embedding = np.array(
            [
                getattr(market_state, "trend_1d", 0),
                getattr(market_state, "adx", 25) / 100.0,
                getattr(market_state, "rsi", 50) / 100.0,
                getattr(market_state, "volatility", 0.02) * 10,
                0.6,  # assumed harmony
                0.5,  # assumed confidence
                0.0,  # not maya
                0.0,  # neutral side
                0.0,  # unknown return
            ]
        )

        # Calculate similarities
        similarities = []
        for trade in self.trades[-500:]:  # Last 500 trades
            trade_emb = trade.to_embedding()
            similarity = np.dot(current_embedding, trade_emb) / (
                np.linalg.norm(current_embedding) * np.linalg.norm(trade_emb)
            )
            similarities.append((similarity, trade))

        # Sort by similarity
        similarities.sort(key=lambda x: x[0], reverse=True)

        return [t for _, t in similarities[:top_k]]

    def get_top_strategies(self, n: int = 3) -> List[StrategyPerformance]:
        """Get top performing active strategies"""
        active = [s for s in self.strategies.values() if s.is_active and s.total_trades >= 5]

        # Sort by Sharpe-like metric (return / drawdown)
        scored = []
        for s in active:
            score = (
                s.avg_return / (s.max_drawdown + 0.01) if s.max_drawdown > 0 else s.avg_return * 10
            )
            scored.append((score, s))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [s for _, s in scored[:n]]

    def should_pause_trading(self, drawdown_limit: float = 0.08) -> Tuple[bool, str]:
        """Determine if trading should pause based on memory"""
        # Check drawdown
        if self.session_stats["current_drawdown"] > drawdown_limit:
            return (
                True,
                f"Drawdown {self.session_stats['current_drawdown']:.1%} > {drawdown_limit:.1%}",
            )

        # Check loss streak
        if self.session_stats["loss_streak"] >= 3:
            return True, f"Loss streak: {self.session_stats['loss_streak']} trades"

        # Check reflection
        reflection = self.reflect_recent(5)
        if reflection["recommended_action"] in [
            "pause_and_reflect",
            "wait_for_clarity",
        ]:
            return True, f"Reflection: {reflection['insights']}"

        return False, ""

    def update_drawdown(self, current_equity: float):
        """Update drawdown tracking"""
        if current_equity > self.session_stats["peak_capital"]:
            self.session_stats["peak_capital"] = current_equity

        if self.session_stats["peak_capital"] > 0:
            self.session_stats["current_drawdown"] = (
                self.session_stats["peak_capital"] - current_equity
            ) / self.session_stats["peak_capital"]

    def _hash_strategy(self, trade: TradeExperience) -> str:
        """Create hash for strategy pattern"""
        key = f"{trade.market_regime}_{trade.dominant_element}_{trade.guna_dominant}_{'maya' if trade.is_maya else 'clear'}"
        return hashlib.md5(key.encode(), usedforsecurity=False).hexdigest()[:16]

    def _extract_pattern(self, trade: TradeExperience) -> Dict[str, Any]:
        """Extract pattern signature from trade"""
        return {
            "market_regime": trade.market_regime,
            "dominant_element": trade.dominant_element,
            "guna_dominant": trade.guna_dominant,
            "is_maya": trade.is_maya,
            "avg_harmony": trade.harmony_score,
        }

    def _save_memory(self):
        """Persist memory to disk"""
        data = {
            "trades": [asdict(t) for t in self.trades[-2000:]],  # Keep last 2000
            "strategies": {k: asdict(v) for k, v in self.strategies.items()},
            "session_stats": self.session_stats,
            "last_save": datetime.now().isoformat(),
        }

        with open(self.storage_path / "chitta_memory.json", "w") as f:
            json.dump(data, f, indent=2, default=str)

    def _load_memory(self):
        """Load memory from disk"""
        memory_file = self.storage_path / "chitta_memory.json"
        if memory_file.exists():
            try:
                with open(memory_file, "r") as f:
                    data = json.load(f)

                # Load trades
                for t_data in data.get("trades", []):
                    self.trades.append(TradeExperience(**t_data))

                # Load strategies
                for k, v in data.get("strategies", {}).items():
                    self.strategies[k] = StrategyPerformance(**v)

                # Load stats
                self.session_stats.update(data.get("session_stats", {}))

            except Exception as e:
                print(f"[CHITTA] Error loading memory: {e}")

    def get_summary(self) -> Dict[str, Any]:
        """Get memory summary"""
        total_trades = len(self.trades)
        wins = sum(1 for t in self.trades if t.is_win())

        return {
            "total_trades_stored": total_trades,
            "overall_win_rate": wins / max(1, total_trades),
            "total_pnl": sum(t.net_pnl for t in self.trades),
            "active_strategies": sum(1 for s in self.strategies.values() if s.is_active),
            "current_drawdown": self.session_stats["current_drawdown"],
            "loss_streak": self.session_stats["loss_streak"],
        }
