"""
Unit tests for JWT Token Caching in API Gateway.
"""

import json
import time
from unittest.mock import AsyncMock

import jwt
import pytest
from fastapi import HTTPException

from backend.api.gateway import JWTManager, TokenCacheEntry


@pytest.fixture
def jwt_manager():
    """Create a JWTManager with test secret."""
    return JWTManager(
        secret_key="test-secret-key",
        algorithm="HS256",
        cache_ttl_seconds=300,
    )


@pytest.fixture
def sample_token_payload():
    """Sample token payload."""
    return {
        "tenant_id": "tenant-1",
        "account_id": "account-1",
        "roles": ["trader", "viewer"],
    }


class TestTokenCacheEntry:
    """Test cases for TokenCacheEntry."""

    def test_creation(self):
        """Test cache entry creation."""
        payload = {"test": "data"}
        entry = TokenCacheEntry(payload, time.time())

        assert entry.payload == payload
        assert entry.cached_at <= time.time()

    def test_is_expired(self):
        """Test expiration check."""
        payload = {"test": "data"}

        # Fresh entry (not expired)
        entry = TokenCacheEntry(payload, time.time())
        assert entry.is_expired(ttl_seconds=300) is False

        # Old entry (expired)
        old_entry = TokenCacheEntry(payload, time.time() - 400)
        assert old_entry.is_expired(ttl_seconds=300) is True


class TestJWTManagerHashToken:
    """Test cases for token hashing."""

    def test_hash_token_consistency(self, jwt_manager):
        """Test that same token produces same hash."""
        token = "test-token-123"
        hash1 = jwt_manager._hash_token(token)
        hash2 = jwt_manager._hash_token(token)

        assert hash1 == hash2
        assert len(hash1) == 64  # SHA256 hex length

    def test_hash_token_uniqueness(self, jwt_manager):
        """Test that different tokens produce different hashes."""
        token1 = "test-token-1"
        token2 = "test-token-2"

        hash1 = jwt_manager._hash_token(token1)
        hash2 = jwt_manager._hash_token(token2)

        assert hash1 != hash2

    def test_hash_token_never_stores_raw(self, jwt_manager):
        """Test that raw token is never stored in cache."""
        token = "sensitive-token-data"
        cache_key = jwt_manager._hash_token(token)

        # Cache key should not contain raw token
        assert token not in cache_key
        assert token not in jwt_manager._token_cache


class TestJWTManagerVerifyToken:
    """Test cases for token verification with caching."""

    @pytest.mark.asyncio
    async def test_verify_token_caches_result(self, jwt_manager, sample_token_payload):
        """Test that verified token is cached."""
        # Create a token
        token = jwt.encode(sample_token_payload, "test-secret-key", algorithm="HS256")

        # First verification (cache miss)
        payload1 = await jwt_manager.verify_token(token)
        assert jwt_manager.cache_misses == 1
        assert jwt_manager.cache_hits == 0

        # Second verification (cache hit)
        payload2 = await jwt_manager.verify_token(token)
        assert jwt_manager.cache_misses == 1
        assert jwt_manager.cache_hits == 1

        assert payload1 == payload2

    @pytest.mark.asyncio
    async def test_verify_expired_token(self, jwt_manager):
        """Test that expired token raises exception."""
        # Create expired token
        expired_payload = {
            "tenant_id": "tenant-1",
            "account_id": "account-1",
            "exp": time.time() - 3600,  # Expired 1 hour ago
        }
        token = jwt.encode(expired_payload, "test-secret-key", algorithm="HS256")

        with pytest.raises(HTTPException, match="expired"):
            await jwt_manager.verify_token(token)

    @pytest.mark.asyncio
    async def test_verify_invalid_token(self, jwt_manager):
        """Test that invalid token raises exception."""
        with pytest.raises(HTTPException, match="Invalid token"):
            await jwt_manager.verify_token("invalid-token")

    @pytest.mark.asyncio
    async def test_cache_expires_after_ttl(self, jwt_manager, sample_token_payload):
        """Test that cache entry expires after TTL."""
        # Create manager with short TTL
        manager = JWTManager(
            secret_key="test-secret-key",
            cache_ttl_seconds=0,  # Immediate expiration
        )

        token = jwt.encode(sample_token_payload, "test-secret-key", algorithm="HS256")

        # First verification
        await manager.verify_token(token)

        # Wait a bit
        time.sleep(0.01)

        # Second verification should be cache miss due to TTL
        await manager.verify_token(token)
        assert manager.cache_misses == 2


class TestJWTManagerRedisCache:
    """Test cases for Redis distributed caching."""

    @pytest.mark.asyncio
    async def test_redis_cache_write(self, jwt_manager, sample_token_payload):
        """Test that verified token is cached in Redis."""
        # Mock Redis
        mock_redis = AsyncMock()
        jwt_manager.redis = mock_redis

        token = jwt.encode(sample_token_payload, "test-secret-key", algorithm="HS256")
        await jwt_manager.verify_token(token)

        # Should have written to Redis
        mock_redis.setex.assert_called_once()
        call_args = mock_redis.setex.call_args
        assert "token_cache:" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_redis_cache_read(self, jwt_manager, sample_token_payload):
        """Test reading from Redis cache."""
        # Mock Redis with cached payload
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=json.dumps(sample_token_payload))
        jwt_manager.redis = mock_redis

        token = jwt.encode(sample_token_payload, "test-secret-key", algorithm="HS256")
        payload = await jwt_manager.verify_token(token)

        assert payload == sample_token_payload
        assert jwt_manager.cache_hits == 1


