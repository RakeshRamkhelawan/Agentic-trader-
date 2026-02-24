import logging
import os
from typing import Any


class MigrationError(Exception):
    """Raised when a database migration fails."""

    pass


class MigrationManager:
    """
    Manages database schema migrations.

    Ensures that SQL migration files are applied in strict order.
    """

    def __init__(self, migration_dir: str, db_client: Any):
        """
        Initialize the manager.

        Args:
            migration_dir: Path to directory containing .sql files
            db_client: Database client with execute(), get_current_version() and update_version()
        """
        if not os.path.exists(migration_dir) or not os.path.isdir(migration_dir):
            raise MigrationError(f"Migration directory not found: {migration_dir}")

        self.migration_dir = migration_dir
        self.db_client = db_client
        self.logger = logging.getLogger(__name__)

    def apply_migrations(self) -> int:
        """
        Apply pending migrations.

        Returns:
            Number of migrations applied.
        """
        try:
            current_version = self.db_client.get_current_version()
        except Exception as e:
            # Als we de versie niet eens kunnen ophalen, is er iets goed mis met de DB
            raise MigrationError(f"Database error during migration: {str(e)}")

        # Haal alle .sql bestanden op en sorteer ze
        try:
            files = sorted([f for f in os.listdir(self.migration_dir) if f.endswith(".sql")])
        except Exception as e:
            raise MigrationError(f"Failed to list migration files: {str(e)}")

        applied_count = 0

        for filename in files:
            # Bestandsnaam formaat verwacht: 001_description.sql
            try:
                version = int(filename.split("_")[0])
            except ValueError:
                self.logger.warning(f"Skipping invalid migration file: {filename}")
                continue

            if version > current_version:
                self._apply_single_migration(filename, version)
                applied_count += 1

        return applied_count

    def _apply_single_migration(self, filename: str, version: int):
        """Apply a single migration file."""
        file_path = os.path.join(self.migration_dir, filename)

        try:
            with open(file_path, encoding="utf-8") as f:
                sql_content = f.read()
        except Exception as e:
            raise MigrationError(f"Failed to read migration file {filename}: {str(e)}")

        try:
            self.logger.info(f"Applying migration: {filename}")
            self.db_client.execute(sql_content)
            self.db_client.update_version(version)
        except Exception as e:
            raise MigrationError(f"Database error during migration {filename}: {str(e)}")
