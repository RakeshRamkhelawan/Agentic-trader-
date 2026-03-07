"""
V12 LLM Reflection Test - Echte AI-generated self-improvement

Deze test toont:
1. LLM-generated reflections per agent
2. Bias detectie door LLM
3. Confidence calibratie obv LLM advies
4. Strategie evolution over tijd
"""
import asyncio
import sys
from datetime import datetime, UTC, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from backend.agents.meta_orchestrator_v2 import MetaOrchestratorV2
from backend.agents.unified_agent_interface_v2 import wrap_agent_v2
from backend.agents.sentiment_agent_v2 import SentimentAgentV2
from backend.agents.analyst_agent import AnalystAgent


class V12LLMReflectionTest:
    """Test met LLM-generated reflections."""

    def __init__(self):
        self.orchestrator = MetaOrchestratorV2()

    async def setup(self):
        """Setup met LLM-enabled agents."""
        print("="*80)
        print("V12 LLM REFLECTION TEST")
        print("Agents gebruiken echte LLM voor self-improvement")
        print("="*80)

        # Wrap agents met LLM reflection
        sentiment = SentimentAgentV2()
        analyst = AnalystAgent()

        wrapped_sentiment = wrap_agent_v2(sentiment, use_llm=True)
        wrapped_analyst = wrap_agent_v2(analyst, use_llm=True)

        self.orchestrator.register_agent(wrapped_sentiment)
        self.orchestrator.register_agent(wrapped_analyst)

        print(f"\n[INIT] Registered 2 LLM-enabled agents")
        print(f"[INIT] Reflection engine: Ollama/llama3.2")
        print(f"[INIT] Agents genereren AI reflections na elke trade")

    async def run_test(self, symbols):
        """Run test met LLM reflections."""
        print(f"\n{'='*80}")
        print(f"TEST: {len(symbols)} symbols met LLM reflections")
        print(f"{'='*80}\n")

        for i, symbol in enumerate(symbols[:15]):  # Eerste 15 voor demo
            market_state = {
                "symbol": symbol,
                "price": 45000 + (i * 100),
                "regime": ["bullish", "bearish", "range"][i % 3],
                "rsi": 25 + (i % 50),
                "adx": 15 + (i % 30),
            }

            print(f"\n[{i+1:2d}/{len(symbols[:15])}] {symbol:12s} ({market_state['regime']})")
            print("-" * 60)

            # Get decision
            decision = await self.orchestrator.deliberate(market_state)

            # Simuleer outcome
            pnl = self._simulate_outcome(decision)

            # Update met outcome
            exit_time = datetime.now(UTC) + timedelta(minutes=30)
            self.orchestrator.update_trade_outcome(
                symbol=symbol,
                exit_price=market_state["price"] * (1 + pnl),
                exit_time=exit_time,
                pnl=pnl,
                exit_reason="tp" if pnl > 0 else "sl"
            )

            # Toon resultaat
            print(f"META DECISION: {decision.action:4s} | P&L: {pnl:+.4f} | H: {decision.harmony_score:.2f}")

            # Toon LLM reflections
            recent_signals = [s for s in self.orchestrator.signal_log if s.symbol == symbol]
            for sig in recent_signals[-2:]:  # Laatste 2 signals
                if sig.reflection:
                    print(f"\n  Agent: {sig.agent_name}")
                    print(f"  Action: {sig.action} (conf: {sig.confidence:.2f})")
                    print(f"  LLM Reflection: {sig.reflection[:80]}...")
                    if sig.bias_acknowledged and sig.bias_acknowledged != "None":
                        print(f"  Bias Detected: {sig.bias_acknowledged}")
                    print(f"  Confidence Adjustment: {sig.confidence_adjustment:.2f}x")

            if decision.divergence_detected:
                print(f"\n  [!] DIVERGENCE: {decision.strongest_conflict}")

        print(f"\n{'='*80}")
        print("TEST COMPLETE")
        print(f"{'='*80}")

    def _simulate_outcome(self, decision) -> float:
        """Simuleer trade outcome."""
        import random
        base = random.gauss(0, 0.02)
        conf_bonus = (decision.confidence - 0.5) * 0.03
        harmony_bonus = decision.harmony_score * 0.01
        return max(-0.05, min(0.05, base + conf_bonus + harmony_bonus))

    def print_llm_insights(self):
        """Print LLM-generated insights."""
        print(f"\n{'='*80}")
        print("LLM REFLECTION INSIGHTS")
        print(f"{'='*80}\n")

        for agent in self.orchestrator.agents:
            if hasattr(agent, 'current_llm_reflection') and agent.current_llm_reflection:
                llm_ref = agent.current_llm_reflection
                print(f"\n{agent.agent_name}:")
                print(f"  Reflection: {llm_ref.reflection_text[:100]}...")
                print(f"  Identified Bias: {llm_ref.identified_bias}")
                print(f"  Suggested Adjustment: {llm_ref.suggested_adjustment}")
                print(f"  New Confidence Mult: {llm_ref.new_confidence_multiplier:.2f}x")
                print(f"  Reasoning Quality: {llm_ref.reasoning_quality_score}/10")
                print(f"  Lesson: {llm_ref.lesson_for_next_trade}")

        # Performance stats
        print(f"\n{'='*80}")
        print("PERFORMANCE SUMMARY")
        print(f"{'='*80}")

        total_signals = len(self.orchestrator.signal_log)
        with_reflections = sum(1 for s in self.orchestrator.signal_log if s.reflection)
        with_bias = sum(1 for s in self.orchestrator.signal_log
                       if s.bias_acknowledged and s.bias_acknowledged != "None")

        print(f"Total signals: {total_signals}")
        print(f"With LLM reflections: {with_reflections}")
        print(f"With bias detection: {with_bias}")

        # Export
        report = self.orchestrator.export_performance_report()
        if not report.empty:
            print(f"\nTop Performers:")
            print(report.nlargest(5, 'total_pnl')[['agent_name', 'symbol', 'winrate', 'total_pnl']].to_string(index=False))

        print(f"\nResults saved to: backend/data/agent_logs/")


async def main():
    """Run LLM reflection test."""
    engine = V12LLMReflectionTest()
    await engine.setup()

    # Load symbols
    cache_dir = Path("backend/data/backtest_cache")
    symbols = [f.stem for f in cache_dir.glob("*.csv")]

    # Run
    await engine.run_test(symbols)

    # Show insights
    engine.print_llm_insights()

    print("\n[COMPLETE] LLM reflection test finished")
    print("Agents hebben nu echte AI-generated self-improvement!")


if __name__ == "__main__":
    asyncio.run(main())
