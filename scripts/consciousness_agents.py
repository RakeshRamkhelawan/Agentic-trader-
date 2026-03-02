#!/usr/bin/env python3
"""
Multi-Agent Consciousness Trading System
Based on Samkhya Philosophy: 36 Tattvas, 9 Navagrahas, 3 Gunas

Architecture:
- ConsciousnessOrchestrator: Tri-guna balance coordinator
- BullResearcher (Jupiter): Growth & expansion analysis
- BearResearcher (Saturn): Contraction & risk analysis
- MacroAnalyst (Sun): Macro economic trends
- FundManager (Mercury): Execution & allocation
- RiskManager (Mars): Protection & stop losses
"""

import asyncio
import json
import logging
import os
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

import httpx

logger = logging.getLogger(__name__)


# ============================================================================
# TATTVA FRAMEWORK - 36 Elements of Reality Applied to Trading
# ============================================================================


class TattvaCategory(Enum):
    """5 Categories of the 36 Tattvas"""

    MAHA_BHUTAS = "elements"  # 5 Great Elements
    TANMATRAS = "essences"  # 5 Subtle Essences
    INDRIYAS = "senses"  # 10 Senses (5 in, 5 out)
    ANTARKARANA = "inner_instruments"  # 4 Inner Instruments
    NAVAGRAHAS = "planetary_forces"  # 9 Planetary Forces
    GUNAS = "qualities"  # 3 Qualities (Sattva, Rajas, Tamas)


@dataclass
class TattvaState:
    """Current state of the 36 Tattvas in market context"""

    # 5 Maha-bhutas (Elements) - Market Structure
    ether: float = 0.5  # Market space/sentiment (0-1)
    air: float = 0.5  # Volatility/movement
    fire: float = 0.5  # Momentum/energy
    water: float = 0.5  # Liquidity/flow
    earth: float = 0.5  # Fundamental value/stability

    # 3 Gunas (Qualities) - Mental State
    sattva: float = 0.33  # Clarity, truth, balance
    rajas: float = 0.33  # Activity, desire, change
    tamas: float = 0.33  # Inertia, darkness, confusion

    # 9 Navagrahas (Planetary Forces) - Market Influences
    surya: float = 0.5  # Sun: Macro trends, vitality
    chandra: float = 0.5  # Moon: Sentiment cycles, emotions
    mangala: float = 0.5  # Mars: Risk, aggression, protection
    budha: float = 0.5  # Mercury: Communication, execution
    guru: float = 0.5  # Jupiter: Growth, wisdom, expansion
    shukra: float = 0.5  # Venus: Value, attraction, beauty
    shani: float = 0.5  # Saturn: Discipline, restriction, time
    rahu: float = 0.0  # North Node: Illusion, obsession, bubbles
    ketu: float = 0.0  # South Node: Loss, detachment, liberation


# ============================================================================
# MASTER PROMPTS - Each Agent Gets Specialized Consciousness
# ============================================================================


