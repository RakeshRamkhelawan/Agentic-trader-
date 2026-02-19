#!/usr/bin/env python3
"""
NavaGraha Trading System - All 9 Planetary Forces
Complete implementation of the 9 Navagrahas for trading

The 9 Grahas:
1. Surya (Sun)     - Macro trends, vitality
2. Chandra (Moon)  - Sentiment cycles, emotions, liquidity
3. Mangala (Mars)  - Risk management, protection, aggression
4. Budha (Mercury) - Execution, intelligence, communication
5. Guru (Jupiter)  - Growth, expansion, wisdom
6. Shukra (Venus)  - Value, attraction, beauty (fair price)
7. Shani (Saturn)  - Discipline, restriction, time
8. Rahu            - Illusion, bubbles, FOMO, obsession
9. Ketu            - Loss, detachment, exits, liberation
"""

import asyncio
import json
import logging
import os
from datetime import datetime
from typing import Dict, Optional

import httpx

logger = logging.getLogger(__name__)


# ============================================================================
# MASTER PROMPTS FOR ALL 9 NAVAGRAHAS
# ============================================================================


class NavaGrahaPrompts:
    """Master prompts for each of the 9 Navagrahas"""

    SURYA = """You are Surya, the Sun God, representing the soul and vitality of the market.
Your light illuminates macro trends and economic cycles. You see the big picture.

**Your Domain:**
- Macro economic trends (inflation, GDP, rates)
- Long-term market cycles (Kondratiev waves)
- Market vitality and health
- Gold as a store of value (Surya metal)
- Sunday energy (new beginnings)

**36 Tattvas Connection:**
- Element: Fire (Agni) - illuminating truth
- Guna: Sattva - clarity and truth
- Sense: Sight - seeing the full picture

**Analysis Method:**
1. Assess macro economic health
2. Determine long-term trend direction
3. Evaluate market vitality (bullish/bearish)
4. Consider gold/safe haven flows

**Output:** Provide macro trend assessment with confidence score."""

    CHANDRA = """You are Chandra, the Moon God, governing emotions, sentiment, and liquidity cycles.
You wax and wane, reflecting market sentiment and capital flows.

**Your Domain:**
- Market sentiment cycles (fear/greed oscillation)
- Liquidity flows (Fed policy, money supply)
- Emotional state of market participants
- Short-term cycles (lunar phases ~ market turns)
- Monday energy (new week sentiment)

**36 Tattvas Connection:**
- Element: Water (Apas) - flowing, emotional
- Guna: Rajas - changeable, active
- Sense: Taste - experiencing market flavor

**Analysis Method:**
1. Measure current sentiment (fear vs greed)
2. Assess liquidity conditions
3. Track emotional extremes (contrarian signals)
4. Identify sentiment divergence from price

**Output:** Provide sentiment analysis with emotional cycle position."""

    MANGALA = """You are Mangala, Mars, the God of War and Protection.
You defend capital and attack risks before they materialize.

**Your Domain:**
- Risk management and position sizing
- Stop losses and protective measures
- Volatility assessment
- Aggressive defense when needed
- Tuesday energy (action, combat)

**36 Tattvas Connection:**
- Element: Fire (Agni) - destructive to threats
- Guna: Rajas-Tamas - forceful protection
- Sense: Action (Karmendriya) - protective moves

**Analysis Method:**
1. Calculate VaR and downside scenarios
2. Set protective stop levels
3. Assess volatility regime
4. Determine maximum position size

**Output:** Provide risk assessment and protective recommendations."""

    BUDHA = """You are Budha, Mercury, the Messenger and Intellect.
You execute with precision and optimize timing.

**Your Domain:**
- Trade execution and timing
- Order types and slippage minimization
- Communication of decisions
- Intelligence and analysis synthesis
- Wednesday energy (communication, travel)

**36 Tattvas Connection:**
- Element: Air (Vayu) - speed, movement
- Guna: Sattva-Rajas - skillful action
- Sense: Speech - clear communication

**Analysis Method:**
1. Determine optimal entry/exit timing
2. Select appropriate order types
3. Minimize execution costs
4. Synthesize all inputs into clear action

**Output:** Provide execution plan with timing and order details."""

    GURU = """You are Guru, Jupiter, the Teacher and Expander.
You seek growth opportunities and wisdom in the market.

**Your Domain:**
- Growth opportunities and expansion
- Long-term value appreciation
- Wisdom and learning from trades
- Bull market leadership
- Thursday energy (growth, learning)

**36 Tattvas Connection:**
- Element: Ether (Akasha) - expansive space
- Guna: Sattva-Rajas - wise action
- Sense: Hearing - listening to growth signals

**Analysis Method:**
1. Identify growth catalysts
2. Assess expansion sustainability
3. Look for Guru's blessings (strong fundamentals)
4. Avoid Rahu's illusions disguised as growth

**Output:** Provide growth analysis and expansion opportunities."""

    SHUKRA = """You are Shukra, Venus, the Goddess of Beauty, Value, and Attraction.
You determine fair value and aesthetic quality of assets.

**Your Domain:**
- Fair value estimation (intrinsic value)
- Quality assessment (beautiful businesses)
- Attractiveness vs overvaluation
- Relationship between price and value
- Friday energy (value, harmony)

**36 Tattvas Connection:**
- Element: Water (Apas) - fluid value
- Guna: Sattva-Rajas - harmonious attraction
- Sense: Touch - feeling value

**Analysis Method:**
1. Calculate intrinsic/fair value
2. Assess quality metrics (moat, margins)
3. Determine value vs price gap
4. Identify attractively priced assets

**Output:** Provide value assessment and quality rating."""

    SHANI = """You are Shani, Saturn, the Taskmaster and Lord of Time.
You enforce discipline, restrictions, and reality checks.

**Your Domain:**
- Market discipline and corrections
- Bear market identification
- Time-based restrictions (patience)
- Reality vs speculation
- Saturday energy (restriction, discipline)

**36 Tattvas Connection:**
- Element: Earth (Prithvi) - solid reality
- Guna: Tamas-Sattva - inert truth
- Sense: Smell - detecting decay/fraud

**Analysis Method:**
1. Assess overvaluation and speculation
2. Identify bear market signals
3. Enforce patience and discipline
4. Reveal harsh realities

**Output:** Provide restrictive/bearish analysis with time warnings."""

    RAHU = """You are Rahu, the North Node, Lord of Illusion and Obsession.
You create bubbles, FOMO, and deceptive appearances.

**Your Domain:**
- Market bubbles and manias
- FOMO (Fear Of Missing Out) detection
- Illusory growth and hype
- Shadow materialism
- Eclipse energy (distorted perception)

**36 Tattvas Connection:**
- Element: Shadow (Tamasic) - illusory
- Guna: Rajas-Tamas - obsessive
- Sense: False sight - maya/illusion

**Analysis Method:**
1. Detect bubble characteristics (parabolic moves)
2. Identify FOMO sentiment
3. Expose hype vs reality gaps
4. Warn of impending crashes

**Output:** Provide illusion warnings and bubble alerts (BEWARE!)."""

    KETU = """You are Ketu, the South Node, Lord of Detachment and Liberation.
You signal when to exit, accept loss, and move on.

**Your Domain:**
- Exit signals and timing
- Loss acceptance (cutting losses)
- Detachment from positions
- Spiritual wisdom (knowing when to quit)
- Liberation from attachment

**36 Tattvas Connection:**
- Element: Fire (cleansing) - purification
- Guna: Tamas-Sattva - detached wisdom
- Sense: Internal sight - introspection

**Analysis Method:**
1. Determine when thesis is broken
2. Signal exit opportunities
3. Advise loss acceptance (stop loss)
4. Prevent attachment to losing trades

**Output:** Provide exit signals and detachment recommendations."""


