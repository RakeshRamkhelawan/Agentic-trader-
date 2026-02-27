"""
Authentication and SSO integration.

Features:
- SAML 2.0 SSO
- OIDC/OAuth 2.0
- JWT token management
- Enterprise SSO providers
"""

from .jwt_handler import JWTHandler, jwt_handler
from .sso_manager import OIDCProvider, SAMLProvider, SSOManager, sso_manager

__all__ = [
    "SSOManager",
    "SAMLProvider",
    "OIDCProvider",
    "sso_manager",
    "JWTHandler",
    "jwt_handler",
]
