def test_redis_url_valid():
    """Redis URL should have exactly one database selector."""
    import os

    url = os.getenv("REDIS_URL", "redis://localhost:6399/0")
    parts = url.split("/")
    # redis://host:port/db — should be 4 parts
    assert len(parts) == 4, f"Invalid Redis URL format: {url}"
