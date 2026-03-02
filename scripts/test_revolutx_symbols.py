#!/usr/bin/env python
"""Quick test for Revolut X symbols."""
import asyncio
import sys
sys.path.insert(0, ".")

from backend.mcp_broker.tools.revolut_x_tools import revolutx_get_symbols

async def test():
    result = await revolutx_get_symbols()
    print(f"Success: {result.get('success')}")
    print(f"Symbols count: {len(result.get('symbols', []))}")
    if result.get('symbols'):
        print(f"Sample: {result['symbols'][:5]}")

asyncio.run(test())
