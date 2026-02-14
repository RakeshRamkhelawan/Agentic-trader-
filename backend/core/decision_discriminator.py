"""
Decision discrimination layer.
Makes choices based on perception and memory.
Equivalent to Buddhi (discriminative intellect function).
"""

from typing import Dict, Any, List, Optional, Tuple
import numpy as np
import time
from backend.core.memory_system import MemorySystem


class DecisionDiscriminator:
    """
    Decision discrimination system.

    Functions:
    - Evaluate options based on memory
    - Discriminate between actions
    - Apply learned wisdom
    - Manage exploration vs exploitation
    """

    def __init__(self, memory_system: MemorySystem):
        """
        Initialize decision discriminator.

        Args:
            memory_system: Shared memory for pattern retrieval
        """
        self.memory = memory_system
        self.decision_threshold = 0.6  # Min confidence for action
        self.exploration_rate = 0.1  # Exploration vs exploitation ratio
        self.total_decisions = 0

    def discriminate(
        self, perception: Dict[str, Any], available_actions: List[int]
    ) -> Tuple[int, float, str]:
        """
        Discriminate (choose) best action.

        Process:
        1. Recall similar past experiences
        2. Evaluate each action based on memory
        3. Apply discrimination logic
        4. Return best action with confidence

        Args:
            perception: Current perception from sensory processor
            available_actions: List of action IDs [0, 1, 2]

        Returns:
            (action_id, confidence, rationale)
        """
        # 1. Recall similar situations
        similar_memories = self.memory.recall(perception, k=10)

        # 2. Check for strong habitual tendency
        habit_action = self.memory.get_tendency(perception)

        # 3. Evaluate each available action
        action_scores = {}
        for action in available_actions:
            score = self._evaluate_action(action, similar_memories)
            action_scores[action] = score

        # 4. Apply discrimination logic
        best_action, confidence, rationale = self._apply_discrimination(
            action_scores, habit_action, perception
        )

        self.total_decisions += 1
        return best_action, confidence, rationale

    def _evaluate_action(self, action: int, memories: List) -> float:
        """
        Evaluate action based on past outcomes.

        Combines:
        - Average outcome from memories
        - Frequency of success
        - Recency weighting

        Args:
            action: Action ID to evaluate
            memories: List of relevant past memories

        Returns:
            Score [-1, 1] with higher = better
        """
        if not memories:
            return 0.0

        # Filter memories for this action
        action_memories = [m for m in memories if m.action_taken == action]

        if not action_memories:
            return 0.0

        # Calculate weighted score with recency bias
        total_score = 0.0
        total_weight = 0.0
        current_time = int(time.time_ns())

        for memory in action_memories:
            # Recency weight (newer memories more important)
            age_seconds = (current_time - memory.timestamp) / 1e9
            recency_weight = memory.decay_rate ** (age_seconds / 3600)  # Decay per hour

            # Outcome contribution
            outcome_score = memory.outcome

            total_score += outcome_score * recency_weight
            total_weight += recency_weight

        if total_weight < 1e-10:
            return 0.0

        return float(total_score / total_weight)

    def _apply_discrimination(
        self,
        action_scores: Dict[int, float],
        habit_action: Optional[int],
        perception: Dict[str, Any],
    ) -> Tuple[int, float, str]:
        """
        Apply discrimination logic to choose final action.

        Buddhi's role:
        - Override habit if significantly better option exists
        - Explore new actions occasionally
        - Ensure sufficient confidence threshold

        Args:
            action_scores: Dict of action -> score
            habit_action: Most habitual action, if any
            perception: Current perception

        Returns:
            (action, confidence, rationale)
        """
        if not action_scores:
            return 0, 0.5, "No actions available, default to hold"

        # Sort actions by score
        sorted_actions = sorted(action_scores.items(), key=lambda x: x[1], reverse=True)

        best_action, best_score = sorted_actions[0]
        rationale = ""

        # Check if habit should be overridden
        if habit_action is not None and habit_action in action_scores:
            habit_score = action_scores[habit_action]

            # Override habit only if significantly better
            if best_score > habit_score * 1.2:  # 20% better threshold
                rationale = f"Override habit (action {habit_action}) with better option"
            else:
                # Follow habit
                best_action = habit_action
                best_score = habit_score
                rationale = "Follow established pattern (Vasana)"
        else:
            rationale = "Novel situation, evaluate all options"

        # Exploration: occasionally try suboptimal actions
        if np.random.random() < self.exploration_rate and len(sorted_actions) > 1:
            best_action, best_score = sorted_actions[1]
            rationale = "Exploration mode - try alternative"

        # Calculate confidence
        confidence = self._calculate_confidence(best_score, perception)

        # Check confidence threshold
        if confidence < self.decision_threshold:
            best_action = 0  # Default to hold
            confidence = 0.5
            rationale = "Insufficient confidence, default to neutral action"

        return best_action, confidence, rationale

    def _calculate_confidence(self, score: float, perception: Dict[str, Any]) -> float:
        """
        Calculate confidence in decision.

        Factors:
        - Score magnitude
        - Pattern coherence
        - Phase alignment

        Args:
            score: Action score from evaluation
            perception: Current perception

        Returns:
            Confidence [0, 1]
        """
        # Base confidence from score
        base_confidence = (score + 1) / 2  # Normalize to [0, 1]

        # Adjust for perception quality
        coherence = perception.get("coherence", 0.5)
        phase_alignment = perception.get("phase_alignment", 0.5)

        # Weighted combination
        confidence = 0.6 * base_confidence + 0.2 * coherence + 0.2 * phase_alignment

        return float(np.clip(confidence, 0, 1))

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get decision statistics for monitoring.
        """
        return {
            "total_decisions": self.total_decisions,
            "exploration_rate": self.exploration_rate,
            "decision_threshold": self.decision_threshold,
        }
