"""
Redis Configuration

Configures Redis connection URL with fallback for different environments.
"""

import os


def get_redis_url() -> str:
    """
    Get Redis URL with automatic fallback.

    Priority:
    1. Environment variable REDIS_URL
    2. Docker Redis on port 6380 (Redis 7+)
    3. Local Redis on port 6379 (may be old version)
    """
    # Check environment variable first
    env_url = os.getenv("REDIS_URL")
    if env_url:
        return env_url

    # Try Docker Redis on port 6380 (mapped from container)
    # This is Redis 7+ with Streams support
    docker_url = "redis://localhost:6380"

    # Test if port 6380 is available
    import socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(2)
    try:
        result = sock.connect_ex(('localhost', 6380))
        if result == 0:
            return docker_url
    finally:
        sock.close()

    # Fallback to default port 6379
    # WARNING: May be Redis 3.x without Streams support
    return "redis://localhost:6379"


# Default Redis URL
REDIS_URL = get_redis_url()


# Stream names (for consistency)
STREAM_DELIBERATIONS = "triad.deliberations"
STREAM_DECISIONS = "triad.decisions"
STREAM_EXECUTIONS = "triad.executions"
STREAM_MARKET = "triad.market"


if __name__ == "__main__":
    print(f"Redis URL: {REDIS_URL}")

    # Test connection
    import redis
    try:
        r = redis.from_url(REDIS_URL)
        info = r.info('server')
        print(f"Redis version: {info.get('redis_version')}")

        # Test XADD
        try:
            msg_id = r.xadd('test_stream', {'test': 'value'})
            print(f"XADD works! ID: {msg_id}")
            r.delete('test_stream')
        except Exception as e:
            print(f"XADD failed: {e}")
            print("WARNING: Redis Streams not available!")

        r.close()
    except Exception as e:
        print(f"Connection failed: {e}")
