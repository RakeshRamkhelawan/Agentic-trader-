from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import logging

logger = logging.getLogger(__name__)


async def set_tenant_context(db: AsyncSession, tenant_id: str):
    """
    Sets the current tenant context for RLS.
    Must be called at the start of any transaction/session usage.
    """
    try:
        # Use set_config with is_local=True so it applies only to current transaction
        # However, since we might reuse sessions, we want it for the session lifetime?
        # Actually, is_local=False sets it for the session duration, which is safer for our scoped dependency.
        await db.execute(
            text(f"SELECT set_config('app.current_tenant', '{tenant_id}', false)")
        )
    except Exception as e:
        # In development, the RLS parameter may not be configured in PostgreSQL
        # Log warning but don't fail the request
        logger.warning(f"RLS context not set (dev mode?): {e}")
