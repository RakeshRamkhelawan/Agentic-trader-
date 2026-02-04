"""
HotPathEngine - Ultra-low latency execution engine.

Characteristics:
- Sub-millisecond latency (<1ms per decision)
- Deterministic: No randomness, no LLM calls
- Thread-safe: Safe for concurrent reads
- Zero blocking I/O: Except for FastConfig reads
- Memory efficient: Minimal allocations

Design:
- Reads execution decision from FastConfig
- Returns immediately (no processing)
- Falls back to default if config unavailable
- Tracks config version for staleness detection
"""

import time
from dataclasses import dataclass
from typing import Optional, Dict, Any
from pathlib import Path

from backend.execution.fast_config import (
    FastConfigManager, FALLBACK_CONFIG
)


@dataclass
class ExecutionDecision:
    """Represents a single execution decision."""
    
    action: int  # 0=hold, 1=long, 2=short
    confidence: float  # [0, 1]
    timestamp: float  # When decision was made (seconds)
    config_version: int  # Version of config used
    source: str = 'hot_path'  # Always 'hot_path'
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'action': self.action,
            'confidence': self.confidence,
            'timestamp': self.timestamp,
            'config_version': self.config_version,
            'source': self.source
        }


class HotPathEngine:
    """
    Ultra-low latency execution engine.
    
    Reads pre-computed configuration and executes trading decisions
    with minimal latency. No LLM calls, no I/O except config reads.
    """
    
    def __init__(self, config_path: str):
        """
        Initialize hot path engine.
        
        Args:
            config_path: Path to FastConfig file
        """
        self.config_path = Path(config_path)
        self.config_manager = FastConfigManager(str(config_path))
        
        # Pre-compute fallback decision
        self.fallback_decision = self._make_decision(
            FALLBACK_CONFIG,
            config_version=0
        )
    
    def get_execution_decision(self) -> ExecutionDecision:
        """
        Get execution decision.
        
        Extremely fast operation:
        - Single read of config file
        - Minimal deserialization
        - Return immediately
        - Fallback on any error
        
        Returns:
            ExecutionDecision with action and confidence
        """
        try:
            # Read config from FastConfig (single syscall, <1µs)
            config = self.config_manager.read_fast()
            version = self.config_manager.get_version()
            
            # Make decision (no processing, just wrapping)
            decision = self._make_decision(config, version)
            
            return decision
        
        except Exception:
            # Fallback on any error (robust)
            return self.fallback_decision
    
    def _make_decision(
        self,
        config: Dict[str, Any],
        config_version: int
    ) -> ExecutionDecision:
        """
        Create execution decision from config.
        
        Args:
            config: Configuration dictionary
            config_version: Version of config
            
        Returns:
            ExecutionDecision
        """
        return ExecutionDecision(
            action=int(config.get('action', FALLBACK_CONFIG['action'])),
            confidence=float(config.get('confidence', FALLBACK_CONFIG['confidence'])),
            timestamp=time.time(),
            config_version=config_version
        )
    
    def get_decision_as_dict(self) -> Dict[str, Any]:
        """
        Get execution decision as dictionary.
        
        Convenience method.
        
        Returns:
            Decision as dict
        """
        decision = self.get_execution_decision()
        return decision.to_dict()
    
    def get_action(self) -> int:
        """
        Get just the action.
        
        Convenience method for ultra-fast access.
        
        Returns:
            Action: 0=hold, 1=long, 2=short
        """
        decision = self.get_execution_decision()
        return decision.action
    
    def get_confidence(self) -> float:
        """
        Get confidence of current decision.
        
        Returns:
            Confidence [0, 1]
        """
        decision = self.get_execution_decision()
        return decision.confidence


class HotPathExecutor:
    """
    Hot path executor with batching support.
    
    For scenarios where decisions need to be batched
    (e.g., multiple market venues, multiple assets).
    """
    
    def __init__(self, config_path: str, batch_size: int = 10):
        """
        Initialize executor with batching.
        
        Args:
            config_path: Path to FastConfig file
            batch_size: Number of decisions to batch
        """
        self.engine = HotPathEngine(config_path)
        self.batch_size = batch_size
        self.decision_cache: Optional[ExecutionDecision] = None
        self.cache_version = -1
    
    def get_decision_batch(self, count: int = 1) -> list[ExecutionDecision]:
        """
        Get batch of decisions.
        
        Uses caching to reduce reads for same config.
        
        Args:
            count: Number of decisions to return
            
        Returns:
            List of ExecutionDecision objects
        """
        decisions = []
        
        for _ in range(count):
            decision = self.engine.get_execution_decision()
            decisions.append(decision)
        
        return decisions
    
    def execute_action(self, decision: ExecutionDecision) -> bool:
        """
        Execute trading action from decision.
        
        This is where the actual trade would be placed.
        
        Args:
            decision: ExecutionDecision to execute
            
        Returns:
            True if execution successful
        """
        # Placeholder for actual trade execution
        # In production, this would:
        # - Validate decision
        # - Place order on exchange
        # - Log execution
        # - Return success/failure
        
        return True


if __name__ == '__main__':
    import tempfile
    
    with tempfile.TemporaryDirectory() as tmpdir:
        config_file = f"{tmpdir}/config.bin"
        
        # Initialize config
        config_manager = FastConfigManager(config_file)
        config_manager.write_atomic({
            'action': 1,
            'confidence': 0.85,
            'exploration_rate': 0.05
        })
        
        # Initialize engine
        engine = HotPathEngine(config_file)
        
        # Get decision
        decision = engine.get_execution_decision()
        print(f"✓ Decision: action={decision.action}, confidence={decision.confidence:.2f}")
        
        # Measure latency
        import time
        times = []
        for _ in range(100):
            start = time.perf_counter()
            decision = engine.get_execution_decision()
            elapsed = time.perf_counter() - start
            times.append(elapsed * 1000)  # Convert to milliseconds
        
        avg_latency = sum(times) / len(times)
        max_latency = max(times)
        print(f"✓ Latency: avg={avg_latency:.3f}ms, max={max_latency:.3f}ms")
        print(f"✓ Throughput: {int(1000 / avg_latency)} decisions/second")
