from enum import Enum
import uuid
from sqlalchemy import Column, String, DateTime, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime, UTC
from backend.core.database import Base

class AssetStatus(str, Enum):
    DISCOVERED = "DISCOVERED"
    ACTIVE = "ACTIVE"
    POOLED = "POOLED"
    WATCHED = "WATCHED"
    INACTIVE = "INACTIVE"

class Asset(Base):
    __tablename__ = "assets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    symbol = Column(String, nullable=False, index=True)
    exchange = Column(String, nullable=False, index=True)
    status = Column(SQLEnum(AssetStatus), default=AssetStatus.DISCOVERED, nullable=False)
    category = Column(String, default="other", nullable=False)
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))

    __table_args__ = (
        # Unique constraint for symbol + exchange could be added here
        # UniqueConstraint('symbol', 'exchange', name='uix_asset_symbol_exchange'),
    )
