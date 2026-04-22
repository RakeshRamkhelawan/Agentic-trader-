"""
V13 Test - Strategy Evolution + Prompt Evolution + Multi-LLM

Test met DeepSeek/OpenAI/Google failover en dual evolution system.
"""
import asyncio
import random
import logging
from datetime import datetime

from backend.agents.meta_orchestrator_v3 import MetaOrchestratorV3, AgentSignalV3
from backend.agents.multi_llm_provider import get_multi_llm
from backend.agents.strategy_evolution import get_strategy_evolution
from backend.agents.prompt_evolution import get_prompt_evolution

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MockSelfImprovingAgent:
    """Mock agent met reflection support."""

    def __init__(self, name: str, preferred_action: str = None):
        self.name = name
        self.preferred_action = preferred_action
        self.trade_count = 0

    async def analyze_with_reflection(self, features, context):
        self.trade_count += 1

        # Simulate some bias
        if self.preferred_action:
            action = self.preferred_action if random.random() < 0.7 else random.choice(["BUY", "SELL", "HOLD"])
        else:
            action = random.choice(["BUY", "SELL", "HOLD"])

        confidence = random.uniform(0.4, 0.9)
        reasoning = f"RSI={random.randint(30,70)} ADX={random.randint(15,40)}"

        return type('Result', (), {
            'action': action,
            'confidence': confidence,
            'reasoning': reasoning,
            'reflection': f"Trade #{self.trade_count} reflection",
            'confidence_adjustment': random.uniform(0.8, 1.2),
            'bias_acknowledged': False
        })()


async def test_multi_llm():
    """Test multi-LLM provider."""
    logger.info("=" * 60)
    logger.info("Testing Multi-LLM Provider")
    logger.info("=" * 60)

    llm = get_multi_llm()

    try:
        response = llm.generate(
            prompt="Geef een korte analyse van markt volatiliteit in 1 zin.",
            temperature=0.3
        )
        logger.info(f"[OK] LLM Response from {response.provider}")
        logger.info(f"     Model: {response.model}")
        logger.info(f"     Latency: {response.latency_ms:.0f}ms")
        logger.info(f"     Text: {response.text[:100]}...")
    except Exception as e:
        logger.warning(f"[X] LLM failed: {e}")


async def test_strategy_evolution():
    """Test strategy evolution."""
    logger.info("\n" + "=" * 60)
    logger.info("Testing Strategy Evolution")
    logger.info("=" * 60)

    evolution = get_strategy_evolution()

    # Register strategies first
    from backend.agents.strategy_evolution import StrategyProfile

    evolution.register_strategy("consensus_weighted", StrategyProfile(
        strategy_name="consensus_weighted",
        entry_threshold=0.6,
        exit_threshold=0.4
    ))

    evolution.register_strategy("aggressive_momentum", StrategyProfile(
        strategy_name="aggressive_momentum",
        entry_threshold=0.5,
        exit_threshold=0.3
    ))

    # Record some trades
    strategies = ["consensus_weighted", "aggressive_momentum"]
    regimes = ["trending_up", "ranging", "trending_down"]

    for i in range(30):
        strategy = random.choice(strategies)
        regime = random.choice(regimes)
        pnl = random.uniform(-0.03, 0.05)

        evolution.record_trade(
            strategy_name=strategy,
            symbol=f"SYM{i%5}",
            regime=regime,
            pnl=pnl,
            duration_days=random.randint(1, 5)
        )

    # Check metrics
    for strategy in strategies:
        metrics = evolution.calculate_metrics(strategy)
        logger.info(f"\nStrategy: {strategy}")
        logger.info(f"  Winrate: {metrics.get('winrate', 0):.1%}")
        logger.info(f"  Total PnL: {metrics.get('total_pnl', 0):.2%}")
        logger.info(f"  Sharpe: {metrics.get('sharpe_ratio', 0):.2f}")

    # Try evolution
    logger.info("\n[Evolving consensus_weighted strategy...]")
    evolved = evolution.evolve_strategy("consensus_weighted")
    if evolved:
        logger.info(f"[OK] Evolved to v{evolved.version}")
        logger.info(f"     Entry threshold: {evolved.entry_threshold}")
        logger.info(f"     Position sizing: {evolved.position_sizing}")


