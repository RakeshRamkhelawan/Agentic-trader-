from datetime import UTC, datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class IdentityPayload(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "sub": "auth0|123456789",
                "email": "trader@example.com",
                "email_verified": True,
                "name": "John Trader",
                "picture": "https://example.com/avatar.jpg",
            }
        }
    )

    sub: str = Field(..., description="Subject (user ID)")
    email: Optional[str] = Field(None, description="User email")
    email_verified: bool = Field(False, description="Email verification status")
    name: Optional[str] = Field(None, description="Full name")
    picture: Optional[str] = Field(None, description="Profile picture URL")


class TokenClaims(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "sub": "auth0|123456789",
                "tenant_id": "tenant-abc-123",
                "roles": ["trader", "admin"],
                "exp": 1735689600,
                "iat": 1735603200,
                "iss": "https://auth.agentic-trader.com/",
                "aud": "https://api.agentic-trader.com",
                "email": "trader@example.com",
            }
        }
    )

    sub: str = Field(..., description="Subject (user ID)")
    tenant_id: str = Field("default", description="Tenant identifier")
    roles: List[str] = Field(default_factory=list, description="User roles")
    exp: int = Field(..., description="Expiration timestamp (Unix epoch)")
    iat: Optional[int] = Field(None, description="Issued at timestamp")
    iss: Optional[str] = Field(None, description="Issuer")
    aud: Optional[str] = Field(None, description="Audience")
    email: Optional[str] = Field(None, description="User email")
    scope: Optional[str] = Field(None, description="OAuth2 scopes")
    azp: Optional[str] = Field(None, description="Authorized party")

    def is_expired(self) -> bool:
        return datetime.now(UTC).timestamp() > self.exp

    def has_role(self, role: str) -> bool:
        return role in self.roles

    def has_any_role(self, required_roles: List[str]) -> bool:
        return bool(set(self.roles) & set(required_roles))


class OIDCUserInfo(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "sub": "auth0|123456789",
                "email": "trader@example.com",
                "email_verified": True,
                "name": "Test User",
                "given_name": "Test",
                "family_name": "User",
                "picture": "https://example.com/avatar.jpg",
                "locale": "en-US",
                "updated_at": 1735603200,
            }
        }
    )

    sub: str
    email: Optional[str] = None
    email_verified: Optional[bool] = False
    name: Optional[str] = None
    given_name: Optional[str] = None
    family_name: Optional[str] = None
    picture: Optional[str] = None
    locale: Optional[str] = None
    updated_at: Optional[int] = None


class SecretMetadata(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "path": "revolut/production",
                "key": "api_key",
                "version": 3,
                "created_at": "2026-01-01T00:00:00Z",
                "updated_at": "2026-02-14T00:00:00Z",
                "rotation_policy": "monthly",
            }
        }
    )

    path: str = Field(..., description="Secret path in vault")
    key: str = Field(..., description="Secret key name")
    version: Optional[int] = Field(None, description="Secret version")
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")
    rotation_policy: Optional[str] = Field(None, description="Rotation policy name")
