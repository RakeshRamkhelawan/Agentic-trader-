import os
from functools import cached_property

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
    ENV: str = Field(
        default="production",
        validation_alias="ENV",
        description="Environment: development, production, test",
    )
    DEBUG: bool = Field(
        default=False,
        validation_alias="DEBUG",
        description="DEBUG mode - NEVER enable in production!",
    )

    # --- VAULT CONFIGURATION ---
    VAULT_ENABLED: bool = False
    VAULT_ADDR: str = "http://localhost:8200"
    VAULT_TOKEN: str | None = None
    VAULT_ROLE_ID: str | None = None
    VAULT_SECRET_ID: str | None = None

    # --- INFRASTRUCTURE URLs ---
    KAFKA_BOOTSTRAP_SERVERS: str = "localhost:6000"  # Zie PORT_ALLOCATION.md
    CLICKHOUSE_HOST: str = "localhost"
    CLICKHOUSE_PORT: int = 5000  # HTTP port, was 8123, zie PORT_ALLOCATION.md
    CLICKHOUSE_HTTP_PORT: int = 5000  # Nieuw
    CLICKHOUSE_NATIVE_PORT: int = 5001  # Nieuw
    CLICKHOUSE_USER: str = "default"
    CLICKHOUSE_PASSWORD: str = ""
    CLICKHOUSE_DB: str = "trading_db"
    REDIS_URL: str = "redis://localhost:6379/0"
    CHROMA_HOST: str = "localhost"
    CHROMA_PORT: int = 8100  # Was 8000, zie PORT_ALLOCATION.md
    CHROMA_DB_HOST: str = "localhost"  # Nieuw
    CHROMA_DB_PORT: int = 8100  # Nieuw

    # --- SECURITY ---
    # CORS origins - restricted by default for security
    BACKEND_CORS_ORIGINS: list[str] = Field(
        default=[],
        validation_alias="BACKEND_CORS_ORIGINS",
        description="Allowed CORS origins. In dev: ['http://localhost:3000']. In prod: specific domains only.",
    )
    ALLOWED_ORIGINS: list[str] = Field(
        default=["http://localhost:3000", "http://127.0.0.1:3000"],
        description="CORS allowed origins. Override via ALLOWED_ORIGINS env var (JSON list).",
    )
    DOCS_ENABLED: bool = Field(
        default=True,
        description="Enable /docs and /redoc. Set DOCS_ENABLED=false in production.",
    )
    # Pydantic will load REVOLUT_API_KEY from .env
    REVOLUT_API_KEY_ENV: str | None = Field(None, validation_alias="REVOLUT_API_KEY")
    REVOLUT_PRIVATE_KEY_PATH: str = "revolut_private.pem"
    REVOLUT_SANDBOX: bool = True
    # JWT Secret - REQUIRED, no fallback for security
    # Named jwt_secret_key_raw to avoid conflict with the @property JWT_SECRET_KEY
    jwt_secret_key_raw: str = Field(
        ...,  # Required field, no default
        validation_alias="JWT_SECRET_KEY",
        description="JWT signing secret - MUST be set via environment variable (min 32 chars)",
        min_length=32,
    )



    DATABASE_URL_ENV: str | None = Field(None, validation_alias="DATABASE_URL")

    # --- DATABASE CONNECTION POOLING ---
    DB_POOL_SIZE: int = Field(
        default=10,
        ge=5,
        le=50,
        description="Database connection pool size"
    )
    DB_MAX_OVERFLOW: int = Field(
        default=20,
        ge=0,
        le=30,
        description="Max overflow connections beyond pool_size"
    )
    DB_POOL_TIMEOUT: int = Field(
        default=30,
        ge=5,
        le=60,
        description="Seconds to wait for connection from pool"
    )
    DB_POOL_RECYCLE: int = Field(
        default=3600,  # 1 hour
        ge=300,
        le=7200,
        description="Seconds after which to recycle connections"
    )

    # --- AUTH0 CONFIGURATION ---
    # Use environment variables - NO hardcoded values for security
    AUTH0_DOMAIN: str = Field(
        default="",
        validation_alias="AUTH0_DOMAIN",
        description="Auth0 tenant domain (e.g., your-app.auth0.com)",
    )
    AUTH0_API_AUDIENCE: str = Field(
        default="", validation_alias="AUTH0_API_AUDIENCE", description="Auth0 API identifier"
    )
    AUTH0_ISSUER: str = Field(
        default="", validation_alias="AUTH0_ISSUER", description="Auth0 token issuer URL"
    )
    AUTH0_ALGORITHM: str = Field(default="RS256", validation_alias="AUTH0_ALGORITHM")

    # Development mode - bypass Auth0 for local testing
    AUTH_DISABLED: bool = Field(
        default=False,
        validation_alias="AUTH_DISABLED",
        description="WARNING: Only for development! Disables authentication.",
    )

    # --- METRICS ---
    METRICS_SERVER_PORT: int = 9090  # Was 8001 (nu MCP Broker), zie PORT_ALLOCATION.md

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
    EXCHANGE_API_KEY: str | None = Field(default=None, validation_alias="BITVAVO_API_KEY")
    EXCHANGE_SECRET: str | None = Field(default=None, validation_alias="BITVAVO_API_SECRET")
    ENABLE_REALTIME_DATA: bool = False

    # --- BITVAVO SPECIFIC ---
    BITVAVO_API_KEY: str | None = None
    BITVAVO_API_SECRET: str | None = None
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

            with open(path) as f:
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
        # Use the Pydantic-validated field (required, min 32 chars)
        return self.jwt_secret_key_raw

    @property
    def DATABASE_URL(self) -> str:
        """Get database URL from Vault or environment."""
        if self.VAULT_ENABLED and self._vault_manager:
            value = self._vault_manager.get_secret("database", "url")
            if value:
                return value
        return (
            self.DATABASE_URL_ENV
            or "postgresql+asyncpg://localhost:5432/agentic_trader"
        )


# Singleton instance
settings = Settings()
