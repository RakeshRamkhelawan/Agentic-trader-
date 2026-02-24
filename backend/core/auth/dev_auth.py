"""
Development Authentication

Provides a bypass for authentication in development mode.
NEVER use in production!

Set AUTH_DISABLED=true in .env for local development only.
"""

import os

from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer


class DevAuthBypass:
    """Development authentication bypass."""

    def __init__(self):
        self.enabled = os.getenv("AUTH_DISABLED", "false").lower() == "true"
        if self.enabled:
            print("\n" + "=" * 60)
            print("WARNING: Authentication is DISABLED!")
            print("This should ONLY be used for local development.")
            print("=" * 60 + "\n")

    async def __call__(
        self,
        request: Request,
        credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer(auto_error=False)),
    ):
        """
        Authenticate request.

        If AUTH_DISABLED is true, returns a mock user.
        Otherwise, validates the JWT token normally.
        """
        if self.enabled:
            # Return mock user for development
            return {
                "sub": "dev-user-001",
                "email": "dev@localhost",
                "tenant_id": "dev-tenant",
                "account_id": "dev-account",
                "permissions": ["read", "write", "trade"],
            }

        # Normal JWT validation
        if not credentials:
            raise HTTPException(status_code=401, detail="Missing authentication token")

        # Import here to avoid circular dependency
        from backend.core.config.settings import settings
        from backend.security.jwt_handler import JWTHandler

        if not settings.AUTH0_DOMAIN:
            raise HTTPException(
                status_code=500,
                detail="Auth0 not configured. Set AUTH0_DOMAIN or AUTH_DISABLED=true for development.",
            )

        handler = JWTHandler(
            jwks_url=f"https://{settings.AUTH0_DOMAIN}/.well-known/jwks.json",
            audience=settings.AUTH0_API_AUDIENCE,
            issuer=settings.AUTH0_ISSUER or f"https://{settings.AUTH0_DOMAIN}/",
        )

        return await handler.verify_token(credentials)


# Singleton instance
dev_auth = DevAuthBypass()


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer(auto_error=False)),
):
    """
    Get current authenticated user.

    In development mode (AUTH_DISABLED=true), returns a mock user.
    In production, validates the JWT token from Auth0.
    """
    return await dev_auth(request, credentials)


# For use in FastAPI dependency injection
require_auth = get_current_user
