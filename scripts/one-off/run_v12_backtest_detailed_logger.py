"""
V12 Detailed Agent Logger - Log EVERYTHING agents do
Exports to CSV for analysis
"""
import asyncio
import json
import sys
import csv
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import List, Dict, Any

sys.path.insert(0, str(Path(__file__).parent))

from backend.agents.meta_orchestrator import MetaOrchestrator
from backend.agents.sentiment_agent_v2 import SentimentAgentV2
from backend.agents.analyst_agent import AnalystAgent
from backend.core.conscious.global_chitta import get_global_chitta
from backend.config.emergency_fix import (
    apply_emergency_fix,
    calculate_bias,
    get_forced_action_if_needed,
    FIXED_WEIGHTS,
    EMERGENCY_THRESHOLDS
)


@dataclass
class AgentDecisionLog:
    """Complete log of a single agent decision."""
    timestamp: str
    test_id: str
    symbol: str
    agent_name: str
    agent_type: str
    market_regime: str
    market_price: float
    market_rsi: float
    market_adx: float
    market_volatility: float

    # Agent internal state
    chitta_trades_count: int
    chitta_winrate: float
    prana_level: float
    guna_sattva: float
    guna_rajas: float
    guna_tamas: float

    # Decision output
    action: str
    confidence: float
    harmony: float
    reasoning: str

    # Meta info
    was_forced: bool
    force_reason: str
    signal_strength: float

    # LLM info (if used)
    llm_used: bool
    llm_model: str
    prompt_tokens: int
    response_time_ms: float


class DetailedAgentLogger:
    """Logs every decision made by every agent."""

    def __init__(self):
        self.logs: List[AgentDecisionLog] = []
        self.session_start = datetime.now().isoformat()
        self.log_dir = Path("backend/data/agent_logs")
        self.log_dir.mkdir(parents=True, exist_ok=True)

    def log_decision(self, log_entry: AgentDecisionLog):
        """Log a single agent decision."""
        self.logs.append(log_entry)

        # Also write to real-time log file
        self._write_realtime_log(log_entry)

    def _write_realtime_log(self, entry: AgentDecisionLog):
        """Write to real-time JSONL log."""
        log_file = self.log_dir / f"agent_decisions_{self.session_start[:10]}.jsonl"
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(asdict(entry), default=str) + '\n')

    def export_to_csv(self, filename: str = None):
        """Export all logs to CSV."""
        if not filename:
            filename = f"agent_decisions_{self.session_start.replace(':', '-')}"

        csv_path = self.log_dir / f"{filename}.csv"

        if not self.logs:
            print(f"[LOGGER] No logs to export!")
            return None

        # Get field names from first log
        fieldnames = asdict(self.logs[0]).keys()

        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for log in self.logs:
                writer.writerow(asdict(log))

        print(f"[LOGGER] Exported {len(self.logs)} decisions to: {csv_path}")
        return csv_path

    def generate_summary(self):
        """Generate summary statistics."""
        if not self.logs:
            return {}

        total = len(self.logs)
        buy_count = sum(1 for l in self.logs if l.action == "BUY")
        sell_count = sum(1 for l in self.logs if l.action == "SELL")
        hold_count = sum(1 for l in self.logs if l.action == "HOLD")
        forced_count = sum(1 for l in self.logs if l.was_forced)

        by_agent = {}
        for log in self.logs:
            if log.agent_name not in by_agent:
                by_agent[log.agent_name] = {"count": 0, "buy": 0, "sell": 0, "hold": 0}
            by_agent[log.agent_name]["count"] += 1
            by_agent[log.agent_name][log.action.lower()] += 1

        return {
            "total_decisions": total,
            "buy_pct": buy_count / total,
            "sell_pct": sell_count / total,
            "hold_pct": hold_count / total,
            "forced_pct": forced_count / total,
            "avg_confidence": sum(l.confidence for l in self.logs) / total,
            "avg_harmony": sum(l.harmony for l in self.logs) / total,
            "by_agent": by_agent
        }


