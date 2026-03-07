"""
Unified Agent Interface V2 - With Self-Improving Prompts

Elke agent:
1. Krijgt eigen performance history mee in prompt
2. Genereert reflection na elke trade
3. Past confidence aan obv historie
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List

from backend.agents.llm_reflection_engine import LLMReflection, get_llm_reflection_engine
from backend.agents.self_improving_prompts import (
    AgentReflection,
    SelfImprovingPromptBuilder,
    generate_agent_reflection,
)

logger = logging.getLogger(__name__)


@dataclass
class EnhancedSignal:
    """Signal with reflection."""

    action: str
    confidence: float
    reasoning: str
    reflection: str  # Agent's self-reflection
    confidence_adjustment: float  # Applied multiplier
    bias_acknowledged: str


class SelfImprovingAgentWrapper:
    """Wrapper that adds self-improving capabilities with LLM."""

    def __init__(self, agent: Any, agent_name: str = None, use_llm: bool = True):
        self.wrapped_agent = agent
        self.agent_name = agent_name or getattr(agent, "agent_name", "UnknownAgent")
        self.agent_type = type(agent).__name__
        self.use_llm = use_llm

        # Performance history (laad uit Chitta indien beschikbaar)
        self.recent_trades: List[Dict] = []
        self.reflection_history: List[AgentReflection] = []
        self.current_reflection: AgentReflection = None
        self.current_llm_reflection: LLMReflection = None

        # LLM Reflection Engine
        if use_llm:
            self.llm_engine = get_llm_reflection_engine()
        else:
            self.llm_engine = None

        # Copy attributes
        if hasattr(agent, "chitta"):
            self.chitta = agent.chitta
        if hasattr(agent, "llm_provider"):
            self.llm_provider = agent.llm_provider

    async def analyze_with_reflection(
        self, market_state: Dict, performance_db: Dict = None
    ) -> EnhancedSignal:
        """
        Analyze with LLM-generated self-improving reflection.
        """
        symbol = market_state.get("symbol", "UNKNOWN")

        # 1. Get recent performance
        recent = self._get_recent_performance(performance_db)

        # 2. Generate LLM reflection (echte AI!)
        if self.use_llm and self.llm_engine:
            self.current_llm_reflection = self.llm_engine.generate_reflection(
                agent_name=self.agent_name,
                symbol=symbol,
                recent_trades=recent,
                market_state=market_state,
            )
            # Use LLM reflection
            reflection_text = self.current_llm_reflection.reflection_text
            confidence_mult = self.current_llm_reflection.new_confidence_multiplier
            bias = self.current_llm_reflection.identified_bias
            lesson = self.current_llm_reflection.lesson_for_next_trade
        else:
            # Fallback to rule-based
            self.current_reflection = generate_agent_reflection(self.agent_name, recent)
            reflection_text = self.current_reflection.lessons_learned
            confidence_mult = self.current_reflection.confidence_adjustment
            bias = self.current_reflection.bias_acknowledged or "None"
            lesson = reflection_text

        # 3. Build self-improving prompt met LLM reflection
        if "Sentiment" in self.agent_type:
            enhanced_prompt = SelfImprovingPromptBuilder.build_sentiment_prompt(
                agent_name=self.agent_name,
                symbol=symbol,
                performance_stats=self._calc_stats(recent),
                recent_trades=recent,
            )
        else:
            enhanced_prompt = SelfImprovingPromptBuilder.build_analyst_prompt(
                agent_name=self.agent_name,
                symbol=symbol,
                market_state=market_state,
                performance_stats=self._calc_stats(recent),
                regime_performance=self._get_regime_performance(performance_db),
            )

        # Add LLM insights to prompt
        enhanced_prompt += "\n\n[LLM COACH ADVIES]:\n"
        enhanced_prompt += f"Reflection: {reflection_text}\n"
        enhanced_prompt += f"Bias: {bias}\n"
        enhanced_prompt += f"Aanpassing: {lesson}\n"

        # 4. Generate signal
        base_signal = await self._generate_base_signal(market_state)

        # 5. Pas confidence aan obv LLM reflection
        adjusted_confidence = base_signal["confidence"] * confidence_mult
        adjusted_confidence = min(1.0, max(0.0, adjusted_confidence))

        # Build enhanced reasoning
        enhanced_reasoning = base_signal["reasoning"]
        if self.use_llm and self.current_llm_reflection:
            enhanced_reasoning += f" [LLM: {self.current_llm_reflection.suggested_adjustment}]"

        return EnhancedSignal(
            action=base_signal["action"],
            confidence=adjusted_confidence,
            reasoning=enhanced_reasoning,
            reflection=f"{reflection_text} | Lesson: {lesson}",
            confidence_adjustment=confidence_mult,
            bias_acknowledged=bias,
        )

    async def _generate_base_signal(self, market_state: Dict) -> Dict:
        """Generate base signal using wrapped agent."""
        try:
            if hasattr(self.wrapped_agent, "analyze"):
                result = await self.wrapped_agent.analyze(features=market_state, context={})
                return {
                    "action": result.get("action", "HOLD"),
                    "confidence": result.get("confidence", 0.5),
                    "reasoning": result.get("reasoning", ""),
                }
            else:
                # Fallback logic
                return self._fallback_signal(market_state)
        except Exception as e:
            logger.error(f"Signal generation error: {e}")
            return {"action": "HOLD", "confidence": 0.0, "reasoning": f"Error: {e}"}

    def _fallback_signal(self, market_state: Dict) -> Dict:
        """Fallback signal generation."""
        rsi = market_state.get("rsi", 50)

        if rsi < 30:
            return {"action": "BUY", "confidence": 0.6, "reasoning": f"RSI oversold: {rsi}"}
        elif rsi > 70:
            return {"action": "SELL", "confidence": 0.6, "reasoning": f"RSI overbought: {rsi}"}
        else:
            return {"action": "HOLD", "confidence": 0.5, "reasoning": f"RSI neutral: {rsi}"}

    def _get_recent_performance(self, performance_db: Dict = None) -> List[Dict]:
        """Get recent trades for this agent."""
        if performance_db and self.agent_name in performance_db:
            return performance_db[self.agent_name][-20:]  # Laatste 20
        return self.recent_trades[-20:]

    def _calc_stats(self, trades: List[Dict]) -> Dict:
        """Calculate performance stats."""
        if not trades:
            return {"winrate": 0.5, "avg_pnl": 0, "total": 0}

        wins = sum(1 for t in trades if t.get("pnl", 0) > 0)
        return {
            "winrate": wins / len(trades),
            "avg_pnl": sum(t.get("pnl", 0) for t in trades) / len(trades),
            "total": len(trades),
        }

    def _get_regime_performance(self, performance_db: Dict = None) -> Dict:
        """Get performance per regime."""
        # Simpele implementatie - in productie uit performance_db halen
        return {
            "bullish": {"winrate": 0.6, "trades": 10},
            "bearish": {"winrate": 0.4, "trades": 10},
            "range": {"winrate": 0.5, "trades": 10},
        }

    def record_trade_outcome(self, pnl: float, market_state: Dict):
        """Record outcome for learning."""
        self.recent_trades.append(
            {
                "timestamp": datetime.now().isoformat(),
                "symbol": market_state.get("symbol", "UNKNOWN"),
                "regime": market_state.get("regime", "unknown"),
                "pnl": pnl,
                "reflection": (
                    self.current_reflection.lessons_learned if self.current_reflection else ""
                ),
            }
        )


def wrap_agent_v2(
    agent: Any, agent_type: str = None, use_llm: bool = True
) -> SelfImprovingAgentWrapper:
    """Factory voor self-improving wrapper."""
    return SelfImprovingAgentWrapper(agent, use_llm=use_llm)
