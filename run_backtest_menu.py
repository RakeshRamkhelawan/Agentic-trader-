#!/usr/bin/env python3
"""
Backtest Menu - Kies welke backtest je wilt runnen

Usage:
    python run_backtest_menu.py
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


def print_menu():
    print("\n" + "=" * 70)
    print("AGENTIC TRADER - BACKTEST MENU")
    print("=" * 70)
    print("\n1. SNELLE BACKTEST (30 dagen, rule-based)")
    print("   └─ python run_agent_backtest.py --days 30")
    print("\n2. LLM-POWERED BACKTEST (met DeepSeek)")
    print("   └─ docker exec api-server python scripts/llm_backtest_runner.py")
    print("\n3. RULE-BASED BACKTEST (zonder LLM)")
    print("   └─ docker exec api-server python scripts/llm_backtest_runner.py --no-llm")
    print("\n4. AGENT BENCHMARK (Vergelijk LLM vs Rule-Based)")
    print("   └─ docker exec api-server python scripts/agent_benchmark.py --days 30")
    print("\n5. UNIFIED CONSCIOUSNESS BACKTEST")
    print("   └─ docker exec api-server python scripts/run_unified_backtest.py")
    print("\n0. EXIT")
    print("\n" + "=" * 70)


async def run_option(option: str):
    import subprocess
    
    if option == "1":
        print("\nRunning: Snelle Backtest...")
        cmd = ["docker", "exec", "api-server", "python", "run_agent_backtest.py", "--days", "30"]
    
    elif option == "2":
        print("\nRunning: LLM-Powered Backtest (DeepSeek)...")
        print("⚠️  Dit maakt daadwerkelijk API calls naar DeepSeek (kosten: ~$0.01-0.05)")
        cmd = ["docker", "exec", "api-server", "python", "scripts/llm_backtest_runner.py", "--days", "30"]
    
    elif option == "3":
        print("\nRunning: Rule-Based Backtest...")
        cmd = ["docker", "exec", "api-server", "python", "scripts/llm_backtest_runner.py", "--days", "30", "--no-llm"]
    
    elif option == "4":
        print("\nRunning: Agent Benchmark...")
        print("⚠️  Dit draait 2 backtests en kan 2-5 minuten duren")
        cmd = ["docker", "exec", "-it", "api-server", "python", "scripts/agent_benchmark.py", "--days", "30"]
    
    elif option == "5":
        print("\nRunning: Unified Consciousness Backtest...")
        cmd = ["docker", "exec", "api-server", "python", "scripts/run_unified_backtest.py", "--days", "30"]
    
    elif option == "0":
        print("\nExiting...")
        return
    
    else:
        print(f"\nInvalid option: {option}")
        return
    
    # Run the command
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    
    # Stream output
    for line in process.stdout:
        print(line, end='')
    
    process.wait()
    print(f"\n✓ Exit code: {process.returncode}")


def main():
    while True:
        print_menu()
        choice = input("\nSelect option [0-5]: ").strip()
        
        if choice == "0":
            break
        
        try:
            asyncio.run(run_option(choice))
        except KeyboardInterrupt:
            print("\n\nInterrupted by user.")
            break
        
        input("\nPress Enter to continue...")
    
    print("\nGoodbye!")


if __name__ == "__main__":
    main()
