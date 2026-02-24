"""
Tenant Middleware - ADR-005
"""

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from .context import TenantContext

PUBLIC_PATHS = {"/health", "/docs", "/openapi.json"}


class TenantMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.path in PUBLIC_PATHS:
            return await call_next(request)

        jwt_claims = getattr(request.state, "jwt_claims", {})
        tenant_ctx = TenantContext.from_jwt(jwt_claims)
        tenant_ctx.set_current()
        request.state.tenant = tenant_ctx

        response = await call_next(request)
        response.headers["X-Tenant-ID"] = tenant_ctx.tenant_id
        return response
