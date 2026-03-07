"""
V12 God-Tier MetaOrchestrator Test
Self-improving supervisor with full agent logging
"""
import asyncio
import json
import sys
import csv
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, asdict

sys.path.insert(0, str(Path(__file__).parent))

from backend.agents.meta_orchestrator_god_tier import GodTierMetaOrchestrator
from backend.agents.unified_agent_interface import wrap_agent
from backend.agents.sentiment_agent_v2 import SentimentAgentV2
from backend.agents.analyst_agent import AnalystAgent


@dataclass
class DecisionLog:
    """Complete decision log entry."""
    timestamp: str
    test_id: str
    symbol: str
    agent_name: str
    agent_type: str
    decision_type: str
    market_regime: str
    market_price: float
    market_rsi: float
    market_adx: float
    action: str
    confidence: float
    harmony: float
    was_forced: bool
    force_reason: str


class GodTierTestRunner:
    """Test runner for God-Tier MetaOrchestrator."""

    def __init__(self):
        self.orchestrator = GodTierMetaOrchestrator()
        self.logs: list = []
        self.session_start = datetime.now().isoformat()
        self.log_dir = Path("backend/data/agent_logs")
        self.log_dir.mkdir(parents=True, exist_ok=True)

    async def setup(self):
        """Setup with wrapped agents."""
        print("="*80)
        print("V12 GOD-TIER METAORCHESTRATOR TEST")
        print("Self-Improving Supreme Supervisor")
        print("="*80)

        # Create and wrap agents
        raw_sentiment = SentimentAgentV2()
        raw_analyst = AnalystAgent()

        wrapped_sentiment = wrap_agent(raw_sentiment)
        wrapped_analyst = wrap_agent(raw_analyst)

        # Register with orchestrator
        self.orchestrator.register_agent(wrapped_sentiment, weight=1.0)
        self.orchestrator.register_agent(wrapped_analyst, weight=1.2)

        print(f"\n[INIT] Session: {self.session_start}")
        print(f"[INIT] Agents registered:")
        print(f"  - {wrapped_sentiment.agent_name} (weight: 1.0)")
        print(f"  - {wrapped_analyst.agent_name} (weight: 1.2)")
        print(f"[INIT] Initial weights: {self.orchestrator.agent_weights}")

    async def run_test(self, symbols, test_name: str = "godtier"):
        """Run test with full logging."""
        print(f"\n{'='*80}")
        print(f"TEST: {test_name} | Symbols: {len(symbols)}")
        print(f"{'='*80}")

        for i, symbol in enumerate(symbols):
            market_state = {
                "symbol": symbol,
                "price": 45000 + (i * 100),
                "regime": ["bullish", "bearish", "range"][i % 3],
                "rsi": 30 + (i % 40),
                "adx": 15 + (i % 25),
                "volatility": 0.15 + (i % 10) / 100
            }

            print(f"\n[{i+1}/{len(symbols)}] {symbol}")
            print(f"  Market: {market_state['regime']} | RSI: {market_state['rsi']} | ADX: {market_state['adx']}")

            # Get orchestrator decision
            result = await self.orchestrator.deliberate_and_improve(market_state)

            print(f"  --> META: {result['action']} (conf: {result['confidence']:.2f}, harm: {result['harmony']:.2f})")

            if result.get('was_forced'):
                print(f"      [BIAS CORRECTION] {result['reasoning']}")

            # Log the decision
            self._log_decision(market_state, result, test_name)

            # Progress every 5
            if (i + 1) % 5 == 0:
                stats = self.orchestrator.get_stats()
                print(f"\n  [PROGRESS] {i+1}/{len(symbols)} decisions")
                print(f"    Distribution: {stats['action_distribution']}")
                print(f"    Bias status: {stats['bias_status']}")

        return self.orchestrator.get_stats()

    def _log_decision(self, market_state: dict, result: dict, test_id: str):
        """Log decision to CSV."""
        log_entry = DecisionLog(
            timestamp=datetime.now().isoformat(),
            test_id=test_id,
            symbol=market_state.get("symbol", "UNKNOWN"),
            agent_name="MetaOrchestrator",
            agent_type="GodTierMetaOrchestrator",
            decision_type="meta_consensus",
            market_regime=market_state.get("regime", "unknown"),
            market_price=market_state.get("price", 0.0),
            market_rsi=market_state.get("rsi", 0.0),
            market_adx=market_state.get("adx", 0.0),
            action=result.get("action", "HOLD"),
            confidence=result.get("confidence", 0.0),
            harmony=result.get("harmony", 0.0),
            was_forced=result.get("was_forced", False),
            force_reason=result.get("reasoning", "") if result.get("was_forced") else ""
        )
        self.logs.append(log_entry)

    def export_results(self):
        """Export logs to CSV."""
        if not self.logs:
            print("[EXPORT] No logs to export")
            return None

        csv_path = self.log_dir / f"godtier_results_{self.session_start.replace(':', '-')}.csv"

        fieldnames = asdict(self.logs[0]).keys()
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for log in self.logs:
                writer.writerow(asdict(log))

        print(f"\n[EXPORT] Saved {len(self.logs)} decisions to: {csv_path}")
        return csv_path

    def print_final_stats(self):
        """Print final statistics."""
        stats = self.orchestrator.get_stats()

        print(f"\n{'='*80}")
        print("FINAL STATISTICS")
        print(f"{'='*80}")
        print(f"Total decisions: {stats['total_decisions']}")
        print(f"Action distribution:")
        for action, count in stats['action_distribution'].items():
            pct = count / max(1, stats['total_decisions']) * 100
            print(f"  {action}: {count} ({pct:.1f}%)")

        print(f"\nCurrent weights:")
        for agent, weight in stats['current_weights'].items():
            print(f"  {agent}: {weight:.2f}")

        print(f"\nBias status:")
        for key, val in stats['bias_status'].items():
            if isinstance(val, float):
                print(f"  {key}: {val:.1%}")
            else:
                print(f"  {key}: {val}")

        print(f"\nStrategies generated: {stats['strategies_active']}")
        print(f"Lessons learned: {stats['lessons_learned']}")

        print(f"\n{'='*80}")


async def main():
    """Run God-Tier test."""
    runner = GodTierTestRunner()
    await runner.setup()

    # Load symbols
    cache_dir = Path("backend/data/backtest_cache")
    all_symbols = [f.stem for f in cache_dir.glob("*.csv")]

    print(f"[INIT] {len(all_symbols)} symbols available")

    # Run test with 20 symbols
    symbols = all_symbols[:20]
    stats = await runner.run_test(symbols, "godtier_v1")

    # Export and print
    runner.export_results()
    runner.print_final_stats()

    print("\n[COMPLETE] God-Tier test finished successfully")


if __name__ == "__main__":
    asyncio.run(main())
