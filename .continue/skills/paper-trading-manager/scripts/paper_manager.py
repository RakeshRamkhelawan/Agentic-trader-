#!/usr/bin/env python3
"""
Paper Trading Manager - Manage paper trading sessions.

Usage:
    python paper_manager.py start --exchange bitvavo --assets BTC/EUR --auto 30
    python paper_manager.py list --limit 10
    python paper_manager.py show latest
    python paper_manager.py compare session1 session2
    python paper_manager.py import session_id
"""

import argparse
import csv
import glob
import json
import shutil
import subprocess
import sys
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional


def find_session_files(pattern: str = "paper_trading_session_*.json") -> list[str]:
    """Find all paper trading session files."""
    files = glob.glob(pattern)
    files.sort(key=lambda f: Path(f).stat().st_mtime, reverse=True)
    return files


def find_real_session_files(pattern: str = "real_paper_session_*.json") -> list[str]:
    """Find real paper trading session files."""
    files = glob.glob(pattern)
    files.sort(key=lambda f: Path(f).stat().st_mtime, reverse=True)
    return files


def parse_session_file(filepath: str) -> dict:
    """Parse a session file."""
    with open(filepath, 'r') as f:
        return json.load(f)


def get_session_summary(filepath: str) -> dict:
    """Get summary of a session."""
    try:
        data = parse_session_file(filepath)

        trades = data.get('trades', [])
        pnls = [t.get('pnl', 0) for t in trades]

        winning_trades = len([p for p in pnls if p > 0])
        total_trades = len(trades)

        return {
            'filename': Path(filepath).name,
            'session_id': data.get('session_id', 'unknown'),
            'timestamp': data.get('timestamp', 'unknown'),
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': total_trades - winning_trades,
            'total_pnl': sum(pnls),
            'avg_pnl': sum(pnls) / len(pnls) if pnls else 0,
            'win_rate': (winning_trades / total_trades * 100) if total_trades > 0 else 0,
            'best_trade': max(pnls) if pnls else 0,
            'worst_trade': min(pnls) if pnls else 0,
            'exchange': data.get('exchange', 'unknown'),
            'symbols': list(set(t.get('symbol', 'unknown') for t in trades)),
        }
    except Exception as e:
        return {
            'filename': Path(filepath).name,
            'error': str(e)
        }


def list_sessions(limit: int = 10, format_type: str = 'table'):
    """List paper trading sessions."""

    files = find_session_files() + find_real_session_files()
    files = files[:limit]

    if not files:
        print("[ERROR] No paper trading sessions found")
        return

    print(f"\n{'='*100}")
    print(f"Paper Trading Sessions (last {limit})")
    print(f"{'='*100}")

    if format_type == 'table':
        print(f"{'Session':<25} {'Date':<16} {'Trades':<8} {'Win%':<8} {'P&L':<12} {'Exchange'}")
        print(f"{'-'*100}")

        for filepath in files:
            summary = get_session_summary(filepath)

            if 'error' in summary:
                continue

            session_id = summary['session_id'][:20]
            date = summary['timestamp'][:16] if len(summary['timestamp']) > 16 else summary['timestamp']
            trades = summary['total_trades']
            win_rate = f"{summary['win_rate']:.1f}%"
            pnl = f"€{summary['total_pnl']:.2f}"
            exchange = summary['exchange']

            print(f"{session_id:<25} {date:<16} {trades:<8} {win_rate:<8} {pnl:<12} {exchange}")

    elif format_type == 'json':
        summaries = [get_session_summary(f) for f in files]
        print(json.dumps(summaries, indent=2))


