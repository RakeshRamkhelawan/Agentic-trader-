"""
Audit Logger - Structured logging for security-critical events.

Provides a standardized way to log security events (Authentication, Authorization,
Trade Execution, Configuration Changes) in a structured JSON format that is
machine-readable and suitable for SIEM ingestion.
"""

import json
import logging
import uuid
from datetime import UTC, datetime
from enum import Enum
from typing import Any, Dict, Optional

# Configure a specific logger for audit events
audit_logger = logging.getLogger("audit")


class AuditEventType(str, Enum):
    """Types of audit events."""
    
    AUTH_LOGIN = "AUTH_LOGIN"
    AUTH_LOGOUT = "AUTH_LOGOUT"
    AUTH_FAILED = "AUTH_FAILED"
    
    AUTHZ_CHECK = "AUTHZ_CHECK"
    AUTHZ_GRANTED = "AUTHZ_GRANTED"
    AUTHZ_DENIED = "AUTHZ_DENIED"
    
    TRADE_REQUESTED = "TRADE_REQUESTED"
    TRADE_EXECUTED = "TRADE_EXECUTED"
    TRADE_FAILED = "TRADE_FAILED"
    TRADE_BLOCKED = "TRADE_BLOCKED"
    
    SYSTEM_STARTUP = "SYSTEM_STARTUP"
    SYSTEM_SHUTDOWN = "SYSTEM_SHUTDOWN"
    CONFIG_CHANGE = "CONFIG_CHANGE"


class AuditLogger:
    """
    Structured logger for security audit trails.
    """
    
    def __init__(self, service_name: str = "agentic_trader"):
        self.service_name = service_name

    def log_event(
        self,
        event_type: AuditEventType,
        actor: str,
        action: str,
        resource: str,
        output_status: str,
        details: Optional[Dict[str, Any]] = None,
        trace_id: Optional[str] = None
    ) -> None:
        """
        Log an audit event.

        Args:
            event_type: Type of the event (AuditEventType)
            actor: Who performed the action (e.g., "agent:researcher", "user:admin")
            action: What action was performed (e.g., "trade_execution", "login")
            resource: What resource was accessed (e.g., "order_executor", "vault")
            output_status: Outcome of the action ("SUCCESS", "FAILURE", "DENIED")
            details: Additional context (non-sensitive info only!)
            trace_id: Distributed trace ID for correlation
        """
        event = {
            "timestamp": datetime.now(UTC).isoformat(),
            "event_id": str(uuid.uuid4()),
            "trace_id": trace_id or str(uuid.uuid4()),
            "service": self.service_name,
            "event_type": event_type.value,
            "actor": actor,
            "action": action,
            "resource": resource,
            "status": output_status,
            "details": details or {}
        }
        
        # Log as a JSON string for easy parsing by monitoring tools (Splunk, ELK, etc.)
        # We use level INFO for audit logs. 
        # Configure the 'audit' logger to write to a separate file in production.
        audit_logger.info(json.dumps(event))

    def log_authz_check(
        self,
        agent_name: str,
        role: str,
        permission: str,
        granted: bool,
        trace_id: Optional[str] = None
    ):
        """Helper for logging authorization checks."""
        status = "GRANTED" if granted else "DENIED"
        event_type = AuditEventType.AUTHZ_GRANTED if granted else AuditEventType.AUTHZ_DENIED
        
        self.log_event(
            event_type=event_type,
            actor=f"agent:{agent_name}",
            action=permission,
            resource="gatekeeper",
            output_status=status,
            details={"role": role},
            trace_id=trace_id
        )

    def log_trade_attempt(
        self,
        execution_plan: Any,
        outcome: str,
        details: Dict[str, Any],
        trace_id: Optional[str] = None
    ):
        """Helper for logging trade execution attempts."""
        self.log_event(
            event_type=AuditEventType.TRADE_REQUESTED,
            actor=f"agent:{execution_plan.caller_name}",
            action=f"trade:{execution_plan.side}",
            resource="order_executor",
            output_status=outcome,
            details={
                "symbol": execution_plan.symbol,
                "quantity": execution_plan.quantity,
                "role": execution_plan.caller_role,
                **details
            },
            trace_id=execution_plan.trace_id or trace_id
        )
