"""
User Settings API - Manages user profile, preferences, and security settings.
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.deps import get_current_tenant_id, get_db
from backend.schemas.user_settings import (AppearanceSettings, BrokerAPIKey,
                                           BrokerAPIKeyCreate,
                                           NotificationSettings,
                                           SecuritySettings, UserPreferences,
                                           UserProfile)
from backend.services.user_settings_service import (UserSettingsService,
                                                    get_settings_service)

router = APIRouter()


async def get_service() -> UserSettingsService:
    return get_settings_service()


# ============================================================================
# Profile
# ============================================================================


@router.get("/profile", response_model=UserProfile)
async def get_profile(
    tenant_id: str = Depends(get_current_tenant_id),
    service: UserSettingsService = Depends(get_service),
    db: AsyncSession = Depends(get_db),
):
    return await service.get_profile(db, tenant_id)


@router.put("/profile", response_model=UserProfile)
async def update_profile(
    profile: UserProfile,
    tenant_id: str = Depends(get_current_tenant_id),
    service: UserSettingsService = Depends(get_service),
    db: AsyncSession = Depends(get_db),
):
    return await service.update_profile(db, tenant_id, profile)


# ============================================================================
# Notifications
# ============================================================================


@router.get("/notifications", response_model=NotificationSettings)
async def get_notifications(
    tenant_id: str = Depends(get_current_tenant_id),
    service: UserSettingsService = Depends(get_service),
    db: AsyncSession = Depends(get_db),
):
    return await service.get_notifications(db, tenant_id)


@router.put("/notifications", response_model=NotificationSettings)
async def update_notifications(
    prefs: NotificationSettings,
    tenant_id: str = Depends(get_current_tenant_id),
    service: UserSettingsService = Depends(get_service),
    db: AsyncSession = Depends(get_db),
):
    return await service.update_notifications(db, tenant_id, prefs)


# ============================================================================
# Security
# ============================================================================


@router.get("/security", response_model=SecuritySettings)
async def get_security_settings(
    tenant_id: str = Depends(get_current_tenant_id),
    service: UserSettingsService = Depends(get_service),
    db: AsyncSession = Depends(get_db),
):
    return await service.get_security_settings(db, tenant_id)


@router.post("/security/2fa")
async def toggle_2fa(
    enabled: bool,
    tenant_id: str = Depends(get_current_tenant_id),
    service: UserSettingsService = Depends(get_service),
    db: AsyncSession = Depends(get_db),
):
    result = await service.toggle_2fa(db, tenant_id, enabled)
    return {"enabled": result}


@router.post("/security/password")
async def change_password(
    current_password: str,
    new_password: str,
    tenant_id: str = Depends(get_current_tenant_id),
    service: UserSettingsService = Depends(get_service),
    db: AsyncSession = Depends(get_db),
):
    # In a real app, validate old password
    return {"success": True}


# ============================================================================
# Appearance
# ============================================================================


@router.get("/appearance", response_model=AppearanceSettings)
async def get_appearance(
    tenant_id: str = Depends(get_current_tenant_id),
    service: UserSettingsService = Depends(get_service),
    db: AsyncSession = Depends(get_db),
):
    return await service.get_appearance(db, tenant_id)


@router.put("/appearance", response_model=AppearanceSettings)
async def update_appearance(
    appearance: AppearanceSettings,
    tenant_id: str = Depends(get_current_tenant_id),
    service: UserSettingsService = Depends(get_service),
    db: AsyncSession = Depends(get_db),
):
    return await service.update_appearance(db, tenant_id, appearance)


# ============================================================================
# API Keys
# ============================================================================


@router.get("/api-keys", response_model=List[BrokerAPIKey])
async def get_api_keys(
    tenant_id: str = Depends(get_current_tenant_id),
    service: UserSettingsService = Depends(get_service),
    db: AsyncSession = Depends(get_db),
):
    return await service.get_api_keys(db, tenant_id)


@router.post("/api-keys", response_model=BrokerAPIKey)
async def add_api_key(
    request: BrokerAPIKeyCreate,
    tenant_id: str = Depends(get_current_tenant_id),
    service: UserSettingsService = Depends(get_service),
    db: AsyncSession = Depends(get_db),
):
    # TODO: Validate key with exchange before saving
    return await service.add_api_key(db, tenant_id, request)


@router.delete("/api-keys/{key_id}")
async def delete_api_key(
    key_id: str,
    tenant_id: str = Depends(get_current_tenant_id),
    service: UserSettingsService = Depends(get_service),
    db: AsyncSession = Depends(get_db),
):
    success = await service.delete_api_key(db, tenant_id, key_id)
    if not success:
        raise HTTPException(status_code=404, detail="API key not found")
    return {"success": True}


# ============================================================================
# Preferences
# ============================================================================


@router.get("/preferences", response_model=UserPreferences)
async def get_preferences(
    tenant_id: str = Depends(get_current_tenant_id),
    service: UserSettingsService = Depends(get_service),
    db: AsyncSession = Depends(get_db),
):
    return await service.get_preferences(db, tenant_id)


@router.put("/preferences", response_model=UserPreferences)
async def update_preferences(
    prefs: UserPreferences,
    tenant_id: str = Depends(get_current_tenant_id),
    service: UserSettingsService = Depends(get_service),
    db: AsyncSession = Depends(get_db),
):
    return await service.update_preferences(db, tenant_id, prefs)


@router.get("/all")
async def get_all_settings(
    tenant_id: str = Depends(get_current_tenant_id),
    service: UserSettingsService = Depends(get_service),
    db: AsyncSession = Depends(get_db),
):
    """Aggregate all settings for initial load."""
    return {
        "profile": await service.get_profile(db, tenant_id),
        "notifications": await service.get_notifications(db, tenant_id),
        "security": await service.get_security_settings(db, tenant_id),
        "appearance": await service.get_appearance(db, tenant_id),
        "preferences": await service.get_preferences(db, tenant_id),
        "api_keys": await service.get_api_keys(db, tenant_id),
    }
