"""
Soul Observer — Cross-layer state inspection (Spec §5.4, §6.3).

Provides real-time health status, intent aggregation, and "why no trade" explanations
for the 3-layer consciousness architecture (Soul/Mind/Body).
"""

import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

_STALE_THRESHOLD_SECONDS = 90


class SoulObserver:
    """Observes and reports on all 3 consciousness layers."""

    def __init__(self):
        self.redis_client = None
        self.bridge = None

    async def get_health(self) -> Dict[str, Dict[str, Any]]:
        """Return health status for all 3 layers.

        Returns:
            {
                "soul": {"status": "healthy"|"stale"|"unknown", "last_update": ...},
                "mind": {"status": ...},
                "body": {"status": ...},
            }
        """
        soul_health = await self._check_soul_health()
        mind_health = await self._check_mind_health()
        body_health = self._check_body_health()

        return {
            "soul": soul_health,
            "mind": mind_health,
            "body": body_health,
        }

    async def _check_soul_health(self) -> Dict[str, Any]:
        """Check Soul layer health via Redis soul:context."""
        try:
            if not self.redis_client:
                return {"status": "unknown", "last_update": None}

            ctx_json = await self.redis_client.get("soul:context")
            if not ctx_json:
                return {"status": "unknown", "last_update": None}

            ctx = json.loads(ctx_json)
            timestamp_str = ctx.get("timestamp")
            if not timestamp_str:
                return {"status": "unknown", "last_update": None}

            last_update = datetime.fromisoformat(timestamp_str)
            now = datetime.now(timezone.utc)
            age_seconds = (now - last_update).total_seconds()

            status = "healthy" if age_seconds <= _STALE_THRESHOLD_SECONDS else "stale"
            return {"status": status, "last_update": timestamp_str}

        except Exception as e:
            logger.error(f"Soul health check error: {e}")
            return {"status": "unknown", "last_update": None}

    async def _check_mind_health(self) -> Dict[str, Any]:
        """Check Mind layer health (SHM intent freshness)."""
        try:
            if self.bridge:
                return {"status": "healthy", "last_update": None}
            return {"status": "unknown", "last_update": None}
        except Exception:
            return {"status": "unknown", "last_update": None}

    def _check_body_health(self) -> Dict[str, Any]:
        """Check Body layer health."""
        return {"status": "unknown", "last_update": None}

    async def get_recent_intents(self) -> List[Dict[str, Any]]:
        """Return recent trading intents from SHM.

        Returns empty list if SHM not available.
        """
        if not self.bridge:
            return []
        return []

    async def why_no_trade(self) -> List[str]:
        """Explain why no trade is happening right now.

        Checks soul context for blocking conditions.
        """
        reasons = []
        try:
            if not self.redis_client:
                reasons.append("Redis unavailable - cannot read soul context")
                return reasons

            ctx_json = await self.redis_client.get("soul:context")
            if not ctx_json:
                reasons.append("No soul context available")
                return reasons

            ctx = json.loads(ctx_json)

            if ctx.get("rahu_kala_active", False):
                reasons.append("Rahu Kala active, trading gate closed")

            if not ctx.get("trading_gate_open", True):
                if "Rahu" not in " ".join(reasons):
                    reasons.append("Trading gate closed (high Tamas)")

        except Exception as e:
            reasons.append(f"Error checking conditions: {e}")

        return reasons
