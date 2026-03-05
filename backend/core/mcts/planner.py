"""
Monte Carlo Tree Search Strategic Planner
Integrates with v8 backtest without breaking changes
"""

import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import json


@dataclass
class MCTSNode:
    """Node in MCTS tree"""
    state: Dict[str, Any]
    parent: Optional['MCTSNode'] = None
    action: Optional[str] = None
    children: List['MCTSNode'] = field(default_factory=list)
    
    # MCTS statistics
    visits: int = 0
    value: float = 0.0
    pnl_history: List[float] = field(default_factory=list)
    
    def is_leaf(self) -> bool:
        return len(self.children) == 0
    
    def uct_score(self, exploration_constant: float = 1.414) -> float:
        """Upper Confidence Bound for Trees"""
        if self.visits == 0:
            return float('inf')
        
        exploitation = self.value / self.visits
        exploration = exploration_constant * np.sqrt(
            np.log(self.parent.visits) / self.visits
        ) if self.parent else 0
        
        return exploitation + exploration
    
    def best_child(self) -> 'MCTSNode':
        """Get child with highest UCT score"""
        return max(self.children, key=lambda c: c.uct_score())


class StrategicMCTSPlanner:
    """
    MCTS-based strategic planner for trading
    
    Integrates with v8 backtest by providing strategic context
    to existing agents without modifying their logic.
    """
    
    def __init__(
        self,
        lookahead_steps: int = 10,
        simulations: int = 100,
        exploration_constant: float = 1.414
    ):
        self.lookahead_steps = lookahead_steps
        self.simulations = simulations
        self.exploration_constant = exploration_constant
        
        # Trading parameters for simulation
        self.atr_sl_mult = 1.6
        self.atr_tp_mult = 4.5
        
    def plan(
        self,
        current_portfolio: Dict[str, Any],
        market_states: Dict[str, Any],
        symbols: List[str]
    ) -> Dict[str, Any]:
        """
        Generate strategic plan using MCTS
        
        Args:
            current_portfolio: Current positions and capital
            market_states: Market data for all symbols
            symbols: List of symbols to consider
        
        Returns:
            Strategic plan with recommended actions
        """
        # Create root node
        root = MCTSNode(
            state={
                "portfolio": current_portfolio,
                "markets": market_states,
                "step": 0,
                "date": datetime.now()
            }
        )
        
        # Run MCTS
        for i in range(self.simulations):
            node = self._select(root)
            child = self._expand(node, symbols)
            reward = self._simulate(child)
            self._backpropagate(child, reward)
            
            if i % 20 == 0:
                print(f"  MCTS Sim {i}/{self.simulations}: Best value {root.value/max(1,root.visits):.3f}")
        
        # Extract best plan
        best_plan = self._extract_plan(root)
        
        return {
            "root": root,
            "best_plan": best_plan,
            "confidence": root.value / max(1, root.visits),
            "expected_sharpe": best_plan.get("expected_sharpe", 0),
            "recommended_symbol": best_plan.get("symbol"),
            "recommended_action": best_plan.get("action"),
            "position_size_mult": best_plan.get("size_mult", 1.0)
        }
    
    def _select(self, node: MCTSNode) -> MCTSNode:
        """Select path using UCT until leaf"""
        while not node.is_leaf() and node.visits > 0:
            # Add exploration noise
            if np.random.random() < 0.1:  # 10% random exploration
                node = np.random.choice(node.children)
            else:
                node = node.best_child()
        return node
    
    def _expand(self, node: MCTSNode, symbols: List[str]) -> MCTSNode:
        """Expand node with possible trading actions"""
        if node.state["step"] >= self.lookahead_steps:
            return node
        
        # Generate possible actions
        actions = self._generate_actions(node.state, symbols)
        
        for action in actions:
            child_state = self._apply_action(node.state, action)
            child = MCTSNode(
                state=child_state,
                parent=node,
                action=action
            )
            node.children.append(child)
        
        # Return first child for simulation
        return node.children[0] if node.children else node
    
    def _generate_actions(
        self, 
        state: Dict, 
        symbols: List[str]
    ) -> List[Dict]:
        """Generate possible trading actions"""
        actions = []
        portfolio = state["portfolio"]
        markets = state["markets"]
        
        for symbol in symbols:
            market = markets.get(symbol, {})
            if not market:
                continue
            
            # Buy action
            actions.append({
                "type": "buy",
                "symbol": symbol,
                "size": 0.1,  # 10% of capital
                "reason": "strategic_entry"
            })
            
            # Sell action (if holding)
            if portfolio.get("positions", {}).get(symbol):
                actions.append({
                    "type": "sell",
                    "symbol": symbol,
                    "reason": "strategic_exit"
                })
        
        # Hold action
        actions.append({"type": "hold", "symbol": None})
        
        return actions[:10]  # Limit branching factor
    
    def _apply_action(self, state: Dict, action: Dict) -> Dict:
        """Apply action to state"""
        import copy
        new_state = copy.deepcopy(state)
        new_state["step"] += 1
        new_state["last_action"] = action
        
        # Simulate portfolio update
        if action["type"] == "buy":
            # Deduct capital, add position
            pass
        elif action["type"] == "sell":
            # Add capital, remove position
            pass
        
        return new_state
    
    def _simulate(self, node: MCTSNode) -> float:
        """Monte Carlo simulation of PnL"""
        state = node.state
        portfolio = state["portfolio"].copy()
        
        total_pnl = 0
        max_dd = 0
        peak = portfolio.get("capital", 100000)
        
        # Simulate forward
        for step in range(state["step"], self.lookahead_steps):
            # Random market movement (simplified GBM)
            returns = np.random.normal(0.0002, 0.02)  # Daily drift/vol
            
            # Update portfolio
            for symbol, pos in portfolio.get("positions", {}).items():
                pnl = pos["size"] * returns
                total_pnl += pnl
            
            # Track drawdown
            current = portfolio.get("capital", 100000) + total_pnl
            if current > peak:
                peak = current
            dd = (peak - current) / peak
            max_dd = max(max_dd, dd)
        
        # Risk-adjusted reward (Sharpe-like)
        if max_dd > 0.20:  # Cap at 20% DD
            return -1.0
        
        sharpe = total_pnl / (max_dd + 0.001)
        return sharpe
    
    def _backpropagate(self, node: MCTSNode, reward: float):
        """Update statistics up the tree"""
        while node:
            node.visits += 1
            # Running average
            node.value += (reward - node.value) / node.visits
            node.pnl_history.append(reward)
            node = node.parent
    
    def _extract_plan(self, root: MCTSNode) -> Dict:
        """Extract best plan from tree"""
        if not root.children:
            return {"action": "hold", "symbol": None}
        
        # Find best child
        best_child = max(root.children, key=lambda c: c.value / max(1, c.visits))
        
        action = best_child.action or {"type": "hold", "symbol": None}
        
        return {
            "action": action.get("type", "hold"),
            "symbol": action.get("symbol"),
            "size_mult": 1.0 + (best_child.value / max(1, best_child.visits)),
            "expected_sharpe": best_child.value / max(1, best_child.visits),
            "confidence": best_child.visits / max(1, root.visits),
            "path_length": self._count_depth(best_child)
        }
    
    def _count_depth(self, node: MCTSNode) -> int:
        """Count depth of node in tree"""
        depth = 0
        current = node
        while current.parent:
            depth += 1
            current = current.parent
        return depth


# Integration helper
def create_strategic_context(mcts_plan: Dict) -> Dict:
    """
    Convert MCTS plan to StrategicContext for v8 adapter
    """
    return {
        "lookahead_days": 10,
        "mcts_confidence": mcts_plan.get("confidence", 0.5),
        "strategic_bias": mcts_plan.get("recommended_action", "neutral"),
        "time_horizon": "swing",
        "position_size_mult": mcts_plan.get("position_size_mult", 1.0),
        "stop_loss_mult": 1.0,
        "take_profit_mult": 1.0,
        "recommended_symbol": mcts_plan.get("recommended_symbol")
    }
