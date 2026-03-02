"""Platform-level administration for SaaS operators."""

from datetime import datetime
from typing import Any

from backend.tenancy.tenant_manager import TenantStatus, TenantTier, tenant_manager


class PlatformAdmin:
    """
    Platform administration for SaaS operators.

    Features:
    - Tenant lifecycle management
    - System-wide monitoring
    - Billing oversight
    - Support tools
    """

    def __init__(self):
        pass

    def get_overview(self) -> dict[str, Any]:
        """Get platform-wide overview."""
        stats = tenant_manager.get_stats()

        return {
            "generated_at": datetime.utcnow().isoformat(),
            "tenants": stats,
            "health": self._get_system_health(),
        }

    def _get_system_health(self) -> dict[str, Any]:
        """Get system health status."""
        # In production, check actual services
        return {
            "status": "healthy",
            "services": {
                "api": "operational",
                "database": "operational",
                "cache": "operational",
                "websocket": "operational",
            },
        }

    def list_tenants(
        self,
        status: str | None = None,
        tier: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """List all tenants with filtering."""
        status_enum = TenantStatus(status) if status else None
        tier_enum = TenantTier(tier) if tier else None

        tenants = tenant_manager.list_tenants(
            status=status_enum,
            tier=tier_enum,
            limit=limit + offset,
        )

        return [t.to_dict() for t in tenants[offset:offset + limit]]

    def get_tenant_details(self, tenant_id: str) -> dict[str, Any] | None:
        """Get detailed information about a tenant."""
        tenant = tenant_manager.get_tenant(tenant_id)
        if not tenant:
            return None

        usage = tenant_manager.get_usage(tenant_id)

        return {
            **tenant.to_dict(),
            "usage": usage,
            "estimated_mrr": self._calculate_mrr(tenant),
        }

    def _calculate_mrr(self, tenant) -> float:
        """Calculate monthly recurring revenue for tenant."""
        pricing = {
            TenantTier.STARTUP: 49.0,
            TenantTier.PROFESSIONAL: 199.0,
            TenantTier.ENTERPRISE: 999.0,
            TenantTier.CUSTOM: 0.0,  # Custom pricing
        }
        return pricing.get(tenant.tier, 0.0)

    def create_tenant(
        self,
        name: str,
        admin_email: str,
        tier: str = "startup",
        slug: str | None = None,
    ) -> dict[str, Any]:
        """Create a new tenant."""
        tier_enum = TenantTier(tier)

        tenant = tenant_manager.create_tenant(
            name=name,
            admin_email=admin_email,
            tier=tier_enum,
            slug=slug,
        )

        return {
            "success": True,
            "tenant": tenant.to_dict(),
            "next_steps": [
                "Send activation email to admin",
                "Configure white-label branding",
                "Set up custom domain (if applicable)",
            ],
        }

    def activate_tenant(self, tenant_id: str) -> bool:
        """Activate a pending tenant."""
        tenant = tenant_manager.activate_tenant(tenant_id)
        return tenant is not None

    def suspend_tenant(self, tenant_id: str, reason: str = "") -> bool:
        """Suspend a tenant."""
        tenant = tenant_manager.suspend_tenant(tenant_id, reason)
        return tenant is not None

    def cancel_tenant(self, tenant_id: str) -> bool:
        """Cancel a tenant subscription."""
        tenant = tenant_manager.cancel_tenant(tenant_id)
        return tenant is not None

    def update_tenant_tier(self, tenant_id: str, tier: str) -> bool:
        """Update tenant subscription tier."""
        tier_enum = TenantTier(tier)
        tenant = tenant_manager.update_tier(tenant_id, tier_enum)
        return tenant is not None

    def get_billing_overview(self) -> dict[str, Any]:
        """Get billing overview across all tenants."""
        tenants = tenant_manager.list_tenants(status=TenantStatus.ACTIVE)

        total_mrr = sum(self._calculate_mrr(t) for t in tenants)
        by_tier = {}

        for tier in TenantTier:
            tier_tenants = [t for t in tenants if t.tier == tier]
            by_tier[tier.value] = {
                "count": len(tier_tenants),
                "mrr": sum(self._calculate_mrr(t) for t in tier_tenants),
            }

        return {
            "generated_at": datetime.utcnow().isoformat(),
            "total_mrr": total_mrr,
            "active_tenants": len(tenants),
            "by_tier": by_tier,
        }

    def get_support_data(self, tenant_id: str) -> dict[str, Any]:
        """Get support data for troubleshooting."""
        tenant = tenant_manager.get_tenant(tenant_id)
        if not tenant:
            return {"error": "Tenant not found"}

        return {
            "tenant": tenant.to_dict(),
            "usage": tenant_manager.get_usage(tenant_id),
            "recent_activity": [],  # In production, query activity log
            "flags": self._check_support_flags(tenant),
        }

    def _check_support_flags(self, tenant) -> list[str]:
        """Check for support flags on tenant."""
        flags = []

        if tenant.status == TenantStatus.SUSPENDED:
            flags.append("Account suspended")

        usage = tenant_manager.get_usage(tenant.id)
        utilization = usage.get("utilization", {})

        if utilization.get("users", 0) > 0.95:
            flags.append("Near user limit")

        return flags

    def impersonate_tenant(self, tenant_id: str) -> dict[str, str]:
        """Generate impersonation token for support."""
        import uuid

        token = str(uuid.uuid4())

        # In production, store token with expiry
        return {
            "impersonation_token": token,
            "tenant_id": tenant_id,
            "expires_in": "1 hour",
            "warning": "Use for support purposes only",
        }


class PlatformAdminAPI:
    """API endpoints for platform admin."""

    @staticmethod
    def get_endpoints():
        """Get FastAPI router with platform admin endpoints."""
        from fastapi import APIRouter, HTTPException

        router = APIRouter(prefix="/admin/platform", tags=["Platform Admin"])
        admin = PlatformAdmin()

        @router.get("/overview")
        async def overview():
            return admin.get_overview()

        @router.get("/tenants")
        async def list_tenants(status: str | None = None, tier: str | None = None):
            return admin.list_tenants(status=status, tier=tier)

        @router.get("/tenants/{tenant_id}")
        async def get_tenant(tenant_id: str):
            tenant = admin.get_tenant_details(tenant_id)
            if not tenant:
                raise HTTPException(status_code=404, detail="Tenant not found")
            return tenant

        @router.post("/tenants/{tenant_id}/activate")
        async def activate_tenant(tenant_id: str):
            if not admin.activate_tenant(tenant_id):
                raise HTTPException(status_code=400, detail="Failed to activate tenant")
            return {"success": True}

        @router.post("/tenants/{tenant_id}/suspend")
        async def suspend_tenant(tenant_id: str, reason: str = ""):
            if not admin.suspend_tenant(tenant_id, reason):
                raise HTTPException(status_code=400, detail="Failed to suspend tenant")
            return {"success": True}

        @router.get("/billing")
        async def billing_overview():
            return admin.get_billing_overview()

        return router
