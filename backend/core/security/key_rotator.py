"""
Key Rotator - Automated Ed25519 Key Pair Rotation

Provides:
- Ed25519 key pair generation
- Key rotation with Vault storage
- Public key upload to exchange APIs
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, Tuple

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

logger = logging.getLogger(__name__)


class KeyRotator:
    """
    Ed25519 Key Rotation Service.

    Manages cryptographic key lifecycle:
    - Generation of new key pairs
    - Storage in HashiCorp Vault with versioning
    - Upload of public keys to exchange APIs
    """

    # Default rotation interval (90 days)
    DEFAULT_ROTATION_DAYS = 90

    def __init__(
        self,
        vault_path: str = "keys/exchange",
        rotation_days: int = DEFAULT_ROTATION_DAYS,
        vault_manager=None,
    ):
        """
        Initialize KeyRotator.

        Args:
            vault_path: Vault path for key storage
            rotation_days: Days between key rotations
            vault_manager: Optional VaultManager instance
        """
        self.vault_path = vault_path
        self.rotation_days = rotation_days
        self._vault_manager = vault_manager
        self._current_private_key: Optional[bytes] = None
        self._current_public_key: Optional[bytes] = None
        self._last_rotation: Optional[datetime] = None

    def generate_key_pair(self) -> Tuple[bytes, bytes]:
        """
        Generate a new Ed25519 key pair.

        Returns:
            Tuple of (private_key_pem, public_key_pem) as bytes
        """
        # Generate new Ed25519 key pair
        private_key = Ed25519PrivateKey.generate()
        public_key = private_key.public_key()

        # Serialize to PEM format
        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )

        public_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )

        logger.info("Generated new Ed25519 key pair")
        return private_pem, public_pem

    def rotate_key(self) -> bool:
        """
        Perform key rotation.

        1. Generate new key pair
        2. Store private key in Vault (with versioning)
        3. Update local cache

        Returns:
            True if rotation successful, False otherwise
        """
        try:
            # Generate new keys
            private_pem, public_pem = self.generate_key_pair()

            # Store in Vault if available
            if self._vault_manager:
                success = self._vault_manager.rotate_key(
                    path=self.vault_path, new_value=private_pem
                )
                if not success:
                    logger.error("Failed to store key in Vault")
                    return False

            # Update local cache
            self._current_private_key = private_pem
            self._current_public_key = public_pem
            self._last_rotation = datetime.utcnow()

            logger.info(f"Key rotation successful at {self._last_rotation}")
            return True

        except Exception as e:
            logger.error(f"Key rotation failed: {e}")
            return False

    def get_current_public_key(self) -> bytes:
        """
        Get the current public key.

        Returns:
            Public key as PEM-encoded bytes
        """
        if self._current_public_key is None:
            # Generate initial key pair if none exists
            (
                self._current_private_key,
                self._current_public_key,
            ) = self.generate_key_pair()
            self._last_rotation = datetime.utcnow()

        return self._current_public_key

    def get_current_private_key(self) -> bytes:
        """
        Get the current private key.

        Returns:
            Private key as PEM-encoded bytes
        """
        if self._current_private_key is None:
            (
                self._current_private_key,
                self._current_public_key,
            ) = self.generate_key_pair()
            self._last_rotation = datetime.utcnow()

        return self._current_private_key

    def needs_rotation(self) -> bool:
        """
        Check if key rotation is due.

        Returns:
            True if rotation is needed, False otherwise
        """
        if self._last_rotation is None:
            return True

        rotation_due = self._last_rotation + timedelta(days=self.rotation_days)
        return datetime.utcnow() >= rotation_due

    @classmethod
    def from_settings(cls, settings=None) -> "KeyRotator":
        """
        Create KeyRotator from application settings.

        Args:
            settings: Optional Settings instance

        Returns:
            Configured KeyRotator instance
        """
        if settings is None:
            from backend.core.config.settings import settings

        vault_manager = None
        if settings.VAULT_ENABLED:
            from backend.core.security.vault_manager import get_vault_manager

            vault_manager = get_vault_manager()

        return cls(vault_manager=vault_manager)
