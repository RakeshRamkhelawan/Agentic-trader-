#!/usr/bin/env python3
"""
Test client for MCP Server.

Usage:
    python scripts/test_mcp_client.py

Requirements:
    pip install mcp[cli]
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def test_mcp_server():
    """Test the MCP server."""
    
    # Server parameters
    server_params = StdioServerParameters(
        command="python",
        args=["-m", "backend.mcp_broker.server"],
        env={"PYTHONPATH": str(Path(__file__).parent.parent)}
    )
    
    print("=" * 60)
    print("AgenticTraderBroker MCP Client Test")
    print("=" * 60)
    print("Connecting to MCP server...")
    
    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                # Initialize
                await session.initialize()
                print("✓ Connected to MCP server\n")
                
                # List tools
                tools = await session.list_tools()
                print(f"✓ Available tools: {len(tools.tools)}")
                print("\nTools:")
                for tool in tools.tools:
                    print(f"  - {tool.name}")
                print()
                
                # Test 1: Elemental consensus
                print("=" * 60)
                print("Test 1: Elemental Ether Consensus")
                print("=" * 60)
                result = await session.call_tool(
                    "elemental__ether_consensus",
                    {
                        "fire_vote": 0.8,
                        "earth_vote": 0.7,
                        "water_vote": 0.6,
                        "air_vote": 0.5
                    }
                )
                print(f"Result: {result.content[0].text if result.content else 'No result'}")
                print()
                
                # Test 2: Fire position sizing
                print("=" * 60)
                print("Test 2: Fire Position Sizing (V17 Constraint Test)")
                print("=" * 60)
                result = await session.call_tool(
                    "elemental__fire_position_size",
                    {
                        "symbol": "AAPL",
                        "portfolio_value": 100000.0,
                        "vedastro_score": 80.0,
                        "dominant_planet": "JUPITER",
                        "price_history": [100.0 + i * 0.5 for i in range(30)]
                    }
                )
                print(f"Result: {result.content[0].text if result.content else 'No result'}")
                print()
                
                # Test 3: Earth entry check
                print("=" * 60)
                print("Test 3: Earth Entry Check (3-Loss Rule)")
                print("=" * 60)
                result = await session.call_tool(
                    "elemental__earth_entry_check",
                    {
                        "symbol": "AAPL",
                        "trade_history": [
                            {"symbol": "AAPL", "pnl": -100, "win": False},
                            {"symbol": "AAPL", "pnl": -200, "win": False},
                            {"symbol": "AAPL", "pnl": -150, "win": False},
                        ]
                    }
                )
                print(f"Result: {result.content[0].text if result.content else 'No result'}")
                print()
                
                # Test 4: Earth exit check
                print("=" * 60)
                print("Test 4: Earth Exit Check (60-Day Failsafe)")
                print("=" * 60)
                from datetime import datetime, timedelta
                entry_date = (datetime.utcnow() - timedelta(days=65)).isoformat()
                current_date = datetime.utcnow().isoformat()
                
                result = await session.call_tool(
                    "elemental__earth_exit_check",
                    {
                        "symbol": "AAPL",
                        "entry_date": entry_date,
                        "current_date": current_date,
                        "entry_price": 100.0,
                        "current_price": 120.0,
                        "peak_price": 130.0
                    }
                )
                print(f"Result: {result.content[0].text if result.content else 'No result'}")
                print()
                
                # Test 5: Water regime check
                print("=" * 60)
                print("Test 5: Water Regime Check")
                print("=" * 60)
                result = await session.call_tool(
                    "elemental__water_regime_check",
                    {
                        "symbol": "SPY",
                        "prices": [400.0 + i * 2 for i in range(25)]
                    }
                )
                print(f"Result: {result.content[0].text if result.content else 'No result'}")
                print()
                
                # Test 6: Data - historical prices
                print("=" * 60)
                print("Test 6: Historical Prices")
                print("=" * 60)
                start_date = (datetime.utcnow() - timedelta(days=30)).isoformat()
                end_date = datetime.utcnow().isoformat()
                
                result = await session.call_tool(
                    "data__get_historical_prices",
                    {
                        "symbol": "AAPL",
                        "start_date": start_date,
                        "end_date": end_date,
                        "timeframe": "1d"
                    }
                )
                print(f"Result: {result.content[0].text if result.content else 'No result'}")
                print()
                
                # Test 7: Execution - paper trade
                print("=" * 60)
                print("Test 7: Paper Trade Execution")
                print("=" * 60)
                result = await session.call_tool(
                    "execution__execute_paper_trade",
                    {
                        "symbol": "AAPL",
                        "action": "BUY",
                        "quantity": 10.0,
                        "current_price": 150.0,
                        "account_id": "test_account_001"
                    }
                )
                print(f"Result: {result.content[0].text if result.content else 'No result'}")
                print()
                
                # Test 8: Health check
                print("=" * 60)
                print("Test 8: System Health Check")
                print("=" * 60)
                result = await session.call_tool("system__health_check", {})
                print(f"Result: {result.content[0].text if result.content else 'No result'}")
                print()
                
                print("=" * 60)
                print("✓ All tests completed!")
                print("=" * 60)
    
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(test_mcp_server())
    sys.exit(exit_code)
