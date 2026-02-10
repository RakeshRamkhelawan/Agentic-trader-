"""
User Settings Service - Manages user profile, security, and preferences via Database.

Now uses PostgreSQL via SQLAlchemy + AsyncPG.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from typing import Optional, List
import logging
from cryptography.fernet import Fernet
import os
import json

from backend.schemas.user_settings import (
    UserProfile, NotificationSettings, SecuritySettings,
    AppearanceSettings, UserPreferences, BrokerAPIKey, BrokerAPIKeyCreate, ExchangeType
)
from backend.models.user_settings import (
    User as DBUser, UserProfile as DBUserProfile, UserSecurity as DBUserSecurity,
    UserPreferences as DBUserPreferences, APIKey as DBAPIKey
)

logger = logging.getLogger(__name__)

# Encryption key management
ENCRYPTION_KEY = os.getenv("API_KEY_ENCRYPTION_KEY", Fernet.generate_key().decode())
cipher_suite = Fernet(ENCRYPTION_KEY.encode())


class UserSettingsService:
    def __init__(self):
        pass

    async def _get_or_create_user(self, db: AsyncSession, tenant_id: str) -> DBUser:
        """Helper to get user by tenant_id, creating root records if missing."""
        result = await db.execute(select(DBUser).where(DBUser.tenant_id == tenant_id))
        user = result.scalars().first()

        if not user:
            user = DBUser(tenant_id=tenant_id, email=f"{tenant_id}@example.com") # Mock email fallback
            db.add(user)
            await db.flush()
            
            # Create default relations
            profile = DBUserProfile(user_id=user.id)
            security = DBUserSecurity(user_id=user.id)
            prefs = DBUserPreferences(user_id=user.id)
            
            db.add_all([profile, security, prefs])
            await db.commit()
            await db.refresh(user)
            
        return user

    # =========================================================================
    # Profile
    # =========================================================================

    async def get_profile(self, db: AsyncSession, tenant_id: str) -> UserProfile:
        user = await self._get_or_create_user(db, tenant_id)
        # Load profile relation if needed, but it's likely already attached or we query it
        result = await db.execute(select(DBUserProfile).where(DBUserProfile.user_id == user.id))
        db_profile = result.scalars().first()
        
        return UserProfile(
            first_name=db_profile.full_name.split(" ")[0] if db_profile.full_name else "",
            last_name=db_profile.full_name.split(" ")[-1] if db_profile.full_name and " " in db_profile.full_name else "",
            email=user.email
        )

    async def update_profile(self, db: AsyncSession, tenant_id: str, profile: UserProfile) -> UserProfile:
        user = await self._get_or_create_user(db, tenant_id)
        result = await db.execute(select(DBUserProfile).where(DBUserProfile.user_id == user.id))
        db_profile = result.scalars().first()
        
        db_profile.full_name = f"{profile.first_name} {profile.last_name}".strip()
        user.email = profile.email
        
        await db.commit()
        return profile

    # =========================================================================
    # Notifications
    # =========================================================================

    async def get_notifications(self, db: AsyncSession, tenant_id: str) -> NotificationSettings:
        user = await self._get_or_create_user(db, tenant_id)
        result = await db.execute(select(DBUserProfile).where(DBUserProfile.user_id == user.id))
        db_profile = result.scalars().first()
        
        prefs = db_profile.notification_preferences or {}
        # Ensure dict keys match NotificationSettings logic if needed, but strict Pydantic helps
        return NotificationSettings(**prefs)

    async def update_notifications(self, db: AsyncSession, tenant_id: str, prefs: NotificationSettings) -> NotificationSettings:
        user = await self._get_or_create_user(db, tenant_id)
        result = await db.execute(select(DBUserProfile).where(DBUserProfile.user_id == user.id))
        db_profile = result.scalars().first()
        
        # Pydantic model to dict
        db_profile.notification_preferences = prefs.dict()
        await db.commit()
        return prefs

    # =========================================================================
    # Security
    # =========================================================================

    async def get_security_settings(self, db: AsyncSession, tenant_id: str) -> SecuritySettings:
        user = await self._get_or_create_user(db, tenant_id)
        result = await db.execute(select(DBUserSecurity).where(DBUserSecurity.user_id == user.id))
        db_sec = result.scalars().first()
        
        return SecuritySettings(
            two_factor_enabled=db_sec.two_factor_enabled,
            last_password_change=db_sec.last_password_change
        )

    async def toggle_2fa(self, db: AsyncSession, tenant_id: str, enabled: bool) -> bool:
        user = await self._get_or_create_user(db, tenant_id)
        result = await db.execute(select(DBUserSecurity).where(DBUserSecurity.user_id == user.id))
        db_sec = result.scalars().first()
        
        db_sec.two_factor_enabled = enabled
        await db.commit()
        return enabled

    # =========================================================================
    # Appearance & Preferences
    # =========================================================================

    async def get_appearance(self, db: AsyncSession, tenant_id: str) -> AppearanceSettings:
        user = await self._get_or_create_user(db, tenant_id)
        result = await db.execute(select(DBUserPreferences).where(DBUserPreferences.user_id == user.id))
        db_prefs = result.scalars().first()
        
        return AppearanceSettings(
            theme=db_prefs.theme or "system"
        )
        
    async def update_appearance(self, db: AsyncSession, tenant_id: str, appearance: AppearanceSettings) -> AppearanceSettings:
        user = await self._get_or_create_user(db, tenant_id)
        result = await db.execute(select(DBUserPreferences).where(DBUserPreferences.user_id == user.id))
        db_prefs = result.scalars().first()
        
        db_prefs.theme = appearance.theme
        await db.commit()
        return appearance

    async def get_preferences(self, db: AsyncSession, tenant_id: str) -> UserPreferences:
        user = await self._get_or_create_user(db, tenant_id)
        result = await db.execute(select(DBUserPreferences).where(DBUserPreferences.user_id == user.id))
        db_prefs = result.scalars().first()
        
        return UserPreferences(
            default_currency=db_prefs.default_currency or "EUR",
            default_exchange=db_prefs.default_exchange or "binance"
        )

    async def update_preferences(self, db: AsyncSession, tenant_id: str, prefs: UserPreferences) -> UserPreferences:
        user = await self._get_or_create_user(db, tenant_id)
        result = await db.execute(select(DBUserPreferences).where(DBUserPreferences.user_id == user.id))
        db_prefs = result.scalars().first()
        
        db_prefs.default_currency = prefs.default_currency
        db_prefs.default_exchange = prefs.default_exchange
        await db.commit()
        return prefs

    # =========================================================================
    # API Keys
    # =========================================================================

    async def get_api_keys(self, db: AsyncSession, tenant_id: str) -> List[BrokerAPIKey]:
        user = await self._get_or_create_user(db, tenant_id)
        result = await db.execute(select(DBAPIKey).where(DBAPIKey.user_id == user.id))
        db_keys = result.scalars().all()
        
        return [
            BrokerAPIKey(
                id=k.id,
                exchange=k.exchange,
                api_key_masked=f"***{cipher_suite.decrypt(k.api_key_encrypted.encode()).decode()[-4:]}",
                created_at=k.created_at,
                is_valid=k.is_valid
            ) for k in db_keys
        ]

    async def add_api_key(self, db: AsyncSession, tenant_id: str, request: BrokerAPIKeyCreate) -> BrokerAPIKey:
        user = await self._get_or_create_user(db, tenant_id)
        
        # Encrypt keys
        key_enc = cipher_suite.encrypt(request.api_key.encode()).decode()
        secret_enc = cipher_suite.encrypt(request.api_secret.encode()).decode()
        pass_enc = cipher_suite.encrypt(request.passphrase.encode()).decode() if request.passphrase else None

        new_key = DBAPIKey(
            user_id=user.id,
            name=f"{request.exchange.value.upper()}_{str(len(await self.get_api_keys(db, tenant_id)) + 1)}", # Auto-name
            exchange=request.exchange,
            api_key_encrypted=key_enc,
            api_secret_encrypted=secret_enc,
            passphrase_encrypted=pass_enc,
            is_valid=True, # In real app, validate first
            permissions=["read", "trade"]
        )
        
        db.add(new_key)
        await db.commit()
        await db.refresh(new_key)
        
        return BrokerAPIKey(
            id=new_key.id,
            exchange=new_key.exchange,
            api_key_masked=f"***{request.api_key[-4:]}",
            created_at=new_key.created_at,
            is_valid=new_key.is_valid
        )

    async def delete_api_key(self, db: AsyncSession, tenant_id: str, key_id: str):
        # Security check: ensure key belongs to user
        user = await self._get_or_create_user(db, tenant_id)
        result = await db.execute(select(DBAPIKey).where(DBAPIKey.id == key_id, DBAPIKey.user_id == user.id))
        key = result.scalars().first()
        
        if key:
            await db.delete(key)
            await db.commit()
            return True
        return False

    async def get_decrypted_api_key(self, db: AsyncSession, tenant_id: str, key_id: str) -> Optional[dict]:
        """Internal method to get decrypted keys for trading service."""
        user = await self._get_or_create_user(db, tenant_id)
        result = await db.execute(select(DBAPIKey).where(DBAPIKey.id == key_id, DBAPIKey.user_id == user.id))
        key = result.scalars().first()
        
        if not key:
            return None
            
        return {
            "api_key": cipher_suite.decrypt(key.api_key_encrypted.encode()).decode(),
            "api_secret": cipher_suite.decrypt(key.api_secret_encrypted.encode()).decode(),
            "passphrase": cipher_suite.decrypt(key.passphrase_encrypted.encode()).decode() if key.passphrase_encrypted else None
        }

# Global instance for dependency injection if needed, but methods now require db session
_service = UserSettingsService()

def get_settings_service() -> UserSettingsService:
    return _service