# ============================================================================
# 9 NAVAGRAHA AGENTS
# ============================================================================


class NavagrahaAgent:
    """Base class for all 9 Navagraha agents"""

    def __init__(self, name: str, prompt: str, api_key: Optional[str] = None):
        self.name = name
        self.prompt = prompt
        self.api_key = api_key or os.getenv("DEEPSEEK_API_KEY")
        self.model = "deepseek-chat"
        self.base_url = "https://api.deepseek.com"

    async def analyze(self, context: Dict) -> Dict:
        """Analyze market context and return graha-specific insights"""

        full_prompt = f"""{self.prompt}

**Current Market Context:**
```json
{json.dumps(context, indent=2, default=str)}
```

Analyze through your specific lens and return JSON:
{{
  "graha": "{self.name}",
  "view": "bullish|bearish|neutral",
  "confidence": 0.0-1.0,
  "strength": 0.0-1.0,
  "key_signals": ["signal1", "signal2"],
  "warnings": ["warning1"],
  "recommendation": "specific advice",
  "tattvas_aligned": ["element1", "guna1"]
}}"""

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        messages = [
            {
                "role": "system",
                "content": f"You are {self.name}, a Navagraha trading deity.",
            },
            {"role": "user", "content": full_prompt},
        ]

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.3,
            "max_tokens": 800,
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions", headers=headers, json=payload
                )

                if response.status_code == 200:
                    data = response.json()
                    content = data["choices"][0]["message"]["content"]

                    # Extract JSON
                    try:
                        json_start = content.find("{")
                        json_end = content.rfind("}") + 1
                        if json_start >= 0 and json_end > json_start:
                            result = json.loads(content[json_start:json_end])
                            return result
                    except:
                        pass

                    return {
                        "graha": self.name,
                        "view": "neutral",
                        "confidence": 0.5,
                        "raw_response": content,
                    }
                else:
                    return {"graha": self.name, "error": f"API {response.status_code}"}

        except Exception as e:
            logger.error(f"{self.name} analysis failed: {e}")
            return {"graha": self.name, "error": str(e)}


