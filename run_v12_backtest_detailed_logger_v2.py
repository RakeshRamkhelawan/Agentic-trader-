"""
V12 Detailed Agent Logger V2 - Log EVERYTHING agents do
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
    decision_type: str  # 'individual' or 'meta_consensus'
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

    # Errors
    error: str


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
        for agent in self.meta.agents:
            print(f"  - {agent.agent_name} ({type(agent).__name__})")
        return True

    def _get_agent_state(self, agent) -> Dict[str, Any]:
        """Extract internal state from agent."""
        state = {
            "chitta_trades": 0,
            "chitta_winrate": 0.5,
            "prana": 100.0,
            "guna": [0.5, 0.3, 0.2]
        }

        if hasattr(agent, 'chitta'):
            try:
                chitta_stats = agent.chitta.reflect_recent(10)
                state["chitta_trades"] = chitta_stats.get('total_trades', 0)
                state["chitta_winrate"] = chitta_stats.get('recent_winrate', 0.5)
            except:
                pass

        if hasattr(agent, 'prana_level'):
            state["prana"] = agent.prana_level

        if hasattr(agent, 'guna_balance'):
            state["guna"] = agent.guna_balance

        return state

    def _create_log_entry(self, agent, market_state: dict, test_id: str,
                          action: str, confidence: float, harmony: float,
                          decision_type: str, was_forced: bool = False,
                          force_reason: str = "", error: str = "") -> AgentDecisionLog:
        """Create a log entry."""
        agent_state = self._get_agent_state(agent)

        return AgentDecisionLog(
            timestamp=datetime.now().isoformat(),
            test_id=test_id,
            symbol=market_state.get("symbol", "UNKNOWN"),
            agent_name=getattr(agent, 'agent_name', 'Unknown'),
            agent_type=type(agent).__name__,
            decision_type=decision_type,
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
            reasoning="",
            was_forced=was_forced,
            force_reason=force_reason,
            signal_strength=confidence * (1 if action == "BUY" else -1 if action == "SELL" else 0),
            error=error
        )

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

            print(f"\n[{i+1}/{len(symbols)}] {symbol}")
            print(f"  Market: {market_state['regime']} | Price: {market_state['price']} | RSI: {market_state['rsi']}")

            # Collect individual agent signals
            agent_signals = []
            for agent in self.meta.agents:
                try:
                    # Log the attempt
                    print(f"  {agent.agent_name}: ", end="")

                    # Use generate_signal instead of analyze/orient to get proper signal
                    if hasattr(agent, 'generate_signal'):
                        signal = await agent.generate_signal(market_state)
                    elif hasattr(agent, 'analyze'):
                        # Try calling analyze with no args or check signature
                        import inspect
                        sig = inspect.signature(agent.analyze)
                        if len(sig.parameters) == 0:
                            signal = await agent.analyze()
                        else:
                            signal = await agent.analyze(market_state)
                    else:
                        signal = {"action": "HOLD", "confidence": 0.5, "harmony": 0.0}

                    action = signal.get("action", "HOLD")
                    confidence = signal.get("confidence", 0.0)
                    harmony = signal.get("harmony", 0.0)

                    print(f"{action} (conf: {confidence:.2f}, harm: {harmony:.2f})")

                    # LOG INDIVIDUAL AGENT DECISION
                    log_entry = self._create_log_entry(
                        agent=agent,
                        market_state=market_state,
                        test_id=test_id,
                        action=action,
                        confidence=confidence,
                        harmony=harmony,
                        decision_type="individual",
                        was_forced=False,
                        force_reason="",
                        error=""
                    )
                    self.logger.log_decision(log_entry)

                    agent_signals.append({
                        "agent": agent.agent_name,
                        "action": action,
                        "confidence": confidence,
                        "harmony": harmony
                    })

                except Exception as e:
                    error_msg = str(e)
                    print(f"ERROR - {error_msg}")

                    # Log the error
                    log_entry = self._create_log_entry(
                        agent=agent,
                        market_state=market_state,
                        test_id=test_id,
                        action="HOLD",
                        confidence=0.0,
                        harmony=0.0,
                        decision_type="individual",
                        was_forced=False,
                        force_reason="",
                        error=error_msg
                    )
                    self.logger.log_decision(log_entry)

                    agent_signals.append({
                        "agent": agent.agent_name,
                        "action": "HOLD",
                        "confidence": 0.0,
                        "harmony": 0.0
                    })

            # Get meta decision
            try:
                decision = await self.meta.deliberate(market_state)
                meta_action = decision.action
                meta_confidence = decision.confidence
                meta_harmony = decision.harmony_score

                print(f"  --> META: {meta_action} (conf: {meta_confidence:.2f}, harm: {meta_harmony:.2f})")

                # LOG META DECISION
                meta_agent = type('MetaAgent', (), {
                    'agent_name': 'MetaOrchestrator',
                    'chitta': None,
                    'prana_level': 100,
                    'guna_balance': [0.5, 0.3, 0.2]
                })()

                log_entry = self._create_log_entry(
                    agent=meta_agent,
                    market_state=market_state,
                    test_id=test_id,
                    action=meta_action,
                    confidence=meta_confidence,
                    harmony=meta_harmony,
                    decision_type="meta_consensus",
                    was_forced=False,
                    force_reason="",
                    error=""
                )
                self.logger.log_decision(log_entry)

                # Track for bias correction
                self.action_history.append(meta_action)
                for agent in self.meta.agents:
                    agent_action_histories[agent.agent_name].append(meta_action)

                decisions.append({
                    "symbol": symbol,
                    "action": meta_action,
                    "confidence": meta_confidence,
                    "harmony": meta_harmony,
                    "individual_signals": agent_signals
                })

            except Exception as e:
                print(f"  --> META ERROR: {e}")
                decisions.append({
                    "symbol": symbol,
                    "action": "HOLD",
                    "confidence": 0.0,
                    "harmony": 0.0,
                    "error": str(e)
                })

            # Progress summary every 5
            if (i + 1) % 5 == 0:
                bias = calculate_bias(self.action_history)
                print(f"\n  [PROGRESS SUMMARY]")
                print(f"    Processed: {i+1}/{len(symbols)}")
                print(f"    Distribution: B:{bias['buy']:.0%} S:{bias['sell']:.0%} H:{bias['hold']:.0%}")
                print(f"    Bias detected: {'YES' if bias['bias_detected'] else 'NO'}")

        return decisions

    async def run_full_test(self):
        """Run complete test with all logging."""
        await self.setup()

        # Load symbols
        cache_dir = Path("backend/data/backtest_cache")
        all_symbols = [f.stem for f in cache_dir.glob("*.csv")]

        print(f"\n[INIT] Found {len(all_symbols)} symbols in cache")

        # Run test with 20 symbols
        symbols = all_symbols[:20]
        decisions = await self.run_logged_test(symbols, "detailed_20")

        # Calculate metrics
        import pandas as pd
        df = pd.DataFrame(decisions)

        print(f"\n{'='*80}")
        print("TEST RESULTS")
        print(f"{'='*80}")
        print(f"Total decisions: {len(decisions)}")
        print(f"Actions: BUY {(df['action'] == 'BUY').mean():.1%} | "
              f"SELL {(df['action'] == 'SELL').mean():.1%} | "
              f"HOLD {(df['action'] == 'HOLD').mean():.1%}")
        print(f"Avg confidence: {df['confidence'].mean():.2%}")
        print(f"Avg harmony: {df['harmony'].mean():.3f}")

        # Export to CSV
        print(f"\n{'='*80}")
        print("EXPORTING LOGS")
        print(f"{'='*80}")
        csv_path = self.logger.export_to_csv(f"detailed_agent_log_{self.logger.session_start.replace(':', '-')}")

        # Generate summary
        summary = self.logger.generate_summary()
        print(f"\n{'='*80}")
        print("AGENT DECISION SUMMARY")
        print(f"{'='*80}")
        print(f"Total logged decisions: {summary.get('total_decisions', 0)}")
        print(f"Overall distribution: B:{summary.get('buy_pct', 0):.1%} S:{summary.get('sell_pct', 0):.1%} H:{summary.get('hold_pct', 0):.1%}")
        print(f"Forced decisions: {summary.get('forced_pct', 0):.1%}")
        print(f"Average confidence: {summary.get('avg_confidence', 0):.2%}")
        print(f"Average harmony: {summary.get('avg_harmony', 0):.3f}")

        print(f"\nPer-agent breakdown:")
        for agent_name, stats in summary.get('by_agent', {}).items():
            print(f"  {agent_name}: {stats['count']} decisions | "
                  f"B:{stats.get('buy', 0)} S:{stats.get('sell', 0)} H:{stats.get('hold', 0)}")

        print(f"\n{'='*80}")
        print(f"CSV file saved to: {csv_path}")
        print(f"JSONL file saved to: {self.logger.log_dir}/agent_decisions_{self.logger.session_start[:10]}.jsonl")
        print(f"{'='*80}")

        return decisions, csv_path


async def main():
    engine = V12BacktestWithLogging()
    await engine.run_full_test()


if __name__ == "__main__":
    asyncio.run(main())
