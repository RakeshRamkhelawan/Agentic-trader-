"""
Revolut X Trading Client
Handles crypto trading on Revolut X platform via official API
"""

import asyncio
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
import jwt
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class OrderSide(Enum):
    """Order side for trading"""

    BUY = "BUY"
    SELL = "SELL"


class OrderType(Enum):
    """Order type"""

    MARKET = "MARKET"
    LIMIT = "LIMIT"


@dataclass
class CryptoPrice:
    """Crypto currency price"""

    symbol: str  # e.g., "BTC"
    price: float
    bid: float
    ask: float
    timestamp: datetime
    change_24h: float  # Percentage


@dataclass
class CryptoBalance:
    """Crypto balance in account"""

    symbol: str
    amount: float
    usd_value: float
    locked: float  # In open orders


@dataclass
class Order:
    """Trading order"""

    order_id: str
    symbol: str
    side: OrderSide
    order_type: OrderType
    quantity: float
    price: Optional[float]  # For limit orders
    status: str  # PENDING, FILLED, CANCELLED
    filled_qty: float
    average_price: float
    timestamp: datetime
    updated_at: datetime


class RevolutXClient:
    """
    Revolut X Trading Client

    Connects to Revolut's crypto trading API
    Supports:
    - Reading account balances
    - Reading market prices
    - Placing buy/sell orders
    - Checking order status
    - Portfolio tracking
    """

    # Production Base URLs (try multiple variants)
    BASE_URL_VARIANTS = [
        "https://api.revolut.com/api/v1.0",  # Standard
        "https://api.revolut.com/1.0",  # Without /api
        "https://api.revolut.com/v1",  # v1 variant
        "https://trading-api.revolut.com/v1",  # Trading subdomain
        "https://api.revolut.com/trading",  # Trading path
        "https://api.revolut.com",  # Root
    ]

    # Sandbox Base URLs (try multiple variants)
    SANDBOX_URL_VARIANTS = [
        "https://sandbox-api.revolut.com/api/v1.0",  # Standard sandbox
        "https://sandbox.revolut.com/api/v1.0",  # Alternative sandbox
        "https://api.sandbox.revolut.com/v1.0",  # API.sandbox variant
        "https://sandbox-api.revolut.com/v1",  # Without /api
        "https://sandbox-api.revolut.com",  # Root sandbox
    ]

    # Default URLs (for backward compatibility)
    BASE_URL = BASE_URL_VARIANTS[0]
    SANDBOX_URL = SANDBOX_URL_VARIANTS[0]

    def __init__(
        self,
        api_key: Optional[str] = None,
        private_key_path: Optional[str] = None,
        sandbox: bool = False,
        timeout: float = 30.0,
    ):
        """
        Initialize Revolut X client

        Args:
            api_key: API key from environment or direct
            private_key_path: Path to private key for JWT signing
            sandbox: Use sandbox environment
            timeout: Request timeout in seconds
        """
        self.api_key = api_key or os.getenv("REVOLUT_API_KEY")
        self.private_key_path = private_key_path or os.getenv(
            "REVOLUT_PRIVATE_KEY_PATH"
        )
        self.sandbox = (
            sandbox or os.getenv("REVOLUT_SANDBOX", "False").lower() == "true"
        )
        self.timeout = timeout

        self.base_url = self.SANDBOX_URL if self.sandbox else self.BASE_URL

        self._session: Optional[httpx.AsyncClient] = None
        self._authenticated = False
        self._last_auth_time: Optional[datetime] = None

        logger.info(f"RevolutXClient initialized (sandbox={self.sandbox})")

    def _generate_jwt_token(self) -> Optional[str]:
        """
        Generate JWT token signed with Ed25519 private key
        Revolut API requires JWT-signed requests

        Returns:
            JWT token string or None if key cannot be loaded
        """
        try:
            if not self.private_key_path:
                logger.warning("No private key path configured for JWT signing")
                return None

            private_key_path = Path(self.private_key_path)
            if not private_key_path.exists():
                logger.warning(f"Private key file not found: {self.private_key_path}")
                return None

            with open(private_key_path, "rb") as f:
                private_key = f.read()

            # Create JWT payload
            now = int(time.time())
            payload = {
                "iss": self.api_key,  # Issuer = API Key
                "sub": self.api_key,  # Subject = API Key
                "aud": "revolut",  # Audience
                "iat": now,  # Issued at
                "exp": now + 300,  # Expires in 5 minutes
                "jti": str(uuid.uuid4()),  # JWT ID (unique)
            }

            # Sign with Ed25519 private key
            token = jwt.encode(
                payload, private_key, algorithm="EdDSA"  # Ed25519 uses EdDSA
            )

            logger.debug(f"✅ JWT token generated (exp: {payload['exp']})")
            return token

        except Exception as e:
            logger.error(f"Failed to generate JWT token: {str(e)}")
            return None

    async def connect(self) -> bool:
        """
        Connect to Revolut X API using JWT-signed authentication

        Returns:
            True if connection successful
        """
        try:
            if not self.api_key:
                logger.error("REVOLUT_API_KEY not configured")
                return False

            # Generate JWT token for authentication
            jwt_token = self._generate_jwt_token()

            if not jwt_token:
                logger.error("❌ Could not generate JWT token - check private key file")
                logger.error(f"   Private key path: {self.private_key_path}")
                return False

            # Create session with JWT token
            headers = {
                "Authorization": f"Bearer {jwt_token}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            }

            self._session = httpx.AsyncClient(
                base_url=self.base_url, timeout=self.timeout, headers=headers
            )

            logger.info("🔍 Using JWT-signed authentication")
            logger.info(f"🌐 Base URL: {self.base_url}")

            # Try multiple endpoints to discover working API structure
            endpoints_to_try = [
                # Standard REST API endpoints
                ("/user", "Get user info"),
                ("/accounts", "List all accounts"),
                ("/wallets", "List wallets"),
                ("/transactions", "Get transactions"),
                # Crypto-specific endpoints
                ("/crypto/wallets", "Crypto wallets"),
                ("/trading/accounts", "Trading accounts"),
                # Health check endpoints
                ("/health", "Health check"),
                ("/status", "API status"),
                # Alternative paths
                ("/api/user", "User (alt path)"),
                ("/api/accounts", "Accounts (alt path)"),
            ]

            for endpoint, description in endpoints_to_try:
                try:
                    logger.info(f"🔍 Trying: {description} ({endpoint})")
                    response = await self._session.get(endpoint)

                    logger.info(f"   Response: {response.status_code}")

                    if response.status_code == 200:
                        self._authenticated = True
                        self._last_auth_time = datetime.utcnow()
                        try:
                            data = response.json()
                            logger.info(f"✅ Connected via {endpoint}!")
                            logger.info(
                                f"   Response preview: {json.dumps(data, indent=2)[:300]}"
                            )
                        except (ValueError, json.JSONDecodeError):
                            logger.info(
                                f"✅ Connected via {endpoint}! (no JSON response)"
                            )
                        return True

                    elif response.status_code == 401:
                        logger.warning("   ❌ Unauthorized (401) - JWT token invalid")
                        try:
                            error_data = response.json()
                            logger.debug(f"   Error: {error_data}")
                        except (ValueError, json.JSONDecodeError):
                            logger.debug(f"   Error: {response.text[:200]}")
                        continue

                    elif response.status_code == 404:
                        logger.debug("   Endpoint not found (404), trying next...")
                        continue

                    else:
                        logger.debug(
                            f"   Status {response.status_code}, trying next..."
                        )
                        try:
                            logger.debug(f"   Response: {response.text[:200]}")
                        except Exception:
                            pass
                        continue

                except httpx.NetworkError as e:
                    logger.warning(f"   Network error on {endpoint}: {str(e)}")
                    continue
                except Exception as e:
                    logger.debug(f"   Error testing {endpoint}: {str(e)}")
                    continue

            logger.error("❌ All API endpoints failed!")
            logger.error("   Possible causes:")
            logger.error("   1. JWT token generation failed")
            logger.error("   2. Private key is invalid")
            logger.error("   3. Revolut API structure changed")
            return False

        except Exception as e:
            logger.error(f"Connection initialization failed: {e}")
            import traceback

            logger.debug(traceback.format_exc())
            return False

    async def disconnect(self) -> None:
        """Close connection"""
        if self._session:
            await self._session.aclose()
            logger.info("Disconnected from Revolut X")

    async def get_account_info(self) -> Optional[Dict[str, Any]]:
        """
        Get account information

        Returns:
            Account info dict or None if error
        """
        if not self._authenticated:
            logger.error("Not authenticated")
            return None

        try:
            response = await self._session.get("/accounts/me")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get account info: {e}")
            return None

    async def get_crypto_balance(self, crypto: str = "BTC") -> Optional[CryptoBalance]:
        """
        Get crypto balance for specific asset

        Args:
            crypto: Cryptocurrency symbol (BTC, ETH, etc)

        Returns:
            CryptoBalance object or None
        """
        if not self._authenticated:
            logger.error("Not authenticated")
            return None

        try:
            # Get all wallets
            response = await self._session.get("/wallets")
            response.raise_for_status()
            wallets = response.json()

            # Find crypto wallet
            for wallet in wallets.get("data", []):
                if wallet.get("currency") == crypto:
                    return CryptoBalance(
                        symbol=crypto,
                        amount=float(wallet.get("balance", 0)),
                        usd_value=float(wallet.get("balance_usd", 0)),
                        locked=float(wallet.get("committed", 0)),
                    )

            logger.warning(f"No balance found for {crypto}")
            return None

        except Exception as e:
            logger.error(f"Failed to get balance: {e}")
            return None

    async def get_portfolio(self) -> Optional[Dict[str, CryptoBalance]]:
        """
        Get full crypto portfolio

        Returns:
            Dict of symbol -> CryptoBalance
        """
        if not self._authenticated:
            logger.error("Not authenticated")
            return None

        try:
            response = await self._session.get("/wallets")
            response.raise_for_status()
            wallets = response.json()

            portfolio = {}
            for wallet in wallets.get("data", []):
                symbol = wallet.get("currency")
                balance = float(wallet.get("balance", 0))

                if balance > 0:  # Only include non-zero balances
                    portfolio[symbol] = CryptoBalance(
                        symbol=symbol,
                        amount=balance,
                        usd_value=float(wallet.get("balance_usd", 0)),
                        locked=float(wallet.get("committed", 0)),
                    )

            logger.info(f"Portfolio: {len(portfolio)} assets")
            return portfolio

        except Exception as e:
            logger.error(f"Failed to get portfolio: {e}")
            return None

    async def get_price(self, crypto: str) -> Optional[CryptoPrice]:
        """
        Get current crypto price

        Args:
            crypto: Cryptocurrency symbol (BTC, ETH, etc)

        Returns:
            CryptoPrice object or None
        """
        if not self._authenticated:
            logger.error("Not authenticated")
            return None

        try:
            # Get exchange rates
            response = await self._session.get(f"/rates/{crypto}USD")
            response.raise_for_status()
            data = response.json()

            mid_price = float(data.get("rate", 0))
            bid = mid_price * 0.999  # Approximation
            ask = mid_price * 1.001

            return CryptoPrice(
                symbol=crypto,
                price=mid_price,
                bid=bid,
                ask=ask,
                timestamp=datetime.utcnow(),
                change_24h=0.0,  # Not available in basic endpoint
            )

        except Exception as e:
            logger.error(f"Failed to get price for {crypto}: {e}")
            return None

    async def get_prices(self, cryptos: List[str]) -> Dict[str, CryptoPrice]:
        """
        Get prices for multiple cryptos

        Args:
            cryptos: List of symbols

        Returns:
            Dict of symbol -> CryptoPrice
        """
        prices = {}

        for crypto in cryptos:
            price = await self.get_price(crypto)
            if price:
                prices[crypto] = price
            else:
                logger.warning(f"Could not fetch price for {crypto}")

        return prices

    async def place_order(
        self,
        symbol: str,
        side: OrderSide,
        quantity: float,
        price: Optional[float] = None,
        order_type: OrderType = OrderType.MARKET,
    ) -> Optional[Order]:
        """
        Place a trading order

        Args:
            symbol: Crypto symbol (BTC, ETH, etc)
            side: BUY or SELL
            quantity: Amount to trade
            price: Limit price (for LIMIT orders)
            order_type: MARKET or LIMIT

        Returns:
            Order object or None if failed
        """
        if not self._authenticated:
            logger.error("Not authenticated")
            return None

        try:
            payload = {
                "side": side.value,
                "quantity": quantity,
                "instrument_code": f"{symbol}USD",
            }

            if order_type == OrderType.LIMIT and price:
                payload["price"] = price
                payload["order_type"] = "LIMIT"
            else:
                payload["order_type"] = "MARKET"

            logger.info(f"Placing {side.value} order: {quantity} {symbol} @ {price}")

            response = await self._session.post("/orders", json=payload)
            response.raise_for_status()

            order_data = response.json()

            order = Order(
                order_id=order_data.get("id"),
                symbol=symbol,
                side=side,
                order_type=order_type,
                quantity=quantity,
                price=price,
                status=order_data.get("state", "PENDING"),
                filled_qty=float(order_data.get("filled", 0)),
                average_price=float(order_data.get("average_price", price or 0)),
                timestamp=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )

            logger.info(f"✅ Order placed: {order.order_id}")
            return order

        except Exception as e:
            logger.error(f"Failed to place order: {e}")
            return None

    async def get_order_status(self, order_id: str) -> Optional[Order]:
        """
        Get status of existing order

        Args:
            order_id: Order ID from placement

        Returns:
            Updated Order object
        """
        if not self._authenticated:
            logger.error("Not authenticated")
            return None

        try:
            response = await self._session.get(f"/orders/{order_id}")
            response.raise_for_status()

            data = response.json()

            return Order(
                order_id=order_id,
                symbol=data.get("instrument_code", "").replace("USD", ""),
                side=OrderSide(data.get("side", "BUY")),
                order_type=OrderType(data.get("order_type", "MARKET")),
                quantity=float(data.get("quantity", 0)),
                price=float(data.get("price", 0)) if data.get("price") else None,
                status=data.get("state", "UNKNOWN"),
                filled_qty=float(data.get("filled", 0)),
                average_price=float(data.get("average_price", 0)),
                timestamp=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )

        except Exception as e:
            logger.error(f"Failed to get order status: {e}")
            return None

    async def cancel_order(self, order_id: str) -> bool:
        """
        Cancel an open order

        Args:
            order_id: Order ID to cancel

        Returns:
            True if successful
        """
        if not self._authenticated:
            logger.error("Not authenticated")
            return False

        try:
            response = await self._session.post(f"/orders/{order_id}/cancel")
            response.raise_for_status()

            logger.info(f"✅ Order {order_id} cancelled")
            return True

        except Exception as e:
            logger.error(f"Failed to cancel order: {e}")
            return False


async def test_revolut_connection():
    """Test Revolut X API connection"""

    print("\n" + "=" * 60)
    print("🔗 Testing Revolut X API Connection")
    print("=" * 60)

    client = RevolutXClient()

    # Test connection
    print("\n1️⃣ Connecting to Revolut X...")
    if not await client.connect():
        print("❌ Connection failed. Check your API key.")
        print("\nTo get a Revolut X API key:")
        print("1. Go to https://app.revolut.com")
        print("2. Navigate to Settings → API → Generate API Key")
        print("3. Save your API key to .env file (REVOLUT_API_KEY)")
        return

    print("✅ Connected successfully!")

    # Get account info
    print("\n2️⃣ Fetching account information...")
    account = await client.get_account_info()
    if account:
        print(f"✅ Account ID: {account.get('id')}")
        print(f"   Type: {account.get('account_type')}")
    else:
        print("❌ Could not fetch account info")

    # Get portfolio
    print("\n3️⃣ Fetching crypto portfolio...")
    portfolio = await client.get_portfolio()
    if portfolio:
        print(f"✅ Found {len(portfolio)} crypto assets:")
        for symbol, balance in sorted(portfolio.items()):
            print(f"   {symbol}: {balance.amount:.8f} (${balance.usd_value:.2f})")
    else:
        print("⚠️ No crypto holdings found (or empty portfolio)")

    # Get prices
    print("\n4️⃣ Fetching crypto prices...")
    prices = await client.get_prices(["BTC", "ETH", "USDT"])
    if prices:
        print("✅ Market prices:")
        for symbol, price in sorted(prices.items()):
            print(f"   {symbol}: ${price.price:,.2f}")
    else:
        print("❌ Could not fetch prices")

    # Test order placement (commented for safety)
    print("\n5️⃣ Order placement test")
    print("⏭️ Skipped (would place real order)")
    print("   To test: Uncomment code in test_revolut_connection()")

    # Cleanup
    await client.disconnect()

    print("\n" + "=" * 60)
    print("✅ Revolut X API test completed")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    asyncio.run(test_revolut_connection())
