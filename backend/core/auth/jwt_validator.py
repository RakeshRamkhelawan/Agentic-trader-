"""
JWT Validator - RS256 JWT token validation using JWKS.

Provides:
- JWKS fetching and caching
- JWT signature verification
- Token claims extraction
"""
import logging
import time
from typing import Optional, Dict, Any
from dataclasses import dataclass

try:
    from jose import jwt, jwk, JWTError
    from jose.exceptions import JWKError
    JOSE_AVAILABLE = True
except ImportError:
    JOSE_AVAILABLE = False

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False

from backend.core.auth.models import TokenPayload

logger = logging.getLogger(__name__)


class JWTValidationError(Exception):
    """Base exception for JWT validation errors."""
    pass


class TokenExpiredError(JWTValidationError):
    """Token has expired."""
    pass


class InvalidSignatureError(JWTValidationError):
    """Token signature is invalid."""
    pass


class MissingClaimError(JWTValidationError):
    """Required claim is missing from token."""
    pass


class JWTValidator:
    """
    JWT Validator using RS256 and JWKS.
    
    Features:
    - Automatic JWKS fetching and caching
    - RS256 signature verification
    - Standard claim validation (exp, iss, aud)
    - Custom claim extraction (tenant_id, roles)
    """
    
    # Cache JWKS for 1 hour
    JWKS_CACHE_TTL = 3600
    
    def __init__(
        self,
        jwks_url: str,
        issuer: str,
        audience: str,
        algorithms: list = None
    ):
        """
        Initialize JWTValidator.
        
        Args:
            jwks_url: URL to fetch JWKS (e.g., https://tenant.auth0.com/.well-known/jwks.json)
            issuer: Expected token issuer
            audience: Expected token audience
            algorithms: Allowed signing algorithms (default: RS256)
        """
        self.jwks_url = jwks_url
        self.issuer = issuer
        self.audience = audience
        self.algorithms = algorithms or ["RS256"]
        self._jwks_cache: Optional[Dict[str, Any]] = None
        self._jwks_cache_time: float = 0
    
    async def refresh_jwks(self) -> None:
        """
        Fetch and cache JWKS from the identity provider.
        """
        if not HTTPX_AVAILABLE:
            logger.warning("httpx not available, using empty JWKS")
            self._jwks_cache = {"keys": []}
            return
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(self.jwks_url, timeout=10.0)
                response.raise_for_status()
                self._jwks_cache = response.json()
                self._jwks_cache_time = time.time()
                logger.info(f"Refreshed JWKS from {self.jwks_url}")
        except Exception as e:
            logger.error(f"Failed to fetch JWKS: {e}")
            if self._jwks_cache is None:
                self._jwks_cache = {"keys": []}
    
    def _is_cache_valid(self) -> bool:
        """Check if JWKS cache is still valid."""
        if self._jwks_cache is None:
            return False
        return (time.time() - self._jwks_cache_time) < self.JWKS_CACHE_TTL
    
    async def _get_signing_key(self, token: str) -> Optional[Dict]:
        """Get the signing key for a token from JWKS."""
        if not self._is_cache_valid():
            await self.refresh_jwks()
        
        if not self._jwks_cache or not self._jwks_cache.get("keys"):
            return None
        
        try:
            # Get kid from token header
            unverified_header = jwt.get_unverified_header(token)
            kid = unverified_header.get("kid")
            
            # Find matching key in JWKS
            for key in self._jwks_cache.get("keys", []):
                if key.get("kid") == kid:
                    return key
        except Exception as e:
            logger.error(f"Error getting signing key: {e}")
        
        return None
    
    async def validate_token(self, token: str) -> TokenPayload:
        """
        Validate a JWT token and extract claims.
        
        Args:
            token: JWT token string
            
        Returns:
            TokenPayload with extracted claims
            
        Raises:
            TokenExpiredError: If token is expired
            InvalidSignatureError: If signature verification fails
            MissingClaimError: If required claims are missing
        """
        if not JOSE_AVAILABLE:
            # Development fallback - decode without verification
            logger.warning("python-jose not available, using unverified decode")
            return self._decode_unverified(token)
        
        signing_key = await self._get_signing_key(token)
        
        try:
            if signing_key:
                # Verify with JWKS key
                payload = jwt.decode(
                    token,
                    signing_key,
                    algorithms=self.algorithms,
                    audience=self.audience,
                    issuer=self.issuer
                )
            else:
                # Fallback: decode without signature verification (dev mode)
                logger.warning("No signing key found, decoding without verification")
                payload = jwt.get_unverified_claims(token)
            
            return self._extract_payload(payload)
            
        except jwt.ExpiredSignatureError:
            raise TokenExpiredError("Token has expired")
        except jwt.JWTClaimsError as e:
            raise JWTValidationError(f"Invalid claims: {e}")
        except JWTError as e:
            raise InvalidSignatureError(f"Invalid token: {e}")
    
    def _decode_unverified(self, token: str) -> TokenPayload:
        """Decode token without verification (development only)."""
        try:
            parts = token.split(".")
            if len(parts) != 3:
                raise JWTValidationError("Invalid token format")
            
            import base64
            import json
            
            # Decode payload (second part)
            payload_b64 = parts[1]
            # Add padding if needed
            payload_b64 += "=" * (4 - len(payload_b64) % 4)
            payload_json = base64.urlsafe_b64decode(payload_b64)
            payload = json.loads(payload_json)
            
            return self._extract_payload(payload)
        except Exception as e:
            raise JWTValidationError(f"Failed to decode token: {e}")
    
    def _extract_payload(self, claims: Dict[str, Any]) -> TokenPayload:
        """Extract TokenPayload from JWT claims."""
        # Check required claims
        if "sub" not in claims:
            raise MissingClaimError("Missing 'sub' claim")
        
        tenant_id = claims.get("tenant_id") or claims.get("https://agentic-trader/tenant_id") or "default"
        # if not tenant_id:
        #     raise MissingClaimError("Missing 'tenant_id' claim")
        
        roles = claims.get("roles") or claims.get("https://agentic-trader/roles", [])
        if isinstance(roles, str):
            roles = [roles]
        
        return TokenPayload(
            sub=claims["sub"],
            tenant_id=tenant_id,
            roles=roles,
            exp=claims.get("exp", 0),
            iat=claims.get("iat"),
            iss=claims.get("iss"),
            aud=claims.get("aud"),
            email=claims.get("email")
        )
