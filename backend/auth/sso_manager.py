"""Enterprise SSO integration (SAML/OIDC)."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class SSOProviderType(Enum):
    """SSO provider types."""
    SAML = "saml"
    OIDC = "oidc"


@dataclass
class SAMLProvider:
    """SAML 2.0 Identity Provider configuration."""
    id: str
    name: str
    entity_id: str
    sso_url: str
    slo_url: str | None = None  # Single Logout URL
    x509_cert: str = ""

    # Service Provider settings
    sp_entity_id: str = ""
    sp_acs_url: str = ""  # Assertion Consumer Service URL

    # Attribute mappings
    email_attribute: str = "email"
    name_attribute: str = "name"
    groups_attribute: str | None = None

    # Options
    require_signed_assertions: bool = True
    require_signed_response: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "type": "saml",
            "entity_id": self.entity_id,
            "sso_url": self.sso_url,
            "slo_url": self.slo_url,
            "sp_entity_id": self.sp_entity_id,
            "sp_acs_url": self.sp_acs_url,
        }


@dataclass
class OIDCProvider:
    """OpenID Connect Provider configuration."""
    id: str
    name: str

    # Provider endpoints
    issuer: str
    authorization_endpoint: str
    token_endpoint: str
    userinfo_endpoint: str
    jwks_uri: str

    # Client credentials
    client_id: str
    client_secret: str

    # Scopes to request
    scopes: list[str] = field(default_factory=lambda: ["openid", "email", "profile"])

    # Redirect URI
    redirect_uri: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "type": "oidc",
            "issuer": self.issuer,
            "authorization_endpoint": self.authorization_endpoint,
            "scopes": self.scopes,
        }


class SSOManager:
    """
    Manages SSO integrations for enterprise tenants.

    Supports:
    - SAML 2.0 (Azure AD, Okta, OneLogin, etc.)
    - OIDC/OAuth 2.0 (Google Workspace, Microsoft 365, etc.)
    """

    def __init__(self):
        self._saml_providers: dict[str, SAMLProvider] = {}
        self._oidc_providers: dict[str, OIDCProvider] = {}
        self._tenant_providers: dict[str, list[str]] = {}  # tenant_id -> provider_ids

    # SAML Provider Management
    def add_saml_provider(
        self,
        tenant_id: str,
        provider: SAMLProvider,
    ) -> SAMLProvider:
        """Add SAML provider for tenant."""
        self._saml_providers[provider.id] = provider

        if tenant_id not in self._tenant_providers:
            self._tenant_providers[tenant_id] = []
        self._tenant_providers[tenant_id].append(provider.id)

        return provider

    def get_saml_provider(self, provider_id: str) -> SAMLProvider | None:
        """Get SAML provider by ID."""
        return self._saml_providers.get(provider_id)

    def remove_saml_provider(self, tenant_id: str, provider_id: str) -> bool:
        """Remove SAML provider."""
        if provider_id in self._saml_providers:
            del self._saml_providers[provider_id]

            if tenant_id in self._tenant_providers:
                self._tenant_providers[tenant_id] = [
                    pid for pid in self._tenant_providers[tenant_id]
                    if pid != provider_id
                ]

            return True
        return False

    def generate_saml_metadata(self, provider_id: str) -> str:
        """Generate SAML Service Provider metadata XML."""
        provider = self._saml_providers.get(provider_id)
        if not provider:
            raise ValueError("Provider not found")

        # In production, use proper XML generation library
        metadata = f"""<?xml version="1.0" encoding="UTF-8"?>
<md:EntityDescriptor xmlns:md="urn:oasis:names:tc:SAML:2.0:metadata"
                     entityID="{provider.sp_entity_id}">
    <md:SPSSODescriptor protocolSupportEnumeration="urn:oasis:names:tc:SAML:2.0:protocol">
        <md:NameIDFormat>urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress</md:NameIDFormat>
        <md:AssertionConsumerService
            Binding="urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST"
            Location="{provider.sp_acs_url}"
            index="0"
            isDefault="true"/>
    </md:SPSSODescriptor>