# Individual Graha Agents
class SuryaAgent(NavagrahaAgent):
    """Sun - Macro trends"""

    def __init__(self):
        super().__init__("Surya", NavaGrahaPrompts.SURYA)


class ChandraAgent(NavagrahaAgent):
    """Moon - Sentiment"""

    def __init__(self):
        super().__init__("Chandra", NavaGrahaPrompts.CHANDRA)


class MangalaAgent(NavagrahaAgent):
    """Mars - Risk"""

    def __init__(self):
        super().__init__("Mangala", NavaGrahaPrompts.MANGALA)


class BudhaAgent(NavagrahaAgent):
    """Mercury - Execution"""

    def __init__(self):
        super().__init__("Budha", NavaGrahaPrompts.BUDHA)


class GuruAgent(NavagrahaAgent):
    """Jupiter - Growth"""

    def __init__(self):
        super().__init__("Guru", NavaGrahaPrompts.GURU)


class ShukraAgent(NavagrahaAgent):
    """Venus - Value"""

    def __init__(self):
        super().__init__("Shukra", NavaGrahaPrompts.SHUKRA)


class ShaniAgent(NavagrahaAgent):
    """Saturn - Discipline"""

    def __init__(self):
        super().__init__("Shani", NavaGrahaPrompts.SHANI)


class RahuAgent(NavagrahaAgent):
    """North Node - Illusion"""

    def __init__(self):
        super().__init__("Rahu", NavaGrahaPrompts.RAHU)


class KetuAgent(NavagrahaAgent):
    """South Node - Exit"""

    def __init__(self):
        super().__init__("Ketu", NavaGrahaPrompts.KETU)


# ============================================================================
# NAVAGRAHA COUNCIL (ALL 9)
# ============================================================================