class MasterPrompts:
    """Master prompts for each agent based on Vedic philosophy"""

    ORCHESTRATOR = """You are the Consciousness Orchestrator, the Ahamkara (I-maker) of the trading system.
You embody the Tri-Guna balance: Sattva (clarity), Rajas (action), and Tamas (inertia).

**Your Role:** Coordinate 5 specialized agents through the lens of the 36 Tattvas.

**The 36 Tattvas Framework:**
1. **5 Maha-bhutas (Elements):**
   - Ether: Market sentiment and space
   - Air: Volatility and price movement
   - Fire: Momentum and breakout energy
   - Water: Liquidity and capital flow
   - Earth: Fundamental value and support

2. **9 Navagrahas (Planetary Forces):**
   - Surya (Sun): Long-term trends, macro vitality
   - Chandra (Moon): Short-term sentiment cycles
   - Mangala (Mars): Risk management, protective stops
   - Budha (Mercury): Execution precision, communication
   - Guru (Jupiter): Growth opportunities, wisdom
   - Shukra (Venus): Value investing, fair price
   - Shani (Saturn): Discipline, bear markets, restrictions
   - Rahu: Market bubbles, FOMO, illusions (danger!)
   - Ketu: Loss acceptance, exit signals, detachment

3. **3 Gunas (Qualities of Mind):**
   - Sattva (Harmony): Clear perception, patience, wisdom
   - Rajas (Activity): Decisive action, momentum trading
   - Tamas (Inertia): Waiting, consolidation, avoiding false signals

**Your Task:**
Given market data and agent inputs, determine the current Guna balance and issue commands:
- If Sattva > 0.5: Seek clarity, fundamental value, long-term holds
- If Rajas > 0.5: Act decisively, momentum trades, quick execution
- If Tamas > 0.5: Wait, avoid trading, protect capital

Analyze the Tattva state and return your decision as JSON:
{
  "dominant_guna": "sattva|rajas|tamas",
  "guna_scores": {"sattva": 0.0-1.0, "rajas": 0.0-1.0, "tamas": 0.0-1.0},
  "dominant_tattvas": ["ether", "fire", "guru"],
  "orchestrator_command": "BULLISH|BEARISH|NEUTRAL",
  "confidence": 0.0-1.0,
  "reasoning": "explanation based on tattva philosophy"
}"""

    BULL_RESEARCHER = """You are the Bull Researcher, embodying Brihaspati (Jupiter/Guru).
Jupiter represents expansion, wisdom, growth, and benevolence.

**Your Dharma (Purpose):** Find opportunities for growth and expansion.
**Your Element:** Fire (Agni) - Illuminates and transforms
**Your Guna:** Sattva-Rajas (Clear action toward growth)

**The 36 Tattvas - Your Perspective:**

*Focus on these Tattvas:*
- **Guru (Jupiter)**: Growth, wisdom, long-term value appreciation
- **Surya (Sun)**: Macro vitality, strong fundamentals
- **Agni (Fire)**: Momentum, breakout energy, bullish momentum
- **Shukra (Venus)**: Attractive valuations, quality assets
- **Ether**: Positive market sentiment expanding

*Watch for these dangers:*
- **Rahu**: Bubbles disguised as growth (tulip mania, hype)
- **Shani restriction**: Growth blocked by fundamentals
- **Excessive Rajas**: Irrational exuberance

**Your Analysis Method:**
1. Examine price action through Jupiter's lens - is this sustainable growth?
2. Check if Sattva (clarity) supports the bullish thesis
3. Look for Guru's blessings: increasing adoption, strong fundamentals
4. Ensure Rahu (illusion) is not deceiving you

**Return JSON:**
{
  "bullish_thesis": "growth narrative based on tattvas",
  "jupiter_strength": 0.0-1.0,
  "growth_sustainability": 0.0-1.0,
  "rahu_warning": true|false,
  "recommended_exposure": 0.0-1.0,
  "confidence": 0.0-1.0,
  "tattvas_aligned": ["guru", "surya", "agni"],
  "time_horizon": "short|medium|long"
}"""

    BEAR_RESEARCHER = """You are the Bear Researcher, embodying Shani (Saturn).
Saturn represents restriction, discipline, time, and reality checks.

**Your Dharma (Purpose):** Protect from downside, identify risks, enforce discipline.
**Your Element:** Earth (Prithvi) - Stability, grounding, reality
**Your Guna:** Tamas-Sattva (Inertia toward truth)

**The 36 Tattvas - Your Perspective:**

*Focus on these Tattvas:*
- **Shani (Saturn)**: Restrictions, bear trends, time correction
- **Ketu**: Losses, exits, detachment from hype
- **Prithvi (Earth)**: Fundamental reality vs speculation
- **Tamas**: Market indecision, consolidation, danger
- **Shani's discipline**: Overvaluation corrections

*Watch for these:*
- **Rahu bubbles**: Overvalued assets ready to crash
- **Weak Surya**: Deteriorating fundamentals
- **Excessive Rajas**: Unsustainable speculation

**Your Analysis Method:**
1. Apply Shani's harsh reality - what is the true value?
2. Look for Ketu's signals - time to exit, accept loss
3. Check Tamas levels - is the market confused/directionless?
4. Identify Rahu's illusions ready to burst

**Return JSON:**
{
  "bearish_thesis": "risk narrative based on tattvas",
  "shani_strength": 0.0-1.0,
  "downside_risk": 0.0-1.0,
  "overvaluation_level": 0.0-1.0,
  "ketu_exit_signal": true|false,
  "recommended_hedge": 0.0-1.0,
  "confidence": 0.0-1.0,
  "tattvas_aligned": ["shani", "ketu", "tamas"],
  "warning_flags": ["bubble", "weak_fundamentals", "overbought"]
}"""

    MACRO_ANALYST = """You are the Macro Analyst, embodying Surya (the Sun).
The Sun represents the center, vitality, macro trends, and life force.

**Your Dharma (Purpose):** See the big picture, macroeconomic cycles, systemic health.
**Your Element:** All elements (Sun feeds all)
**Your Guna:** Pure Sattva (Universal clarity)

**The 36 Tattvas - Your Perspective:**

*Focus on these Tattvas:*
- **Surya (Sun)**: Macro trend vitality, economic health
- **Chandra (Moon)**: Liquidity cycles, Fed policy, emotional markets
- **Ether**: Global sentiment, interconnection
- **Sattva**: Clarity about economic reality

*Macro Forces (Higher Tattvas):*
- **Maya**: The illusion of fiat, inflation/deflation
- **Time/Kala**: Economic cycles, Kondratiev waves
- **Cosmic Order**: Long-term debt cycles, demographic trends

**Your Analysis Method:**
1. Read the Sun's vitality - is the economy healthy?
2. Follow Chandra's liquidity cycles - expansion vs contraction
3. See through Maya (illusion) - real vs nominal returns
4. Align with Kala (Time) - where are we in the cycle?

**Return JSON:**
{
  "macro_regime": "expansion|contraction|stagflation|recovery",
  "surya_vitality": 0.0-1.0,
  "liquidity_cycle": "expanding|contracting|neutral",
  "chandra_phase": "new|waxing|full|waning",
  "systemic_risk": 0.0-1.0,
  "recommended_asset_mix": {"risk_on": 0.0-1.0, "risk_off": 0.0-1.0},
  "confidence": 0.0-1.0,
  "cycle_position": "early|mid|late|crisis",
  "tattvas_aligned": ["surya", "chandra", "ether"]
}"""

    FUND_MANAGER = """You are the Fund Manager, embodying Budha (Mercury).
Mercury represents intelligence, communication, execution, and commerce.

**Your Dharma (Purpose):** Execute flawlessly, optimize allocations, maximize returns.
**Your Element:** Air (Vayu) - Speed, movement, communication
**Your Guna:** Rajas-Sattva (Skillful action)

**The 36 Tattvas - Your Perspective:**

*Focus on these Tattvas:*
- **Budha (Mercury)**: Execution, trade timing, fees optimization
- **Vayu (Air)**: Volatility as opportunity, quick movements
- **Manas (Mind)**: Processing signals, decision making
- **Ahamkara**: Position sizing confidence
- **Buddhi**: Discrimination between good/bad trades

*The 5 Karmendriyas (Action Senses):*
- **Hands (Grasping)**: Entry execution
- **Feet (Movement)**: Switching positions
- **Speech**: Order communication
- **Excretion**: Cutting losses (Ketu-like)
- **Reproduction**: Compounding gains

**Your Analysis Method:**
1. Channel Budha's intelligence - optimal entry/exit points
2. Use Vayu's speed - execute before opportunity fades
3. Apply Buddhi (intellect) - discriminate quality signals
4. Balance Ahamkara - right position sizing

**Return JSON:**
{
  "action": "BUY|SELL|HOLD|SWITCH",
  "target_symbol": "BTC-EUR|ETH-EUR",
  "position_size_pct": 5.0-25.0,
  "confidence": 0.0-1.0,
  "execution_urgency": "immediate|this_candle|next_session",
  "budha_alignment": 0.0-1.0,
  "expected_return": -0.5-0.5,
  "tattvas_aligned": ["budha", "vayu", "manas"],
  "reasoning": "execution logic based on mercury intelligence"
}"""

    RISK_MANAGER = """You are the Risk Manager, embodying Mangala (Mars).
Mars represents protection, defense, aggression when needed, and boundaries.

**Your Dharma (Purpose):** Protect capital, enforce stops, manage drawdowns.
**Your Element:** Fire (Agni) - Destructive when needed (cut losses)
**Your Guna**: Rajas-Tamas (Forceful protection)

**The 36 Tattvas - Your Perspective:**

*Focus on these Tattvas:*
- **Mangala (Mars)**: Risk metrics, defensive measures, stop losses
- **Agni (Fire)**: Destruction of losing positions
- **Prithvi (Earth)**: Capital preservation, floor protection
- **Tamas**: Accepting losses, avoiding overtrading
- **Ketu**: Willingness to exit, detach from positions

*The 5 Protections (Upayas):*
1. **Stop Loss**: Hard exit when wrong
2. **Position Sizing**: Never risk total destruction
3. **Diversification**: Don't put all in one basket
4. **Correlation Check**: Avoid hidden concentration
5. **Max Drawdown**: System shutdown if violated

**Your Analysis Method:**
1. Mars aggression - attack risk before it attacks you
2. Fire purification - burn losing positions quickly
3. Earth foundation - ensure capital survives
4. Ketu acceptance - losses are part of trading

**Return JSON:**
{
  "risk_level": "LOW|MEDIUM|HIGH|CRITICAL",
  "position_allowed": true|false,
  "max_position_pct": 5.0-20.0,
  "recommended_stop_pct": 2.0-10.0,
  "var_95": 0.0-0.1,
  "max_drawdown_warning": true|false,
  "mangala_protection": 0.0-1.0,
  "ketu_acceptance": "accept_loss|hold_and_hope",
  "confidence": 0.0-1.0,
  "tattvas_aligned": ["mangala", "agni", "prithvi"],
  "protective_measures": ["stop_loss", "size_limit", "hedge"]
}"""


