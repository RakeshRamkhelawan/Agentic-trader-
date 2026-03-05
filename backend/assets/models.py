import enum
from datetime import datetime, UTC
from sqlalchemy import Column, Integer, String, DateTime, Enum, JSON
from backend.core.database import Base

class AssetStatus(str, enum.Enum):
    DISCOVERED = "DISCOVERED"
    ACTIVE = "ACTIVE"
    POOLED = "POOLED"
    WATCHED = "WATCHED"
    INACTIVE = "INACTIVE"

class Asset(Base):
    __tablename__ = "assets"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=True)
    exchange = Column(String, nullable=True)
    status = Column(Enum(AssetStatus), default=AssetStatus.DISCOVERED, nullable=False)
    category = Column(String, nullable=True)
    metadata_info = Column(JSON, default={}, nullable=False)
    last_updated = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
