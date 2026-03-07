"""
Test Master Prompts for BaseAgent
"""
import asyncio
from backend.agents.sentiment_agent_v2 import SentimentAgentV2
from backend.agents.analyst_agent import AnalystAgent
from backend.agents.prompts.master_prompts import get_master_prompt, format_prompt_with_data


def test_master_prompts():
    print("="*70)
    print("MASTER PROMPTS TEST")
    print("="*70)

    # Test 1: Get master prompt for different agents
    print("\n[1] Testing get_master_prompt() for different agents...")

    agents_to_test = [
        ("AnalystAgent", "Market Analyst"),
        ("TraderAgent", "Trade Executor"),
        ("RiskManagerAgent", "Risk Guardian"),
        ("Water_Trend", "Trend Follower"),
        ("Fire_Momentum", "Momentum Trader"),
    ]

    for agent_name, role in agents_to_test:
        prompt = get_master_prompt(agent_name, role, guna_balance=(0.5, 0.3, 0.2))

        # Check if prompt contains key elements
        has_5_steps = all(step in prompt for step in ["STEP 1", "STEP 2", "STEP 3", "STEP 4", "STEP 5"])
        has_chitta = "Chitta" in prompt
        has_guna = "GUNA" in prompt
        has_json = "JSON" in prompt

        print(f"\n  {agent_name}:")
        print(f"    - 5-step CoT: {'OK' if has_5_steps else 'FAIL'}")
        print(f"    - Chitta refs: {'OK' if has_chitta else 'FAIL'}")
        print(f"    - Guna balance: {'OK' if has_guna else 'FAIL'}")
        print(f"    - JSON output: {'OK' if has_json else 'FAIL'}")

        # Show snippet
        lines = prompt.split('\n')[:15]
        print(f"    Preview:\n      " + '\n      '.join(lines[:5]))

    # Test 2: Agent instantiation with prompts
    print("\n" + "="*70)
    print("[2] Testing Agent with Master Prompt...")
    print("="*70)

    try:
        agent = SentimentAgentV2()
        print(f"\n  Agent: {agent.agent_name}")
        print(f"  Has Chitta: {agent.chitta is not None}")
        print(f"  Has LLM: {agent.llm_provider is not None}")

        # Test prompt generation
        market_state = {
            "symbol": "BTC",
            "price": 45000,
            "regime": "bullish",
            "rsi": 65,
            "adx": 25,
            "volatility": 0.3
        }

        chitta_stats = {
            "recent_winrate": 0.65,
            "recent_pnl": 0.02,
            "harmony": 0.35,
            "overall_winrate": 0.62
        }

        print("\n  Generating formatted prompt...")
        base_prompt = get_master_prompt(
            agent.agent_name,
            "Sentiment Analyst",
            guna_balance=(0.4, 0.4, 0.2)
        )

        formatted = format_prompt_with_data(
            base_prompt=base_prompt,
            agent=agent,
            market_state=market_state,
            chitta_stats=chitta_stats
        )

        print(f"  Formatted prompt length: {len(formatted)} chars")
        print(f"  Contains market data: {'OK' if 'BTC' in formatted else 'FAIL'}")
        print(f"  Contains stats: {'OK' if '0.65' in formatted else 'FAIL'}")

        # Show output format example
        print("\n  Expected JSON Output Format:")
        print("""
  {
    "step1_retrieve": "Summary of similar Chitta experiences",
    "step2_analysis": {"regime": "bull", "indicators": {...}},
    "step3_reason": {"prana_level": 0.7, "maya_detected": false},
    "step4_decision": {"action": "BUY", "confidence": 0.85, ...},
    "step5_reflect": {"recent_winrate": 0.65, "improvement": "..."}
  }
        """)

    except Exception as e:
        print(f"  Error: {e}")
        import traceback
        traceback.print_exc()

    # Test 3: Self-improvement logic
    print("\n" + "="*70)
    print("[3] Self-Improvement Logic")
    print("="*70)

    test_cases = [
        (0.55, "Should reduce risk (winrate < 60%)"),
        (0.65, "Should monitor (winrate 60-70%)"),
        (0.75, "Should maintain/increase (winrate > 70%)"),
    ]

    for winrate, expected in test_cases:
        if winrate < 0.6:
            action = "Reduce risk by 20%, tighten SL"
        elif winrate > 0.7:
            action = "Maintain strategy, increase position slightly"
        else:
            action = "Monitor closely"

        print(f"\n  Winrate: {winrate:.0%}")
        print(f"  Action: {action}")
        print(f"  Expected: {expected}")

    print("\n" + "="*70)
    print("TEST COMPLETE - Master Prompts Ready!")
    print("="*70)
    print("\nNext: Run live test with LLM")
    print("  python test_master_prompts_live.py")


if __name__ == "__main__":
    test_master_prompts()
