"""Multi-tenancy manager for enterprise SaaS."""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any


class TenantStatus(Enum):
    """Tenant account statuses."""
    PENDING = "pending"      # Awaiting activation
    ACTIVE = "active"        # Fully operational
    SUSPENDED = "suspended"  # Temporarily disabled
    CANCELLED = "cancelled"  # Terminated


class TenantTier(Enum):
    """Tenant subscription tiers."""
    STARTUP = "startup"      # Small teams
    PROFESSIONAL = "professional"  # Growing teams
    ENTERPRISE = "enterprise"  # Large organizations
    CUSTOM = "custom"        # Custom pricing


@dataclass
class TenantLimits:
    """Resource limits for a tenant."""
    max_users: int = 10
    max_competitors: int = 50
    max_tournaments: int = 10
    max_strategies: int = 100
    max_api_calls_per_min: int = 1000
    storage_gb: int = 10
    data_retention_days: int = 90


@dataclass
class TenantConfig:
    """Tenant configuration."""
    features: Dict[str, bool] = field(default_factory=dict)
    integrations: Dict[str, Any] = field(default_factory=dict)
    security_settings: Dict[str, Any] = field(default_factory=dict)
    custom_fields: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Tenant:
    """A tenant/organization in the system."""
    id: str
    name: str
    slug: str  # URL-friendly identifier
    status: TenantStatus
    tier: TenantTier
    
    # Contact info
    admin_email: str
    billing_email: Optional[str] = None
    
    # Configuration
    limits: TenantLimits = field(default_factory=TenantLimits)
    config: TenantConfig = field(default_factory=TenantConfig)
    
    # Usage tracking
    created_at: datetime = field(default_factory=datetime.utcnow)
    activated_at: Optional[datetime] = None
    last_activity_at: Optional[datetime] = None
    
    # Billing
    stripe_customer_id: Optional[str] = None
    subscription_id: Optional[str] = None
    
    def is_active(self) -> bool:
        """Check if tenant is active."""
        return self.status == TenantStatus.ACTIVE
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "slug": self.slug,
            "status": self.status.value,
            "tier": self.tier.value,
            "admin_email": self.admin_email,
            "billing_email": self.billing_email,
            "limits": {
                "max_users": self.limits.max_users,
                "max_competitors": self.limits.max_competitors,
                "max_tournaments": self.limits.max_tournaments,
                "max_strategies": self.limits.max_strategies,
                "max_api_calls_per_min": self.limits.max_api_calls_per_min,
                "storage_gb": self.limits.storage_gb,
                "data_retention_days": self.limits.data_retention_days,
            },
            "created_at": self.created_at.isoformat(),
            "activated_at": self.activated_at.isoformat() if self.activated_at else None,
        }


