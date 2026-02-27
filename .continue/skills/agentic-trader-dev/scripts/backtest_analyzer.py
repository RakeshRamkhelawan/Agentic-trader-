#!/usr/bin/env python3
"""
Backtest Result Analyzer - Analyze and compare backtest results.

Usage:
    python backtest_analyzer.py --latest
    python backtest_analyzer.py --compare 3
    python backtest_analyzer.py --file elemental_backtest_*.json
"""

import argparse
import json
import glob
import sys
from pathlib import Path
from datetime import datetime
from collections import defaultdict


def find_latest_backtest(pattern="elemental_backtest_*.json"):
    """Find the most recent backtest result file."""
    files = glob.glob(pattern)
    if not files:
        return None
    return max(files, key=lambda f: Path(f).stat().st_mtime)


def find_backtest_runs(pattern="elemental_backtest_*.json", count=5):
    """Find the N most recent backtest runs."""
    files = glob.glob(pattern)
    files.sort(key=lambda f: Path(f).stat().st_mtime, reverse=True)
    return files[:count]


def load_backtest_result(filepath):
    """Load and parse a backtest result file."""
    with open(filepath, 'r') as f:
        return json.load(f)


def analyze_backtest(data):
    """Extract key metrics from backtest data."""
    metrics = {
        'total_return': data.get('total_return', 0),
        'sharpe_ratio': data.get('sharpe_ratio', 0),
        'max_drawdown': data.get('max_drawdown', 0),
        'win_rate': data.get('win_rate', 0),
        'total_trades': data.get('total_trades', 0),
        'profitable_trades': data.get('profitable_trades', 0),
        'start_date': data.get('start_date', 'N/A'),
        'end_date': data.get('end_date', 'N/A'),
    }
    
    # Calculate additional metrics
    if metrics['total_trades'] > 0:
        metrics['win_rate_pct'] = (metrics['profitable_trades'] / metrics['total_trades']) * 100
    else:
        metrics['win_rate_pct'] = 0
    
    return metrics


def print_summary(filepath, metrics):
    """Print a formatted summary of backtest results."""
    filename = Path(filepath).name
    print(f"\n{'='*70}")
    print(f"Backtest: {filename}")
    print(f"{'='*70}")
    print(f"Period:        {metrics['start_date']} to {metrics['end_date']}")
    print(f"Total Return:  {metrics['total_return']:.2f}%")
    print(f"Sharpe Ratio:  {metrics['sharpe_ratio']:.2f}")
    print(f"Max Drawdown:  {metrics['max_drawdown']:.2f}%")
    print(f"Win Rate:      {metrics['win_rate_pct']:.1f}% ({metrics['profitable_trades']}/{metrics['total_trades']})")
    print(f"{'='*70}")


def compare_backtests(files):
    """Compare multiple backtest runs."""
    results = []
    for f in files:
        try:
            data = load_backtest_result(f)
            metrics = analyze_backtest(data)
            results.append((f, metrics))
        except Exception as e:
            print(f"[WARNING] Error loading {f}: {e}")
    
    if len(results) < 2:
        print("Need at least 2 valid backtest files to compare")
        return
    
    print(f"\n{'='*90}")
    print(f"Backtest Comparison (Latest First)")
    print(f"{'='*90}")
    print(f"{'File':<35} {'Return':>10} {'Sharpe':>8} {'Drawdown':>10} {'Win%':>8} {'Trades':>8}")
    print(f"{'-'*90}")
    
    baseline = results[0][1]
    for filepath, metrics in results:
        filename = Path(filepath).name[:32]
        print(f"{filename:<35} {metrics['total_return']:>9.2f}% {metrics['sharpe_ratio']:>8.2f} "
              f"{metrics['max_drawdown']:>9.2f}% {metrics['win_rate_pct']:>7.1f}% {metrics['total_trades']:>8}")
    
    print(f"{'='*90}")
    
    # Show improvement/deterioration
    if len(results) >= 2:
        latest = results[0][1]
        previous = results[1][1]
        
        print(f"\n📊 Changes vs Previous Run:")
        ret_change = latest['total_return'] - previous['total_return']
        sharpe_change = latest['sharpe_ratio'] - previous['sharpe_ratio']
        
        print(f"   Return:    {ret_change:+.2f}% {'📈' if ret_change > 0 else '📉' if ret_change < 0 else '➡️'}")
        print(f"   Sharpe:    {sharpe_change:+.2f} {'📈' if sharpe_change > 0 else '📉' if sharpe_change < 0 else '➡️'}")


def analyze_symbol_performance(filepath):
    """Analyze performance by symbol from trades CSV."""
    csv_path = filepath.replace('.json', '_trades.csv')
    if not Path(csv_path).exists():
        print(f"\n⚠️  No trades CSV found at {csv_path}")
        return
    
    try:
        import csv
        symbol_stats = defaultdict(lambda: {'trades': 0, 'wins': 0, 'pnl': 0})
        
        with open(csv_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                symbol = row.get('symbol', 'UNKNOWN')
                pnl = float(row.get('pnl', 0))
                
                symbol_stats[symbol]['trades'] += 1
                symbol_stats[symbol]['pnl'] += pnl
                if pnl > 0:
                    symbol_stats[symbol]['wins'] += 1
        
        print(f"\n📈 Symbol Performance:")
        print(f"{'Symbol':<12} {'Trades':>8} {'Win%':>8} {'Total P&L':>12}")
        print(f"{'-'*45}")
        
        for symbol, stats in sorted(symbol_stats.items(), key=lambda x: x[1]['pnl'], reverse=True):
            win_pct = (stats['wins'] / stats['trades'] * 100) if stats['trades'] > 0 else 0
            print(f"{symbol:<12} {stats['trades']:>8} {win_pct:>7.1f}% {stats['pnl']:>11.2f}")
            
    except Exception as e:
        print(f"[WARNING] Error analyzing trades: {e}")


def main():
    parser = argparse.ArgumentParser(description='Analyze backtest results')
    parser.add_argument('--latest', action='store_true', help='Show latest backtest summary')
    parser.add_argument('--compare', type=int, metavar='N', help='Compare last N backtests')
    parser.add_argument('--file', type=str, help='Analyze specific backtest file')
    parser.add_argument('--symbols', action='store_true', help='Analyze symbol performance')
    
    args = parser.parse_args()
    
    if args.latest:
        latest = find_latest_backtest()
        if not latest:
            print("❌ No backtest files found (elemental_backtest_*.json)")
            sys.exit(1)
        
        data = load_backtest_result(latest)
        metrics = analyze_backtest(data)
        print_summary(latest, metrics)
        
        if args.symbols:
            analyze_symbol_performance(latest)
    
    elif args.compare:
        files = find_backtest_runs(count=args.compare)
        if len(files) < 2:
            print(f"[ERROR] Only found {len(files)} backtest file(s), need at least 2 to compare")
            sys.exit(1)
        
        compare_backtests(files)
    
    elif args.file:
        if not Path(args.file).exists():
            print(f"[ERROR] File not found: {args.file}")
            sys.exit(1)
        
        data = load_backtest_result(args.file)
        metrics = analyze_backtest(data)
        print_summary(args.file, metrics)
        
        if args.symbols:
            analyze_symbol_performance(args.file)
    
    else:
        parser.print_help()
        print("\n[TIP] Run 'python run_backtest_menu.py' to execute a new backtest")


if __name__ == '__main__':
    main()
