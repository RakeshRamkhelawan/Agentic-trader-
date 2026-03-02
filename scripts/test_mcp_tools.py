"""
Test MCP tools via client.
"""

import asyncio
import sys

from backend.mcp_broker.client import MCPClientWrapper


async def test_tools():
    """Test MCP tools."""
    print("="*60, file=sys.stderr)
    print("TEST 2: MCP Tools Test", file=sys.stderr)
    print("="*60, file=sys.stderr)
    
    client = MCPClientWrapper()
    
    try:
        # Test 1: Health check
        print("\n[1] Testing system__health_check...", file=sys.stderr)
        result = await client.call_tool('system__health_check', {})
        print(f"Status: {result.get('status', 'N/A')}", file=sys.stderr)
        assert result.get('status') == 'healthy', "Health check failed"
        
        # Test 2: VedAstro signal
        print("\n[2] Testing vedastro__generate_signal...", file=sys.stderr)
        result = await client.call_tool('vedastro__generate_signal', {
            'symbol': 'AAPL',
            'current_price': 150.0
        })
        print(f"Signal: {result.get('signal', 'N/A')}", file=sys.stderr)
        assert 'signal' in result, "Missing signal in response"
        
        # Test 3: Elemental consensus
        print("\n[3] Testing elemental__ether_consensus...", file=sys.stderr)
        result = await client.call_tool('elemental__ether_consensus', {
            'fire_vote': 0.8,
            'earth_vote': 0.7,
            'water_vote': 0.6,
            'air_vote': 0.5,
            'symbol': 'AAPL'
        })
        print(f"Should enter: {result.get('should_enter', False)}", file=sys.stderr)
        assert 'should_enter' in result, "Missing should_enter in response"
        
        # Test 4: Position sizing
        print("\n[4] Testing elemental__fire_position_size...", file=sys.stderr)
        result = await client.call_tool('elemental__fire_position_size', {
            'symbol': 'AAPL',
            'portfolio_value': 100000.0,
            'vedastro_score': 80.0,
            'price_history': [150.0] * 20
        })
        print(f"Position size: {result.get('position_size_eur', 0):.2f} EUR", file=sys.stderr)
        assert result.get('position_size_eur', 0) > 0, "Invalid position size"
        
        print("\n" + "="*60, file=sys.stderr)
        print("[OK] All tool tests passed!", file=sys.stderr)
        print("="*60, file=sys.stderr)
        return True
        
    except Exception as e:
        print(f"\n[FAILED] Tool test error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        return False


if __name__ == "__main__":
    success = asyncio.run(test_tools())
    sys.exit(0 if success else 1)
