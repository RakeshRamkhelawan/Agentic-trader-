"""
Approval Service - ADR-007
"""

import uuid
from datetime import datetime, timedelta
from enum import Enum


class ApprovalStatus(Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"


class ApprovalService:
    """Manages trade approval workflows."""

    def __init__(self, db, audit_logger):
        self.db = db
        self.audit = audit_logger

    async def request_approval(self, trade, policy_result, context):
        approval_id = str(uuid.uuid4())

        approval = {
            "id": approval_id,
            "trade": trade,
            "status": ApprovalStatus.PENDING,
            "approvers": policy_result.approvers,
            "risk_score": policy_result.risk_score,
            "created_at": datetime.utcnow(),
            "expires_at": datetime.utcnow() + timedelta(minutes=5),
        }

        await self.db.store_approval(approval)
        await self.audit.log_approval_requested(approval)
        return approval

    async def approve(self, approval_id: str, approver_id: str):
        approval = await self.db.get_approval(approval_id)
        approval["status"] = ApprovalStatus.APPROVED
        approval["approved_by"] = approver_id
        approval["approved_at"] = datetime.utcnow()

        await self.db.update_approval(approval)
        await self.audit.log_approval_action(approval, approver_id, "approved")
        return approval
