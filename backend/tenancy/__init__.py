"""
Multi-tenancy system for enterprise SaaS.

Features:
- Tenant isolation (data, configuration)
- Organization management
- White-label customization
- Usage metering
"""

from .tenant_manager import (
    Tenant,
    TenantConfig,
    TenantLimits,
    TenantManager,
    TenantStatus,
    TenantTier,
    tenant_manager,
)
from .tenant_middleware import TenantMiddleware, current_tenant, get_current_tenant, require_tenant
from .white_label import BrandingConfig, WhiteLabelManager, white_label_manager

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
