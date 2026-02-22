"""
System Identity and Meta-Coordination - OPTIMIZED VERSION (Sprint 2).

Coordinates all cognitive subsystems and maintains coherence with:
- Pre-computed Tattva masks for sparse/full mode traversal
- Vectorized numpy operations for layer processing
- Prometheus metrics for latency tracking

Sparse Mode Philosophy:
When coherence >= threshold (default 0.8), we traverse only the 8 critical layers
that are essential for the current cognitive cycle. This is like meditation at
Samadhi level 7 - lower layers are latent (sankara), not absent.

Full Mode:
When coherence < threshold or during regime changes, all 36 layers are traversed
for complete consciousness processing.

The 8 Critical Layers (Sparse Mode):
- L1: Shiva (Pure Consciousness)
- L2: Sadashiva (First Vibration)
- L3: Ishvara (Divine Will)
- L14: Buddhi (Intellect/Decision)
- L15: Ahamkara (Self/Identity)
- L16: Manas (Mind aggregation)
- L17: Prana (Vital Energy)
- L36: Prithvi (Physical Manifestation)
"""

import logging
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Optional

import numpy as np

# Optional Prometheus metrics
try:
    from prometheus_client import Gauge, Histogram

    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False

from backend.config.schemas import TattvaConfig
from backend.core.config.settings import settings
from backend.core.decision_discriminator import DecisionDiscriminator
from backend.core.memory_system import MemorySystem
from backend.core.navagraha.service import NavagrahaService
from backend.core.sensory_processor import SensoryProcessor

logger = logging.getLogger(__name__)


class TraversalMode(Enum):
    """Tattva traversal modes."""

    SPARSE = "sparse"  # 8 critical layers (high coherence >= 0.8)
    FULL = "full"  # All 36 layers (low coherence or regime change)


@dataclass
class TattvaMetrics:
    """Metrics for Tattva traversal performance."""

    mode: TraversalMode
    layers_traversed: int
    latency_us: float
    coherence_threshold: float


# Prometheus metrics (optional)
if PROMETHEUS_AVAILABLE:
    TATTVA_TRAVERSAL_LATENCY = Histogram(
        "tattva_traversal_latency_microseconds",
        "Tattva traversal latency in microseconds",
        ["mode", "layer_count"],
    )
    TATTVA_MODE_GAUGE = Gauge(
        "tattva_current_mode", "Current Tattva traversal mode (0=sparse, 1=full)"
    )
else:
    TATTVA_TRAVERSAL_LATENCY = None
    TATTVA_MODE_GAUGE = None


