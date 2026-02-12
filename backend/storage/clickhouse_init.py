
import clickhouse_connect
import os
import logging
from backend.core.config.settings import settings

logger = logging.getLogger(__name__)

def get_clickhouse_client():
    """Create a ClickHouse client."""
    try:
        pw_len = len(settings.CLICKHOUSE_PASSWORD) if settings.CLICKHOUSE_PASSWORD else 0
        pw_start = settings.CLICKHOUSE_PASSWORD[:2] if settings.CLICKHOUSE_PASSWORD else ""
        logger.info(f"Connecting to ClickHouse: {settings.CLICKHOUSE_HOST}:{settings.CLICKHOUSE_PORT} User={settings.CLICKHOUSE_USER} PW_Len={pw_len} Start='{pw_start}'")
        # Connect to default DB first to ensure target DB exists
        client = clickhouse_connect.get_client(
            host=settings.CLICKHOUSE_HOST,
            port=settings.CLICKHOUSE_PORT,
            username=settings.CLICKHOUSE_USER or 'default', 
            password=settings.CLICKHOUSE_PASSWORD or ''
        )
        
        target_db = settings.CLICKHOUSE_DB
        logger.info(f"Ensuring database '{target_db}' exists...")
        client.command(f"CREATE DATABASE IF NOT EXISTS {target_db}")
        
        # Reconnect to target DB
        # Or just use the client to query fast? client.database = target_db ?
        # clickhouse_connect client is stateful?
        # Safer to get a new client for the target DB or just assume it's created and let the app connect?
        # The app uses ClickHouseClient which connects to settings.CLICKHOUSE_DB.
        # This init script ALSO needs to apply migrations TO that DB.
        
        client.close()
        
        logger.info(f"Connecting to {target_db} to apply migrations...")
        client = clickhouse_connect.get_client(
            host=settings.CLICKHOUSE_HOST,
            port=settings.CLICKHOUSE_PORT,
            username=settings.CLICKHOUSE_USER or 'default', 
            password=settings.CLICKHOUSE_PASSWORD or '',
            database=target_db
        )
        
        return client
    except Exception as e:
        logger.error(f"Failed to connect/init ClickHouse: {e}")
        return None

def init_clickhouse():
    """Initialize ClickHouse schema."""
    client = get_clickhouse_client()
    if not client:
        return False
        
    try:
        migrations_dir = os.path.join(os.path.dirname(__file__), 'migrations')
        if not os.path.exists(migrations_dir):
             logger.warning(f"Migrations directory not found: {migrations_dir}")
             return True

        # Sort files to ensure order (01_, 02_, etc.)
        migration_files = sorted([f for f in os.listdir(migrations_dir) if f.endswith('.sql')])

        for filename in migration_files:
            migration_path = os.path.join(migrations_dir, filename)
            logger.info(f"Applying migration: {filename}")
            try:
                with open(migration_path, 'r') as f:
                    sql = f.read()
                # Split by statement if needed, but usually one CREATE TABLE per file or block
                # ClickHouse client .command might handle single statement only?
                # .command() is for DDL.
                client.command(sql)
                logger.info(f"Applied migration: {filename}")
            except Exception as e:
                # Idempotency check: "Table already exists" is fine
                if "EXISTS" in str(e).upper():
                     logger.info(f"Migration {filename} skipped (already exists).")
                else:
                    logger.error(f"Failed to apply {filename}: {e}")
                    # Decide if we stop or continue. For now, log and continue/return False?
                    # return False 
            
        return True
    except Exception as e:
        logger.error(f"Failed to initialize ClickHouse schema: {e}")
        return False
