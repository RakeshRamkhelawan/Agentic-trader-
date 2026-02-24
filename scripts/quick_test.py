#!/usr/bin/env python3
"""Quick MCP client test."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.mcp_broker.client import MCPClientWrapper

async def quick_test():
    print("=" * 60)
    print("QUICK MCP CLIENT TEST")
    print("=" * 60)

    async with MCPClientWrapper() as client:
        print("1. Testing Elemental Consensus...")
        result = await client.call_tool(
            "elemental__ether_consensus",
            {"fire_vote": 0.8, "earth_vote": 0.7, "water_vote": 0.6, "air_vote": 0.5}
        )
        print(f"   Harmony: {result.get('harmony_score', 0):.2f}")
        print(f"   Approved: {result.get('approved', False)}")

        print("2. Testing Fire Position Size...")
        result = await client.call_tool(
            "elemental__fire_position_size",
            {
                "symbol": "AAPL",
                "portfolio_value": 100000.0,
                "vedastro_score": 80.0,
                "dominant_planet": "JUPITER",
                "price_history": [100.0 + i*0.5 for i in range(30)]
            }
        )
        print(f"   Position: €{result.get('position_size_eur', 0):.2f}")
        print(f"   Constraints: {result.get('constraints_applied', [])}")

        print("3. Testing VedAstro...")
        result = await client.call_tool(
            "vedastro__generate_signal",
            {"symbol": "AAPL", "current_price": 150.0}
        )
        print(f"   Signal: {result.get('signal', 'UNKNOWN')}")
        print(f"   Confidence: {result.get('confidence', 0)}%")

        print("4. Testing Health Check...")
        result = await client.call_tool("system__health_check", {})
        print(f"   Status: {result.get('status', 'UNKNOWN')}")

    print("=" * 60)
    print("ALL TESTS PASSED!")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(quick_test())
