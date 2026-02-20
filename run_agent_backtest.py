#!/usr/bin/env python3
"""
Agent Backtest Runner - Test hoe de AI agents presteren

Usage:
    python run_agent_backtest.py --symbol BTC-EUR --days 30
    python run_agent_backtest.py --symbol ETH-EUR --mode auto --capital 50000
"""

import argparse
import asyncio
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from backend.backtesting.models import BacktestConfig
from backend.backtesting.engine import BacktestEngine
from backend.backtesting.data_feed import MockDataFeed
from backend.backtesting.consciousness_strategy import ConsciousnessStrategy
from backend.backtesting.strategies.simple_ma import MovingAverageStrategy


async def run_backtest(
    symbol: str = "BTC-EUR",
    days: int = 30,
    capital: float = 10000.0,
    mode: str = "paper",
    strategy: str = "ConsciousnessStrategy"
):
    """Run een backtest met de agents."""
    
    print("=" * 70)
    print("AGENT BACKTEST - Agentic Trader Platform")
    print("=" * 70)
    print(f"\nConfiguratie:")
    print(f"  Symbol:        {symbol}")
    print(f"  Periode:       Laatste {days} dagen")
    print(f"  Initieel:      €{capital:,.2f}")
    print(f"  Mode:          {mode}")
    print(f"  Strategy:      {strategy}")
    print()
    
    # 1. Setup data feed (mock data voor demo)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    data_feed = MockDataFeed()
    data_feed.load_data(
        symbols=[symbol],
        start_date=start_date,
        end_date=end_date
    )
    
    # 2. Setup engine
    engine = BacktestEngine(
        data_feed=data_feed,
        initial_capital=capital
    )
    
    # 3. Setup strategy
    if strategy == "ConsciousnessStrategy":
        strat = ConsciousnessStrategy(engine.exchange)
    elif strategy == "MovingAverage":
        strat = MovingAverageStrategy(engine.exchange)
    else:
        print(f"Onbekende strategie: {strategy}")
        return
    
    # 4. Setup config
    config = BacktestConfig(
        symbols=[symbol],
        start_date=start_date,
        end_date=end_date,
        initial_capital=capital,
        strategy_name=strategy
    )
    
    # 5. Run backtest
    print("Backtest wordt uitgevoerd...")
    print("-" * 70)
    
    result = await engine.run(strat, config)
    
    # 6. Print results
    print("\n" + "=" * 70)
    print("BACKTEST RESULTATEN")
    print("=" * 70)
    
    print(f"\n[MARKT DATA]")
    print(f"  Symbol:           {result.config.symbols[0]}")
    print(f"  Periode:          {result.config.start_date.date()} tot {result.config.end_date.date()}")
    print(f"  Strategie:        {result.config.strategy_name}")
    
    print(f"\n[PERFORMANCE]")
    print(f"  Start kapitaal:   €{capital:,.2f}")
    final_equity = result.equity_curve[-1]['equity'] if result.equity_curve else capital
    print(f"  Eind kapitaal:    €{final_equity:,.2f}")
    print(f"  Totaal rendement: {result.metrics.total_return*100:+.2f}%")
    print(f"  CAGR:             {result.metrics.cagr*100:.2f}%")
    print(f"  Max drawdown:     {result.metrics.max_drawdown*100:.2f}%")
    print(f"  Sharpe ratio:     {result.metrics.sharpe_ratio:.2f}")
    print(f"  Sortino ratio:    {result.metrics.sortino_ratio:.2f}")
    
    print(f"\n[TRADING STATISTIEKEN]")
    print(f"  Aantal trades:    {result.metrics.total_trades}")
    print(f"  Win rate:         {result.metrics.win_rate*100:.1f}%")
    
    print(f"\n[PORTFOLIO OVER TIME]")
    print(f"  Data points:      {len(result.equity_curve)}")
    if result.equity_curve:
        print(f"  Start equity:     €{result.equity_curve[0]['equity']:,.2f}")
        print(f"  End equity:       €{result.equity_curve[-1]['equity']:,.2f}")
        max_equity = max(p['equity'] for p in result.equity_curve)
        min_equity = min(p['equity'] for p in result.equity_curve)
        print(f"  Max equity:       €{max_equity:,.2f}")
        print(f"  Min equity:       €{min_equity:,.2f}")
    
    print("\n" + "=" * 70)
    print(f"Backtest voltooid! Totaal rendement: {result.metrics.total_return*100:+.2f}%")
    print("=" * 70)
    
    return result


def main():
    parser = argparse.ArgumentParser(
        description="Run een backtest met de AI agents",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Voorbeelden:
  # Standaard backtest (30 dagen, BTC-EUR)
  python run_agent_backtest.py
  
  # Backtest met ETH, 90 dagen, auto mode
  python run_agent_backtest.py --symbol ETH-EUR --days 90 --mode auto
  
  # Groter kapitaal, andere strategie
  python run_agent_backtest.py --capital 50000 --strategy MovingAverage
        """
    )
    
    parser.add_argument(
        "--symbol",
        default="BTC-EUR",
        help="Trading pair (default: BTC-EUR)"
    )
    parser.add_argument(
        "--days",
        type=int,
        default=30,
        help="Aantal dagen historische data (default: 30)"
    )
    parser.add_argument(
        "--capital",
        type=float,
        default=10000.0,
        help="Initieel kapitaal (default: 10000)"
    )
    parser.add_argument(
        "--mode",
        default="paper",
        choices=["paper", "auto"],
        help="Trading mode (default: paper)"
    )
    parser.add_argument(
        "--strategy",
        default="ConsciousnessStrategy",
        choices=["ConsciousnessStrategy", "MovingAverage"],
        help="Trading strategie (default: ConsciousnessStrategy)"
    )
    
    args = parser.parse_args()
    
    try:
        result = asyncio.run(run_backtest(
            symbol=args.symbol,
            days=args.days,
            capital=args.capital,
            mode=args.mode,
            strategy=args.strategy
        ))
        
        # Exit code gebaseerd op resultaat
        sys.exit(0 if result.metrics.total_return > -0.20 else 1)
        
    except KeyboardInterrupt:
        print("\n\nBacktest onderbroken door gebruiker.")
        sys.exit(130)
    except Exception as e:
        print(f"\n\nFout tijdens backtest: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