def show_session(session_id: str, show_trades: bool = False, show_chart: bool = False):
    """Show details of a specific session."""

    # Find session file
    if session_id.lower() == 'latest':
        files = find_session_files() + find_real_session_files()
        if not files:
            print("❌ No sessions found")
            return
        filepath = files[0]
    else:
        # Search by partial ID
        files = find_session_files() + find_real_session_files()
        filepath = None
        for f in files:
            if session_id in f:
                filepath = f
                break

        if not filepath:
            print(f"[ERROR] Session '{session_id}' not found")
            return

    summary = get_session_summary(filepath)

    if 'error' in summary:
        print(f"[ERROR] Error reading session: {summary['error']}")
        return

    print(f"\n{'='*70}")
    print(f"Session: {summary['session_id']}")
    print(f"{'='*70}")
    print(f"Timestamp:  {summary['timestamp']}")
    print(f"Exchange:   {summary['exchange']}")
    print(f"Symbols:    {', '.join(summary['symbols'])}")
    print(f"\n📊 Performance:")
    print(f"   Total Trades: {summary['total_trades']}")
    print(f"   Win Rate:     {summary['win_rate']:.1f}%")
    print(f"   Total P&L:    €{summary['total_pnl']:.2f}")
    print(f"   Avg Trade:    €{summary['avg_pnl']:.2f}")
    print(f"   Best Trade:   €{summary['best_trade']:.2f}")
    print(f"   Worst Trade:  €{summary['worst_trade']:.2f}")

    if show_trades:
        data = parse_session_file(filepath)
        trades = data.get('trades', [])

        if trades:
            print(f"\n📋 Trades:")
            print(f"   {'Time':<12} {'Symbol':<10} {'Side':<6} {'Price':<12} {'P&L':<12}")
            print(f"   {'-'*60}")

            for trade in trades[:20]:  # Show first 20
                time = trade.get('timestamp', '')[-12:-4] if len(trade.get('timestamp', '')) > 12 else 'N/A'
                symbol = trade.get('symbol', 'N/A')
                side = trade.get('side', 'N/A')
                price = f"€{trade.get('price', 0):,.2f}"
                pnl = f"€{trade.get('pnl', 0):.2f}"
                print(f"   {time:<12} {symbol:<10} {side:<6} {price:<12} {pnl:<12}")

            if len(trades) > 20:
                print(f"   ... and {len(trades) - 20} more trades")


def compare_sessions(session1: str, session2: str, metrics: list[str] = None):
    """Compare two sessions."""

    # Find session files
    files = find_session_files() + find_real_session_files()

    file1 = None
    file2 = None

    for f in files:
        if session1 in f:
            file1 = f
        if session2 in f:
            file2 = f

    if not file1:
        print(f"❌ Session '{session1}' not found")
        return
    if not file2:
        print(f"❌ Session '{session2}' not found")
        return

    summary1 = get_session_summary(file1)
    summary2 = get_session_summary(file2)

    print(f"\n{'='*70}")
    print(f"Session Comparison")
    print(f"{'='*70}")

    # Header
    print(f"\n{'Metric':<20} {summary1['session_id'][:20]:<25} {summary2['session_id'][:20]:<25} {'Change'}")
    print(f"{'-'*80}")

    # Metrics
    comparisons = [
        ('Total Trades', 'total_trades', 0),
        ('Win Rate (%)', 'win_rate', 1),
        ('Total P&L (€)', 'total_pnl', 2),
        ('Avg Trade (€)', 'avg_pnl', 2),
        ('Best Trade (€)', 'best_trade', 2),
        ('Worst Trade (€)', 'worst_trade', 2),
    ]

    for label, key, decimals in comparisons:
        v1 = summary1.get(key, 0)
        v2 = summary2.get(key, 0)
        change = v2 - v1

        if decimals == 0:
            val1 = f"{int(v1)}"
            val2 = f"{int(v2)}"
            change_str = f"{int(change):+d}"
        else:
            val1 = f"{v1:.{decimals}f}"
            val2 = f"{v2:.{decimals}f}"
            change_str = f"{change:+.2f}"

        icon = '[UP]' if change > 0 else '[DOWN]' if change < 0 else '[SAME]'
        print(f"{label:<20} {val1:<25} {val2:<25} {change_str} {icon}")


def start_session(exchange: str, assets: str, auto: Optional[int] = None, duration: Optional[int] = None):
    """Start a new paper trading session."""

    print(f"\n{'='*70}")
    print(f"Starting Paper Trading Session")
    print(f"{'='*70}")
    print(f"Exchange: {exchange}")
    print(f"Assets: {assets}")
    if auto:
        print(f"Auto-trades: {auto}")

    # Build command
    cmd = [
        sys.executable,
        'scripts/realtime_paper_trading.py',
        '--exchange', exchange,
        '--symbols' if ',' in assets else '--symbol', assets
    ]

    if auto:
        cmd.extend(['--auto', str(auto)])

    print(f"\n🚀 Starting...")
    print(f"Command: {' '.join(cmd)}\n")

    # Run
    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("\n\n⏹️  Session interrupted")


