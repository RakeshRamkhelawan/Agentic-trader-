"""Comprehensive audit logging system."""

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class AuditAction(Enum):
    """Types of auditable actions."""
    # User actions
    USER_LOGIN = "user:login"
    USER_LOGOUT = "user:logout"
    USER_CREATE = "user:create"
    USER_UPDATE = "user:update"
    USER_DELETE = "user:delete"

    # Trading actions
    TRADE_CREATE = "trade:create"
    TRADE_MODIFY = "trade:modify"
    TRADE_CANCEL = "trade:cancel"
    TRADE_EXECUTE = "trade:execute"

    # Order actions
    ORDER_PLACE = "order:place"
    ORDER_CANCEL = "order:cancel"
    ORDER_FILL = "order:fill"

    # Strategy actions
    STRATEGY_CREATE = "strategy:create"
    STRATEGY_MODIFY = "strategy:modify"
    STRATEGY_DELETE = "strategy:delete"
    STRATEGY_DEPLOY = "strategy:deploy"

    # Tournament actions
    TOURNAMENT_CREATE = "tournament:create"
    TOURNAMENT_JOIN = "tournament:join"
    TOURNAMENT_LEAVE = "tournament:leave"

    # Admin actions
    ADMIN_USER_INVITE = "admin:user_invite"
    ADMIN_USER_REMOVE = "admin:user_remove"
    ADMIN_SETTINGS_CHANGE = "admin:settings_change"

    # Security actions
    PERMISSION_GRANT = "permission:grant"
    PERMISSION_REVOKE = "permission:revoke"
    API_KEY_CREATE = "api_key:create"
    API_KEY_REVOKE = "api_key:revoke"


@dataclass
class AuditEvent:
    """A single audit log entry."""
    id: str
    timestamp: datetime
    action: AuditAction
    actor_type: str  # "user", "system", "api"
    actor_id: str
    tenant_id: str
    resource_type: str
    resource_id: str

    # Details
    before_state: dict | None = None
    after_state: dict | None = None
    changes: list[str] = field(default_factory=list)

    # Context
    ip_address: str | None = None
    user_agent: str | None = None
    session_id: str | None = None
    request_id: str | None = None

    # Risk flags
    risk_score: float = 0.0  # 0-1, higher = more suspicious
    requires_review: bool = False
    reviewed_by: str | None = None
    reviewed_at: datetime | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat(),
            "action": self.action.value,
            "actor": {
                "type": self.actor_type,
                "id": self.actor_id,
            },
            "tenant_id": self.tenant_id,
            "resource": {
                "type": self.resource_type,
                "id": self.resource_id,
            },
            "changes": self.changes,
            "ip_address": self.ip_address,
            "risk_score": self.risk_score,
            "requires_review": self.requires_review,
        }


