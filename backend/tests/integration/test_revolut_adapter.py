from unittest.mock import ANY, AsyncMock, MagicMock, patch

import pytest

from backend.execution.exchange_adapter import ExchangeAdapter

# Mock Key Data (Needs to be valid structure for serialization load)
MOCK_PRIVATE_KEY = "-----BEGIN PRIVATE KEY-----\nMC4CAQAwBQYDK2VwBCIEILxSKu5u8pA+A2HPCjIaZMf8QWEg04T8HzOnnyokNQ1t\n-----END PRIVATE KEY-----"


@pytest.fixture
def mock_adapter():
    with patch(
        "backend.execution.exchange_adapter.serialization.load_pem_private_key"
    ) as mock_load:
        # Mock the private key object and its sign method
        mock_key = MagicMock()
        mock_key.sign.return_value = b"mock_signature"
        mock_load.return_value = mock_key

        adapter = ExchangeAdapter(api_key="mock_key", private_key_pem=MOCK_PRIVATE_KEY)
        # Mock the http client
        adapter.client = AsyncMock()
        return adapter


@pytest.mark.asyncio
async def test_get_instruments_success(mock_adapter):
    """Happy Path: Successfully fetch instrument configurations"""
    mock_data = {
        "pairs": [
            {
                "symbol": "BTC-EUR",
                "base_currency": "BTC",
                "quote_currency": "EUR",
                "min_order_size": "0.0001",
                "max_order_size": "10.0",
            },
            {
                "symbol": "ETH-EUR",
                "base_currency": "ETH",
                "quote_currency": "EUR",
                "min_order_size": "0.01",
                "max_order_size": "100.0",
            },
        ]
    }
    # Mock the response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = (
        mock_data  # Note: Actual API returns top level list/dict?
    )
    # Based on user doc: "Response: Trading pair configuraties" (likely list or dict with key)
    # Adjusting to likely structure or list directly if that's what user implied.
    # For now assuming list or wrapped list. The adapter logic will handle "isinstance(list)" check.

    mock_adapter.client.request.return_value = mock_response

    # Call method (not yet implemented)
    instruments = await mock_adapter.get_instruments()

    assert len(instruments) > 0
    assert "BTC-EUR" in [i["symbol"] for i in instruments]
    # Check method/path
    mock_adapter.client.request.assert_called_with(
        "GET", "/api/1.0/configuration/pairs", headers=ANY, content=None
    )


@pytest.mark.asyncio
async def test_get_ticker_success(mock_adapter):
    """Happy Path: Successfully fetch ticker"""
    mock_data = [
        {"symbol": "BTC-EUR", "last_price": 50000.0, "bid": 49990.0, "ask": 50010.0}
    ]

    # Allow adapter to handle list response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = mock_data
    mock_adapter.client.request.return_value = mock_response

    ticker = await mock_adapter.get_ticker("BTC-EUR")

    assert ticker["last"] == 50000.0
    # The adapter currently proxies /trades but now should use /tickers for better data
    # or efficiently filter from list.


@pytest.mark.asyncio
async def test_get_candles_success(mock_adapter):
    """Happy Path: Successfully fetch candles"""
    # [timestamp, open, high, low, close, volume] ? or dicts?
    # User doc says: OHLCV candlestick data
    # Assuming standard list of lists or list of dicts.
    mock_data = {
        "data": [{"t": 1600000000, "o": 100, "h": 110, "l": 90, "c": 105, "v": 1000}]
    }

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = mock_data
    mock_adapter.client.request.return_value = mock_response

    candles = await mock_adapter.get_candles("BTC-EUR", "1h")

    assert len(candles) == 1
    assert candles[0]["c"] == 105


@pytest.mark.asyncio
async def test_api_unauthorized(mock_adapter):
    """Unhappy Path: 401 Unauthorized"""
    mock_response = MagicMock()
    mock_response.status_code = 401
    mock_response.text = "Unauthorized"
    mock_adapter.client.request.return_value = mock_response

    with pytest.raises(Exception, match="Exchange API Error"):
        await mock_adapter.get_instruments()


@pytest.mark.asyncio
async def test_api_rate_limited(mock_adapter):
    """Unhappy Path: 429 Rate Limit"""
    mock_response = MagicMock()
    mock_response.status_code = 429
    mock_adapter.client.request.return_value = mock_response

    with pytest.raises(Exception, match="Rate Limited"):
        await mock_adapter.get_instruments()
