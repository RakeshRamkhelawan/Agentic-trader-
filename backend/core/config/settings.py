import os
from functools import cached_property
from typing import List, Optional

from pydantic import Field  # Explicit import
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Central Configuration.
    Reads from environment variables or .env file.
    Supports HashiCorp Vault for sensitive secrets when VAULT_ENABLED=True.

    Priority Order: Vault -> K8s Secrets -> Environment Variables -> Defaults
    """

    # --- APP INFO ---
    APP_NAME: str = "Agentic Trader Platform"
    ENV: str = "development"  # development, production, test
    DEBUG: bool = True

    # --- VAULT CONFIGURATION ---
    VAULT_ENABLED: bool = False
    VAULT_ADDR: str = "http://localhost:8200"
    VAULT_TOKEN: Optional[str] = None
    VAULT_ROLE_ID: Optional[str] = None
    VAULT_SECRET_ID: Optional[str] = None

    # --- INFRASTRUCTURE URLs ---
    KAFKA_BOOTSTRAP_SERVERS: str = "localhost:9092"
    CLICKHOUSE_HOST: str = "localhost"
    CLICKHOUSE_PORT: int = 8123
    CLICKHOUSE_USER: str = "default"
    CLICKHOUSE_PASSWORD: str = ""
    CLICKHOUSE_DB: str = "trading_db"
    REDIS_URL: str = "redis://localhost:6379/0"
    CHROMA_HOST: str = "localhost"
    CHROMA_PORT: int = 8000

    # --- SECURITY (Non-sensitive defaults) ---
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8000"]
    ALLOWED_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://127.0.0.1:3000"],
        description="CORS allowed origins. Override via ALLOWED_ORIGINS env var (JSON list).",
    )
    DOCS_ENABLED: bool = Field(
        default=True,
        description="Enable /docs and /redoc. Set DOCS_ENABLED=false in production.",
    )
    # Pydantic will load REVOLUT_API_KEY from .env
    REVOLUT_API_KEY_ENV: Optional[str] = Field(None, validation_alias="REVOLUT_API_KEY")
    REVOLUT_PRIVATE_KEY_PATH: str = "revolut_private.pem"
    REVOLUT_SANDBOX: bool = True
    _jwt_secret_key: Optional[str] = None  # Deprecated, use env field below
    JWT_SECRET_KEY_ENV: Optional[str] = Field(None, validation_alias="JWT_SECRET_KEY")

    _database_url: Optional[str] = None  # Deprecated, use env field below
    DATABASE_URL_ENV: Optional[str] = Field(None, validation_alias="DATABASE_URL")

    # --- AUTH0 CONFIGURATION ---
    AUTH0_DOMAIN: str = "agentictrader.eu.auth0.com"
    AUTH0_API_AUDIENCE: str = "https://api.agentic-trader.com"
    AUTH0_ISSUER: str = "https://agentictrader.eu.auth0.com/"
    AUTH0_ALGORITHM: str = "RS256"

    # --- METRICS ---
    METRICS_SERVER_PORT: int = 8001

    # --- RISK LIMITS (Hardcoded defaults for safety) ---
    MAX_ORDER_SIZE_EUR: float = 1000.0
    MAX_DAILY_LOSS_EUR: float = 50.0

    # --- TRADING CONTROLS ---
    TRADING_MODE: str = "paper"  # paper, live, backtest
    KILL_SWITCH: bool = False
    BYBIT_USE_EU: bool = False

    # --- LOCATION (for Vedic Calculations) ---
    LATITUDE: float = 28.6139  # New Delhi (Default)
    LONGITUDE: float = 77.2090

    # --- MARKET DATA (Phase 2) ---
    EXCHANGE_ID: str = "bitvavo"  # Options: bitvavo, kraken, binance, etc.
    EXCHANGE_API_KEY: Optional[str] = Field(
        default=None, validation_alias="BITVAVO_API_KEY"
    )
    EXCHANGE_SECRET: Optional[str] = Field(
        default=None, validation_alias="BITVAVO_API_SECRET"
    )
    ENABLE_REALTIME_DATA: bool = False

    # --- BITVAVO SPECIFIC ---
    BITVAVO_API_KEY: Optional[str] = None
    BITVAVO_API_SECRET: Optional[str] = None
    BITVAVO_SANDBOX: bool = False

    # Pydantic Settings Config
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore", case_sensitive=True
    )

    @cached_property
    def _vault_manager(self):
        """Lazy-load VaultManager only when needed."""
        if self.VAULT_ENABLED:
            from backend.core.security.vault_manager import VaultManager

            return VaultManager(
                vault_addr=self.VAULT_ADDR,
                vault_token=self.VAULT_TOKEN,
                role_id=self.VAULT_ROLE_ID,
                secret_id=self.VAULT_SECRET_ID,
            )
        return None

    @property
    def REVOLUT_API_KEY(self) -> str:
        """Get Revolut API key from Vault or environment."""
        if self.VAULT_ENABLED and self._vault_manager:
            value = self._vault_manager.get_secret("revolut", "api_key")
            if value:
                return value
        return self.REVOLUT_API_KEY_ENV or ""

    @property
    def REVOLUT_PRIVATE_KEY(self) -> str:
        """Read private key content from file path."""
        try:
            # Strip quotes that might be left from .env parsing
            path = self.REVOLUT_PRIVATE_KEY_PATH.strip('"').strip("'")

            if not os.path.exists(path):
                # Check root directory relative to CWD if absolute fails
                if not os.path.isabs(path) and os.path.exists(os.path.abspath(path)):
                    path = os.path.abspath(path)
                else:
                    print(f"Private Key File not found at: {path}")
                    return ""

            with open(path, "r") as f:
                return f.read()
        except Exception as e:
            # logger isn't available in settings usually, print or ignore
            print(f"Error reading private key: {e}")
            return ""

    @property
    def JWT_SECRET_KEY(self) -> str:
        """Get JWT secret key from Vault or environment."""
        if self.VAULT_ENABLED and self._vault_manager:
            value = self._vault_manager.get_secret("auth", "jwt_secret")
            if value:
                return value
        # No fallback default - must be explicitly set in .env or Vault
        return self.JWT_SECRET_KEY_ENV or self._jwt_secret_key or ""

    @property
    def DATABASE_URL(self) -> str:
        """Get database URL from Vault or environment."""
        if self.VAULT_ENABLED and self._vault_manager:
            value = self._vault_manager.get_secret("database", "url")
            if value:
                return value
        return (
            self.DATABASE_URL_ENV
            or self._database_url
            or "postgresql+asyncpg://localhost:5432/agentic_trader"
        )


# Singleton instance
settings = Settings()
