import clickhouse_connect
import os
from backend.core.config.settings import settings

def list_dbs():
    print(f"Connecting to {settings.CLICKHOUSE_HOST}:{settings.CLICKHOUSE_PORT}...")
    client = clickhouse_connect.get_client(
        host=settings.CLICKHOUSE_HOST,
        port=settings.CLICKHOUSE_PORT,
        username=settings.CLICKHOUSE_USER,
        password=settings.CLICKHOUSE_PASSWORD,
        database="trading_db"
    )
    print("Connected to trading_db.")
    result = client.command("SHOW DATABASES")
    print("Databases:", result)

if __name__ == "__main__":
    list_dbs()
