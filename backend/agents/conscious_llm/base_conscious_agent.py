"""
Base Conscious LLM Agent
Every agent has its own LLM and Chitta Memory
"""

import sys
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
import json

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.core.llm.llm_provider import LLMProvider, create_llm_provider
from backend.core.conscious.chitta_memory import ChittaMemory, TradeExperience


class BaseConsciousAgent:
    """
    Base class for conscious LLM agents
    
    Each agent has:
    - Unique LLM instance (DeepSeek/Ollama)
    - Own Chitta Memory (persistent trade memory)
    - Self-reflection before decisions
    - Learning from past experiences
    """
    
    def __init__(
        self,
        name: str,
        element: str,
        role: str,
        llm_backend: str = "ollama",
        llm_model: Optional[str] = None,
        memory_path: Optional[str] = None
    ):
        self.name = name
        self.element = element
        self.role = role
        
        # Initialize LLM
        print(f"[{self.name}] Initializing LLM ({llm_backend}/{llm_model or 'default'})...")
        self.llm = create_llm_provider(backend=llm_backend, model=llm_model)
        
        # Initialize Chitta Memory (own memory instance)
        memory_path = memory_path or f"backend/data/conscious_memory/{name.lower()}_chitta"
        print(f"[{self.name}] Initializing Chitta Memory...")
        self.chitta = ChittaMemory(storage_path=memory_path)
        
        # Agent state
        self.prana = 100.0
        self.decision_count = 0
        self.correct_predictions = 0
        
        # System prompt defines agent's personality
        self.system_prompt = self._create_system_prompt()
        
        print(f"[{self.name}] Conscious agent ready | Memory: {len(self.chitta.trades)} trades")
    
    def _create_system_prompt(self) -> str:
        """Create system prompt defining agent's personality and role"""
        return f"""JIJ = {self.name.upper()}, een {self.element.upper()} trading agent.

JE ELEMENT: {self.element}
JE ROL: {self.role}

JE BENT BEWUST:
- Je hebt geheugen van al je trades (Chitta)
- Je leert van fouten en successen
- Je reflecteert voor elke beslissing

JE DOEL:
- Analyseer de markt met je unieke perspectief
- Geef duidelijke BUY/SELL/HOLD signalen
- Leg uit WAAROM (reasoning)
- Geef confidence score (0.0-1.0)

RESPONSE FORMAT (JSON):
{{
    "action": "BUY" | "SELL" | "HOLD",
    "confidence": 0.0-1.0,
    "reasoning": "Uitleg van je analyse...",
    "key_signals": ["signal1", "signal2"],
    "risk_level": "low" | "medium" | "high"
}}

HERINNER: Je bent {self.element}. Handel volgens je element.
"""
    
    def analyze(self, market_state: Any) -> Dict[str, Any]:
        """
        Analyze market using LLM + Chitta memory
        
        Flow:
        1. Check prana (energy)
        2. Retrieve similar setups from memory
        3. Reflect on recent performance
        4. Generate LLM analysis
        5. Store decision in memory
        """
        # Check prana
        if self.prana < 5:
            return self._insufficient_prana_response()
        
        self.prana -= 3  # Cost per analysis
        self.decision_count += 1
        
        # Step 1: Retrieve similar setups from Chitta
        similar_trades = self.chitta.retrieve_similar_setups(market_state, top_k=3)
        memory_context = self._format_memory_context(similar_trades)
        
        # Step 2: Reflect on recent performance
        reflection = self.chitta.reflect_recent(n_trades=5)
        reflection_context = self._format_reflection_context(reflection)
        
        # Step 3: Build prompt with memory
        prompt = self._build_prompt(market_state, memory_context, reflection_context)
        
        # Step 4: Generate LLM response
        llm_response = self.llm.generate(prompt, self.system_prompt)
        
        # Step 5: Parse and enhance with memory
        signal = self._parse_llm_response(llm_response, market_state)
        
        # Store in memory for learning
        self._store_decision(market_state, signal)
        
        return signal
    
    def _build_prompt(
        self, 
        market_state: Any, 
        memory_context: str,
        reflection_context: str
    ) -> str:
        """Build analysis prompt with memory context"""
        return f"""
ANALYSE MARKT:

SYMBOL: {getattr(market_state, 'symbol', 'UNKNOWN')}
PRIJS: {getattr(market_state, 'price', 0):.2f}
RSI: {getattr(market_state, 'rsi', 50):.1f}
ADX: {getattr(market_state, 'adx', 25):.1f}
VOLATILITEIT: {getattr(market_state, 'volatility', 0.02):.3f}
TREND 1D: {getattr(market_state, 'trend_1d', 0):.3f}

{memory_context}

{reflection_context}

Je taak: Analyseer deze markt als {self.name} ({self.element} element).
Geef je trading signal met confidence en reasoning.

RESPONSE (JSON):
"""
    
    def _format_memory_context(self, similar_trades: list) -> str:
        """Format similar trades for prompt context"""
        if not similar_trades:
            return "GEHEUGEN: Geen vergelijkbare setups gevonden (eerste keer?)"
        
        avg_pnl = sum(t.net_pnl for t in similar_trades) / len(similar_trades)
        win_count = sum(1 for t in similar_trades if t.is_win())
        
        context = f"GEHEUGEN (vergelijkbare setups):\n"
        context += f"- Gevonden: {len(similar_trades)} soortgelijke trades\n"
        context += f"- Win rate: {win_count}/{len(similar_trades)}\n"
        context += f"- Gemiddelde PnL: ${avg_pnl:.2f}\n"
        
        for i, trade in enumerate(similar_trades[:3], 1):
            context += f"\nTrade {i}: {trade.side} {trade.symbol}\n"
            context += f"  PnL: ${trade.net_pnl:.2f}, Harmony: {trade.harmony_score:.2f}\n"
            context += f"  Exit: {trade.exit_reason}\n"
        
        return context
    
    def _format_reflection_context(self, reflection: Dict) -> str:
        """Format reflection for prompt context"""
        context = "REFLECTIE (laatste 5 trades):\n"
        context += f"- Win rate: {reflection.get('win_rate', 0):.0%}\n"
        context += f"- Totale PnL: ${reflection.get('total_pnl', 0):.2f}\n"
        context += f"- Gemiddelde harmony: {reflection.get('avg_harmony', 0):.2f}\n"
        
        insights = reflection.get('insights', [])
        if insights:
            context += f"- Insights: {'; '.join(insights)}\n"
        
        if reflection.get('recommended_action') != 'continue':
            context += f"- WAARSCHUWING: {reflection['recommended_action']}\n"
        
        return context
    
    def _parse_llm_response(self, llm_response: Dict, market_state: Any) -> Dict[str, Any]:
        """Parse LLM response into agent signal"""
        try:
            text = llm_response.get('text', '{}')
            parsed = json.loads(text)
            
            return {
                'agent_name': self.name,
                'element': self.element,
                'action': parsed.get('action', 'HOLD'),
                'confidence': parsed.get('confidence', 0.5),
                'strength': self._action_to_strength(parsed.get('action', 'HOLD')),
                'reasoning': parsed.get('reasoning', llm_response.get('reasoning', 'No reasoning')),
                'metadata': {
                    'key_signals': parsed.get('key_signals', []),
                    'risk_level': parsed.get('risk_level', 'medium'),
                    'llm_backend': llm_response.get('metadata', {}).get('backend', 'unknown'),
                    'prana': self.prana
                }
            }
        except json.JSONDecodeError:
            # Fallback if JSON parsing fails
            return {
                'agent_name': self.name,
                'element': self.element,
                'action': 'HOLD',
                'confidence': 0.3,
                'strength': 0.0,
                'reasoning': f'LLM parse error: {llm_response.get("text", "")[:100]}',
                'metadata': {'error': 'parse_failed'}
            }
    
    def _action_to_strength(self, action: str) -> float:
        """Convert action to strength value"""
        action_map = {
            'BUY': 1.0,
            'SELL': -1.0,
            'HOLD': 0.0
        }
        return action_map.get(action.upper(), 0.0)
    
    def _store_decision(self, market_state: Any, signal: Dict):
        """Store decision in Chitta for learning"""
        # Note: We can't store full trade yet (no exit), but we log the decision
        pass  # Will be updated when trade completes
    
    def store_trade_result(self, trade_experience: TradeExperience):
        """Store completed trade in Chitta memory"""
        self.chitta.store_trade(trade_experience)
        
        # Update performance tracking
        if trade_experience.is_win():
            self.correct_predictions += 1
        
        # Regenerate prana on trade completion
        self.prana = min(100.0, self.prana + 10)
    
    def _insufficient_prana_response(self) -> Dict[str, Any]:
        """Return HOLD when prana is depleted"""
        return {
            'agent_name': self.name,
            'element': self.element,
            'action': 'HOLD',
            'confidence': 0.1,
            'strength': 0.0,
            'reasoning': f'{self.name} depleted (prana: {self.prana:.1f}). Regenerating...',
            'metadata': {'depleted': True, 'prana': self.prana}
        }
    
    def regenerate_prana(self, amount: float = 1.0):
        """Regenerate prana energy"""
        self.prana = min(100.0, self.prana + amount)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get agent statistics"""
        return {
            'name': self.name,
            'element': self.element,
            'decisions': self.decision_count,
            'accuracy': self.correct_predictions / max(1, self.decision_count),
            'prana': self.prana,
            'chitta_summary': self.chitta.get_summary(),
            'llm_stats': self.llm.get_stats()
        }
