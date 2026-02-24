"""
Database Verification - Async SQLAlchemy Setup.
"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy import event, text
from sqlalchemy.engine import Engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from backend.core.auth.context import get_current_tenant_optional
from backend.core.config.settings import settings
from backend.core.context import set_tenant_context

DATABASE_URL = settings.DATABASE_URL

engine = create_async_engine(DATABASE_URL, echo=False)

AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

Base = declarative_base()


# get_db moved to api/deps.py to support dependency injection

# ============================================================================
# SESSION FACTORY (Pillar II: Context-Agnostic DAL)
# ============================================================================


class SessionManager:
    """
    Factory for creating context-aware database sessions.
    Decouples DB access from HTTP Requests.
    """

    @staticmethod
    @asynccontextmanager
    async def system_admin_session() -> AsyncGenerator[AsyncSession]:
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
    async def tenant_session(tenant_id: str) -> AsyncGenerator[AsyncSession]:
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

# ============================================================================
# RLS EVENT LISTENER
# ============================================================================


@event.listens_for(Engine, "before_cursor_execute")
def receive_before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    """
    Inject tenant_id into the PostgreSQL session variable before any query.
    This enables Row Level Security (RLS) policies to filter data automatically.
    """
    tenant_id = get_current_tenant_optional()

    # Prevent infinite recursion: If the statement is already setting the tenant, do nothing.
    stmt_str = str(statement).lower()
    if "set_config" in stmt_str and "app.current_tenant" in stmt_str:
        return
    if stmt_str.strip().startswith("set app.current_tenant"):
        return

    if tenant_id:
        # Use set_config for safe parameter binding with asyncpg
        conn.execute(
            text("SELECT set_config('app.current_tenant', :tenant_id, false)"),
            {"tenant_id": tenant_id},
        )
    else:
        # If no tenant context (e.g. background job without context),
        # ensure no leakage or strict default.
        # Ideally, background jobs should set a context too.
        pass
