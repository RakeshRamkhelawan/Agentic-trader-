"""
Strategy Evolution - Langetermijn strategie aanpassingen

Agents kunnen hun strategieen evolueren gebaseerd op:
- Winrate per marktregime
- Performance per symbool-type
- Seizoenspatronen
- Macro-omstandigheden
"""

import json
import logging
import statistics
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from backend.agents.multi_llm_provider import get_multi_llm

logger = logging.getLogger(__name__)


@dataclass
class StrategyProfile:
    """Evolving strategy configuration."""

    strategy_name: str
    version: int = 1
    created_at: datetime = field(default_factory=datetime.now)

    # Parameters (worden aangepast)
    entry_threshold: float = 0.6
    exit_threshold: float = 0.4
    position_sizing: str = "kelly"
    max_positions: int = 5
    hold_time_preference: str = "medium"  # short/medium/long

    # Performance tracking
    wins: int = 0
    losses: int = 0
    total_pnl: float = 0.0
    sharpe_ratio: float = 0.0
    max_drawdown: float = 0.0

    # Context-specific performance
    regime_performance: Dict[str, Dict[str, float]] = field(default_factory=dict)
    symbol_performance: Dict[str, Dict[str, float]] = field(default_factory=dict)


@dataclass
class EvolutionSuggestion:
    """LLM-generated evolution suggestion."""

    parameter: str
    current_value: Any
    suggested_value: Any
    reasoning: str
    confidence: float
    expected_improvement: str


