#!/usr/bin/env python3
"""
Test script for BacktestEngine V18.

Tests the complete backtest cycle using MCP tools.
"""

import asyncio
import json
import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.mcp_broker import run_backtest_v18, ElementalAgentManagerV18, MCPClientWrapper

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_elemental_manager():
    """Test ElementalAgentManagerV18."""
    print("\n" + "=" * 60)
    print("TEST 1: ElementalAgentManagerV18")
    print("=" * 60)

    async with MCPClientWrapper() as client:
        manager = ElementalAgentManagerV18(client)
        await manager.initialize()

        # Test consensus
        print("\n1. Testing Elemental Consensus...")
        result = await manager.get_elemental_consensus(
            fire_vote=0.8,
            earth_vote=0.7,
            water_vote=0.6,
            air_vote=0.5
        )
        print(f"   Harmony: {result.get('harmony_score', 0):.2f}")
        print(f"   Approved: {result.get('approved', False)}")
        print(f"   Dominant: {result.get('dominant_element', 'unknown')}")

        # Test entry evaluation
        print("\n2. Testing Entry Evaluation...")
        price_history = [100.0 + i * 0.5 for i in range(30)]

        entry = await manager.evaluate_entry(
            symbol="AAPL",
            current_price=150.0,
            portfolio_value=100000.0,
            vedastro_score=75.0,
            dominant_planet="JUPITER",
            price_history=price_history
        )

        if entry:
            print(f"   Entry approved!")
            print(f"   Position size: €{entry['position_size']:.2f}")
            print(f"   Quantity: {entry['quantity']:.2f}")
        else:
            print("   Entry blocked")

        # Test exit evaluation
        print("\n3. Testing Exit Evaluation...")

        # Manually add a position
        manager.open_positions["TEST"] = {
            "entry_date": (datetime.utcnow() - timedelta(days=65)).isoformat(),
            "entry_price": 100.0,
            "quantity": 10.0
        }
        manager.peak_prices["TEST"] = 140.0

        should_exit, reason = await manager.evaluate_exit(
            symbol="TEST",
            current_price=120.0
        )

        print(f"   Should exit: {should_exit}")
        print(f"   Reason: {reason}")

        await manager.close()

    print("\n✓ ElementalManagerV18 test complete")


async def test_backtest_engine():
    """Test BacktestEngineV18."""
    print("\n" + "=" * 60)
    print("TEST 2: BacktestEngineV18")
    print("=" * 60)

    start_date = datetime(2024, 1, 1)
    end_date = datetime(2024, 1, 31)
    symbols = ["AAPL", "MSFT", "GOOGL"]

    print(f"\nRunning backtest:")
    print(f"  Period: {start_date.date()} to {end_date.date()}")
    print(f"  Symbols: {', '.join(symbols)}")
    print(f"  Initial cash: €50,000")

    results = await run_backtest_v18(
        symbols=symbols,
        start_date=start_date,
        end_date=end_date,
        initial_cash=50000.0
    )

    print("\n" + "-" * 60)
    print("BACKTEST RESULTS")
    print("-" * 60)
    print(f"Final value: €{results['results']['final_value']:,.2f}")
    print(f"Total return: {results['results']['total_return_pct']:+.2f}%")
    print(f"Total trades: {results['results']['total_trades']}")
    print(f"Win rate: {results['results']['win_rate']*100:.1f}%")
    print(f"Gross P&L: €{results['results']['gross_pnl']:,.2f}")
    print(f"Commissions: €{results['results']['total_commission']:,.2f}")
    print(f"Net P&L: €{results['results']['net_pnl']:,.2f}")

    # Show some trades
    if results['trades']:
        print("\nSample trades:")
        for trade in results['trades'][:5]:
            action = trade['action']
            symbol = trade['symbol']
            price = trade['price']
            print(f"  {action} {symbol} @ ${price:.2f}")

    print("\n✓ BacktestEngineV18 test complete")

    return results


