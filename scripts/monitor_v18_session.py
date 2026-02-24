#!/usr/bin/env python3
"""
V18 Paper Trading Session Monitor

Real-time monitoring van de 8-uur paper trading sessie.
Toont status, trades, consensus distributie, en waarschuwt bij problemen.

Usage:
    python scripts/monitor_v18_session.py

Of voor continu monitoring:
    python scripts/monitor_v18_session.py --watch
"""

import json
import sys
import time
import argparse
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict

def format_duration(seconds):
    """Format seconds to readable duration."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"

def get_session_status():
    """Get current session status from API."""
    try:
        import urllib.request
        import urllib.error

        req = urllib.request.Request(
            "http://localhost:8003/api/v1/paper-trading/status",
            method="GET"
        )
        with urllib.request.urlopen(req, timeout=5) as response:
            return json.loads(response.read().decode())
    except Exception as e:
        return {"error": str(e)}

def read_analytics_summary():
    """Read latest analytics summary."""
    try:
        # Check in docker container
        import subprocess
        result = subprocess.run(
            ["docker", "exec", "trader-api", "cat",
             "/app/paper_trading_analytics/v18_summary_" + datetime.now().strftime("%Y%m%d") + ".json"],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            return json.loads(result.stdout)
    except:
        pass
    return None

def read_session_log():
    """Read recent session log entries."""
    try:
        import subprocess
        result = subprocess.run(
            ["docker", "exec", "trader-api", "tail", "-30", "/app/paper_trading_session.log"],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            return result.stdout
    except:
        pass
    return None

def display_status():
    """Display current session status."""
    print("\n" + "="*80)
    print("     V18 PANCHA-TATTVA SESSION MONITOR")
    print("="*80)
    print(f"     Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)

    # Get API status
    status = get_session_status()

    if "error" in status:
        print(f"\n[ERROR] Cannot connect to API: {status['error']}")
        print("\nTroubleshooting:")
        print("  1. Check if docker container is running: docker ps | findstr trader-api")
        print("  2. Check API logs: docker logs trader-api --tail 20")
        return False

    is_running = status.get('is_running', False)
    print(f"\n[SESSION STATUS] {'RUNNING' if is_running else 'STOPPED'}")

    if not is_running:
        print("\nNo active session. Start one with:")
        print('  $body = @{ initial_capital = 10000; duration_hours = 8 } | ConvertTo-Json')
        print('  Invoke-RestMethod -Uri "http://localhost:8003/api/v1/paper-trading/start" -Method POST -Body $body -ContentType "application/json"')
        return False

    # Display trading mode
    print(f"Trading Mode: {status.get('trading_mode', 'unknown')}")

    # Read analytics
    analytics = read_analytics_summary()
    if analytics:
        print("\n[ANALYTICS SUMMARY]")

        # Trades
        total_evals = analytics.get('summary', {}).get('total_evaluations', 0)
        v18_trades = analytics.get('summary', {}).get('v18_trades', 0)
        print(f"  Evaluations: {total_evals}")
        print(f"  Trades: {v18_trades}")
        if total_evals > 0:
            print(f"  Selectivity: {v18_trades/total_evals*100:.1f}%")

        # Agent leadership
        agent_perf = analytics.get('agent_performance', {})
        print(f"\n[AGENT LEADERSHIP]")
        for agent, data in agent_perf.items():
            if data.get('evaluations', 0) > 0:
                rate = data.get('leadership_rate', 0)
                print(f"  {agent}: {rate:.1f}% ({data['trades_led']}/{data['evaluations']})")

        # Entry types
        entry_types = analytics.get('entry_types', {})
        print(f"\n[ENTRY TYPES]")
        for entry_type, count in entry_types.items():
            if count > 0:
                print(f"  {entry_type}: {count}")

        # Regime performance
        regime_perf = analytics.get('regime_performance', {})
        print(f"\n[REGIME PERFORMANCE]")
        for regime, data in regime_perf.items():
            if data.get('evaluations', 0) > 0:
                rate = data.get('trades', 0) / data.get('evaluations', 1) * 100
                print(f"  {regime}: {data['trades']}/{data['evaluations']} ({rate:.1f}%)")

        # Vayu
        vayu = analytics.get('vayu_stats', {})
        if vayu.get('total_evaluations', 0) > 0:
            print(f"\n[VAYU DAMPENING]")
            print(f"  Events: {vayu.get('dampened_evaluations', 0)}/{vayu.get('total_evaluations', 0)}")
            print(f"  Avg dampener: {vayu.get('avg_dampener', 1.0):.3f}")

    # Recent log entries
    print("\n[RECENT LOG ENTRIES]")
    log = read_session_log()
    if log:
        lines = log.strip().split('\n')
        # Filter for important lines
        important = [l for l in lines if any(x in l for x in ['[ENTRY]', '[EXIT]', '[VEDASTRO', '[CONSENSUS]', 'Cycle', 'STATUS'])]
        for line in important[-10:]:
            print(f"  {line}")
    else:
        print("  (No log entries available)")

    print("\n" + "="*80)
    return True

def watch_mode():
    """Continuous monitoring mode."""
    print("\n[MONITOR MODE] Press Ctrl+C to stop\n")
    try:
        while True:
            display_status()
            time.sleep(30)  # Update every 30 seconds
    except KeyboardInterrupt:
        print("\n\nMonitor stopped.")

def generate_report():
    """Generate final session report."""
    print("\n" + "="*80)
    print("     V18 SESSION FINAL REPORT")
    print("="*80)

    analytics = read_analytics_summary()
    if not analytics:
        print("\nNo analytics data found.")
        return

    # Key metrics
    summary = analytics.get('summary', {})
    print(f"\n[SESSION METRICS]")
    print(f"  Total Evaluations: {summary.get('total_evaluations', 0)}")
    print(f"  Total Trades: {summary.get('v18_trades', 0)}")
    print(f"  Trade Rate: {summary.get('v18_trades', 0) / max(summary.get('total_evaluations', 1), 1) * 100:.1f}%")

    # Insights
    insights = analytics.get('insights', [])
    if insights:
        print(f"\n[KEY INSIGHTS]")
        for insight in insights:
            print(f"  • {insight}")

    # Recommendations
    print(f"\n[RECOMMENDATIONS]")
    agent_perf = analytics.get('agent_performance', {})
    earth_rate = agent_perf.get('EARTH', {}).get('leadership_rate', 0)
    vedastro_rate = agent_perf.get('VEDASTRO', {}).get('leadership_rate', 0)

    if earth_rate > 80:
        print("  • Earth dominates >80% - VedAstro signals may be too conservative")
        print("  • Consider lowering VedAstro threshold or checking Dasha calculations")
    elif vedastro_rate > 50:
        print("  • VedAstro leads >50% - Good cosmic timing alignment")

    vayu = analytics.get('vayu_stats', {})
    if vayu.get('dampened_evaluations', 0) > vayu.get('total_evaluations', 0) * 0.5:
        print("  • Vayu dampening >50% - Market very volatile, consider adjusting dampener thresholds")

    print("\n" + "="*80)

def main():
    parser = argparse.ArgumentParser(description="V18 Paper Trading Monitor")
    parser.add_argument("--watch", "-w", action="store_true", help="Continuous monitoring mode")
    parser.add_argument("--report", "-r", action="store_true", help="Generate final report")

    args = parser.parse_args()

    if args.report:
        generate_report()
    elif args.watch:
        watch_mode()
    else:
        display_status()
        print("\nTip: Use --watch for continuous monitoring, --report for final analysis")

if __name__ == "__main__":
    main()
