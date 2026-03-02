"""
Fase 2 Integration Tests - High Priority Fixes

Tests for:
- Taak 2.1: SQLAlchemy N+1 queries fixed with lazy='selectin'
- Taak 2.2: Rate limiter circuit breaker pattern
- Taak 2.3: Frontend auth hardening (verified via TypeScript compile)

Run with: pytest backend/tests/security/test_fase2_integration.py -v
"""

import time
from unittest.mock import AsyncMock, MagicMock

import pytest


# ============================================================================
# Taak 2.1: N+1 Query Fix Tests (user_settings.py)
# ============================================================================


class TestUserModelSelectInLoading:
    """Verify User model relationships use selectin loading."""

    def test_profile_relationship_has_selectin(self):
        """Profile relationship uses selectin loading."""
        from backend.models.user_settings import User

        rel = User.__mapper__.relationships["profile"]
        assert rel.lazy == "selectin", f"Expected selectin, got {rel.lazy}"

    def test_security_relationship_has_selectin(self):
        """Security relationship uses selectin loading."""
        from backend.models.user_settings import User

        rel = User.__mapper__.relationships["security"]
        assert rel.lazy == "selectin", f"Expected selectin, got {rel.lazy}"

    def test_preferences_relationship_has_selectin(self):
        """Preferences relationship uses selectin loading."""
        from backend.models.user_settings import User

        rel = User.__mapper__.relationships["preferences"]
        assert rel.lazy == "selectin", f"Expected selectin, got {rel.lazy}"

    def test_api_keys_relationship_has_selectin(self):
        """API keys relationship uses selectin loading."""
        from backend.models.user_settings import User

        rel = User.__mapper__.relationships["api_keys"]
        assert rel.lazy == "selectin", f"Expected selectin, got {rel.lazy}"


# ============================================================================
# Taak 2.2: Rate Limiter Circuit Breaker Tests (gateway.py)
# ============================================================================


class TestRateLimiterCircuitBreaker:
    """Tests for circuit breaker pattern in RateLimiter."""

    def _make_limiter(self, rpm=60):
        """Create a RateLimiter without Redis for testing."""
        from backend.api.gateway import RateLimiter

        limiter = RateLimiter(requests_per_minute=rpm, redis_url=None)
        return limiter

    def _make_limiter_with_mock_redis(self, rpm=60):
        """Create a RateLimiter with a mock Redis client."""
        from backend.api.gateway import RateLimiter

        limiter = RateLimiter(requests_per_minute=rpm, redis_url=None)
        limiter.redis = MagicMock()
        return limiter

    def test_circuit_starts_closed(self):
        """Circuit breaker starts in CLOSED state."""
        limiter = self._make_limiter()
        assert limiter._get_circuit_state() == "CLOSED"
        assert limiter._failure_count == 0

    def test_degraded_limit_is_25_percent(self):
        """Degraded limit is 25% of normal rate, minimum 10."""
        limiter = self._make_limiter(rpm=60)
        assert limiter._degraded_limit == 15  # 60 // 4

        limiter2 = self._make_limiter(rpm=20)
        assert limiter2._degraded_limit == 10  # max(10, 20//4=5) = 10

    def test_circuit_opens_after_max_failures(self):
        """Circuit opens after MAX_FAILURES Redis failures."""
        limiter = self._make_limiter()
        for i in range(limiter.MAX_FAILURES):
            limiter._on_redis_failure(Exception(f"fail {i}"))

        assert limiter._get_circuit_state() == "OPEN"
        assert limiter._failure_count >= limiter.MAX_FAILURES

    def test_circuit_half_open_after_timeout(self):
        """Circuit transitions to HALF_OPEN after cooldown."""
        limiter = self._make_limiter()
        for i in range(limiter.MAX_FAILURES):
            limiter._on_redis_failure(Exception(f"fail {i}"))

        # Simulate time passing
        limiter._circuit_open_until = time.time() - 1  # expired
        assert limiter._get_circuit_state() == "HALF_OPEN"

    def test_circuit_resets_on_success(self):
        """Circuit resets to CLOSED on Redis success."""
        limiter = self._make_limiter()
        limiter._failure_count = 5
        limiter._circuit_open_until = time.time() + 100

        limiter._on_redis_success()
        assert limiter._get_circuit_state() == "CLOSED"
        assert limiter._failure_count == 0

    @pytest.mark.asyncio
    async def test_closed_state_allows_requests_locally(self):
        """In CLOSED state without Redis, local limit applies."""
        limiter = self._make_limiter(rpm=60)
        # Without Redis, should use degraded local limit
        result = await limiter.is_allowed("test-key")
        assert result is True

    @pytest.mark.asyncio
    async def test_open_state_uses_degraded_limit(self):
        """In OPEN state, uses strict degraded local limit."""
        limiter = self._make_limiter(rpm=60)
        # Force circuit open
        for i in range(limiter.MAX_FAILURES):
            limiter._on_redis_failure(Exception(f"fail {i}"))

        assert limiter._get_circuit_state() == "OPEN"

        # Should allow up to degraded_limit (15) requests
        for i in range(limiter._degraded_limit):
            result = await limiter.is_allowed("test-key")
            assert result is True, f"Request {i+1} should be allowed"

        # Next request should be blocked
        result = await limiter.is_allowed("test-key")
        assert result is False, "Should block after degraded limit"

    @pytest.mark.asyncio
    async def test_redis_failure_triggers_circuit(self):
        """Redis failures trigger circuit breaker."""
        limiter = self._make_limiter_with_mock_redis(rpm=60)

        # Mock Redis to fail
        mock_pipe = MagicMock()
        mock_pipe.incr = MagicMock()
        mock_pipe.ttl = MagicMock()
        mock_pipe.execute = AsyncMock(side_effect=Exception("Redis down"))
        limiter.redis.pipeline = MagicMock(return_value=mock_pipe)

        # Make MAX_FAILURES requests
        for i in range(limiter.MAX_FAILURES):
            await limiter.is_allowed(f"key-{i}")

        assert limiter._get_circuit_state() == "OPEN"


