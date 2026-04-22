"""
V12 Full Backtest - Ultimate MetaOrchestrator Test
Tests the enhanced MetaOrchestrator with:
- 9-step GuruAgents process
- Individual agent signal logging
- Bias detection & correction
- Self-improvement
"""
import asyncio
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from backend.agents.meta_orchestrator import MetaOrchestrator, MetaDecision
from backend.agents.unified_agent_interface import wrap_agent
from backend.agents.sentiment_agent_v2 import SentimentAgentV2
from backend.agents.analyst_agent import AnalystAgent


class V12FullBacktest:
    """Full backtest with enhanced MetaOrchestrator."""

    def __init__(self):
        self.orchestrator = None
        self.results = []

    async def setup(self):
        """Setup orchestrator with wrapped agents."""
        print("="*80)
        print("V12 FULL BACKTEST - Enhanced MetaOrchestrator")
        print("="*80)
        print(f"\n[INIT] Starting: {datetime.now().isoformat()}")

        # Create orchestrator
        self.orchestrator = MetaOrchestrator()

        # Create and wrap agents
        sentiment = SentimentAgentV2()
        analyst = AnalystAgent()

        wrapped_sentiment = wrap_agent(sentiment)
        wrapped_analyst = wrap_agent(analyst)

        # Register
        self.orchestrator.register_agent(wrapped_sentiment)
        self.orchestrator.register_agent(wrapped_analyst)

        print(f"[INIT] Registered {len(self.orchestrator.agents)} agents")
        print(f"[INIT] Bias threshold: {self.orchestrator.bias_threshold}")
        print(f"[INIT] Target distribution: {self.orchestrator.target_distribution}")

    async def run_backtest(self, symbols):
        """Run full backtest."""
        print(f"\n{'='*80}")
        print(f"BACKTEST: {len(symbols)} symbols")
        print(f"{'='*80}\n")

        for i, symbol in enumerate(symbols):
            # Varied market conditions
            market_state = {
                "symbol": symbol,
                "price": 45000 + (i * 100),
                "regime": ["bullish", "bearish", "range"][i % 3],
                "rsi": 25 + (i % 50),  # 25-75 range
                "adx": 15 + (i % 30),  # 15-45 range
                "volatility": 0.1 + (i % 20) / 100
            }

            print(f"[{i+1:3d}/{len(symbols)}] {symbol:12s} | "
                  f"{market_state['regime']:8s} | "
                  f"RSI:{market_state['rsi']:2d} | "
                  f"ADX:{market_state['adx']:2d} | ", end="")

            try:
                # Get orchestrator decision
                decision = await self.orchestrator.deliberate(market_state)

                # Print result
                forced_tag = " [FORCED]" if decision.was_forced else ""
                print(f"{decision.action:4s} | "
                      f"C:{decision.confidence:.2f} | "
                      f"H:{decision.harmony_score:.2f}{forced_tag}")

                if decision.was_forced:
                    print(f"                    -> {decision.force_reason}")

                self.results.append({
                    "symbol": symbol,
                    "action": decision.action,
                    "confidence": decision.confidence,
                    "harmony": decision.harmony_score,
                    "was_forced": decision.was_forced,
                    "regime": market_state["regime"]
                })

                # Progress stats every 10
                if (i + 1) % 10 == 0:
                    self._print_progress_stats(i + 1)

            except Exception as e:
                print(f"ERROR: {e}")
                import traceback
                traceback.print_exc()

        print(f"\n{'='*80}")
        print("BACKTEST COMPLETE")
        print(f"{'='*80}")

    def _print_progress_stats(self, processed):
        """Print progress statistics."""
        summary = self.orchestrator.get_session_summary()
        bias = summary.get("bias_status", {})
        dist = summary.get("action_distribution", {})

        print(f"\n    [STATS] Processed: {processed}")
        print(f"            Distribution: B:{dist.get('BUY', 0)} S:{dist.get('SELL', 0)} H:{dist.get('HOLD', 0)}")
        print(f"            Bias: B:{bias.get('buy', 0):.0%} S:{bias.get('sell', 0):.0%} H:{bias.get('hold', 0):.0%}")
        print(f"            Biased: {'YES' if bias.get('is_biased') else 'NO'}")
        print()

    def print_final_report(self):
        """Print final report."""
        summary = self.orchestrator.get_session_summary()

        print(f"\n{'='*80}")
        print("FINAL REPORT")
        print(f"{'='*80}")

        print(f"\nTotal Decisions: {len(self.results)}")

        dist = summary.get("action_distribution", {})
        total = sum(dist.values()) if dist else 1

        print(f"\nAction Distribution:")
        for action in ["BUY", "SELL", "HOLD"]:
            count = dist.get(action, 0)
            pct = count / total * 100 if total > 0 else 0
            bar = "█" * int(pct / 5)
            forced_count = sum(1 for r in self.results if r["action"] == action and r.get("was_forced"))
            print(f"  {action:5s}: {count:3d} ({pct:5.1f}%) {bar:20s} (forced: {forced_count})")

        print(f"\nBias Status:")
        bias = summary.get("bias_status", {})
        print(f"  BUY:  {bias.get('buy', 0):.1%}")
        print(f"  SELL: {bias.get('sell', 0):.1%}")
        print(f"  HOLD: {bias.get('hold', 0):.1%}")
        print(f"  Max Bias: {bias.get('max_bias', 0):.1%}")
        print(f"  Is Biased: {'YES' if bias.get('is_biased') else 'NO'}")

        # Forced decisions
        forced_total = sum(1 for r in self.results if r.get("was_forced"))
        print(f"\nBias Corrections: {forced_total} ({forced_total/len(self.results)*100:.1f}%)")

        # Average metrics
        if self.results:
            avg_conf = sum(r["confidence"] for r in self.results) / len(self.results)
            avg_harmony = sum(r["harmony"] for r in self.results) / len(self.results)
            print(f"\nAverage Confidence: {avg_conf:.2f}")
            print(f"Average Harmony: {avg_harmony:.2f}")

        print(f"\nAgent Weights:")
        for agent, weight in self.orchestrator.agent_weights.items():
            print(f"  {agent}: {weight:.2f}")

        # Signal log info
        print(f"\nIndividual Signals Logged: {len(self.orchestrator.signal_log)}")
        print(f"Log file: backend/data/agent_logs/individual_signals_*.csv")

        print(f"\n{'='*80}")

    def save_summary(self):
        """Save summary to file."""
        summary = self.orchestrator.get_session_summary()

        output = {
            "timestamp": datetime.now().isoformat(),
            "total_decisions": len(self.results),
            "action_distribution": summary.get("action_distribution", {}),
            "bias_status": summary.get("bias_status", {}),
            "agent_weights": self.orchestrator.agent_weights,
            "individual_signals_count": len(self.orchestrator.signal_log)
        }

        output_path = Path("backend/data/backtest_results/v12_enhanced_summary.json")
        output_path.parent.mkdir(parents=True, exist_ok=True)

        import json
        with open(output_path, 'w') as f:
            json.dump(output, f, indent=2)

        print(f"\n[SAVE] Summary saved to: {output_path}")


async def main():
    """Run full backtest."""
    engine = V12FullBacktest()
    await engine.setup()

    # Load all available symbols
    cache_dir = Path("backend/data/backtest_cache")
    all_symbols = [f.stem for f in cache_dir.glob("*.csv")]

    print(f"[INIT] Found {len(all_symbols)} symbols")

    # Run with all symbols
    await engine.run_backtest(all_symbols)

    # Report and save
    engine.print_final_report()
    engine.save_summary()

    print("\n[COMPLETE] Full backtest finished successfully")


if __name__ == "__main__":
    asyncio.run(main())
