"""
Exchange Factory V2 - Using New Adapter Architecture.

Week 3-4 of Exchange Integration Refactor.

Replaces legacy connectors with new adapter pattern:
- BitvavoConnector → BitvavoAdapter
- RevolutConnector → RevolutXAdapter

Maintains backward compatibility through adapter wrapper.
"""

from __future__ import annotations

import logging
from typing import Any

from backend.core.config.settings import settings
from backend.execution.bitvavo_adapter import BitvavoAdapter
from backend.execution.revolut_x_adapter import RevolutXAdapter

logger = logging.getLogger(__name__)


class ExchangeFactoryV2:
    """
    Factory for creating and managing exchange adapters.

    Uses the new adapter architecture with:
    - BitvavoAdapter (CCXT-based)
    - RevolutXAdapter (REST API)

    Example:
        >>> factory = ExchangeFactoryV2()
        >>> bitvavo = await factory.create_exchange("bitvavo")
        >>> revolut = await factory.create_exchange("revolut")
    """

    _exchange_types: dict[str, Any] = {}

    def __init__(self):
        """Initialize exchange factory."""
        self._exchanges: dict[str, Any] = {}
        self._default_configs: dict[str, dict[str, Any]] = {}

        # Register default exchange types
        self._register_default_types()

        logger.info("[ExchangeFactoryV2] Initialized")

    def _register_default_types(self) -> None:
        """Register default exchange adapter types."""
        self.register_exchange_type("bitvavo", BitvavoAdapter)
        self.register_exchange_type("revolut", RevolutXAdapter)
        logger.info("[ExchangeFactoryV2] Registered default exchange types")

    @classmethod
    def register_exchange_type(cls, name: str, adapter_class: Any) -> None:
        """
        Register an exchange adapter type.

        Args:
            name: Exchange type identifier
            adapter_class: Exchange adapter class
        """
        cls._exchange_types[name.lower()] = adapter_class
        logger.info(f"[ExchangeFactoryV2] Registered: {name}")

    async def create_exchange(
        self,
        exchange_type: str,
        exchange_id: str | None = None,
        config: dict[str, Any] | None = None,
        auto_connect: bool = True,
    ) -> Any | None:
        """
        Create and initialize an exchange adapter.

        Args:
            exchange_type: Type of exchange (bitvavo, revolut)
            exchange_id: Unique identifier for this instance
            config: Configuration dictionary
            auto_connect: Whether to connect immediately

        Returns:
            Initialized exchange adapter or None if failed
        """
        exchange_type = exchange_type.lower()

        # Get adapter class
        adapter_class = self._exchange_types.get(exchange_type)
        if not adapter_class:
            logger.error(f"[ExchangeFactoryV2] Unknown type: {exchange_type}")
            return None

        # Generate exchange ID if not provided
        if exchange_id is None:
            existing = [k for k in self._exchanges.keys() if k.startswith(exchange_type)]
            exchange_id = f"{exchange_type}_{len(existing) + 1}"

        try:
            # Create adapter instance
            if exchange_type == "bitvavo":
                adapter = BitvavoAdapter()
            elif exchange_type == "revolut":
                adapter = RevolutXAdapter()
            else:
                adapter = adapter_class()

            # Initialize if requested
            if auto_connect:
                if exchange_type == "bitvavo":
                    success = await adapter.initialize()
                elif exchange_type == "revolut":
                    success = await adapter.connect()
                else:
                    success = True

                if not success:
                    logger.error(f"[ExchangeFactoryV2] Failed to init {exchange_id}")
                    return None

            # Store instance
            self._exchanges[exchange_id] = adapter

            logger.info(f"[ExchangeFactoryV2] Created: {exchange_id} ({exchange_type})")
            return adapter

        except Exception as e:
            logger.error(f"[ExchangeFactoryV2] Failed to create {exchange_type}: {e}")
            return None

    def get_exchange(self, exchange_id: str) -> Any | None:
        """Get exchange by ID."""
        return self._exchanges.get(exchange_id)

    def list_exchanges(self) -> list[str]:
        """List all managed exchange IDs."""
        return list(self._exchanges.keys())

    def get_all_exchanges(self) -> dict[str, Any]:
        """Get all managed exchanges."""
        return self._exchanges.copy()

    async def close_exchange(self, exchange_id: str) -> bool:
        """Close and remove an exchange."""
        adapter = self._exchanges.get(exchange_id)
        if not adapter:
            return False

        try:
            # Close based on adapter type
            if hasattr(adapter, "close"):
                await adapter.close()

            del self._exchanges[exchange_id]
            logger.info(f"[ExchangeFactoryV2] Closed: {exchange_id}")
            return True
        except Exception as e:
            logger.error(f"[ExchangeFactoryV2] Error closing {exchange_id}: {e}")
            return False

    async def close_all(self) -> None:
        """Close all managed exchanges."""
        for exchange_id in list(self._exchanges.keys()):
            await self.close_exchange(exchange_id)

    @staticmethod
    def get_available_types() -> list[str]:
        """Get list of available exchange types."""
        return list(ExchangeFactoryV2._exchange_types.keys())


# Global factory instance
_global_factory_v2: ExchangeFactoryV2 | None = None


def get_exchange_factory_v2() -> ExchangeFactoryV2:
    """Get or create global exchange factory."""
    global _global_factory_v2
    if _global_factory_v2 is None:
        _global_factory_v2 = ExchangeFactoryV2()
    return _global_factory_v2


async def create_default_exchanges_v2() -> dict[str, Any]:
    """
    Create default exchanges from environment configuration.

    Returns:
        Dictionary of created exchanges
    """
    factory = get_exchange_factory_v2()
    exchanges = {}

    # Create Bitvavo if configured
    if settings.BITVAVO_API_KEY:
        exchange = await factory.create_exchange("bitvavo")
        if exchange:
            exchanges["bitvavo"] = exchange
            logger.info("[ExchangeFactoryV2] Bitvavo configured")

    # Create Revolut if configured
    if settings.REVOLUT_API_KEY:
        exchange = await factory.create_exchange("revolut")
        if exchange:
            exchanges["revolut"] = exchange
            logger.info("[ExchangeFactoryV2] Revolut configured")

    return exchanges
