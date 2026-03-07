"""
RAG Knowledge Base Seed Script

Seeds the trading_knowledge vector store with:
- Strategy playbooks
- Market regime guidance
- Historical scenarios
- Elemental agent guidance
- VedAstro interpretations

Usage:
    python scripts/seed_rag_knowledge.py

Environment:
    Requires DATABASE_URL to be set in environment or .env file
"""

import asyncio
import json
import os
import sys
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

load_dotenv()

from backend.core.config.settings import settings
from backend.rag.vector_memory import VectorMemory, VectorStoreError


# Strategy Playbooks
STRATEGY_PLAYBOOKS = [
    {
        "category": "playbook",
        "content": """
V18 Elemental Consensus Strategy - BUY Entry Rules:

REQUIRED for BUY entry:
1. VedAstro signal must be BUY or STRONG_BUY with confidence > 50%
2. Earth element must NOT block entry (no 3 recent losses on symbol)
3. Fire element must approve position size > 0
4. Water element regime must not be strongly contractionary
5. Total consensus must exceed threshold (typically 0.4-0.6)

Position Sizing:
- Max 2% of portfolio per position
- Max EUR 2000 per position
- Fire element calculates size based on confidence and volatility

Best performing planets for BUY: JUPITER (expansion), VENUS (harmony), MERCURY (opportunity)
        """,
        "metadata": {"strategy": "V18_Consensus", "type": "entry_rules", "side": "buy"}
    },
    {
        "category": "playbook",
        "content": """
V18 Elemental Consensus Strategy - SELL/Exit Rules:

HARD EXIT triggers (immediate exit regardless of consensus):
1. Stop loss at -7% from entry
2. Trailing stop: 50% of maximum profit lost
3. Portfolio circuit breaker at -5% daily loss
4. 3 consecutive losses on symbol (Earth element block)

SOFT EXIT (consensus-based):
1. VedAstro signal changes to SELL
2. Total consensus below negative threshold
3. Water element detects regime change to contraction
4. Better opportunity found (reallocate capital)

Exit Execution:
- Use market orders for hard exits (speed priority)
- Use limit orders for soft exits (price priority)
- Record detailed exit reason for Chitta learning
        """,
        "metadata": {"strategy": "V18_Consensus", "type": "exit_rules", "side": "sell"}
    },
    {
        "category": "playbook",
        "content": """
V18 Elemental Agents - Role Definitions:

VEDASTRO (Navagrahas - 9 Planets):
- Provides cosmic timing signals based on planetary positions
- Dominant planet influences: Sun (authority), Moon (mood), Mars (action),
  Mercury (communication), Jupiter (expansion), Venus (value), Saturn (discipline)
- Vote range: -1.0 (strong sell) to +1.0 (strong buy)
- Weight in consensus: 30-40%

EARTH (Prithvi - Stability):
- Risk management and position validation
- Blocks entry after 3 consecutive losses on symbol
- Tracks trade history for pattern detection
- Vote range: -0.5 to +0.5
- Weight in consensus: 25-35%

FIRE (Agni - Transformation):
- Position sizing and momentum detection
- Calculates optimal position based on confidence and volatility
- Approves/rejects position sizes
- Vote range: -0.5 to +0.5
- Weight in consensus: 20-30%

WATER (Varuna - Flow):
- Market regime detection (expansion/contraction/neutral)
- Dampens signals during unfavorable regimes
- Vote range: -0.3 to +0.3
- Weight in consensus: 10-20%
        """,
        "metadata": {"strategy": "V18_Consensus", "type": "agent_roles"}
    },
]

# Market Regime Guidance
REGIME_GUIDANCE = [
    {
        "category": "macro_event",
        "content": """
Expansion Regime Characteristics:
- ADX > 25 (trending market)
- Price above 20-day EMA
- Increasing volume on up days
- VedAstro: Jupiter or Venus dominant

Strategy Adjustments:
- Increase position sizes (Fire element boost)
- Lower entry thresholds (more aggressive)
- Focus on momentum strategies
- Reduce cash allocation

Historical Performance: Win rate ~65% in expansion regimes
        """,
        "metadata": {"regime": "expansion", "indicator": "adx", "trend": "bullish"}
    },
    {
        "category": "macro_event",
        "content": """
Contraction Regime Characteristics:
- ADX < 20 (choppy/ranging market)
- Price below 20-day EMA
- Decreasing volume
- VedAstro: Saturn or Mars dominant

Strategy Adjustments:
- Decrease position sizes (Fire element reduction)
- Raise entry thresholds (more conservative)
- Increase cash allocation
- Focus on mean reversion strategies
- Enable tighter stop losses

Historical Performance: Win rate ~45% in contraction regimes, use caution
        """,
        "metadata": {"regime": "contraction", "indicator": "adx", "trend": "bearish"}
    },
    {
        "category": "macro_event",
        "content": """
Neutral Regime Characteristics:
- ADX 20-25 (transition zone)
- Price around 20-day EMA
- Mixed signals from indicators
- VedAstro: Mercury or Moon dominant

Strategy Adjustments:
- Maintain normal position sizes
- Standard entry thresholds
- Diversify across more symbols
- Wait for clear directional signals

Historical Performance: Win rate ~55% in neutral regimes
        """,
        "metadata": {"regime": "neutral", "indicator": "adx", "trend": "sideways"}
    },
]

