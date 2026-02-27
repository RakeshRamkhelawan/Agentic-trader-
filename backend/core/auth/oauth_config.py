
from pydantic import BaseModel, Field


class OIDCConfig(BaseModel):
    client_id: str = Field(..., env="OAUTH_CLIENT_ID")
    client_secret: str = Field(..., env="OAUTH_CLIENT_SECRET")
    discovery_url: str = Field(..., env="OAUTH_DISCOVERY_URL")
    audiences: list[str] = ["api://default"]


class OAuthConfig:
    """
    Configuration for OAuth2/OIDC integration.
    """

    def __init__(self):
        # In a real app, load from env vars
        # For now, we stub this to avoid needing actual credentials in dev
        self.enabled = False
        self.oidc_config: OIDCConfig | None = None

    def validate_token(self, token: str) -> dict:
        """
        Stub for JWT validation.
        In production, this would:
        1. Fetch JWKS from discovery_url.
        2. Verify signature.
        3. Validate claims (aud, exp, iss).
        """
        if not self.enabled:
            return {"sub": "mock_user", "scope": "read write"}

        # Mock validation
        if token == "invalid":  # nosec B105 - Test value for mock validation
            raise ValueError("Invalid token")

        return {"sub": "user_123", "tenant_id": "tenant_abc"}
