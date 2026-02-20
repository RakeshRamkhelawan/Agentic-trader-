#!/usr/bin/env python3
"""
Quick Benchmark - Vergelijk 2 backtests snel
"""
import asyncio
import sys
from datetime import datetime, timedelta
from pathlib import Path

project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from backend.backtesting.data_feed import MockDataFeed
from backend.backtesting.engine import BacktestEngine
from backend.backtesting.models import BacktestConfig
from backend.backtesting.consciousness_strategy import ConsciousnessStrategy
from backend.backtesting.strategies.simple_ma import MovingAverageStrategy


async def run_single_backtest(name: str, symbol: str, days: int, capital: float, use_consciousness: bool = True):
    """Run een enkele backtest."""
    print(f"\n{'='*60}")
    print(f"Running: {name}")
    print('='*60)
    
    # Setup data
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    data_feed = MockDataFeed()
    data_feed.load_data(symbols=[symbol], start_date=start_date, end_date=end_date)
    
    # Setup engine
    engine = BacktestEngine(data_feed, initial_capital=capital)
    
    # Setup strategy
    if use_consciousness:
        strategy = ConsciousnessStrategy(engine.exchange)
    else:
        strategy = MovingAverageStrategy(engine.exchange)
    
    config = BacktestConfig(
        symbols=[symbol],
        start_date=start_date,
        end_date=end_date,
        initial_capital=capital,
        strategy_name="Consciousness" if use_consciousness else "MovingAverage"
    )
    
    # Run
    result = await engine.run(strategy, config)
    
    # Print summary
    final_equity = result.equity_curve[-1]['equity'] if result.equity_curve else capital
    total_return = (final_equity - capital) / capital * 100
    
    print(f"\nResults for {name}:")
    print(f"  Final Equity:   €{final_equity:,.2f}")
    print(f"  Total Return:   {total_return:+.2f}%")
    print(f"  Sharpe Ratio:   {result.metrics.sharpe_ratio:.2f}")
    print(f"  Max Drawdown:   {result.metrics.max_drawdown*100:.2f}%")
    print(f"  Total Trades:   {result.metrics.total_trades}")
    print(f"  Win Rate:       {result.metrics.win_rate*100:.1f}%")
    
    return {
        'name': name,
        'final_equity': final_equity,
        'total_return': total_return,
        'sharpe': result.metrics.sharpe_ratio,
        'drawdown': result.metrics.max_drawdown * 100,
        'trades': result.metrics.total_trades,
        'win_rate': result.metrics.win_rate * 100
    }


async def main():
    symbol = "BTC-EUR"
    days = 365  # Meer data voor betere signals
    capital = 10000.0
    
    print("="*60)
    print("QUICK BENCHMARK - Trading Strategies")
    print("="*60)
    print(f"\nSymbol:  {symbol}")
    print(f"Period:  {days} days")
    print(f"Capital: €{capital:,.2f}")
    
    # Run both backtests
    results = []
    
    # 1. Consciousness Strategy
    r1 = await run_single_backtest(
        "Consciousness Strategy (Triple-Layer)",
        symbol, days, capital, use_consciousness=True
    )
    results.append(r1)
    
    # 2. Simple Moving Average
    r2 = await run_single_backtest(
        "Simple Moving Average",
        symbol, days, capital, use_consciousness=False
    )
    results.append(r2)
    
    # Comparison
    print("\n" + "="*60)
    print("COMPARISON")
    print("="*60)
    
    print(f"\n{'Metric':<25} {'Consciousness':>15} {'Simple MA':>15} {'Difference':>15}")
    print("-"*60)
    
    print(f"{'Total Return':<25} {r1['total_return']:>14.2f}% {r2['total_return']:>14.2f}% {r1['total_return']-r2['total_return']:>+14.2f}%")
    print(f"{'Final Equity':<25} €{r1['final_equity']:>13,.2f} €{r2['final_equity']:>13,.2f} €{r1['final_equity']-r2['final_equity']:>+13,.2f}")
    print(f"{'Sharpe Ratio':<25} {r1['sharpe']:>15.2f} {r2['sharpe']:>15.2f} {r1['sharpe']-r2['sharpe']:>+15.2f}")
    print(f"{'Max Drawdown':<25} {r1['drawdown']:>14.2f}% {r2['drawdown']:>14.2f}% {r1['drawdown']-r2['drawdown']:>+14.2f}%")
    print(f"{'Total Trades':<25} {r1['trades']:>15.0f} {r2['trades']:>15.0f} {r1['trades']-r2['trades']:>+15.0f}")
    print(f"{'Win Rate':<25} {r1['win_rate']:>14.1f}% {r2['win_rate']:>14.1f}% {r1['win_rate']-r2['win_rate']:>+14.1f}%")
    
    winner = r1['name'] if r1['total_return'] > r2['total_return'] else r2['name']
    print(f"\n🏆 Winner: {winner}")
    print(f"   Return advantage: {abs(r1['total_return']-r2['total_return']):.2f}%")
    
    print("\n" + "="*60)
    

if __name__ == "__main__":
    asyncio.run(main())
