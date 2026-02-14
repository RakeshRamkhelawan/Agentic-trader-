"""
Revolut X Crypto Exchange REST API Client
Official implementation based on https://developer.revolut.com/docs/x-api/revolut-x-crypto-exchange-rest-api
"""

import asyncio
import base64
import json
import logging
import os
import time
import uuid
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class OrderSide(Enum):
    """Order side"""

    BUY = "buy"
    SELL = "sell"


class OrderType(Enum):
    """Order type"""

    MARKET = "market"
    LIMIT = "limit"


@dataclass
class Order:
    """Revolut X Order"""

    id: str
    client_order_id: str
    symbol: str
    side: str
    type: str
    quantity: str
    filled_quantity: str
    leaves_quantity: str
    price: Optional[str]
    status: str
    time_in_force: str
    execution_instructions: List[str]
    created_date: int
    updated_date: int


class RevolutXClient:
    """
    Revolut X Crypto Exchange REST API Client

    Official implementation with Ed25519 signature authentication
    Docs: https://developer.revolut.com/docs/x-api/revolut-x-crypto-exchange-rest-api
    """

    BASE_URL = "https://revx.revolut.com/api/1.0"
    TIMESTAMP_OFFSET_MS = (
        5000  # Subtract 5 seconds to prevent "future timestamp" errors
    )

    def __init__(
        self,
        api_key: Optional[str] = None,
        private_key_path: Optional[str] = None,
        timeout: float = 30.0,
    ):
        """
        Initialize Revolut X client

        Args:
            api_key: 64-character alphanumeric API key from Revolut X
            private_key_path: Path to Ed25519 private key PEM file
            timeout: Request timeout in seconds
        """
        self.api_key = api_key or os.getenv("REVOLUT_API_KEY")
        self.private_key_path = private_key_path or os.getenv(
            "REVOLUT_PRIVATE_KEY_PATH"
        )
        self.timeout = timeout

        self._session: Optional[httpx.AsyncClient] = None
        self._private_key: Optional[Ed25519PrivateKey] = None
        self._authenticated = False

        logger.info("✅ RevolutXClient initialized")
        logger.info(f"   Base URL: {self.BASE_URL}")

    def _load_private_key(self) -> Ed25519PrivateKey:
        """Load Ed25519 private key from PEM file"""
        if not self.private_key_path:
            raise ValueError("REVOLUT_PRIVATE_KEY_PATH not configured")

        private_key_file = Path(self.private_key_path)
        if not private_key_file.exists():
            raise FileNotFoundError(
                f"Private key file not found: {self.private_key_path}"
            )

        with open(private_key_file, "rb") as f:
            private_key_data = f.read()

        private_key = serialization.load_pem_private_key(
            private_key_data, password=None
        )

        if not isinstance(private_key, Ed25519PrivateKey):
            raise ValueError("Private key is not an Ed25519 key")

        logger.info("✅ Ed25519 private key loaded")
        return private_key

    def _sign_request(
        self,
        timestamp: int,
        method: str,
        path: str,
        query_string: str = "",
        body: str = "",
    ) -> str:
        """
        Sign a request using Ed25519 private key

        Message format: timestamp + method + path + query + body

        Args:
            timestamp: Unix timestamp in milliseconds
            method: HTTP method (GET, POST, etc.) in UPPERCASE
            path: Request path starting with /api
            query_string: URL query string (without ?)
            body: Minified JSON body string

        Returns:
            Base64-encoded signature
        """
        if not self._private_key:
            self._private_key = self._load_private_key()

        # Construct message to sign (no separators!)
        message = f"{timestamp}{method}{path}{query_string}{body}"

        logger.debug(f"Signing message: {message[:100]}...")

        # Sign with Ed25519 private key
        signature = self._private_key.sign(message.encode("utf-8"))

        # Base64 encode
        signature_b64 = base64.b64encode(signature).decode("utf-8")

        return signature_b64

    async def connect(self) -> bool:
        """
        Initialize connection and validate credentials

        Returns:
            True if connection successful
        """
        try:
            if not self.api_key:
                logger.error("❌ REVOLUT_API_KEY not configured")
                return False

            # Load private key
            try:
                self._private_key = self._load_private_key()
            except Exception as e:
                logger.error(f"❌ Failed to load private key: {str(e)}")
                return False

            # Create HTTP session
            self._session = httpx.AsyncClient(
                base_url=self.BASE_URL,
                timeout=self.timeout,
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                },
            )

            logger.info("🔍 Testing connection to Revolut X...")

            # Test with GET /orders/active (requires authentication)
            # Use current UTC time in milliseconds with offset
            timestamp = int(time.time() * 1000) - self.TIMESTAMP_OFFSET_MS

            logger.info(
                f"   Client timestamp: {timestamp} ({datetime.fromtimestamp(timestamp/1000)})"
            )

            path = "/api/1.0/orders/active"
            method = "GET"

            signature = self._sign_request(timestamp, method, path)

            headers = {
                "X-Revx-API-Key": self.api_key,
                "X-Revx-Timestamp": str(timestamp),
                "X-Revx-Signature": signature,
            }

            response = await self._session.get("/orders/active", headers=headers)

            logger.info(f"   Response: {response.status_code}")

            if response.status_code == 200:
                self._authenticated = True
                data = response.json()
                logger.info(f"✅ Connected to Revolut X!")
                logger.info(f"   Active orders: {len(data.get('data', []))}")
                return True
            elif response.status_code == 401:
                logger.error(f"❌ Authentication failed (401)")
                try:
                    error_data = response.json()
                    logger.error(f"   Error: {error_data}")
                except:
                    logger.error(f"   Response: {response.text[:200]}")
                return False
            elif response.status_code == 409:
                logger.warning(f"⚠️ Conflict (409) - API key may not be activated")
                try:
                    error_data = response.json()
                    logger.warning(f"   Error details: {error_data}")
                except:
                    logger.warning(f"   Response: {response.text}")
                return False
            else:
                logger.warning(f"⚠️ Unexpected response: {response.status_code}")
                try:
                    logger.warning(f"   Response: {response.json()}")
                except:
                    logger.warning(f"   Response: {response.text[:200]}")
                return False

        except Exception as e:
            logger.error(f"❌ Connection failed: {str(e)}")
            import traceback

            logger.debug(traceback.format_exc())
            return False

    async def disconnect(self) -> None:
        """Close connection"""
        if self._session:
            await self._session.aclose()
            logger.info("Connection closed")

    async def get_active_orders(
        self, symbols: Optional[List[str]] = None, limit: int = 100
    ) -> List[Order]:
        """
        Get active orders

        Args:
            symbols: Filter by symbols (e.g., ["BTC-USD"])
            limit: Max results (default 100)

        Returns:
            List of active orders
        """
        if not self._session or not self._authenticated:
            raise RuntimeError("Client not connected. Call connect() first.")

        # Build query string
        params = {"limit": limit}
        if symbols:
            params["symbols"] = ",".join(symbols)

        query_string = "&".join(f"{k}={v}" for k, v in params.items())

        # Sign request
        timestamp = int(time.time() * 1000) - self.TIMESTAMP_OFFSET_MS
        path = "/api/1.0/orders/active"
        method = "GET"

        signature = self._sign_request(timestamp, method, path, query_string)

        headers = {
            "X-Revx-API-Key": self.api_key,
            "X-Revx-Timestamp": str(timestamp),
            "X-Revx-Signature": signature,
        }

        response = await self._session.get(
            f"/orders/active?{query_string}", headers=headers
        )

        if response.status_code == 200:
            data = response.json()
            orders = [Order(**order_data) for order_data in data.get("data", [])]
            logger.info(f"✅ Retrieved {len(orders)} active orders")
            return orders
        else:
            logger.error(f"❌ Failed to get orders: {response.status_code}")
            logger.error(f"   Response: {response.text[:200]}")
            return []

    async def place_order(
        self,
        symbol: str,
        side: OrderSide,
        quantity: str,
        price: Optional[str] = None,
        client_order_id: Optional[str] = None,
        order_type: OrderType = OrderType.LIMIT,
        time_in_force: str = "gtc",
        execution_instructions: Optional[List[str]] = None,
    ) -> Optional[Order]:
        """
        Place a new order

        Args:
            symbol: Trading pair (e.g., "BTC-USD")
            side: BUY or SELL
            quantity: Order quantity in base currency
            price: Limit price (required for limit orders)
            client_order_id: Optional client order ID
            order_type: MARKET or LIMIT
            time_in_force: "gtc", "ioc", "fok"
            execution_instructions: ["post_only"] or ["allow_taker"]

        Returns:
            Placed order or None if failed
        """
        if not self._session or not self._authenticated:
            raise RuntimeError("Client not connected. Call connect() first.")

        if not client_order_id:
            client_order_id = str(uuid.uuid4())

        # Build request body
        order_config = {}
        if order_type == OrderType.LIMIT:
            if not price:
                raise ValueError("Price required for limit orders")
            order_config["limit"] = {"base_size": quantity, "price": price}
            if execution_instructions:
                order_config["limit"]["execution_instructions"] = execution_instructions
        else:
            order_config["market"] = {"base_size": quantity}

        body = {
            "client_order_id": client_order_id,
            "symbol": symbol,
            "side": side.value,
            "order_configuration": order_config,
        }

        # Minify JSON for signing
        body_str = json.dumps(body, separators=(",", ":"))

        # Sign request
        timestamp = int(time.time() * 1000) - self.TIMESTAMP_OFFSET_MS
        path = "/api/1.0/orders"
        method = "POST"

        signature = self._sign_request(timestamp, method, path, "", body_str)

        headers = {
            "X-Revx-API-Key": self.api_key,
            "X-Revx-Timestamp": str(timestamp),
            "X-Revx-Signature": signature,
        }

        response = await self._session.post("/orders", headers=headers, json=body)

        if response.status_code == 200:
            data = response.json()
            if data.get("data"):
                order_data = data["data"][0]
                logger.info(f"✅ Order placed: {order_data.get('venue_order_id')}")
                # Return basic order info (full details need separate GET)
                return Order(
                    id=order_data.get("venue_order_id"),
                    client_order_id=order_data.get("client_order_id"),
                    symbol=symbol,
                    side=side.value,
                    type=order_type.value,
                    quantity=quantity,
                    filled_quantity="0",
                    leaves_quantity=quantity,
                    price=price,
                    status=order_data.get("state", "new"),
                    time_in_force=time_in_force,
                    execution_instructions=execution_instructions or [],
                    created_date=timestamp,
                    updated_date=timestamp,
                )
        else:
            logger.error(f"❌ Failed to place order: {response.status_code}")
            logger.error(f"   Response: {response.text}")

        return None

    async def cancel_order(self, order_id: str) -> bool:
        """
        Cancel an active order

        Args:
            order_id: Venue order ID

        Returns:
            True if cancelled successfully
        """
        if not self._session or not self._authenticated:
            raise RuntimeError("Client not connected. Call connect() first.")

        # Sign request
        timestamp = int(time.time() * 1000) - self.TIMESTAMP_OFFSET_MS
        path = f"/api/1.0/orders/{order_id}"
        method = "DELETE"

        signature = self._sign_request(timestamp, method, path)

        headers = {
            "X-Revx-API-Key": self.api_key,
            "X-Revx-Timestamp": str(timestamp),
            "X-Revx-Signature": signature,
        }

        response = await self._session.delete(f"/orders/{order_id}", headers=headers)

        if response.status_code == 200:
            logger.info(f"[SUCCESS] Order cancelled: {order_id}")
            return True
        else:
            logger.error(f"[ERROR] Failed to cancel order: {response.status_code}")
            logger.error(f"   Response: {response.text[:200]}")
            return False

    # ========================================================================
    # MARKET DATA METHODS (Public - No Authentication Required)
    # ========================================================================

    async def get_ticker(self, symbol: str) -> Dict[str, Any]:
        """
        Get ticker data for a symbol (requires authentication)

        Args:
            symbol: Trading pair (e.g., 'BTC-USD')

        Returns:
            Dict with: last, volume, bid, ask, timestamp, high_24h, low_24h
        """
        if not self._session or not self._authenticated:
            raise RuntimeError("Client not connected. Call connect() first.")

        try:
            # Sign request (authenticated endpoint)
            timestamp = int(time.time() * 1000) - self.TIMESTAMP_OFFSET_MS
            path = f"/api/1.0/ticker/{symbol}"
            method = "GET"

            signature = self._sign_request(timestamp, method, path)

            headers = {
                "X-Revx-API-Key": self.api_key,
                "X-Revx-Timestamp": str(timestamp),
                "X-Revx-Signature": signature,
            }

            response = await self._session.get(f"/ticker/{symbol}", headers=headers)

            if response.status_code == 200:
                data = response.json()
                logger.debug(f"Ticker data for {symbol}: {data}")

                # Parse Revolut X ticker response
                return {
                    "last": float(data.get("last_price", 0)),
                    "volume": float(data.get("volume_24h", 0)),
                    "bid": float(data.get("best_bid", 0)),
                    "ask": float(data.get("best_ask", 0)),
                    "high_24h": float(data.get("high_24h", 0)),
                    "low_24h": float(data.get("low_24h", 0)),
                    "timestamp": data.get("timestamp", int(time.time() * 1000)),
                }
            else:
                logger.error(f"[ERROR] Failed to get ticker: {response.status_code}")
                logger.error(f"   Response: {response.text[:200]}")
                raise ValueError(f"Ticker request failed: {response.status_code}")

        except Exception as e:
            logger.error(f"[ERROR] Ticker fetch failed for {symbol}: {e}")
            raise

    async def get_orderbook(self, symbol: str, depth: int = 10) -> Dict[str, Any]:
        """
        Get orderbook snapshot (requires authentication)

        Args:
            symbol: Trading pair (e.g., 'BTC-USD')
            depth: Number of levels per side (default 10)

        Returns:
            Dict with: bids [[price, size], ...], asks [[price, size], ...]
        """
        if not self._session or not self._authenticated:
            raise RuntimeError("Client not connected. Call connect() first.")

        try:
            # Build query string
            query_string = f"depth={depth}"

            # Sign request (authenticated endpoint)
            timestamp = int(time.time() * 1000) - self.TIMESTAMP_OFFSET_MS
            path = f"/api/1.0/orderbook/{symbol}"
            method = "GET"

            signature = self._sign_request(timestamp, method, path, query_string)

            headers = {
                "X-Revx-API-Key": self.api_key,
                "X-Revx-Timestamp": str(timestamp),
                "X-Revx-Signature": signature,
            }

            response = await self._session.get(
                f"/orderbook/{symbol}", params={"depth": depth}, headers=headers
            )

            if response.status_code == 200:
                data = response.json()

                # Parse orderbook
                return {
                    "bids": [
                        [float(b["price"]), float(b["quantity"])]
                        for b in data.get("bids", [])
                    ],
                    "asks": [
                        [float(a["price"]), float(a["quantity"])]
                        for a in data.get("asks", [])
                    ],
                    "timestamp": data.get("timestamp", int(time.time() * 1000)),
                }
            else:
                logger.error(f"[ERROR] Failed to get orderbook: {response.status_code}")
                raise ValueError(f"Orderbook request failed: {response.status_code}")

        except Exception as e:
            logger.error(f"[ERROR] Orderbook fetch failed for {symbol}: {e}")
            raise

    async def get_symbols(self) -> List[str]:
        """
        Get list of available trading symbols (PUBLIC endpoint)

        Returns:
            List of symbol strings (e.g., ['BTC-USD', 'ETH-USD'])
        """
        if not self._session:
            raise RuntimeError("Client not connected. Call connect() first.")

        try:
            response = await self._session.get("/symbols")

            if response.status_code == 200:
                data = response.json()
                symbols = [s["symbol"] for s in data.get("data", [])]
                logger.info(f"[SUCCESS] Found {len(symbols)} trading symbols")
                return symbols
            else:
                logger.error(f"[ERROR] Failed to get symbols: {response.status_code}")
                return []

        except Exception as e:
            logger.error(f"[ERROR] Symbols fetch failed: {e}")
            return []