def export_session(session_id: str, format_type: str = 'csv', output: Optional[str] = None):
    """Export session to file."""

    # Find session
    files = find_session_files() + find_real_session_files()
    filepath = None

    if session_id.lower() == 'latest':
        filepath = files[0] if files else None
    else:
        for f in files:
            if session_id in f:
                filepath = f
                break

    if not filepath:
        print(f"[ERROR] Session '{session_id}' not found")
        return

    data = parse_session_file(filepath)
    trades = data.get('trades', [])

    if not output:
        output = f"session_export_{session_id}.{format_type}"

    if format_type == 'csv':
        with open(output, 'w', newline='') as f:
            if trades:
                writer = csv.DictWriter(f, fieldnames=trades[0].keys())
                writer.writeheader()
                writer.writerows(trades)
        print(f"[DONE] Exported to: {output}")

    elif format_type == 'json':
        with open(output, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"[DONE] Exported to: {output}")


def cleanup_sessions(older_than_days: int = 30, dry_run: bool = True):
    """Clean up old session files."""

    cutoff = datetime.now() - timedelta(days=older_than_days)

    files = find_session_files() + find_real_session_files()

    to_delete = []
    for filepath in files:
        mtime = datetime.fromtimestamp(Path(filepath).stat().st_mtime)
        if mtime < cutoff:
            to_delete.append(filepath)

    print(f"\n{'='*70}")
    print(f"Cleanup (older than {older_than_days} days)")
    print(f"{'='*70}")
    print(f"Found {len(to_delete)} files to delete")

    if dry_run:
        print("\n🔍 Dry run - no files deleted")
        for f in to_delete:
            print(f"   Would delete: {f}")
    else:
        print("\n🗑️  Deleting files...")
        for f in to_delete:
            Path(f).unlink()
            print(f"   Deleted: {f}")
        print(f"\n✅ Deleted {len(to_delete)} files")


def main():
    parser = argparse.ArgumentParser(
        description='Paper Trading Manager'
    )
    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # List
    list_parser = subparsers.add_parser('list', help='List sessions')
    list_parser.add_argument('--limit', '-l', type=int, default=10)
    list_parser.add_argument('--format', '-f', choices=['table', 'json'], default='table')

    # Show
    show_parser = subparsers.add_parser('show', help='Show session details')
    show_parser.add_argument('session', help='Session ID or "latest"')
    show_parser.add_argument('--trades', '-t', action='store_true')
    show_parser.add_argument('--chart', '-c', action='store_true')

    # Compare
    compare_parser = subparsers.add_parser('compare', help='Compare two sessions')
    compare_parser.add_argument('session1', help='First session ID')
    compare_parser.add_argument('session2', help='Second session ID')

    # Start
    start_parser = subparsers.add_parser('start', help='Start new session')
    start_parser.add_argument('--exchange', '-e', default='bitvavo')
    start_parser.add_argument('--assets', '-a', required=True)
    start_parser.add_argument('--auto', type=int)
    start_parser.add_argument('--duration', type=int)

    # Export
    export_parser = subparsers.add_parser('export', help='Export session')
    export_parser.add_argument('session', help='Session ID or "latest"')
    export_parser.add_argument('--format', choices=['csv', 'json'], default='csv')
    export_parser.add_argument('--output', '-o')

    # Cleanup
    cleanup_parser = subparsers.add_parser('cleanup', help='Clean old sessions')
    cleanup_parser.add_argument('--older-than', type=int, default=30)
    cleanup_parser.add_argument('--dry-run', action='store_true', default=True)

    args = parser.parse_args()

    if args.command == 'list':
        list_sessions(args.limit, args.format)

    elif args.command == 'show':
        show_session(args.session, args.trades, args.chart)

    elif args.command == 'compare':
        compare_sessions(args.session1, args.session2)

    elif args.command == 'start':
        start_session(args.exchange, args.assets, args.auto, args.duration)

    elif args.command == 'export':
        export_session(args.session, args.format, args.output)

    elif args.command == 'cleanup':
        cleanup_sessions(args.older_than, args.dry_run)

    else:
        parser.print_help()
        print("\n💡 Examples:")
        print("   python paper_manager.py list --limit 5")
        print("   python paper_manager.py show latest --trades")
        print("   python paper_manager.py compare 20260219 20260220")
        print("   python paper_manager.py start --assets BTC/EUR --auto 30")


if __name__ == '__main__':
    main()
