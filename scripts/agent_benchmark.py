#!/usr/bin/env python3
"""
Agent Benchmark - Vergelijk LLM vs Rule-Based Backtests

Deze benchmark draait beide backtests (met en zonder DeepSeek LLM)
en genereert een vergelijkingsrapport.

Usage:
    python scripts/agent_benchmark.py --symbol BTC-EUR --days 30
    python scripts/agent_benchmark.py --symbol ETH-EUR --days 90 --runs 3
"""

import argparse
import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List

import numpy as np

# Add project root to path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from backend.backtesting.data_feed import MockDataFeed
from scripts.llm_backtest_runner import LLMBacktestResult, LLMBacktestRunner


def run_backtest_sync(
    symbol: str, days: int, capital: float, use_llm: bool
) -> LLMBacktestResult:
    """Run a single backtest (synchronous wrapper)."""
    from datetime import datetime, timedelta

    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)

    data_feed = MockDataFeed()
    data_feed.load_data(symbols=[symbol], start_date=start_date, end_date=end_date)

    runner = LLMBacktestRunner(
        symbol=symbol, data_feed=data_feed, initial_capital=capital, use_llm=use_llm
    )

    return asyncio.run(runner.run())


class AgentBenchmark:
    """
    Benchmark comparing LLM-powered vs Rule-based trading agents.
    """

    def __init__(self, symbol: str, days: int, capital: float = 10000.0, runs: int = 1):
        self.symbol = symbol
        self.days = days
        self.capital = capital
        self.runs = runs
        self.results_llm: List[LLMBacktestResult] = []
        self.results_rule: List[LLMBacktestResult] = []

    def run(self) -> Dict:
        """Run benchmark comparing both approaches."""
        print("=" * 80)
        print("AGENT BENCHMARK - LLM vs Rule-Based Trading")
        print("=" * 80)
        print("\nConfiguration:")
        print(f"  Symbol:     {self.symbol}")
        print(f"  Period:     {self.days} days")
        print(f"  Capital:    €{self.capital:,.2f}")
        print(f"  Runs:       {self.runs} per approach")
        print()

        # Run LLM-powered backtests
        print("\n" + "-" * 80)
        print("PHASE 1: LLM-POWERED BACKTESTS (DeepSeek)")
        print("-" * 80)
        for i in range(self.runs):
            print(f"\nRun {i+1}/{self.runs}...")
            result = run_backtest_sync(
                self.symbol, self.days, self.capital, use_llm=True
            )
            self.results_llm.append(result)
            print(
                f"  Return: {result.total_return_pct:+.2f}% | Trades: {result.trades_executed} | LLM Calls: {result.llm_calls_made}"
            )

        # Run Rule-based backtests
        print("\n" + "-" * 80)
        print("PHASE 2: RULE-BASED BACKTESTS")
        print("-" * 80)
        for i in range(self.runs):
            print(f"\nRun {i+1}/{self.runs}...")
            result = run_backtest_sync(
                self.symbol, self.days, self.capital, use_llm=False
            )
            self.results_rule.append(result)
            print(
                f"  Return: {result.total_return_pct:+.2f}% | Trades: {result.trades_executed}"
            )

        return self._generate_report()

    def _avg(self, values: List[float]) -> float:
        return np.mean(values) if values else 0.0

    def _std(self, values: List[float]) -> float:
        return np.std(values) if values else 0.0

    def _generate_report(self) -> Dict:
        """Generate comprehensive comparison report."""

        # Aggregate metrics
        llm_returns = [r.total_return_pct for r in self.results_llm]
        rule_returns = [r.total_return_pct for r in self.results_rule]

        llm_sharpes = [r.sharpe_ratio for r in self.results_llm]
        rule_sharpes = [r.sharpe_ratio for r in self.results_rule]

        llm_drawdowns = [r.max_drawdown_pct for r in self.results_llm]
        rule_drawdowns = [r.max_drawdown_pct for r in self.results_rule]

        llm_trades = [r.trades_executed for r in self.results_llm]
        rule_trades = [r.trades_executed for r in self.results_rule]

        llm_winrates = [r.win_rate for r in self.results_llm]
        rule_winrates = [r.win_rate for r in self.results_rule]

        llm_costs = [r.llm_cost_estimate_usd for r in self.results_llm]
        llm_calls = [r.llm_calls_made for r in self.results_llm]
        llm_latencies = [r.llm_latency_avg_ms for r in self.results_llm]

        report = {
            "benchmark_date": datetime.now().isoformat(),
            "configuration": {
                "symbol": self.symbol,
                "days": self.days,
                "capital": self.capital,
                "runs": self.runs,
            },
            "llm_powered": {
                "avg_return_pct": self._avg(llm_returns),
                "std_return_pct": self._std(llm_returns),
                "avg_sharpe": self._avg(llm_sharpes),
                "avg_drawdown_pct": self._avg(llm_drawdowns),
                "avg_trades": self._avg(llm_trades),
                "avg_win_rate": self._avg(llm_winrates),
                "total_llm_calls": sum(llm_calls),
                "total_cost_usd": sum(llm_costs),
                "avg_latency_ms": self._avg(llm_latencies),
            },
            "rule_based": {
                "avg_return_pct": self._avg(rule_returns),
                "std_return_pct": self._std(rule_returns),
                "avg_sharpe": self._avg(rule_sharpes),
                "avg_drawdown_pct": self._avg(rule_drawdowns),
                "avg_trades": self._avg(rule_trades),
                "avg_win_rate": self._avg(rule_winrates),
            },
            "comparison": {
                "return_difference": self._avg(llm_returns) - self._avg(rule_returns),
                "sharpe_difference": self._avg(llm_sharpes) - self._avg(rule_sharpes),
                "drawdown_difference": self._avg(llm_drawdowns)
                - self._avg(rule_drawdowns),
                "win_rate_difference": self._avg(llm_winrates)
                - self._avg(rule_winrates),
                "cost_per_run_usd": self._avg(llm_costs),
            },
        }

        self._print_report(report)
        return report

    def _print_report(self, report: Dict):
        """Print formatted benchmark report."""

        print("\n" + "=" * 80)
        print("BENCHMARK RESULTS")
        print("=" * 80)

        print("\n[RETURNS]")
        llm_ret = report["llm_powered"]["avg_return_pct"]
        rule_ret = report["rule_based"]["avg_return_pct"]
        diff = report["comparison"]["return_difference"]

        print(
            f"  LLM-Powered:     {llm_ret:+.2f}% ± {report['llm_powered']['std_return_pct']:.2f}%"
        )
        print(
            f"  Rule-Based:      {rule_ret:+.2f}% ± {report['rule_based']['std_return_pct']:.2f}%"
        )
        print(
            f"  Difference:      {diff:+.2f}% ({'+' if diff > 0 else ''}{diff/rule_ret*100 if rule_ret != 0 else 0:.1f}%)"
        )

        print("\n[RISK METRICS]")
        llm_sharpe = report["llm_powered"]["avg_sharpe"]
        rule_sharpe = report["rule_based"]["avg_sharpe"]
        llm_dd = report["llm_powered"]["avg_drawdown_pct"]
        rule_dd = report["rule_based"]["avg_drawdown_pct"]

        print(
            f"  Sharpe Ratio:    LLM={llm_sharpe:.2f} vs Rule={rule_sharpe:.2f} (Δ{llm_sharpe-rule_sharpe:+.2f})"
        )
        print(
            f"  Max Drawdown:    LLM={llm_dd:.2f}% vs Rule={rule_dd:.2f}% (Δ{llm_dd-rule_dd:+.2f}%)"
        )

        print("\n[TRADING ACTIVITY]")
        llm_trades = report["llm_powered"]["avg_trades"]
        rule_trades = report["rule_based"]["avg_trades"]
        llm_wr = report["llm_powered"]["avg_win_rate"]
        rule_wr = report["rule_based"]["avg_win_rate"]

        print(f"  Avg Trades:      LLM={llm_trades:.1f} vs Rule={rule_trades:.1f}")
        print(f"  Win Rate:        LLM={llm_wr:.1f}% vs Rule={rule_wr:.1f}%")

        print("\n[LLM PERFORMANCE]")
        total_calls = report["llm_powered"]["total_llm_calls"]
        total_cost = report["llm_powered"]["total_cost_usd"]
        avg_latency = report["llm_powered"]["avg_latency_ms"]
        cost_per_run = report["comparison"]["cost_per_run_usd"]

        print(f"  Total LLM Calls: {total_calls:,}")
        print(f"  Total Cost:      ${total_cost:.4f} USD")
        print(f"  Cost per Run:    ${cost_per_run:.4f} USD")
        print(f"  Avg Latency:     {avg_latency:.1f}ms per call")

        print("\n[CONCLUSION]")
        winner = "LLM-POWERED" if llm_ret > rule_ret else "RULE-BASED"
        margin = abs(diff)

        if margin < 1.0:
            print("  Result: SIMILAR PERFORMANCE (difference < 1%)")
        else:
            print(f"  Winner: {winner} (+{margin:.2f}% return)")

        cost_benefit = diff / cost_per_run if cost_per_run > 0 else 0
        print(f"  Cost-Benefit:    €{cost_benefit:.2f} return per $1 spent on LLM")

        print("\n" + "=" * 80)

        # Save report to file
        report_path = Path(
            f"benchmark_report_{self.symbol.replace('/', '_')}_{self.days}d.json"
        )
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2, default=str)
        print(f"\nReport saved to: {report_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Benchmark LLM vs Rule-Based Trading Agents",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Standard benchmark (1 run each)
  python scripts/agent_benchmark.py --symbol BTC-EUR --days 30

  # Multiple runs for statistical significance
  python scripts/agent_benchmark.py --symbol ETH-EUR --days 60 --runs 5

  # Long-term benchmark
  python scripts/agent_benchmark.py --symbol BTC-EUR --days 365 --capital 50000
        """,
    )

    parser.add_argument(
        "--symbol", default="BTC-EUR", help="Trading pair (default: BTC-EUR)"
    )
    parser.add_argument(
        "--days", type=int, default=30, help="Number of days to backtest (default: 30)"
    )
    parser.add_argument(
        "--capital",
        type=float,
        default=10000.0,
        help="Initial capital (default: 10000)",
    )
    parser.add_argument(
        "--runs",
        type=int,
        default=1,
        help="Number of runs per approach for averaging (default: 1)",
    )

    args = parser.parse_args()

    if args.runs < 1:
        print("Error: --runs must be at least 1")
        sys.exit(1)

    print("\n" + "=" * 80)
    print("AGENT BENCHMARK")
    print("Comparing DeepSeek LLM vs Rule-Based Trading")
    print("=" * 80)
    print(f"\nThis will run {args.runs} backtest(s) for EACH approach")
    print(f"Total backtests: {args.runs * 2}")
    print(f"Estimated time: ~{args.runs * 2} minutes (depending on LLM latency)")

    confirm = input("\nContinue? [Y/n]: ").strip().lower()
    if confirm and confirm not in ("y", "yes"):
        print("Benchmark cancelled.")
        sys.exit(0)

    try:
        benchmark = AgentBenchmark(
            symbol=args.symbol, days=args.days, capital=args.capital, runs=args.runs
        )

        report = benchmark.run()

        print("\n✓ Benchmark completed successfully!")

        # Exit with success if LLM performed better or similar
        llm_ret = report["llm_powered"]["avg_return_pct"]
        rule_ret = report["rule_based"]["avg_return_pct"]
        sys.exit(0 if llm_ret >= rule_ret - 5 else 1)  # Allow 5% tolerance

    except KeyboardInterrupt:
        print("\n\nBenchmark interrupted by user.")
        sys.exit(130)
    except Exception as e:
        print(f"\n\nError during benchmark: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
