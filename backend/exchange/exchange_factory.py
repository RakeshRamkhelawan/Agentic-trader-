"""
Exchange Factory for creating and managing exchange connectors.

Provides a centralized way to create, configure, and manage exchange
instances with proper initialization and error handling.

Usage:
    >>> from backend.exchange.exchange_factory import ExchangeFactory
    >>>
    >>> factory = ExchangeFactory()
    >>> bitvavo = await factory.create_exchange("bitvavo", sandbox=True)
    >>> revolut = await factory.create_exchange("revolut")
    >>>
    >>> # Get all active exchanges
    >>> exchanges = factory.get_all_exchanges()
"""

from __future__ import annotations

import logging
from typing import Any

from backend.exchange.base_exchange import BaseExchange

logger = logging.getLogger(__name__)


class ExchangeFactory:
    """
    Factory for creating and managing exchange connectors.

    This factory handles:
    - Exchange instantiation
    - Configuration management
    - Connection lifecycle
    - Sandbox vs live mode

    Example:
        >>> factory = ExchangeFactory()
        >>>
        >>> # Create exchange with auto-connect
        >>> exchange = await factory.create_exchange(
        ...     "bitvavo",
        ...     config={"sandbox": True}
        ... )
        >>>
        >>> # List all managed exchanges
        >>> for ex_id in factory.list_exchanges():
        ...     print(f"{ex_id}: {factory.get_exchange(ex_id)}")
    """

    # Registry of exchange types
    _exchange_types: dict[str, Any] = {}

    def __init__(self):
        """Initialize exchange factory."""
        self._exchanges: dict[str, BaseExchange] = {}
        self._default_configs: dict[str, dict[str, Any]] = {}

        # Register default exchange types
        self._register_default_types()

        logger.info("[ExchangeFactory] Initialized")

    def _register_default_types(self) -> None:
        """Register default exchange connector types."""
        try:
            from backend.exchange.connectors.bitvavo_connector import BitvavoConnector
            self.register_exchange_type("bitvavo", BitvavoConnector)
        except ImportError as e:
            logger.warning(f"[ExchangeFactory] Could not register Bitvavo: {e}")

        try:
            from backend.exchange.connectors.revolut_connector import RevolutConnector
            self.register_exchange_type("revolut", RevolutConnector)
        except ImportError as e:
            logger.warning(f"[ExchangeFactory] Could not register Revolut: {e}")

    @classmethod
    def register_exchange_type(cls, name: str, exchange_class: Any) -> None:
        """
        Register an exchange connector type.

        Args:
            name: Exchange type identifier
            exchange_class: Exchange connector class
        """
        cls._exchange_types[name.lower()] = exchange_class
        logger.info(f"[ExchangeFactory] Registered exchange type: {name}")

    async def create_exchange(
        self,
        exchange_type: str,
        exchange_id: str | None = None,
        config: dict[str, Any] | None = None,
        auto_connect: bool = True
    ) -> BaseExchange | None:
        """
        Create and initialize an exchange connector.

        Args:
            exchange_type: Type of exchange (bitvavo, revolut, etc.)
            exchange_id: Unique identifier for this instance (default: auto-generated)
            config: Configuration dictionary
            auto_connect: Whether to connect immediately

        Returns:
            Initialized exchange connector or None if failed
        """
        exchange_type = exchange_type.lower()

        # Get exchange class
        exchange_class = self._exchange_types.get(exchange_type)
        if not exchange_class:
            logger.error(f"[ExchangeFactory] Unknown exchange type: {exchange_type}")
            logger.error(f"[ExchangeFactory] Available types: {list(self._exchange_types.keys())}")
            return None

        # Generate exchange ID if not provided
        if exchange_id is None:
            existing = [k for k in self._exchanges.keys() if k.startswith(exchange_type)]
            exchange_id = f"{exchange_type}_{len(existing) + 1}"

        # Merge with default config
        merged_config = self._default_configs.get(exchange_type, {}).copy()
        if config:
            merged_config.update(config)

        # Create instance
        try:
            exchange = exchange_class(exchange_id=exchange_id, config=merged_config)

            # Connect if requested
            if auto_connect:
                success = await exchange.connect()
                if not success:
                    logger.error(f"[ExchangeFactory] Failed to connect to {exchange_id}")
                    return None

            # Store instance
            self._exchanges[exchange_id] = exchange

            logger.info(f"[ExchangeFactory] Created exchange: {exchange_id} ({exchange_type})")
            return exchange

        except Exception as e:
            logger.error(f"[ExchangeFactory] Failed to create {exchange_type}: {e}")
            return None

    def get_exchange(self, exchange_id: str) -> BaseExchange | None:
        """Get exchange by ID."""
        return self._exchanges.get(exchange_id)

    def list_exchanges(self) -> list[str]:
        """List all managed exchange IDs."""
        return list(self._exchanges.keys())

    def get_all_exchanges(self) -> dict[str, BaseExchange]:
        """Get all managed exchanges."""
        return self._exchanges.copy()

    async def close_exchange(self, exchange_id: str) -> bool:
        """
        Close and remove an exchange.

        Args:
            exchange_id: Exchange to close

        Returns:
            True if closed successfully
        """
        exchange = self._exchanges.get(exchange_id)
        if not exchange:
            return False

        try:
            await exchange.disconnect()
            del self._exchanges[exchange_id]
            logger.info(f"[ExchangeFactory] Closed exchange: {exchange_id}")
            return True
        except Exception as e:
            logger.error(f"[ExchangeFactory] Error closing {exchange_id}: {e}")
            return False

    async def close_all(self) -> None:
        """Close all managed exchanges."""
        for exchange_id in list(self._exchanges.keys()):
            await self.close_exchange(exchange_id)

    def set_default_config(self, exchange_type: str, config: dict[str, Any]) -> None:
        """
        Set default configuration for an exchange type.

        Args:
            exchange_type: Exchange type
            config: Default configuration
        """
        self._default_configs[exchange_type.lower()] = config
        logger.info(f"[ExchangeFactory] Set default config for {exchange_type}")

    @staticmethod
    def get_available_types() -> list[str]:
        """Get list of available exchange types."""
        return list(ExchangeFactory._exchange_types.keys())


# Global factory instance
_global_factory: ExchangeFactory | None = None


def get_exchange_factory() -> ExchangeFactory:
    """Get or create global exchange factory."""
    global _global_factory
    if _global_factory is None:
        _global_factory = ExchangeFactory()
    return _global_factory


async def create_default_exchanges() -> dict[str, BaseExchange]:
    """
    Create default exchanges from environment configuration.

    Returns:
        Dictionary of created exchanges
    """
    from backend.core.config.settings import settings

    factory = get_exchange_factory()
    exchanges = {}

    # Create Bitvavo if configured
    if settings.BITVAVO_API_KEY:
        exchange = await factory.create_exchange(
            "bitvavo",
            config={
                "api_key": settings.BITVAVO_API_KEY,
                "api_secret": settings.BITVAVO_API_SECRET,
                "sandbox": settings.BITVAVO_SANDBOX,
            }
        )
        if exchange:
            exchanges["bitvavo"] = exchange

    # Create Revolut if configured
    if settings.REVOLUT_API_KEY:
        exchange = await factory.create_exchange(
            "revolut",
            config={
                "api_key": settings.REVOLUT_API_KEY,
                "private_key_path": settings.REVOLUT_PRIVATE_KEY_PATH,
                "sandbox": settings.REVOLUT_SANDBOX,
            }
        )
        if exchange:
            exchanges["revolut"] = exchange

    return exchanges