class SystemIdentityOptimized:
    """
    Optimized System Identity with pre-computed Tattva matrices.

    Performance targets:
    - Sparse mode: < 80μs (p99)
    - Full mode: < 200μs (p99)

    Philosophy preserved:
    The 36 Tattvas remain conceptually intact. Sparse mode is like focused
    meditation - we attend to the essential layers while others remain latent.
    """

    # The 8 critical layers for sparse mode
    SPARSE_LAYERS: np.ndarray = np.array([1, 2, 3, 14, 15, 16, 17, 36], dtype=np.int32)

    # All 36 layers for full mode
    FULL_LAYERS: np.ndarray = np.arange(1, 37, dtype=np.int32)

    # Layer processing order by phase
    PHASE_LAYERS = {
        "ascend": np.array([1, 2, 3, 4, 5], dtype=np.int32),
        "filter": np.array([6, 7, 8, 9, 10, 11, 12], dtype=np.int32),
        "interface": np.array([13, 14, 15], dtype=np.int32),
        "sense": np.array([16, 17, 18, 19, 20, 21, 22, 23, 24, 25], dtype=np.int32),
        "act": np.array([26, 27, 28, 29, 30, 31], dtype=np.int32),
        "materialize": np.array([32, 33, 34, 35, 36], dtype=np.int32),
    }

    def __init__(
        self,
        tattva_config: Optional[TattvaConfig] = None,
        coherence_threshold: float = 0.8,
        enable_metrics: bool = True,
    ):
        """
        Initialize optimized System Identity.

        Args:
            tattva_config: Tattva configuration (36 layers)
            coherence_threshold: Threshold for sparse vs full mode (default: 0.8)
            enable_metrics: Enable Prometheus metrics
        """
        # Core cognitive subsystems
        self.navagraha_service = NavagrahaService()
        self.sensory_processor = SensoryProcessor()
        self.memory_system = MemorySystem()
        self.decision_maker = DecisionDiscriminator(self.memory_system)

        # Tattva configuration
        self.tattva_config = tattva_config or TattvaConfig.default_36_tattvas()
        self.coherence_threshold = coherence_threshold
        self.enable_metrics = enable_metrics and PROMETHEUS_AVAILABLE

        # Pre-computed masks for vectorized operations
        self._precompute_layer_masks()

        # System state monitoring
        self.system_state: Dict[str, Any] = {
            "coherence": 1.0,
            "confidence": 0.5,
            "learning_rate": 0.1,
            "exploration_rate": 0.1,
            "total_experiences": 0,
            "tattva_coherence": {},
            "current_mode": TraversalMode.FULL,
        }

        # Initialize tattva coherence tracking
        for layer in self.tattva_config.layers:
            self.system_state["tattva_coherence"][layer.layer_number] = 1.0

        # Available actions
        self.action_space = [0, 1, 2]  # 0=hold, 1=buy, 2=sell

        # Performance tracking
        self.performance_history: Dict[str, Any] = {
            "outcomes": [],
            "confidences": [],
            "actions": [],
            "tattva_traversals": [],
            "traversal_latencies": [],
        }

    def _precompute_layer_masks(self) -> None:
        """
        Pre-compute layer masks for sparse and full mode traversal.

        This eliminates runtime loop overhead by using vectorized numpy operations.
        """
        # Sparse mode: 8 critical layers
        self._sparse_mask = np.isin(self.FULL_LAYERS, self.SPARSE_LAYERS)

        # Full mode: all 36 layers
        self._full_mask = np.ones(36, dtype=bool)

        # Pre-compute coherence base values for each layer
        self._layer_base_coherence = np.ones(36, dtype=np.float32)

        # Apply known coherence modifiers based on layer type
        # Kanchukas (6-12) introduce friction
        self._layer_base_coherence[5:12] = 0.95  # Layers 6-12

        # Buddhi (14) varies with system confidence
        self._layer_base_coherence[13] = 0.9  # Will be updated dynamically

        # Action layers (26-31) depend on decision confidence
        self._layer_base_coherence[25:31] = 0.8

        logger.info(
            f"Pre-computed Tattva masks: sparse={self.SPARSE_LAYERS.tolist()}, "
            f"threshold={self.coherence_threshold}"
        )

    def _select_traversal_mode(self, coherence: float) -> TraversalMode:
        """
        Select traversal mode based on system coherence.

        High coherence (>= 0.8): Sparse mode (8 layers)
        Low coherence (< 0.8): Full mode (36 layers)

        Args:
            coherence: Current system coherence [0, 1]

        Returns:
            Selected traversal mode
        """
        if coherence >= self.coherence_threshold:
            return TraversalMode.SPARSE
        return TraversalMode.FULL

    def _traverse_layers_vectorized(
        self,
        layer_numbers: np.ndarray,
        direction: str,
        context: Optional[Dict] = None,
    ) -> Dict[int, float]:
        """
        Traverse multiple Tattva layers using vectorized operations.

        This replaces the Python for-loop with numpy vectorized operations
        for significant performance improvement.

        Args:
            layer_numbers: Array of layer numbers to traverse
            direction: Direction of traversal ('ascend', 'filter', etc.)
            context: Optional context data

        Returns:
            Dictionary mapping layer number to coherence value
        """
        # Vectorized coherence calculation
        # Start with base coherence values
        coherences = np.ones(len(layer_numbers), dtype=np.float32)

        # Apply direction-specific modifiers
        if direction == "ascend":
            # Pure source activation - perfect coherence
            coherences = np.ones(len(layer_numbers), dtype=np.float32)

        elif direction == "filter":
            # Kanchukas introduce friction
            mask = (layer_numbers >= 6) & (layer_numbers <= 12)
            coherences[mask] = 0.95

        elif direction == "interface":
            # Buddhi (14) uses system confidence
            mask = layer_numbers == 14
            coherences[mask] = self.system_state["confidence"]

        elif direction == "sense":
            # Sensory coherence from input quality
            if context and "coherence" in context:
                coherences[:] = float(context["coherence"]) * 0.9
            else:
                coherences[:] = 0.9

        elif direction == "act":
            # Action coherence from decision confidence
            if context and "confidence" in context:
                coherences[:] = float(context["confidence"])
            else:
                coherences[:] = 0.8

        elif direction == "materialize":
            # Physical manifestation
            coherences = self._calculate_materialization_coherence_vectorized(
                layer_numbers, context
            )

        # Create result dictionary
        return {int(layer): float(coh) for layer, coh in zip(layer_numbers, coherences)}

    def _calculate_materialization_coherence_vectorized(
        self,
        layer_numbers: np.ndarray,
        context: Optional[Dict],
    ) -> np.ndarray:
        """
        Vectorized materialization coherence calculation.

        Args:
            layer_numbers: Array of layer numbers (should be 32-36)
            context: Optional context with hardware metrics

        Returns:
            Array of coherence values
        """
        if not self.tattva_config.mahabhutas:
            return np.ones(len(layer_numbers), dtype=np.float32)

        coherences = np.ones(len(layer_numbers), dtype=np.float32)
        maha = self.tattva_config.mahabhutas

        # Vectorized layer-specific logic
        for i, layer_num in enumerate(layer_numbers):
            if layer_num == 32:  # Akasha
                coherences[i] = 0.9 if maha.akasha.enabled else 0.5
            elif layer_num == 33:  # Vayu
                coherences[i] = 0.98 if maha.vayu.broadcast_to_all_agents else 0.9
            elif layer_num == 34:  # Agni
                coherences[i] = 0.99 if maha.agni.enabled else 0.5
            elif layer_num == 35:  # Apas
                coherences[i] = 0.9 if maha.apas.enabled else 0.5
            elif layer_num == 36:  # Prithvi
                coherences[i] = 1.0 if maha.prithvi.enable_transaction_safety else 0.9

        return coherences

    async def process_market_cycle_optimized(
        self,
        price_data: np.ndarray,
        volume_data: np.ndarray,
        orderbook_imbalance: float,
        funding_rate: float,
        social_sentiment: float,
    ) -> Dict[str, Any]:
        """
        Optimized cognitive cycle with vectorized Tattva traversal.

        Performance:
        - Sparse mode: < 80μs (p99)
        - Full mode: < 200μs (p99)

        Philosophy:
        The 36 Tattvas remain conceptually intact. Sparse mode focuses attention
        on essential layers, like meditation at Samadhi level 7.

        Args:
            price_data: Historical price array
            volume_data: Historical volume array
            orderbook_imbalance: [-1, 1] bid/ask imbalance
            funding_rate: [-0.1, 0.1] derivative appetite
            social_sentiment: [-1, 1] sentiment score

        Returns:
            Decision result with perception, action, confidence, Tattva metrics
        """
        cycle_start = time.perf_counter_ns()

        # Select traversal mode based on current coherence
        current_coherence = self.system_state["coherence"]
        mode = self._select_traversal_mode(current_coherence)
        self.system_state["current_mode"] = mode

        # Update Prometheus gauge
        if self.enable_metrics and TATTVA_MODE_GAUGE:
            TATTVA_MODE_GAUGE.set(0 if mode == TraversalMode.SPARSE else 1)

        # Choose layer set based on mode
        if mode == TraversalMode.SPARSE:
            layers_to_traverse = self.SPARSE_LAYERS
        else:
            layers_to_traverse = self.FULL_LAYERS

        tattva_traversal: Dict[str, Any] = {
            "mode": mode.value,
            "layers_traversed": layers_to_traverse.tolist(),
            "coherence_per_layer": {},
        }

        try:
            # ========== VECTORIZED TATTVA TRAVERSAL ==========
            # Process layers by phase using vectorized operations

            # Ascend: Layers 1-5
            ascend_layers = layers_to_traverse[
                (layers_to_traverse >= 1) & (layers_to_traverse <= 5)
            ]
            tattva_traversal["coherence_per_layer"].update(
                self._traverse_layers_vectorized(ascend_layers, "ascend")
            )

            # Filter: Layers 6-12
            filter_layers = layers_to_traverse[
                (layers_to_traverse >= 6) & (layers_to_traverse <= 12)
            ]
            tattva_traversal["coherence_per_layer"].update(
                self._traverse_layers_vectorized(filter_layers, "filter")
            )

            # Interface: Layers 13-15
            interface_layers = layers_to_traverse[
                (layers_to_traverse >= 13) & (layers_to_traverse <= 15)
            ]
            tattva_traversal["coherence_per_layer"].update(
                self._traverse_layers_vectorized(interface_layers, "interface")
            )

            # Fetch Navagraha State
            navagraha_state = await self.navagraha_service.get_current_state(
                lat=settings.LATITUDE, lon=settings.LONGITUDE
            )

            # Sense: Layers 16-25
            perception = self.sensory_processor.process_input(
                price_stream=price_data,
                volume_stream=volume_data,
                orderbook_imbalance=orderbook_imbalance,
                funding_rate=funding_rate,
                social_sentiment=social_sentiment,
                navagraha_state=navagraha_state,
            )

            sense_layers = layers_to_traverse[
                (layers_to_traverse >= 16) & (layers_to_traverse <= 25)
            ]
            tattva_traversal["coherence_per_layer"].update(
                self._traverse_layers_vectorized(sense_layers, "sense", perception)
            )

            # Decide: Layer 14 (Buddhi)
            action, confidence, rationale = self.decision_maker.discriminate(
                perception, self.action_space, navagraha_state
            )

            # Update Layer 14 coherence
            self.system_state["tattva_coherence"][14] = confidence
            tattva_traversal["coherence_per_layer"][14] = confidence

            # Act: Layers 26-31
            act_layers = layers_to_traverse[
                (layers_to_traverse >= 26) & (layers_to_traverse <= 31)
            ]
            act_context = {"action": action, "confidence": confidence}
            tattva_traversal["coherence_per_layer"].update(
                self._traverse_layers_vectorized(act_layers, "act", act_context)
            )

            # Materialize: Layers 32-36
            materialize_layers = layers_to_traverse[
                (layers_to_traverse >= 32) & (layers_to_traverse <= 36)
            ]
            tattva_traversal["coherence_per_layer"].update(
                self._traverse_layers_vectorized(materialize_layers, "materialize")
            )

            # Memory: Store experience
            outcome = 0.0
            await self.memory_system.store(perception, action, outcome)

            # Ahamkara: Self-monitor
            self._update_system_state(perception, confidence, action, tattva_traversal)

            # Calculate latency
            cycle_end = time.perf_counter_ns()
            latency_us = (cycle_end - cycle_start) / 1000.0

            # Record Prometheus metrics
            if self.enable_metrics and TATTVA_TRAVERSAL_LATENCY:
                TATTVA_TRAVERSAL_LATENCY.labels(
                    mode=mode.value, layer_count=len(layers_to_traverse)
                ).observe(latency_us)

            # Track performance
            self.performance_history["outcomes"].append(outcome)
            self.performance_history["confidences"].append(confidence)
            self.performance_history["actions"].append(action)
            self.performance_history["tattva_traversals"].append(tattva_traversal)
            self.performance_history["traversal_latencies"].append(latency_us)

            # Calculate overall Tattva coherence
            tattva_coherence_values = list(
                tattva_traversal["coherence_per_layer"].values()
            )
            overall_tattva_coherence = (
                float(np.mean(tattva_coherence_values))
                if tattva_coherence_values
                else 1.0
            )

            # Create metrics
            metrics = TattvaMetrics(
                mode=mode,
                layers_traversed=len(layers_to_traverse),
                latency_us=latency_us,
                coherence_threshold=self.coherence_threshold,
            )

            return {
                "action": action,
                "confidence": confidence,
                "rationale": rationale,
                "perception": {
                    k: v for k, v in perception.items() if k != "state_vector"
                },
                "perception_state": perception["state_vector"].tolist(),
                "system_state": self.system_state.copy(),
                "tattva_traversal": tattva_traversal,
                "tattva_metrics": {
                    "current_layer_coherence": tattva_traversal[
                        "coherence_per_layer"
                    ].copy(),
                    "overall_coherence": overall_tattva_coherence,
                    "total_layers": len(layers_to_traverse),
                    "mode": mode.value,
                    "traversal_latency_us": latency_us,
                },
                "cycle_latency_us": latency_us,
                "metrics": {
                    "mode": metrics.mode.value,
                    "layers": metrics.layers_traversed,
                    "latency_target_met": (
                        latency_us < 80
                        if mode == TraversalMode.SPARSE
                        else latency_us < 200
                    ),
                },
            }

        except Exception as e:
            logger.error(f"Error in optimized market cycle: {e}")
            return {
                "action": 0,
                "confidence": 0.0,
                "rationale": f"Error: {str(e)}",
                "error": True,
            }

    def _update_system_state(
        self,
        perception: Dict[str, Any],
        confidence: float,
        action: int,
        tattva_traversal: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Update system's self-awareness (Ahamkara function)."""
        # Update coherence
        perception_coherence = perception.get("coherence", 0.5)
        self.system_state["coherence"] = (
            0.9 * self.system_state["coherence"] + 0.1 * perception_coherence
        )

        # Update confidence
        self.system_state["confidence"] = (
            0.9 * self.system_state["confidence"] + 0.1 * confidence
        )

        # Update Tattva coherence tracking
        if tattva_traversal and "coherence_per_layer" in tattva_traversal:
            for layer_num, layer_coherence in tattva_traversal[
                "coherence_per_layer"
            ].items():
                if layer_num in self.system_state["tattva_coherence"]:
                    self.system_state["tattva_coherence"][layer_num] = (
                        0.9 * self.system_state["tattva_coherence"][layer_num]
                        + 0.1 * layer_coherence
                    )

        # Increment experience counter
        self.system_state["total_experiences"] += 1

        # Adapt exploration rate
        if self.system_state["coherence"] > self.coherence_threshold:
            self.system_state["exploration_rate"] = min(0.15, 0.1)
        else:
            self.system_state["exploration_rate"] = max(0.05, 0.1)

        # Log periodically
        if self.system_state["total_experiences"] % 100 == 0:
            mode = self.system_state.get("current_mode", TraversalMode.FULL)
            logger.info(
                f"System state (exp={self.system_state['total_experiences']}): "
                f"coherence={self.system_state['coherence']:.2f}, "
                f"mode={mode.value}, "
                f"threshold={self.coherence_threshold}"
            )

    def get_performance_statistics(self) -> Dict[str, Any]:
        """Get comprehensive performance statistics."""
        latencies = self.performance_history.get("traversal_latencies", [])

        if not latencies:
            return {"error": "No performance data available"}

        latencies_array = np.array(latencies)

        # Separate by mode
        sparse_latencies = [
            lat
            for lat, trav in zip(
                latencies, self.performance_history.get("tattva_traversals", [])
            )
            if trav.get("mode") == "sparse"
        ]
        full_latencies = [
            lat
            for lat, trav in zip(
                latencies, self.performance_history.get("tattva_traversals", [])
            )
            if trav.get("mode") == "full"
        ]

        return {
            "total_cycles": len(latencies),
            "all_modes": {
                "mean_us": float(np.mean(latencies_array)),
                "p50_us": float(np.percentile(latencies_array, 50)),
                "p99_us": float(np.percentile(latencies_array, 99)),
                "min_us": float(np.min(latencies_array)),
                "max_us": float(np.max(latencies_array)),
            },
            "sparse_mode": {
                "count": len(sparse_latencies),
                "mean_us": float(np.mean(sparse_latencies)) if sparse_latencies else 0,
                "p99_us": float(np.percentile(sparse_latencies, 99))
                if sparse_latencies
                else 0,
                "target_met": all(lat < 80 for lat in sparse_latencies)
                if sparse_latencies
                else True,
            },
            "full_mode": {
                "count": len(full_latencies),
                "mean_us": float(np.mean(full_latencies)) if full_latencies else 0,
                "p99_us": float(np.percentile(full_latencies, 99))
                if full_latencies
                else 0,
                "target_met": all(lat < 200 for lat in full_latencies)
                if full_latencies
                else True,
            },
            "configuration": {
                "coherence_threshold": self.coherence_threshold,
                "sparse_layers": self.SPARSE_LAYERS.tolist(),
            },
        }


# Backward compatibility alias
SystemIdentity = SystemIdentityOptimized
