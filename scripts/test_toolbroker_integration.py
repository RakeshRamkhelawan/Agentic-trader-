#!/usr/bin/env python3
"""
Test ToolBroker Integration.

This script tests the symbiotic integration between agents and the ToolBroker.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


async def test_toolbroker_http():
    """Test ToolBroker HTTP server."""
    import httpx
    
    base_url = "http://localhost:8001"
    
    print("=" * 60)
    print("Testing ToolBroker HTTP Server")
    print("=" * 60)
    
    async with httpx.AsyncClient() as client:
        # Test health
        print("\n1. Testing health endpoint...")
        try:
            response = await client.get(f"{base_url}/health")
            if response.status_code == 200:
                data = response.json()
                print(f"   [OK] Status: {data['status']}")
                print(f"   [OK] Tools available: {data['tools_available']}")
            else:
                print(f"   [FAIL] HTTP {response.status_code}")
                return False
        except Exception as e:
            print(f"   [FAIL] {e}")
            return False
        
        # Test list tools
        print("\n2. Testing list tools...")
        try:
            response = await client.get(f"{base_url}/tools")
            if response.status_code == 200:
                data = response.json()
                tools = data.get("tools", [])
                print(f"   [OK] Found {len(tools)} tools")
                
                # Show some tools
                for tool in tools[:5]:
                    print(f"      - {tool['name']}")
            else:
                print(f"   [FAIL] HTTP {response.status_code}")
        except Exception as e:
            print(f"   [FAIL] {e}")
        
        # Test sentiment analysis
        print("\n3. Testing sentiment analysis tool...")
        try:
            response = await client.post(
                f"{base_url}/tools/call",
                json={
                    "tool_name": "tool__external_sentiment_analysis",
                    "params": {"symbol": "BTC", "source": "news"}
                }
            )
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    result = data.get("result", {})
                    print(f"   [OK] Sentiment: {result.get('sentiment_score', 'N/A')}")
                    print(f"   [OK] Trend: {result.get('trend', 'N/A')}")
                else:
                    print(f"   [FAIL] {data.get('error')}")
            else:
                print(f"   [FAIL] HTTP {response.status_code}")
        except Exception as e:
            print(f"   [FAIL] {e}")
        
        # Test technical indicators
        print("\n4. Testing technical indicators...")
        try:
            price_history = [40000 + i * 100 for i in range(30)]  # Simulated prices
            response = await client.post(
                f"{base_url}/tools/call",
                json={
                    "tool_name": "tool__external_technical_indicators",
                    "params": {
                        "symbol": "BTC",
                        "price_history": price_history,
                        "indicators": ["rsi", "sma"]
                    }
                }
            )
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    result = data.get("result", {})
                    indicators = result.get("indicators", {})
                    print(f"   [OK] RSI: {indicators.get('rsi', 'N/A')}")
                    print(f"   [OK] Signal: {result.get('overall_signal', 'N/A')}")
                else:
                    print(f"   [FAIL] {data.get('error')}")
            else:
                print(f"   [FAIL] HTTP {response.status_code}")
        except Exception as e:
            print(f"   [FAIL] {e}")
        
        # Test VedAstro
        print("\n5. Testing VedAstro signal...")
        try:
            response = await client.post(
                f"{base_url}/tools/call",
                json={
                    "tool_name": "vedastro__generate_signal",
                    "params": {"symbol": "BTC", "current_price": 45000}
                }
            )
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    result = data.get("result", {})
                    print(f"   [OK] Signal: {result.get('signal', 'N/A')}")
                    print(f"   [OK] Confidence: {result.get('confidence', 'N/A')}")
                else:
                    print(f"   [FAIL] {data.get('error')}")
            else:
                print(f"   [FAIL] HTTP {response.status_code}")
        except Exception as e:
            print(f"   [FAIL] {e}")
    
    return True


async def test_agent_with_tools():
    """Test agent with ToolBroker integration."""
    print("\n" + "=" * 60)
    print("Testing Agent with ToolBroker")
    print("=" * 60)
    
    try:
        from backend.agents.agent_with_tools import AgentWithTools
        from backend.governance.agent_gatekeeper import AgentRole
        
        # Create agent
        print("\n1. Creating test agent...")
        agent = AgentWithTools(
            agent_name="TestAgent",
            agent_role=AgentRole.STANDARD,
            tool_broker_url="http://localhost:8001"
        )
        print("   [OK] Agent created")
        
        # Check ToolBroker health
        print("\n2. Checking ToolBroker health...")
        health = await agent.check_toolbroker_health()
        print(f"   [OK] Status: {health.get('status', 'unknown')}")
        
        # List tools
        print("\n3. Listing available tools...")
        tools = await agent.list_available_tools()
        print(f"   [OK] Found {len(tools)} tools")
        
        # Test sentiment via agent
        print("\n4. Testing sentiment via agent...")
        sentiment = await agent.call_tool(
            "tool__external_sentiment_analysis",
            {"symbol": "BTC", "source": "news"}
        )
        print(f"   [OK] Sentiment: {sentiment.get('sentiment_score', 'N/A')}")
        
        # Cleanup
        await agent.close()
        print("\n   [OK] Agent closed successfully")
        
        return True
        
    except Exception as e:
        print(f"   [FAIL] {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_enhanced_sentiment_agent():
    """Test EnhancedSentimentAgent."""
    print("\n" + "=" * 60)
    print("Testing EnhancedSentimentAgent")
    print("=" * 60)
    
    try:
        from backend.agents.enhanced_sentiment_agent import EnhancedSentimentAgent
        
        # Create agent
        print("\n1. Creating EnhancedSentimentAgent...")
        agent = EnhancedSentimentAgent(
            tool_broker_url="http://localhost:8001"
        )
        print("   [OK] Agent created")
        
        # Run analysis
        print("\n2. Running analysis...")
        result = await agent.analyze(
            features={
                "symbol": "BTC",
                "price": 45000.0,
                "history": [40000 + i * 150 for i in range(50)]
            },
            context={"portfolio_value": 100000.0}
        )
        
        print(f"   [OK] Signal: {result['signal']}")
        print(f"   [OK] Confidence: {result['confidence']}")
        print(f"   [OK] Metadata keys: {list(result['metadata'].keys())}")
        
        # Cleanup
        await agent.close()
        print("\n   [OK] Agent closed successfully")
        
        return True
        
    except Exception as e:
        print(f"   [FAIL] {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("ToolBroker Integration Test Suite")
    print("=" * 60)
    
    results = []
    
    # Test 1: HTTP Server
    results.append(("ToolBroker HTTP", await test_toolbroker_http()))
    
    # Test 2: Agent with tools
    results.append(("Agent with Tools", await test_agent_with_tools()))
    
    # Test 3: Enhanced Sentiment Agent
    results.append(("EnhancedSentimentAgent", await test_enhanced_sentiment_agent()))
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    for name, passed in results:
        status = "[PASS]" if passed else "[FAIL]"
        print(f"{status} {name}")
    
    total = len(results)
    passed = sum(1 for _, p in results if p)
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n[OK] All tests passed!")
        return 0
    else:
        print("\n[WARNING] Some tests failed")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
