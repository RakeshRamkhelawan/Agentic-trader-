"""Tenant administration functionality."""

from datetime import datetime
from typing import Any

from backend.rbac.roles import Permission, role_manager
from backend.tenancy.tenant_manager import tenant_manager


class TenantAdmin:
    """
    Admin functions for tenant management.

    Provides:
    - User management within tenant
    - Usage monitoring
    - Settings management
    - Billing overview
    """

    def __init__(self, tenant_id: str):
        self.tenant_id = tenant_id
        self.tenant = tenant_manager.get_tenant(tenant_id)

    def get_dashboard_data(self) -> dict[str, Any]:
        """Get dashboard data for tenant admin."""
        if not self.tenant:
            return {"error": "Tenant not found"}

        usage = tenant_manager.get_usage(self.tenant_id)
        users = role_manager.list_tenant_users(self.tenant_id)

        return {
            "tenant": self.tenant.to_dict(),
            "usage": usage,
            "users": {
                "total": len(users),
                "list": users,
            },
            "subscription": {
                "tier": self.tenant.tier.value,
                "status": self.tenant.status.value,
                "created_at": self.tenant.created_at.isoformat(),
                "activated_at": self.tenant.activated_at.isoformat() if self.tenant.activated_at else None,
            },
        }

    def invite_user(self, email: str, role_id: str, invited_by: str) -> dict[str, Any]:
        """Invite a new user to the tenant."""
        # Check user limit
        current_users = len(role_manager.list_tenant_users(self.tenant_id))
        if not tenant_manager.check_limit(self.tenant_id, "max_users", current_users):
            return {"error": "User limit reached"}

        # In production, send email invitation
        # For now, return invitation token
        import uuid
        invitation_token = str(uuid.uuid4())

        return {
            "success": True,
            "email": email,
            "role": role_id,
            "invitation_token": invitation_token,
            "expires_at": "24 hours",
        }

    def remove_user(self, user_id: str) -> bool:
        """Remove user from tenant."""
        return role_manager.remove_user_role(self.tenant_id, user_id)

    def update_user_role(self, user_id: str, new_role_id: str) -> bool:
        """Update user's role in tenant."""
        return role_manager.assign_role(self.tenant_id, user_id, new_role_id)

    def get_usage_report(self, period: str = "monthly") -> dict[str, Any]:
        """Get detailed usage report."""
        usage = tenant_manager.get_usage(self.tenant_id)

        return {
            "period": period,
            "generated_at": datetime.utcnow().isoformat(),
            "usage": usage,
            "recommendations": self._generate_recommendations(usage),
        }

    def _generate_recommendations(self, usage: dict) -> list[str]:
        """Generate usage recommendations."""
        recommendations = []

        utilization = usage.get("utilization", {})

        if utilization.get("users", 0) > 0.8:
            recommendations.append("Consider upgrading tier - approaching user limit")

        if utilization.get("tournaments", 0) > 0.9:
            recommendations.append("Tournament usage high - archive old tournaments")

        return recommendations

    def update_settings(self, settings: dict[str, Any]) -> bool:
        """Update tenant settings."""
        if not self.tenant:
            return False

        # Update allowed settings
        if "features" in settings:
            self.tenant.config.features.update(settings["features"])

        if "security_settings" in settings:
            self.tenant.config.security_settings.update(settings["security_settings"])

        return True

    def get_audit_log(self, limit: int = 100) -> list[dict[str, Any]]:
        """Get audit log for tenant."""
        # In production, query actual audit log
        # For now, return mock data
        return [
            {
                "timestamp": datetime.utcnow().isoformat(),
                "user_id": "user_123",
                "action": "USER_INVITED",
                "details": {"email": "newuser@example.com"},
            }
        ]


class TenantAdminAPI:
    """API endpoints for tenant admin (to be used with FastAPI)."""

    @staticmethod
    def get_endpoints():
        """Get FastAPI router with tenant admin endpoints."""
        from fastapi import APIRouter, HTTPException

        router = APIRouter(prefix="/admin/tenant", tags=["Tenant Admin"])

        @router.get("/dashboard")
        async def dashboard(request):
            tenant_id = request.state.tenant_id
            admin = TenantAdmin(tenant_id)
            return admin.get_dashboard_data()

        @router.post("/users/invite")
        async def invite_user(request, email: str, role_id: str):
            tenant_id = request.state.tenant_id
            user_id = request.headers.get("X-User-ID")

            # Check permission
            if not role_manager.check_permission(tenant_id, user_id, Permission.ADMIN_USERS):
                raise HTTPException(status_code=403, detail="Permission denied")

            admin = TenantAdmin(tenant_id)
            return admin.invite_user(email, role_id, user_id)

        @router.get("/usage")
        async def usage_report(request, period: str = "monthly"):
            tenant_id = request.state.tenant_id
            admin = TenantAdmin(tenant_id)
            return admin.get_usage_report(period)

        return router
