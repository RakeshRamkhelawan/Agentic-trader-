"""
MCTS Planner v2 - Enhanced for Trading
Improved reward function and v8 integration
"""

import copy
import math
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

import numpy as np


@dataclass
class MCTSNode:
    """Node in MCTS tree"""

    state: Dict[str, Any]
    action: str = ""
    parent: Optional["MCTSNode"] = None
    children: List["MCTSNode"] = field(default_factory=list)

    visits: int = 0
    value: float = 0.0
    depth: int = 0

    def is_leaf(self) -> bool:
        return len(self.children) == 0

    def uct_score(self, exploration_constant: float = 1.414) -> float:
        """Upper Confidence Bound for Trees"""
        if self.visits == 0:
            return float("inf")

        exploitation = self.value / self.visits

        if self.parent and self.parent.visits > 0:
            exploration = exploration_constant * math.sqrt(
                math.log(self.parent.visits) / self.visits
            )
        else:
            exploration = 0

        return exploitation + exploration


class MCTSPlanner:
    """
    Monte Carlo Tree Search for strategic trading decisions

    Integrates with v8 by providing 10-step lookahead
    """

    def __init__(
        self,
        iterations: int = 1000,
        lookahead: int = 10,
        exploration_constant: float = 1.414,
        max_children: int = 5,
    ):
        self.iterations = iterations
        self.lookahead = lookahead
        self.c = exploration_constant
        self.max_children = max_children

    def search(self, root_state: Dict) -> Dict[str, Any]:
        """
        Run MCTS and return best action with metadata

        Args:
            root_state: Current market + portfolio state

        Returns:
            Dict with action, confidence, expected_sharpe, path
        """
        root = MCTSNode(state=root_state, depth=0)

        for i in range(self.iterations):
            # 1. Selection
            node = self._select(root)

            # 2. Expansion
            if not self._is_terminal(node):
                child = self._expand(node)
            else:
                child = node

            # 3. Simulation
            reward = self._simulate(child)

            # 4. Backpropagation
            self._backpropagate(child, reward)

            if i % 200 == 0 and i > 0:
                best_val = (
                    max([c.value / max(1, c.visits) for c in root.children]) if root.children else 0
                )
                print(f"    MCTS {i}/{self.iterations}: Best Q={best_val:.3f}")

        return self._extract_result(root)

    def _select(self, node: MCTSNode) -> MCTSNode:
        """UCT selection until leaf"""
        while not node.is_leaf():
            # Add epsilon-greedy: 10% random exploration
            if np.random.random() < 0.1:
                node = np.random.choice(node.children)
            else:
                node = max(node.children, key=lambda c: c.uct_score(self.c))
        return node

    def _expand(self, node: MCTSNode) -> MCTSNode:
        """Generate actions and create children"""
        actions = self._generate_actions(node.state)

        for action in actions[: self.max_children]:
            child_state = self._apply_action(node.state, action)
            child = MCTSNode(state=child_state, action=action, parent=node, depth=node.depth + 1)
            node.children.append(child)

        # Return first child for simulation
        return node.children[0] if node.children else node

    def _generate_actions(self, state: Dict) -> List[str]:
        """Generate possible trading actions (v8-compatible)"""
        market = state.get("market", {})
        portfolio = state.get("portfolio", {})

        actions = []

        # Get top symbols from market state
        symbols = market.get("symbols", ["BTC/EUR", "ETH/EUR"])

        for sym in symbols[:3]:  # Top 3 symbols
            # Buy actions
            actions.append(f"Buy {sym} 10%")
            actions.append(f"Scale-in {sym} 5%")

            # Sell if holding
            positions = portfolio.get("positions", {})
            if sym in positions:
                actions.append(f"Sell {sym} 50%")
                actions.append(f"Close {sym}")

        # General actions
        actions.append("Hold")
        actions.append("Rebalance sectors")
        actions.append("Risk-off: Close 20%")

        return actions

    def _apply_action(self, state: Dict, action: str) -> Dict:
        """Apply action to state (simplified)"""
        new_state = copy.deepcopy(state)
        new_state["last_action"] = action
        new_state["step"] = state.get("step", 0) + 1

        # Simulate portfolio change
        if "Buy" in action:
            # Reduce cash, add position
            pass
        elif "Sell" in action or "Close" in action:
            # Add cash, reduce position
            pass

        return new_state

    def _simulate(self, node: MCTSNode) -> float:
        """
        Monte Carlo simulation with GBM
        Returns risk-adjusted Sharpe-like score
        """
        state = copy.deepcopy(node.state)
        portfolio = state.get("portfolio", {"capital": 100000, "positions": {}})
        market = state.get("market", {"volatility": 0.02})

        initial_capital = portfolio.get("capital", 100000)
        current_capital = initial_capital
        peak_capital = initial_capital

        daily_returns = []

        # Simulate forward
        for step in range(self.lookahead):
            # Geometric Brownian Motion
            mu = 0.001  # Daily drift
            sigma = market.get("volatility", 0.02)

            returns = np.random.normal(mu, sigma)

            # Update portfolio
            current_capital *= 1 + returns
            daily_returns.append(returns)

            # Track drawdown
            if current_capital > peak_capital:
                peak_capital = current_capital

            drawdown = (peak_capital - current_capital) / peak_capital

            # Early termination on large drawdown
            if drawdown > 0.20:
                return -1.0 * (1 + drawdown)  # Penalty

        # Calculate metrics
        total_return = (current_capital - initial_capital) / initial_capital
        max_drawdown = (peak_capital - min(current_capital, peak_capital * 0.8)) / peak_capital

        # Sharpe-like ratio (simplified)
        if len(daily_returns) > 1:
            mean_ret = np.mean(daily_returns)
            std_ret = np.std(daily_returns) + 1e-6
            sharpe = (mean_ret / std_ret) * np.sqrt(252)  # Annualized
        else:
            sharpe = 0

        # Risk-adjusted reward (Calmar-like)
        if max_drawdown > 0:
            calmar = total_return / max_drawdown
        else:
            calmar = total_return * 10  # No drawdown bonus

        # Combined score
        reward = sharpe * 0.5 + calmar * 0.3 + total_return * 10

        # Penalize excessive drawdown
        if max_drawdown > 0.15:
            reward *= 1 - max_drawdown

        return reward

    def _backpropagate(self, node: MCTSNode, reward: float):
        """Update statistics up the tree"""
        while node:
            node.visits += 1
            # Incremental average
            node.value += (reward - node.value) / node.visits
            node = node.parent

    def _is_terminal(self, node: MCTSNode) -> bool:
        """Check if node is terminal"""
        return node.depth >= self.lookahead

    def _extract_result(self, root: MCTSNode) -> Dict[str, Any]:
        """Extract best action from tree"""
        if not root.children:
            return {
                "action": "Hold",
                "confidence": 0.5,
                "expected_sharpe": 0.0,
                "visits": 0,
            }

        # Select most visited child (exploitation)
        best_child = max(root.children, key=lambda c: c.visits)

        # Alternative: highest value
        best_value_child = max(root.children, key=lambda c: c.value / max(1, c.visits))

        return {
            "action": best_child.action,
            "confidence": best_child.visits / max(1, root.visits),
            "expected_sharpe": best_child.value / max(1, best_child.visits),
            "visits": best_child.visits,
            "alternative": (best_value_child.action if best_value_child != best_child else None),
        }
