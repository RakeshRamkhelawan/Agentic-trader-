"""
Exchange Module for Agentic Trader Platform.

This module provides a unified interface for trading across multiple
exchanges with consistent APIs, risk management, and portfolio tracking.

Quick Start:
    >>> from backend.exchange import ExchangeFactory, OrderManager, PortfolioManager
    >>>
    >>> # Create exchange
    >>> factory = ExchangeFactory()
    >>> bitvavo = await factory.create_exchange("bitvavo")
    >>>
    >>> # Place order
    >>> order_manager = OrderManager()
    >>> order_manager.register_exchange("bitvavo", bitvavo)
    >>> order = await order_manager.place_order(order_request)
"""

# Base classes
from backend.exchange.base_exchange import (
    Balance,
    BaseExchange,
    ExchangeCapabilities,
    Order,
    OrderBook,
    OrderRequest,
    OrderSide,
    OrderStatus,
    OrderType,
    Position,
    Symbol,
    Ticker,
    TimeInForce,
    Trade,
)

# Connectors
from backend.exchange.connectors.bitvavo_connector import BitvavoConnector
from backend.exchange.connectors.revolut_connector import RevolutConnector

# Factory
from backend.exchange.exchange_factory import ExchangeFactory, create_default_exchanges

# Managers
from backend.exchange.order_manager import OrderManager, OrderRoute
from backend.exchange.portfolio_manager import PortfolioManager, PortfolioSnapshot
from backend.exchange.risk.order_validator import (
    OrderRiskValidator,
    RiskLimits,
    ValidationResult,
    ValidationStatus,
)

__all__ = [
    # Base classes
    "BaseExchange",
    "Balance",
    "Order",
    "OrderBook",
    "OrderRequest",
    "OrderSide",
    "OrderStatus",
    "OrderType",
    "Position",
    "Symbol",
    "Ticker",
    "Trade",
    "ExchangeCapabilities",
    "TimeInForce",
    # Managers
    "OrderManager",
    "OrderRoute",
    "PortfolioManager",
    "PortfolioSnapshot",
    "OrderRiskValidator",
    "RiskLimits",
    "ValidationResult",
    "ValidationStatus",
    "OrderBook",
    # Factory
    "ExchangeFactory",
    "create_default_exchanges",
    # Connectors
    "BitvavoConnector",
    "RevolutConnector",
]
