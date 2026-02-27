#!/usr/bin/env python3
"""
Strategy Version Manager - Manage trading strategy versions V13-V18+.

Usage:
    python version_manager.py --create v18 --from v17
    python version_manager.py --compare v16,v17
    python version_manager.py --list
    python version_manager.py --analyze v17 --suggest
"""

import argparse
import json
import re
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional

# Version registry
VERSIONS = {
    'v13': {'name': 'Baseline', 'year': 2024},
    'v14': {'name': 'Elemental System', 'year': 2024},
    'v15': {'name': 'Risk Management', 'year': 2024},
    'v16': {'name': 'Multi-Asset', 'year': 2025},
    'v17': {'name': 'VedAstro Hybrid', 'year': 2026},
    'v18': {'name': 'TBD', 'year': 2026},
}


def parse_summary_file(version: str) -> dict:
    """Parse a V{VERSION}_RESULTS_SUMMARY.md file."""
    filepath = Path(f"V{version.upper()}_RESULTS_SUMMARY.md")
    
    if not filepath.exists():
        return {}
    
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Extract metrics using regex
    metrics = {}
    
    # Total Return
    return_match = re.search(r'\*\*Total Return\*\*\s*\|\s*([\d.]+)%', content)
    if return_match:
        metrics['return'] = float(return_match.group(1))
    
    # Sharpe Ratio
    sharpe_match = re.search(r'\*\*Sharpe Ratio\*\*\s*\|\s*([\d.]+)', content)
    if sharpe_match:
        metrics['sharpe'] = float(sharpe_match.group(1))
    
    # Max Drawdown
    dd_match = re.search(r'\*\*Max Drawdown\*\s*\|\s*(-?[\d.]+)%', content)
    if dd_match:
        metrics['max_drawdown'] = float(dd_match.group(1))
    
    # Trades
    trades_match = re.search(r'\*\*Total Trades\*\*\s*\|\s*(\d+)', content)
    if trades_match:
        metrics['trades'] = int(trades_match.group(1))
    
    # Win Rate
    wr_match = re.search(r'\*\*Win Rate\*\*\s*\|\s*([\d.]+)%', content)
    if wr_match:
        metrics['win_rate'] = float(wr_match.group(1))
    
    return metrics


def list_versions(format_type: str = 'table'):
    """List all versions with metrics."""
    
    print(f"\n{'='*80}")
    print("Strategy Versions")
    print(f"{'='*80}")
    
    if format_type == 'table':
        print(f"{'Version':<8} {'Name':<20} {'Return':<10} {'Sharpe':<8} {'Trades':<8} {'Status'}")
        print(f"{'-'*80}")
        
        for ver in ['v13', 'v14', 'v15', 'v16', 'v17', 'v18']:
            info = VERSIONS.get(ver, {})
            metrics = parse_summary_file(ver)
            
            ret = f"{metrics.get('return', 0):.2f}%" if metrics else "N/A"
            sharpe = f"{metrics.get('sharpe', 0):.2f}" if metrics else "N/A"
            trades = str(metrics.get('trades', 0)) if metrics else "N/A"
            
            status = "[OK] Ready" if metrics else "[PENDING]"
            
            print(f"{ver.upper():<8} {info.get('name', 'Unknown'):<20} {ret:<10} {sharpe:<8} {trades:<8} {status}")
    
    elif format_type == 'json':
        data = {}
        for ver in VERSIONS:
            data[ver] = {
                'info': VERSIONS[ver],
                'metrics': parse_summary_file(ver)
            }
        print(json.dumps(data, indent=2))