class AuditLogger:
    """
    Comprehensive audit logging system.

    Tracks all significant actions for compliance,
    security monitoring, and forensic analysis.
    """

    def __init__(self):
        self._logs: list[AuditEvent] = []
        self._index_by_tenant: dict[str, list[str]] = defaultdict(list)
        self._index_by_user: dict[str, list[str]] = defaultdict(list)
        self._index_by_resource: dict[str, list[str]] = defaultdict(list)
        self._counter = 0

    def log(
        self,
        action: AuditAction,
        actor_type: str,
        actor_id: str,
        tenant_id: str,
        resource_type: str,
        resource_id: str,
        before_state: dict | None = None,
        after_state: dict | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
        session_id: str | None = None,
        request_id: str | None = None,
    ) -> AuditEvent:
        """
        Log an audit event.

        Args:
            action: Type of action performed
            actor_type: Type of actor (user/system/api)
            actor_id: ID of the actor
            tenant_id: Tenant context
            resource_type: Type of resource affected
            resource_id: ID of resource affected
            before_state: State before action (for updates)
            after_state: State after action
            ip_address: Client IP address
            user_agent: Client user agent
            session_id: Session identifier
            request_id: Request identifier

        Returns:
            Created audit event
        """
        self._counter += 1

        # Calculate changes
        changes = self._calculate_changes(before_state, after_state)

        # Calculate risk score
        risk_score = self._calculate_risk_score(
            action, actor_type, before_state, after_state
        )

        event = AuditEvent(
            id=f"audit_{self._counter}_{datetime.utcnow().timestamp()}",
            timestamp=datetime.utcnow(),
            action=action,
            actor_type=actor_type,
            actor_id=actor_id,
            tenant_id=tenant_id,
            resource_type=resource_type,
            resource_id=resource_id,
            before_state=before_state,
            after_state=after_state,
            changes=changes,
            ip_address=ip_address,
            user_agent=user_agent,
            session_id=session_id,
            request_id=request_id,
            risk_score=risk_score,
            requires_review=risk_score > 0.7,
        )

        # Store event
        self._logs.append(event)

        # Update indexes
        self._index_by_tenant[tenant_id].append(event.id)
        self._index_by_user[actor_id].append(event.id)
        resource_key = f"{resource_type}:{resource_id}"
        self._index_by_resource[resource_key].append(event.id)

        return event

    def _calculate_changes(
        self,
        before: dict | None,
        after: dict | None,
    ) -> list[str]:
        """Calculate what changed between states."""
        changes = []

        if not before or not after:
            return changes

        for key in set(before.keys()) | set(after.keys()):
            before_val = before.get(key)
            after_val = after.get(key)

            if before_val != after_val:
                changes.append(f"{key}: {before_val} -> {after_val}")

        return changes

    def _calculate_risk_score(
        self,
        action: AuditAction,
        actor_type: str,
        before: dict | None,
        after: dict | None,
    ) -> float:
        """Calculate risk score for the action."""
        risk = 0.0

        # System actions are lower risk
        if actor_type == "system":
            risk -= 0.2

        # High-risk actions
        high_risk_actions = {
            AuditAction.PERMISSION_GRANT,
            AuditAction.PERMISSION_REVOKE,
            AuditAction.ADMIN_USER_REMOVE,
            AuditAction.API_KEY_CREATE,
        }
        if action in high_risk_actions:
            risk += 0.4

        # Large value changes are higher risk
        if before and after:
            before_value = before.get("value", 0) or before.get("amount", 0)
            after_value = after.get("value", 0) or after.get("amount", 0)
            if before_value and after_value:
                change_pct = abs(after_value - before_value) / before_value
                if change_pct > 0.5:
                    risk += 0.3

        return max(0, min(risk, 1.0))

    def query(
        self,
        tenant_id: str | None = None,
        user_id: str | None = None,
        action: AuditAction | None = None,
        resource_type: str | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        limit: int = 100,
    ) -> list[AuditEvent]:
        """Query audit logs with filters."""
        events = self._logs

        # Apply filters
        if tenant_id:
            event_ids = set(self._index_by_tenant.get(tenant_id, []))
            events = [e for e in events if e.id in event_ids]

        if user_id:
            event_ids = set(self._index_by_user.get(user_id, []))
            events = [e for e in events if e.id in event_ids]

        if action:
            events = [e for e in events if e.action == action]

        if resource_type:
            events = [e for e in events if e.resource_type == resource_type]

        if start_time:
            events = [e for e in events if e.timestamp >= start_time]

        if end_time:
            events = [e for e in events if e.timestamp <= end_time]

        # Sort by timestamp desc and limit
        events = sorted(events, key=lambda e: e.timestamp, reverse=True)
        return events[:limit]

    def get_events_requiring_review(self) -> list[AuditEvent]:
        """Get all events flagged for review."""
        return [e for e in self._logs if e.requires_review and not e.reviewed_by]

    def mark_reviewed(self, event_id: str, reviewer_id: str) -> bool:
        """Mark an event as reviewed."""
        for event in self._logs:
            if event.id == event_id:
                event.reviewed_by = reviewer_id
                event.reviewed_at = datetime.utcnow()
                return True
        return False

    def get_user_activity_summary(
        self,
        user_id: str,
        days: int = 30,
    ) -> dict[str, Any]:
        """Get activity summary for a user."""
        cutoff = datetime.utcnow() - __import__('datetime').timedelta(days=days)

        events = self.query(user_id=user_id, start_time=cutoff)

        action_counts = defaultdict(int)
        for event in events:
            action_counts[event.action.value] += 1

        return {
            "user_id": user_id,
            "period_days": days,
            "total_events": len(events),
            "action_breakdown": dict(action_counts),
            "high_risk_events": len([e for e in events if e.risk_score > 0.5]),
            "events_requiring_review": len([e for e in events if e.requires_review]),
        }


# Global audit logger
audit_logger = AuditLogger()
