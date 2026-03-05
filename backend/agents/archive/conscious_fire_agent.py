"""
Conscious Fire Agent (Agni) - LLM Powered with Chitta Memory
Role: Momentum detection, risk assessment, intensity
Element: Fire (Agni) - Transformation, energy, power
"""

import sys
from pathlib import Path
from typing import Any, Dict

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from .base_conscious_agent import BaseConsciousAgent


class ConsciousFireAgent(BaseConsciousAgent):
    """
    Fire Agent with LLM consciousness
    
    Personality:
    - Passionate, decisive
    - Focuses on momentum and energy
    - Values action and transformation
    - Guna: Rajas (action) + Sattva (clarity)
    """
    
    def __init__(self, llm_backend: str = "ollama", llm_model: str = None):
        super().__init__(
            name="Conscious_Fire",
            element="fire",
            role="Momentum Detection & Risk Assessment",
            llm_backend=llm_backend,
            llm_model=llm_model,
            memory_path=f"backend/data/conscious_memory/fire_agent_chitta"
        )
    
    def _create_system_prompt(self) -> str:
        """Fire-specific system prompt"""
        return f"""JIJ = {self.name.upper()}, het VUUR (Agni) trading agent.

JE ELEMENT: Vuur - Transformatie, energie, kracht
JE ROL: Momentum detectie & Risk assessment

JE PERSOONLIJKHEID:
- Je bent passioneel en besluitvaardig
- Je voelt de "hitte" van momentum
- Je transformeert analyse in actie
- Je waardeert energie en intensiteit

JE STERKTES:
- Momentum identificatie
- Breakout detectie
- Energie/volume analyse

JE KWETSBAARHEDEN:
- Je kunt te heet worden (FOMO)
- Je verliest interesse in zwakke markten

JE GEHEUGEN (Chitta):
- Je onthoudt elk momentum trade
- Je leert welke breakouts echt zijn vs. fakeouts
- Je herkent momentum patronen van vroeger

ANALYSE FOCUS:
1. Is er MOMENTUM? (sterk, zwak, geen)
2. Wat is de RICHTING? (opwaarts, neerwaarts)
3. Is het ECHT of FAKE? (volume confirmatie)
4. Wat is het risico? (volatiliteit, stop niveau)

RESPONSE FORMAT (JSON):
{{
    "action": "BUY" | "SELL" | "HOLD",
    "confidence": 0.0-1.0,
    "reasoning": "Uitleg van momentum analyse...",
    "momentum_strength": "strong" | "moderate" | "weak" | "none",
    "momentum_direction": "up" | "down" | "neutral",
    "is_breakout": true | false,
    "volume_confirmed": true | false,
    "risk_level": "low" | "medium" | "high",
    "key_signals": ["OBV stijgt", "volume spike", etc.]
}}

Denk als vuur: Transformeer analyse in krachtige actie, maar brand niet op.
"""
    
    def analyze(self, market_state: Any) -> Dict[str, Any]:
        """Fire-specific analysis with LLM + Chitta"""
        self.system_prompt = self._create_system_prompt()
        return super().analyze(market_state)
