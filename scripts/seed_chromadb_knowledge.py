"""
RAG Knowledge Base Seed Script for ChromaDB

Seeds ChromaDB with trading knowledge for V18 RAG integration.
Uses ChromaDB instead of PostgreSQL pgvector.

Usage:
    python scripts/seed_chromadb_knowledge.py
"""

import asyncio
import json
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

import chromadb
from chromadb.config import Settings

# Strategy Playbooks
STRATEGY_PLAYBOOKS = [
    {
        "id": "v18_entry_rules",
        "category": "playbook",
        "content": """V18 Elemental Consensus Strategy - BUY Entry Rules:

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

Best performing planets for BUY: JUPITER (expansion), VENUS (harmony), MERCURY (opportunity)""",
        "metadata": {"strategy": "V18_Consensus", "type": "entry_rules", "side": "buy"}
    },
    {
        "id": "v18_exit_rules",
        "category": "playbook",
        "content": """V18 Elemental Consensus Strategy - SELL/Exit Rules:

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
- Record detailed exit reason for Chitta learning""",
        "metadata": {"strategy": "V18_Consensus", "type": "exit_rules", "side": "sell"}
    },
    {
        "id": "v18_agent_roles",
        "category": "playbook",
        "content": """V18 Elemental Agents - Role Definitions:

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
- Weight in consensus: 10-20%""",
        "metadata": {"strategy": "V18_Consensus", "type": "agent_roles"}
    },
]

# Market Regime Guidance
REGIME_GUIDANCE = [
    {
        "id": "regime_expansion",
        "category": "macro_event",
        "content": """Expansion Regime Characteristics:
- ADX > 25 (trending market)
- Price above 20-day EMA
- Increasing volume on up days
- VedAstro: Jupiter or Venus dominant

Strategy Adjustments:
- Increase position sizes (Fire element boost)
- Lower entry thresholds (more aggressive)
- Focus on momentum strategies
- Reduce cash allocation

Historical Performance: Win rate ~65% in expansion regimes""",
        "metadata": {"regime": "expansion", "indicator": "adx", "trend": "bullish"}
    },
    {
        "id": "regime_contraction",
        "category": "macro_event",
        "content": """Contraction Regime Characteristics:
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

Historical Performance: Win rate ~45% in contraction regimes, use caution""",
        "metadata": {"regime": "contraction", "indicator": "adx", "trend": "bearish"}
    },
    {
        "id": "regime_neutral",
        "category": "macro_event",
        "content": """Neutral Regime Characteristics:
- ADX 20-25 (transition zone)
- Price around 20-day EMA
- Mixed signals from indicators
- VedAstro: Mercury or Moon dominant

Strategy Adjustments:
- Maintain normal position sizes
- Standard entry thresholds
- Diversify across more symbols
- Wait for clear directional signals

Historical Performance: Win rate ~55% in neutral regimes""",
        "metadata": {"regime": "neutral", "indicator": "adx", "trend": "sideways"}
    },
]

# Historical Scenarios
HISTORICAL_SCENARIOS = [
    {
        "id": "scenario_btc_jupiter",
        "category": "scenario",
        "content": """Scenario: BTC-EUR Strong Buy with Jupiter Dominant
Context: Expansion regime, ADX 32, RSI 58, Jupiter dominant planet
Action: BUY entry with 1.5% position size
Outcome: SUCCESS - 12% profit over 5 days

Key Factors:
- High VedAstro confidence (72%) with Jupiter expansion energy
- Strong trend (ADX > 30)
- Good momentum (RSI not overbought)
- Water regime confirmed expansion

Lesson: Jupiter + high ADX + expansion = high probability long setup""",
        "metadata": {"symbol": "BTC-EUR", "outcome": "success", "return_pct": 12.0, "planet": "JUPITER", "regime": "expansion"}
    },
    {
        "id": "scenario_eth_saturn",
        "category": "scenario",
        "content": """Scenario: ETH-EUR Buy with Saturn Dominant
Context: Contraction regime, ADX 18, Saturn dominant planet
Action: BUY entry with 1.0% position size
Outcome: FAILURE - 7% loss, hit stop loss

Key Factors:
- Saturn (restriction) dominant during contraction
- Low ADX (choppy market)
- Should have waited for regime shift
- Earth element should have blocked entry

Lesson: Avoid entries when Saturn dominant in contraction regime""",
        "metadata": {"symbol": "ETH-EUR", "outcome": "failure", "return_pct": -7.0, "planet": "SATURN", "regime": "contraction"}
    },
    {
        "id": "scenario_sol_mars",
        "category": "scenario",
        "content": """Scenario: SOL-EUR Strong Buy with Mars Dominant
Context: Neutral regime, ADX 24, Mars dominant, high volatility
Action: BUY entry with 0.8% position size (reduced due to Mars)
Outcome: SUCCESS - 8% profit over 3 days

Key Factors:
- Mars (action) can work with smaller size
- Moderate ADX
- Tight stop loss used (5% instead of 7%)
- Quick profit taking

Lesson: Mars dominant requires smaller size but can be profitable with tight risk management""",
        "metadata": {"symbol": "SOL-EUR", "outcome": "success", "return_pct": 8.0, "planet": "MARS", "regime": "neutral"}
    },
    {
        "id": "scenario_ada_moon",
        "category": "scenario",
        "content": """Scenario: ADA-EUR Buy with Moon Dominant
Context: Expansion regime, ADX 28, Moon dominant, emotional market
Action: BUY entry with 1.2% position size
Outcome: PARTIAL SUCCESS - 4% profit but high volatility

Key Factors:
- Moon (mood) creates volatility
- Good trend but whipsaws
- Chitta adjusted consensus down due to past Moon volatility
- Required patience

Lesson: Moon dominant = expect volatility, use smaller size, be patient""",
        "metadata": {"symbol": "ADA-EUR", "outcome": "partial", "return_pct": 4.0, "planet": "MOON", "regime": "expansion"}
    },
    {
        "id": "scenario_dot_trailing",
        "category": "scenario",
        "content": """Scenario: Hard Exit Trigger on DOT-EUR
Context: Position up 15%, then reversed
Action: Trailing stop triggered at +7.5% (50% of max profit)
Outcome: SUCCESS - Preserved 7.5% profit instead of full reversal

Key Factors:
- Trailing stop worked as designed
- Peak price tracking functioned correctly
- No emotional decision needed (systematic exit)
- Chitta recorded the pattern

Lesson: Always respect trailing stops, they protect profits""",
        "metadata": {"symbol": "DOT-EUR", "outcome": "success", "return_pct": 7.5, "exit_type": "trailing_stop"}
    },
]

