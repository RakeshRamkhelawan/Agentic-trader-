"""
Database Verification - Async SQLAlchemy Setup.
"""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from typing import AsyncGenerator
import os

# Default to internal docker URL if not set
DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql+asyncpg://app:app_secure@localhost:5455/trading_db"
)

engine = create_async_engine(DATABASE_URL, echo=False)

AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

Base = declarative_base()


# get_db moved to api/deps.py to support dependency injection

# ============================================================================
# SESSION FACTORY (Pillar II: Context-Agnostic DAL)
# ============================================================================
from contextlib import asynccontextmanager
from backend.core.context import set_tenant_context


class SessionManager:
    """
    Factory for creating context-aware database sessions.
    Decouples DB access from HTTP Requests.
    """

    @staticmethod
    @asynccontextmanager
    async def system_admin_session() -> AsyncGenerator[AsyncSession, None]:
        """Provides a session with system_admin privileges (bypasses RLS)."""
        async with AsyncSessionLocal() as session:
            try:
                # 'system_admin' is a special tenant ID that RLS policies allow globally
                await set_tenant_context(session, "system_admin")
                yield session
            finally:
                await session.close()

    @staticmethod
    @asynccontextmanager
    async def tenant_session(tenant_id: str) -> AsyncGenerator[AsyncSession, None]:
        """Provides a session scoped to a specific tenant."""
        async with AsyncSessionLocal() as session:
            try:
                await set_tenant_context(session, tenant_id)
                yield session
            finally:
                await session.close()


# Export context managers for ease of use (e.g. 'async with system_admin_session() as db:')
system_admin_session = SessionManager.system_admin_session
tenant_session = SessionManager.tenant_session
