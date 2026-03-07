"""
V12 Self-Improving Agents Test

Test met agents die:
1. Hun eigen performance reflecteren
2. Confidence aanpassen obv historie
3. Biases detecteren en erkennen
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


class V12SelfImprovingTest:
    """Test self-improving agents."""

    def __init__(self):
        self.orchestrator = MetaOrchestratorV2()

    async def setup(self):
        """Setup met self-improving agents."""
        print("="*80)
        print("V12 SELF-IMPROVING AGENTS TEST")
        print("Agents reflecteren op eigen performance en leren bij")
        print("="*80)

        # Wrap agents met self-improving capabilities
        sentiment = SentimentAgentV2()
        analyst = AnalystAgent()

        wrapped_sentiment = wrap_agent_v2(sentiment)
        wrapped_analyst = wrap_agent_v2(analyst)

        self.orchestrator.register_agent(wrapped_sentiment)
        self.orchestrator.register_agent(wrapped_analyst)

        print(f"\n[INIT] Registered {len(self.orchestrator.agents)} self-improving agents")
        print(f"[INIT] Agents genereren na elke trade een reflection")

    async def run_test(self, symbols):
        """Run test met learning."""
        print(f"\n{'='*80}")
        print(f"TEST: {len(symbols)} symbols met self-improvement")
        print(f"{'='*80}\n")

        for i, symbol in enumerate(symbols[:20]):  # Eerste 20 voor demo
            market_state = {
                "symbol": symbol,
                "price": 45000 + (i * 100),
                "regime": ["bullish", "bearish", "range"][i % 3],
                "rsi": 25 + (i % 50),
                "adx": 15 + (i % 30),
            }

            print(f"\n[{i+1:2d}/{len(symbols[:20])}] {symbol:12s} ({market_state['regime']})")

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
            print(f"  META: {decision.action:4s} | P&L: {pnl:+.4f} | H: {decision.harmony_score:.2f}")

            # Toon agent reflections (van laatste signal)
            recent_signals = [s for s in self.orchestrator.signal_log if s.symbol == symbol]
            for sig in recent_signals:
                if sig.reflection:
                    print(f"  +-- {sig.agent_name:20s}: conf_adj={sig.confidence_adjustment:.2f}")
                    print(f"  |   Reflection: {sig.reflection[:60]}...")
                    if sig.bias_acknowledged:
                        print(f"  |   Bias: {sig.bias_acknowledged}")

            if decision.divergence_detected and decision.strongest_conflict:
                print(f"  [!] Conflict: {decision.strongest_conflict[0]} vs {decision.strongest_conflict[1]}")

        print(f"\n{'='*80}")
        print("TEST COMPLETE")
        print(f"{'='*80}")

    def _simulate_outcome(self, decision) -> float:
        """Simuleer trade outcome."""
        import random
        base = random.gauss(0, 0.02)
        conf_bonus = (decision.confidence - 0.5) * 0.03
        return max(-0.05, min(0.05, base + conf_bonus))

    def print_reflections(self):
        """Print alle generated reflections."""
        print(f"\n{'='*80}")
        print("AGENT REFLECTIONS SUMMARY")
        print(f"{'='*80}\n")

        for agent in self.orchestrator.agents:
            if hasattr(agent, 'reflection_history') and agent.reflection_history:
                print(f"\n{agent.agent_name}:")
                print(f"  Total reflections: {len(agent.reflection_history)}")

                if agent.reflection_history:
                    latest = agent.reflection_history[-1]
                    print(f"  Latest winrate: {latest.recent_winrate:.1%}")
                    print(f"  Latest lesson: {latest.lessons_learned}")
                    print(f"  Confidence adj: {latest.confidence_adjustment:.2f}")
                    if latest.bias_acknowledged:
                        print(f"  Bias detected: {latest.bias_acknowledged}")

        # Signal log stats
        print(f"\n{'='*80}")
        print("SIGNAL LOG STATS")
        print(f"{'='*80}")

        reflections_count = sum(1 for s in self.orchestrator.signal_log if s.reflection)
        biases_count = sum(1 for s in self.orchestrator.signal_log if s.bias_acknowledged)

        print(f"Total signals: {len(self.orchestrator.signal_log)}")
        print(f"With reflections: {reflections_count}")
        print(f"With bias acknowledged: {biases_count}")

        # Export
        self.orchestrator.export_performance_report()
        print(f"\nResults saved to: backend/data/agent_logs/signals_v2_*.csv")


async def main():
    """Run self-improving test."""
    engine = V12SelfImprovingTest()
    await engine.setup()

    # Load symbols
    cache_dir = Path("backend/data/backtest_cache")
    symbols = [f.stem for f in cache_dir.glob("*.csv")]

    # Run
    await engine.run_test(symbols)

    # Show reflections
    engine.print_reflections()

    print("\n[COMPLETE] Self-improving test finished")


if __name__ == "__main__":
    asyncio.run(main())
