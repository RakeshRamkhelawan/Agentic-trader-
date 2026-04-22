"""
V12 Enhanced Backtest - Met PnL Learning & Adaptive Weights

Features:
- Simuleert trades en tracks PnL
- Update agent weights gebaseerd op performance
- Detecteert conflicts tussen agents
- Exporteert uitgebreide analyse
"""
import asyncio
import sys
import random
from datetime import datetime, timedelta, UTC
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from backend.agents.meta_orchestrator_v2 import MetaOrchestratorV2, MetaDecisionV2
from backend.agents.unified_agent_interface import wrap_agent
from backend.agents.sentiment_agent_v2 import SentimentAgentV2
from backend.agents.analyst_agent import AnalystAgent


class V12EnhancedBacktest:
    """Enhanced backtest met PnL simulatie."""

    def __init__(self):
        self.orchestrator = MetaOrchestratorV2()
        self.results = []
        self.trade_outcomes = []

    async def setup(self):
        """Setup met agents."""
        print("="*80)
        print("V12 ENHANCED BACKTEST - PnL Learning & Adaptive Weights")
        print("="*80)

        # Register agents
        agents = [
            (SentimentAgentV2(), 1.0, "Sentiment"),
            (AnalystAgent(), 1.2, "Analyst"),
        ]

        for agent, weight, name in agents:
            wrapped = wrap_agent(agent)
            self.orchestrator.register_agent(wrapped)
            self.orchestrator.agent_weights[wrapped.agent_name] = weight

        print(f"\n[INIT] Registered {len(self.orchestrator.agents)} agents")
        print(f"[INIT] Initial weights: {self.orchestrator.agent_weights}")

    async def run_backtest(self, symbols):
        """Run backtest met simulated PnL."""
        print(f"\n{'='*80}")
        print(f"BACKTEST: {len(symbols)} symbols")
        print(f"{'='*80}\n")

        for i, symbol in enumerate(symbols):
            # Market state
            market_state = {
                "symbol": symbol,
                "price": 45000 + (i * 100),
                "regime": ["bullish", "bearish", "range"][i % 3],
                "rsi": 25 + (i % 50),
                "adx": 15 + (i % 30),
            }

            # Get decision
            decision = await self.orchestrator.deliberate(market_state)

            # Simulate trade outcome (randomized for demo)
            pnl = self._simulate_trade_outcome(decision, market_state)

            # Update orchestrator with outcome
            exit_time = datetime.now(UTC) + timedelta(minutes=30)
            self.orchestrator.update_trade_outcome(
                symbol=symbol,
                exit_price=market_state["price"] * (1 + pnl),
                exit_time=exit_time,
                pnl=pnl,
                exit_reason="tp" if pnl > 0 else "sl"
            )

            # Track results
            self.results.append({
                "symbol": symbol,
                "action": decision.action,
                "confidence": decision.confidence,
                "harmony": decision.harmony_score,
                "pnl": pnl,
                "divergence": decision.divergence_detected
            })

            # Print progress
            div_tag = " [DIV]" if decision.divergence_detected else ""
            print(f"[{i+1:3d}/{len(symbols)}] {symbol:12s} -> {decision.action:4s} | "
                  f"P&L: {pnl:+.4f} | H: {decision.harmony_score:.2f}{div_tag}")

            if decision.strongest_conflict:
                print(f"                    Conflict: {decision.strongest_conflict[0]} vs {decision.strongest_conflict[1]}")

        print(f"\n{'='*80}")
        print("BACKTEST COMPLETE")
        print(f"{'='*80}")

    def _simulate_trade_outcome(self, decision: MetaDecisionV2, market_state: dict) -> float:
        """Simuleer trade outcome gebaseerd op decision quality."""
        # Base random outcome
        base_pnl = random.gauss(0, 0.02)  # Mean 0, std 2%

        # Bonus voor hoge confidence
        confidence_bonus = (decision.confidence - 0.5) * 0.04

        # Bonus voor hoge harmony (agreement)
        harmony_bonus = decision.harmony_score * 0.01

        # Penalty voor divergence
        divergence_penalty = -0.01 if decision.divergence_detected else 0

        pnl = base_pnl + confidence_bonus + harmony_bonus + divergence_penalty

        # Clamp
        return max(-0.05, min(0.05, pnl))

    def print_report(self):
        """Print final report."""
        print(f"\n{'='*80}")
        print("FINAL REPORT - ENHANCED V12")
        print(f"{'='*80}")

        # Overall stats
        total_pnl = sum(r["pnl"] for r in self.results)
        wins = sum(1 for r in self.results if r["pnl"] > 0)
        winrate = wins / len(self.results) if self.results else 0

        print(f"\nOverall Performance:")
        print(f"  Total P&L: {total_pnl:.4f}")
        print(f"  Winrate: {winrate:.1%} ({wins}/{len(self.results)})")
        print(f"  Avg P&L per trade: {total_pnl/len(self.results):.4f}")

        # Per action
        print(f"\nPer Action:")
        for action in ["BUY", "SELL", "HOLD"]:
            action_results = [r for r in self.results if r["action"] == action]
            if action_results:
                avg_pnl = sum(r["pnl"] for r in action_results) / len(action_results)
                print(f"  {action}: {len(action_results)} trades, avg P&L: {avg_pnl:+.4f}")

        # Divergence analysis
        divergence_count = sum(1 for r in self.results if r["divergence"])
        print(f"\nDivergence Events: {divergence_count} ({divergence_count/len(self.results)*100:.1f}%)")

        # Updated weights
        print(f"\nUpdated Agent Weights:")
        for symbol, weights in list(self.orchestrator.symbol_weights.items())[:5]:
            print(f"  {symbol}: {dict(weights)}")

        # Export performance
        report = self.orchestrator.export_performance_report()
        if not report.empty:
            print(f"\nTop Agent-Symbol Combinations:")
            top = report.nlargest(5, 'total_pnl')[['agent_name', 'symbol', 'winrate', 'total_pnl']]
            print(top.to_string(index=False))

        print(f"\n{'='*80}")

    def save_results(self):
        """Save results to CSV."""
        import pandas as pd

        # Save decisions
        decisions_df = pd.DataFrame(self.results)
        decisions_df.to_csv("v12_enhanced_decisions.csv", index=False)

        # Save signals with outcomes
        signals_df = pd.DataFrame([
            {
                'timestamp': s.timestamp,
                'agent_name': s.agent_name,
                'symbol': s.symbol,
                'action': s.action,
                'confidence': s.confidence,
                'weight': s.weight,
                'rsi': s.rsi,
                'adx': s.adx,
                'regime': s.regime,
                'pnl': s.pnl,
                'was_correct': s.was_correct,
                'harmony': s.agent_harmony,
                'divergence': s.divergence_flag
            }
            for s in self.orchestrator.signal_log
        ])
        signals_df.to_csv("v12_enhanced_signals.csv", index=False)

        print(f"\n[SAVE] Results saved:")
        print(f"  - v12_enhanced_decisions.csv")
        print(f"  - v12_enhanced_signals.csv")


async def main():
    """Run enhanced backtest."""
    engine = V12EnhancedBacktest()
    await engine.setup()

    # Load symbols
    cache_dir = Path("backend/data/backtest_cache")
    symbols = [f.stem for f in cache_dir.glob("*.csv")]

    # Run (limited for demo)
    await engine.run_backtest(symbols[:30])

    # Report
    engine.print_report()
    engine.save_results()


if __name__ == "__main__":
    asyncio.run(main())
