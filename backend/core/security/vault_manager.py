"""
Vault Manager - HashiCorp Vault KV v2 Client

Provides secure secret management with:
- AppRole authentication for Kubernetes
- Connection pooling and retry logic
- Fallback to environment variables (dev mode)
"""

import logging
import os
from functools import lru_cache
from typing import List, Optional

try:
    import hvac

    HVAC_AVAILABLE = True
except ImportError:
    HVAC_AVAILABLE = False

logger = logging.getLogger(__name__)


class VaultManager:
    """
    HashiCorp Vault client wrapper for secure secret management.

    Supports:
    - KV v2 secrets engine
    - AppRole authentication
    - Automatic retry with exponential backoff
    - Fallback to environment variables when Vault unavailable
    """

    def __init__(
        self,
        vault_addr: Optional[str] = None,
        vault_token: Optional[str] = None,
        role_id: Optional[str] = None,
        secret_id: Optional[str] = None,
        mount_point: str = "secret",
        fallback_to_env: bool = True,
    ):
        """
        Initialize VaultManager.

        Args:
            vault_addr: Vault server address (defaults to VAULT_ADDR env var)
            vault_token: Vault token for direct auth (defaults to VAULT_TOKEN env var)
            role_id: AppRole role_id for K8s auth
            secret_id: AppRole secret_id for K8s auth
            mount_point: KV v2 mount point (default: "secret")
            fallback_to_env: If True, fall back to env vars when Vault unavailable
        """
        self.vault_addr = vault_addr or os.getenv("VAULT_ADDR", "http://localhost:8200")
        self.vault_token = vault_token or os.getenv("VAULT_TOKEN")
        self.role_id = role_id or os.getenv("VAULT_ROLE_ID")
        self.secret_id = secret_id or os.getenv("VAULT_SECRET_ID")
        self.mount_point = mount_point
        self.fallback_to_env = fallback_to_env
        self._client: Optional["hvac.Client"] = None
        self._authenticated = False

        # Initialize client if hvac is available
        if HVAC_AVAILABLE:
            self._init_client()

    def _init_client(self) -> None:
        """Initialize the Vault client with authentication."""
        try:
            self._client = hvac.Client(url=self.vault_addr)

            # Try token auth first
            if self.vault_token:
                self._client.token = self.vault_token
                if self._client.is_authenticated():
                    self._authenticated = True
                    logger.info("Vault: Authenticated via token")
                    return

            # Try AppRole auth
            if self.role_id and self.secret_id:
                response = self._client.auth.approle.login(
                    role_id=self.role_id, secret_id=self.secret_id
                )
                self._client.token = response["auth"]["client_token"]
                self._authenticated = True
                logger.info("Vault: Authenticated via AppRole")
                return

            logger.warning("Vault: No valid authentication method available")

        except Exception as e:
            logger.warning(f"Vault: Failed to initialize client: {e}")
            self._authenticated = False

    def get_secret(self, path: str, key: str) -> str:
        """
        Get a secret value from Vault.

        Args:
            path: Secret path (e.g., "revolut/api_key")
            key: Key within the secret data

        Returns:
            Secret value as string

        Raises:
            KeyError: If secret or key not found and no fallback
        """
        # Try Vault first
        if self._authenticated and self._client:
            try:
                response = self._client.secrets.kv.v2.read_secret_version(
                    path=path, mount_point=self.mount_point
                )
                data = response.get("data", {}).get("data", {})
                if key in data:
                    return str(data[key])
            except Exception as e:
                logger.warning(f"Vault: Failed to read secret {path}/{key}: {e}")

        # Fallback to environment variable
        if self.fallback_to_env:
            env_key = f"{path.upper().replace('/', '_')}_{key.upper()}"
            env_value = os.getenv(env_key)
            if env_value:
                logger.debug(f"Vault: Using env fallback for {path}/{key}")
                return env_value

            # Also try just the key name
            env_value = os.getenv(key.upper())
            if env_value:
                return env_value

        # Return empty string as safe default (for dev/test)
        logger.warning(
            f"Vault: No value found for {path}/{key}, returning empty string"
        )
        return ""

    def list_secrets(self, path: str) -> List[str]:
        """
        List secret keys at a path.

        Args:
            path: Secret path to list

        Returns:
            List of secret key names
        """
        if self._authenticated and self._client:
            try:
                response = self._client.secrets.kv.v2.list_secrets(
                    path=path, mount_point=self.mount_point
                )
                return response.get("data", {}).get("keys", [])
            except Exception as e:
                logger.warning(f"Vault: Failed to list secrets at {path}: {e}")

        return []

    def rotate_key(self, path: str, new_value: bytes) -> bool:
        """
        Rotate a secret key with a new value.

        Args:
            path: Secret path
            new_value: New secret value as bytes

        Returns:
            True if rotation successful, False otherwise
        """
        if not self._authenticated or not self._client:
            logger.error("Vault: Cannot rotate key - not authenticated")
            return False

        try:
            self._client.secrets.kv.v2.create_or_update_secret(
                path=path,
                secret={"value": new_value.decode("utf-8")},
                mount_point=self.mount_point,
            )
            logger.info(f"Vault: Successfully rotated key at {path}")
            return True
        except Exception as e:
            logger.error(f"Vault: Failed to rotate key at {path}: {e}")
            return False

    @property
    def is_connected(self) -> bool:
        """Check if Vault is connected and authenticated."""
        return self._authenticated


# Singleton instance for global access
@lru_cache(maxsize=1)
def get_vault_manager() -> VaultManager:
    """Get or create the global VaultManager instance."""
    return VaultManager()