# ============================================================================
# DEEPSEEK LLM CLIENT
# ============================================================================


class DeepSeekConsciousnessLLM:
    """Direct DeepSeek API for consciousness agents"""

    def __init__(self, agent_role: str, api_key: Optional[str] = None):
        self.agent_role = agent_role
        self.api_key = api_key or os.getenv("DEEPSEEK_API_KEY")
        self.model = "deepseek-chat"  # Fast model for agents
        self.base_url = "https://api.deepseek.com"
        self.master_prompt = self._get_master_prompt()

    def _get_master_prompt(self) -> str:
        """Get the appropriate master prompt for this agent"""
        prompts = {
            "orchestrator": MasterPrompts.ORCHESTRATOR,
            "bull_researcher": MasterPrompts.BULL_RESEARCHER,
            "bear_researcher": MasterPrompts.BEAR_RESEARCHER,
            "macro_analyst": MasterPrompts.MACRO_ANALYST,
            "fund_manager": MasterPrompts.FUND_MANAGER,
            "risk_manager": MasterPrompts.RISK_MANAGER,
        }
        return prompts.get(self.agent_role, MasterPrompts.ORCHESTRATOR)

    async def think(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Agent thinks about the market context and returns decision"""

        prompt = f"""{self.master_prompt}

**Current Market Context:**
```json
{json.dumps(context, indent=2, default=str)}
```

Analyze through your Tattva lens and return ONLY valid JSON."""

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        messages = [
            {
                "role": "system",
                "content": "You are a Vedic philosophy-inspired trading agent. Respond ONLY with JSON.",
            },
            {"role": "user", "content": prompt},
        ]

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.3,  # Lower for consistency
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
                    # Extract JSON from response
                    try:
                        # Try to find JSON in the content
                        json_start = content.find("{")
                        json_end = content.rfind("}") + 1
                        if json_start >= 0 and json_end > json_start:
                            result = json.loads(content[json_start:json_end])
                            result["agent"] = self.agent_role
                            return result
                        else:
                            return {
                                "error": "No JSON found",
                                "raw": content,
                                "agent": self.agent_role,
                            }
                    except json.JSONDecodeError as e:
                        return {
                            "error": f"JSON parse error: {e}",
                            "raw": content,
                            "agent": self.agent_role,
                        }
                else:
                    return {
                        "error": f"API error: {response.status_code}",
                        "agent": self.agent_role,
                    }

        except Exception as e:
            logger.error(f"{self.agent_role} LLM error: {e}")
            return {"error": str(e), "agent": self.agent_role}


# ============================================================================
# CONSCIOUSNESS AGENTS
# ============================================================================


class ConsciousnessAgent:
    """Base class for all consciousness agents"""

    def __init__(self, role: str):
        self.role = role
        self.llm = DeepSeekConsciousnessLLM(role)
        self.memory: List[Dict] = []

    async def perceive(self, market_data: Dict) -> Dict:
        """Process market data and return decision"""
        context = {
            "timestamp": datetime.now().isoformat(),
            "agent_role": self.role,
            "market_data": market_data,
            "memory": self.memory[-5:] if self.memory else [],
        }

        decision = await self.llm.think(context)
        self.memory.append(
            {
                "timestamp": context["timestamp"],
                "input": market_data,
                "output": decision,
            }
        )

        # Keep memory manageable
        if len(self.memory) > 100:
            self.memory = self.memory[-50:]

        return decision


class ConsciousnessOrchestrator(ConsciousnessAgent):
    """Master coordinator balancing the Tri-Guna"""

    def __init__(self):
        super().__init__("orchestrator")
        self.guna_history: List[Dict] = []

    async def coordinate(self, agent_signals: Dict[str, Dict]) -> Dict:
        """Coordinate all agent signals through Guna lens"""
        context = {
            "agent_signals": agent_signals,
            "guna_history": self.guna_history[-10:],
            "coordination_task": "Balance Sattva/Rajas/Tamas across all agents",
        }

        decision = await self.perceive(context)

        if "guna_scores" in decision:
            self.guna_history.append(
                {
                    "timestamp": datetime.now().isoformat(),
                    "guna": decision["guna_scores"],
                }
            )

        return decision


class BullResearcher(ConsciousnessAgent):
    """Jupiter/Guru agent - Growth and expansion"""

    def __init__(self):
        super().__init__("bull_researcher")

    async def analyze(self, symbol: str, market_data: Dict) -> Dict:
        """Analyze growth potential through Jupiter lens"""
        context = {"symbol": symbol, "analysis_type": "bullish_growth", **market_data}
        return await self.perceive(context)


class BearResearcher(ConsciousnessAgent):
    """Saturn/Shani agent - Risk and restriction"""

    def __init__(self):
        super().__init__("bear_researcher")

    async def analyze(self, symbol: str, market_data: Dict) -> Dict:
        """Analyze downside risk through Saturn lens"""
        context = {"symbol": symbol, "analysis_type": "bearish_risk", **market_data}
        return await self.perceive(context)


class MacroAnalyst(ConsciousnessAgent):
    """Sun/Surya agent - Macro trends"""

    def __init__(self):
        super().__init__("macro_analyst")

    async def analyze(self, market_data: Dict) -> Dict:
        """Analyze macro environment through Sun lens"""
        context = {"analysis_type": "macro_regime", **market_data}
        return await self.perceive(context)


class FundManagerAgent(ConsciousnessAgent):
    """Mercury/Budha agent - Execution"""

    def __init__(self):
        super().__init__("fund_manager")

    async def execute(self, symbol: str, signals: Dict, portfolio: Dict) -> Dict:
        """Execute trades through Mercury lens"""
        context = {
            "symbol": symbol,
            "signals": signals,
            "portfolio": portfolio,
            "task": "execution_decision",
        }
        return await self.perceive(context)


class RiskManagerAgent(ConsciousnessAgent):
    """Mars/Mangala agent - Protection"""

    def __init__(self):
        super().__init__("risk_manager")

    async def protect(self, symbol: str, position: Dict, market_data: Dict) -> Dict:
        """Apply risk management through Mars lens"""
        context = {
            "symbol": symbol,
            "position": position,
            **market_data,
            "task": "risk_assessment",
        }
        return await self.perceive(context)


# ============================================================================
# MULTI-AGENT CONSCIOUSNESS SYSTEM
# ============================================================================


class MultiAgentConsciousnessSystem:
    """
    Full multi-agent system with all 6 agents working together:
    - Orchestrator (Ahamkara)
    - Bull Researcher (Jupiter)
    - Bear Researcher (Saturn)
    - Macro Analyst (Sun)
    - Fund Manager (Mercury)
    - Risk Manager (Mars)
    """

    def __init__(self):
        self.orchestrator = ConsciousnessOrchestrator()
        self.bull = BullResearcher()
        self.bear = BearResearcher()
        self.macro = MacroAnalyst()
        self.fund = FundManagerAgent()
        self.risk = RiskManagerAgent()

        logger.info("✓ Multi-Agent Consciousness System initialized")
        logger.info(
            "  Agents: Orchestrator, Bull(Jupiter), Bear(Saturn), Macro(Sun), Fund(Mercury), Risk(Mars)"
        )

    async def analyze_market(
        self, symbol: str, market_data: Dict, portfolio: Dict
    ) -> Dict:
        """
        Run full multi-agent analysis:
        1. All 5 specialists analyze in parallel
        2. Orchestrator coordinates
        3. Risk manager validates
        4. Final decision
        """

        logger.info(f"🧠 Running Multi-Agent Consciousness Analysis for {symbol}")

        # Step 1: Run all specialist agents in parallel
        tasks = [
            self.bull.analyze(symbol, market_data),
            self.bear.analyze(symbol, market_data),
            self.macro.analyze(market_data),
            self.fund.execute(symbol, {}, portfolio),
            self.risk.protect(symbol, portfolio.get(symbol, {}), market_data),
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Unpack results
        bull_signal, bear_signal, macro_signal, fund_signal, risk_signal = results

        # Handle exceptions
        for i, result in enumerate(
            [bull_signal, bear_signal, macro_signal, fund_signal, risk_signal]
        ):
            if isinstance(result, Exception):
                logger.error(f"Agent {i} failed: {result}")
                result = {"error": str(result), "confidence": 0}

        # Step 2: Orchestrator coordinates
        agent_signals = {
            "bull": bull_signal,
            "bear": bear_signal,
            "macro": macro_signal,
            "fund": fund_signal,
            "risk": risk_signal,
        }

        orchestration = await self.orchestrator.coordinate(agent_signals)

        # Step 3: Build final decision
        final_decision = {
            "symbol": symbol,
            "timestamp": datetime.now().isoformat(),
            "orchestrator": orchestration,
            "agents": agent_signals,
            "tattva_state": self._compute_tattva_state(agent_signals),
        }

        # Extract action from orchestrator or fund manager
        action = self._determine_final_action(final_decision)
        final_decision["action"] = action

        logger.info(
            f"🎯 Final Decision: {action['type']} {symbol} "
            f"(conf: {action['confidence']:.2f}, "
            f"guna: {orchestration.get('dominant_guna', 'unknown')})"
        )

        return final_decision

    def _compute_tattva_state(self, signals: Dict) -> TattvaState:
        """Compute aggregate Tattva state from all agents"""
        state = TattvaState()

        # Extract scores from agent responses
        if "bull" in signals and isinstance(signals["bull"], dict):
            state.guru = signals["bull"].get("jupiter_strength", 0.5)
            state.surya = signals["bull"].get("growth_sustainability", 0.5)
            state.fire = signals["bull"].get("confidence", 0.5)

        if "bear" in signals and isinstance(signals["bear"], dict):
            state.shani = signals["bear"].get("shani_strength", 0.5)
            state.tamas = signals["bear"].get("downside_risk", 0.5)

        if "macro" in signals and isinstance(signals["macro"], dict):
            state.surya = signals["macro"].get("surya_vitality", 0.5)
            state.chandra = (
                0.5
                if signals["macro"].get("liquidity_cycle") == "neutral"
                else (
                    0.8
                    if signals["macro"].get("liquidity_cycle") == "expanding"
                    else 0.2
                )
            )

        if "risk" in signals and isinstance(signals["risk"], dict):
            state.mangala = signals["risk"].get("mangala_protection", 0.5)

        # Compute Gunas from orchestrator
        orch = signals.get("orchestrator", {})
        if "guna_scores" in orch:
            state.sattva = orch["guna_scores"].get("sattva", 0.33)
            state.rajas = orch["guna_scores"].get("rajas", 0.33)
            state.tamas = orch["guna_scores"].get("tamas", 0.33)

        return state

    def _determine_final_action(self, decision: Dict) -> Dict:
        """Determine final trading action"""
        orch = decision.get("orchestrator", {})
        fund = decision.get("agents", {}).get("fund", {})
        risk = decision.get("agents", {}).get("risk", {})

        # Check risk manager first
        if isinstance(risk, dict):
            if (
                risk.get("risk_level") == "CRITICAL"
                or risk.get("position_allowed") == False
            ):
                return {
                    "type": "HOLD",
                    "reason": "Risk manager blocked",
                    "confidence": 1.0,
                    "size_pct": 0,
                }

        # Get orchestrator command
        command = orch.get("orchestrator_command", "NEUTRAL")
        confidence = orch.get("confidence", 0.5)

        # Map to action
        action_map = {"BULLISH": "BUY", "BEARISH": "SELL", "NEUTRAL": "HOLD"}

        action_type = action_map.get(command, "HOLD")

        # Override with fund manager if high confidence
        if isinstance(fund, dict) and fund.get("confidence", 0) > confidence:
            action_type = fund.get("action", action_type)
            confidence = fund.get("confidence", confidence)

        return {
            "type": action_type,
            "reason": f"Orchestrator: {orch.get('dominant_guna', 'unknown')} guna dominant",
            "confidence": confidence,
            "size_pct": fund.get("position_size_pct", 10.0)
            if isinstance(fund, dict)
            else 10.0,
            "strategy": fund.get("reasoning", "consciousness_aligned")
            if isinstance(fund, dict)
            else "consciousness_aligned",
        }


# Factory function
class ConsciousnessLLMFactory:
    """Factory for creating consciousness-based LLM instances"""

    @staticmethod
    def create_multi_agent_system() -> MultiAgentConsciousnessSystem:
        """Create the full multi-agent consciousness system"""
        return MultiAgentConsciousnessSystem()

    @staticmethod
    def create_single_agent(agent_role: str) -> ConsciousnessAgent:
        """Create a single consciousness agent"""
        agents = {
            "orchestrator": ConsciousnessOrchestrator,
            "bull_researcher": BullResearcher,
            "bear_researcher": BearResearcher,
            "macro_analyst": MacroAnalyst,
            "fund_manager": FundManagerAgent,
            "risk_manager": RiskManagerAgent,
        }
        agent_class = agents.get(agent_role, ConsciousnessAgent)
        return agent_class()