# VedAstro Guidance
VEDASTRO_GUIDANCE = [
    {
        "id": "planet_guide",
        "category": "playbook",
        "content": """Planet Influence Guide for Crypto Trading:

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
- Risk: Emotional whipsaws""",
        "metadata": {"type": "planet_guide", "system": "vedastro"}
    },
]


def seed_chromadb():
    """Seed ChromaDB with trading knowledge."""
    print("="*60)
    print("🌱 SEEDING CHROMADB KNOWLEDGE BASE")
    print("="*60)

    # Connect to ChromaDB
    print("\n🔌 Connecting to ChromaDB at localhost:8100...")
    client = chromadb.HttpClient(
        host="localhost",
        port=8100,
        settings=Settings(allow_reset=True, anonymized_telemetry=False)
    )

    # Test connection
    try:
        heartbeat = client.heartbeat()
        print(f"✅ ChromaDB connected (heartbeat: {heartbeat})")
    except Exception as e:
        print(f"❌ Failed to connect: {e}")
        return

    # Create or get collection
    collection_name = "trading_knowledge"
    try:
        client.delete_collection(collection_name)
        print(f"🗑️  Deleted existing collection: {collection_name}")
    except:
        pass

    collection = client.create_collection(
        name=collection_name,
        metadata={"description": "V18 Trading Strategy Knowledge Base"}
    )
    print(f"✅ Created collection: {collection_name}")

    # Combine all knowledge
    all_knowledge = STRATEGY_PLAYBOOKS + REGIME_GUIDANCE + HISTORICAL_SCENARIOS + VEDASTRO_GUIDANCE

    print(f"\n📚 Seeding {len(all_knowledge)} knowledge items...")

    # Add documents in batches
    for item in all_knowledge:
        try:
            # Create embedding-friendly document
            doc_id = item["id"]
            content = item["content"].strip()
            metadata = {
                "category": item["category"],
                **item.get("metadata", {}),
                "seeded_at": datetime.utcnow().isoformat()
            }

            # Add to collection (ChromaDB generates embeddings automatically)
            collection.add(
                ids=[doc_id],
                documents=[content],
                metadatas=[metadata]
            )

            print(f"  ✅ Added: {doc_id} ({item['category']})")

        except Exception as e:
            print(f"  ❌ Failed to add {item.get('id', 'unknown')}: {e}")

    # Verify
    count = collection.count()
    print(f"\n📊 Total documents in collection: {count}")

    # Test query
    print("\n🧪 Testing similarity search...")
    test_query = "Jupiter expansion regime BUY signal"
    results = collection.query(
        query_texts=[test_query],
        n_results=3
    )

    print(f"\n  Query: '{test_query}'")
    print(f"  Results:")
    for i, (doc_id, distance) in enumerate(zip(results['ids'][0], results['distances'][0])):
        print(f"    {i+1}. {doc_id} (distance: {distance:.3f})")

    print("\n" + "="*60)
    print("✅ CHROMADB SEEDING COMPLETE!")
    print("="*60)
    print("\nV18 RAG is now ready to use!")
    print("The engine will query ChromaDB for similar scenarios during trading.")


if __name__ == "__main__":
    seed_chromadb()
