import time
import json
import base64
import httpx
import logging
from typing import Dict, Any, Optional, List, AsyncGenerator
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

logger = logging.getLogger(__name__)

from backend.execution.broker_interface import ExecutionInterface, OrderResult
from backend.schemas.orders import OrderRequest, OrderSide, OrderType, OrderStatus
from backend.schemas.market_data import TickerUpdate, OrderBook, OrderUpdate


class RateLimitError(Exception):
    pass


class ExchangeAdapter(ExecutionInterface):
    """
    Generic Adapter for Crypto Exchanges using REST API and Ed25519 Signing.
    Designed to work with Revolut X but extensible for others.
    """

    def __init__(
        self,
        api_key: str,
        private_key_pem: str,
        base_url: str = "https://revx.revolut.com",
    ):
        self.api_key = api_key
        self.base_url = base_url
        self.private_key = self._load_private_key(private_key_pem)
        self.client = httpx.AsyncClient(base_url=self.base_url, timeout=10.0)

    def _load_private_key(self, pem_content: str):
        if isinstance(pem_content, str):
            pem_bytes = pem_content.encode("utf-8")
        else:
            pem_bytes = pem_content

        return serialization.load_pem_private_key(pem_bytes, password=None)

    def _generate_signature(
        self, timestamp: str, method: str, path: str, query: str, body: str = ""
    ) -> str:
        # Standardize signing string: timestamp + method + path + query + body
        # Doc: "When concatenating, do not add any separators (spaces, newlines, or commas) between the fields."
        # Query String: "Do not include the ?."

        signing_string = f"{timestamp}{method.upper()}{path}{query}{body}"
        signature_bytes = self.private_key.sign(signing_string.encode("utf-8"))
        return base64.b64encode(signature_bytes).decode("utf-8")

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type(
            (httpx.NetworkError, httpx.TimeoutException, RateLimitError)
        ),
        reraise=True,
    )
    async def _request(
        self,
        method: str,
        path: str,
        params: Optional[Dict] = None,
        data: Optional[Dict] = None,
    ) -> Any:
        timestamp = str(int(time.time() * 1000))

        # Compact JSON for signing
        body_str = json.dumps(data, separators=(",", ":")) if data else ""

        query_str = ""
        full_path = path
        if params:
            query_str = "&".join([f"{k}={v}" for k, v in sorted(params.items())])
            full_path = f"{path}?{query_str}"

        signature = self._generate_signature(
            timestamp, method, path, query_str, body_str
        )

        # Generic Headers (Might need adjustment for other exchanges via subclassing)
        headers = {
            "Content-Type": "application/json",
            "X-Revx-Api-Key": self.api_key,
            "X-Revx-Timestamp": timestamp,
            "X-Revx-Signature": signature,
        }

        try:
            response = await self.client.request(
                method, full_path, headers=headers, content=body_str if data else None
            )

            if response.status_code >= 500:
                raise Exception(f"Server Error {response.status_code}")

            if response.status_code >= 400:
                if response.status_code == 429:
                    raise RateLimitError("Rate Limited")
                raise Exception(
                    f"Exchange API Error ({response.status_code}): {response.text}"
                )

            return response.json()
        except json.JSONDecodeError:
            raise Exception(f"Invalid JSON Response from {self.base_url}{full_path}")

    async def submit_order(self, order: OrderRequest) -> OrderResult:
        # Standardized payload mapping
        data = {
            "client_order_id": str(order.client_order_id),
            "symbol": order.symbol,
            "side": order.side.value.lower(),
            "type": order.order_type.value.lower(),
        }

        if order.qty:
            data["quantity"] = str(order.qty)
        if order.limit_price:
            data["price"] = str(order.limit_price)

        response = await self._request("POST", "/api/1.0/orders", data=data)

        return OrderResult(
            order_id=response.get("order_id"),
            client_order_id=str(order.client_order_id),
            status=OrderStatus.PENDING,
            raw_response=response,
        )

    async def get_balance(self) -> Dict[str, float]:
        # Fallback strategy for balance endpoints
        # /api/1.0/balances is the confirmed working endpoint for Revolut X
        endpoints = ["/api/1.0/balances", "/api/1.0/wallets", "/api/1.0/accounts"]

        last_error = None
        for endpoint in endpoints:
            try:
                response = await self._request("GET", endpoint)
                balances = {}
                if isinstance(response, list):
                    for item in response:
                        currency = item.get(
                            "currency", item.get("asset", item.get("code"))
                        )
                        balance = item.get(
                            "balance",
                            item.get("available_balance", item.get("amount", 0)),
                        )
                        if currency:
                            balances[currency] = float(balance)
                    return balances
                elif isinstance(response, dict) and "balances" in response:
                    for k, v in response["balances"].items():
                        balances[k] = float(v)
                    return balances
            except Exception as e:
                last_error = e
                continue

        raise Exception(
            f"Could not find balance endpoint. Last error: {str(last_error)}"
        )

    async def get_order_status(self, order_id: str) -> OrderResult:
        response = await self._request("GET", f"/api/1.0/orders/{order_id}")

        status_map = {
            "filled": OrderStatus.FILLED,
            "rejected": OrderStatus.REJECTED,
            "cancelled": OrderStatus.CANCELLED,
            "open": OrderStatus.PENDING,
        }

        return OrderResult(
            order_id=order_id,
            client_order_id=response.get("client_order_id", ""),
            status=status_map.get(response.get("status"), OrderStatus.PENDING),
            filled_qty=float(response.get("filled_quantity", 0)),
            avg_price=(
                float(response.get("avg_price", 0))
                if response.get("avg_price")
                else None
            ),
            raw_response=response,
        )

    async def get_instruments(self) -> List[Dict[str, Any]]:
        """Get all tradable pairs from Revolut."""
        data = await self._request("GET", "/api/1.0/configuration/pairs")
        if isinstance(data, dict) and "pairs" in data:
            return data["pairs"]
        if isinstance(data, dict) and "data" in data:
            return data["data"]
        return data

    async def get_ticker(self, symbol: str) -> Dict[str, Any]:
        """Get ticker data for a specific symbol."""
        tickers = await self.get_tickers([symbol])
        return tickers.get(symbol, {"symbol": symbol, "last": 0.0})

    async def get_tickers(self, symbols: List[str]) -> Dict[str, Dict[str, Any]]:
        """Get ticker data for multiple symbols in bulk with chunking."""
        if not symbols:
            return {}

        results = {}
        # Revolut might limit the number of symbols or URL length. Let's chunk by 20.
        chunk_size = 20
        for i in range(0, len(symbols), chunk_size):
            chunk = symbols[i : i + chunk_size]

            # Format symbols for API (Revolut expects BTC-EUR, not BTC/EUR)
            formatted_chunk = [s.replace("/", "-") for s in chunk]
            symbols_str = ",".join(formatted_chunk)

            try:
                response = await self._request(
                    "GET", "/api/1.0/tickers", params={"symbols": symbols_str}
                )

                # Normalize response to list (handle {data: [...]})
                items = []
                if (
                    isinstance(response, dict)
                    and "data" in response
                    and isinstance(response["data"], list)
                ):
                    items = response["data"]
                elif isinstance(response, list):
                    items = response
                elif isinstance(response, dict):
                    items = [response]

                for item in items:
                    sym = item.get("symbol")
                    if sym:
                        # Normalize symbol for matching (e.g. BTCEUR -> BTC/EUR)
                        norm_sym = sym
                        if "/" not in sym and "-" not in sym:
                            if sym.endswith("EUR") and len(sym) > 3:
                                norm_sym = f"{sym[:-3]}/EUR"
                            elif sym.endswith("USD") and len(sym) > 3:
                                norm_sym = f"{sym[:-3]}/USD"
                        elif "-" in sym:
                            norm_sym = sym.replace("-", "/")

                        results[norm_sym] = {
                            "symbol": norm_sym,
                            "last": float(item.get("last_price", 0)),
                            "bid": float(item.get("bid", 0)),
                            "ask": float(item.get("ask", 0)),
                            "volume_24h": (
                                float(item.get("volume_24h", 0))
                                if item.get("volume_24h")
                                else 0.0
                            ),
                            "change_24h": (
                                float(item.get("price_change_24h", 0))
                                if item.get("price_change_24h")
                                else 0.0
                            ),
                        }
            except Exception as e:
                # ... (Failure logging) ...
                with open("debug_adapter.txt", "a") as f:
                    f.write(f"Bulk chunk failed: {e}\n")
                logger.warning(
                    f"Bulk tickers chunk failed, falling back to individual: {e}"
                )
                # Fallback to individual fetches for this chunk
                for sym in chunk:
                    try:
                        formatted_sym = sym.replace("/", "-")
                        resp = await self._request(
                            "GET", "/api/1.0/tickers", params={"symbols": formatted_sym}
                        )

                        # Handle dict or list response (unwrap data)
                        target_item = None

                        if (
                            isinstance(resp, dict)
                            and "data" in resp
                            and isinstance(resp["data"], list)
                            and len(resp["data"]) > 0
                        ):
                            target_item = resp["data"][0]
                        elif isinstance(resp, list) and len(resp) > 0:
                            target_item = resp[0]
                        elif (
                            isinstance(resp, dict) and "data" not in resp
                        ):  # plain dict
                            target_item = resp

                        if target_item:
                            results[sym] = {
                                "symbol": sym,
                                "last": float(target_item.get("last_price", 0)),
                                "bid": float(target_item.get("bid", 0)),
                                "ask": float(target_item.get("ask", 0)),
                                "volume_24h": (
                                    float(target_item.get("volume_24h", 0))
                                    if target_item.get("volume_24h")
                                    else 0.0
                                ),
                                "change_24h": (
                                    float(target_item.get("price_change_24h", 0))
                                    if target_item.get("price_change_24h")
                                    else 0.0
                                ),
                            }
                    except Exception as ex:
                        with open("debug_adapter.txt", "a") as f:
                            f.write(f"Fallback exception for {sym}: {ex}\n")
                        continue

        with open("debug_adapter.txt", "a") as f:
            f.write(f"GetTickers returning {len(results)} results\n")
        return results

    async def get_candles(
        self, symbol: str, timeframe: str = "1h", limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get OHLCV candles."""
        params = {"interval": timeframe, "limit": limit}
        data = await self._request("GET", f"/api/1.0/candles/{symbol}", params=params)
        if isinstance(data, dict) and "data" in data:
            return data["data"]
        return data

    async def cancel_all_orders(self):
        await self._request("DELETE", "/api/1.0/orders")

    async def subscribe_ticker(self, symbol: str) -> AsyncGenerator[TickerUpdate, None]:
        from datetime import datetime
        import asyncio

        while True:
            try:
                ticker = await self.get_ticker(symbol)
                yield TickerUpdate(
                    symbol=symbol,
                    bid=float(ticker.get("bid", 0)),
                    ask=float(ticker.get("ask", 0)),
                    last=float(ticker.get("last", 0)),
                    volume_24h=0.0,
                    timestamp=datetime.utcnow(),
                    source="revolut_rest_poll",
                )
                await asyncio.sleep(2.0)
            except Exception:
                await asyncio.sleep(5.0)

    async def subscribe_orderbook(
        self, symbol: str, depth: int = 10
    ) -> AsyncGenerator[OrderBook, None]:
        from datetime import datetime
        import asyncio

        while True:
            yield OrderBook(
                symbol=symbol, bids=[], asks=[], timestamp=datetime.utcnow()
            )
            await asyncio.sleep(5.0)

    async def subscribe_orders(self) -> AsyncGenerator[OrderUpdate, None]:
        from datetime import datetime
        import asyncio

        while True:
            await asyncio.sleep(10.0)
            yield OrderUpdate(
                order_id="keepalive",
                status=OrderStatus.PENDING,
                filled_qty=0,
                avg_price=0,
                timestamp=datetime.utcnow(),
            )
