#!/usr/bin/env python3
"""
LLM Backtest Runner - Backtest met DeepSeek LLM Agents

Deze backtest gebruikt daadwerkelijk de AI agents met DeepSeek LLM:
- Research Agents (Bull/Bear) met deepseek-reasoner
- Risk Manager Agent met deepseek-reasoner  
- Fund Manager Agent met deepseek-reasoner
- Analyst Agent met deepseek-chat

Usage:
    python scripts/llm_backtest_runner.py --symbol BTC-EUR --days 30
    python scripts/llm_backtest_runner.py --symbol ETH-EUR --capital 50000 --days 60
"""

import argparse
import asyncio
import logging
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List

import numpy as np

# Add project root to path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from backend.backtesting.data_feed import MockDataFeed
from backend.backtesting.exchange import SimulatedExchange
from backend.backtesting.models import OrderSide
from backend.llm.factory import LLMFactory

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("LLMBacktest")


@dataclass
class LLMBacktestResult:
    """Complete LLM backtest results."""

    symbol: str
    start_date: datetime
    end_date: datetime
    total_candles: int
    processed_candles: int
    llm_calls_made: int
    llm_errors: int

    # Trading results
    initial_capital: float
    final_equity: float
    total_return_pct: float
    max_drawdown_pct: float
    sharpe_ratio: float

    # Agent decisions
    research_signals: int
    risk_blocks: int
    fund_manager_approvals: int
    trades_executed: int
    win_rate: float
    avg_trade_pnl: float

    # LLM Performance
    llm_latency_avg_ms: float
    llm_cost_estimate_usd: float

    # Agent insights
    agent_reasoning_logs: List[str] = field(default_factory=list)
    guna_distribution: Dict[str, float] = field(default_factory=dict)


