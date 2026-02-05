from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """
    Central Configuration.
    Reads from environment variables or .env file.
    """
    
    # --- APP INFO ---
    APP_NAME: str = "Agentic Trader Platform"
    ENV: str = "development" # development, production, test
    DEBUG: bool = True
    
    # --- INFRASTRUCTURE URLs ---
    KAFKA_BOOTSTRAP_SERVERS: str = "localhost:9092"
    CLICKHOUSE_HOST: str = "localhost"
    CLICKHOUSE_PORT: int = 8123
    REDIS_URL: str = "redis://localhost:6379/0"
    CHROMA_HOST: str = "localhost" # NIEUW
    CHROMA_PORT: int = 8000 # NIEUW
    
    # --- SECURITY ---
    REVOLUT_API_KEY: Optional[str] = None
    REVOLUT_PRIVATE_KEY_PATH: str = "revolut_private.pem"
    REVOLUT_SANDBOX: bool = True
    
    # --- METRICS ---
    METRICS_SERVER_PORT: int = 8001
    
    # --- RISK LIMITS (Hardcoded defaults for safety) ---
    MAX_ORDER_SIZE_EUR: float = 1000.0
    MAX_DAILY_LOSS_EUR: float = 50.0
    
    # Pydantic Settings Config
    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=True
    )

# Singleton instance
settings = Settings()