# Historical Scenarios
HISTORICAL_SCENARIOS = [
    {
        "category": "scenario",
        "content": """
Scenario: BTC-EUR Strong Buy with Jupiter Dominant
Context: Expansion regime, ADX 32, RSI 58, Jupiter dominant planet
Action: BUY entry with 1.5% position size
Outcome: SUCCESS - 12% profit over 5 days

Key Factors:
- High VedAstro confidence (72%) with Jupiter expansion energy
- Strong trend (ADX > 30)
- Good momentum (RSI not overbought)
- Water regime confirmed expansion

Lesson: Jupiter + high ADX + expansion = high probability long setup
        """,
        "asset": "BTC-EUR",
        "metadata": {"outcome": "success", "return_pct": 12.0, "planet": "JUPITER", "regime": "expansion"}
    },
    {
        "category": "scenario",
        "content": """
Scenario: ETH-EUR Buy with Saturn Dominant
Context: Contraction regime, ADX 18, Saturn dominant planet
Action: BUY entry with 1.0% position size
Outcome: FAILURE - 7% loss, hit stop loss

Key Factors:
- Saturn (restriction) dominant during contraction
- Low ADX (choppy market)
- Should have waited for regime shift
- Earth element should have blocked entry

Lesson: Avoid entries when Saturn dominant in contraction regime
        """,
        "asset": "ETH-EUR",
        "metadata": {"outcome": "failure", "return_pct": -7.0, "planet": "SATURN", "regime": "contraction"}
    },
    {
        "category": "scenario",
        "content": """
Scenario: SOL-EUR Strong Buy with Mars Dominant
Context: Neutral regime, ADX 24, Mars dominant, high volatility
Action: BUY entry with 0.8% position size (reduced due to Mars)
Outcome: SUCCESS - 8% profit over 3 days

Key Factors:
- Mars (action) can work with smaller size
- Moderate ADX
- Tight stop loss used (5% instead of 7%)
- Quick profit taking

Lesson: Mars dominant requires smaller size but can be profitable with tight risk management
        """,
        "asset": "SOL-EUR",
        "metadata": {"outcome": "success", "return_pct": 8.0, "planet": "MARS", "regime": "neutral"}
    },
    {
        "category": "scenario",
        "content": """
Scenario: ADA-EUR Buy with Moon Dominant
Context: Expansion regime, ADX 28, Moon dominant, emotional market
Action: BUY entry with 1.2% position size
Outcome: PARTIAL SUCCESS - 4% profit but high volatility

Key Factors:
- Moon (mood) creates volatility
- Good trend but whipsaws
- Chitta adjusted consensus down due to past Moon volatility
- Required patience

Lesson: Moon dominant = expect volatility, use smaller size, be patient
        """,
        "asset": "ADA-EUR",
        "metadata": {"outcome": "partial", "return_pct": 4.0, "planet": "MOON", "regime": "expansion"}
    },
    {
        "category": "scenario",
        "content": """
Scenario: Hard Exit Trigger on DOT-EUR
Context: Position up 15%, then reversed
Action: Trailing stop triggered at +7.5% (50% of max profit)
Outcome: SUCCESS - Preserved 7.5% profit instead of full reversal

Key Factors:
- Trailing stop worked as designed
- Peak price tracking functioned correctly
- No emotional decision needed (systematic exit)
- Chitta recorded the pattern

Lesson: Always respect trailing stops, they protect profits
        """,
        "asset": "DOT-EUR",
        "metadata": {"outcome": "success", "return_pct": 7.5, "exit_type": "trailing_stop"}
    },
]

