"""Role and permission management."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class Permission(Enum):
    """System permissions."""
    # User management
    USER_CREATE = "user:create"
    USER_READ = "user:read"
    USER_UPDATE = "user:update"
    USER_DELETE = "user:delete"

    # Tournament management
    TOURNAMENT_CREATE = "tournament:create"
    TOURNAMENT_READ = "tournament:read"
    TOURNAMENT_UPDATE = "tournament:update"
    TOURNAMENT_DELETE = "tournament:delete"
    TOURNAMENT_MANAGE = "tournament:manage"  # Start/end tournaments

    # Strategy management
    STRATEGY_CREATE = "strategy:create"
    STRATEGY_READ = "strategy:read"
    STRATEGY_UPDATE = "strategy:update"
    STRATEGY_DELETE = "strategy:delete"
    STRATEGY_SHARE = "strategy:share"

    # Trading
    TRADE_EXECUTE = "trade:execute"
    TRADE_READ = "trade:read"
    TRADE_MANAGE = "trade:manage"  # Cancel/modify

    # Analytics
    ANALYTICS_READ = "analytics:read"
    ANALYTICS_EXPORT = "analytics:export"

    # Administration
    ADMIN_DASHBOARD = "admin:dashboard"
    ADMIN_USERS = "admin:users"
    ADMIN_SETTINGS = "admin:settings"
    ADMIN_BILLING = "admin:billing"

    # Tenant administration (platform level)
    PLATFORM_ADMIN = "platform:admin"
    PLATFORM_MANAGE_TENANTS = "platform:manage_tenants"
    PLATFORM_BILLING = "platform:billing"


@dataclass
class Role:
    """A role with associated permissions."""
    id: str
    name: str
    description: str
    permissions: set[Permission] = field(default_factory=set)
    is_system: bool = True  # System roles cannot be deleted

    def has_permission(self, permission: Permission) -> bool:
        """Check if role has permission."""
        return permission in self.permissions

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "permissions": [p.value for p in self.permissions],
            "is_system": self.is_system,
        }


class RoleManager:
    """
    Manages roles and permissions.

    Provides pre-configured system roles:
    - Super Admin: Full platform access
    - Tenant Admin: Full tenant administration
    - Manager: Can manage users and tournaments
    - Trader: Can trade and share strategies
    - Viewer: Read-only access
    """

    def __init__(self):
        self._roles: dict[str, Role] = {}
        self._user_roles: dict[str, dict[str, str]] = {}  # tenant_id -> {user_id -> role_id}
        self._init_system_roles()

    def _init_system_roles(self) -> None:
        """Initialize system roles."""
        # Platform Super Admin
        self._roles["super_admin"] = Role(
            id="super_admin",
            name="Super Admin",
            description="Full platform access",
            permissions=set(Permission),
            is_system=True,
        )

        # Tenant Administrator
        self._roles["tenant_admin"] = Role(
            id="tenant_admin",
            name="Tenant Administrator",
            description="Full access to tenant resources",
            permissions={
                Permission.USER_CREATE,
                Permission.USER_READ,
                Permission.USER_UPDATE,
                Permission.USER_DELETE,
                Permission.TOURNAMENT_CREATE,
                Permission.TOURNAMENT_READ,
                Permission.TOURNAMENT_UPDATE,
                Permission.TOURNAMENT_DELETE,
                Permission.TOURNAMENT_MANAGE,
                Permission.STRATEGY_CREATE,
                Permission.STRATEGY_READ,
                Permission.STRATEGY_UPDATE,
                Permission.STRATEGY_DELETE,
                Permission.STRATEGY_SHARE,
                Permission.TRADE_EXECUTE,
                Permission.TRADE_READ,
                Permission.TRADE_MANAGE,
                Permission.ANALYTICS_READ,
                Permission.ANALYTICS_EXPORT,
                Permission.ADMIN_DASHBOARD,
                Permission.ADMIN_USERS,
                Permission.ADMIN_SETTINGS,
                Permission.ADMIN_BILLING,
            },
            is_system=True,
        )

        # Manager
        self._roles["manager"] = Role(
            id="manager",
            name="Manager",
            description="Can manage users and tournaments",
            permissions={
                Permission.USER_CREATE,
                Permission.USER_READ,
                Permission.USER_UPDATE,
                Permission.TOURNAMENT_CREATE,
                Permission.TOURNAMENT_READ,
                Permission.TOURNAMENT_UPDATE,
                Permission.TOURNAMENT_MANAGE,
                Permission.STRATEGY_READ,
                Permission.STRATEGY_SHARE,
                Permission.TRADE_READ,
                Permission.ANALYTICS_READ,
                Permission.ANALYTICS_EXPORT,
            },
            is_system=True,
        )

        # Trader
        self._roles["trader"] = Role(
            id="trader",
            name="Trader",
            description="Can trade and share strategies",
            permissions={
                Permission.TOURNAMENT_READ,
                Permission.STRATEGY_CREATE,
                Permission.STRATEGY_READ,
                Permission.STRATEGY_UPDATE,
                Permission.STRATEGY_DELETE,
                Permission.STRATEGY_SHARE,
                Permission.TRADE_EXECUTE,
                Permission.TRADE_READ,
                Permission.ANALYTICS_READ,
            },
            is_system=True,
        )

        # Viewer
        self._roles["viewer"] = Role(
            id="viewer",
            name="Viewer",
            description="Read-only access",
            permissions={
                Permission.TOURNAMENT_READ,
                Permission.STRATEGY_READ,
                Permission.TRADE_READ,
                Permission.ANALYTICS_READ,
            },
            is_system=True,
        )

        # Platform Admin (for SaaS operators)
        self._roles["platform_admin"] = Role(
            id="platform_admin",
            name="Platform Admin",
            description="Manage platform and tenants",
            permissions={
                Permission.PLATFORM_ADMIN,
                Permission.PLATFORM_MANAGE_TENANTS,
                Permission.PLATFORM_BILLING,
                Permission.USER_READ,
            },
            is_system=True,
        )

    def create_custom_role(
        self,
        role_id: str,
        name: str,
        description: str,
        permissions: set[Permission],
    ) -> Role:
        """Create a custom role."""
        if role_id in self._roles:
            raise ValueError(f"Role {role_id} already exists")

        role = Role(
            id=role_id,
            name=name,
            description=description,
            permissions=permissions,
            is_system=False,
        )

        self._roles[role_id] = role
        return role

    def get_role(self, role_id: str) -> Role | None:
        """Get role by ID."""
        return self._roles.get(role_id)

    def list_roles(self, include_system: bool = True) -> list[Role]:
        """List all roles."""
        roles = list(self._roles.values())
        if not include_system:
            roles = [r for r in roles if not r.is_system]
        return roles

    def delete_custom_role(self, role_id: str) -> bool:
        """Delete a custom role."""
        role = self._roles.get(role_id)
        if role and not role.is_system:
            del self._roles[role_id]
            return True
        return False

    def assign_role(self, tenant_id: str, user_id: str, role_id: str) -> bool:
        """Assign role to user in tenant."""
        if role_id not in self._roles:
            return False

        if tenant_id not in self._user_roles:
            self._user_roles[tenant_id] = {}

        self._user_roles[tenant_id][user_id] = role_id
        return True

    def get_user_role(self, tenant_id: str, user_id: str) -> Role | None:
        """Get role assigned to user in tenant."""
        role_id = self._user_roles.get(tenant_id, {}).get(user_id)
        if role_id:
            return self._roles.get(role_id)
        return None

    def remove_user_role(self, tenant_id: str, user_id: str) -> bool:
        """Remove role from user in tenant."""
        if tenant_id in self._user_roles and user_id in self._user_roles[tenant_id]:
            del self._user_roles[tenant_id][user_id]
            return True
        return False

    def check_permission(
        self,
        tenant_id: str,
        user_id: str,
        permission: Permission,
    ) -> bool:
        """Check if user has permission."""
        role = self.get_user_role(tenant_id, user_id)
        if role:
            return role.has_permission(permission)
        return False

    def get_user_permissions(self, tenant_id: str, user_id: str) -> set[Permission]:
        """Get all permissions for user."""
        role = self.get_user_role(tenant_id, user_id)
        if role:
            return role.permissions
        return set()

    def list_tenant_users(self, tenant_id: str) -> list[dict[str, Any]]:
        """List all users in tenant with their roles."""
        users = []
        for user_id, role_id in self._user_roles.get(tenant_id, {}).items():
            role = self._roles.get(role_id)
            users.append({
                "user_id": user_id,
                "role_id": role_id,
                "role_name": role.name if role else "Unknown",
            })
        return users


# Global role manager
role_manager = RoleManager()