class StrategyEvolutionEngine:
    """
    Engine voor langetermijn strategie evolutie.
    """

    STRATEGY_EVOLUTION_PROMPT = """# Strategy Evolution Analysis

Je bent een elite trading strategie architect. Analyseer de performance data en stuur strategie verbeteringen voor.

## Huidige Strategie
{strategy_json}

## Performance Laatste 100 Trades
- Winrate: {winrate:.1%}
- Total PnL: {total_pnl:.2%}
- Sharpe Ratio: {sharpe_ratio:.2f}
- Max Drawdown: {max_drawdown:.1%}

## Performance per Marktregime
{regime_performance}

## Performance per Symbool-type
{symbol_performance}

## Opdracht
1. Identificeer zwakke parameters
2. Suggest verbeteringen met verwachte impact
3. Focus op regime-specifieke optimalisatie

## Output Format (JSON)
{{
    "analysis": "korte analyse van problemen",
    "suggestions": [
        {{
            "parameter": "parameter naam",
            "current_value": "huidige waarde",
            "suggested_value": "nieuwe waarde",
            "reasoning": "waarom deze aanpassing",
            "confidence": 0.8,
            "expected_improvement": "+5% winrate in ranging markets"
        }}
    ],
    "new_strategy_version": {new_version},
    "evolution_reasoning": "overkoepelende strategie shift"
}}

Geef ALLEEN de JSON output, geen markdown."""

    def __init__(self):
        self.multi_llm = get_multi_llm()
        self.strategies: Dict[str, StrategyProfile] = {}
        self.trade_history: List[Dict[str, Any]] = []
        self.evolution_log: List[Dict[str, Any]] = []

    def register_strategy(self, name: str, profile: StrategyProfile) -> None:
        """Registreer een strategie voor evolutie."""
        self.strategies[name] = profile
        logger.info(f"Strategy registered: {name}")

    def record_trade(
        self,
        strategy_name: str,
        symbol: str,
        regime: str,
        pnl: float,
        duration_days: int,
        metadata: Dict = None,
    ) -> None:
        """Record trade voor strategie analyse."""
        trade = {
            "timestamp": datetime.now(),
            "strategy": strategy_name,
            "symbol": symbol,
            "regime": regime,
            "pnl": pnl,
            "duration_days": duration_days,
            "metadata": metadata or {},
        }
        self.trade_history.append(trade)

        # Update strategy stats
        if strategy_name in self.strategies:
            profile = self.strategies[strategy_name]
            if pnl > 0:
                profile.wins += 1
            else:
                profile.losses += 1
            profile.total_pnl += pnl

            # Update regime performance
            if regime not in profile.regime_performance:
                profile.regime_performance[regime] = {"wins": 0, "losses": 0, "pnl": 0}
            profile.regime_performance[regime]["pnl"] += pnl
            if pnl > 0:
                profile.regime_performance[regime]["wins"] += 1
            else:
                profile.regime_performance[regime]["losses"] += 1

    def calculate_metrics(self, strategy_name: str) -> Dict[str, float]:
        """Bereken performance metrics."""
        if strategy_name not in self.strategies:
            return {}

        profile = self.strategies[strategy_name]
        total = profile.wins + profile.losses

        if total == 0:
            return {"winrate": 0, "total_pnl": 0}

        # Recent trades for sharpe
        recent_pnl = [t["pnl"] for t in self.trade_history if t["strategy"] == strategy_name][-30:]

        sharpe = 0.0
        if len(recent_pnl) > 1:
            mean = statistics.mean(recent_pnl)
            stdev = statistics.stdev(recent_pnl) if len(recent_pnl) > 1 else 1
            sharpe = mean / stdev if stdev > 0 else 0

        # Max drawdown
        cumulative = 0
        max_dd = 0
        peak = 0
        for pnl in recent_pnl:
            cumulative += pnl
            peak = max(peak, cumulative)
            dd = peak - cumulative
            max_dd = max(max_dd, dd)

        return {
            "winrate": profile.wins / total,
            "total_pnl": profile.total_pnl,
            "sharpe_ratio": sharpe,
            "max_drawdown": max_dd,
            "total_trades": total,
        }

    def evolve_strategy(self, strategy_name: str) -> Optional[StrategyProfile]:
        """
        Evolveer een strategie gebaseerd op performance.
        """
        if strategy_name not in self.strategies:
            logger.warning(f"Strategy not found: {strategy_name}")
            return None

        profile = self.strategies[strategy_name]
        metrics = self.calculate_metrics(strategy_name)

        # Format regime performance
        regime_str = ""
        for regime, data in profile.regime_performance.items():
            total = data.get("wins", 0) + data.get("losses", 0)
            winrate = data.get("wins", 0) / total if total > 0 else 0
            regime_str += f"- {regime}: {winrate:.1%} winrate, {data.get('pnl', 0):.2%} pnl\n"

        # Get symbol performance summary
        symbol_str = "Wordt berekend uit trade history..."

        # Build prompt
        prompt = self.STRATEGY_EVOLUTION_PROMPT.format(
            strategy_json=json.dumps(
                {
                    "name": profile.strategy_name,
                    "entry_threshold": profile.entry_threshold,
                    "exit_threshold": profile.exit_threshold,
                    "position_sizing": profile.position_sizing,
                    "max_positions": profile.max_positions,
                    "hold_time_preference": profile.hold_time_preference,
                },
                indent=2,
            ),
            winrate=metrics.get("winrate", 0),
            total_pnl=metrics.get("total_pnl", 0),
            sharpe_ratio=metrics.get("sharpe_ratio", 0),
            max_drawdown=metrics.get("max_drawdown", 0),
            regime_performance=regime_str,
            symbol_performance=symbol_str,
            new_version=profile.version + 1,
        )

        try:
            response = self.multi_llm.generate(prompt=prompt, temperature=0.3)

            result = json.loads(response.text)

            # Apply suggestions
            suggestions = result.get("suggestions", [])
            for sugg in suggestions:
                param = sugg.get("parameter")
                new_val = sugg.get("suggested_value")

                if hasattr(profile, param):
                    old_val = getattr(profile, param)
                    setattr(profile, param, new_val)
                    logger.info(f"Strategy {strategy_name}: {param} {old_val} -> {new_val}")

            # Update version
            profile.version += 1
            profile.sharpe_ratio = metrics.get("sharpe_ratio", 0)
            profile.max_drawdown = metrics.get("max_drawdown", 0)

            # Log evolution
            self.evolution_log.append(
                {
                    "timestamp": datetime.now(),
                    "strategy": strategy_name,
                    "version": profile.version,
                    "suggestions": suggestions,
                    "reasoning": result.get("evolution_reasoning", ""),
                }
            )

            logger.info(f"Strategy {strategy_name} evolved to v{profile.version}")
            return profile

        except Exception as e:
            logger.error(f"Strategy evolution failed: {e}")
            return None

    def get_evolution_report(self, strategy_name: str) -> Dict[str, Any]:
        """Genereer evolutie report."""
        if strategy_name not in self.strategies:
            return {}

        profile = self.strategies[strategy_name]
        metrics = self.calculate_metrics(strategy_name)

        # Filter evolution history
        history = [e for e in self.evolution_log if e["strategy"] == strategy_name]

        return {
            "strategy_name": strategy_name,
            "current_version": profile.version,
            "performance_metrics": metrics,
            "current_parameters": {
                "entry_threshold": profile.entry_threshold,
                "exit_threshold": profile.exit_threshold,
                "position_sizing": profile.position_sizing,
                "max_positions": profile.max_positions,
                "hold_time_preference": profile.hold_time_preference,
            },
            "regime_performance": profile.regime_performance,
            "evolution_history": history,
            "total_evolutions": len(history),
        }

    def should_evolve(self, strategy_name: str, min_trades: int = 20) -> bool:
        """Check of strategie evolutie nodig is."""
        metrics = self.calculate_metrics(strategy_name)

        if metrics.get("total_trades", 0) < min_trades:
            return False

        # Check if performance degrading
        recent_trades = [t for t in self.trade_history if t["strategy"] == strategy_name][-20:]

        if len(recent_trades) < 10:
            return False

        recent_pnl = sum(t["pnl"] for t in recent_trades)

        # Evolve if recent performance is poor
        return recent_pnl < 0


# Singleton
_evolution_engine = None


def get_strategy_evolution() -> StrategyEvolutionEngine:
    """Get singleton strategy evolution engine."""
    global _evolution_engine
    if _evolution_engine is None:
        _evolution_engine = StrategyEvolutionEngine()
    return _evolution_engine