async def test_revolut_x_connection():
    """Test Revolut X API connection"""
    print("=" * 70)
    print("🔗 REVOLUT X API CONNECTION TEST")
    print("=" * 70)

    client = RevolutXClient()

    print("\n1️⃣ Connecting to Revolut X...")
    connected = await client.connect()

    if not connected:
        print("❌ Connection failed. Check your API key and private key.")
        print("\n📋 Setup instructions:")
        print("1. Generate Ed25519 key pair: python scripts/setup_revolut_keys.py")
        print("2. Add public key to Revolut X: https://exchange.revolut.com/ → Profile")
        print("3. Copy API key to .env file (REVOLUT_API_KEY)")
        return

    print("\n2️⃣ Getting active orders...")
    orders = await client.get_active_orders()
    print(f"   Found {len(orders)} active orders")

    if orders:
        for order in orders[:3]:
            print(f"   - {order.symbol} {order.side} {order.quantity} @ {order.price}")

    print("\n3️⃣ Test order placement (simulated - not executed)")
    print("   To place real orders, uncomment the code below")
    # Uncomment to test real order placement:
    # order = await client.place_order(
    #     symbol="BTC-USD",
    #     side=OrderSide.BUY,
    #     quantity="0.0001",
    #     price="50000",
    #     execution_instructions=["post_only"]
    # )
    # if order:
    #     print(f"   Order placed: {order.id}")

    await client.disconnect()

    print("\n" + "=" * 70)
    print("✅ REVOLUT X API TEST COMPLETED")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(test_revolut_x_connection())
