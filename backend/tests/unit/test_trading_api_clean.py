def test_trading_api_no_legacy_imports():
    """Verify trading_api.py does not contain legacy or dead code imports."""
    import inspect

    import backend.api.trading_api as trading_api

    source = inspect.getsource(trading_api)
    assert "AuditAction" not in source, "Trading API must not import AuditAction"
    assert (
        "routers.trading" not in source
    ), "Trading API must not self-reference legacy routers.trading"
