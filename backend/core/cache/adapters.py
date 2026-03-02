import json
import pickle
from abc import ABC, abstractmethod
from collections import OrderedDict
from datetime import datetime, timedelta
from typing import Any


class CacheAdapter(ABC):
    @abstractmethod
    async def get(self, key: str) -> Any | None:
        pass

    @abstractmethod
    async def set(self, key: str, value: Any, ttl: int) -> bool:
        pass

    @abstractmethod
    async def delete(self, key: str) -> bool:
        pass

    @abstractmethod
    async def clear(self) -> bool:
        pass

    @abstractmethod
    async def exists(self, key: str) -> bool:
        pass


class MemoryAdapter(CacheAdapter):
    def __init__(self, max_size: int = 1000):
        self._cache: OrderedDict = OrderedDict()
        self._expiry: dict[str, datetime] = {}
        self._max_size = max_size

    async def get(self, key: str) -> Any | None:
        if key not in self._cache:
            return None

        if key in self._expiry and datetime.utcnow() > self._expiry[key]:
            await self.delete(key)
            return None

        self._cache.move_to_end(key)
        return self._cache[key]

    async def set(self, key: str, value: Any, ttl: int) -> bool:
        if key in self._cache:
            self._cache.move_to_end(key)
        elif len(self._cache) >= self._max_size:
            self._cache.popitem(last=False)

        self._cache[key] = value
        self._expiry[key] = datetime.utcnow() + timedelta(seconds=ttl)
        return True

    async def delete(self, key: str) -> bool:
        if key in self._cache:
            del self._cache[key]
        if key in self._expiry:
            del self._expiry[key]
        return True

    async def clear(self) -> bool:
        self._cache.clear()
        self._expiry.clear()
        return True

    async def exists(self, key: str) -> bool:
        if key not in self._cache:
            return False

        if key in self._expiry and datetime.utcnow() > self._expiry[key]:
            await self.delete(key)
            return False

        return True


class RedisAdapter(CacheAdapter):
    def __init__(self, redis_client):
        self._redis = redis_client

    async def get(self, key: str) -> Any | None:
        try:
            value = await self._redis.get(key)
            if value is None:
                return None
            return pickle.loads(value)  # nosec B301 - Internal cache only, Redis not exposed externally
        except Exception:
            return None

    async def set(self, key: str, value: Any, ttl: int) -> bool:
        try:
            serialized = pickle.dumps(value)  # nosec B301 - Internal serialization for cache
            await self._redis.setex(key, ttl, serialized)
            return True
        except Exception:
            return False

    async def delete(self, key: str) -> bool:
        try:
            await self._redis.delete(key)
            return True
        except Exception:
            return False

    async def clear(self) -> bool:
        try:
            await self._redis.flushdb()
            return True
        except Exception:
            return False

    async def exists(self, key: str) -> bool:
        try:
            return await self._redis.exists(key) > 0
        except Exception:
            return False


class ClickHouseAdapter(CacheAdapter):
    # Whitelist of allowed table names to prevent SQL injection
    ALLOWED_TABLES = {"cache_store", "analytics_cache", "session_cache"}
    
    def __init__(self, clickhouse_client, table_name: str = "cache_store"):
        self._client = clickhouse_client
        # Validate table name against whitelist to prevent SQL injection
        if table_name not in self.ALLOWED_TABLES:
            raise ValueError(f"Invalid table name: {table_name}. Must be one of: {self.ALLOWED_TABLES}")
        self._table = table_name

    async def get(self, key: str) -> Any | None:
        try:
            query = """
                SELECT value, expires_at
                FROM {table}
                WHERE key = %(key)s
                AND expires_at > now()
                LIMIT 1
            """.format(table=self._table)
            result = await self._client.execute(query, {"key": key})

            if not result:
                return None

            value_json = result[0][0]
            return json.loads(value_json)
        except Exception:
            return None

    async def set(self, key: str, value: Any, ttl: int) -> bool:
        try:
            value_json = json.dumps(value)
            query = """
                INSERT INTO {table} (key, value, expires_at, created_at)
                VALUES (%(key)s, %(value)s, now() + INTERVAL %(ttl)s SECOND, now())
            """.format(table=self._table)
            await self._client.execute(query, {"key": key, "value": value_json, "ttl": ttl})
            return True
        except Exception:
            return False

    async def delete(self, key: str) -> bool:
        try:
            query = "ALTER TABLE {table} DELETE WHERE key = %(key)s".format(table=self._table)
            await self._client.execute(query, {"key": key})
            return True
        except Exception:
            return False

    async def clear(self) -> bool:
        try:
            query = "TRUNCATE TABLE {table}".format(table=self._table)
            await self._client.execute(query)
            return True
        except Exception:
            return False

    async def exists(self, key: str) -> bool:
        try:
            query = (  # nosec B608
                f"""
                SELECT count(*) FROM {self._table}
                WHERE key = %(key)s AND expires_at > now()
            """
            )
            result = await self._client.execute(query, {"key": key})
            return result[0][0] > 0
        except Exception:
            return False
