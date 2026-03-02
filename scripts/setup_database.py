"""
Database Setup Script - Future-proof database initialization
Ensures all required tables exist before application starts.
"""

import asyncio
import logging
import sys
from contextlib import asynccontextmanager
from typing import List, Optional

from sqlalchemy import (
    Boolean, Column, DateTime, Float, ForeignKey, Index, Integer,
    String, Text, inspect, text
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.sql import func

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("DatabaseSetup")

Base = declarative_base()


# ============================================================================
# CORE TABLES
# ============================================================================

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    tenant_id = Column(String(50), default="demo-tenant")


class AgentExperience(Base):
    __tablename__ = "agent_experiences"

    id = Column(Integer, primary_key=True)
    agent_id = Column(String(50), nullable=False, index=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    state_vector = Column(JSONB, default={})
    next_state_vector = Column(JSONB, default={})
    action = Column(String(50))
    reward = Column(Float, default=0.0)
    done = Column(Boolean, default=False)
    meta_info = Column(JSONB, default={})
    tenant_id = Column(String(50), default="demo-tenant")

    __table_args__ = (
        Index('idx_agent_exp_agent_id', 'agent_id'),
        Index('idx_agent_exp_timestamp', 'timestamp'),
    )


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True)
    order_id = Column(String(100), unique=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"))
    symbol = Column(String(20), nullable=False, index=True)
    side = Column(String(10), nullable=False)  # buy, sell
    order_type = Column(String(20), nullable=False)  # market, limit
    quantity = Column(Float, nullable=False)
    price = Column(Float)
    status = Column(String(20), default="pending")  # pending, filled, cancelled
    exchange_id = Column(String(50))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    tenant_id = Column(String(50), default="demo-tenant")

    __table_args__ = (
        Index('idx_orders_symbol_status', 'symbol', 'status'),
        Index('idx_orders_user_id', 'user_id'),
    )


class Trade(Base):
    __tablename__ = "trades"

    id = Column(Integer, primary_key=True)
    trade_id = Column(String(100), unique=True, nullable=False)
    order_id = Column(String(100), ForeignKey("orders.order_id"))
    symbol = Column(String(20), nullable=False, index=True)
    side = Column(String(10), nullable=False)
    quantity = Column(Float, nullable=False)
    price = Column(Float, nullable=False)
    total_value = Column(Float, nullable=False)
    exchange_id = Column(String(50))
    executed_at = Column(DateTime(timezone=True), server_default=func.now())
    tenant_id = Column(String(50), default="demo-tenant")

    __table_args__ = (
        Index('idx_trades_symbol_executed', 'symbol', 'executed_at'),
    )


class Portfolio(Base):
    __tablename__ = "portfolio"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    total_value = Column(Float, default=0.0)
    cash_balance = Column(Float, default=0.0)
    total_pnl = Column(Float, default=0.0)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    tenant_id = Column(String(50), default="demo-tenant")


class PortfolioHolding(Base):
    __tablename__ = "portfolio_holdings"

    id = Column(Integer, primary_key=True)
    portfolio_id = Column(Integer, ForeignKey("portfolio.id"))
    symbol = Column(String(20), nullable=False)
    quantity = Column(Float, default=0.0)
    avg_cost = Column(Float, default=0.0)
    current_price = Column(Float)
    unrealized_pnl = Column(Float, default=0.0)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    tenant_id = Column(String(50), default="demo-tenant")

    __table_args__ = (
        Index('idx_holdings_portfolio_symbol', 'portfolio_id', 'symbol', unique=True),
    )


class MarketData(Base):
    __tablename__ = "market_data"

    id = Column(Integer, primary_key=True)
    symbol = Column(String(20), nullable=False, index=True)
    price = Column(Float, nullable=False)
    bid = Column(Float)
    ask = Column(Float)
    volume = Column(Float)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    exchange_id = Column(String(50))
    tenant_id = Column(String(50), default="demo-tenant")

    __table_args__ = (
        Index('idx_market_symbol_time', 'symbol', 'timestamp'),
    )


class DecisionAuditLog(Base):
    __tablename__ = "decision_audit_logs"

    id = Column(Integer, primary_key=True)
    decision_id = Column(String(100), unique=True, nullable=False)
    agent_id = Column(String(50), nullable=False)
    decision_type = Column(String(50))
    context = Column(JSONB, default={})
    decision = Column(JSONB, default={})
    outcome = Column(JSONB, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    tenant_id = Column(String(50), default="demo-tenant")

    __table_args__ = (
        Index('idx_audit_agent_time', 'agent_id', 'created_at'),
    )


class RuntimeConfig(Base):
    __tablename__ = "runtime_configs"

    id = Column(Integer, primary_key=True)
    key = Column(String(100), unique=True, nullable=False)
    value = Column(JSONB, default={})
    description = Column(Text)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    updated_by = Column(String(100))
    tenant_id = Column(String(50), default="demo-tenant")


class CircuitBreakerState(Base):
    __tablename__ = "circuit_breaker_state"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)
    state = Column(String(20), default="closed")  # closed, open, half-open
    failure_count = Column(Integer, default=0)
    last_failure_time = Column(DateTime(timezone=True))
    last_success_time = Column(DateTime(timezone=True))
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    tenant_id = Column(String(50), default="demo-tenant")


class TradingModeChange(Base):
    __tablename__ = "trading_mode_changes"

    id = Column(Integer, primary_key=True)
    mode = Column(String(20), nullable=False)  # paper, live, backtest
    reason = Column(Text)
    changed_by = Column(String(100))
    changed_at = Column(DateTime(timezone=True), server_default=func.now())
    tenant_id = Column(String(50), default="demo-tenant")


# ============================================================================
# FEDERATED TRIAD TABLES
# ============================================================================

class ChittaNodeDB(Base):
    __tablename__ = "chitta_nodes"

    id = Column(Integer, primary_key=True)
    node_id = Column(String(64), unique=True, nullable=False, index=True)
    content = Column(Text, nullable=False)
    source = Column(String(50), nullable=False)
    council = Column(String(50), nullable=False)
    element = Column(String(20))
    confidence = Column(Float, default=0.5)
    verified = Column(Boolean, default=False)
    metadata_json = Column(JSONB, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True))
    tenant_id = Column(String(50), default="demo-tenant")

    __table_args__ = (
        Index('idx_chitta_council', 'council'),
        Index('idx_chitta_element', 'element'),
        Index('idx_chitta_created', 'created_at'),
    )


class DeliberationRecordDB(Base):
    __tablename__ = "deliberation_records"

    id = Column(Integer, primary_key=True)
    cycle_id = Column(String(64), nullable=False, index=True)
    iteration = Column(Integer, nullable=False)
    council = Column(String(50), nullable=False)
    perspective = Column(String(50), nullable=False)
    confidence = Column(Float, nullable=False)
    insights = Column(JSONB, default=[])
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    tenant_id = Column(String(50), default="demo-tenant")


class BuddhiDecisionDB(Base):
    __tablename__ = "buddhi_decisions"

    id = Column(Integer, primary_key=True)
    decision_id = Column(String(64), unique=True, nullable=False, index=True)
    action = Column(String(20), nullable=False)  # buy, sell, hold
    confidence = Column(Float, nullable=False)
    rationale = Column(Text, nullable=False)
    supporting = Column(JSONB, default=[])
    opposing = Column(JSONB, default=[])
    contradictions = Column(Integer, default=0)
    council_views = Column(JSONB, default={})
    market_context = Column(JSONB, default={})
    executed = Column(Boolean, default=False)
    execution_result = Column(JSONB)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    tenant_id = Column(String(50), default="demo-tenant")


# ============================================================================
# ASSET TABLES
# ============================================================================

class Asset(Base):
    __tablename__ = "assets"

    id = Column(Integer, primary_key=True)
    symbol = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    asset_type = Column(String(20), default="crypto")  # crypto, stock, forex
    exchange_id = Column(String(50))
    is_active = Column(Boolean, default=True)
    metadata_json = Column(JSONB, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    tenant_id = Column(String(50), default="demo-tenant")


class MarketCandle(Base):
    __tablename__ = "market_candles"

    id = Column(Integer, primary_key=True)
    symbol = Column(String(20), nullable=False, index=True)
    timeframe = Column(String(10), nullable=False)  # 1m, 5m, 1h, 1d
    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    volume = Column(Float, default=0.0)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    tenant_id = Column(String(50), default="demo-tenant")

    __table_args__ = (
        Index('idx_candles_symbol_timeframe_time', 'symbol', 'timeframe', 'timestamp', unique=True),
    )


# ============================================================================
# DATABASE SETUP CLASS
# ============================================================================

class DatabaseSetup:
    """Future-proof database setup manager."""

    ALL_TABLES = [
        User,
        AgentExperience,
        Order,
        Trade,
        Portfolio,
        PortfolioHolding,
        MarketData,
        DecisionAuditLog,
        RuntimeConfig,
        CircuitBreakerState,
        TradingModeChange,
        ChittaNodeDB,
        DeliberationRecordDB,
        BuddhiDecisionDB,
        Asset,
        MarketCandle,
    ]

    def __init__(self, database_url: str):
        self.engine = create_async_engine(
            database_url,
            echo=False,
            future=True,
        )

    async def check_connection(self) -> bool:
        """Check database connection."""
        try:
            async with self.engine.connect() as conn:
                result = await conn.execute(text("SELECT 1"))
                _ = result.scalar()
                logger.info("✅ Database connection successful")
                return True
        except Exception as e:
            logger.error(f"❌ Database connection failed: {e}")
            return False

    async def get_existing_tables(self) -> List[str]:
        """Get list of existing tables."""
        async with self.engine.connect() as conn:
            result = await conn.execute(text(
                "SELECT tablename FROM pg_catalog.pg_tables WHERE schemaname = 'public'"
            ))
            rows = result.fetchall()
            tables = [row[0] for row in rows]
            return tables

    async def create_missing_tables(self) -> List[str]:
        """Create only missing tables (future-proof)."""
        existing = await self.get_existing_tables()
        created = []

        for table_class in self.ALL_TABLES:
            table_name = table_class.__tablename__

            if table_name not in existing:
                try:
                    async with self.engine.begin() as conn:
                        await conn.run_sync(table_class.__table__.create)
                    logger.info(f"✅ Created table: {table_name}")
                    created.append(table_name)
                except Exception as e:
                    logger.error(f"❌ Failed to create {table_name}: {e}")
            else:
                logger.debug(f"Table already exists: {table_name}")

        return created

    async def verify_tables(self) -> bool:
        """Verify all required tables exist."""
        existing = await self.get_existing_tables()
        required = {t.__tablename__ for t in self.ALL_TABLES}
        missing = required - set(existing)

        if missing:
            logger.warning(f"⚠️  Missing tables: {missing}")
            return False
        else:
            logger.info(f"✅ All {len(required)} tables verified")
            return True

    async def run_migrations(self):
        """Run full database setup."""
        logger.info("🚀 Starting database setup...")

        # Check connection
        if not await self.check_connection():
            raise Exception("Cannot connect to database")

        # Get current state
        existing = await self.get_existing_tables()
        logger.info(f"📊 Existing tables: {len(existing)}")

        # Create missing tables
        created = await self.create_missing_tables()
        logger.info(f"📊 Created tables: {len(created)}")

        # Verify
        if await self.verify_tables():
            logger.info("🎉 Database setup complete!")
            return True
        else:
            logger.error("❌ Database setup incomplete")
            return False

    async def reset_database(self):
        """Drop and recreate all tables (USE WITH CAUTION)."""
        logger.warning("⚠️  Dropping all tables...")

        async with self.engine.begin() as conn:
            for table_class in reversed(self.ALL_TABLES):
                try:
                    await conn.run_sync(table_class.__table__.drop, checkfirst=True)
                    logger.info(f"Dropped table: {table_class.__tablename__}")
                except Exception as e:
                    logger.warning(f"Could not drop {table_class.__tablename__}: {e}")

        # Recreate
        return await self.run_migrations()

    async def close(self):
        """Close database connection."""
        await self.engine.dispose()


async def main():
    """Main entry point."""
    import os

    # Get database URL from environment or use default
    database_url = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://trader:trading_secure@localhost:5456/trading_db"
    )

    setup = DatabaseSetup(database_url)

    try:
        success = await setup.run_migrations()
        sys.exit(0 if success else 1)
    except Exception as e:
        logger.error(f"Setup failed: {e}")
        sys.exit(1)
    finally:
        await setup.close()


if __name__ == "__main__":
    asyncio.run(main())