def compare_versions(versions: list[str], metrics: list[str] = None):
    """Compare multiple versions."""
    
    if metrics is None:
        metrics = ['return', 'sharpe', 'trades', 'win_rate']
    
    print(f"\n{'='*80}")
    print(f"Version Comparison: {', '.join([v.upper() for v in versions])}")
    print(f"{'='*80}")
    
    # Header
    header = f"{'Metric':<15}"
    for ver in versions:
        header += f" {ver.upper():<12}"
    print(header)
    print(f"{'-'*80}")
    
    # Data
    all_metrics = {}
    for ver in versions:
        all_metrics[ver] = parse_summary_file(ver)
    
    for metric in metrics:
        row = f"{metric.replace('_', ' ').title():<15}"
        for ver in versions:
            value = all_metrics[ver].get(metric, 0)
            if metric == 'return':
                row += f" {value:>10.2f}%"
            elif metric in ['sharpe', 'win_rate']:
                row += f" {value:>10.2f}"
            else:
                row += f" {value:>10}"
        print(row)
    
    # Calculate changes
    if len(versions) == 2:
        print(f"\n📊 Changes ({versions[0].upper()} → {versions[1].upper()}):")
        v1, v2 = versions[0], versions[1]
        for metric in metrics:
            old = all_metrics[v1].get(metric, 0)
            new = all_metrics[v2].get(metric, 0)
            change = new - old
            
            if metric == 'return':
                print(f"   {metric}: {change:+.2f}% {'📈' if change > 0 else '📉' if change < 0 else '➡️'}")
            else:
                print(f"   {metric}: {change:+.2f} {'📈' if change > 0 else '📉' if change < 0 else '➡️'}")


def analyze_version(version: str, suggest: bool = False):
    """Analyze a version and optionally suggest improvements."""
    
    print(f"\n{'='*80}")
    print(f"Analysis: {version.upper()}")
    print(f"{'='*80}")
    
    metrics = parse_summary_file(version)
    
    if not metrics:
        print(f"[ERROR] No metrics found for {version.upper()}")
        return
    
    # Evaluate against targets
    targets = {
        'return': 10.0,
        'sharpe': 1.0,
        'max_drawdown': -5.0,
        'trades': 800,
        'win_rate': 45.0
    }
    
    print(f"\n📊 Metrics vs Targets:")
    for metric, target in targets.items():
        actual = metrics.get(metric, 0)
        
        if metric == 'max_drawdown':
            # Lower is better (less negative)
            status = '✅' if actual > target else '⚠️'
        else:
            # Higher is better
            status = '✅' if actual >= target else '⚠️'
        
        if metric in ['return', 'max_drawdown', 'win_rate']:
            print(f"   {status} {metric:15s}: {actual:>7.2f}% (target: {target:.2f}%)")
        else:
            print(f"   {status} {metric:15s}: {actual:>7} (target: {target:.0f})")
    
    # Specific V17 analysis
    if version.lower() == 'v17':
        print(f"\n🔍 V17 Specific Analysis:")
        print(f"   Execute Rate: ~6.34% (target: 15-25%)")
        print(f"   VedAstro Entries: 332/332 (100%)")
        print(f"   Hedge Entries: 1 (first working hedge!)")
        
        if suggest:
            print(f"\n💡 Recommendations for V18:")
            print(f"\n   Option A: Relax VedAstro Filters")
            print(f"      - Lower min confidence: 50% → 40%")
            print(f"      - Lower min score: 45 → 40")
            print(f"      - Expected: +50-100% more trades")
            print(f"\n   Option B: Parallel Entry System")
            print(f"      - Keep VedAstro for quality")
            print(f"      - Add momentum entries for quantity")
            print(f"      - Expected: Execute rate 15-20%")
            print(f"\n   Option C: Dynamic Filters")
            print(f"      - Relaxed filters in strong trends")
            print(f"      - Strict filters in choppy markets")
            print(f"      - Use Water agent regime detection")


