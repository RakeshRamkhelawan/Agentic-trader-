def test_jwt_decode_verifies_audience():
    """JWT decode must verify audience claim."""
    import inspect

    from backend.api.deps import get_current_tenant_id

    source = inspect.getsource(get_current_tenant_id)
    assert 'verify_aud": False' not in source
