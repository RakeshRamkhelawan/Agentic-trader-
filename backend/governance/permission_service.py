"""
Permission Service - RBAC enforcement en audit logging.

Service voor permission checks en tracking van mode changes.
"""

import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, UTC
from sqlalchemy import Column, String, Integer, DateTime, Text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from backend.core.database import Base
from backend.governance.trading_permissions import (
    TradingRole,
    TradingPermission,
    PermissionDeniedError,
    has_permission
)

logger = logging.getLogger(__name__)


class TradingModeChange(Base):
    """
    Audit trail voor trading mode changes.
    
    Tracks wie, wanneer, en waarom TRADING_MODE is gewijzigd.
    """
    
    __tablename__ = "trading_mode_changes"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(64), nullable=False, index=True)
    user_role = Column(String(32), nullable=False)
    previous_mode = Column(String(16), nullable=False)
    new_mode = Column(String(16), nullable=False)
    reason = Column(Text, nullable=True)
    approved_by = Column(String(64), nullable=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(UTC), nullable=False, index=True)
    
    def __repr__(self):
        return f"<TradingModeChange {self.user_id}: {self.previous_mode} → {self.new_mode}>"


class PermissionService:
    """
    Permission service voor RBAC enforcement.
    
    Features:
    - Permission checking
    - Role retrieval
    - Audit logging van mode changes
    """
    
    def __init__(
        self,
        db_session: AsyncSession,
        role_provider: Optional[Any] = None
    ):
        """
        Initialize PermissionService.
        
        Args:
            db_session: Async database session
            role_provider: Optional role provider (default: hardcoded mapping)
        """
        self.db_session = db_session
        self.role_provider = role_provider
        
        # Hardcoded role mapping voor development
        # In productie: gebruik JWT claims of database
        self._user_roles: Dict[str, TradingRole] = {
            "admin": TradingRole.ADMIN,
            "operator": TradingRole.OPERATOR,
            "viewer": TradingRole.VIEWER
        }
    
    def get_user_role(self, user_id: str) -> TradingRole:
        """
        Get role voor user.
        
        Args:
            user_id: User identifier
        
        Returns:
            TradingRole
        
        Raises:
            ValueError: Als user niet gevonden
        """
        if self.role_provider:
            return self.role_provider.get_role(user_id)
        
        # Fallback: hardcoded mapping
        role = self._user_roles.get(user_id)
        if not role:
            logger.warning(f"Unknown user {user_id}, defaulting to VIEWER")
            return TradingRole.VIEWER
        
        return role
    
    def check_permission(
        self,
        user_id: str,
        permission: TradingPermission
    ) -> bool:
        """
        Check of user permission heeft.
        
        Args:
            user_id: User identifier
            permission: Required permission
        
        Returns:
            True if user has permission
        """
        try:
            role = self.get_user_role(user_id)
            return has_permission(role, permission)
        except Exception as e:
            logger.error(f"Permission check error for {user_id}: {e}")
            return False
    
    def require_permission(
        self,
        user_id: str,
        permission: TradingPermission
    ):
        """
        Require permission (raises exception als niet gevonden).
        
        Args:
            user_id: User identifier
            permission: Required permission
        
        Raises:
            PermissionDeniedError: Als user geen permission heeft
        """
        role = self.get_user_role(user_id)
        
        if not has_permission(role, permission):
            logger.warning(
                f"Permission denied: user={user_id}, role={role}, "
                f"permission={permission}"
            )
            raise PermissionDeniedError(user_id, permission, role)
        
        logger.debug(f"Permission granted: {user_id} has {permission}")
    
    async def log_mode_change(
        self,
        user_id: str,
        previous_mode: str,
        new_mode: str,
        reason: Optional[str] = None,
        approved_by: Optional[str] = None
    ) -> TradingModeChange:
        """
        Log trading mode change naar database.
        
        Args:
            user_id: User die change maakte
            previous_mode: Oude mode
            new_mode: Nieuwe mode
            reason: Optionele reden
            approved_by: Optionele approver
        
        Returns:
            TradingModeChange record
        """
        role = self.get_user_role(user_id)
        
        change = TradingModeChange(
            user_id=user_id,
            user_role=role.value,
            previous_mode=previous_mode,
            new_mode=new_mode,
            reason=reason,
            approved_by=approved_by
        )
        
        self.db_session.add(change)
        await self.db_session.commit()
        await self.db_session.refresh(change)
        
        logger.info(
            f"TRADING_MODE changed: {previous_mode} → {new_mode} "
            f"(user={user_id}, role={role}, reason={reason})"
        )
        
        return change
    
    async def get_mode_changes(
        self,
        user_id: Optional[str] = None,
        limit: int = 100
    ) -> List[TradingModeChange]:
        """
        Get recent mode changes.
        
        Args:
            user_id: Optional filter by user
            limit: Max results
        
        Returns:
            List van TradingModeChange records
        """
        query = select(TradingModeChange).order_by(
            TradingModeChange.timestamp.desc()
        ).limit(limit)
        
        if user_id:
            query = query.where(TradingModeChange.user_id == user_id)
        
        result = await self.db_session.execute(query)
        return list(result.scalars().all())
    
    def set_user_role(self, user_id: str, role: TradingRole):
        """
        Set user role (development helper).
        
        Args:
            user_id: User identifier
            role: Trading role
        """
        self._user_roles[user_id] = role
        logger.info(f"Role set: {user_id} → {role}")
