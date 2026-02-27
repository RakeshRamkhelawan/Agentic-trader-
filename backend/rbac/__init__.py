"""
Role-Based Access Control (RBAC) system.

Features:
- Roles and permissions
- Resource-level access control
- Tenant-scoped permissions
"""

from .roles import Role, RoleManager, Permission, role_manager
from .access_control import AccessControl, require_permission, TenantResourceAccess

__all__ = [
    "Role",
    "RoleManager",
    "Permission",
    "role_manager",
    "AccessControl",
    "require_permission",
    "TenantResourceAccess",
]
