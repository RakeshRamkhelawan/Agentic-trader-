# ADR-007: Trade Governance - Policy Engine & Human-in-the-Loop

**Status**: Proposed
**Date**: 2026-02-20
**Author**: Architecture Team
**Scope**: Trade approvals, policy enforcement, audit trails

---

## Context

Het Agentic Trader Platform voert autonoom trades uit via AI agents, maar moet:

- **Risico beheersen**: Grote trades moeten gecontroleerd worden
- **Compliance**: Regulatoire vereisten (MiFID II, best execution)
- **Accountability**: Wie is verantwoordelijk voor trades?
- **Override**: Humans moeten kunnen ingrijpen

Huidige situatie:
- Approval API bestaat maar niet volledig geïmplementeerd
- Geen policy-as-code
- Geen human-in-the-loop workflow
- Basis audit logging aanwezig

---

## Decision

### 1. Governance Model

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         GOVERNANCE HIERARCHY                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Level 1: Automatic (90% of trades)                                        │
│  ─────────────────────────────────                                         │
│  • Routine trades onder limieten                                           │
│  • Agents met hoge confidence (>0.85)                                      │
│  • Gekende strategieën                                                     │
│                                                                             │
│  Level 2: Auto + Notify (8% of trades)                                     │
│  ─────────────────────────────────                                         │
│  • Trades nabij limieten                                                   │
│  • Ongebruikelijke tijden/patronen                                         │
│  • Async notificatie naar compliance                                       │
│                                                                             │
│  Level 3: Pre-Approval Required (2% of trades)                             │
│  ─────────────────────────────────                                         │
│  • Grote trades (>€100K)                                                   │
│  • High-risk assets                                                        │
│  • First-time strategies                                                   │
│  • Systeem anomaly gedetecteerd                                            │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2. Policy-as-Code

**Policy Engine**: Open Policy Agent (OPA) of Python-based rules

```python
# policies/trade_approval.rego
package trading.approval

import future.keywords.if
import future.keywords.in

default allow := false

# Level 1: Auto-approve routine trades
allow if {
    input.trade.value < input.user.daily_limit * 0.1
    input.agent.confidence > 0.85
    input.risk.vaR_95 < input.portfolio.max_var
    not input.market.high_volatility
}

# Level 2: Auto-approve with notification
allow_with_notification if {
    input.trade.value >= input.user.daily_limit * 0.1
    input.trade.value < input.user.daily_limit * 0.5
    input.agent.confidence > 0.70
}

# Level 3: Require human approval
require_approval if {
    input.trade.value >= input.user.daily_limit * 0.5
}

require_approval if {
    input.trade.asset.risk_rating == "high"
}

require_approval if {
    input.market.regime == "stressed"
}
```

### 3. Approval Workflow

```
Trade Request
     │
     ▼
┌──────────────┐
│ Policy Check │
└──────┬───────┘
       │
       ├──► Auto-Approved ──► Execute ──► Log
       │
       ├──► Notify-Only ──► Execute + Alert
       │
       └──► Approval Required ──► Queue ──► Review
                                          │
                              ┌───────────┼───────────┐
                              ▼           ▼           ▼
                           Approved   Rejected   Timeout
                              │           │         │
                              ▼           ▼         ▼
                           Execute      Block    Escalate
```

### 4. Human Review Interface

**Approval Dashboard**:
- Pending approvals queue
- Trade details (waarde, risico, agent reasoning)
- One-click approve/reject
- Bulk actions
- Audit trail

