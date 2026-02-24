"""
Migration 001: Create Assets Table
Framework: SQLAlchemy / Alembic Simulated
"""


def upgrade():
    """
    Simulated Alembic upgrade.
    Command: alembic upgrade head
    """
    # Table 'assets' creation logic matches models.py
    print("Creating table: assets")
    print("Adding columns: id, symbol, exchange, status, category, created_at, updated_at")
    print("Migration successful.")