async def test_prompt_evolution():
    """Test prompt evolution."""
    logger.info("\n" + "=" * 60)
    logger.info("Testing Prompt Evolution")
    logger.info("=" * 60)

    prompt_evo = get_prompt_evolution()

    # Simulate prompt usage
    for i in range(15):
        success = random.random() < 0.6  # 60% success rate
        prompt_evo.record_usage(
            prompt_name="agent_reflection",
            input_data=f"trade_data_{i}",
            output_data="reflection_text",
            success=success,
            quality_score=random.uniform(4, 8),
            error_message="" if success else "parsing_error"
        )

    # Check if evolution needed
    should_evolve = prompt_evo.should_evolve("agent_reflection")
    logger.info(f"Should evolve prompt: {should_evolve}")

    # Get report
    report = prompt_evo.get_evolution_report("agent_reflection")
    logger.info(f"Total uses: {report.get('total_uses', 0)}")
    logger.info(f"Success rate: {report.get('success_rate', 0):.1%}")
    logger.info(f"Avg quality: {report.get('avg_quality', 0):.1f}/10")

    if should_evolve:
        logger.info("\n[Evolving prompt...]")
        evolved = prompt_evo.evolve_prompt("agent_reflection")
        if evolved:
            logger.info(f"[OK] Prompt evolved to v{evolved.version}")


async def test_meta_orchestrator_v3():
    """Test V3 orchestrator."""
    logger.info("\n" + "=" * 60)
    logger.info("Testing MetaOrchestrator V3")
    logger.info("=" * 60)

    orchestrator = MetaOrchestratorV3(enable_evolution=True)

    # Register mock agents
    agents = [
        MockSelfImprovingAgent("TrendFollower", "BUY"),
        MockSelfImprovingAgent("MeanReversion", "SELL"),
        MockSelfImprovingAgent("Momentum", "BUY"),
        MockSelfImprovingAgent("Volatility", "HOLD"),
        MockSelfImprovingAgent("Breakout", "BUY"),
    ]

    for agent in agents:
        orchestrator.register_agent(agent.name, agent, weight=1.0)

    logger.info(f"Registered {len(agents)} agents")

    # Run simulation
    symbols = ["AAPL", "MSFT", "GOOGL", "TSLA", "NVDA"]

    logger.info("\n[Running deliberation cycles...]")

    for i in range(20):
        symbol = random.choice(symbols)
        regime = random.choice(["trending", "ranging", "volatile"])

        market_state = {
            "symbol": symbol,
            "price": random.uniform(100, 500),
            "regime": regime,
            "rsi": random.uniform(30, 70),
            "adx": random.uniform(15, 40)
        }

        decision = await orchestrator.deliberate(market_state)

        # Simulate outcome
        pnl = random.uniform(-0.05, 0.08)
        orchestrator.update_trade_outcome(symbol, market_state["price"], pnl, "tp" if pnl > 0 else "sl")

        if i < 5:  # Show first 5
            logger.info(f"  [{i+1}] {symbol} -> {decision.final_action} "
                       f"(conf: {decision.confidence:.2f}, "
                       f"agents: {len(decision.agent_signals)}, "
                       f"pnl: {pnl:+.2%})")

    logger.info(f"\n[Completed 20 cycles]")

    # Get evolution report
    report = orchestrator.get_evolution_report()
    logger.info("\n[Evolution Report]")
    logger.info(f"  Total signals: {report['performance_summary']['total_signals_logged']}")
    logger.info(f"  Total trades: {report['performance_summary']['total_trades']}")
    logger.info(f"  Weight updates: {report['performance_summary']['adaptive_weight_updates']}")


async def main():
    """Main test runner."""
    logger.info("\n" + "=" * 60)
    logger.info("V13 EVOLUTION TEST - Multi-LLM + Dual Evolution")
    logger.info("=" * 60)
    logger.info("Features:")
    logger.info("  - DeepSeek/OpenAI/Google GenAI failover")
    logger.info("  - Strategy Evolution (langetermijn aanpassingen)")
    logger.info("  - Prompt Evolution (LLM past eigen prompts aan)")
    logger.info("  - Evolution tracking en reporting")
    logger.info("=" * 60)

    try:
        # Test components
        await test_multi_llm()
        await test_strategy_evolution()
        await test_prompt_evolution()
        await test_meta_orchestrator_v3()

        logger.info("\n" + "=" * 60)
        logger.info("[OK] V13 Test Complete!")
        logger.info("=" * 60)
        logger.info("\nOutput files:")
        logger.info("  - .tmp/signals_v3_*.csv (signal logs)")
        logger.info("  - Evolution reports in orchestrator")
        logger.info("\nNext: Check .env for DEEPSEEK_API_KEY, OPENAI_API_KEY, GOOGLE_API_KEY")

    except Exception as e:
        logger.error(f"[X] Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
