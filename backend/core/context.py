import logging

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


async def set_tenant_context(db: AsyncSession, tenant_id: str):
    """
    Sets the current tenant context for RLS.
    Must be called at the start of any transaction/session usage.

    SECURITY: This function is FAIL-CLOSED. If the tenant context cannot be set,
    a RuntimeError is raised to prevent queries from running without RLS enforcement.
    This prevents cross-tenant data leakage.
    """
    if not tenant_id or not tenant_id.strip():
        raise ValueError(
            "tenant_id must be a non-empty string. "
            "Cannot proceed without tenant context for RLS enforcement."
        )

    try:
        # Use set_config with is_local=False so it applies for the session duration,
        # which is safer for our scoped dependency.
        await db.execute(
            text("SELECT set_config('app.current_tenant', :tenant_id, false)"),
            {"tenant_id": tenant_id},
        )
    except Exception as e:
        # FAIL-CLOSED: Never silently continue without RLS context.
        # This prevents cross-tenant data leakage via connection pooling.
        logger.error("CRITICAL: Failed to set RLS tenant context for tenant '%s': %s", tenant_id, e)
        raise RuntimeError(
            f"Failed to set RLS tenant context for tenant '{tenant_id}'. "
            f"Refusing to proceed without data isolation. Error: {e}"
        ) from e
