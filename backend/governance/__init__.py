"""
Governance Package

Audit logging, watchdogs, circuit breakers, RBAC, en compliance.
"""

from .circuit_breaker import (
    BreakerState,
    CircuitBreaker,
    CircuitBreakerState,
    CircuitBreakerTrippedError,
    TripReason,
)
from .decision_audit import AuditLogger, DecisionAuditLog
from .permission_service import PermissionService, TradingModeChange
from .trading_permissions import (
    PermissionDeniedError,
    TradingPermission,
    TradingRole,
    get_required_permission_for_mode,
    has_permission,
)

__all__ = [
    "DecisionAuditLog",
    "AuditLogger",
    "CircuitBreaker",
    "CircuitBreakerState",
    "CircuitBreakerTrippedError",
    "BreakerState",
    "TripReason",
    "TradingPermission",
    "TradingRole",
    "PermissionDeniedError",
    "has_permission",
    "get_required_permission_for_mode",
    "PermissionService",
    "TradingModeChange",
]
