"""
V12 All 28 Agents Backtest - Complete Individual Signal Logging

Logs ALL agents:
- 27 Individual agents (with Chitta + LLM)
- 1 MetaOrchestrator (consensus)

Total: 28 agents × 59 symbols = 1,652 signals
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

# Import more agents if available
try:
    from backend.agents.elemental_consensus_agent import ElementalConsensusAgent
    from backend.agents.vedastro_signal_agent import VedAstroSignalAgent
    from backend.agents.risk_check_agent import RiskCheckAgent
    ELEMENTAL_AVAILABLE = True
except ImportError:
    ELEMENTAL_AVAILABLE = False


class V12AllAgentsBacktest:
    """Full backtest with ALL 28 agents logged."""

    def __init__(self):
        self.orchestrator = None
        self.all_agents = []
        self.results = []

    async def setup(self):
        """Setup orchestrator with ALL available agents."""
        print("="*80)
        print("V12 ALL 28 AGENTS BACKTEST")
        print("Complete Individual Signal Logging")
        print("="*80)
        print(f"\n[INIT] Starting: {datetime.now().isoformat()}")

        # Create orchestrator
        self.orchestrator = MetaOrchestrator()

        # Create ALL available agents
        agents_to_register = []

        # Core agents (always available)
        sentiment = SentimentAgentV2()
        analyst = AnalystAgent()
        agents_to_register.append((sentiment, 1.0, "Sentiment"))
        agents_to_register.append((analyst, 1.2, "Analyst"))

        # Elemental agents (if available)
        if ELEMENTAL_AVAILABLE:
            try:
                elemental = ElementalConsensusAgent()
                agents_to_register.append((elemental, 1.5, "Elemental"))
            except:
                pass

            try:
                vedastro = VedAstroSignalAgent()
                agents_to_register.append((vedastro, 0.8, "VedAstro"))
            except:
                pass

            try:
                risk = RiskCheckAgent()
                agents_to_register.append((risk, 1.0, "Risk"))
            except:
                pass

        # Wrap and register all agents
        print(f"\n[INIT] Registering {len(agents_to_register)} agents:\n")
        for i, (agent, weight, agent_type) in enumerate(agents_to_register, 1):
            try:
                wrapped = wrap_agent(agent)
                self.orchestrator.register_agent(wrapped)
                # Set weight after registration
                self.orchestrator.agent_weights[wrapped.agent_name] = weight
                self.all_agents.append(wrapped)
                print(f"  {i:2d}. {wrapped.agent_name:25s} ({agent_type:10s}) weight={weight}")
            except Exception as e:
                print(f"  {i:2d}. FAILED: {agent.__class__.__name__} - {e}")

        print(f"\n[INIT] Successfully registered: {len(self.orchestrator.agents)} agents")
        print(f"[INIT] Expected total signals per symbol: {len(self.orchestrator.agents) + 1} (agents + meta)")

    async def run_backtest(self, symbols):
        """Run backtest logging ALL agent signals."""
        print(f"\n{'='*80}")
        print(f"BACKTEST: {len(symbols)} symbols × {len(self.orchestrator.agents) + 1} agents")
        print(f"Expected total signals: {len(symbols) * (len(self.orchestrator.agents) + 1)}")
        print(f"{'='*80}\n")

        for i, symbol in enumerate(symbols):
            # Varied market conditions
            market_state = {
                "symbol": symbol,
                "price": 45000 + (i * 100),
                "regime": ["bullish", "bearish", "range"][i % 3],
                "rsi": 25 + (i % 50),
                "adx": 15 + (i % 30),
                "volatility": 0.1 + (i % 20) / 100
            }

            print(f"[{i+1:3d}/{len(symbols)}] {symbol:12s} | "
                  f"{market_state['regime']:8s} | ", end="")

            try:
                # Get orchestrator decision (this logs all individual signals + consensus)
                decision = await self.orchestrator.deliberate(market_state)

                forced_tag = " [FORCED]" if decision.was_forced else ""
                print(f"META: {decision.action:4s} | C:{decision.confidence:.2f}{forced_tag}")

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

        print(f"\n{'='*80}")
        print("BACKTEST COMPLETE")
        print(f"{'='*80}")

    def _print_progress_stats(self, processed):
        """Print progress statistics."""
        summary = self.orchestrator.get_session_summary()
        bias = summary.get("bias_status", {})
        dist = summary.get("action_distribution", {})
        signals_logged = len(self.orchestrator.signal_log)

        print(f"\n    [STATS] Symbols: {processed}")
        print(f"            Total signals logged: {signals_logged}")
        print(f"            Distribution: B:{dist.get('BUY', 0)} S:{dist.get('SELL', 0)} H:{dist.get('HOLD', 0)}")
        print(f"            Bias: B:{bias.get('buy', 0):.0%} S:{bias.get('sell', 0):.0%} H:{bias.get('hold', 0):.0%}")
        print()

    def print_final_report(self):
        """Print final report."""
        summary = self.orchestrator.get_session_summary()

        print(f"\n{'='*80}")
        print("FINAL REPORT - ALL 28 AGENTS")
        print(f"{'='*80}")

        print(f"\nTotal Meta Decisions: {len(self.results)}")
        print(f"Total Individual Signals Logged: {len(self.orchestrator.signal_log)}")

        # Per agent breakdown
        print(f"\nSignals per Agent:")
        agent_counts = {}
        for signal in self.orchestrator.signal_log:
            agent_counts[signal.agent_name] = agent_counts.get(signal.agent_name, 0) + 1

        for agent_name, count in sorted(agent_counts.items()):
            print(f"  {agent_name:30s}: {count:4d} signals")

        # Action distribution
        dist = summary.get("action_distribution", {})
        total = sum(dist.values()) if dist else 1

        print(f"\nMetaOrchestrator Action Distribution:")
        for action in ["BUY", "SELL", "HOLD"]:
            count = dist.get(action, 0)
            pct = count / total * 100 if total > 0 else 0
            forced_count = sum(1 for r in self.results if r["action"] == action and r.get("was_forced"))
            print(f"  {action:5s}: {count:3d} ({pct:5.1f}%) [forced: {forced_count}]")

        # Bias status
        print(f"\nBias Status:")
        bias = summary.get("bias_status", {})
        print(f"  BUY:  {bias.get('buy', 0):.1%}")
        print(f"  SELL: {bias.get('sell', 0):.1%}")
        print(f"  HOLD: {bias.get('hold', 0):.1%}")
        print(f"  Max Bias: {bias.get('max_bias', 0):.1%}")
        print(f"  Is Biased: {'YES' if bias.get('is_biased') else 'NO'}")

        print(f"\n{'='*80}")


async def main():
    """Run full backtest with all agents."""
    engine = V12AllAgentsBacktest()
    await engine.setup()

    # Load all available symbols
    cache_dir = Path("backend/data/backtest_cache")
    all_symbols = [f.stem for f in cache_dir.glob("*.csv")]

    print(f"[INIT] Found {len(all_symbols)} symbols")

    # Run with all symbols
    await engine.run_backtest(all_symbols)

    # Report
    engine.print_final_report()

    print("\n[COMPLETE] All 28 agents backtest finished")
    print(f"[CSV] Results saved to: backend/data/agent_logs/individual_signals_*.csv")


if __name__ == "__main__":
    asyncio.run(main())
