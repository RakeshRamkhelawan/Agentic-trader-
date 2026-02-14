"""
Unified Model Registry for Agentic Trader.

This file aggregates all SQLAlchemy models to provide a single entry point
for Alembic migrations and Repository access.
"""

from backend.core.database import Base
# Governance
from backend.governance.decision_audit import DecisionAuditLog
# Learning & Knowledge
from backend.models.agent_experience import AgentExperience
from backend.models.config import RuntimeConfig
# Trading & Market
from backend.models.market_data import MarketCandle, MarketTick
from backend.models.orders import Order, OrderStatus
# Identity & Access
from backend.models.user_settings import (APIKey, User, UserPreferences,
                                          UserProfile, UserSecurity)
from backend.rag.vector_memory import TradingKnowledge

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