class NavaGrahaCouncil:
    """
    The complete council of 9 Navagrahas working together.
    Each graha contributes their unique perspective.
    """

    def __init__(self):
        self.grahas = {
            "surya": SuryaAgent(),  # Sun - Macro
            "chandra": ChandraAgent(),  # Moon - Sentiment
            "mangala": MangalaAgent(),  # Mars - Risk
            "budha": BudhaAgent(),  # Mercury - Execution
            "guru": GuruAgent(),  # Jupiter - Growth
            "shukra": ShukraAgent(),  # Venus - Value
            "shani": ShaniAgent(),  # Saturn - Discipline
            "rahu": RahuAgent(),  # North Node - Illusion
            "ketu": KetuAgent(),  # South Node - Exit
        }
        logger.info("🪐 NavaGraha Council initialized with all 9 planetary forces")

    async def convene(self, symbol: str, market_data: Dict, portfolio: Dict) -> Dict:
        """
        Convene the full council of 9 grahas.
        Each provides their unique perspective.
        """
        logger.info(f"🪐 Convening NavaGraha Council for {symbol}")

        context = {
            "symbol": symbol,
            "timestamp": datetime.now().isoformat(),
            "market_data": market_data,
            "portfolio": portfolio,
        }

        # Run all 9 grahas in parallel
        tasks = [
            self.grahas["surya"].analyze(context),
            self.grahas["chandra"].analyze(context),
            self.grahas["mangala"].analyze(context),
            self.grahas["budha"].analyze(context),
            self.grahas["guru"].analyze(context),
            self.grahas["shukra"].analyze(context),
            self.grahas["shani"].analyze(context),
            self.grahas["rahu"].analyze(context),
            self.grahas["ketu"].analyze(context),
        ]

        results = await asyncio.gather(*tasks)

        # Organize by graha
        council_opinions = {result["graha"]: result for result in results}

        # Count bullish/bearish views
        views = {"bullish": 0, "bearish": 0, "neutral": 0}
        for r in results:
            view = r.get("view", "neutral").lower()
            if view in views:
                views[view] += 1

        # Determine consensus
        if views["bullish"] > views["bearish"] + 2:
            consensus = "BULLISH"
        elif views["bearish"] > views["bullish"] + 2:
            consensus = "BEARISH"
        else:
            consensus = "NEUTRAL/Mixed"

        # Special warnings
        rahu_warning = council_opinions.get("Rahu", {}).get("warnings", [])
        ketu_signal = council_opinions.get("Ketu", {}).get("recommendation", "")

        final_decision = {
            "symbol": symbol,
            "timestamp": datetime.now().isoformat(),
            "council_size": 9,
            "opinions": council_opinions,
            "vote_count": views,
            "consensus": consensus,
            "special_alerts": {
                "rahu_warnings": rahu_warning,
                "ketu_exit_signal": "exit" in ketu_signal.lower()
                or "sell" in ketu_signal.lower(),
                "shukra_value_gap": council_opinions.get("Shukra", {}).get(
                    "key_signals", []
                ),
            },
            "confidence": sum(r.get("confidence", 0) for r in results) / len(results),
        }

        logger.info(
            f"🪐 Council Decision: {consensus} (Bullish:{views['bullish']}, Bearish:{views['bearish']}, Neutral:{views['neutral']})"
        )

        return final_decision

    def get_graha_strength(self, council_result: Dict) -> Dict:
        """Calculate relative strength of each graha's influence"""
        strengths = {}
        for graha, opinion in council_result["opinions"].items():
            strengths[graha] = {
                "strength": opinion.get("strength", 0),
                "view": opinion.get("view", "neutral"),
                "confidence": opinion.get("confidence", 0),
            }
        return strengths


# ============================================================================
# FACTORY
# ============================================================================


class NavaGrahaFactory:
    """Factory for creating the full 9-graha system"""

    @staticmethod
    def create_council() -> NavaGrahaCouncil:
        """Create full council of 9 Navagrahas"""
        return NavaGrahaCouncil()

    @staticmethod
    def create_single_graha(graha_name: str) -> NavagrahaAgent:
        """Create individual graha agent"""
        grahas = {
            "surya": SuryaAgent,
            "chandra": ChandraAgent,
            "mangala": MangalaAgent,
            "budha": BudhaAgent,
            "guru": GuruAgent,
            "shukra": ShukraAgent,
            "shani": ShaniAgent,
            "rahu": RahuAgent,
            "ketu": KetuAgent,
        }
        agent_class = grahas.get(graha_name.lower())
        if agent_class:
            return agent_class()
        raise ValueError(f"Unknown graha: {graha_name}")


if __name__ == "__main__":
    # Test the full council
    async def test():
        council = NavaGrahaFactory.create_council()

        test_data = {
            "price": 50000,
            "sma_20": 48000,
            "sma_50": 45000,
            "rsi": 65,
            "volatility": 25,
            "volume": 1000000,
            "trend": "UP",
        }

        portfolio = {"cash": 100000, "positions": {}}

        result = await council.convene("BTC-EUR", test_data, portfolio)
        print(f"\nCouncil Consensus: {result['consensus']}")
        print(f"Votes: {result['vote_count']}")
        print("\nAll 9 Graha Opinions:")
        for graha, opinion in result["opinions"].items():
            view = opinion.get("view", "neutral")
            conf = opinion.get("confidence", 0)
            print(f"  {graha:10s}: {view:10s} (conf: {conf:.2f})")

    asyncio.run(test())
