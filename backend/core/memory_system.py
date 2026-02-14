"""
Memory and state management system.
Stores impressions (patterns) and learns from experience.
Equivalent to Chitta (consciousness/memory function).
"""

import time
from collections import deque
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

import numpy as np


@dataclass
class MemoryTrace:
    """
    Single memory impression.
    Stores pattern + action + outcome for learning.
    """

    pattern: np.ndarray  # Input pattern (perception features)
    action_taken: int  # Action chosen [0, 1, 2]
    outcome: float  # Result (reward/loss)
    timestamp: int  # When it occurred (nanoseconds)
    decay_rate: float = 0.99  # Exponential decay for old memories


@dataclass
class MemoryCluster:
    """
    Group of related memories (pattern clusters).
    Emerges from repeated similar patterns.
    """

    centroid: np.ndarray  # Average pattern (cluster center)
    members: List[MemoryTrace] = field(default_factory=list)
    activation_count: int = 0
    average_outcome: float = 0.0


class MemorySystem:
    """
    Long-term memory storage and retrieval.

    Functions:
    - Store experiences (action + outcome pairs)
    - Form pattern clusters (Vasanas - tendencies)
    - Retrieve similar past experiences
    - Enable learning from patterns
    """

    def __init__(self, capacity: int = 10000):
        """
        Initialize memory system.
        """
        self.capacity = capacity
        self.memory_buffer = deque(maxlen=capacity)
        self.clusters: List[MemoryCluster] = []
        self.cluster_threshold = 0.7
        from backend.core.database import AsyncSessionLocal

        self._db_factory = AsyncSessionLocal

    async def load_from_db(self):
        """
        Hydrate memory from persistent storage (Postgres).
        Loads the most recent 'capacity' experiences.
        """
        from sqlalchemy import desc, select

        from backend.models.agent_experience import AgentExperience

        async with self._db_factory() as session:
            # Query recent experiences
            result = await session.execute(
                select(AgentExperience)
                .order_by(desc(AgentExperience.timestamp))
                .limit(self.capacity)
            )
            rows = result.scalars().all()

            # Reconstruct memory buffer (older to newer)
            self.memory_buffer.clear()
            self.clusters.clear()

            for row in reversed(rows):
                # Convert list/JSON back to numpy
                pattern = np.array(row.state_vector, dtype=np.float32)

                trace = MemoryTrace(
                    pattern=pattern,
                    action_taken=row.action,
                    outcome=row.reward,
                    timestamp=int(row.timestamp.timestamp() * 1e9),  # Approx ns
                )
                self.memory_buffer.append(trace)
                self._update_clusters(trace)

        print(f"MemorySystem: Hydrated {len(self.memory_buffer)} experiences from DB.")

    async def store(
        self,
        perception: Dict[str, Any],
        action: int,
        outcome: float,
        agent_id: str = "system",
    ) -> None:
        """
        Store new memory trace (In-Memory + Database).
        """
        # Extract pattern
        pattern = self._extract_pattern(perception)

        # 1. Update In-Memory
        trace = MemoryTrace(
            pattern=pattern,
            action_taken=action,
            outcome=outcome,
            timestamp=int(time.time_ns()),
        )
        self.memory_buffer.append(trace)
        self._update_clusters(trace)

        # 2. Persist to DB (Async)
        from backend.models.agent_experience import AgentExperience

        # Convert numpy to list for JSONB
        state_list = pattern.tolist()

        experience_obj = AgentExperience(
            agent_id=agent_id,
            state_vector=state_list,
            next_state_vector=[],  # Placeholder for now, typically RL needs (s, a, r, s')
            action=action,
            reward=outcome,
            done=False,
        )

        async with self._db_factory() as session:
            session.add(experience_obj)
            await session.commit()

    def recall(
        self, current_perception: Dict[str, Any], k: int = 5
    ) -> List[MemoryTrace]:
        """
        Recall similar past experiences (From In-Memory Buffer).
        Fast cosine similarity scan.
        """
        if len(self.memory_buffer) == 0:
            return []

        current_pattern = self._extract_pattern(current_perception)

        # Calculate similarity (Vectorized for performance)
        # Gather all patterns
        patterns = np.stack([t.pattern for t in self.memory_buffer])

        # Norms
        norm_curr = np.linalg.norm(current_pattern)
        norm_patterns = np.linalg.norm(patterns, axis=1)

        # Dot product
        dots = np.dot(patterns, current_pattern)

        sims = dots / (norm_patterns * norm_curr + 1e-10)

        # Top K indices
        # Partition is faster than sort for large K
        if k >= len(sims):
            top_indices = np.argsort(sims)[::-1]
        else:
            top_indices = np.argpartition(sims, -k)[-k:]
            # Sort the top k
            top_indices = top_indices[np.argsort(sims[top_indices])[::-1]]

        return [self.memory_buffer[i] for i in top_indices]

    def get_tendency(self, current_perception: Dict[str, Any]) -> Optional[int]:
        """
        Get habitual tendency (Vasana) for current situation.
        """
        current_pattern = self._extract_pattern(current_perception)
        closest_cluster = self._find_closest_cluster(current_pattern)

        if not closest_cluster or len(closest_cluster.members) < 3:
            return None

        # Find most common action
        actions = [m.action_taken for m in closest_cluster.members]
        if not actions:
            return None
        most_common = max(set(actions), key=actions.count)

        return most_common

    def get_cluster_quality(self, cluster: MemoryCluster) -> float:
        if not cluster.members:
            return 0.0
        size_score = min(len(cluster.members) / 10.0, 1.0)
        outcome_score = (cluster.average_outcome + 1) / 2
        outcomes = [m.outcome for m in cluster.members]
        variance = np.var(outcomes) if outcomes else 0.0
        coherence_score = 1.0 / (1.0 + variance)
        quality = 0.4 * size_score + 0.3 * outcome_score + 0.3 * coherence_score
        return float(np.clip(quality, 0, 1))

    def _extract_pattern(self, perception: Dict[str, Any]) -> np.ndarray:
        state_vec = perception.get("state_vector", np.zeros(5))
        coherence = np.array([perception.get("coherence", 0.5)])
        phase = np.array([perception.get("phase_alignment", 0.5)])
        harmonics = np.array(perception.get("harmonic_profile", [0, 0, 0]))
        pattern = np.concatenate([state_vec, coherence, phase, harmonics])
        return pattern.astype(np.float32)

    def _calculate_similarity(
        self, pattern1: np.ndarray, pattern2: np.ndarray
    ) -> float:
        dot = np.dot(pattern1, pattern2)
        norm1 = np.linalg.norm(pattern1)
        norm2 = np.linalg.norm(pattern2)
        if norm1 < 1e-10 or norm2 < 1e-10:
            return 0.0
        return float(np.clip(dot / (norm1 * norm2), 0, 1))

    def _find_closest_cluster(self, pattern: np.ndarray) -> Optional[MemoryCluster]:
        if not self.clusters:
            return None
        max_sim = -1
        closest = None
        for cluster in self.clusters:
            sim = self._calculate_similarity(pattern, cluster.centroid)
            if sim > max_sim and sim > self.cluster_threshold:
                max_sim = sim
                closest = cluster
        return closest

    def _update_clusters(self, trace: MemoryTrace) -> None:
        closest = self._find_closest_cluster(trace.pattern)
        if closest:
            closest.members.append(trace)
            closest.activation_count += 1
            alpha = 0.1
            closest.centroid = alpha * trace.pattern + (1 - alpha) * closest.centroid
            closest.average_outcome = (
                alpha * trace.outcome + (1 - alpha) * closest.average_outcome
            )
        else:
            self.clusters.append(
                MemoryCluster(
                    centroid=trace.pattern.copy(),
                    members=[trace],
                    activation_count=1,
                    average_outcome=trace.outcome,
                )
            )

    def get_statistics(self) -> Dict[str, Any]:
        if not self.memory_buffer:
            return {
                "total_memories": 0,
                "total_clusters": 0,
                "avg_cluster_size": 0,
                "win_rate": 0.0,
            }
        outcomes = [m.outcome for m in self.memory_buffer]
        return {
            "total_memories": len(self.memory_buffer),
            "total_clusters": len(self.clusters),
            "avg_cluster_size": (
                len(self.memory_buffer) / len(self.clusters) if self.clusters else 0
            ),
            "avg_outcome": float(np.mean(outcomes)),
            "win_rate": float(sum(1 for o in outcomes if o > 0) / len(outcomes)),
        }
