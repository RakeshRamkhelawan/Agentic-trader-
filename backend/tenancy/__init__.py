"""
Multi-tenancy system for enterprise SaaS.

Features:
- Tenant isolation (data, configuration)
- Organization management
- White-label customization
- Usage metering
"""

from .tenant_manager import TenantManager, Tenant, TenantConfig, TenantLimits, TenantStatus, TenantTier, tenant_manager
from .tenant_middleware import TenantMiddleware, get_current_tenant, require_tenant, current_tenant
from .white_label import WhiteLabelManager, BrandingConfig, white_label_manager

__all__ = [
    "TenantManager",
    "Tenant",
    "TenantConfig",
    "TenantLimits",
    "TenantStatus",
    "TenantTier",
    "tenant_manager",
    "TenantMiddleware",
    "get_current_tenant",
    "require_tenant",
    "current_tenant",
    "WhiteLabelManager",
    "BrandingConfig",
    "white_label_manager",
]
