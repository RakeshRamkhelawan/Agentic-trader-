from unittest.mock import MagicMock, patch

import pytest
import respx
from httpx import Response

from backend.execution.broker_interface import (OrderRequest, OrderSide,
                                                OrderType)
from backend.execution.exchange_adapter import ExchangeAdapter


@pytest.fixture
def mock_keys(tmp_path):
    """Maak dummy key files aan."""
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import ed25519
    
    priv = ed25519.Ed25519PrivateKey.generate()
    pem = priv.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )
    key_path = tmp_path / "private.pem"
    key_path.write_bytes(pem)
    return str(key_path)

@pytest.mark.asyncio
async def test_retry_on_server_error(mock_keys):
    """
    Unhappy Path -> Happy Path:
    API geeft eerst 503 (Unavailable), dan 500 (Server Error), en dan 200 (OK).
    """
    adapter = ExchangeAdapter(api_key="test_key", private_key_path=mock_keys)
    
    with respx.mock(base_url="https://revx.revolut.com") as respx_mock:
        route = respx_mock.get("/api/1.0/wallets")
        route.side_effect = [
            Response(503, json={"error": "Service Unavailable"}),
            Response(500, json={"error": "Internal Error"}),
            Response(200, json=[{"asset": "BTC", "balance": "1.5"}])
        ]
        
        balances = await adapter.get_balance()
        assert balances["BTC"] == 1.5
        assert route.call_count == 3

@pytest.mark.asyncio
async def test_fail_after_max_retries(mock_keys):
    """
    Unhappy Path: API blijft falen. Adapter moet uiteindelijk opgeven.
    """
    adapter = ExchangeAdapter(api_key="test_key", private_key_path=mock_keys)
    
    with respx.mock(base_url="https://revx.revolut.com") as respx_mock:
        route = respx_mock.get("/api/1.0/wallets")
        route.return_value = Response(503, json={"error": "Down forever"})
        
        with pytest.raises(Exception):
            await adapter.get_balance()
            
        assert route.call_count >= 3