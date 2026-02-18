"""
Sensory input processing layer.
Receives raw market data and transforms to cognitive representation.
Equivalent to Manas (mind's sensory processing function).
"""

import time
from typing import Any, Dict, List, Optional

import numpy as np

from backend.core.frequency_analysis import VibrationalAnalyzer
from backend.core.navagraha.models import NavagrahaState


class SensoryProcessor:
    """
    First layer of processing: Raw sensation → Structured perception.

    Takes 5 input streams (market data channels) and synthesizes into
    a unified perceptual representation.
    """

    def __init__(self):
        self.vibration_analyzer = VibrationalAnalyzer()
        self.input_channels = 5  # Five data streams
        self.perception_buffer: List[Dict[str, Any]] = []
        self.buffer_size = 144  # 12² for harmonic analysis

    def process_input(
        self,
        price_stream: np.ndarray,
        volume_stream: np.ndarray,
        orderbook_imbalance: float,
        funding_rate: float,
        social_sentiment: float,
        navagraha_state: Optional[NavagrahaState] = None,
    ) -> Dict[str, Any]:
        """
        Process 5 input streams into unified perception.

        Input channels (market "senses"):
        1. Price: Primary signal
        2. Volume: Activity level
        3. Orderbook imbalance: Bid/ask pressure
        4. Funding rate: Derivative appetite
        5. Sentiment: Social/news mood

        Args:
            price_stream: Historical price array
            volume_stream: Historical volume array
            orderbook_imbalance: Current imbalance [-1, 1]
            funding_rate: Current funding [-0.1, 0.1]
            funding_rate: Current funding [-0.1, 0.1]
            social_sentiment: Sentiment score [-1, 1]
            navagraha_state: Optional Vedic astrology state

        Returns:
            Unified perception dictionary with decomposed features
        """
        # 1. Frequency decomposition of primary channels
        price_freq = self.vibration_analyzer.decompose(price_stream)
        volume_freq = self.vibration_analyzer.decompose(volume_stream)

        # 2. Classify state of each channel
        price_state = self.vibration_analyzer.classify_state(price_freq)
        volume_state = self.vibration_analyzer.classify_state(volume_freq)

        # 3. Discretize secondary inputs
        ob_state = self._discretize(orderbook_imbalance, 3)
        funding_state = self._discretize(funding_rate, 3)
        sentiment_state = self._discretize(social_sentiment, 3)

        # 4. Calculate phase alignment (coherence between price and volume)
        phase_alignment = self._calculate_phase_alignment(price_freq, volume_freq)

        # Apply Navagraha Modulations
        coherence = float(price_freq.coherence)
        guna_context = {}

        if navagraha_state:
            # Rahu Kala Penalty: If active, reduce coherence (distortion)
            if navagraha_state.rahu_kala_active:
                coherence *= 0.8  # 20% penalty

            # Inject Guna Context
            guna_context = navagraha_state.guna_distribution.model_dump()

        # 5. Build unified perception
        perception = {
            "primary_frequency": float(price_freq.fundamental),
            "harmonic_profile": [float(h) for h in price_freq.harmonics[:3]],
            "coherence": coherence,
            "phase": float(price_freq.phase),
            # State vector [price, volume, ob, funding, sentiment]
            "state_vector": np.array(
                [price_state, volume_state, ob_state, funding_state, sentiment_state],
                dtype=np.int32,
            ),
            # Cross-channel alignment
            "phase_alignment": phase_alignment,
            # Metadata
            "timestamp": int(time.time_ns()),
            "price_amplitude": float(price_freq.amplitude),
            "volume_amplitude": float(volume_freq.amplitude),
            "guna_context": guna_context,
            "rahu_kala_active": (
                navagraha_state.rahu_kala_active if navagraha_state else False
            ),
        }

        # 6. Buffer for temporal analysis
        self.perception_buffer.append(perception)
        if len(self.perception_buffer) > self.buffer_size:
            self.perception_buffer.pop(0)

        return perception

    def _discretize(self, value: float, levels: int = 3) -> int:
        """
        Discretize continuous value into N categorical levels.

        Converts [-1, 1] → [0, levels-1]
        """
        # Normalize to [0, 1]
        normalized = (value + 1) / 2
        normalized = np.clip(normalized, 0, 1)

        # Map to discrete levels
        level = int(normalized * levels)
        return min(level, levels - 1)

    def _calculate_phase_alignment(
        self, freq1, freq2  # FrequencyDecomposition  # FrequencyDecomposition
    ) -> float:
        """
        Calculate phase alignment between two signals.

        High alignment = signals in sync (good)
        Low alignment = signals conflicting (warning)

        Returns: [0, 1] where 1 = perfectly aligned
        """
        phase_diff = abs(freq1.phase - freq2.phase)

        # Normalize to [0, 1], where 1 = perfectly aligned
        alignment = 1.0 - (phase_diff / np.pi)

        return float(np.clip(alignment, 0, 1))

    def get_perception_history(self, lookback: int = 10) -> List[Dict[str, Any]]:
        """
        Get perception history for temporal analysis.

        Args:
            lookback: Number of recent perceptions to return

        Returns:
            List of perception dictionaries
        """
        return self.perception_buffer[-lookback:]
