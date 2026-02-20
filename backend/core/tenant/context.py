"""
Tenant Context Management - ADR-005
"""
import contextvars
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

_tenant_context: contextvars.ContextVar[
    Optional["TenantContext"]
] = contextvars.ContextVar("tenant_context", default=None)


@dataclass(frozen=True)
class TenantQuotas:
    requests_per_minute: int
    orders_per_day: int
    ws_connections: int
    api_calls_per_month: int
    max_agents: int


@dataclass
class TenantContext:
    tenant_id: str
    tier: str
    quotas: TenantQuotas
    features: List[str]
    settings: Dict[str, Any]

    TIERS: Dict[str, TenantQuotas] = field(
        default_factory=lambda: {
            "free": TenantQuotas(60, 10, 1, 10_000, 1),
            "professional": TenantQuotas(600, 1000, 10, 1_000_000, 5),
            "enterprise": TenantQuotas(6000, 999_999, 100, 999_999_999, 999),
        }
    )

    @classmethod
    def from_jwt(cls, jwt_claims: dict) -> "TenantContext":
        tenant_id = jwt_claims.get("tenant_id", "default")
        tier = jwt_claims.get("quota_tier", "free")
        return cls(
            tenant_id=tenant_id,
            tier=tier,
            quotas=cls.TIERS.get(tier, cls.TIERS["free"]),
            features=jwt_claims.get("features", []),
            settings=jwt_claims.get("settings", {}),
        )

    def set_current(self) -> None:
        _tenant_context.set(self)

    @classmethod
    def get_current(cls) -> Optional["TenantContext"]:
        return _tenant_context.get()
