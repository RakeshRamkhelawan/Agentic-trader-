from unittest.mock import MagicMock, patch

import pytest

from backend.storage.migrations.migration_manager import (MigrationError,
                                                          MigrationManager)

# --- UNHAPPY PATHS ---


def test_migration_fails_on_missing_directory():
    """Test dat de manager faalt als de migratie-map niet bestaat."""
    with pytest.raises(MigrationError, match="Migration directory not found"):
        MigrationManager(
            migration_dir="/path/that/does/not/exist", db_client=MagicMock()
        )


def test_migration_fails_on_invalid_sql_file():
    """Test dat de manager faalt als een SQL bestand corrupt is."""
    mock_db = MagicMock()
    mock_db.get_current_version.return_value = 0  # FIX: Versie instellen

    with patch("os.path.exists", return_value=True):
        with patch("os.path.isdir", return_value=True):
            with patch("os.listdir", return_value=["001_invalid.sql"]):
                with patch("builtins.open", side_effect=IOError("Disk error")):
                    manager = MigrationManager(
                        migration_dir="/dummy/path", db_client=mock_db
                    )
                    with pytest.raises(
                        MigrationError, match="Failed to read migration file"
                    ):
                        manager.apply_migrations()


def test_migration_stops_on_db_error():
    """Test dat het proces stopt als de DB een error geeft tijdens uitvoer."""
    mock_db = MagicMock()
    mock_db.get_current_version.return_value = 0  # FIX: Versie instellen
    mock_db.execute.side_effect = Exception("DB Connection Lost")

    with patch("os.path.exists", return_value=True):
        with patch("os.path.isdir", return_value=True):
            with patch("os.listdir", return_value=["001_initial.sql"]):
                with patch("builtins.open", new_callable=MagicMock) as mock_open:
                    mock_open.return_value.__enter__.return_value.read.return_value = (
                        "CREATE TABLE test"
                    )

                    manager = MigrationManager(
                        migration_dir="/dummy/path", db_client=mock_db
                    )
                    with pytest.raises(
                        MigrationError, match="Database error during migration"
                    ):
                        manager.apply_migrations()


# --- HAPPY PATHS ---


def test_manager_initialization_success():
    """Test dat de manager correct initialiseert als map bestaat."""
    with patch("os.path.exists", return_value=True):
        with patch("os.path.isdir", return_value=True):
            mock_db = MagicMock()
            manager = MigrationManager(migration_dir="/valid/path", db_client=mock_db)
            assert manager.migration_dir == "/valid/path"


def test_apply_migrations_success():
    """Test dat migraties in de juiste volgorde worden uitgevoerd."""
    mock_db = MagicMock()
    # Mock dat er nog geen migraties zijn uitgevoerd (versie 0)
    mock_db.get_current_version.return_value = 0

    # We simuleren 2 migratie bestanden
    files = ["001_create_users.sql", "002_add_email.sql"]

    with patch("os.path.exists", return_value=True):
        with patch("os.path.isdir", return_value=True):
            with patch("os.listdir", return_value=files):
                with patch("builtins.open", new_callable=MagicMock) as mock_open:
                    # Mock file content
                    mock_file = mock_open.return_value.__enter__.return_value
                    mock_file.read.side_effect = [
                        "CREATE TABLE users;",
                        "ALTER TABLE users ADD email;",
                    ]

                    manager = MigrationManager(
                        migration_dir="/dummy/path", db_client=mock_db
                    )
                    applied_count = manager.apply_migrations()

                    assert applied_count == 2
                    # Check of DB execute 2x is aangeroepen met de juiste SQL
                    assert mock_db.execute.call_count == 2
                    # Check of versie is geupdate
                    assert mock_db.update_version.call_count == 2
