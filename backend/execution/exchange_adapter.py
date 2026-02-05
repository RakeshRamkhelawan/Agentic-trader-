import time
import json
import base64
import httpx
from typing import Dict, Any, Optional, List
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from backend.execution.broker_interface import ExecutionInterface, OrderResult
from backend.schemas.orders import OrderRequest, OrderSide, OrderType, OrderStatus

class ExchangeAdapter(ExecutionInterface):
    """
    Generic Adapter for Crypto Exchanges using REST API and Ed25519 Signing.
    Designed to work with Revolut X but extensible for others.
    """
    
    def __init__(self, api_key: str, private_key_path: str, base_url: str = "https://revx.revolut.com"):
        self.api_key = api_key
        self.base_url = base_url
        self.private_key = self._load_private_key(private_key_path)
        self.client = httpx.AsyncClient(base_url=self.base_url, timeout=10.0)

    def _load_private_key(self, path: str):
        with open(path, "rb") as key_file:
            return serialization.load_pem_private_key(
                key_file.read(),
                password=None
            )

    def _generate_signature(self, timestamp: str, method: str, path: str, body: str = "") -> str:
        # Standardize signing string: timestamp + method + path + body
        # This is common for modern exchanges (Revolut, DYDX, etc.)
        signing_string = f"{timestamp}{method.upper()}{path}{body}"
        signature_bytes = self.private_key.sign(signing_string.encode('utf-8'))
        return base64.b64encode(signature_bytes).decode('utf-8')

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((httpx.NetworkError, httpx.TimeoutException, Exception))
    )
    async def _request(self, method: str, path: str, params: Optional[Dict] = None, data: Optional[Dict] = None) -> Any:
        timestamp = str(int(time.time() * 1000))
        
        # Compact JSON for signing
        body_str = json.dumps(data, separators=(',', ':')) if data else ""
        
        full_path = path
        if params:
            query_str = "&".join([f"{k}={v}" for k, v in sorted(params.items())])
            full_path = f"{path}?{query_str}"

        signature = self._generate_signature(timestamp, method, full_path, body_str)

        # Generic Headers (Might need adjustment for other exchanges via subclassing)
        headers = {
            "Content-Type": "application/json",
            "X-Revx-Api-Key": self.api_key,
            "X-Revx-Timestamp": timestamp,
            "X-Revx-Signature": signature
        }

        try:
            response = await self.client.request(
                method, full_path, headers=headers, content=body_str if data else None
            )
            
            if response.status_code >= 500:
                 raise Exception(f"Server Error {response.status_code}")
                 
            if response.status_code >= 400:
                if response.status_code == 429:
                    raise Exception("Rate Limited")
                raise Exception(f"Exchange API Error ({response.status_code}): {response.text}")
                
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
            raw_response=response
        )

    async def get_balance(self) -> Dict[str, float]:
        # Fallback strategy for balance endpoints
        endpoints = ["/api/1.0/wallets", "/api/1.0/accounts", "/api/1.0/balances"]
        
        last_error = None
        for endpoint in endpoints:
            try:
                response = await self._request("GET", endpoint)
                balances = {}
                if isinstance(response, list):
                    for item in response:
                        currency = item.get('currency', item.get('asset', item.get('code')))
                        balance = item.get('balance', item.get('available_balance', item.get('amount', 0)))
                        if currency:
                            balances[currency] = float(balance)
                    return balances
                elif isinstance(response, dict) and 'balances' in response:
                    for k, v in response['balances'].items():
                        balances[k] = float(v)
                    return balances
            except Exception as e:
                last_error = e
                continue
        
        raise Exception(f"Could not find balance endpoint. Last error: {str(last_error)}")

    async def get_order_status(self, order_id: str) -> OrderResult:
        response = await self._request("GET", f"/api/1.0/orders/{order_id}")
        
        status_map = {
            "filled": OrderStatus.FILLED,
            "rejected": OrderStatus.REJECTED,
            "cancelled": OrderStatus.CANCELLED,
            "open": OrderStatus.PENDING
        }
        
        return OrderResult(
            order_id=order_id,
            client_order_id=response.get("client_order_id", ""),
            status=status_map.get(response.get("status"), OrderStatus.PENDING),
            filled_qty=float(response.get("filled_quantity", 0)),
            avg_price=float(response.get("avg_price", 0)) if response.get("avg_price") else None,
            raw_response=response
        )

    async def get_ticker(self, symbol: str) -> Dict[str, float]:
        response = await self._request("GET", f"/api/1.0/tickers/{symbol}")
        return {
            "best_bid": float(response.get("best_bid", 0)),
            "best_ask": float(response.get("best_ask", 0)),
            "last_price": float(response.get("last_price", 0))
        }

    async def cancel_all_orders(self):
        await self._request("DELETE", "/api/1.0/orders")
