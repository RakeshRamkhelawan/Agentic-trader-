"""
Authentication and SSO integration.

Features:
- SAML 2.0 SSO
- OIDC/OAuth 2.0
- JWT token management
- Enterprise SSO providers
"""

from .sso_manager import SSOManager, SAMLProvider, OIDCProvider, sso_manager
from .jwt_handler import JWTHandler, jwt_handler

__all__ = [
    "SSOManager",
    "SAMLProvider",
    "OIDCProvider",
    "sso_manager",
    "JWTHandler",
    "jwt_handler",
]
