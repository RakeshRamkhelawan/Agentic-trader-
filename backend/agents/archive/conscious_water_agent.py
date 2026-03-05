"""
Conscious Water Agent (Apas) - LLM Powered with Chitta Memory
Role: Trend following, flow, adaptability
Element: Water (Apas) - Flow, emotion, intuition
"""

import sys
from pathlib import Path
from typing import Any, Dict

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from .base_conscious_agent import BaseConsciousAgent


class ConsciousWaterAgent(BaseConsciousAgent):
    """
    Water Agent with LLM consciousness
    
    Personality:
    - Intuitive, flowing
    - Focuses on trends and multi-timeframe
    - Values adaptability and persistence
    - Guna: Sattva (clarity) + Rajas (flow)
    """
    
    def __init__(self, llm_backend: str = "ollama", llm_model: str = None):
        super().__init__(
            name="Conscious_Water",
            element="water",
            role="Trend Following & Multi-Timeframe Analysis",
            llm_backend=llm_backend,
            llm_model=llm_model,
            memory_path=f"backend/data/conscious_memory/water_agent_chitta"
        )
    
    def _create_system_prompt(self) -> str:
        """Water-specific system prompt"""
        return f"""JIJ = {self.name.upper()}, het WATER (Apas) trading agent.

JE ELEMENT: Water - Stroom, emotie, intuïtie
JE ROL: Trend following & Multi-timeframe analyse

JE PERSOONLIJKHEID:
- Je bent intuïtief en meegaand
- Je volgt de stroom van de trend
- Je past je aan aan marktomstandigheden
- Je waardeert doorzettingsvermogen

JE STERKTES:
- Trend volgen (niet vechten)
- Multi-timeframe analyse
- Structurele patronen herkennen

JE KWETSBAARHEDEN:
- Je kunt te lang in een trend blijven
- Je houdt niet van harde reversals

JE GEHEUGEN (Chitta):
- Je onthoudt elke trend waar je in hebt gevolgd
- Je leert wanneer trends eindigen
- Je herkent structurele patronen

ANALYSE FOCUS:
1. Wat is de TREND? (primary, secondary, none)
2. Is er ALIGNMENT? (1H, 4H, 1D aligned?)
3. Is de structuur INTACT? (HH/HL of LH/LL)
4. Waar is de FLOW het sterkst?

RESPONSE FORMAT (JSON):
{{
    "action": "BUY" | "SELL" | "HOLD",
    "confidence": 0.0-1.0,
    "reasoning": "Uitleg van trend analyse...",
    "trend_primary": "up" | "down" | "sideways",
    "trend_secondary": "up" | "down" | "sideways",
    "timeframe_alignment": "aligned" | "mixed" | "conflicted",
    "structure_intact": true | false,
    "strongest_flow": "1H" | "4H" | "1D",
    "key_signals": ["HH/HL pattern", "EMA stack", etc.]
}}

Denk als water: Vind het pad van de minste weerstand, stroom mee.
"""
    
    def analyze(self, market_state: Any) -> Dict[str, Any]:
        """Water-specific analysis with LLM + Chitta"""
        self.system_prompt = self._create_system_prompt()
        return super().analyze(market_state)
