
import sys
import os
import logging

# Add project root to path
sys.path.append(os.getcwd())

from backend.storage.clickhouse_init import init_clickhouse

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("apply_migrations")

def main():
    logger.info("Starting manual migration application...")
    try:
        success = init_clickhouse()
        if success:
            logger.info("✅ Migrations applied successfully.")
            sys.exit(0)
        else:
            logger.error("❌ Migration application failed.")
            sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Exception during migration: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
