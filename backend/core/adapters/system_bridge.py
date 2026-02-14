"""
Cognitive Bridge - Adapter tussen OODA types en SystemIdentity.

Vertaalt nieuwe Pydantic Observation modellen naar de numpy arrays
die de bestaande SystemIdentity verwacht.
"""

import logging
import numpy as np
from typing import Dict, Any

from backend.core.system_identity import SystemIdentity
from backend.core.schemas.ooda_types import Observation

logger = logging.getLogger(__name__)


class CognitiveBridge:
    """
    Bridge tussen OODA Pydantic types en bestaande cognitive core.

    Converteert moderne Observation objects naar de numpy-gebaseerde
    interface van SystemIdentity, waardoor backward compatibility
    behouden blijft terwijl we nieuwe type-safe interfaces introduceren.
    """

    def __init__(self, system_identity: SystemIdentity, window_size: int = 20):
        """
        Initialiseer de bridge.

        Args:
            system_identity: Bestaande SystemIdentity instance
            window_size: Aantal samples voor price/volume arrays
        """
        self.system_identity = system_identity
        self.window_size = window_size

        # Sliding window buffers voor tijdseries data
        self._price_buffer = []
        self._volume_buffer = []

        logger.info(f"CognitiveBridge initialized (window_size={window_size})")

    async def process_observation(self, obs: Observation) -> float:
        """
        Verwerk een Observation door de cognitieve core.

        Converteert de Pydantic Observation naar numpy arrays en roept
        SystemIdentity.process_market_cycle() aan. Extraheert de
        confidence score uit het resultaat.

        Args:
            obs: Observation object met marktdata

        Returns:
            Confidence score van de cognitive core (0.0-1.0)

        Raises:
            ValueError: Als observation data ongeldig is
        """
        try:
            # Update buffers met nieuwe data
            self._price_buffer.append(obs.price)
            self._volume_buffer.append(obs.volume)

            # Trim buffers naar window_size
            if len(self._price_buffer) > self.window_size:
                self._price_buffer = self._price_buffer[-self.window_size :]
            if len(self._volume_buffer) > self.window_size:
                self._volume_buffer = self._volume_buffer[-self.window_size :]

            # Converteer naar numpy arrays
            price_array = np.array(self._price_buffer, dtype=np.float32)
            volume_array = np.array(self._volume_buffer, dtype=np.float32)

            # Pad arrays als we nog niet genoeg data hebben
            if len(price_array) < self.window_size:
                pad_size = self.window_size - len(price_array)
                price_array = np.pad(price_array, (pad_size, 0), mode="edge")
                volume_array = np.pad(volume_array, (pad_size, 0), mode="edge")

            # Extract orderbook imbalance
            orderbook_imbalance = self._extract_orderbook_imbalance(obs.orderbook)

            # Call SystemIdentity
            result = await self.system_identity.process_market_cycle(
                price_data=price_array,
                volume_data=volume_array,
                orderbook_imbalance=orderbook_imbalance,
                funding_rate=obs.funding_rate or 0.0,
                social_sentiment=obs.social_sentiment,
            )

            # Extract confidence from result
            confidence = result.get("confidence", 0.0)

            logger.debug(
                f"Processed observation: {obs.symbol} @ {obs.price}, "
                f"core_confidence={confidence:.3f}"
            )

            # Update SystemIdentity stats
            stats = self.system_identity.get_system_statistics()
            logger.debug(
                f"System stats: experiences={stats.get('total_experiences')}, "
                f"avg_coherence={stats.get('avg_coherence', 0):.3f}"
            )

            return float(confidence)

        except Exception as e:
            logger.error(f"Failed to process observation: {e}", exc_info=True)
            # Return low confidence on error (fail-safe)
            return 0.0

    def _extract_orderbook_imbalance(self, orderbook: Dict[str, Any]) -> float:
        """
        Bereken orderbook imbalance van bids/asks.

        Imbalance = (bid_volume - ask_volume) / (bid_volume + ask_volume)
        Range: [-1, 1]

        Args:
            orderbook: Dict met 'bids' en 'asks' arrays

        Returns:
            Imbalance score in [-1, 1], of 0.0 bij ontbrekende data
        """
        try:
            bids = orderbook.get("bids", [])
            asks = orderbook.get("asks", [])

            if not bids or not asks:
                return 0.0

            # Som volumes (assuming format [[price, volume], ...])
            bid_volume = sum(float(bid[1]) for bid in bids if len(bid) >= 2)
            ask_volume = sum(float(ask[1]) for ask in asks if len(ask) >= 2)

            total_volume = bid_volume + ask_volume
            if total_volume == 0:
                return 0.0

            imbalance = (bid_volume - ask_volume) / total_volume

            # Clamp to [-1, 1]
            return max(-1.0, min(1.0, imbalance))

        except Exception as e:
            logger.warning(f"Failed to extract orderbook imbalance: {e}")
            return 0.0

    def reset_buffers(self):
        """Reset price/volume buffers (bijv. bij symbol switch)."""
        self._price_buffer.clear()
        self._volume_buffer.clear()
        logger.info("Buffers reset")

    def get_buffer_stats(self) -> Dict[str, Any]:
        """
        Krijg statistieken over de buffers.

        Returns:
            Dict met buffer sizes en statistieken
        """
        return {
            "price_buffer_size": len(self._price_buffer),
            "volume_buffer_size": len(self._volume_buffer),
            "price_latest": self._price_buffer[-1] if self._price_buffer else None,
            "volume_latest": self._volume_buffer[-1] if self._volume_buffer else None,
        }
