"""Tests for Phase 3 architectural cleanup."""

import inspect
import os


def test_single_websocket_manager():
    """Only one websocket manager file should exist."""
    ws_files = [
        f for f in os.listdir("backend/api") if "websocket_manager" in f and f.endswith(".py")
    ]
    assert len(ws_files) == 1, f"Expected 1 WS manager, found: {ws_files}"


def test_no_dashboard_skeleton():
    """dashboard.skeleton.py should be removed."""
    assert not os.path.exists("backend/api/dashboard.skeleton.py")


def test_single_paper_trading_ws():
    """Only one paper_trading_ws module should exist."""
    ws_files = [
        f for f in os.listdir("backend/api") if "paper_trading_ws" in f and f.endswith(".py")
    ]
    assert len(ws_files) == 1, f"Expected 1 paper_trading_ws, found: {ws_files}"


def test_dashboard_uses_asyncio_lock():
    """dashboard.py should use asyncio.Lock instead of threading.RLock."""
    source = open("backend/api/dashboard.py", encoding="utf-8").read()
    assert "threading.RLock" not in source, "Use asyncio.Lock instead of threading.RLock"
    assert "asyncio.Lock()" in source, "dashboard.py should use asyncio.Lock()"


def test_dockerfile_python_313():
    """Dockerfile should use python:3.13-slim."""
    content = open("Dockerfile", encoding="utf-8").read()
    assert "python:3.13-slim" in content, "Dockerfile must use python:3.13-slim"
    assert "python:3.12" not in content, "Dockerfile must not reference python:3.12"


def test_no_dead_gateway_files():
    """gateway.py and derivatives should be removed."""
    for name in [
        "backend/api/gateway.py",
        "backend/api/gateway_optimized.py",
        "backend/api/gateway_inference.py",
    ]:
        assert not os.path.exists(name), f"{name} should be deleted"


def test_no_dead_gateway_imports():
    """main.py should not import from gateway modules."""
    from backend.api import main

    source = inspect.getsource(main)
    assert "from backend.api.gateway" not in source


def test_trading_api_no_global_state():
    """trading_api.py must use dependency injection, not global state."""
    from backend.api import trading_api

    source = inspect.getsource(trading_api)
    assert "global " not in source, "trading_api.py should use DI, not global state"