def create_version(new_version: str, from_version: str, name: str = None):
    """Create a new version from an existing one."""
    
    new_ver = new_version.lower().replace('v', '')
    from_ver = from_version.lower().replace('v', '')
    
    print(f"\n{'='*80}")
    print(f"Creating V{new_ver} from V{from_ver}")
    print(f"{'='*80}")
    
    # Check source files exist
    agent_source = Path(f"backend/agents/elemental_agent_manager_v{from_ver}.py")
    backtest_source = Path(f"scripts/backtest_elemental_v{from_ver}.py")
    
    if not agent_source.exists():
        print(f"[ERROR] Source file not found: {agent_source}")
        return
    
    # Create new files
    agent_target = Path(f"backend/agents/elemental_agent_manager_v{new_ver}.py")
    backtest_target = Path(f"scripts/backtest_elemental_v{new_ver}.py")
    
    # Copy and modify agent file
    print(f"\n📄 Creating {agent_target}...")
    with open(agent_source, 'r') as f:
        content = f.read()
    
    # Update version references
    content = content.replace(f'V{from_ver}', f'V{new_ver}')
    content = content.replace(f'v{from_ver}', f'v{new_ver}')
    content = content.replace(
        f'ElementalAgentManagerV{from_ver}',
        f'ElementalAgentManagerV{new_ver}'
    )
    
    # Add version header comment
    version_header = f'"""\nElemental Agent Manager V{new_ver}'
    if name:
        version_header += f' - {name}'
    version_header += '\n"""\n'
    
    content = version_header + content[content.find('import'):]
    
    with open(agent_target, 'w') as f:
        f.write(content)
    print(f"   [OK] Created")
    
    # Copy backtest file
    if backtest_source.exists():
        print(f"\n📄 Creating {backtest_target}...")
        with open(backtest_source, 'r') as f:
            content = f.read()
        
        content = content.replace(f'V{from_ver}', f'V{new_ver}')
        content = content.replace(f'v{from_ver}', f'v{new_ver}')
        
        with open(backtest_target, 'w') as f:
            f.write(content)
        print(f"   [OK] Created")
    
    # Create summary template
    summary_file = Path(f"V{new_ver}_RESULTS_SUMMARY.md")
    print(f"\n📄 Creating {summary_file}...")
    
    summary_template = f"""# V{new_ver} Results Summary - {name or 'New Version'}

## Overview
V{new_ver} builds on V{from_ver} with [DESCRIPTION].

## Results

### Full Backtest (2020-2026, 50 Assets)
| Metric | V{from_ver} | **V{new_ver}** | Change |
|--------|-------------|----------------|--------|
| **Total Return** | - | **-%** | - |
| **Sharpe Ratio** | - | **-.--** | - |
| **Max Drawdown** | - | **-%** | - |
| **Total Trades** | - | **-** | - |
| **Win Rate** | - | **-%** | - |

### Key Changes
1. [Change 1]
2. [Change 2]
3. [Change 3]

### Files
- Agent: `backend/agents/elemental_agent_manager_v{new_ver}.py`
- Engine: `scripts/backtest_elemental_v{new_ver}.py`
- Results: `backtest_v{new_ver}_full_*.json`

## Conclusion
[Summary of V{new_ver} performance and next steps]
"""
    
    with open(summary_file, 'w') as f:
        f.write(summary_template)
    print(f"   [OK] Created")
    
    print(f"\n✨ V{new_ver} scaffolded successfully!")
    print(f"\nNext steps:")
    print(f"   1. Edit {agent_target}")
    print(f"   2. Implement your changes")
    print(f"   3. Run: python {backtest_target}")
    print(f"   4. Update {summary_file}")


def main():
    parser = argparse.ArgumentParser(
        description='Strategy Version Manager'
    )
    parser.add_argument('--list', '-l', action='store_true',
                       help='List all versions')
    parser.add_argument('--format', default='table',
                       choices=['table', 'json'],
                       help='Output format')
    parser.add_argument('--compare', '-c',
                       help='Compare versions (comma-separated)')
    parser.add_argument('--metrics', '-m',
                       help='Metrics to compare (comma-separated)')
    parser.add_argument('--analyze', '-a',
                       help='Analyze specific version')
    parser.add_argument('--suggest', '-s', action='store_true',
                       help='Suggest improvements')
    parser.add_argument('--create',
                       help='Create new version (e.g., v18)')
    parser.add_argument('--from', dest='from_ver',
                       help='Base version for creation')
    parser.add_argument('--name', '-n',
                       help='Name for new version')
    
    args = parser.parse_args()
    
    if args.list:
        list_versions(args.format)
    
    elif args.compare:
        versions = [v.strip() for v in args.compare.split(',')]
        metrics = None
        if args.metrics:
            metrics = [m.strip() for m in args.metrics.split(',')]
        compare_versions(versions, metrics)
    
    elif args.analyze:
        analyze_version(args.analyze, args.suggest)
    
    elif args.create and args.from_ver:
        create_version(args.create, args.from_ver, args.name)
    
    else:
        parser.print_help()
        print("\n💡 Examples:")
        print("   python version_manager.py --list")
        print("   python version_manager.py --compare v16,v17")
        print("   python version_manager.py --analyze v17 --suggest")
        print("   python version_manager.py --create v18 --from v17 --name 'Execute Rate Fix'")


if __name__ == '__main__':
    main()
