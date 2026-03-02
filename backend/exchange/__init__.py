# NOTE: Legacy imports removed during Week 8 cleanup
# See: docs/adr/ADR-008-unified-execution-schema.md

"""
Exchange Module for Agentic Trader Platform.

This module provides a unified interface for trading across multiple
exchanges with consistent APIs, risk management, and portfolio tracking.

Quick Start:
    >>> from backend.exchange.exchange_factory_v2 import ExchangeFactoryV2
    >>> from backend.execution.order_executor import OrderExecutor
    >>> from backend.execution.portfolio_manager import PortfolioManager
    >>>
    >>> # Create exchange
    >>> factory = ExchangeFactoryV2()
    >>> bitvavo = await factory.create_exchange("bitvavo")
    >>>
    >>> # Place order
    >>> executor = OrderExecutor(exchange_adapter=bitvavo)
    >>> outcome = await executor.execute_trade(execution_plan)
"""

# New factory (v2) - USE THIS
from backend.exchange.exchange_factory_v2 import (
    ExchangeFactoryV2,
    create_default_exchanges_v2,
    get_exchange_factory_v2,
)

# Legacy factory (deprecated, will be removed in future)
# Only imports the class/functions, not the legacy connectors
# from backend.exchange.exchange_factory import (
#     ExchangeFactory,
#     create_default_exchanges,
#     get_exchange_factory,
# )

__all__ = [
    # New v2 components - RECOMMENDED
    "ExchangeFactoryV2",
    "create_default_exchanges_v2",
    "get_exchange_factory_v2",
]