# VedAstro Guidance
VEDASTRO_GUIDANCE = [
    {
        "category": "playbook",
        "content": """
Planet Influence Guide for Crypto Trading:

JUPITER (Expansion):
- Best for: Long entries, increasing position sizes
- Effect: +20% boost to confidence
- Favorable regimes: All, especially expansion
- Risk: Can cause overtrading during strong Jupiter

SATURN (Restriction):
- Best for: Short entries, risk management
- Effect: -15% reduction to confidence, tighter stops
- Favorable regimes: Contraction for shorts
- Risk: Missed opportunities if too restrictive

MARS (Action):
- Best for: Momentum trades, quick entries/exits
- Effect: High volatility expected
- Favorable regimes: Expansion with high ADX
- Risk: Whipsaws in choppy markets

VENUS (Value):
- Best for: Swing trades, finding value entries
- Effect: +10% boost, focus on quality setups
- Favorable regimes: Neutral to expansion
- Risk: Overthinking entries

MERCURY (Communication):
- Best for: News-driven moves, quick reactions
- Effect: Information processing speed matters
- Favorable regimes: Any (adaptable)
- Risk: Fakeouts on news

SUN (Authority):
- Best for: Trend confirmation, strong directional moves
- Effect: +15% boost to trend strength
- Favorable regimes: Expansion
- Risk: Late entries

MOON (Mood):
- Best for: Sentiment-based moves
- Effect: Volatility increase
- Favorable regimes: Requires smaller size
- Risk: Emotional whipsaws
        """,
        "metadata": {"type": "planet_guide", "system": "vedastro"}
    },
]


class RAGSeeder:
    """Seeds the RAG vector store with trading knowledge."""

    def __init__(self):
        self.vector_memory = None
        self.embedding_model = None

    async def initialize(self):
        """Initialize vector memory and embedding model."""
        print("🔌 Initializing vector memory...")

        self.vector_memory = VectorMemory(
            connection_string=settings.DATABASE_URL
        )

        # Initialize schema
        await self.vector_memory.initialize_schema()
        print("✅ Vector memory schema initialized")

        # Load embedding model
        try:
            from sentence_transformers import SentenceTransformer
            self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
            print("✅ Embedding model loaded (all-MiniLM-L6-v2)")
        except ImportError:
            print("⚠️ sentence-transformers not installed, install with: pip install sentence-transformers")
            raise
        except Exception as e:
            print(f"❌ Failed to load embedding model: {e}")
            raise

    def create_embedding(self, text: str) -> list[float]:
        """Create embedding for text."""
        if self.embedding_model:
            return self.embedding_model.encode(text).tolist()
        raise RuntimeError("Embedding model not loaded")

    async def seed_knowledge(self, items: list[dict], asset: str | None = None):
        """Seed knowledge items into vector store."""
        for item in items:
            try:
                content = item["content"].strip()
                embedding = self.create_embedding(content)

                metadata = item.get("metadata", {})
                metadata["seeded_at"] = datetime.utcnow().isoformat()

                await self.vector_memory.insert(
                    content=content,
                    embedding=embedding,
                    category=item["category"],
                    asset=item.get("asset", asset),
                    metadata=metadata
                )

                print(f"  ✅ Seeded {item['category']}: {content[:50]}...")

            except Exception as e:
                print(f"  ❌ Failed to seed item: {e}")

    async def seed_all(self):
        """Seed all knowledge categories."""
        print("\n" + "="*60)
        print("🌱 RAG KNOWLEDGE BASE SEEDING")
        print("="*60)

        # Strategy Playbooks
        print("\n📚 Seeding Strategy Playbooks...")
        await self.seed_knowledge(STRATEGY_PLAYBOOKS)

        # Regime Guidance
        print("\n📊 Seeding Regime Guidance...")
        await self.seed_knowledge(REGIME_GUIDANCE)

        # Historical Scenarios
        print("\n📖 Seeding Historical Scenarios...")
        await self.seed_knowledge(HISTORICAL_SCENARIOS)

        # VedAstro Guidance
        print("\n🪐 Seeding VedAstro Guidance...")
        await self.seed_knowledge(VEDASTRO_GUIDANCE)

        print("\n" + "="*60)
        print("✅ RAG Knowledge Base Seeding Complete!")
        print("="*60)
        print(f"📊 Total items seeded: {len(STRATEGY_PLAYBOOKS) + len(REGIME_GUIDANCE) + len(HISTORICAL_SCENARIOS) + len(VEDASTRO_GUIDANCE)}")
        print("\nYou can now query similar scenarios using:")
        print("  await vector_memory.search_similar(")
        print("      query_embedding=embedding,")
        print("      category='scenario',")
        print("      limit=3")
        print("  )")

    async def close(self):
        """Close connections."""
        if self.vector_memory:
            await self.vector_memory.close()


async def main():
    """Main entry point."""
    seeder = RAGSeeder()

    try:
        await seeder.initialize()
        await seeder.seed_all()
    except Exception as e:
        print(f"\n❌ Seeding failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        await seeder.close()


if __name__ == "__main__":
    asyncio.run(main())
