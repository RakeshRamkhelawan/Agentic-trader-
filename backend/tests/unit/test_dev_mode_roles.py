def test_dev_mode_roles():
    """Verify dev mode assigns 'viewer' role by default."""
    from backend.core.auth.middleware import AuthMiddleware

    # We can mock or just create the middleware
    middleware = AuthMiddleware(app=None)

    import os

    os.environ["DEVELOPMENT_MODE"] = "true"
    payload = middleware._create_dev_payload("test-token")

    assert "viewer" in payload.roles, f"Expected 'viewer' role in dev payload, got {payload.roles}"
    assert "admin" not in payload.roles, "Dev mode should not grant 'admin' role by default"
