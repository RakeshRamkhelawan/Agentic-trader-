# NOTE: Legacy imports removed during Week 8 cleanup
# See: docs/adr/ADR-008-unified-execution-schema.md

"""
Exchange Factory for creating and managing exchange connectors.

⚠️ DEPRECATED: This module is deprecated and will be removed in a future version.
Use ExchangeFactoryV2 from backend.exchange.exchange_factory_v2 instead.

See: docs/adr/ADR-008-unified-execution-schema.md
"""

from __future__ import annotations

import logging
import warnings
from typing import Any

# Deprecation warning
warnings.warn(
    "ExchangeFactory is deprecated. Use ExchangeFactoryV2 from "
    "backend.exchange.exchange_factory_v2 instead. "
    "See ADR-008 for migration guide.",
    DeprecationWarning,
    stacklevel=2
)

logger = logging.getLogger(__name__)


class ExchangeFactory:
    """
    Factory for creating and managing exchange connectors.

    ⚠️ DEPRECATED: Use ExchangeFactoryV2 instead.

    This factory is kept for backwards compatibility but will be removed
    in a future version. All functionality has been migrated to
    ExchangeFactoryV2 with the new adapter architecture.
    """

    def __init__(self):
        """Initialize exchange factory."""
        logger.warning(
            "[ExchangeFactory] DEPRECATED: Use ExchangeFactoryV2 instead. "
            "See ADR-008 for migration guide."
        )
        self._exchanges: dict[str, Any] = {}

    def _register_default_types(self) -> None:
        """Register default exchange connector types."""
        logger.warning(
            "[ExchangeFactory] Legacy connectors removed. "
            "Use ExchangeFactoryV2 with BitvavoAdapter/RevolutXAdapter."
        )

    async def create_exchange(
        self,
        exchange_type: str,
        exchange_id: str | None = None,
        config: dict[str, Any] | None = None,
        auto_connect: bool = True
    ) -> Any | None:
        """
        Create and initialize an exchange connector.

        ⚠️ DEPRECATED: This method no longer works with legacy connectors.
        Use ExchangeFactoryV2.create_exchange() instead.
        """
        raise NotImplementedError(
            "Legacy connectors removed. Use ExchangeFactoryV2 instead. "
            "See: backend.exchange.exchange_factory_v2"
        )

    def get_exchange(self, exchange_id: str) -> Any | None:
        """Get exchange by ID."""
        return self._exchanges.get(exchange_id)

    def list_exchanges(self) -> list[str]:
        """List all managed exchange IDs."""
        return list(self._exchanges.keys())

    def get_all_exchanges(self) -> dict[str, Any]:
        """Get all managed exchanges."""
        return self._exchanges.copy()


# Global factory instance
_global_factory: ExchangeFactory | None = None


def get_exchange_factory() -> ExchangeFactory:
    """Get or create global exchange factory."""
    global _global_factory
    if _global_factory is None:
        _global_factory = ExchangeFactory()
    return _global_factory


async def create_default_exchanges() -> dict[str, Any]:
    """
    Create default exchanges from environment configuration.

    ⚠️ DEPRECATED: Use create_default_exchanges_v2() instead.
    """
    raise NotImplementedError(
        "Legacy connectors removed. Use create_default_exchanges_v2() instead. "
        "See: backend.exchange.exchange_factory_v2"
    )
