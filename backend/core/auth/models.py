"""
Auth Models - Data structures for authentication system.
"""

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class TokenPayload:
    """
    JWT Token Payload structure.

    Contains claims extracted from validated JWT tokens.
    """

    sub: str  # Subject (user ID)
    tenant_id: str = "default"  # Default if missing in token (e.g. strict Auth0 setup not yet done)
    roles: list[str] = field(default_factory=list)  # User roles
    exp: int = 0  # Expiration timestamp
    iat: int | None = None  # Issued at timestamp
    iss: str | None = None  # Issuer
    aud: str | None = None  # Audience
    email: str | None = None  # User email (optional claim)

    @property
    def is_expired(self) -> bool:
        """Check if token is expired."""
        return datetime.utcnow().timestamp() > self.exp

    def has_role(self, role: str) -> bool:
        """Check if user has a specific role."""
        return role in self.roles

    def has_any_role(self, roles: list[str]) -> bool:
        """Check if user has any of the specified roles."""
        return bool(set(self.roles) & set(roles))


@dataclass
class User:
    """
    User representation from token.
    """

    id: str
    tenant_id: str
    email: str | None
    roles: list[str]

    @classmethod
    def from_token_payload(cls, payload: TokenPayload) -> "User":
        """Create User from TokenPayload."""
        return cls(
            id=payload.sub,
            tenant_id=payload.tenant_id,
            email=payload.email,
            roles=payload.roles,
        )
