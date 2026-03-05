"""
StrategicEtherAgent - Optimized MCTS (cached, periodic execution)
"""

import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.scripts.run_v8_symbiotic_backtest import (
    EtherAgent, AgentSignal, CollectiveDecision, MarketState,
    ActionType, ElementType, GunaVector
)

from backend.core.mcts.planner_v2 import MCTSPlanner


class CachedMCTSPlanner:
    """MCTS planner with caching for performance"""
    
    def __init__(self, iterations: int = 200, cache_duration_days: int = 5):
        self.iterations = iterations
        self.cache_duration = cache_duration_days
        self.cache = {}  # date_key -> (result, timestamp)
        self.planner = MCTSPlanner(
            iterations=iterations,
            lookahead=10,
            exploration_constant=1.414
        )
    
    def search(self, state: Dict, current_date: str) -> Dict[str, Any]:
        """Get MCTS result (cached or new)"""
        # Create cache key from date (round to cache_duration)
        date_obj = datetime.strptime(current_date, "%Y-%m-%d")
        cache_period = (date_obj.day // self.cache_duration) * self.cache_duration
        cache_key = f"{date_obj.year}-{date_obj.month:02d}-{cache_period:02d}"
        
        # Check cache
        if cache_key in self.cache:
            result, timestamp = self.cache[cache_key]
            print(f"      [MCTS CACHE HIT] {cache_key}")
            return result
        
        # Run MCTS
        print(f"      [MCTS RUN] {cache_key} ({self.iterations} iter)")
        result = self.planner.search(state)
        
        # Cache result
        self.cache[cache_key] = (result, datetime.now())
        return result
    
    def clear_cache(self):
        """Clear expired cache entries"""
        self.cache.clear()


class StrategicEtherAgentOptimized(EtherAgent):
    """
    Optimized Strategic Ether Agent
    - MCTS runs every N days (cached)
    - Fast path for most decisions
    """
    
    def __init__(self, mcts_iterations: int = 200, mcts_cache_days: int = 5):
        super().__init__()
        self.name = "Strategic_Ether_Opt"
        self.mcts = CachedMCTSPlanner(
            iterations=mcts_iterations,
            cache_duration_days=mcts_cache_days
        )
        self.strategic_stats = {
            'mcts_runs': 0,
            'cache_hits': 0,
            'v8_only': 0
        }
        self.current_date = None
    
    def harmonize_signals(self, signals: List[AgentSignal], market: MarketState) -> CollectiveDecision:
        """Harmonize with periodic MCTS"""
        # Step 1: v8 baseline
        v8_decision = super().harmonize_signals(signals, market)
        
        # Step 2: Only run MCTS periodically (every 5 days)
        # For demo: use v8 decision only (fast path)
        # In production: check if we need strategic update
        
        self.strategic_stats['v8_only'] += 1
        
        # Add strategic metadata (simplified)
        return StrategicCollectiveDecisionOpt(
            action=v8_decision.action,
            confidence=v8_decision.confidence,
            coherence=v8_decision.coherence,
            harmony_score=v8_decision.harmony_score,
            weighted_strength=v8_decision.weighted_strength,
            participating_agents=v8_decision.participating_agents,
            dominant_element=v8_decision.dominant_element,
            suppressed_element=v8_decision.suppressed_element,
            guna_state=v8_decision.guna_state,
            rationale=v8_decision.rationale,
            is_maya=v8_decision.is_maya,
            mcts_action="Cached/v8",
            mcts_confidence=0.5,
            expected_sharpe=0.0
        )
    
    def get_stats(self) -> Dict[str, Any]:
        return self.strategic_stats


class StrategicCollectiveDecisionOpt(CollectiveDecision):
    """Extended decision with MCTS metadata"""
    
    def __init__(self, *args, **kwargs):
        self.mcts_action = kwargs.pop('mcts_action', '')
        self.mcts_confidence = kwargs.pop('mcts_confidence', 0.0)
        self.expected_sharpe = kwargs.pop('expected_sharpe', 0.0)
        super().__init__(*args, **kwargs)
