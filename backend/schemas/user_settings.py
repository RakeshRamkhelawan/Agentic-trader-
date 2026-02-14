"""
User Settings Schemas - Pydantic models for user settings API.
"""

from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
from datetime import datetime
from enum import Enum


class ThemeType(str, Enum):
    """Available theme options."""

    DARK = "dark"
    LIGHT = "light"
    SYSTEM = "system"


class CurrencyType(str, Enum):
    """Supported currencies."""

    EUR = "EUR"
    USD = "USD"
    GBP = "GBP"


class ExchangeType(str, Enum):
    """Supported exchanges."""

    BINANCE = "binance"
    KRAKEN = "kraken"
    COINBASE = "coinbase"
    BITVAVO = "bitvavo"


# ============================================================================
# Profile Settings
# ============================================================================


class UserProfile(BaseModel):
    """User profile information."""

    first_name: str = Field(default="", max_length=100)
    last_name: str = Field(default="", max_length=100)
    email: Optional[EmailStr] = None


class UserProfileUpdate(BaseModel):
    """Update request for user profile."""

    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    email: Optional[EmailStr] = None


# ============================================================================
# Notification Settings
# ============================================================================


class NotificationSettings(BaseModel):
    """User notification preferences."""

    order_executions: bool = Field(default=True, description="Notify on order fills")
    price_alerts: bool = Field(default=True, description="Price target alerts")
    ai_signals: bool = Field(default=True, description="AI trading signals")
    security_alerts: bool = Field(default=True, description="Security notifications")


class NotificationSettingsUpdate(BaseModel):
    """Update request for notifications."""

    order_executions: Optional[bool] = None
    price_alerts: Optional[bool] = None
    ai_signals: Optional[bool] = None
    security_alerts: Optional[bool] = None


# ============================================================================
# Security Settings
# ============================================================================


class SecuritySettings(BaseModel):
    """User security settings."""

    two_factor_enabled: bool = False
    last_password_change: Optional[datetime] = None


class Enable2FARequest(BaseModel):
    """Request to enable 2FA."""

    method: str = Field(default="totp", description="2FA method: totp or sms")


class Enable2FAResponse(BaseModel):
    """Response after enabling 2FA."""

    secret: str = Field(description="TOTP secret for authenticator app")
    qr_code_url: str = Field(description="QR code URL for scanning")
    backup_codes: List[str] = Field(description="Backup recovery codes")


class ChangePasswordRequest(BaseModel):
    """Request to change password."""

    current_password: str = Field(min_length=8)
    new_password: str = Field(min_length=8)


# ============================================================================
# Appearance Settings
# ============================================================================


class AppearanceSettings(BaseModel):
    """User appearance/theme settings."""

    theme: ThemeType = ThemeType.DARK


class AppearanceSettingsUpdate(BaseModel):
    """Update request for appearance."""

    theme: Optional[ThemeType] = None


# ============================================================================
# API Keys
# ============================================================================


class BrokerAPIKey(BaseModel):
    """Broker API key (response model - key is masked)."""

    id: str
    exchange: ExchangeType
    api_key_masked: str = Field(description="Masked API key (last 4 chars visible)")
    created_at: datetime
    last_used: Optional[datetime] = None
    is_valid: bool = True


class BrokerAPIKeyCreate(BaseModel):
    """Request to add new broker API key."""

    exchange: ExchangeType
    api_key: str = Field(min_length=10, description="Exchange API key")
    api_secret: str = Field(min_length=10, description="Exchange API secret")
    passphrase: Optional[str] = Field(
        None, description="Optional passphrase (for Coinbase)"
    )


class BrokerAPIKeyList(BaseModel):
    """List of broker API keys."""

    keys: List[BrokerAPIKey]
    total: int


# ============================================================================
# Preferences
# ============================================================================


class UserPreferences(BaseModel):
    """User trading preferences."""

    default_currency: CurrencyType = CurrencyType.EUR
    default_exchange: ExchangeType = ExchangeType.BINANCE


class UserPreferencesUpdate(BaseModel):
    """Update request for preferences."""

    default_currency: Optional[CurrencyType] = None
    default_exchange: Optional[ExchangeType] = None


# ============================================================================
# Combined Settings Response
# ============================================================================


class AllUserSettings(BaseModel):
    """Complete user settings response."""

    profile: UserProfile
    notifications: NotificationSettings
    security: SecuritySettings
    appearance: AppearanceSettings
    preferences: UserPreferences
    api_keys_count: int = 0
