"""JWT token handling for authentication."""

from datetime import datetime, timedelta
from typing import Any

import jwt


class JWTHandler:
    """
    Handles JWT token creation and validation.

    Supports:
    - Access tokens (short-lived)
    - Refresh tokens (long-lived)
    - Tenant-scoped claims
    """

    def __init__(
        self,
        secret_key: str = "your-secret-key-change-in-production",
        algorithm: str = "HS256",
        access_token_expire_minutes: int = 30,
        refresh_token_expire_days: int = 7,
    ):
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.access_token_expire_minutes = access_token_expire_minutes
        self.refresh_token_expire_days = refresh_token_expire_days

    def create_access_token(
        self,
        user_id: str,
        tenant_id: str,
        role: str,
        additional_claims: dict | None = None,
    ) -> str:
        """Create JWT access token."""
        now = datetime.utcnow()
        expires = now + timedelta(minutes=self.access_token_expire_minutes)

        payload = {
            "sub": user_id,
            "tenant_id": tenant_id,
            "role": role,
            "type": "access",
            "iat": now,
            "exp": expires,
        }

        if additional_claims:
            payload.update(additional_claims)

        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def create_refresh_token(self, user_id: str, tenant_id: str) -> str:
        """Create JWT refresh token."""
        now = datetime.utcnow()
        expires = now + timedelta(days=self.refresh_token_expire_days)

        payload = {
            "sub": user_id,
            "tenant_id": tenant_id,
            "type": "refresh",
            "iat": now,
            "exp": expires,
        }

        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def decode_token(self, token: str) -> dict[str, Any] | None:
        """Decode and validate JWT token."""
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm],
            )
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None

    def verify_access_token(self, token: str) -> dict[str, Any] | None:
        """Verify access token and return payload."""
        payload = self.decode_token(token)
        if payload and payload.get("type") == "access":
            return payload
        return None

    def verify_refresh_token(self, token: str) -> dict[str, Any] | None:
        """Verify refresh token and return payload."""
        payload = self.decode_token(token)
        if payload and payload.get("type") == "refresh":
            return payload
        return None

    def refresh_access_token(self, refresh_token: str) -> str | None:
        """Create new access token from refresh token."""
        payload = self.verify_refresh_token(refresh_token)
        if not payload:
            return None

        return self.create_access_token(
            user_id=payload["sub"],
            tenant_id=payload["tenant_id"],
            role=payload.get("role", "user"),
        )


# Global JWT handler
jwt_handler = JWTHandler()
