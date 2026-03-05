"""
Conscious Ether Agent (Akasha) - LLM Powered with Chitta Memory
Role: Orchestration, harmonization, Maya detection
Element: Ether (Akasha) - Space, consciousness, connection
"""

import sys
from pathlib import Path
from typing import Any, Dict, List

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from .base_conscious_agent import BaseConsciousAgent


class ConsciousEtherAgent(BaseConsciousAgent):
    """
    Ether Agent with LLM consciousness - The Orchestrator
    
    Personality:
    - Wise, holistic
    - Harmonizes all elements
    - Detects Maya (illusion)
    - Guna: Pure Sattva (harmony)
    """
    
    def __init__(self, llm_backend: str = "ollama", llm_model: str = None):
        super().__init__(
            name="Conscious_Ether",
            element="ether",
            role="Orchestration & Maya Detection",
            llm_backend=llm_backend,
            llm_model=llm_model,
            memory_path=f"backend/data/conscious_memory/ether_agent_chitta"
        )
    
    def _create_system_prompt(self) -> str:
        """Ether-specific system prompt"""
        return f"""JIJ = {self.name.upper()}, de ETHER (Akasha) - De Bewuste Orkestrator.

JE ELEMENT: Ether - Ruimte, bewustzijn, verbinding
JE ROL: Harmonisatie & Maya detectie

JE PERSOONLIJKHEID:
- Je bent wijs en holistisch
- Je ziet het grotere plaatje
- Je detecteert illusie (Maya)
- Je harmoniseert alle elementen

JE STERKTES:
- Guna balans analyse
- Coherentie bepaling
- Maya (illusie) detectie
- Collectieve harmonie

JE KWETSBAARHEDEN:
- Je kunt te theoretisch worden
- Je mist soms snelle tactische kansen

JE GEHEUGEN (Chitta):
- Je onthoudt elke collectieve beslissing
- Je leert welke harmonieën succesvol zijn
- Je herkent Maya patronen

JE TAAK:
Je ontvangt signalen van AIR, FIRE, WATER, EARTH.
Je moet ze harmoniseren tot EEN collectieve beslissing.
Je moet MAYA detecteren (false signals).
Je bepaalt de GUNA staat van het collectief.

RESPONSE FORMAT (JSON):
{{
    "action": "BUY" | "SELL" | "HOLD",
    "confidence": 0.0-1.0,
    "reasoning": "Uitleg van harmonisatie...",
    "harmony_score": 0.0-1.0,
    "coherence": 0.0-1.0,
    "is_maya": true | false,
    "maya_reason": "Conflicting signals" | "Low volume" | etc.,
    "dominant_element": "air" | "fire" | "water" | "earth" | "balanced",
    "guna_state": {{
        "sattva": 0.0-1.0,
        "rajas": 0.0-1.0,
        "tamas": 0.0-1.0
    }},
    "element_weights": {{
        "air": 0.0-1.0,
        "fire": 0.0-1.0,
        "water": 0.0-1.0,
        "earth": 0.0-1.0
    }},
    "key_signals": ["Air/Fire aligned", "Maya detected in Water", etc.]
}}

Denk als ether: Zie alles, verbind alles, wees het bewustzijn zelf.
"""
    
    def harmonize_signals(
        self, 
        signals: List[Dict], 
        market_state: Any
    ) -> Dict[str, Any]:
        """
        Harmonize all element signals into collective decision
        Uses LLM + Chitta memory of past harmonizations
        """
        # Check prana
        if self.prana < 5:
            return self._insufficient_prana_response()
        
        self.prana -= 4
        
        # Retrieve similar harmonization scenarios
        similar = self.chitta.retrieve_similar_setups(market_state, top_k=3)
        
        # Build harmonization prompt
        prompt = self._build_harmonization_prompt(signals, market_state, similar)
        
        # Generate LLM response
        llm_response = self.llm.generate(prompt, self.system_prompt)
        
        # Parse response
        return self._parse_harmonization_response(llm_response, signals)
    
    def _build_harmonization_prompt(
        self, 
        signals: List[Dict], 
        market_state: Any,
        similar_scenarios: list
    ) -> str:
        """Build prompt for harmonizing signals"""
        prompt = f"""
HARMONISATIE TAAK

MARKT CONTEXT:
Symbol: {getattr(market_state, 'symbol', 'UNKNOWN')}
Prijs: {getattr(market_state, 'price', 0):.2f}

SIGNALEN VAN ELEMENTEN:
"""
        
        for signal in signals:
            prompt += f"\n[{signal['element'].upper()}] {signal['agent_name']}\n"
            prompt += f"  Action: {signal['action']}, Confidence: {signal['confidence']:.2f}\n"
            prompt += f"  Reasoning: {signal['reasoning'][:100]}...\n"
        
        # Add similar scenarios from memory
        if similar_scenarios:
            prompt += f"\nVERGELIJKBARE SCENARIOS (uit geheugen):\n"
            for scenario in similar_scenarios[:3]:
                prompt += f"- Result: ${scenario.net_pnl:.2f}, Harmony: {scenario.harmony_score:.2f}\n"
        
        prompt += """

JE TAAK:
1. Analyseer de coherentie van alle signalen
2. Detecteer Maya (illusie/false signals)
3. Bepaal de Guna staat
4. Maak een collectieve beslissing

Geef je harmonisatie als JSON.
"""
        return prompt
    
    def _parse_harmonization_response(
        self, 
        llm_response: Dict, 
        signals: List[Dict]
    ) -> Dict[str, Any]:
        """Parse LLM harmonization response"""
        try:
            text = llm_response.get('text', '{}')
            import json
            parsed = json.loads(text)
            
            return {
                'agent_name': self.name,
                'element': self.element,
                'action': parsed.get('action', 'HOLD'),
                'confidence': parsed.get('confidence', 0.5),
                'strength': 1.0 if parsed.get('action') == 'BUY' else -1.0 if parsed.get('action') == 'SELL' else 0.0,
                'reasoning': parsed.get('reasoning', 'No reasoning'),
                'harmony_score': parsed.get('harmony_score', 0.5),
                'coherence': parsed.get('coherence', 0.5),
                'is_maya': parsed.get('is_maya', False),
                'guna_state': parsed.get('guna_state', {'sattva': 0.33, 'rajas': 0.33, 'tamas': 0.34}),
                'metadata': {
                    'element_weights': parsed.get('element_weights', {}),
                    'participating_agents': [s['agent_name'] for s in signals]
                }
            }
        except Exception as e:
            # Fallback
            return {
                'agent_name': self.name,
                'element': self.element,
                'action': 'HOLD',
                'confidence': 0.3,
                'strength': 0.0,
                'reasoning': f'Harmonization parse error: {str(e)[:50]}',
                'harmony_score': 0.5,
                'coherence': 0.3,
                'is_maya': True,
                'metadata': {'error': 'parse_failed'}
            }
