"""Test MetaOrchestrator with Global Chitta."""
import asyncio
from backend.agents.meta_orchestrator import MetaOrchestrator, get_global_chitta
from backend.agents.sentiment_agent_v2 import SentimentAgentV2
from backend.agents.analyst_agent import AnalystAgent


async def test_meta_orchestrator():
    print("=" * 60)
    print("V12 META ORCHESTRATOR TEST")
    print("=" * 60)

    # 1. Initialize Global Chitta
    print("\n[1] Initializing Global Chitta...")
    global_chitta = get_global_chitta()
    print(f"   Global trades: {len(global_chitta.global_trades)}")

    # 2. Create agents
    print("\n[2] Creating conscious agents...")
    sentiment_agent = SentimentAgentV2()
    analyst_agent = AnalystAgent()

    print(f"   SentimentAgentV2: Chitta={len(sentiment_agent.chitta.trades) if sentiment_agent.chitta else 0} trades")
    print(f"   AnalystAgent: Chitta={len(analyst_agent.chitta.trades) if analyst_agent.chitta else 0} trades")

    # 3. Create MetaOrchestrator
    print("\n[3] Creating MetaOrchestrator...")
    meta = MetaOrchestrator()
    meta.register_agent(sentiment_agent)
    meta.register_agent(analyst_agent)

    print(f"   Registered {len(meta.agents)} agents")

    # 4. Get agent rankings
    print("\n[4] Agent Rankings:")
    rankings = global_chitta.get_agent_rankings()
    for rank in rankings[:5]:
        print(f"   {rank['agent']}: {rank['winrate']:.0%} winrate ({rank['total_trades']} trades)")

    # 5. Simulate deliberation
    print("\n[5] Running Collective Deliberation...")
    market_state = {
        "symbol": "BTC",
        "price": 45000,
        "trend": "bullish",
        "volatility": 0.3
    }

    decision = await meta.deliberate(market_state)

    print(f"   Action: {decision.action}")
    print(f"   Confidence: {decision.confidence:.2%}")
    print(f"   Harmony Score: {decision.harmony_score:.2f}")
    print(f"   Supporting Agents: {decision.supporting_agents}")
    print(f"   Reasoning: {decision.collective_reasoning}")
    print(f"   Should Pause: {decision.should_pause}")

    # 6. Get collective consensus
    print("\n[6] Collective Consensus for BTC:")
    consensus = global_chitta.get_collective_consensus("BTC", market_state)
    print(f"   Consensus: {consensus['consensus_action']}")
    print(f"   Confidence: {consensus['confidence']:.2%}")
    print(f"   Harmony: {consensus['harmony_score']:.2f}")

    # 7. Reflect on collective performance
    print("\n[7] Collective Reflection:")
    reflection = global_chitta.reflect_collective(n_trades=50)
    print(f"   Insight: {reflection['insight']}")
    print(f"   Action: {reflection['action']}")
    print(f"   Winrate: {reflection.get('winrate', 0):.0%}")

    # 8. Session summary
    print("\n[8] Session Summary:")
    summary = meta.get_session_summary()
    print(f"   {summary}")

    print("\n" + "=" * 60)
    print("TEST COMPLETE - MetaOrchestrator v12 Working!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_meta_orchestrator())
