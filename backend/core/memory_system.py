"""
Memory and state management system.
Stores impressions (patterns) and learns from experience.
Equivalent to Chitta (consciousness/memory function).
"""

from typing import Dict, Any, List, Optional, Tuple
from collections import deque
import numpy as np
from dataclasses import dataclass, field
import time


@dataclass
class MemoryTrace:
    """
    Single memory impression.
    Stores pattern + action + outcome for learning.
    """
    pattern: np.ndarray          # Input pattern (perception features)
    action_taken: int            # Action chosen [0, 1, 2]
    outcome: float               # Result (reward/loss)
    timestamp: int               # When it occurred (nanoseconds)
    decay_rate: float = 0.99     # Exponential decay for old memories


@dataclass
class MemoryCluster:
    """
    Group of related memories (pattern clusters).
    Emerges from repeated similar patterns.
    """
    centroid: np.ndarray         # Average pattern (cluster center)
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
        
        Args:
            capacity: Maximum number of memories to store
        """
        self.capacity = capacity
        self.memory_buffer = deque(maxlen=capacity)
        self.clusters: List[MemoryCluster] = []
        self.cluster_threshold = 0.7  # Similarity threshold for clustering
    
    def store(
        self,
        perception: Dict[str, Any],
        action: int,
        outcome: float
    ) -> None:
        """
        Store new memory trace.
        Updates clusters (tendencies) as patterns emerge.
        
        Args:
            perception: Perception dictionary from sensory processor
            action: Action taken [0=hold, 1=buy, 2=sell]
            outcome: Reward/loss from action
        """
        # Extract pattern from perception
        pattern = self._extract_pattern(perception)
        
        # Create memory trace
        trace = MemoryTrace(
            pattern=pattern,
            action_taken=action,
            outcome=outcome,
            timestamp=int(time.time_ns())
        )
        
        # Add to buffer
        self.memory_buffer.append(trace)
        
        # Update clusters (Vasanas - tendencies)
        self._update_clusters(trace)
    
    def recall(
        self,
        current_perception: Dict[str, Any],
        k: int = 5
    ) -> List[MemoryTrace]:
        """
        Recall similar past experiences via pattern matching.
        
        Args:
            current_perception: Current perception to match
            k: Number of similar memories to return
            
        Returns:
            List of k most similar MemoryTraces
        """
        if len(self.memory_buffer) == 0:
            return []
        
        current_pattern = self._extract_pattern(current_perception)
        
        # Calculate similarity to all memories
        similarities = []
        for trace in self.memory_buffer:
            sim = self._calculate_similarity(current_pattern, trace.pattern)
            similarities.append((sim, trace))
        
        # Sort by similarity and return top k
        similarities.sort(key=lambda x: x[0], reverse=True)
        return [trace for _, trace in similarities[:k]]
    
    def get_tendency(
        self,
        current_perception: Dict[str, Any]
    ) -> Optional[int]:
        """
        Get habitual tendency (Vasana) for current situation.
        
        Returns most common action from similar past patterns.
        Only returns if cluster is sufficiently populated.
        
        Args:
            current_perception: Current perception
            
        Returns:
            Most common action ID, or None if insufficient data
        """
        current_pattern = self._extract_pattern(current_perception)
        closest_cluster = self._find_closest_cluster(current_pattern)
        
        if not closest_cluster or len(closest_cluster.members) < 3:
            return None
        
        # Find most common action in cluster
        actions = [m.action_taken for m in closest_cluster.members]
        most_common = max(set(actions), key=actions.count)
        
        return most_common
    
    def get_cluster_quality(
        self,
        cluster: MemoryCluster
    ) -> float:
        """
        Evaluate quality of a cluster based on:
        - Size (more members = higher confidence)
        - Outcome (better average outcome = higher quality)
        - Coherence (low variance = higher quality)
        """
        if not cluster.members:
            return 0.0
        
        # Size score
        size_score = min(len(cluster.members) / 10.0, 1.0)
        
        # Outcome score (normalize to [0, 1])
        outcome_score = (cluster.average_outcome + 1) / 2
        
        # Coherence: low variance = high coherence
        outcomes = [m.outcome for m in cluster.members]
        variance = np.var(outcomes)
        coherence_score = 1.0 / (1.0 + variance)
        
        # Weighted quality
        quality = (
            0.4 * size_score +
            0.3 * outcome_score +
            0.3 * coherence_score
        )
        
        return float(np.clip(quality, 0, 1))
    
    def _extract_pattern(self, perception: Dict[str, Any]) -> np.ndarray:
        """
        Extract pattern vector from perception.
        Used for pattern matching and clustering.
        """
        # Concatenate key features
        state_vec = perception.get('state_vector', np.zeros(5))
        coherence = np.array([perception.get('coherence', 0.5)])
        phase_alignment = np.array([perception.get('phase_alignment', 0.5)])
        harmonics = np.array(perception.get('harmonic_profile', [0, 0, 0]))
        
        pattern = np.concatenate([
            state_vec,
            coherence,
            phase_alignment,
            harmonics
        ])
        
        return pattern.astype(np.float32)
    
    def _calculate_similarity(
        self,
        pattern1: np.ndarray,
        pattern2: np.ndarray
    ) -> float:
        """
        Calculate similarity between patterns using cosine similarity.
        
        Returns: [0, 1] where 1 = identical
        """
        dot_product = np.dot(pattern1, pattern2)
        norm1 = np.linalg.norm(pattern1)
        norm2 = np.linalg.norm(pattern2)
        
        if norm1 < 1e-10 or norm2 < 1e-10:
            return 0.0
        
        similarity = dot_product / (norm1 * norm2)
        return float(np.clip(similarity, 0, 1))
    
    def _update_clusters(self, trace: MemoryTrace) -> None:
        """
        Update memory clusters (Vasanas).
        Adds memory to existing cluster or creates new one.
        """
        closest_cluster = self._find_closest_cluster(trace.pattern)
        
        if closest_cluster:
            # Add to existing cluster
            closest_cluster.members.append(trace)
            closest_cluster.activation_count += 1
            
            # Update centroid (exponential moving average)
            alpha = 0.1
            closest_cluster.centroid = (
                alpha * trace.pattern +
                (1 - alpha) * closest_cluster.centroid
            )
            
            # Update average outcome
            closest_cluster.average_outcome = (
                alpha * trace.outcome +
                (1 - alpha) * closest_cluster.average_outcome
            )
        else:
            # Create new cluster
            new_cluster = MemoryCluster(
                centroid=trace.pattern.copy(),
                members=[trace],
                activation_count=1,
                average_outcome=trace.outcome
            )
            self.clusters.append(new_cluster)
    
    def _find_closest_cluster(
        self,
        pattern: np.ndarray
    ) -> Optional[MemoryCluster]:
        """
        Find cluster with most similar centroid.
        
        Returns: Closest cluster if similarity > threshold, else None
        """
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
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get system statistics for monitoring.
        
        Returns:
            Dictionary with memory statistics
        """
        if not self.memory_buffer:
            return {
                'total_memories': 0,
                'total_clusters': 0,
                'avg_cluster_size': 0,
                'avg_outcome': 0
            }
        
        outcomes = [m.outcome for m in self.memory_buffer]
        
        return {
            'total_memories': len(self.memory_buffer),
            'total_clusters': len(self.clusters),
            'avg_cluster_size': len(self.memory_buffer) / len(self.clusters)
                               if self.clusters else 0,
            'avg_outcome': float(np.mean(outcomes)),
            'win_rate': float(sum(1 for o in outcomes if o > 0) / len(outcomes))
        }
