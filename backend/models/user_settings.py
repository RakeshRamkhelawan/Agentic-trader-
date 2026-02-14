"""
Database Models for User Settings.
"""

import uuid
from datetime import datetime

from sqlalchemy import (JSON, Boolean, Column, DateTime, ForeignKey, String,
                        Text)
from sqlalchemy.orm import relationship

from backend.core.database import Base


def generate_uuid():
    return str(uuid.uuid4())


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=generate_uuid)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=True)  # NULL for legacy users
    tenant_id = Column(String, index=True, nullable=False)
    role = Column(String, default="user")  # admin, user, demo
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    profile = relationship(
        "UserProfile",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )
    security = relationship(
        "UserSecurity",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )
    preferences = relationship(
        "UserPreferences",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )
    api_keys = relationship(
        "APIKey", back_populates="user", cascade="all, delete-orphan"
    )


class UserProfile(Base):
    __tablename__ = "user_profiles"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, unique=True)
    full_name = Column(String, nullable=True)
    avatar_url = Column(String, nullable=True)

    # Notifications stored as JSON
    notification_preferences = Column(
        JSON,
        default={
            "email_alerts": True,
            "push_notifications": False,
            "marketing_emails": False,
            "security_alerts": True,
        },
    )

    user = relationship("User", back_populates="profile")


class UserSecurity(Base):
    __tablename__ = "user_security"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, unique=True)
    two_factor_enabled = Column(Boolean, default=False)
    last_password_change = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="security")


class UserPreferences(Base):
    __tablename__ = "user_preferences"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, unique=True)
    theme = Column(String, default="system")
    language = Column(String, default="en")
    default_currency = Column(String, default="EUR")
    default_exchange = Column(String, default="binance")
    chart_preferences = Column(JSON, default={})

    # HITL & Risk Settings
    autonomy_status = Column(String, default="MANUAL")  # MANUAL, SEMI_AUTO, FULL_AUTO
    risk_settings = Column(
        JSON,
        default={
            "max_daily_loss": 50.0,
            "max_order_size": 20.0,
            "max_open_positions": 3,
            "kill_switch_enabled": False,
            "allowed_assets": ["BTC-EUR", "ETH-EUR"],
        },
    )

    user = relationship("User", back_populates="preferences")


class APIKey(Base):
    __tablename__ = "api_keys"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    exchange = Column(String, nullable=False)

    # Encrypted fields
    api_key_encrypted = Column(Text, nullable=False)
    api_secret_encrypted = Column(Text, nullable=False)
    passphrase_encrypted = Column(Text, nullable=True)

    is_valid = Column(Boolean, default=True)
    permissions = Column(JSON, default=["read"])
    created_at = Column(DateTime, default=datetime.utcnow)
    last_used_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="api_keys")