# ============================================================================
# Taak 2.3: Frontend Auth Hardening Tests
# ============================================================================


class TestFrontendConfigHardening:
    """Verify frontend config.ts changes via code inspection."""

    def test_config_ts_has_production_guard(self):
        """config.ts contains production guard for AUTH0_DOMAIN."""
        import os

        config_path = os.path.join(
            os.path.dirname(__file__),
            "..", "..", "..",
            "frontend", "src", "lib", "config.ts"
        )
        with open(config_path) as f:
            content = f.read()

        # Verify production guard exists
        assert "import.meta.env.PROD" in content, "Missing production guard"
        assert "throw new Error" in content, "Missing fatal error throw"
        assert "VITE_AUTH0_DOMAIN" in content, "Missing AUTH0_DOMAIN reference"

    def test_config_ts_isdevmode_uses_dev_check(self):
        """isDevMode uses import.meta.env.DEV, not just missing var."""
        import os

        config_path = os.path.join(
            os.path.dirname(__file__),
            "..", "..", "..",
            "frontend", "src", "lib", "config.ts"
        )
        with open(config_path) as f:
            content = f.read()

        # isDevMode must check import.meta.env.DEV
        assert "import.meta.env.DEV && !AUTH0_DOMAIN" in content, (
            "isDevMode should be 'import.meta.env.DEV && !AUTH0_DOMAIN'"
        )

    def test_config_ts_no_prod_console_logs(self):
        """Console logs are wrapped in DEV check."""
        import os

        config_path = os.path.join(
            os.path.dirname(__file__),
            "..", "..", "..",
            "frontend", "src", "lib", "config.ts"
        )
        with open(config_path) as f:
            lines = f.readlines()

        # No top-level console.log (should be inside if blocks)
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if stripped.startswith("console.log(") and not stripped.startswith("//"):
                # Check the preceding non-empty line is an if block
                prev_lines = [ln.strip() for ln in lines[max(0, i-5):i-1] if ln.strip()]
                has_guard = any(
                    "import.meta.env.DEV" in ln or "if (" in ln
                    for ln in prev_lines
                )
                assert has_guard, (
                    f"Line {i}: console.log not guarded by DEV check: {stripped}"
                )