</md:EntityDescriptor>"""

        return metadata

    def parse_saml_response(self, provider_id: str, saml_response: str) -> dict[str, Any]:
        """Parse and validate SAML response."""
        # In production, use python-saml or similar library
        # For now, return mock parsed data
        return {
            "email": "user@example.com",
            "name": "John Doe",
            "groups": ["employees"],
            "authenticated": True,
        }

    # OIDC Provider Management
    def add_oidc_provider(
        self,
        tenant_id: str,
        provider: OIDCProvider,
    ) -> OIDCProvider:
        """Add OIDC provider for tenant."""
        self._oidc_providers[provider.id] = provider

        if tenant_id not in self._tenant_providers:
            self._tenant_providers[tenant_id] = []
        self._tenant_providers[tenant_id].append(provider.id)

        return provider

    def get_oidc_provider(self, provider_id: str) -> OIDCProvider | None:
        """Get OIDC provider by ID."""
        return self._oidc_providers.get(provider_id)

    def get_oidc_authorization_url(self, provider_id: str, state: str) -> str:
        """Generate OIDC authorization URL."""
        provider = self._oidc_providers.get(provider_id)
        if not provider:
            raise ValueError("Provider not found")

        scopes = " ".join(provider.scopes)

        url = (
            f"{provider.authorization_endpoint}?"
            f"client_id={provider.client_id}&"
            f"response_type=code&"
            f"scope={scopes}&"
            f"redirect_uri={provider.redirect_uri}&"
            f"state={state}"
        )

        return url

    def exchange_oidc_code(self, provider_id: str, code: str) -> dict[str, Any]:
        """Exchange authorization code for tokens."""
        # In production, make actual HTTP request to token endpoint
        # For now, return mock tokens
        return {
            "access_token": "mock_access_token",
            "id_token": "mock_id_token",
            "refresh_token": "mock_refresh_token",
            "expires_in": 3600,
        }

    def get_oidc_userinfo(self, provider_id: str, access_token: str) -> dict[str, Any]:
        """Get user info from OIDC provider."""
        # In production, make HTTP request to userinfo endpoint
        return {
            "email": "user@example.com",
            "name": "John Doe",
            "picture": None,
        }

    # General Methods
    def get_tenant_providers(self, tenant_id: str) -> list[dict[str, Any]]:
        """Get all SSO providers for tenant."""
        provider_ids = self._tenant_providers.get(tenant_id, [])
        providers = []

        for pid in provider_ids:
            if pid in self._saml_providers:
                providers.append(self._saml_providers[pid].to_dict())
            elif pid in self._oidc_providers:
                providers.append(self._oidc_providers[pid].to_dict())

        return providers

    def initiate_sso(self, provider_id: str) -> dict[str, Any]:
        """Initiate SSO flow for provider."""
        import uuid

        state = str(uuid.uuid4())

        if provider_id in self._saml_providers:
            provider = self._saml_providers[provider_id]
            return {
                "type": "saml",
                "sso_url": provider.sso_url,
                "saml_request": "mock_saml_request",  # In production, generate proper SAMLRequest
                "relay_state": state,
            }

        elif provider_id in self._oidc_providers:
            provider = self._oidc_providers[provider_id]
            auth_url = self.get_oidc_authorization_url(provider_id, state)
            return {
                "type": "oidc",
                "authorization_url": auth_url,
                "state": state,
            }

        raise ValueError("Provider not found")

    def complete_sso(
        self,
        provider_id: str,
        response_data: dict[str, Any],
    ) -> dict[str, Any]:
        """Complete SSO flow and return user info."""
        if provider_id in self._saml_providers:
            saml_response = response_data.get("SAMLResponse")
            user_info = self.parse_saml_response(provider_id, saml_response)
            return {
                "success": True,
                "provider_type": "saml",
                "user": user_info,
            }

        elif provider_id in self._oidc_providers:
            code = response_data.get("code")
            tokens = self.exchange_oidc_code(provider_id, code)
            user_info = self.get_oidc_userinfo(provider_id, tokens["access_token"])
            return {
                "success": True,
                "provider_type": "oidc",
                "user": user_info,
                "tokens": tokens,
            }

        return {"success": False, "error": "Provider not found"}


# Global SSO manager
sso_manager = SSOManager()
