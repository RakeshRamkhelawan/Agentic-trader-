"""Tenant middleware for request isolation."""

from typing import Optional, Dict, Any
from contextvars import ContextVar

from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware

from .tenant_manager import tenant_manager, Tenant


# Context variable for current tenant
current_tenant: ContextVar[Optional[Tenant]] = ContextVar("current_tenant", default=None)


class TenantMiddleware(BaseHTTPMiddleware):
    """
    Middleware to extract and validate tenant from requests.
    
    Supports tenant identification via:
    - Subdomain (tenant.example.com)
    - Header (X-Tenant-ID or X-Tenant-Slug)
    - Query parameter (?tenant=slug)
    """
    
    def __init__(self, app, domain_base: str = "example.com"):
        super().__init__(app)
        self.domain_base = domain_base
    
    async def dispatch(self, request: Request, call_next):
        """Process request with tenant context."""
        # Extract tenant
        tenant = await self._extract_tenant(request)
        
        if tenant is None:
            # For public endpoints, allow no tenant
            if request.url.path.startswith(("/api/public", "/health", "/docs")):
                response = await call_next(request)
                return response
            
            raise HTTPException(status_code=404, detail="Tenant not found")
        
        if not tenant.is_active():
            raise HTTPException(
                status_code=403,
                detail=f"Tenant is {tenant.status.value}",
            )
        
        # Set tenant context
        token = current_tenant.set(tenant)
        
        # Add tenant info to request state
        request.state.tenant = tenant
        request.state.tenant_id = tenant.id
        
        try:
            response = await call_next(request)
            
            # Add tenant headers to response
            response.headers["X-Tenant-ID"] = tenant.id
            response.headers["X-Tenant-Slug"] = tenant.slug
            
            return response
        finally:
            # Reset context
            current_tenant.reset(token)
    
    async def _extract_tenant(self, request: Request) -> Optional[Tenant]:
        """Extract tenant from request."""
        # Try subdomain first
        host = request.headers.get("host", "")
        tenant = self._extract_from_subdomain(host)
        if tenant:
            return tenant
        
        # Try header
        tenant_id = request.headers.get("X-Tenant-ID")
        if tenant_id:
            return tenant_manager.get_tenant(tenant_id)
        
        tenant_slug = request.headers.get("X-Tenant-Slug")
        if tenant_slug:
            return tenant_manager.get_tenant_by_slug(tenant_slug)
        
        # Try query parameter
        tenant_slug = request.query_params.get("tenant")
        if tenant_slug:
            return tenant_manager.get_tenant_by_slug(tenant_slug)
        
        return None
    
    def _extract_from_subdomain(self, host: str) -> Optional[Tenant]:
        """Extract tenant from subdomain."""
        if not host or not self.domain_base:
            return None
        
        # Check if host ends with domain base
        if not host.endswith(self.domain_base):
            return None
        
        # Extract subdomain
        subdomain = host.replace(f".{self.domain_base}", "").replace(self.domain_base, "")
        
        # Remove port if present
        if ":" in subdomain:
            subdomain = subdomain.split(":")[0]
        
        if subdomain and subdomain != "www":
            return tenant_manager.get_tenant_by_slug(subdomain)
        
        return None


def get_current_tenant() -> Optional[Tenant]:
    """Get current tenant from context."""
    return current_tenant.get()


def require_tenant() -> Tenant:
    """Require current tenant, raise if not set."""
    tenant = current_tenant.get()
    if tenant is None:
        raise HTTPException(status_code=400, detail="Tenant context required")
    return tenant


class TenantAwareDB:
    """
    Database connection manager that routes to tenant-specific schema.
    
    In production, this would:
    - Route to tenant-specific database/schema
    - Apply row-level security policies
    - Manage connection pooling
    """
    
    def __init__(self):
        self._connections: Dict[str, Any] = {}
    
    def get_connection(self, tenant_id: str):
        """Get database connection for tenant."""
        # In production, implement actual schema/database routing
        # For now, return default connection
        return self._connections.get("default")
    
    def execute_with_tenant(self, query: str, tenant_id: str, params: tuple = ()):
        """Execute query with tenant isolation."""
        # Add tenant filter to query
        # In production, use proper parameterized queries
        tenant_aware_query = query.replace(
            "WHERE ",
            f"WHERE tenant_id = '{tenant_id}' AND "
        )
        return tenant_aware_query, params