class TenantManager:
    """
    Manages tenants in a multi-tenant SaaS architecture.
    
    Features:
    - Tenant CRUD operations
    - Subdomain/slug management
    - Usage tracking
    - Resource limits enforcement
    """
    
    # Default limits by tier
    TIER_LIMITS = {
        TenantTier.STARTUP: TenantLimits(
            max_users=10,
            max_competitors=50,
            max_tournaments=10,
            max_strategies=100,
            max_api_calls_per_min=1000,
            storage_gb=10,
            data_retention_days=90,
        ),
        TenantTier.PROFESSIONAL: TenantLimits(
            max_users=50,
            max_competitors=200,
            max_tournaments=50,
            max_strategies=500,
            max_api_calls_per_min=5000,
            storage_gb=50,
            data_retention_days=180,
        ),
        TenantTier.ENTERPRISE: TenantLimits(
            max_users=500,
            max_competitors=1000,
            max_tournaments=200,
            max_strategies=2000,
            max_api_calls_per_min=50000,
            storage_gb=500,
            data_retention_days=365,
        ),
    }
    
    def __init__(self):
        self._tenants: Dict[str, Tenant] = {}  # id -> tenant
        self._slug_index: Dict[str, str] = {}  # slug -> tenant_id
        self._email_index: Dict[str, str] = {}  # admin_email -> tenant_id
        self._usage_stats: Dict[str, Dict] = {}  # tenant_id -> usage stats
    
    def create_tenant(
        self,
        name: str,
        admin_email: str,
        tier: TenantTier = TenantTier.STARTUP,
        slug: Optional[str] = None,
    ) -> Tenant:
        """
        Create a new tenant.
        
        Args:
            name: Organization name
            admin_email: Admin contact email
            tier: Subscription tier
            slug: Custom slug (optional)
            
        Returns:
            Created tenant
        """
        # Generate unique ID
        tenant_id = str(uuid.uuid4())
        
        # Generate or validate slug
        if slug is None:
            slug = self._generate_slug(name)
        else:
            slug = self._validate_slug(slug)
        
        # Check for duplicate email
        if admin_email in self._email_index:
            raise ValueError(f"Tenant with email {admin_email} already exists")
        
        # Create tenant
        tenant = Tenant(
            id=tenant_id,
            name=name,
            slug=slug,
            status=TenantStatus.PENDING,
            tier=tier,
            admin_email=admin_email,
            limits=self.TIER_LIMITS.get(tier, TenantLimits()).__copy__(),
        )
        
        # Store tenant
        self._tenants[tenant_id] = tenant
        self._slug_index[slug] = tenant_id
        self._email_index[admin_email] = tenant_id
        
        return tenant
    
    def _generate_slug(self, name: str) -> str:
        """Generate URL-friendly slug from name."""
        import re
        
        # Convert to lowercase, replace spaces with hyphens
        slug = re.sub(r'[^\w\s-]', '', name.lower())
        slug = re.sub(r'[-\s]+', '-', slug)
        
        # Ensure unique
        base_slug = slug
        counter = 1
        while slug in self._slug_index:
            slug = f"{base_slug}-{counter}"
            counter += 1
        
        return slug
    
    def _validate_slug(self, slug: str) -> str:
        """Validate and ensure unique slug."""
        import re
        
        # Validate format
        if not re.match(r'^[\w-]+$', slug):
            raise ValueError("Slug can only contain letters, numbers, hyphens")
        
        # Ensure unique
        if slug in self._slug_index:
            raise ValueError(f"Slug '{slug}' is already taken")
        
        return slug.lower()
    
    def get_tenant(self, tenant_id: str) -> Optional[Tenant]:
        """Get tenant by ID."""
        return self._tenants.get(tenant_id)
    
    def get_tenant_by_slug(self, slug: str) -> Optional[Tenant]:
        """Get tenant by slug."""
        tenant_id = self._slug_index.get(slug.lower())
        if tenant_id:
            return self._tenants.get(tenant_id)
        return None
    
    def get_tenant_by_email(self, email: str) -> Optional[Tenant]:
        """Get tenant by admin email."""
        tenant_id = self._email_index.get(email)
        if tenant_id:
            return self._tenants.get(tenant_id)
        return None
    
    def activate_tenant(self, tenant_id: str) -> Optional[Tenant]:
        """Activate a pending tenant."""
        tenant = self._tenants.get(tenant_id)
        if tenant and tenant.status == TenantStatus.PENDING:
            tenant.status = TenantStatus.ACTIVE
            tenant.activated_at = datetime.utcnow()
            return tenant
        return None
    
    def suspend_tenant(self, tenant_id: str, reason: str = "") -> Optional[Tenant]:
        """Suspend a tenant."""
        tenant = self._tenants.get(tenant_id)
        if tenant:
            tenant.status = TenantStatus.SUSPENDED
            tenant.config.custom_fields["suspension_reason"] = reason
            return tenant
        return None
    
    def cancel_tenant(self, tenant_id: str) -> Optional[Tenant]:
        """Cancel a tenant (soft delete)."""
        tenant = self._tenants.get(tenant_id)
        if tenant:
            tenant.status = TenantStatus.CANCELLED
            return tenant
        return None
    
    def update_tier(self, tenant_id: str, tier: TenantTier) -> Optional[Tenant]:
        """Update tenant subscription tier."""
        tenant = self._tenants.get(tenant_id)
        if tenant:
            tenant.tier = tier
            tenant.limits = self.TIER_LIMITS.get(tier, TenantLimits()).__copy__()
            return tenant
        return None
    
    def update_limits(self, tenant_id: str, **kwargs) -> Optional[Tenant]:
        """Update tenant resource limits (for custom tiers)."""
        tenant = self._tenants.get(tenant_id)
        if tenant:
            for key, value in kwargs.items():
                if hasattr(tenant.limits, key):
                    setattr(tenant.limits, key, value)
            return tenant
        return None
    
    def record_usage(self, tenant_id: str, metric: str, value: int = 1) -> None:
        """Record usage metric for tenant."""
        if tenant_id not in self._usage_stats:
            self._usage_stats[tenant_id] = {}
        
        if metric not in self._usage_stats[tenant_id]:
            self._usage_stats[tenant_id][metric] = 0
        
        self._usage_stats[tenant_id][metric] += value
    
    def get_usage(self, tenant_id: str) -> Dict[str, Any]:
        """Get usage statistics for tenant."""
        tenant = self._tenants.get(tenant_id)
        if not tenant:
            return {}
        
        usage = self._usage_stats.get(tenant_id, {})
        
        return {
            "tenant_id": tenant_id,
            "current_usage": usage,
            "limits": {
                "max_users": tenant.limits.max_users,
                "max_competitors": tenant.limits.max_competitors,
                "max_tournaments": tenant.limits.max_tournaments,
            },
            "utilization": {
                "users": usage.get("users", 0) / tenant.limits.max_users if tenant.limits.max_users > 0 else 0,
                "competitors": usage.get("competitors", 0) / tenant.limits.max_competitors if tenant.limits.max_competitors > 0 else 0,
                "tournaments": usage.get("tournaments", 0) / tenant.limits.max_tournaments if tenant.limits.max_tournaments > 0 else 0,
            },
        }
    
    def check_limit(self, tenant_id: str, metric: str, current_value: int) -> bool:
        """Check if tenant is within limits."""
        tenant = self._tenants.get(tenant_id)
        if not tenant:
            return False
        
        limit = getattr(tenant.limits, metric, None)
        if limit is None:
            return True
        
        return current_value < limit
    
    def list_tenants(
        self,
        status: Optional[TenantStatus] = None,
        tier: Optional[TenantTier] = None,
        limit: int = 100,
    ) -> List[Tenant]:
        """List tenants with optional filters."""
        tenants = list(self._tenants.values())
        
        if status:
            tenants = [t for t in tenants if t.status == status]
        
        if tier:
            tenants = [t for t in tenants if t.tier == tier]
        
        return tenants[:limit]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get tenant system statistics."""
        total = len(self._tenants)
        by_status = {}
        by_tier = {}
        
        for tenant in self._tenants.values():
            by_status[tenant.status.value] = by_status.get(tenant.status.value, 0) + 1
            by_tier[tenant.tier.value] = by_tier.get(tenant.tier.value, 0) + 1
        
        return {
            "total_tenants": total,
            "by_status": by_status,
            "by_tier": by_tier,
        }


# Global tenant manager
tenant_manager = TenantManager()
