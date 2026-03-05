"""
StrategicEtherAgent - MCTS-enhanced v8 Ether Agent
Integrates 10-step lookahead with symbiotic deliberation
"""

import sys
from pathlib import Path
from typing import List, Dict, Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# v8 imports
from backend.scripts.run_v8_symbiotic_backtest import (
    EtherAgent, AgentSignal, CollectiveDecision, MarketState,
    ActionType, ElementType, GunaVector
)

# v9 MCTS
from backend.core.mcts.planner_v2 import MCTSPlanner


class StrategicEtherAgent(EtherAgent):
    """
    Ether Agent enhanced with MCTS strategic planning
    
    Maintains full v8 compatibility while adding:
    - 10-step lookahead via MCTS
    - Strategic path selection
    - Enhanced confidence calibration
    """
    
    def __init__(self, mcts_iterations: int = 1000):
        super().__init__()
        self.name = "Strategic_Ether"
        self.mcts = MCTSPlanner(
            iterations=mcts_iterations,
            lookahead=10,
            exploration_constant=1.414
        )
        self.strategic_stats = {
            'mcts_runs': 0,
            'v8_override': 0,
            'mcts_override': 0,
            'agreements': 0
        }
    
    def harmonize_signals(self, signals: List[AgentSignal], market: MarketState) -> CollectiveDecision:
        """
        Enhanced harmonization with MCTS strategic layer
        
        Flow:
        1. Run v8 consensus (existing logic)
        2. Run MCTS strategic planning
        3. Combine with confidence weighting
        4. Return strategic decision
        """
        # Step 1: v8 baseline consensus
        v8_decision = super().harmonize_signals(signals, market)
        
        # Step 2: MCTS strategic planning
        mcts_state = self._build_mcts_state(signals, market, v8_decision)
        mcts_result = self.mcts.search(mcts_state)
        
        self.strategic_stats['mcts_runs'] += 1
        
        # Step 3: Combine v8 + MCTS
        combined = self._combine_decisions(v8_decision, mcts_result, signals, market)
        
        # Track stats
        if combined.is_strategic_override:
            self.strategic_stats['mcts_override'] += 1
        else:
            self.strategic_stats['agreements'] += 1
        
        return combined
    
    def _build_mcts_state(
        self, 
        signals: List[AgentSignal], 
        market: MarketState,
        v8_decision: CollectiveDecision
    ) -> Dict[str, Any]:
        """Build state dict for MCTS from v8 components"""
        
        # Extract symbol from market state (current symbol being analyzed)
        current_symbol = market.symbol
        
        # Determine best/worst sectors based on agent signals
        sector_scores = {'crypto': 0, 'forex': 0, 'indices': 0, 'commodities': 0}
        for sig in signals:
            # Infer sector from agent element and name
            if sig.element == ElementType.FIRE:  # Fire often crypto/momentum
                sector_scores['crypto'] += sig.strength
            elif sig.element == ElementType.AIR:  # Air = regime/forex
                sector_scores['forex'] += sig.strength
            elif sig.element == ElementType.WATER:  # Water = trend/indices
                sector_scores['indices'] += sig.strength
            elif sig.element == ElementType.EARTH:  # Earth = commodities
                sector_scores['commodities'] += sig.strength
        
        best_sector = max(sector_scores, key=sector_scores.get)
        worst_sector = min(sector_scores, key=sector_scores.get)
        
        return {
            'market': {
                'symbol': current_symbol,
                'price': market.price,
                'volatility': market.volatility,
                'adx': market.adx,
                'rsi': market.rsi,
                'trend_1d': market.trend_1d,
                'symbols': [current_symbol],
                'best_sector': best_sector,
                'worst_sector': worst_sector
            },
            'portfolio': {
                'v8_action': v8_decision.action.name,
                'v8_confidence': v8_decision.confidence,
                'v8_harmony': v8_decision.harmony_score,
                'positions': {},  # Simplified
                'exposure': 0.5
            },
            'signals': [
                {
                    'agent': s.agent_name,
                    'action': s.action.name,
                    'strength': s.strength,
                    'confidence': s.confidence
                }
                for s in signals
            ],
            'step': 0
        }
    
    def _combine_decisions(
        self,
        v8: CollectiveDecision,
        mcts: Dict[str, Any],
        signals: List[AgentSignal],
        market: MarketState
    ) -> 'StrategicCollectiveDecision':
        """
        Combine v8 and MCTS decisions strategically
        """
        v8_action = v8.action
        mcts_action_str = mcts['action']
        mcts_confidence = mcts['confidence']
        
        # Parse MCTS action
        mcts_action = self._parse_action(mcts_action_str)
        
        # Decision logic
        is_override = False
        final_action = v8_action
        final_confidence = v8.confidence
        
        # Case 1: MCTS and v8 agree → Boost confidence
        if self._actions_align(v8_action, mcts_action_str):
            final_confidence = min(0.95, v8.confidence * (1 + mcts_confidence * 0.3))
            rationale = f"{v8.rationale} | MCTS agrees ({mcts_action_str}, conf={mcts_confidence:.2f})"
        
        # Case 2: v8 HOLD, MCTS wants to trade → Respect v8 (tactical expertise)
        elif v8_action == ActionType.HOLD and mcts_action in [ActionType.BUY, ActionType.SELL]:
            final_action = ActionType.HOLD  # v8 wins
            final_confidence = v8.confidence * 0.9
            rationale = f"{v8.rationale} | MCTS suggests {mcts_action_str} but v8 holds"
        
        # Case 3: v8 wants to trade, MCTS says HOLD → Strategic caution
        elif v8_action in [ActionType.BUY, ActionType.SELL] and mcts_action == ActionType.HOLD:
            # Reduce confidence but allow trade
            final_confidence = v8.confidence * 0.7
            rationale = f"{v8.rationale} | MCTS caution: {mcts_action_str}"
        
        # Case 4: Disagreement on direction → v8 wins (tactical > strategic)
        else:
            final_action = v8_action
            final_confidence = v8.confidence * 0.8
            is_override = True
            rationale = f"{v8.rationale} | MCTS override: {mcts_action_str} (ignored)"
        
        return StrategicCollectiveDecision(
            action=final_action,
            confidence=final_confidence,
            coherence=v8.coherence,
            harmony_score=v8.harmony_score,
            weighted_strength=v8.weighted_strength,
            participating_agents=v8.participating_agents,
            dominant_element=v8.dominant_element,
            suppressed_element=v8.suppressed_element,
            guna_state=v8.guna_state,
            rationale=rationale,
            is_maya=v8.is_maya,
            # v9 additions
            mcts_action=mcts_action_str,
            mcts_confidence=mcts_confidence,
            expected_sharpe=mcts.get('expected_sharpe', 0),
            is_strategic_override=is_override
        )
    
    def _parse_action(self, action_str: str) -> ActionType:
        """Parse MCTS action string to ActionType"""
        if 'Buy' in action_str or 'Scale-in' in action_str:
            return ActionType.BUY
        elif 'Sell' in action_str or 'Close' in action_str:
            return ActionType.SELL
        else:
            return ActionType.HOLD
    
    def _actions_align(self, v8_action: ActionType, mcts_str: str) -> bool:
        """Check if v8 and MCTS actions align"""
        if v8_action == ActionType.BUY and ('Buy' in mcts_str or 'Scale-in' in mcts_str):
            return True
        if v8_action == ActionType.SELL and ('Sell' in mcts_str or 'Close' in mcts_str):
            return True
        if v8_action == ActionType.HOLD and 'Hold' in mcts_str:
            return True
        return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get strategic statistics"""
        total = self.strategic_stats['mcts_runs']
        if total == 0:
            return self.strategic_stats
        
        return {
            **self.strategic_stats,
            'agreement_rate': self.strategic_stats['agreements'] / total,
            'override_rate': self.strategic_stats['mcts_override'] / total
        }


class StrategicCollectiveDecision(CollectiveDecision):
    """Extended decision with MCTS metadata"""
    
    def __init__(self, *args, **kwargs):
        # Extract v9 fields
        self.mcts_action = kwargs.pop('mcts_action', '')
        self.mcts_confidence = kwargs.pop('mcts_confidence', 0.0)
        self.expected_sharpe = kwargs.pop('expected_sharpe', 0.0)
        self.is_strategic_override = kwargs.pop('is_strategic_override', False)
        
        # Call parent init with remaining args
        super().__init__(*args, **kwargs)