class V12BacktestWithLogging:
    """Backtest with full agent decision logging."""

    def __init__(self):
        self.meta = None
        self.global_chitta = get_global_chitta()
        self.logger = DetailedAgentLogger()
        self.action_history = []
        self.test_counter = 0

    async def setup(self):
        """Setup agents with emergency fix."""
        print("="*80)
        print("V12 BACKTEST WITH DETAILED AGENT LOGGING")
        print("="*80)
        print(f"\n[INIT] Session: {self.logger.session_start}")
        print(f"[INIT] Log directory: {self.logger.log_dir}")

        # Create agents
        sentiment = SentimentAgentV2()
        analyst = AnalystAgent()

        # Create MetaOrchestrator
        self.meta = MetaOrchestrator()
        self.meta.register_agent(sentiment)
        self.meta.register_agent(analyst)

        # Apply emergency fix
        apply_emergency_fix(self.meta)

        print(f"[INIT] Agents registered: {len(self.meta.agents)}")
        return True

    def _extract_agent_state(self, agent) -> Dict[str, Any]:
        """Extract internal state from agent."""
        state = {
            "chitta_trades": 0,
            "chitta_winrate": 0.5,
            "prana": 100.0,
            "guna": [0.5, 0.3, 0.2]
        }

        # Get Chitta stats if available
        if hasattr(agent, 'chitta'):
            try:
                chitta_stats = agent.chitta.reflect_recent(10)
                state["chitta_trades"] = chitta_stats.get('total_trades', 0)
                state["chitta_winrate"] = chitta_stats.get('recent_winrate', 0.5)
            except:
                pass

        # Get prana if available
        if hasattr(agent, 'prana_level'):
            state["prana"] = agent.prana_level

        # Get guna balance if available
        if hasattr(agent, 'guna_balance'):
            state["guna"] = agent.guna_balance

        return state

    def _log_agent_decision(self, agent, market_state: dict, test_id: str,
                            action: str, confidence: float, harmony: float,
                            was_forced: bool = False, force_reason: str = ""):
        """Log a single agent decision."""

        agent_state = self._extract_agent_state(agent)

        log_entry = AgentDecisionLog(
            timestamp=datetime.now().isoformat(),
            test_id=test_id,
            symbol=market_state.get("symbol", "UNKNOWN"),
            agent_name=agent.agent_name,
            agent_type=type(agent).__name__,
            market_regime=market_state.get("regime", "unknown"),
            market_price=market_state.get("price", 0.0),
            market_rsi=market_state.get("rsi", 0.0),
            market_adx=market_state.get("adx", 0.0),
            market_volatility=market_state.get("volatility", 0.0),
            chitta_trades_count=agent_state["chitta_trades"],
            chitta_winrate=agent_state["chitta_winrate"],
            prana_level=agent_state["prana"],
            guna_sattva=agent_state["guna"][0] if len(agent_state["guna"]) > 0 else 0.5,
            guna_rajas=agent_state["guna"][1] if len(agent_state["guna"]) > 1 else 0.3,
            guna_tamas=agent_state["guna"][2] if len(agent_state["guna"]) > 2 else 0.2,
            action=action,
            confidence=confidence,
            harmony=harmony,
            reasoning="",  # Could extract from agent
            was_forced=was_forced,
            force_reason=force_reason,
            signal_strength=confidence * (1 if action == "BUY" else -1 if action == "SELL" else 0),
            llm_used=hasattr(agent, 'llm_provider') and agent.llm_provider is not None,
            llm_model=getattr(agent, 'llm_provider', None).__class__.__name__ if hasattr(agent, 'llm_provider') else "none",
            prompt_tokens=0,  # Could track if needed
            response_time_ms=0.0  # Could track if needed
        )

        self.logger.log_decision(log_entry)

    async def run_logged_test(self, symbols, test_name: str = "test"):
        """Run backtest with full logging."""
        self.test_counter += 1
        test_id = f"{test_name}_{self.test_counter}"

        print(f"\n{'='*80}")
        print(f"TEST: {test_id} | Symbols: {len(symbols)}")
        print(f"{'='*80}")

        decisions = []
        agent_action_histories = {agent.agent_name: [] for agent in self.meta.agents}

        for i, symbol in enumerate(symbols):
            market_state = {
                "symbol": symbol,
                "price": 45000 + (i * 100),
                "regime": ["bullish", "bearish", "range"][i % 3],
                "rsi": 30 + (i % 40),
                "adx": 15 + (i % 25),
                "volatility": 0.15 + (i % 10) / 100
            }

            try:
                # Log each agent's individual signal BEFORE meta decision
                agent_signals = []
                for agent in self.meta.agents:
                    # Get agent's individual signal
                    try:
                        if hasattr(agent, 'orient'):
                            signal = await agent.orient(market_state)
                        elif hasattr(agent, 'analyze'):
                            signal = await agent.analyze(market_state)
                        else:
                            signal = {"action": "HOLD", "confidence": 0.5, "harmony": 0.0}

                        agent_signals.append({
                            "agent": agent.agent_name,
                            "signal": signal
                        })

                        # LOG THIS AGENT'S DECISION
                        self._log_agent_decision(
                            agent=agent,
                            market_state=market_state,
                            test_id=test_id,
                            action=signal.get("action", "HOLD"),
                            confidence=signal.get("confidence", 0.0),
                            harmony=signal.get("harmony", 0.0),
                            was_forced=False,
                            force_reason=""
                        )

                    except Exception as e:
                        print(f"    [ERROR] {agent.agent_name}: {e}")
                        agent_signals.append({
                            "agent": agent.agent_name,
                            "signal": {"action": "HOLD", "confidence": 0.0, "harmony": 0.0}
                        })

                # Check for bias and get meta decision
                should_force = False
                forced_action = None
                forced_confidence = 0.0

                for agent in self.meta.agents:
                    history = agent_action_histories[agent.agent_name]
                    should_force, forced_action, forced_confidence = get_forced_action_if_needed(
                        agent.agent_name, history
                    )
                    if should_force:
                        break

                # Get final decision
                if should_force:
                    decision = type('obj', (object,), {
                        'action': forced_action,
                        'confidence': forced_confidence,
                        'harmony_score': 0.2,
                        'supporting_agents': ['bias_correction'],
                        'opposing_agents': [],
                        'collective_reasoning': f'Forced {forced_action} to correct bias',
                        'should_pause': False
                    })()
                    force_reason = f"Bias correction triggered (history: {agent_action_histories})"
                else:
                    decision = await self.meta.deliberate(market_state)
                    force_reason = ""

                # Track actions
                self.action_history.append(decision.action)
                for agent in self.meta.agents:
                    agent_action_histories[agent.agent_name].append(decision.action)

                # Log meta decision (as separate entry)
                self._log_agent_decision(
                    agent=type('MetaOrchestrator', (), {'agent_name': 'MetaOrchestrator', 'chitta': None, 'prana_level': 100, 'guna_balance': [0.5, 0.3, 0.2]})(),
                    market_state=market_state,
                    test_id=test_id,
                    action=decision.action,
                    confidence=decision.confidence,
                    harmony=decision.harmony_score,
                    was_forced=should_force,
                    force_reason=force_reason
                )

                decisions.append({
                    "symbol": symbol,
                    "action": decision.action,
                    "confidence": decision.confidence,
                    "harmony": decision.harmony_score,
                    "forced": should_force
                })

                # Progress update
                if (i + 1) % 5 == 0:
                    bias = calculate_bias(self.action_history)
                    print(f"  Progress: {i+1}/{len(symbols)} | "
                          f"B:{bias['buy']:.0%} S:{bias['sell']:.0%} H:{bias['hold']:.0%} | "
                          f"Bias: {'YES' if bias['bias_detected'] else 'NO'}")
                    print(f"    Agents logged: {len(agent_signals)} signals")

            except Exception as e:
                print(f"  [ERROR] {symbol}: {e}")
                import traceback
                traceback.print_exc()

        # Calculate metrics
        import pandas as pd
        df = pd.DataFrame(decisions)

        metrics = {
            "total": len(decisions),
            "buy_pct": (df['action'] == 'BUY').mean() if len(df) > 0 else 0,
            "sell_pct": (df['action'] == 'SELL').mean() if len(df) > 0 else 0,
            "hold_pct": (df['action'] == 'HOLD').mean() if len(df) > 0 else 0,
            "forced_pct": df['forced'].mean() if 'forced' in df and len(df) > 0 else 0,
            "avg_confidence": df['confidence'].mean() if len(df) > 0 else 0,
            "avg_harmony": df['harmony'].mean() if len(df) > 0 else 0,
        }

        return metrics, decisions

    async def run_full_test(self):
        """Run complete test with all logging."""
        await self.setup()

        # Load symbols
        cache_dir = Path("backend/data/backtest_cache")
        all_symbols = [f.stem for f in cache_dir.glob("*.csv")]

        print(f"\n[INIT] Found {len(all_symbols)} symbols in cache")

        # Run test with 20 symbols
        symbols = all_symbols[:20]
        metrics, decisions = await self.run_logged_test(symbols, "detailed_20")

        # Print results
        print(f"\n{'='*80}")
        print("TEST RESULTS")
        print(f"{'='*80}")
        print(f"Total decisions: {metrics['total']}")
        print(f"Actions: BUY {metrics['buy_pct']:.1%} | SELL {metrics['sell_pct']:.1%} | HOLD {metrics['hold_pct']:.1%}")
        print(f"Forced: {metrics['forced_pct']:.1%}")
        print(f"Avg confidence: {metrics['avg_confidence']:.2%}")
        print(f"Avg harmony: {metrics['avg_harmony']:.3f}")

        # Export to CSV
        print(f"\n{'='*80}")
        print("EXPORTING LOGS")
        print(f"{'='*80}")
        csv_path = self.logger.export_to_csv(f"detailed_agent_log_{self.logger.session_start.replace(':', '-')}")

        # Generate and print summary
        summary = self.logger.generate_summary()
        print(f"\n{'='*80}")
        print("AGENT DECISION SUMMARY")
        print(f"{'='*80}")
        print(f"Total logged decisions: {summary.get('total_decisions', 0)}")
        print(f"Overall distribution: B:{summary.get('buy_pct', 0):.1%} S:{summary.get('sell_pct', 0):.1%} H:{summary.get('hold_pct', 0):.1%}")
        print(f"Average confidence: {summary.get('avg_confidence', 0):.2%}")
        print(f"Average harmony: {summary.get('avg_harmony', 0):.3f}")

        print(f"\nPer-agent breakdown:")
        for agent_name, stats in summary.get('by_agent', {}).items():
            print(f"  {agent_name}: {stats['count']} decisions | "
                  f"B:{stats.get('buy', 0)} S:{stats.get('sell', 0)} H:{stats.get('hold', 0)}")

        print(f"\n{'='*80}")
        print(f"CSV file saved to: {csv_path}")
        print(f"{'='*80}")

        return metrics, csv_path


async def main():
    engine = V12BacktestWithLogging()
    await engine.run_full_test()


if __name__ == "__main__":
    asyncio.run(main())
