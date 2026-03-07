"""
Unified Model Registry for Agentic Trader.

This file aggregates all SQLAlchemy models to provide a single entry point
for Alembic migrations and Repository access.
"""

# Assets
from backend.assets.models import Asset
from backend.core.database import Base

# Learning & Knowledge
from backend.db_models.agent_experience import AgentExperience
from backend.db_models.config import RuntimeConfig

# Trading & Market
from backend.db_models.market_data import MarketCandle, MarketTick
from backend.db_models.orders import Order, OrderStatus

# Paper Trading Models (V18)
from backend.db_models.paper_trading import (
    AgentPerformance,
    ChittaExperience,
    PaperTrade,
    PaperTradingAnalytics,
    PaperTradingSession,
)

# Identity & Access
from backend.db_models.user_settings import APIKey, User, UserPreferences, UserProfile, UserSecurity

# Governance
from backend.governance.decision_audit import DecisionAuditLog
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
    "Asset",
    # Paper Trading Models
    "PaperTradingSession",
    "PaperTrade",
    "PaperTradingAnalytics",
    "AgentPerformance",
    "ChittaExperience",
]