class TestJWTManagerCreateToken:
    """Test cases for token creation."""

    def test_create_token_with_roles(self, jwt_manager):
        """Test creating token with role claims."""
        token = jwt_manager.create_token(
            tenant_id="tenant-1",
            account_id="account-1",
            roles=["trader", "admin"],
            expires_in_hours=24,
        )

        # Verify token can be decoded
        payload = jwt.decode(token, "test-secret-key", algorithms=["HS256"])

        assert payload["tenant_id"] == "tenant-1"
        assert payload["account_id"] == "account-1"
        assert payload["roles"] == ["trader", "admin"]
        assert "exp" in payload
        assert "iat" in payload

    def test_create_token_expiration(self, jwt_manager):
        """Test token has correct expiration."""
        token = jwt_manager.create_token(
            tenant_id="tenant-1",
            account_id="account-1",
            roles=["viewer"],
            expires_in_hours=1,
        )

        payload = jwt.decode(token, "test-secret-key", algorithms=["HS256"])

        # Expiration should be ~1 hour from now
        expected_exp = time.time() + 3600
        assert abs(payload["exp"] - expected_exp) < 5  # Within 5 seconds


class TestJWTManagerInvalidateCache:
    """Test cases for cache invalidation."""

    @pytest.mark.asyncio
    async def test_invalidate_cache_removes_entry(
        self, jwt_manager, sample_token_payload
    ):
        """Test that cache invalidation removes entry."""
        token = jwt.encode(sample_token_payload, "test-secret-key", algorithm="HS256")

        # Verify token (adds to cache)
        await jwt_manager.verify_token(token)
        assert len(jwt_manager._token_cache) == 1

        # Invalidate
        jwt_manager.invalidate_cache(token)
        assert len(jwt_manager._token_cache) == 0

    @pytest.mark.asyncio
    async def test_invalidate_cache_redis(self, jwt_manager, sample_token_payload):
        """Test that cache invalidation removes from Redis."""
        mock_redis = AsyncMock()
        jwt_manager.redis = mock_redis

        token = jwt.encode(sample_token_payload, "test-secret-key", algorithm="HS256")
        jwt_manager.invalidate_cache(token)

        mock_redis.delete.assert_called_once()


class TestJWTManagerCacheStats:
    """Test cases for cache statistics."""

    @pytest.mark.asyncio
    async def test_get_cache_stats(self, jwt_manager, sample_token_payload):
        """Test getting cache statistics."""
        token = jwt.encode(sample_token_payload, "test-secret-key", algorithm="HS256")

        # Generate some cache activity
        await jwt_manager.verify_token(token)  # miss
        await jwt_manager.verify_token(token)  # hit
        await jwt_manager.verify_token(token)  # hit

        stats = jwt_manager.get_cache_stats()

        assert stats["cache_hits"] == 2
        assert stats["cache_misses"] == 1
        assert stats["hit_rate_percent"] == 66.67
        assert stats["cached_tokens"] == 1

    def test_clear_cache(self, jwt_manager):
        """Test clearing cache."""
        # Add some data
        jwt_manager._token_cache["test"] = TokenCacheEntry({}, time.time())
        jwt_manager.cache_hits = 10
        jwt_manager.cache_misses = 5

        jwt_manager.clear_cache()

        assert len(jwt_manager._token_cache) == 0
        assert jwt_manager.cache_hits == 0
        assert jwt_manager.cache_misses == 0


class TestRBACIntegration:
    """Test cases for RBAC integration."""

    def test_has_role_with_matching_role(self):
        """Test has_role with matching role."""
        from backend.api.gateway import has_role

        user_payload = {"roles": ["trader", "viewer"]}
        assert has_role(user_payload, ["trader"]) is True
        assert has_role(user_payload, ["viewer"]) is True

    def test_has_role_without_matching_role(self):
        """Test has_role without matching role."""
        from backend.api.gateway import has_role

        user_payload = {"roles": ["viewer"]}
        assert has_role(user_payload, ["trader"]) is False
        assert has_role(user_payload, ["admin"]) is False

    def test_has_role_with_multiple_required(self):
        """Test has_role with multiple required roles."""
        from backend.api.gateway import has_role

        user_payload = {"roles": ["trader"]}
        assert has_role(user_payload, ["trader", "admin"]) is True

    def test_has_role_empty_roles(self):
        """Test has_role with empty roles."""
        from backend.api.gateway import has_role

        user_payload = {"roles": []}
        assert has_role(user_payload, ["trader"]) is False

    def test_has_role_missing_roles_key(self):
        """Test has_role with missing roles key."""
        from backend.api.gateway import has_role

        user_payload = {}
        assert has_role(user_payload, ["trader"]) is False
