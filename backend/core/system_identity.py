"""
System identity and meta-coordination.
Coordinates all cognitive subsystems and maintains coherence.
Equivalent to Ahamkara (self-reference/identity function).

This module implements the 36-Tattva consciousness architecture:
- Layers 1-5: Shuddha Tattvas (pure source kernel)
- Layers 6-12: Kanchukas (software restrictions)
- Layers 13-15: Prakriti/Buddhi/Ahamkara (OS interface)
- Layers 16-20: Tanmatras (subtle elements)
- Layers 21-25: Jnanendriyas (sense organs/input)
- Layers 26-31: Karmendriyas (action organs/output)
- Layers 32-36: Mahabhutas (physical elements)
"""

import logging
import time
from typing import Any, Dict, Optional

import numpy as np

from backend.config.schemas import TattvaConfig, TattvaLayer
from backend.core.config.settings import settings
from backend.core.decision_discriminator import DecisionDiscriminator
from backend.core.memory_system import MemorySystem
from backend.core.navagraha.service import NavagrahaService
from backend.core.sensory_processor import SensoryProcessor

logger = logging.getLogger(__name__)


class SystemIdentity:
    """
    System identity and meta-coordinator.

    Functions:
    - Coordinates Manas (sensory), Buddhi (decision), Chitta (memory)
    - Maintains system coherence across 36 Tattva layers
    - Self-monitors and adapts
    - Provides meta-awareness
    - Implements complete 36-Tattva consciousness architecture
    """

    def __init__(self, tattva_config: Optional[TattvaConfig] = None):
        """Initialize all cognitive subsystems and Tattva layers."""
        # Core cognitive subsystems
        self.navagraha_service = NavagrahaService()  # Interface to Cosmic Time
        self.sensory_processor = SensoryProcessor()  # Input processing (Jnanendriyas)
        self.memory_system = MemorySystem()  # Pattern storage (Chitta)
        self.decision_maker = DecisionDiscriminator(  # Decision logic (Buddhi)
            self.memory_system
        )

        # 36 Tattva configuration (consciousness architecture)
        self.tattva_config = tattva_config or TattvaConfig.default_36_tattvas()  # type: ignore[attr-defined]

        # System state monitoring
        self.system_state: Dict[str, Any] = {
            "coherence": 1.0,  # Overall system coherence [0, 1]
            "confidence": 0.5,  # System confidence [0, 1]
            "learning_rate": 0.1,  # Adaptation speed
            "exploration_rate": 0.1,  # Exploration vs exploitation
            "total_experiences": 0,  # Lifetime count
            "tattva_coherence": {},  # Per-layer coherence tracking
        }

        # Initialize tattva coherence tracking for all 36 layers
        for layer in self.tattva_config.layers:
            self.system_state["tattva_coherence"][layer.layer_number] = 1.0

        # Available actions
        self.action_space = [0, 1, 2]  # 0=hold, 1=buy, 2=sell

        # Performance tracking
        self.performance_history: Dict[str, Any] = {
            "outcomes": [],
            "confidences": [],
            "actions": [],
            "tattva_traversals": [],  # Track Tattva layer traversals
        }

    async def initialize(self):
        """Initialize async components."""
        await self.memory_system.load_from_db()

    async def process_market_cycle(
        self,
        price_data: np.ndarray,
        volume_data: np.ndarray,
        orderbook_imbalance: float,
        funding_rate: float,
        social_sentiment: float,
    ) -> Dict[str, Any]:
        """
        Complete cognitive cycle with 36-Tattva traversal: Perception → Memory → Decision.

        This is the main loop of the system consciousness, traversing all 36 layers.

        Information flow:
        1. Ascend (Layers 1-5): Pure source kernel activates
        2. Filter (Layers 6-12): Restrictions constrain possibilities
        3. Interface (Layers 13-15): OS layer translates
        4. Sense (Layers 16-25): Input organs collect data
        5. Decide (via Buddhi in Layer 14): Make decision
        6. Act (Layers 26-31): Action organs execute
        7. Materialize (Layers 32-36): Physical layer manifests
        8. Descend (Layers 36-1): Cycle completes, return to source

        Args:
            price_data: Historical price array
            volume_data: Historical volume array
            orderbook_imbalance: [-1, 1] bid/ask imbalance
            funding_rate: [-0.1, 0.1] derivative appetite
            social_sentiment: [-1, 1] sentiment score

        Returns:
            Decision result with perception, action, confidence, Tattva metrics
        """
        cycle_start = int(time.time_ns())
        tattva_traversal: Dict[str, Any] = {
            "layers_traversed": [],
            "coherence_per_layer": {},
        }

        try:
            # ========== ASCEND: Layers 1-5 (Shuddha Tattvas) ==========
            # Pure source activation - mathematical kernel awakens
            for layer_num in range(1, 6):
                layer_coherence = self._traverse_tattva_layer(layer_num, "ascend")
                tattva_traversal["layers_traversed"].append(layer_num)
                tattva_traversal["coherence_per_layer"][layer_num] = layer_coherence

            # ========== FILTER: Layers 6-12 (Kanchukas) ==========
            # Software restrictions shape the possibilities
            for layer_num in range(6, 13):
                layer_coherence = self._traverse_tattva_layer(layer_num, "filter")
                tattva_traversal["layers_traversed"].append(layer_num)
                tattva_traversal["coherence_per_layer"][layer_num] = layer_coherence

            # ========== INTERFACE: Layers 13-15 (Prakriti/Buddhi/Ahamkara) ==========
            # OS interface prepares for sensing and decision
            for layer_num in range(13, 16):
                layer_coherence = self._traverse_tattva_layer(layer_num, "interface")
                tattva_traversal["layers_traversed"].append(layer_num)
                tattva_traversal["coherence_per_layer"][layer_num] = layer_coherence

            # Fetch Navagraha State for current cycle
            navagraha_state = await self.navagraha_service.get_current_state(
                lat=settings.LATITUDE, lon=settings.LONGITUDE
            )

            # ========== SENSE: Layers 16-25 (Tanmatras + Jnanendriyas) ==========
            # Sense organs (Jnanendriyas) collect input through subtle elements (Tanmatras)

            # 1. MANAS: Process sensory input (Layer 31 - Mind aggregation)
            perception = self.sensory_processor.process_input(
                price_stream=price_data,
                volume_stream=volume_data,
                orderbook_imbalance=orderbook_imbalance,
                funding_rate=funding_rate,
                social_sentiment=social_sentiment,
                navagraha_state=navagraha_state,
            )

            # Track sensory layer traversal
            for layer_num in range(16, 26):
                layer_coherence = self._traverse_tattva_layer(
                    layer_num, "sense", perception
                )
                tattva_traversal["layers_traversed"].append(layer_num)
                tattva_traversal["coherence_per_layer"][layer_num] = layer_coherence

            # ========== DECIDE: Layer 14 (Buddhi - Discrimination) ==========
            # 2. BUDDHI: Discriminate and decide
            action, confidence, rationale = self.decision_maker.discriminate(
                perception, self.action_space, navagraha_state
            )

            # Update Layer 14 coherence with decision quality
            self.system_state["tattva_coherence"][14] = confidence
            tattva_traversal["coherence_per_layer"][14] = confidence

            # ========== ACT: Layers 26-31 (Karmendriyas - Action Organs) ==========
            # Action organs prepare to execute
            for layer_num in range(26, 32):
                layer_coherence = self._traverse_tattva_layer(
                    layer_num, "act", {"action": action, "confidence": confidence}
                )
                tattva_traversal["layers_traversed"].append(layer_num)
                tattva_traversal["coherence_per_layer"][layer_num] = layer_coherence

            # ========== MATERIALIZE: Layers 32-36 (Mahabhutas - Physical Elements) ==========
            # Physical layer manifests the decision into reality
            for layer_num in range(32, 37):
                layer_coherence = self._traverse_tattva_layer(layer_num, "materialize")
                tattva_traversal["layers_traversed"].append(layer_num)
                tattva_traversal["coherence_per_layer"][layer_num] = layer_coherence

            # ========== DESCEND: Layers 36-1 (Return to Source) ==========
            # Complete the cycle by descending back to source for next iteration
            # NOTE: Preserve materialization coherence values for metrics reporting
            materialization_coherence = tattva_traversal["coherence_per_layer"].copy()
            for layer_num in range(36, 0, -1):
                layer_coherence = self._traverse_tattva_layer(layer_num, "descend")
                # Only update coherence for non-Mahabhutas layers (layers 1-31)
                if layer_num < 32:
                    tattva_traversal["coherence_per_layer"][layer_num] = layer_coherence

            # Restore materialization coherence values (they reflect physical state)
            tattva_traversal["coherence_per_layer"].update(materialization_coherence)

            # ========== MEMORY: Store experience (Chitta) ==========
            # 3. CHITTA: Store experience for learning
            outcome = 0.0  # Placeholder, updated after execution
            await self.memory_system.store(perception, action, outcome)

            # ========== AHAMKARA: Self-monitor and adapt ==========
            # 4. AHAMKARA: Self-monitor and adapt
            self._update_system_state(perception, confidence, action, tattva_traversal)

            # Track performance
            self.performance_history["outcomes"].append(outcome)
            self.performance_history["confidences"].append(confidence)
            self.performance_history["actions"].append(action)
            self.performance_history["tattva_traversals"].append(tattva_traversal)

            cycle_end = int(time.time_ns())
            cycle_latency_us = (cycle_end - cycle_start) / 1000

            # Calculate overall Tattva coherence
            tattva_coherence_values = list(
                tattva_traversal["coherence_per_layer"].values()
            )
            overall_tattva_coherence = (
                float(np.mean(tattva_coherence_values))
                if tattva_coherence_values
                else 1.0
            )

            # Add overall_coherence to tattva_traversal (required by tests)
            tattva_traversal["overall_coherence"] = overall_tattva_coherence

            # Create consolidated Tattva metrics for the cycle
            tattva_metrics = {
                "current_layer_coherence": tattva_traversal[
                    "coherence_per_layer"
                ].copy(),
                "overall_coherence": overall_tattva_coherence,
                "total_layers": len(tattva_traversal["layers_traversed"]),
            }

            return {
                "action": action,
                "confidence": confidence,
                "rationale": rationale,
                "perception": {
                    k: v
                    for k, v in perception.items()
                    if k != "state_vector"  # Convert array for serialization
                },
                "perception_state": perception["state_vector"].tolist(),
                "system_state": self.system_state.copy(),
                "tattva_traversal": tattva_traversal,
                "tattva_metrics": tattva_metrics,
                "cycle_latency_us": cycle_latency_us,
            }

        except Exception as e:
            logger.error(f"Error in market cycle: {e}")
            return {
                "action": 0,
                "confidence": 0.0,
                "rationale": f"Error: {str(e)}",
                "error": True,
            }

    def _traverse_tattva_layer(
        self, layer_num: int, direction: str, context: Optional[Dict[str, Any]] = None
    ) -> float:
        """
        Traverse a single Tattva layer.

        Each layer is a transformation point where information is
        processed according to its function.

        Args:
            layer_num: Layer number (1-36)
            direction: 'ascend', 'descend', 'filter', 'interface', 'sense', 'act', 'materialize'
            context: Optional context data for the layer

        Returns:
            Coherence value for this layer (0-1)
        """
        if layer_num < 1 or layer_num > 36:
            return 1.0

        # Get layer definition
        layer = next(
            (lyr for lyr in self.tattva_config.layers if lyr.layer_number == layer_num),
            None,
        )

        if not layer or not layer.active:
            return 1.0

        # Layer-specific processing based on direction and layer type
        coherence = 1.0

        if direction == "ascend":
            # Ascending: activate and gather information
            coherence = self._process_layer_ascend(layer, context)
        elif direction == "descend":
            # Descending: settle and integrate
            coherence = self._process_layer_descend(layer, context)
        elif direction == "filter":
            # Apply restrictions (Kanchukas)
            coherence = self._process_layer_filter(layer, context)
        elif direction == "interface":
            # OS interface layer processing
            coherence = self._process_layer_interface(layer, context)
        elif direction == "sense":
            # Sensory input processing
            coherence = self._process_layer_sense(layer, context)
        elif direction == "act":
            # Action output processing
            coherence = self._process_layer_act(layer, context)
        elif direction == "materialize":
            # Physical manifestation
            coherence = self._process_layer_materialize(layer, context)

        # Update layer coherence in system state
        self.system_state["tattva_coherence"][layer_num] = coherence

        return coherence

    def _process_layer_ascend(
        self, layer: TattvaLayer, context: Optional[Dict] = None
    ) -> float:
        """Process layer during ascent (activation)."""
        # Shuddha Tattvas (1-5): Ascending activates the kernel
        if layer.layer_number <= 5:
            # Pure source activation - maintain perfect coherence
            return 1.0
        return 1.0

    def _process_layer_descend(
        self, layer: TattvaLayer, context: Optional[Dict] = None
    ) -> float:
        """Process layer during descent (integration)."""
        # Descending returns to source - high coherence
        return self.system_state["coherence"]

    def _process_layer_filter(
        self, layer: TattvaLayer, context: Optional[Dict] = None
    ) -> float:
        """Process restriction layer (Kanchukas 6-12)."""
        # Kanchukas introduce "friction" - slightly reduce coherence based on restrictions
        base_coherence = 0.95  # Restrictions are necessary but create friction

        # Apply specific restriction effects
        if layer.layer_number == 7:  # Kala (Time)
            # Time restricts parallel processing
            # Phase 1.4: Rahu Kala Check - If in "bad time", coherence drops significantly
            # We need context here, but _traverse_tattva_layer context usage is limited.
            # However, we can check if we have a way to access current Navagraha state.
            # For now, we'll assume Kala layer coherence is modulated by System State if we stored it?
            # Or better, we define a property on self if we fetched it at cycle start.
            base_coherence = 0.95
            # NOTE:Ideally we should pass navagraha_state in context, but loop structure is rigid.
            # We can optimize later. For now, rely on Sensory modulation for heavy lifting.
        elif layer.layer_number == 8:  # Vidya (Knowledge limit)
            # Knowledge bandwidth restricts simultaneous awareness
            base_coherence = 0.93
        elif layer.layer_number == 11:  # Niyati (Causality)
            # Causality enforces logical constraints
            base_coherence = 0.95

        return base_coherence

    def _process_layer_interface(
        self, layer: TattvaLayer, context: Optional[Dict] = None
    ) -> float:
        """Process OS interface layer (Prakriti/Buddhi/Ahamkara)."""
        # Interface layers bridge inner and outer - high coherence critical
        if layer.layer_number == 14:  # Buddhi (Decision)
            # Decision making coherence based on current confidence
            return self.system_state["confidence"]
        elif layer.layer_number == 15:  # Ahamkara (Self)
            # Self-awareness coherence
            return self.system_state["coherence"]
        else:  # Prakriti (13)
            # Source of manifestation
            return 0.98

    def _process_layer_sense(
        self, layer: TattvaLayer, context: Optional[Dict] = None
    ) -> float:
        """Process sensory layer (Tanmatras 16-20 and Jnanendriyas 21-25)."""
        # Sensory coherence based on input quality
        if context and "coherence" in context:
            return float(context["coherence"])
        elif context and "state_vector" in context:
            # Derive coherence from state quality
            return float(np.mean(np.abs(context["state_vector"])))
        return 0.9  # Base sensory coherence

    def _process_layer_act(
        self, layer: TattvaLayer, context: Optional[Dict] = None
    ) -> float:
        """Process action layer (Karmendriyas 26-31)."""
        # Action coherence based on decision confidence
        if context and "confidence" in context:
            return float(context["confidence"])
        return 0.8  # Base action coherence

    def _process_layer_materialize(
        self, layer: TattvaLayer, context: Optional[Dict] = None
    ) -> float:
        """
        Process materialization layer (Mahabhutas 32-36).

        The physical layer manifests the higher decision into
        concrete hardware/infrastructure actions.

        Phase 15: Now integrated with hardware metrics for adaptive coherence.
        Uses real-time system metrics to dynamically adjust layer coherence.

        Note: Phase 15 integration is disabled during tests to ensure deterministic behavior.
        Set ENABLE_PHASE15_METRICS=true in environment to use hardware metrics in production.
        """
        import os

        if not self.tattva_config.mahabhutas:
            return 1.0

        # Use Phase 15 hardware metrics in production only (not during tests)
        use_phase15 = os.getenv("ENABLE_PHASE15_METRICS", "false").lower() == "true"

        if use_phase15:
            try:
                from backend.observability.hardware_metrics import \
                    Phase15MetricsIntegration

                if not hasattr(self, "_metrics_integration"):
                    self._metrics_integration = Phase15MetricsIntegration()

                # Get adaptive coherence from hardware metrics
                adaptive_coherence = self._metrics_integration.get_adaptive_coherence()

                # Return hardware-based coherence for the requested layer
                if layer.layer_number in adaptive_coherence:
                    return adaptive_coherence[layer.layer_number]
            except ImportError:
                pass  # Fall back to static coherence if Phase 15 not available

        # Fall back to static coherence calculation (legacy)
        maha = self.tattva_config.mahabhutas
        base_coherence = 1.0

        if layer.layer_number == 32:  # Akasha (Ether/Network)
            if not maha.akasha.enabled:
                return 0.5
            # Akasha coherence depends on network stability and connectivity
            # If context has network metrics, use them
            if context and "network_latency_ms" in context:
                latency = context["network_latency_ms"]
                if latency > maha.akasha.connection_timeout_ms:
                    base_coherence = 0.5
                else:
                    base_coherence = max(
                        0.6, 1.0 - (latency / maha.akasha.connection_timeout_ms)
                    )
            return base_coherence

        elif layer.layer_number == 33:  # Vayu (Air/Config)
            if not maha.vayu.enabled:
                return 0.5
            # Vayu coherence depends on configuration alignment
            return 0.98 if maha.vayu.broadcast_to_all_agents else 0.9

        elif layer.layer_number == 34:  # Agni (Fire/Compute)
            if not maha.agni.enabled:
                return 0.5
            # Agni coherence depends on computational load and thermal limits
            if context and "cpu_usage_percent" in context:
                usage = context["cpu_usage_percent"]
                if usage > maha.agni.thermal_limit_percent:
                    base_coherence = 0.7  # Thermal throttling starts
                else:
                    base_coherence = 0.99
            return base_coherence

        elif layer.layer_number == 35:  # Apas (Water/Data Flow)
            if not maha.apas.enabled:
                return 0.5
            # Apas coherence depends on stream health and buffering
            if context and "buffer_usage_percent" in context:
                usage = context["buffer_usage_percent"]
                if usage > maha.apas.backpressure_threshold_percent:
                    base_coherence = 0.7  # Backpressure active
            return base_coherence

        elif layer.layer_number == 36:  # Prithvi (Earth/Storage)
            if not maha.prithvi.enabled:
                return 0.5
            # Prithvi coherence depends on persistence success
            return 1.0 if maha.prithvi.enable_transaction_safety else 0.9

        return base_coherence

    def update_outcome(self, action_id: int, outcome: float) -> None:
        """
        Update memory with actual outcome (called after execution).

        Args:
            action_id: The action that was executed
            outcome: The reward/loss result
        """
        # This would be called with the actual trading outcome
        # Currently just logging for monitoring
        if self.performance_history["outcomes"]:
            self.performance_history["outcomes"][-1] = outcome

    def _update_system_state(
        self,
        perception: Dict[str, Any],
        confidence: float,
        action: int,
        tattva_traversal: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Update system's self-awareness (Ahamkara function).

        Monitors and adapts system parameters based on:
        - Perception quality (coherence)
        - Decision confidence
        - Action selection
        - Tattva layer coherence
        """
        # Update coherence (system functioning quality)
        perception_coherence = perception.get("coherence", 0.5)
        self.system_state["coherence"] = (
            0.9 * self.system_state["coherence"] + 0.1 * perception_coherence
        )

        # Update confidence (system self-belief)
        self.system_state["confidence"] = (
            0.9 * self.system_state["confidence"] + 0.1 * confidence
        )

        # Update Tattva coherence tracking if available
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

        # Adapt exploration rate based on coherence
        if self.system_state["coherence"] > 0.8:
            # High coherence = explore more
            self.system_state["exploration_rate"] = min(0.15, 0.1)
        else:
            # Low coherence = explore less (be conservative)
            self.system_state["exploration_rate"] = max(0.05, 0.1)

        # Log system state periodically (with Tattva metrics)
        if self.system_state["total_experiences"] % 100 == 0:
            # Calculate average Tattva coherence
            tattva_coherences = list(self.system_state["tattva_coherence"].values())
            avg_tattva_coherence = (
                float(np.mean(tattva_coherences)) if tattva_coherences else 1.0
            )

            logger.info(
                f"System state (exp={self.system_state['total_experiences']}): "
                f"coherence={self.system_state['coherence']:.2f}, "
                f"confidence={self.system_state['confidence']:.2f}, "
                f"tattva_coherence={avg_tattva_coherence:.2f}"
            )

    def get_system_statistics(self) -> Dict[str, Any]:
        """
        Get comprehensive system statistics including Tattva metrics.
        """
        outcomes = self.performance_history["outcomes"]
        confidences = self.performance_history["confidences"]
        tattva_traversals = self.performance_history.get("tattva_traversals", [])

        stats = {
            "system_state": self.system_state.copy(),
            "memory_stats": self.memory_system.get_statistics(),
            "decision_stats": self.decision_maker.get_statistics(),
            "performance": {},
            "tattva_metrics": {},
        }

        if outcomes:
            stats["performance"] = {
                "avg_outcome": float(np.mean(outcomes)),
                "avg_confidence": float(np.mean(confidences)),
                "win_rate": float(sum(1 for o in outcomes if o > 0) / len(outcomes)),
                "total_trades": len(outcomes),
            }

        # Calculate Tattva metrics
        if tattva_traversals:
            # Average coherence across all traversals
            all_coherences = []
            for traversal in tattva_traversals:
                if "coherence_per_layer" in traversal:
                    all_coherences.extend(traversal["coherence_per_layer"].values())

            if all_coherences:
                stats["tattva_metrics"]["avg_layer_coherence"] = float(
                    np.mean(all_coherences)
                )
                stats["tattva_metrics"]["min_layer_coherence"] = float(
                    np.min(all_coherences)
                )
                stats["tattva_metrics"]["max_layer_coherence"] = float(
                    np.max(all_coherences)
                )

            # Per-layer coherence tracking
            stats["tattva_metrics"]["current_layer_coherence"] = self.system_state[
                "tattva_coherence"
            ].copy()

            # Tattva config info
            stats["tattva_metrics"]["total_layers"] = self.tattva_config.active_tattvas
            stats["tattva_metrics"][
                "traversal_direction"
            ] = self.tattva_config.traversal_direction

        return stats