class LLMBacktestRunner:
    """
    Backtest runner that uses actual LLM-powered agents.
    """

    def __init__(
        self,
        symbol: str,
        data_feed: MockDataFeed,
        initial_capital: float = 10000.0,
        use_llm: bool = True,
    ):
        self.symbol = symbol
        self.data_feed = data_feed
        self.initial_capital = initial_capital
        self.use_llm = use_llm

        # Exchange simulation
        self.exchange = SimulatedExchange(initial_capital)

        # State tracking
        self.equity = initial_capital
        self.equity_curve = []
        self.trades = []
        self.price_history = []

        # LLM tracking
        self.llm_calls = 0
        self.llm_errors = 0
        self.llm_latency_total = 0.0
        self.agent_logs = []

        # Agent signals
        self.signals_generated = 0
        self.risk_blocked = 0
        self.fund_approved = 0

        # Initialize LLM providers if enabled
        self._init_agents()

    def _init_agents(self):
        """Initialize LLM providers for agents."""
        if not self.use_llm:
            logger.info("Running WITHOUT LLM (rule-based mode)")
            self.research_llm = None
            self.risk_llm = None
            self.fund_llm = None
            return

        logger.info("Initializing DeepSeek LLM providers...")
        try:
            # Research Agents - use deepseek-reasoner for complex analysis
            self.research_llm = LLMFactory.create_for_agent("bull_researcher")
            logger.info("✓ Research LLM initialized (deepseek-reasoner)")

            # Risk Manager - use deepseek-reasoner for careful evaluation
            self.risk_llm = LLMFactory.create_for_agent("risk_manager")
            logger.info("✓ Risk LLM initialized (deepseek-reasoner)")

            # Fund Manager - use deepseek-reasoner for portfolio decisions
            self.fund_llm = LLMFactory.create_for_agent("fund_manager")
            logger.info("✓ Fund LLM initialized (deepseek-reasoner)")

        except Exception as e:
            logger.error(f"Failed to initialize LLM: {e}")
            logger.warning("Falling back to rule-based mode")
            self.use_llm = False

    async def _call_llm_research(self, bar: Dict, context: str) -> Dict[str, Any]:
        """
        Call Research Agent (Bull/Bear) via LLM.
        Returns: {'signal': 'BUY'/'SELL'/'HOLD', 'confidence': 0.0-1.0, 'reasoning': str}
        """
        if not self.use_llm or not self.research_llm:
            # Fallback: simple trend following
            return self._rule_based_signal(bar)

        start_time = time.time()
        self.llm_calls += 1

        try:
            price = bar.get("close", 0)
            volume = bar.get("volume", 0)

            # Build prompt for research agent
            prompt = f"""
Analyze this market data for {self.symbol}:
- Current Price: €{price:,.2f}
- Volume: {volume:,.0f}
- Price History (last 10): {self.price_history[-10:]}
- Context: {context}

Provide a trading signal with reasoning.
Respond in this format:
SIGNAL: [BUY/SELL/HOLD]
CONFIDENCE: [0.0-1.0]
REASONING: [Your analysis]
"""

            response = await self.research_llm.generate_text(prompt)
            latency = (time.time() - start_time) * 1000
            self.llm_latency_total += latency

            # Parse response
            signal = "HOLD"
            confidence = 0.0
            reasoning = ""

            for line in response.split("\n"):
                if line.startswith("SIGNAL:"):
                    signal = line.split(":")[1].strip().upper()
                elif line.startswith("CONFIDENCE:"):
                    try:
                        confidence = float(line.split(":")[1].strip())
                    except:
                        confidence = 0.5
                elif line.startswith("REASONING:"):
                    reasoning = line.split(":", 1)[1].strip()

            self.agent_logs.append(
                f"[{bar.get('timestamp')}] Research: {signal} ({confidence:.2f}) - {reasoning[:100]}..."
            )

            return {
                "signal": signal if signal in ["BUY", "SELL", "HOLD"] else "HOLD",
                "confidence": max(0.0, min(1.0, confidence)),
                "reasoning": reasoning,
            }

        except Exception as e:
            self.llm_errors += 1
            logger.error(f"LLM Research error: {e}")
            return self._rule_based_signal(bar)

    async def _call_llm_risk(
        self, signal: str, confidence: float, bar: Dict
    ) -> Dict[str, Any]:
        """
        Call Risk Manager Agent via LLM.
        Returns: {'allowed': bool, 'position_size': float, 'reason': str}
        """
        if not self.use_llm or not self.risk_llm:
            return self._rule_based_risk(signal, confidence, bar)

        start_time = time.time()
        self.llm_calls += 1

        try:
            price = bar.get("close", 0)
            current_drawdown = self._calculate_drawdown()

            prompt = f"""
Risk assessment for trade:
- Symbol: {self.symbol}
- Signal: {signal}
- Confidence: {confidence:.2f}
- Current Price: €{price:,.2f}
- Portfolio Drawdown: {current_drawdown*100:.2f}%
- Recent Volatility: {np.std(self.price_history[-20:]) if len(self.price_history) >= 20 else 0:.2f}

Evaluate risk and provide position sizing.
Respond in this format:
ALLOWED: [YES/NO]
POSITION_SIZE: [0.0-1.0] (percentage of portfolio)
REASON: [Risk assessment]
"""

            response = await self.risk_llm.generate_text(prompt)
            latency = (time.time() - start_time) * 1000
            self.llm_latency_total += latency

            allowed = False
            position_size = 0.0
            reason = ""

            for line in response.split("\n"):
                if line.startswith("ALLOWED:"):
                    allowed = "YES" in line.upper()
                elif line.startswith("POSITION_SIZE:"):
                    try:
                        position_size = float(line.split(":")[1].strip())
                    except:
                        position_size = 0.0
                elif line.startswith("REASON:"):
                    reason = line.split(":", 1)[1].strip()

            self.agent_logs.append(
                f"[{bar.get('timestamp')}] Risk: {'APPROVED' if allowed else 'BLOCKED'} - {reason[:80]}..."
            )

            return {
                "allowed": allowed,
                "position_size": max(0.0, min(1.0, position_size)),
                "reason": reason,
            }

        except Exception as e:
            self.llm_errors += 1
            logger.error(f"LLM Risk error: {e}")
            return self._rule_based_risk(signal, confidence, bar)

    async def _call_llm_fund_manager(
        self, signal: str, risk_result: Dict, bar: Dict
    ) -> bool:
        """
        Call Fund Manager Agent via LLM for final approval.
        Returns: bool (execute trade yes/no)
        """
        if not self.use_llm or not self.fund_llm:
            return risk_result.get("allowed", False)

        start_time = time.time()
        self.llm_calls += 1

        try:
            price = bar.get("close", 0)
            portfolio_value = self.exchange.get_equity({self.symbol: price})

            prompt = f"""
Final trade approval:
- Symbol: {self.symbol}
- Signal: {signal}
- Current Price: €{price:,.2f}
- Portfolio Value: €{portfolio_value:,.2f}
- Risk Assessment: {risk_result.get('reason', 'N/A')}
- Suggested Position: {risk_result.get('position_size', 0)*100:.1f}%

Make final decision.
Respond in this format:
DECISION: [EXECUTE/PASS]
REASON: [Brief justification]
"""

            response = await self.fund_llm.generate_text(prompt)
            latency = (time.time() - start_time) * 1000
            self.llm_latency_total += latency

            decision = False
            for line in response.split("\n"):
                if line.startswith("DECISION:"):
                    decision = "EXECUTE" in line.upper()

            self.agent_logs.append(
                f"[{bar.get('timestamp')}] Fund Manager: {'EXECUTE' if decision else 'PASS'}"
            )

            return decision

        except Exception as e:
            self.llm_errors += 1
            logger.error(f"LLM Fund Manager error: {e}")
            return risk_result.get("allowed", False)

    def _rule_based_signal(self, bar: Dict) -> Dict[str, Any]:
        """Fallback rule-based signal generation."""
        if len(self.price_history) < 20:
            return {
                "signal": "HOLD",
                "confidence": 0.0,
                "reasoning": "Insufficient data",
            }

        # Simple SMA crossover
        sma_short = np.mean(self.price_history[-10:])
        sma_long = np.mean(self.price_history[-20:])

        if sma_short > sma_long * 1.01:
            return {
                "signal": "BUY",
                "confidence": 0.6,
                "reasoning": "SMA crossover (rule-based)",
            }
        elif sma_short < sma_long * 0.99:
            return {
                "signal": "SELL",
                "confidence": 0.6,
                "reasoning": "SMA crossunder (rule-based)",
            }

        return {
            "signal": "HOLD",
            "confidence": 0.0,
            "reasoning": "No signal (rule-based)",
        }

    def _rule_based_risk(
        self, signal: str, confidence: float, bar: Dict
    ) -> Dict[str, Any]:
        """Fallback rule-based risk management."""
        drawdown = self._calculate_drawdown()

        # Max drawdown kill switch
        if drawdown > 0.15:
            return {
                "allowed": False,
                "position_size": 0.0,
                "reason": "Max drawdown exceeded",
            }

        # Confidence threshold
        if confidence < 0.50:
            return {"allowed": False, "position_size": 0.0, "reason": "Low confidence"}

        # Position sizing based on confidence
        if confidence >= 0.70:
            size = 0.25
        elif confidence >= 0.60:
            size = 0.15
        else:
            size = 0.05

        # Reduce size in drawdown
        if drawdown > 0.05:
            size *= 0.5

        return {"allowed": True, "position_size": size, "reason": "Rule-based approval"}

    def _calculate_drawdown(self) -> float:
        """Calculate current drawdown from peak."""
        if not self.equity_curve:
            return 0.0
        peak = max(p["equity"] for p in self.equity_curve)
        if peak == 0:
            return 0.0
        return (peak - self.equity) / peak

    async def run(self) -> LLMBacktestResult:
        """Run the complete LLM-powered backtest."""
        logger.info("=" * 70)
        logger.info("LLM-POWERED BACKTEST" if self.use_llm else "RULE-BASED BACKTEST")
        logger.info("=" * 70)
        logger.info(f"Symbol: {self.symbol}")
        logger.info(f"Initial Capital: €{self.initial_capital:,.2f}")
        logger.info(f"LLM Enabled: {self.use_llm}")
        logger.info("")

        candles_processed = 0
        total_candles = len(self.data_feed._timestamps)
        log_interval = max(1, total_candles // 10)

        while self.data_feed.next():
            bar = self.data_feed.get_latest_bar(self.symbol)
            if not bar:
                continue

            candles_processed += 1
            close = bar.get("close", 0)
            timestamp = bar.get("timestamp", datetime.now())

            # Track price history
            self.price_history.append(close)

            # Progress log
            if candles_processed % log_interval == 0:
                progress = (candles_processed / total_candles) * 100
                logger.info(
                    f"Progress: {progress:.1f}% | Equity: €{self.equity:,.2f} | LLM Calls: {self.llm_calls}"
                )

            # Skip if insufficient data
            if len(self.price_history) < 20:
                self.equity_curve.append(
                    {"timestamp": timestamp, "equity": self.equity}
                )
                continue

            # ============ PHASE 1: RESEARCH (LLM) ============
            research_result = await self._call_llm_research(
                bar, context="Regular analysis"
            )

            if research_result["signal"] == "HOLD":
                self.equity_curve.append(
                    {"timestamp": timestamp, "equity": self.equity}
                )
                continue

            self.signals_generated += 1

            # ============ PHASE 2: RISK (LLM) ============
            risk_result = await self._call_llm_risk(
                research_result["signal"], research_result["confidence"], bar
            )

            if not risk_result["allowed"]:
                self.risk_blocked += 1
                self.equity_curve.append(
                    {"timestamp": timestamp, "equity": self.equity}
                )
                continue

            # ============ PHASE 3: FUND MANAGER (LLM) ============
            execute = await self._call_llm_fund_manager(
                research_result["signal"], risk_result, bar
            )

            if not execute:
                self.equity_curve.append(
                    {"timestamp": timestamp, "equity": self.equity}
                )
                continue

            self.fund_approved += 1

            # ============ PHASE 4: EXECUTE TRADE ============
            position = self.exchange.positions.get(self.symbol)
            current_qty = position.quantity if position else 0.0

            if research_result["signal"] == "BUY" and current_qty == 0:
                position_size = risk_result["position_size"]
                qty = (self.equity * position_size) / close

                trade = self.exchange.execute_market_order(
                    symbol=self.symbol,
                    side=OrderSide.BUY,
                    quantity=qty,
                    current_price=close,
                    timestamp=timestamp,
                )
                if trade:
                    self.trades.append(trade)

            elif research_result["signal"] == "SELL" and current_qty > 0:
                trade = self.exchange.execute_market_order(
                    symbol=self.symbol,
                    side=OrderSide.SELL,
                    quantity=current_qty,
                    current_price=close,
                    timestamp=timestamp,
                )
                if trade:
                    self.trades.append(trade)
                    # Calculate P&L
                    pnl = trade.pnl or 0
                    self.equity += pnl

            # Update equity tracking
            current_prices = {self.symbol: close}
            self.equity = self.exchange.get_equity(current_prices)
            self.equity_curve.append({"timestamp": timestamp, "equity": self.equity})

        return self._calculate_results(candles_processed, total_candles)

    def _calculate_results(self, processed: int, total: int) -> LLMBacktestResult:
        """Calculate final backtest metrics."""

        # Basic returns
        total_return = (self.equity - self.initial_capital) / self.initial_capital

        # Calculate max drawdown
        max_dd = 0.0
        peak = self.initial_capital
        for point in self.equity_curve:
            eq = point["equity"]
            if eq > peak:
                peak = eq
            dd = (peak - eq) / peak if peak > 0 else 0
            if dd > max_dd:
                max_dd = dd

        # Calculate Sharpe
        if len(self.equity_curve) > 1:
            returns = []
            for i in range(1, len(self.equity_curve)):
                prev = self.equity_curve[i - 1]["equity"]
                curr = self.equity_curve[i]["equity"]
                if prev > 0:
                    returns.append((curr - prev) / prev)
            sharpe = (
                np.mean(returns) / (np.std(returns) + 1e-8) * np.sqrt(365)
                if returns
                else 0.0
            )
        else:
            sharpe = 0.0

        # Win rate
        if self.trades:
            wins = sum(1 for t in self.trades if (t.pnl or 0) > 0)
            win_rate = wins / len(self.trades)
            avg_pnl = (
                np.mean([t.pnl for t in self.trades if t.pnl is not None])
                if self.trades
                else 0.0
            )
        else:
            win_rate = 0.0
            avg_pnl = 0.0

        # LLM cost estimate (DeepSeek pricing)
        # deepseek-chat: ~$0.00014 per 1K tokens input, $0.00028 per 1K output
        # Assuming avg 500 tokens input, 200 tokens output per call
        cost_per_call = (500 / 1000 * 0.00014) + (200 / 1000 * 0.00028)
        estimated_cost = self.llm_calls * cost_per_call

        return LLMBacktestResult(
            symbol=self.symbol,
            start_date=self.data_feed._timestamps[0]
            if self.data_feed._timestamps
            else datetime.now(),
            end_date=self.data_feed._timestamps[-1]
            if self.data_feed._timestamps
            else datetime.now(),
            total_candles=total,
            processed_candles=processed,
            llm_calls_made=self.llm_calls,
            llm_errors=self.llm_errors,
            initial_capital=self.initial_capital,
            final_equity=self.equity,
            total_return_pct=total_return * 100,
            max_drawdown_pct=max_dd * 100,
            sharpe_ratio=sharpe,
            research_signals=self.signals_generated,
            risk_blocks=self.risk_blocked,
            fund_manager_approvals=self.fund_approved,
            trades_executed=len(self.trades),
            win_rate=win_rate * 100,
            avg_trade_pnl=avg_pnl,
            llm_latency_avg_ms=self.llm_latency_total / max(1, self.llm_calls),
            llm_cost_estimate_usd=estimated_cost,
            agent_reasoning_logs=self.agent_logs[-20:],  # Last 20 logs
            guna_distribution={
                "sattva": 0.4,
                "rajas": 0.35,
                "tamas": 0.25,
            },  # Placeholder
        )


def print_results(result: LLMBacktestResult, use_llm: bool):
    """Print formatted backtest results."""
    print("\n" + "=" * 70)
    print(f"BACKTEST RESULTS - {'LLM-POWERED' if use_llm else 'RULE-BASED'}")
    print("=" * 70)

    print("\n[MARKET DATA]")
    print(f"  Symbol:           {result.symbol}")
    print(f"  Period:           {result.start_date.date()} to {result.end_date.date()}")
    print(f"  Total Candles:    {result.total_candles:,}")

    print("\n[LLM PERFORMANCE]")
    print(f"  LLM Calls Made:   {result.llm_calls_made}")
    print(f"  LLM Errors:       {result.llm_errors}")
    print(f"  Avg Latency:      {result.llm_latency_avg_ms:.1f}ms")
    print(f"  Est. Cost:        ${result.llm_cost_estimate_usd:.4f}")

    print("\n[AGENT DECISIONS]")
    print(f"  Research Signals: {result.research_signals}")
    print(f"  Risk Blocks:      {result.risk_blocks}")
    print(f"  Fund Approvals:   {result.fund_manager_approvals}")
    print(f"  Trades Executed:  {result.trades_executed}")

    print("\n[PERFORMANCE]")
    print(f"  Initial Equity:   €{result.initial_capital:,.2f}")
    print(f"  Final Equity:     €{result.final_equity:,.2f}")
    print(f"  Total Return:     {result.total_return_pct:+.2f}%")
    print(f"  Max Drawdown:     {result.max_drawdown_pct:.2f}%")
    print(f"  Sharpe Ratio:     {result.sharpe_ratio:.2f}")

    print("\n[TRADING STATS]")
    print(f"  Win Rate:         {result.win_rate:.1f}%")
    print(f"  Avg Trade P&L:    €{result.avg_trade_pnl:,.2f}")

    if result.agent_reasoning_logs:
        print("\n[RECENT AGENT LOGS]")
        for log in result.agent_reasoning_logs[-5:]:
            print(f"  {log}")

    print("\n" + "=" * 70)


async def main():
    parser = argparse.ArgumentParser(description="LLM-Powered Backtest Runner")
    parser.add_argument("--symbol", default="BTC-EUR", help="Trading pair")
    parser.add_argument("--days", type=int, default=30, help="Number of days")
    parser.add_argument(
        "--capital", type=float, default=10000.0, help="Initial capital"
    )
    parser.add_argument(
        "--no-llm", action="store_true", help="Run without LLM (rule-based)"
    )

    args = parser.parse_args()

    # Setup data feed
    end_date = datetime.now()
    start_date = end_date - timedelta(days=args.days)

    data_feed = MockDataFeed()
    data_feed.load_data(symbols=[args.symbol], start_date=start_date, end_date=end_date)

    # Run backtest
    runner = LLMBacktestRunner(
        symbol=args.symbol,
        data_feed=data_feed,
        initial_capital=args.capital,
        use_llm=not args.no_llm,
    )

    result = await runner.run()
    print_results(result, use_llm=not args.no_llm)

    return result


if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(0 if result.total_return_pct > -50 else 1)
