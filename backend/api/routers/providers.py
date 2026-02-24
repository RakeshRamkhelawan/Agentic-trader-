"""
Providers Router — Exchange Provider Management.

Endpoints for managing connected exchange providers (API keys) per tenant.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.deps import get_current_tenant_id, get_db
from backend.schemas.user_settings import BrokerAPIKeyCreate, ExchangeType
from backend.services.user_settings_service import get_settings_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/providers", tags=["Providers"])

SUPPORTED_EXCHANGES: dict[str, dict] = {
    "revolut": {
        "name": "Revolut X",
        "type": "custom",
        "requires_private_key": True,
        "website": "https://revx.revolut.com",
    },
    "bitvavo": {
        "name": "Bitvavo",
        "type": "ccxt",
        "requires_private_key": False,
        "website": "https://bitvavo.com",
    },
    "kraken": {
        "name": "Kraken",
        "type": "ccxt",
        "requires_private_key": False,
        "website": "https://kraken.com",
    },
    "binance": {
        "name": "Binance",
        "type": "ccxt",
        "requires_private_key": False,
        "website": "https://binance.com",
    },
    "coinbase": {
        "name": "Coinbase",
        "type": "ccxt",
        "requires_private_key": False,
        "website": "https://coinbase.com",
    },
    "bybit": {
        "name": "Bybit",
        "type": "ccxt",
        "requires_private_key": False,
        "website": "https://bybit.com",
    },
}


class ConnectRequest(BaseModel):
    api_key: str = Field(min_length=10, description="Exchange API key")
    api_secret: str = Field(min_length=10, description="Exchange API secret")
    passphrase: str | None = Field(None, description="Optional passphrase (Coinbase)")


@router.get("/supported")
async def get_supported_exchanges():
    """Return all supported exchanges with metadata."""
    return SUPPORTED_EXCHANGES


@router.get("")
async def get_connected_providers(
    db: AsyncSession = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id),
):
    """Return all connected exchanges (masked API keys) for this tenant."""
    service = get_settings_service()
    keys = await service.get_api_keys(db, tenant_id)
    return [
        {
            "id": k.id,
            "exchange": k.exchange,
            "api_key_masked": k.api_key_masked,
            "created_at": k.created_at,
            "is_valid": k.is_valid,
            "name": SUPPORTED_EXCHANGES.get(str(k.exchange), {}).get("name", str(k.exchange)),
        }
        for k in keys
    ]


@router.post("/{exchange_id}/connect", status_code=201)
async def connect_provider(
    exchange_id: str,
    body: ConnectRequest,
    db: AsyncSession = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id),
):
    """Add API credentials for an exchange."""
    if exchange_id not in SUPPORTED_EXCHANGES:
        raise HTTPException(status_code=400, detail=f"Unsupported exchange: {exchange_id}")

    service = get_settings_service()
    try:
        exchange_enum = ExchangeType(exchange_id)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Unknown exchange type: {exchange_id}")

    create_req = BrokerAPIKeyCreate(
        exchange=exchange_enum,
        api_key=body.api_key,
        api_secret=body.api_secret,
        passphrase=body.passphrase,
    )
    result = await service.add_api_key(db, tenant_id, create_req)
    return {
        "id": result.id,
        "exchange": result.exchange,
        "api_key_masked": result.api_key_masked,
        "created_at": result.created_at,
        "is_valid": result.is_valid,
        "name": SUPPORTED_EXCHANGES[exchange_id]["name"],
    }


@router.delete("/{exchange_id}")
async def disconnect_provider(
    exchange_id: str,
    db: AsyncSession = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id),
):
    """Remove all API credentials for an exchange."""
    service = get_settings_service()
    keys = await service.get_api_keys(db, tenant_id)
    matching = [k for k in keys if str(k.exchange) == exchange_id]

    if not matching:
        raise HTTPException(status_code=404, detail=f"No credentials found for {exchange_id}")

    for key in matching:
        await service.delete_api_key(db, tenant_id, key.id)

    return {"deleted": exchange_id, "count": len(matching)}


@router.get("/{exchange_id}/status")
async def get_provider_status(
    exchange_id: str,
    db: AsyncSession = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id),
):
    """Test connectivity and return balances for an exchange."""
    if exchange_id not in SUPPORTED_EXCHANGES:
        raise HTTPException(status_code=400, detail=f"Unsupported exchange: {exchange_id}")

    service = get_settings_service()
    keys = await service.get_api_keys(db, tenant_id)
    matching = [k for k in keys if str(k.exchange) == exchange_id]

    if not matching:
        return {"connected": False, "exchange_id": exchange_id, "balances": {}}

    # Try to fetch balance to verify connectivity
    try:
        from backend.services.trading_service import get_trading_service

        trading = get_trading_service()
        adapter = await trading._get_exchange_adapter(db, tenant_id, exchange_id)
        if adapter:
            balances = await adapter.get_balance()
            return {"connected": True, "exchange_id": exchange_id, "balances": balances}
    except Exception as e:
        logger.warning(f"Connectivity check failed for {exchange_id}: {e}")

    return {"connected": False, "exchange_id": exchange_id, "balances": {}, "error": "Connection failed"}
