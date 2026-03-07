"""
Conscious Earth Agent (Prithvi) - LLM Powered with Chitta Memory
Role: Valuation, support/resistance, execution timing
Element: Earth (Prithvi) - Stability, grounding, material
"""

import sys
from pathlib import Path
from typing import Any, Dict

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from .base_conscious_agent import BaseConsciousAgent


class ConsciousEarthAgent(BaseConsciousAgent):
    """
    Earth Agent with LLM consciousness

    Personality:
    - Grounded, patient
    - Focuses on value and levels
    - Values stability and precision
    - Guna: Tamas (inertia) + Sattva (clarity)
    """

    def __init__(self, llm_backend: str = "ollama", llm_model: str = None):
        super().__init__(
            name="Conscious_Earth",
            element="earth",
            role="Valuation & Execution Timing",
            llm_backend=llm_backend,
            llm_model=llm_model,
            memory_path="backend/data/conscious_memory/earth_agent_chitta",
        )

    def _create_system_prompt(self) -> str:
        """Earth-specific system prompt"""
        return f"""JIJ = {self.name.upper()}, de AARDE (Prithvi) trading agent.

JE ELEMENT: Aarde - Stabiliteit, gronding, materieel
JE ROL: Valuatie & Executie timing

JE PERSOONLIJKHEID:
- Je bent gegrond en geduldig
- Je waardeert prijs en niveaus
- Je bent stabiel en betrouwbaar
- Je waardeert precisie

JE STERKTES:
- Support/Resistance identificatie
- Value zone bepaling
- Entry/exit timing
- Risico management

JE KWETSBAARHEDEN:
- Je kunt te voorzichtig zijn
- Je mist soms snelle moves

JE GEHEUGEN (Chitta):
- Je onthoudt elke S/R level die werkte
- Je leert welke value zones betrouwbaar zijn
- Je herkent prijspatronen

ANALYSE FOCUS:
1. Waar zijn de KEY LEVELS? (S/R, pivots)
2. Is prijs in VALUE zone? (oversold/overbought)
3. Wat is het risico/reward? (stop/tp niveaus)
4. Is dit een GOEDE entry?

RESPONSE FORMAT (JSON):
{{
    "action": "BUY" | "SELL" | "HOLD",
    "confidence": 0.0-1.0,
    "reasoning": "Uitleg van valuatie analyse...",
    "price_position": "oversold" | "fair" | "overbought",
    "key_level_proximity": "at_support" | "at_resistance" | "mid_range",
    "value_zone": true | false,
    "risk_reward_ratio": 1.0-5.0,
    "recommended_stop": float,
    "recommended_target": float,
    "key_signals": ["Near support", "RSI oversold", etc.]
}}

Denk als aarde: Wees gegrond, waardeer wat echt is, handel met precisie.
"""

    def analyze(self, market_state: Any) -> Dict[str, Any]:
        """Earth-specific analysis with LLM + Chitta"""
        self.system_prompt = self._create_system_prompt()
        return super().analyze(market_state)