async def test_mcp_tools_directly():
    """Test MCP tools directly."""
    print("\n" + "=" * 60)
    print("TEST 3: Direct MCP Tool Calls")
    print("=" * 60)

    async with MCPClientWrapper() as client:
        # Test Fire position sizing
        print("\n1. Fire Position Sizing...")
        result = await client.call_tool(
            "elemental__fire_position_size",
            {
                "symbol": "AAPL",
                "portfolio_value": 100000.0,
                "vedastro_score": 80.0,
                "dominant_planet": "JUPITER",
                "price_history": [100.0 + i * 0.5 for i in range(30)]
            }
        )
        print(f"   Position size: €{result.get('position_size_eur', 0):.2f}")
        print(f"   Max allowed: €{result.get('max_position_eur', 0):.2f}")

        # Test Earth entry check
        print("\n2. Earth Entry Check...")
        result = await client.call_tool(
            "elemental__earth_entry_check",
            {
                "symbol": "AAPL",
                "trade_history": [
                    {"symbol": "AAPL", "pnl": 100, "win": True},
                    {"symbol": "AAPL", "pnl": 200, "win": True},
                ]
            }
        )
        print(f"   Can enter: {result.get('can_enter', False)}")

        # Test VedAstro signal
        print("\n3. VedAstro Signal...")
        result = await client.call_tool(
            "vedastro__generate_signal",
            {
                "symbol": "AAPL",
                "current_price": 150.0
            }
        )
        print(f"   Signal: {result.get('signal', 'UNKNOWN')}")
        print(f"   Confidence: {result.get('confidence', 0)}%")

        # Test execution
        print("\n4. Paper Trade Execution...")
        result = await client.call_tool(
            "execution__execute_paper_trade",
            {
                "symbol": "AAPL",
                "action": "BUY",
                "quantity": 10.0,
                "current_price": 150.0,
                "account_id": "test_v18"
            }
        )
        print(f"   Order ID: {result.get('order_id', 'N/A')}")
        print(f"   Status: {result.get('status', 'N/A')}")
        print(f"   Commission: €{result.get('commission', 0):.4f}")

        # Test health check
        print("\n5. System Health Check...")
        result = await client.call_tool("system__health_check", {})
        print(f"   Status: {result.get('status', 'UNKNOWN')}")
        print(f"   Circuit breakers: {len(result.get('circuit_breaker_states', {}))}")

    print("\n✓ Direct MCP tool calls test complete")


async def compare_v17_v18():
    """Compare V17 vs V18 approaches."""
    print("\n" + "=" * 60)
    print("COMPARISON: V17 vs V18 Architecture")
    print("=" * 60)

    print("\nV17 (Old):")
    print("  - Direct agent method calls")
    print("  - Tightly coupled components")
    print("  - No failure isolation")
    print("  - Hardcoded backtest loop")

    print("\nV18 (New):")
    print("  - MCP tool calls via stdio/SSE")
    print("  - Decoupled via ToolBroker")
    print("  - Circuit breakers for resilience")
    print("  - LLM orchestration support")
    print("  - Same V17 financial constraints")

    print("\nKey improvements:")
    print("  ✓ Better error isolation")
    print("  ✓ Retry logic with backoff")
    print("  ✓ LLM can orchestrate tools")
    print("  ✓ External tools easy to add")
    print("  ✓ Standard MCP protocol")

    print("\nPreserved:")
    print("  ✓ €2,000 max position size")
    print("  ✓ 60-day failsafe")
    print("  ✓ 3-loss rule")
    print("  ✓ Trailing stops")
    print("  ✓ 0.05% commission")
    print("  ✓ 0.1% slippage")


async def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("BACKTEST V18 - MCP INTEGRATION TEST SUITE")
    print("=" * 60)

    try:
        # Test 1: Elemental Manager
        await test_elemental_manager()

        # Test 2: Backtest Engine
        results = await test_backtest_engine()

        # Test 3: Direct tool calls
        await test_mcp_tools_directly()

        # Comparison
        await compare_v17_v18()

        # Save results
        output_file = Path("backtest_v18_results.json")
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)

        print(f"\n✓ Results saved to {output_file}")

        print("\n" + "=" * 60)
        print("ALL TESTS COMPLETED SUCCESSFULLY!")
        print("=" * 60)

        return 0

    except Exception as e:
        logger.error(f"Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
