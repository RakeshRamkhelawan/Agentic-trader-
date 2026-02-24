import logging
import os
from functools import lru_cache
from typing import Protocol

logger = logging.getLogger(__name__)


class SecretBackend(Protocol):
    def get_secret(self, path: str, key: str) -> str: ...

    def is_connected(self) -> bool: ...


class VaultBackend:
    def __init__(self, vault_manager):
        self._vault = vault_manager

    def get_secret(self, path: str, key: str) -> str:
        return self._vault.get_secret(path, key)

    def is_connected(self) -> bool:
        return self._vault.is_connected


class EnvBackend:
    def get_secret(self, path: str, key: str) -> str:
        env_key = f"{path.upper().replace('/', '_')}_{key.upper()}"
        value = os.getenv(env_key)
        if value:
            return value
        return os.getenv(key.upper(), "")

    def is_connected(self) -> bool:
        return True


class SecretManager:
    def __init__(
        self,
        primary_backend: SecretBackend | None = None,
        fallback_backend: SecretBackend | None = None,
        cache_enabled: bool = True,
    ):
        self._primary = primary_backend
        self._fallback = fallback_backend or EnvBackend()
        self._cache_enabled = cache_enabled
        self._cache: dict[str, str] = {}

        if self._primary and self._primary.is_connected():
            logger.info("SecretManager: Using primary backend (Vault)")
        else:
            logger.warning("SecretManager: Primary backend unavailable, using fallback")

    def get_secret(self, path: str, key: str, default: str | None = None) -> str:
        cache_key = f"{path}/{key}"

        if self._cache_enabled and cache_key in self._cache:
            return self._cache[cache_key]

        try:
            if self._primary and self._primary.is_connected():
                value = self._primary.get_secret(path, key)
                if value:
                    if self._cache_enabled:
                        self._cache[cache_key] = value
                    return value
        except Exception as e:
            logger.warning(f"SecretManager: Primary backend failed for {cache_key}: {e}")

        try:
            value = self._fallback.get_secret(path, key)
            if value:
                if self._cache_enabled:
                    self._cache[cache_key] = value
                return value
        except Exception as e:
            logger.warning(f"SecretManager: Fallback backend failed for {cache_key}: {e}")

        if default is not None:
            return default

        return ""

    def get_api_key(self, service: str) -> str:
        return self.get_secret(service, "api_key")

    def get_database_url(self) -> str:
        return self.get_secret("database", "url", default="sqlite:///./test.db")

    def clear_cache(self) -> None:
        self._cache.clear()
        logger.debug("SecretManager: Cache cleared")

    @property
    def is_vault_connected(self) -> bool:
        return self._primary is not None and self._primary.is_connected()


@lru_cache(maxsize=1)
def get_secret_manager() -> SecretManager:
    try:
        from backend.core.security.vault_manager import get_vault_manager

        vault = get_vault_manager()
        primary = VaultBackend(vault) if vault.is_connected else None
    except Exception as e:
        logger.warning(f"SecretManager: Failed to initialize Vault backend: {e}")
        primary = None

    return SecretManager(primary_backend=primary)
