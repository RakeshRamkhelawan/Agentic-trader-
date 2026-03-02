import enum
import uuid
from datetime import datetime

from sqlalchemy import JSON, Column, DateTime, Float, String

from backend.core.database import Base


class OrderStatus(str, enum.Enum):
    PENDING_APPROVAL = "PENDING_APPROVAL"  # Blocked by HITL/Risk
    APPROVED = "APPROVED"  # Cleared for execution
    REJECTED = "REJECTED"  # User or Risk rejected
    SUBMITTED = "SUBMITTED"  # Sent to Exchange
    FILLED = "FILLED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


def generate_uuid():
    return str(uuid.uuid4())


class Order(Base):
    __tablename__ = "orders"

    id = Column(String, primary_key=True, default=generate_uuid)
    tenant_id = Column(String, index=True, nullable=False)

    # Order Details
    symbol = Column(String, nullable=False)
    side = Column(String, nullable=False)  # buy/sell
    quantity = Column(Float, nullable=False)
    price = Column(Float, nullable=True)  # Limit price
    order_type = Column(String, default="market")

    # Status
    status = Column(String, default=OrderStatus.PENDING_APPROVAL.value)

    # Risk & Governance
    risk_check_result = Column(JSON, nullable=True)  # Snapshot of Risk Guardian output
    rejection_reason = Column(String, nullable=True)
    approved_at = Column(DateTime, nullable=True)
    approved_by = Column(String, nullable=True)  # User ID

    # Execution
    exchange_order_id = Column(String, nullable=True)
    filled_qty = Column(Float, default=0.0)
    avg_price = Column(Float, nullable=True)
    commission = Column(Float, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
