"""
Unified Model Registry for Agentic Trader.

This file aggregates all SQLAlchemy models to provide a single entry point
for Alembic migrations and Repository access.
"""

from backend.core.database import Base

# Identity & Access
from backend.models.user_settings import (
    User,
    UserPreferences,
    UserProfile,
    UserSecurity,
    APIKey,
)

# Trading & Market
from backend.models.market_data import MarketCandle, MarketTick
from backend.models.orders import Order, OrderStatus

# Learning & Knowledge
from backend.models.agent_experience import AgentExperience
from backend.rag.vector_memory import TradingKnowledge

# Governance
from backend.governance.decision_audit import DecisionAuditLog
from backend.models.config import RuntimeConfig

__all__ = [
    "Base",
    "User",
    "UserPreferences",
    "UserProfile",
    "UserSecurity",
    "APIKey",
    "MarketCandle",
    "MarketTick",
    "Order",
    "OrderStatus",
    "AgentExperience",
    "TradingKnowledge",
    "DecisionAuditLog",
    "RuntimeConfig",
]