**Notification Channels**:
- In-app notifications
- Email for urgent approvals
- Slack/Teams webhook
- SMS voor kritieke trades (>

## Implementation

### 1. Policy Engine

```python
# backend/governance/policy_engine.py
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum

class ApprovalLevel(Enum):
    AUTO = "auto"                    # Direct execution
    AUTO_NOTIFY = "auto_notify"      # Execute + alert
    REQUIRES_APPROVAL = "approval"   # Human approval needed
    BLOCKED = "blocked"              # Always blocked

@dataclass
class TradeContext:
    trade: OrderRequest
    agent: AgentContext
    portfolio: PortfolioState
    market: MarketConditions
    user: UserContext

@dataclass
class PolicyResult:
    level: ApprovalLevel
    reason: str
    approvers: List[str]           # Required approver roles
    timeout_seconds: int           # Approval timeout
    risk_score: float              # 0-1 calculated risk

class PolicyEngine:
    """
    Evaluates trades against governance policies.
    """

    def __init__(self):
        self.rules = self._load_rules()
        self.risk_calculator = RiskCalculator()

    async def evaluate(self, context: TradeContext) -> PolicyResult:
        """Evaluate trade against all policies."""

        # Calculate risk score
        risk_score = await self.risk_calculator.calculate(context)

        # Check hard blocks first
        if self._is_blocked(context):
            return PolicyResult(
                level=ApprovalLevel.BLOCKED,
                reason="Trade violates hard constraints",
                approvers=[],
                timeout_seconds=0,
                risk_score=risk_score
            )

        # Check auto-approve criteria
        if await self._can_auto_approve(context, risk_score):
            return PolicyResult(
                level=ApprovalLevel.AUTO,
                reason="Within risk parameters",
                approvers=[],
                timeout_seconds=0,
                risk_score=risk_score
            )

        # Check notify-only criteria
        if await self._can_auto_notify(context, risk_score):
            return PolicyResult(
                level=ApprovalLevel.AUTO_NOTIFY,
                reason="Elevated risk, notification sent",
                approvers=["compliance_team"],
                timeout_seconds=0,
                risk_score=risk_score
            )

        # Requires human approval
        approvers = self._determine_approvers(context, risk_score)

        return PolicyResult(
            level=ApprovalLevel.REQUIRES_APPROVAL,
            reason=f"Risk score {risk_score:.2f} exceeds threshold",
            approvers=approvers,
            timeout_seconds=300,  # 5 minute timeout
            risk_score=risk_score
        )

    async def _can_auto_approve(self, ctx: TradeContext, risk: float) -> bool:
        """Check if trade can be auto-approved."""
        return all([
            ctx.trade.value < ctx.user.daily_limit * 0.1,
            ctx.agent.confidence > 0.85,
            risk < 0.3,
            not ctx.market.high_volatility,
            not ctx.trade.asset.is_restricted
        ])

    async def _can_auto_notify(self, ctx: TradeContext, risk: float) -> bool:
        """Check if trade can auto-execute with notification."""
        return all([
            ctx.trade.value < ctx.user.daily_limit * 0.5,
            ctx.agent.confidence > 0.70,
            risk < 0.6,
        ])

    def _is_blocked(self, ctx: TradeContext) -> bool:
        """Check if trade is hard-blocked."""
        return any([
            ctx.trade.asset.is_sanctioned,
            ctx.user.trading_suspended,
            ctx.trade.value > ctx.user.hard_limit,
            ctx.market.trading_halted
        ])

    def _determine_approvers(self, ctx: TradeContext, risk: float) -> List[str]:
        """Determine who must approve this trade."""
        approvers = ["senior_trader"]

        if risk > 0.8:
            approvers.append("risk_manager")

        if ctx.trade.value > 100_000:
            approvers.append("compliance_officer")

        if ctx.trade.asset.risk_rating == "high":
            approvers.append("portfolio_manager")

        return approvers
```

### 2. Approval Service

```python
# backend/governance/approval_service.py
import uuid
from datetime import datetime, timedelta
from typing import Optional

class ApprovalService:
    """
    Manages approval workflows for trades.
    """

    def __init__(self, db, notifier, audit_logger):
        self.db = db
        self.notifier = notifier
        self.audit = audit_logger

    async def request_approval(
        self,
        trade: OrderRequest,
        policy_result: PolicyResult,
        context: TradeContext
    ) -> ApprovalRequest:
        """Create approval request for trade."""

        approval_id = str(uuid.uuid4())

        approval = ApprovalRequest(
            id=approval_id,
            trade=trade,
            requester_id=context.user.id,
            approvers=policy_result.approvers,
            risk_score=policy_result.risk_score,
            reason=policy_result.reason,
            status=ApprovalStatus.PENDING,
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(seconds=policy_result.timeout_seconds)
        )

        # Store in database
        await self.db.store_approval(approval)

        # Notify approvers
        await self.notifier.notify_approvers(approval)

        # Audit log
        await self.audit.log_approval_requested(approval)

        return approval

    async def approve(
        self,
        approval_id: str,
        approver_id: str,
        comment: Optional[str] = None
    ) -> ApprovalRequest:
        """Approve a pending trade."""

        approval = await self.db.get_approval(approval_id)

        if approval.status != ApprovalStatus.PENDING:
            raise InvalidApprovalState("Approval not pending")

        if approver_id not in approval.approvers:
            raise UnauthorizedApprover("User cannot approve this trade")

        # Record approval
        approval.approvals.append(ApprovalAction(
            approver_id=approver_id,
            action="approved",
            comment=comment,
            timestamp=datetime.utcnow()
        ))

        # Check if fully approved
        if self._is_fully_approved(approval):
            approval.status = ApprovalStatus.APPROVED

            # Execute trade
            await self._execute_approved_trade(approval)

        await self.db.update_approval(approval)

        # Audit log
        await self.audit.log_approval_action(approval, approver_id, "approved")

        return approval

    async def reject(
        self,
        approval_id: str,
        approver_id: str,
        reason: str
    ) -> ApprovalRequest:
        """Reject a pending trade."""

        approval = await self.db.get_approval(approval_id)

        approval.status = ApprovalStatus.REJECTED
        approval.rejection_reason = reason
        approval.rejected_by = approver_id
        approval.rejected_at = datetime.utcnow()

        await self.db.update_approval(approval)

        # Notify requester
        await self.notifier.notify_rejection(approval)

        # Audit log
        await self.audit.log_approval_action(approval, approver_id, "rejected", reason)

        return approval

    async def check_expired_approvals(self):
        """Background task to handle expired approvals."""
        expired = await self.db.get_expired_approvals()

        for approval in expired:
            approval.status = ApprovalStatus.EXPIRED
            await self.db.update_approval(approval)

            # Notify requester
            await self.notifier.notify_expiration(approval)

            # Audit log
            await self.audit.log_approval_expired(approval)
```

### 3. Audit Trail

```python
# backend/governance/audit_logger.py
from datetime import datetime
from typing import Dict, Any

class GovernanceAuditLogger:
    """
    Immutable audit logging for governance decisions.
    """

    async def log_decision(
        self,
        decision_type: str,      # 'trade', 'approval', 'policy_override'
        decision_id: str,
        actor_id: str,           # Who made the decision
        actor_type: str,         # 'agent', 'user', 'system'
        context: Dict[str, Any], # Full decision context
        outcome: str,            # 'approved', 'rejected', 'auto_executed'
        reasoning: str,          # Why this decision was made
        risk_metrics: Dict[str, float]
    ):
        """Log governance decision with full context."""

        entry = GovernanceAuditEntry(
            timestamp=datetime.utcnow(),
            decision_type=decision_type,
            decision_id=decision_id,
            actor_id=actor_id,
            actor_type=actor_type,
            context=context,
            outcome=outcome,
            reasoning=reasoning,
            risk_metrics=risk_metrics,
            # Cryptographic hash for tamper detection
            hash=self._calculate_hash(context)
        )

        # Write to append-only log
        await self._write_to_audit_log(entry)

        # Replicate to secure storage
        await self._replicate(entry)

        # Real-time compliance dashboard
        await self._notify_compliance(entry)

    def _calculate_hash(self, data: Dict) -> str:
        """Calculate tamper-evident hash."""
        import hashlib
        import json

        content = json.dumps(data, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()
```

### 4. Integration with Execution

```python
# backend/execution/smart_order_router.py
class SmartOrderRouter:
    async def route_order(self, order: OrderRequest, agent_context: AgentContext):
        """Route order with governance checks."""

        # Build trade context
        context = await self._build_trade_context(order, agent_context)

        # Evaluate policies
        policy_result = await self.policy_engine.evaluate(context)

        if policy_result.level == ApprovalLevel.BLOCKED:
            raise OrderBlocked(policy_result.reason)

        elif policy_result.level == ApprovalLevel.AUTO:
            # Execute immediately
            await self._execute(order, context)

            # Log decision
            await self.audit.log_decision(
                decision_type="trade",
                decision_id=order.id,
                actor_id=agent_context.agent_id,
                actor_type="agent",
                outcome="auto_executed",
                reasoning=policy_result.reason,
                risk_metrics={"score": policy_result.risk_score}
            )

        elif policy_result.level == ApprovalLevel.AUTO_NOTIFY:
            # Execute and notify
            await self._execute(order, context)
            await self.notifier.send_alert("High-risk trade executed", context)

        elif policy_result.level == ApprovalLevel.REQUIRES_APPROVAL:
            # Queue for approval
            approval = await self.approval_service.request_approval(
                order, policy_result, context
            )

            return ApprovalPending(approval.id)
```

---

## Human Interface

### Approval Dashboard (Frontend)

```typescript
// frontend/src/components/governance/ApprovalQueue.tsx
interface ApprovalQueueProps {
  approvals: ApprovalRequest[];
  onApprove: (id: string, comment?: string) => void;
  onReject: (id: string, reason: string) => void;
}

const ApprovalQueue: React.FC<ApprovalQueueProps> = ({
  approvals,
  onApprove,
  onReject
}) => {
  return (
    <div className="approval-queue">
      {approvals.map(approval => (
        <ApprovalCard
          key={approval.id}
          trade={approval.trade}
          riskScore={approval.risk_score}
          agentReasoning={approval.agent_reasoning}
          onApprove={(comment) => onApprove(approval.id, comment)}
          onReject={(reason) => onReject(approval.id, reason)}
        />
      ))}
    </div>
  );
};
```

---

## Monitoring

### Grafana Dashboard: "Governance"

**Panels**:
1. **Approval Queue**: Pending, avg wait time
2. **Decision Distribution**: Auto/Notify/Approval %
3. **Risk Score Trend**: Over time
4. **Approver Workload**: Per approver
5. **Audit Events**: Log volume, anomalies

### Alerts

```yaml
- alert: HighApprovalQueue
  expr: approval_queue_depth > 10
  severity: warning

- alert: ApprovalTimeout
  expr: rate(approvals_expired[1h]) > 5
  severity: critical

- alert: UnusualRejectionRate
  expr: rejection_rate > 0.3
  severity: warning
```

---

## Compliance Mapping

| Regulation | Requirement | Implementation |
|------------|-------------|----------------|
| MiFID II | Best execution | Policy checks |
| MiFID II | Transaction reporting | Audit logs |
| GDPR | Data retention | Audit retention policy |
| SOC 2 | Access controls | Approval workflows |

---

## Decision Log

| Date | Change | Author |
|------|--------|--------|
| 2026-02-20 | Initial policy framework | Architecture Team |
