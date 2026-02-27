"""
Role-Based Access Control (RBAC) system.

Features:
- Roles and permissions
- Resource-level access control
- Tenant-scoped permissions
"""

from .access_control import AccessControl, TenantResourceAccess, require_permission
from .roles import Permission, Role, RoleManager, role_manager

__all__ = [
    "Role",
    "RoleManager",
    "Permission",
    "role_manager",
    "AccessControl",
    "require_permission",
    "TenantResourceAccess",
]
