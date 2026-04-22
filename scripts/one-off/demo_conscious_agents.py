"""
Demo: Conscious Agents with LLM + Chitta Memory
Shows the integration without creating new agents
"""

import asyncio
from datetime import datetime

# Import existing agents (now with consciousness)
from backend.agents.elemental_orchestrator import ElementalOrchestrator
from backend.agents.elemental_base import ElementalBase


async def demo_conscious_orchestrator():
    """Demonstrate Ether orchestrator with LLM + Chitta"""

    print("=" * 70)
    print("  CONSCIOUS AGENTS DEMO - LLM + Chitta Integration")
    print("=" * 70)

    # Initialize Ether Orchestrator (auto-loads Chitta + LLM)
    print("\n[1] Initializing Ether Orchestrator...")
    ether = ElementalOrchestrator()

    print(f"  Agent: {ether.agent_name}")
    print(f"  Element: {ether.element}")
    print(f"  Guna Balance: {ether.guna_balance}")
    print(f"  Chitta Memory: {len(ether.chitta.trades)} trades loaded")
    print(f"  LLM Backend: {ether.llm.config.backend.value}/{ether.llm.config.model}")

    # Simulate processing signals from other elements
    print("\n[2] Processing elemental signals...")

    mock_signal = {
        "inputs": {
            "air": {
                "sentiment": 0.6,
                "regime": "trending_up",
                "confidence": 0.75
            },
            "fire": {
                "approved": True,
                "momentum": 0.7,
                "risk_level": "medium"
            },
            "water": {
                "regime": "expansion",
                "trend_strength": 0.8,
                "structure": "bullish"
            },
            "earth": {
                "valuation_gap": 0.12,
                "near_support": True,
                "entry_quality": 0.7
            }
        }
    }

    print("  Inputs:")
    for element, data in mock_signal["inputs"].items():
        print(f"    [{element.upper()}]: {data}")

    # Process (this uses LLM for harmonization)
    print("\n[3] Harmonizing with LLM...")
    result = await ether.process_signal(mock_signal)

    print(f"  Harmony Score: {result.get('harmony_score', 0):.2f}")
    print(f"  Synthesis: {result.get('synthesis', {})}")
    print(f"  Prana Remaining: {result.get('prana_remaining', 0):.1f}")

    # Show Chitta + LLM stats
    print("\n[4] Conscious Stats...")
    stats = ether.get_conscious_stats()
    print(f"  Chitta Trades Stored: {stats['chitta_stats']['total_trades_stored']}")
    print(f"  Active Strategies: {stats['chitta_stats']['active_strategies']}")
    print(f"  LLM Backend: {stats['llm_stats']['backend']}")
    print(f"  LLM Model: {stats['llm_stats']['model']}")

    # Demonstrate reflection
    print("\n[5] Reflection capability...")
    reflection = ether.reflect_recent_performance(n_trades=5)
    print(f"  Insight: {reflection.get('insight', 'N/A')}")
    print(f"  Recommended Action: {reflection.get('recommended_action', 'N/A')}")

    print("\n" + "=" * 70)
    print("  DEMO COMPLETE")
    print("=" * 70)
    print("\nEach elemental agent now has:")
    print("  - Its own Chitta Memory (persistent learning)")
    print("  - LLM integration (DeepSeek/Ollama)")
    print("  - Reflection capabilities")
    print("  - Similar experience retrieval (RAG)")
    print("\nNO new agents were created - existing agents enhanced!")


if __name__ == "__main__":
    asyncio.run(demo_conscious_orchestrator())
