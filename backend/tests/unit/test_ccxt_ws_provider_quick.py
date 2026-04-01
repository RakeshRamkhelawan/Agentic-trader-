"""
Fase 4.1: CCXT WebSocket Provider - Quick Verification Tests

Simplified test suite to verify provider implementation works.
This is a subset of the full test suite for quick validation.
"""

import asyncio
from typing import Any, Dict
from unittest.mock import AsyncMock, patch

import pytest

from backend.market_data.providers.ccxt_ws_provider import (
    CCXTWSProvider,
    ConnectionConfig,
)


@pytest.mark.asyncio
async def test_provider_initialization():
    """Verify provider can be initialized."""
    provider = CCXTWSProvider(exchange_id="binance")

    assert provider.exchange_id == "binance"
    assert not provider.is_connected
    assert provider.get_subscription_count() == 0
    assert provider.retry_count == 0


@pytest.mark.asyncio
async def test_subscribe_before_connect_fails():
    """Verify subscribing before connection raises RuntimeError."""
    provider = CCXTWSProvider(exchange_id="binance")

    async def dummy_callback(symbol: str, data: Dict[str, Any]):
        pass

    with pytest.raises(RuntimeError, match="Provider not connected"):
        await provider.subscribe_ticker("BTC/USDT", dummy_callback)


@pytest.mark.asyncio
async def test_connect_with_mock_exchange():
    """Verify provider connects with mocked exchange."""
    with patch("ccxt.async_support.binance") as mock_exchange_class:
        # Create mock instance
        mock_instance = AsyncMock()
        mock_instance.fetch_symbols = AsyncMock(return_value=["BTC/USDT", "ETH/USDT"])
        mock_exchange_class.return_value = mock_instance

        provider = CCXTWSProvider(exchange_id="binance")
        await provider.connect()

        assert provider.is_connected
        await provider.close()


@pytest.mark.asyncio
async def test_subscribe_after_connect():
    """Verify ticker subscription works after connect."""
    with patch("ccxt.async_support.binance") as mock_exchange_class:
        mock_instance = AsyncMock()
        mock_instance.fetch_symbols = AsyncMock(return_value=["BTC/USDT", "ETH/USDT"])
        mock_exchange_class.return_value = mock_instance

        provider = CCXTWSProvider(exchange_id="binance")
        await provider.connect()

        callback_data = []

        async def on_ticker(symbol: str, data: Dict[str, Any]):
            callback_data.append((symbol, data))

        # Subscribe
        await provider.subscribe_ticker("BTC/USDT", on_ticker)
        assert provider.get_subscription_count() == 1

        # Inject simulated data
        await provider.inject_simulated_data("ticker", "BTC/USDT", {"last": 49500.0})

        # Give callback time to execute
        await asyncio.sleep(0.2)

        # Verify callback was called
        assert len(callback_data) > 0
        assert callback_data[0][0] == "BTC/USDT"
        assert callback_data[0][1]["last"] == 49500.0

        await provider.close()


@pytest.mark.asyncio
async def test_multiple_subscriptions():
    """Verify multiple subscriptions on same connection."""
    with patch("ccxt.async_support.binance") as mock_exchange_class:
        mock_instance = AsyncMock()
        mock_instance.fetch_symbols = AsyncMock(return_value=["BTC/USDT", "ETH/USDT", "SOL/USDT"])
        mock_exchange_class.return_value = mock_instance

        provider = CCXTWSProvider(exchange_id="binance")
        await provider.connect()

        all_data = {"BTC/USDT": [], "ETH/USDT": [], "SOL/USDT": []}

        async def on_ticker(symbol: str, data: Dict[str, Any]):
            if symbol in all_data:
                all_data[symbol].append(data)

        # Subscribe to all
        symbols = ["BTC/USDT", "ETH/USDT", "SOL/USDT"]
        for symbol in symbols:
            await provider.subscribe_ticker(symbol, on_ticker)

        assert provider.get_subscription_count() == 3

        # Send data for each symbol
        for symbol in symbols:
            await provider.inject_simulated_data("ticker", symbol, {"last": 50000.0})

        await asyncio.sleep(0.2)

        # Verify all received data
        for symbol in symbols:
            assert len(all_data[symbol]) > 0, f"No data for {symbol}"

        await provider.close()


@pytest.mark.asyncio
async def test_unsubscribe():
    """Verify unsubscribing works."""
    with patch("ccxt.async_support.binance") as mock_exchange_class:
        mock_instance = AsyncMock()
        mock_instance.fetch_symbols = AsyncMock(return_value=["BTC/USDT"])
        mock_exchange_class.return_value = mock_instance

        provider = CCXTWSProvider(exchange_id="binance")
        await provider.connect()

        async def on_ticker(symbol: str, data: Dict[str, Any]):
            pass

        # Subscribe
        await provider.subscribe_ticker("BTC/USDT", on_ticker)
        assert provider.get_subscription_count() == 1

        # Unsubscribe
        await provider.unsubscribe_ticker("BTC/USDT")
        assert provider.get_subscription_count() == 0

        await provider.close()


@pytest.mark.asyncio
async def test_max_retries_exceeded():
    """Verify max retries exceeded causes ConnectionError."""
    with patch("ccxt.async_support.binance", side_effect=Exception("Connection refused")):
        provider = CCXTWSProvider(
            exchange_id="binance",
            config=ConnectionConfig(max_retries=2, initial_backoff_ms=10),
        )

        with pytest.raises(ConnectionError, match="Failed to connect after"):
            await provider.connect()


@pytest.mark.asyncio
async def test_config_custom_values():
    """Verify custom configuration works."""
    config = ConnectionConfig(
        exchange_id="kraken",
        testnet=True,
        max_retries=3,
        heartbeat_interval_s=15,
        heartbeat_timeout_s=45,
    )

    provider = CCXTWSProvider(exchange_id="kraken", config=config)

    assert provider.config.testnet is True
    assert provider.config.max_retries == 3
    assert provider.config.heartbeat_interval_s == 15


@pytest.mark.asyncio
async def test_close_cleanup():
    """Verify close properly cleans up resources."""
    with patch("ccxt.async_support.binance") as mock_exchange_class:
        mock_instance = AsyncMock()
        mock_instance.fetch_symbols = AsyncMock(return_value=["BTC/USDT"])
        mock_exchange_class.return_value = mock_instance

        provider = CCXTWSProvider(exchange_id="binance")
        await provider.connect()

        assert provider.is_connected
        assert provider.get_subscription_count() == 0

        # Add subscription
        async def on_ticker(symbol: str, data: Dict[str, Any]):
            pass

        await provider.subscribe_ticker("BTC/USDT", on_ticker)
        assert provider.get_subscription_count() == 1

        # Close
        await provider.close()

        assert not provider.is_connected
        assert provider.get_subscription_count() == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
