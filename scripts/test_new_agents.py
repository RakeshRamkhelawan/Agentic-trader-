#!/usr/bin/env python
"""
Test script for AgentWithTools base class and concrete agent implementations.

Usage:
    python scripts/test_new_agents.py
"""

import asyncio
import logging
import sys
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)

# Add project root to path
sys.path.insert(0, "backend")

from backend.agents.elemental_consensus_agent import ElementalConsensusAgent
from backend.agents.risk_check_agent import RiskCheckAgent
from backend.agents.vedastro_signal_agent import VedAstroSignalAgent


async def test_vedastro_agent():
    """Test VedAstroSignalAgent."""
    print("\n" + "=" * 60)
    print("Testing VedAstroSignalAgent...")
    print("=" * 60)

    agent = VedAstroSignalAgent(min_confidence=0.6)
    print(f"Agent initialized: {agent.agent_name}")
    print(f"Agent role: {agent.agent_role}")
    print(f"Min confidence: {agent.min_confidence}")

    features = {"symbol": "BTC", "price": 65000.0}
    context = {"portfolio_id": "test-portfolio-123", "market_regime": "bullish"}

    result = await agent.analyze(features, context)

    print(f"\nAnalysis result: {result}")
    return result.get("action") in ["buy", "sell", "hold"]


async def test_elemental_consensus_agent():
    """Test ElementalConsensusAgent."""
    print("\n" + "=" * 60)
    print("Testing ElementalConsensusAgent...")
    print("=" * 60)

    agent = ElementalConsensusAgent()
    print(f"Agent initialized: {agent.agent_name}")
    print(f"Agent role: {agent.agent_role}")

    features = {"symbol": "BTC", "price": 65000.0}
    context = {"portfolio_id": "test-portfolio-123"}

    result = await agent.analyze(features, context)

    print(f"\nAnalysis result: {result}")
    return result.get("consensus") in ["buy", "sell", "hold"]


async def test_risk_check_agent():
    """Test RiskCheckAgent."""
    print("\n" + "=" * 60)
    print("Testing RiskCheckAgent...")
    print("=" * 60)

    agent = RiskCheckAgent(max_position_size=0.1, max_portfolio_var=0.02)
    print(f"Agent initialized: {agent.agent_name}")
    print(f"Max position size: {agent.max_position_size}")

    features = {
        "symbol": "BTC",
        "price": 65000.0,
        "side": "buy",
        "proposed_quantity": 0.5,
        "portfolio_value": 100000.0,
        "win_rate": 0.6,
        "avg_win": 0.08,
        "avg_loss": 0.04,
    }
    context = {"portfolio_id": "test-portfolio-123"}

    result = await agent.analyze(features, context)

    print(f"\nAnalysis result: {result}")
    return result.get("action") in ["approve", "modify", "reject"]


async def test_vedic_tools():
    """Test vedic tools directly."""
    print("\n" + "=" * 60)
    print("Testing Vedic Tools (direct import)...")
    print("=" * 60)

    from backend.mcp_broker.tools.vedic_dasha_tools import (
        vedic_calculate_transits,
        vedic_calculate_vimshottari_dasha,
        vedic_get_nakshatra_analysis,
    )

    class MinimalContext:
        def info(self, msg):
            print(f"[INFO] {msg}")

        def error(self, msg):
            print(f"[ERROR] {msg}")

    ctx = MinimalContext()

    # Test 1: Nakshatra analysis
    print("\n1. Testing Nakshatra Analysis...")
    nakshatra_result = await vedic_get_nakshatra_analysis("Ashwini", 1, ctx)
    print(f"   Success: {nakshatra_result.get('success')}")
    result_data = nakshatra_result.get('result', {})
    print(f"   Lord: {result_data.get('lord')}")
    nakshatra_ok = nakshatra_result.get("success") is True

    # Test 2: Vimshottari Dasha
    print("\n2. Testing Vimshottari Dasha...")
    dasha_result = await vedic_calculate_vimshottari_dasha(
        "Ashwini", 1, "2020-01-01", ctx
    )
    print(f"   Success: {dasha_result.get('success')}")
    result_data = dasha_result.get('result', {})
    current = result_data.get('current_mahadasha', {})
    print(f"   Current Dasha: {current.get('planet', 'N/A')}")
    dasha_ok = dasha_result.get("success") is True

    # Test 3: Transits
    print("\n3. Testing Transit Calculation...")
    transit_result = await vedic_calculate_transits(
        "2024-12-20",
        ["BTC", "ETH"],
        ctx,
    )
    print(f"   Success: {transit_result.get('success')}")
    result_data = transit_result.get('result', {})
    print(f"   Transit count: {len(result_data.get('transits', []))}")
    transit_ok = transit_result.get("success") is True

    return nakshatra_ok and dasha_ok and transit_ok


async def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("AgentWithTools and Concrete Agents Test Suite")
    print("=" * 60)

    results = {}

    try:
        results["vedastro_agent"] = await test_vedastro_agent()
    except Exception as e:
        logger.error(f"VedAstroSignalAgent test failed: {e}")
        results["vedastro_agent"] = False

    try:
        results["elemental_consensus_agent"] = await test_elemental_consensus_agent()
    except Exception as e:
        logger.error(f"ElementalConsensusAgent test failed: {e}")
        results["elemental_consensus_agent"] = False

    try:
        results["risk_check_agent"] = await test_risk_check_agent()
    except Exception as e:
        logger.error(f"RiskCheckAgent test failed: {e}")
        results["risk_check_agent"] = False

    try:
        results["vedic_tools"] = await test_vedic_tools()
    except Exception as e:
        logger.error(f"Vedic tools test failed: {e}")
        results["vedic_tools"] = False

    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)

    for test_name, passed in results.items():
        status = "PASS" if passed else "FAIL"
        emoji = " " if passed else " "
        print(f"{emoji} {test_name}: {status}")

    all_passed = all(results.values())
    print("\n" + "=" * 60)
    if all_passed:
        print("All tests passed!  Agents ready for production.")
    else:
        print("Some tests failed. Check logs above.")
    print("=" * 60)

    return 0 if all_passed else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
