from sqlalchemy import Column, String, Boolean, JSON, DateTime, UniqueConstraint
from datetime import datetime
import uuid
from backend.core.database import Base


class RuntimeConfig(Base):
    """
    Dynamic Configuration Store.
    Used for feature flags, risk limits, and system-wide settings that need
    to be adjustable at runtime without deployment.
    """

    __tablename__ = "runtime_configs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    key = Column(String, unique=True, index=True, nullable=False)
    value = Column(
        JSON, nullable=False
    )  # JSON for flexible typing (int, float, bool, dict)
    description = Column(String, nullable=True)
    is_encrypted = Column(Boolean, default=False)  # For sensitive keys
    group = Column(
        String, index=True, default="general"
    )  # e.g. "risk", "trading", "system"
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = Column(String, nullable=True)  # User ID or 'system'

    def __repr__(self):
        return f"<RuntimeConfig {self.key}={self.value}>"
