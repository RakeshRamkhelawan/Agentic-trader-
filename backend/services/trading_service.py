"""
Trading Service - Manages exchange connections and data retrieval.

Supports:
- Market data (tickers, products)
- Portfolio management (balances, positions)
- Trade history
- CCXT integration with smart mock fallback
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.cache_layer import get_cache
from backend.core.compliance.decorators import audit_decision
from backend.execution.ccxt_adapter import CCXTAdapter
from backend.services.user_settings_service import get_settings_service

logger = logging.getLogger(__name__)


class TradingService:
    """Service for retrieving trading data from exchanges or mock source."""

    def __init__(self):
        self.settings_service = get_settings_service()
        self._exchange_instances: Dict[str, CCXTAdapter] = {}

        # Determine if we should force mock data (for dev/demo)
        # In a real app, this would be False by default
        self.force_mock = False

    async def _get_exchange_adapter(
        self, db: AsyncSession, tenant_id: str, exchange_id: str
    ) -> Optional[Any]:
        """
        Get or create an exchange adapter for the user.
        """
        from backend.core.config.settings import settings

        # 1. Get API keys
        keys_list = await self.settings_service.get_api_keys(db, tenant_id)
        target_key = next(
            (k for k in keys_list if k.exchange == exchange_id and k.is_valid), None
        )

        creds = {}
        if target_key:
            # 2. Decrypt user credentials
            creds = await self.settings_service.get_decrypted_api_key(
                db, tenant_id, target_key.id
            )
        elif exchange_id == "revolut":
            # 2b. Fallback to System Credentials (defined in .env/settings)

            if settings.REVOLUT_API_KEY and settings.REVOLUT_PRIVATE_KEY:
                logger.info("Using System Credentials for Revolut")
                creds = {
                    "api_key": settings.REVOLUT_API_KEY,
                    "api_secret": settings.REVOLUT_PRIVATE_KEY,  # Pass Private Key as secret
                    "password": "",
                }

        if not creds:
            return None

        # 3. Create/Return adapter
        # Cache key: tenant_id:exchange_id
        cache_key = f"{tenant_id}:{exchange_id}"

        if cache_key in self._exchange_instances:
            return self._exchange_instances[cache_key]

        try:
            adapter = None
            if exchange_id == "revolut":
                from backend.execution.exchange_adapter import ExchangeAdapter

                # Use the custom Revolut X adapter
                adapter = ExchangeAdapter(
                    api_key=creds["api_key"],
                    private_key_pem=creds["api_secret"],
                    base_url=(
                        "https://revx.revolut.com"
                        if not settings.REVOLUT_SANDBOX
                        else "https://sandbox-revx.revolut.com"
                    ),
                )
            else:
                # Check if this is Revolut to pass specific options (legacy check removed)
                options: Dict[str, Any] = {}

                adapter = CCXTAdapter(
                    exchange_id=exchange_id,
                    api_key=creds["api_key"],
                    secret=creds["api_secret"],
                    password=creds.get("passphrase", ""),
                    sandbox=False,  # Only support sandbox for revolut for now via settings
                    options=options,
                )

            # await adapter.connect() # Start connection if needed, usually lazy or managed elsewhere
            self._exchange_instances[cache_key] = adapter
            return adapter
        except Exception as e:
            logger.error(f"Failed to initialize exchange {exchange_id}: {e}")
            return None

    async def get_markets(
        self, db: AsyncSession, tenant_id: str
    ) -> List[Dict[str, Any]]:
        """Get available markets data from cache (populated by MarketDataSync)."""
        cache = get_cache()

        # 1. Try to get from aggregate cache first
        cached_markets = await cache.get("markets:all")
        if cached_markets:
            logger.debug(f"Returning {len(cached_markets)} markets from cache")
            return cached_markets

        # 2. Fallback: try individual exchange caches
        all_markets = []
        seen_symbols = set()

        for exchange_id in ["revolut", "bitvavo", "kraken"]:
            cached = await cache.get(f"markets:{exchange_id}")
            if cached:
                for m in cached:
                    if m["symbol"] not in seen_symbols:
                        all_markets.append(m)
                        seen_symbols.add(m["symbol"])

        if all_markets:
            logger.debug(f"Returning {len(all_markets)} markets from exchange caches")
            return all_markets

        # 3. Last resort: fetch directly (legacy behavior)
        logger.warning("Cache empty, falling back to direct fetch")
        return await self._fetch_markets_direct(db, tenant_id)

    async def _fetch_markets_direct(
        self, db: AsyncSession, tenant_id: str
    ) -> List[Dict[str, Any]]:
        """Direct market fetch fallback (legacy method)."""
        import ccxt.async_support as ccxt

        # Get all valid API keys for the user
        keys_list = await self.settings_service.get_api_keys(db, tenant_id)

        # Identify which exchanges we should fetch from
        active_exchanges = []
        if keys_list:
            for k in keys_list:
                if k.is_valid and k.exchange not in active_exchanges:
                    active_exchanges.append(k.exchange)

        # Always attempt Revolut if system credentials exist
        if "revolut" not in active_exchanges:
            from backend.core.config.settings import settings

            if settings.REVOLUT_API_KEY and settings.REVOLUT_PRIVATE_KEY:
                active_exchanges.append("revolut")

        # Always include Kraken as a base fallback
        if "kraken" not in active_exchanges:
            active_exchanges.append("kraken")

        logger.info(
            f"[DEBUG] Aggregating markets for tenant {tenant_id} from: {active_exchanges}"
        )

        all_markets = []
        seen_symbols = set()
        cache = get_cache()

        for exchange_id in active_exchanges:
            try:
                # 2. Try Cache first
                cache_key = f"markets:{exchange_id}"
                cached_data = await cache.get(cache_key)

                if cached_data:
                    logger.info(
                        f"[DEBUG] Found {len(cached_data)} cached markets for {exchange_id}"
                    )
                    for m in cached_data:
                        if m["symbol"] not in seen_symbols:
                            all_markets.append(m)
                            seen_symbols.add(m["symbol"])
                    continue

                # 3. Cache miss: Fetch and process
                logger.info(f"[DEBUG] Cache miss for {exchange_id}, fetching...")
                adapter = await self._get_exchange_adapter(db, tenant_id, exchange_id)

                exchange_instance = None
                adapter = await self._get_exchange_adapter(db, tenant_id, exchange_id)

                exchange_instance = None
                if adapter and hasattr(adapter, "exchange"):
                    exchange_instance = adapter.exchange
                elif exchange_id == "kraken":
                    exchange_instance = ccxt.kraken()

                # Fetch available symbols
                available_symbols = []
                instruments = await cache.get_instruments(exchange_id)

                if not instruments and adapter:
                    instruments = await adapter.get_instruments()
                    if instruments:
                        await cache.set_instruments(instruments, exchange_id)

                if instruments:
                    if isinstance(instruments, dict):
                        items = instruments.items()
                    elif isinstance(instruments, list):
                        items = [
                            (
                                (
                                    inst
                                    if isinstance(inst, str)
                                    else (inst.get("symbol") or inst.get("name"))
                                ),
                                inst,
                            )
                            for inst in instruments
                        ]
                    else:
                        items = []

                    for sym, detail in items:
                        if not sym:
                            continue
                        if any(
                            x in sym.upper()
                            for x in ["/EUR", "-EUR", "BTCEUR", "ETHEUR"]
                        ):
                            available_symbols.append(sym)

                if not available_symbols and exchange_id == "kraken":
                    available_symbols = [
                        "BTC/EUR",
                        "ETH/EUR",
                        "SOL/EUR",
                        "ADA/EUR",
                        "DOT/EUR",
                        "XRP/EUR",
                        "LINK/EUR",
                        "DOGE/EUR",
                    ]

                if not available_symbols:
                    continue

                target_symbols = available_symbols[:100]
                tickers = {}

                # 4. Fetch Tickers (Bulk or individual)
                if exchange_instance:
                    if not exchange_instance.markets:
                        await exchange_instance.load_markets()
                    try:
                        tickers = await exchange_instance.fetch_tickers(target_symbols)
                    except Exception as e:
                        logger.warning(f"fetch_tickers failed for {exchange_id}: {e}")
                        for symbol in target_symbols:
                            try:
                                tickers[symbol] = await exchange_instance.fetch_ticker(
                                    symbol
                                )
                            except Exception:
                                continue
                elif adapter and hasattr(adapter, "get_tickers"):
                    # Use custom individual/bulk fetcher for Revolut
                    tickers = await adapter.get_tickers(target_symbols)
                elif adapter and hasattr(adapter, "get_ticker"):
                    # Fallback to individual
                    for symbol in target_symbols:
                        ticker = await adapter.get_ticker(symbol)
                        if ticker:
                            tickers[symbol] = ticker

                # 5. Transform and Aggregate
                exchange_markets = []
                for symbol, ticker in tickers.items():
                    if not ticker:
                        continue
                    display_symbol = symbol.replace("/", "-")
                    name = symbol.split("/")[0].split("-")[0]

                    # Map common fields across sources
                    price = ticker.get("last", ticker.get("last_price", 0.0))
                    change = ticker.get("percentage", ticker.get("change_24h", 0.0))
                    volume_val = (
                        ticker.get(
                            "baseVolume",
                            ticker.get("volume_24h", ticker.get("quoteVolume", 0.0)),
                        )
                        or 0.0
                    )

                    market_item = {
                        "symbol": display_symbol,
                        "name": name,
                        "price": float(price),
                        "change": float(change),
                        "volume": self._format_volume(float(volume_val)),
                        "favorite": False,
                    }
                    exchange_markets.append(market_item)
                    if display_symbol not in seen_symbols:
                        all_markets.append(market_item)
                        seen_symbols.add(display_symbol)

                if exchange_markets:
                    await cache.set(cache_key, exchange_markets, ttl=30)

                # Close temporary instance
                if exchange_instance and (
                    not adapter or not hasattr(adapter, "exchange")
                ):
                    await exchange_instance.close()

            except Exception as e:
                logger.error(f"Error fetching {exchange_id} markets: {e}")

        return all_markets

    def _format_volume(self, volume: float) -> str:
        if volume >= 1_000_000_000:
            return f"{volume / 1_000_000_000:.1f}B"
        if volume >= 1_000_000:
            return f"{volume / 1_000_000:.1f}M"
        if volume >= 1_000:
            return f"{volume / 1_000:.1f}K"
        return str(round(volume, 2))

    # ========================================================================
    # Candles Data
    # ========================================================================

    async def get_candles(
        self,
        db: AsyncSession,
        tenant_id: str,
        symbol: str,
        timeframe: str = "1m",
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Get OHLCV candles data."""
        import ccxt.async_support as ccxt

        # 1. Get Exchange Adapter
        keys_list = await self.settings_service.get_api_keys(db, tenant_id)
        adapter = None

        if keys_list:
            valid_key = next((k for k in keys_list if k.is_valid), None)
            if valid_key:
                adapter = await self._get_exchange_adapter(
                    db, tenant_id, valid_key.exchange
                )

        # 2. Fallback to public
        exchange_instance = None
        should_close = False

        if adapter and adapter.exchange:
            exchange_instance = adapter.exchange
        else:
            # Fallback to public Kraken
            try:
                exchange_instance = ccxt.kraken()
                should_close = True
            except Exception as e:
                logger.error(f"Failed to init public exchange: {e}")
                return []

        if not exchange_instance:
            return []

        candles = []
        try:
            # Check market loading
            if not exchange_instance.markets:
                await exchange_instance.load_markets()

            # Normalize symbol (BTC-EUR -> BTC/EUR)
            # Check if symbol format needs adjustment
            exchange_symbol = symbol.replace("-", "/")

            # Fetch OHLCV
            # CCXT returns list of lists: [timestamp, open, high, low, close, volume]
            ohlcv = await exchange_instance.fetch_ohlcv(
                exchange_symbol, timeframe, limit=limit
            )

            for candle in ohlcv:
                candles.append(
                    {
                        "time": candle[0]
                        / 1000,  # Convert ms to seconds for lightweight-charts
                        "open": candle[1],
                        "high": candle[2],
                        "low": candle[3],
                        "close": candle[4],
                        "value": candle[5],  # Volume
                    }
                )

        except Exception as e:
            logger.error(f"Error fetching candles for {symbol}: {e}")
            return []
        finally:
            if should_close:
                await exchange_instance.close()

        return candles

    # ========================================================================
    # Portfolio Data
    # ========================================================================

    async def get_portfolio(self, db: AsyncSession, tenant_id: str) -> Dict[str, Any]:
        """Get portfolio holdings and stats from DB (Local Tracking) and/or Exchange."""
        from sqlalchemy import select

        from backend.models.orders import Order, OrderStatus

        # 1. Calculate Local Portfolio from Order History (DB)
        # This ensures we show "something" even if exchange API fails or is not connected,
        # provided the user has executed trades via our platform.

        query = select(Order).where(
            Order.tenant_id == tenant_id, Order.status == OrderStatus.FILLED
        )
        result = await db.execute(query)
        filled_orders = result.scalars().all()

        # Calculate holdings
        holdings_map = {}  # symbol -> {amount, value_basis}

        for order in filled_orders:
            # parse symbol (BTC-EUR -> BTC)
            base_asset = (
                order.symbol.split("-")[0] if "-" in order.symbol else order.symbol
            )

            if base_asset not in holdings_map:
                holdings_map[base_asset] = 0.0

            if order.side == "buy":
                holdings_map[base_asset] += order.filled_qty
            elif order.side == "sell":
                holdings_map[base_asset] -= order.filled_qty

        # 2. (Optional) Fetch Real Exchange Balances if keys exist
        # For now, we mix in Local DB data.
        # In a full PROD version, we would prioritise Exchange Data.

        # Construct output list
        holdings_list = []
        total_value = 0.0

        # We need current prices to calculate value
        # Reuse get_markets logic lightly or fetch single tickers?
        # For speed, let's assume we might need to fetch prices.
        # For this iteration, we'll try to fetch prices for held assets.

        import ccxt.async_support as ccxt

        public_exchange = ccxt.kraken()  # Use for pricing

        try:
            for asset, amount in holdings_map.items():
                if amount <= 0:
                    continue

                symbol_pair = f"{asset}/EUR"
                price = 0.0
                change = 0.0

                try:
                    ticker = await public_exchange.fetch_ticker(symbol_pair)
                    price = ticker["last"]
                    change = ticker["percentage"]
                except Exception:
                    # Fallback or distinct naming (e.g. USDT)
                    pass

                value = amount * price
                total_value += value

                holdings_list.append(
                    {
                        "symbol": asset,
                        "name": asset,  # Could map to full name
                        "amount": round(amount, 6),
                        "value": round(value, 2),
                        "change": round(change, 2),
                        "allocation": 0,  # calc later
                    }
                )
        finally:
            await public_exchange.close()

        # Calc allocation
        for h in holdings_list:
            if total_value > 0:
                h["allocation"] = round((h["value"] / total_value) * 100, 1)

        # Get Recent Orders (Raw DB)
        recent_orders_query = (
            select(Order)
            .where(Order.tenant_id == tenant_id)
            .order_by(Order.created_at.desc())
            .limit(10)
        )

        res_orders = await db.execute(recent_orders_query)
        db_orders = res_orders.scalars().all()

        recent_orders_list = []
        for o in db_orders:
            # relative time format
            diff = datetime.utcnow() - o.created_at
            if diff.days > 0:
                time_str = f"{diff.days}d ago"
            elif diff.seconds > 3600:
                time_str = f"{diff.seconds // 3600}h ago"
            elif diff.seconds > 60:
                time_str = f"{diff.seconds // 60}m ago"
            else:
                time_str = "just now"

            recent_orders_list.append(
                {
                    "id": o.id,
                    "symbol": o.symbol,
                    "side": o.side,
                    "amount": o.quantity,
                    "price": o.price or o.avg_price or 0,
                    "time": time_str,
                }
            )

        return {
            "total_value": round(total_value, 2),
            "daily_change": 0,  # TODO: Track portfolio snapshots for history
            "daily_change_pct": 0,
            "holdings": holdings_list,
            "recent_orders": recent_orders_list,
        }

    # ========================================================================
    # History Data
    # ========================================================================

    async def get_history(
        self, db: AsyncSession, tenant_id: str
    ) -> List[Dict[str, Any]]:
        """Get trade history from DB."""
        from sqlalchemy import select

        from backend.models.orders import Order

        query = (
            select(Order)
            .where(Order.tenant_id == tenant_id)
            .order_by(Order.created_at.desc())
        )

        result = await db.execute(query)
        orders = result.scalars().all()

        trades = []
        for o in orders:
            trades.append(
                {
                    "id": o.id,
                    "symbol": o.symbol,
                    "side": o.side,
                    "amount": o.quantity,
                    "price": o.avg_price or o.price or 0,
                    "total": (o.avg_price or o.price or 0) * o.quantity,
                    "fee": o.commission or 0,
                    "time": o.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                    "status": o.status.lower(),
                }
            )

        return trades

    async def execute_order(
        self,
        db: AsyncSession,
        tenant_id: str,
        order_request: Dict[str, Any],
        user_prefs: Optional[Dict[str, Any]] = None,
        bypass_risk: bool = False,
    ) -> Dict[str, Any]:
        """
        Execute an order with strict HITL and Risk checks.
        Last Line of Defense.

        Args:
            bypass_risk (bool): If True, skips RiskGuardian check (Use ONLY for Manual Approvals).
        """
        # Audit Log is handled by decorator
        return await self._execute_order_impl(
            db, tenant_id, order_request, user_prefs, bypass_risk
        )

    @audit_decision(action="EXECUTE_ORDER", resource_type="order")
    async def _execute_order_impl(
        self,
        db: AsyncSession,
        tenant_id: str,
        order_request: Dict[str, Any],
        user_prefs: Optional[Dict[str, Any]] = None,
        bypass_risk: bool = False,
    ) -> Dict[str, Any]:
        """
        Internal implementation of execute order.
        """
        # 1. Fetch Preferences if not provided
        if not user_prefs:
            user_prefs = await self.settings_service.get_user_preferences(db, tenant_id)
            # Convert to dict if object
            if hasattr(user_prefs, "__dict__"):
                user_prefs = user_prefs.__dict__

        # 2. Re-Validate with Risk Guardian (Stateless check)
        if not bypass_risk:
            # We instantiate a temporary Guardian to verify this specific request
            from backend.services.risk_guardian_agent import RiskGuardianAgent

            guardian = RiskGuardianAgent(settings_service=self.settings_service)

            # Construct risk payload
            validation = await guardian.validate_order(
                tenant_id, order_request, user_prefs
            )

            if not validation["allowed"]:
                logger.warning(
                    f"🚫 Order BLOCKED by TradingService Guard: {validation['reason']}"
                )
                return {
                    "status": "rejected",
                    "reason": validation["reason"],
                    "requires_approval": validation["requires_approval"],
                }
        else:
            logger.warning(
                f"⚠️ BYPASSING RISK CHECKS for Order: {order_request.get('symbol', 'Unknown')}"
            )

        # 3. Get Exchange Adapter
        # Determine exchange from order or default
        exchange_id = user_prefs.get("default_exchange", "binance")
        adapter = await self._get_exchange_adapter(db, tenant_id, exchange_id)

        if not adapter:
            return {"status": "failed", "reason": f"No credentials for {exchange_id}"}

        # 4. Execute
        # Convert dict to OrderRequest object if needed by Adapter
        # Assuming CCXTAdapter takes a specific object or dict.
        # Checking adapter signature: submit_order(self, order: OrderRequest)
        from backend.schemas.orders import OrderRequest as SchemaOrderRequest

        try:
            req = SchemaOrderRequest(**order_request)
            result = await adapter.submit_order(req)
            return result.__dict__
        except Exception as e:
            logger.error(f"Execution failed: {e}")
            return {"status": "failed", "reason": str(e)}

    async def get_active_orders(
        self, db: AsyncSession, tenant_id: str
    ) -> List[Dict[str, Any]]:
        """Fetch all active orders (SUBMITTED, PENDING_APPROVAL, APPROVED, PARTIALLY_FILLED)."""
        from sqlalchemy import or_, select

        from backend.models.orders import Order, OrderStatus

        query = (
            select(Order)
            .where(
                Order.tenant_id == tenant_id,
                or_(
                    Order.status == OrderStatus.SUBMITTED,
                    Order.status == OrderStatus.PENDING_APPROVAL,
                    Order.status == OrderStatus.APPROVED,
                    Order.status
                    == "PARTIALLY_FILLED",  # Enum might not have this, check model
                ),
            )
            .order_by(Order.created_at.desc())
        )

        result = await db.execute(query)
        orders = result.scalars().all()

        return [
            {
                "order_id": o.id,
                "symbol": o.symbol,
                "side": o.side,
                "quantity": o.quantity,
                "filled_qty": o.filled_qty,
                "status": o.status if isinstance(o.status, str) else o.status.value,
                "created_at": o.created_at.isoformat(),
            }
            for o in orders
        ]

    async def cancel_order(
        self, db: AsyncSession, tenant_id: str, order_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Cancel a specific order by ID.
        Returns None when the order is not found (caller raises 404).
        """
        from sqlalchemy import select

        from backend.models.orders import Order, OrderStatus

        query = select(Order).where(
            Order.id == order_id,
            Order.tenant_id == tenant_id,
        )
        result = await db.execute(query)
        order = result.scalar_one_or_none()

        if not order:
            return None

        cancellable = (
            OrderStatus.SUBMITTED,
            OrderStatus.PENDING_APPROVAL,
            OrderStatus.APPROVED,
        )
        current_status = order.status
        if current_status not in cancellable:
            status_str = (
                current_status.value
                if hasattr(current_status, "value")
                else str(current_status)
            )
            return {
                "status": "error",
                "order_id": order_id,
                "message": f"Order cannot be cancelled (current status: {status_str})",
            }

        order.status = OrderStatus.CANCELLED
        await db.commit()

        return {
            "status": "success",
            "order_id": order_id,
            "message": "Order successfully cancelled",
        }

    async def cancel_all_orders(
        self, db: AsyncSession, tenant_id: str
    ) -> Dict[str, Any]:
        """
        Emergency: Cancel all open orders.
        Returns summary of cancelled orders.
        """
        # Audit Log handled by decorator
        return await self._cancel_all_orders_impl(db, tenant_id)

    @audit_decision(action="CANCEL_ALL_ORDERS", resource_type="order_batch")
    async def _cancel_all_orders_impl(
        self, db: AsyncSession, tenant_id: str
    ) -> Dict[str, Any]:
        """
        Internal implementation of cancel all.
        """
        from sqlalchemy import or_, select

        from backend.models.orders import Order, OrderStatus

        # 1. Fetch active orders
        query = select(Order).where(
            Order.tenant_id == tenant_id,
            or_(
                Order.status == OrderStatus.SUBMITTED,
                Order.status == OrderStatus.PENDING_APPROVAL,
                Order.status == OrderStatus.APPROVED,
            ),
        )
        result = await db.execute(query)
        active_orders = result.scalars().all()

        if not active_orders:
            return {
                "status": "success",
                "cancelled_count": 0,
                "message": "No active orders found.",
            }

        # 2. Iterate and Cancel
        cancelled_count = 0
        errors = []

        # Get adapter (assuming single exchange preference for now, or per order if stored)
        # Ideally we check order.exchange_id if we stored it.
        # Fallback to default exchange.
        user_prefs = await self.settings_service.get_user_preferences(db, tenant_id)
        exchange_id = user_prefs.default_exchange if user_prefs else "binance"

        adapter = await self._get_exchange_adapter(db, tenant_id, exchange_id)
        # Note: If we have multiple exchanges, we should group orders by exchange.

        for order in active_orders:
            try:
                # If adapter supports cancellation
                if adapter and order.status == OrderStatus.SUBMITTED:
                    try:
                        await adapter.cancel_order(order.id, order.symbol)
                    except Exception as e:
                        logger.error(
                            f"Failed to cancel order {order.id} on exchange: {e}"
                        )
                        # We might still want to mark it as CANCELED in DB if we trust the intent?
                        # No, keep it open if exchange fail.
                        errors.append(f"Order {order.id}: {str(e)}")
                        continue

                # Update DB
                order.status = OrderStatus.CANCELLED
                cancelled_count += 1

            except Exception as inner_e:
                errors.append(f"Order {order.id}: {str(inner_e)}")

        await db.commit()

        return {
            "status": "success" if not errors else "partial_success",
            "cancelled_count": cancelled_count,
            "errors": errors,
        }

    async def get_order_history(
        self, db: AsyncSession, tenant_id: str, limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Fetch historical orders (FILLED, FAILED, CANCELLED, REJECTED).
        """
        from sqlalchemy import or_, select

        from backend.models.orders import Order, OrderStatus

        query = (
            select(Order)
            .where(
                Order.tenant_id == tenant_id,
                or_(
                    Order.status == OrderStatus.FILLED,
                    Order.status == OrderStatus.FAILED,
                    Order.status == OrderStatus.CANCELLED,
                    Order.status == OrderStatus.REJECTED,
                ),
            )
            .order_by(Order.created_at.desc())
            .limit(limit)
        )

        result = await db.execute(query)
        orders = result.scalars().all()

        return [
            {
                "order_id": o.id,
                "symbol": o.symbol,
                "side": o.side,
                "quantity": o.quantity,
                "filled_qty": o.filled_qty,
                "status": o.status if isinstance(o.status, str) else o.status.value,
                "avg_price": o.avg_price,
                "created_at": o.created_at.isoformat(),
                "updated_at": o.updated_at.isoformat() if o.updated_at else None,
            }
            for o in orders
        ]

    async def store_market_tick(self, tick_data: Dict[str, Any]):
        """
        Store real-time tick data to TimescaleDB hypertable.

        Args:
            tick_data: Dict matching MarketTick model (symbol, price, etc.)
        """
        from backend.core.database import AsyncSessionLocal
        from backend.models.market_data import MarketTick

        async with AsyncSessionLocal() as session:
            tick = MarketTick(
                symbol=tick_data["symbol"],
                timestamp=(
                    datetime.fromisoformat(tick_data["timestamp"])
                    if isinstance(tick_data["timestamp"], str)
                    else tick_data["timestamp"]
                ),
                price=tick_data["price"],
                volume=tick_data["volume"],
                side=tick_data.get("side"),
                exchange_sequence=tick_data.get("seq"),
            )
            session.add(tick)
            await session.commit()

    async def store_market_ticks_bulk(self, ticks_data: List[Dict[str, Any]]):
        """
        Bulk store market ticks.
        """
        from backend.core.database import AsyncSessionLocal
        from backend.models.market_data import MarketTick

        if not ticks_data:
            return

        async with AsyncSessionLocal() as session:
            ticks = [
                MarketTick(
                    symbol=t["symbol"],
                    timestamp=t["timestamp"],
                    price=t["price"],
                    volume=t.get("volume", 0.0),
                    side=t.get("side"),
                    exchange_sequence=t.get("seq"),
                )
                for t in ticks_data
            ]
            session.add_all(ticks)
            await session.commit()

    async def get_24h_reference_prices(self, symbols: List[str]) -> Dict[str, float]:
        """
        Get the closing price for symbols from roughly 24 hours ago.
        Used to calculate change% when API doesn't provide it.
        """
        from sqlalchemy import text

        from backend.core.database import AsyncSessionLocal

        target_time = datetime.utcnow() - timedelta(hours=24)
        # Look for ticks in a window around 24h ago (e.g. 24h to 25h ago)
        # to find the most relevant "close" of that time.
        # Actually simpler: Get the latest tick BEFORE (now - 24h)

        # DISTINCT ON (symbol) ... ORDER BY timestamp DESC
        # Note: distinct on is Postgres specific

        async with AsyncSessionLocal() as session:
            # We want for each symbol, the tick with timestamp <= target_time, ordered by timestamp desc limit 1
            # In pure SQL: SELECT DISTINCT ON (symbol) symbol, price FROM market_ticks WHERE symbol IN (...) AND timestamp <= ... ORDER BY symbol, timestamp DESC

            if not symbols:
                return {}

            # Create a query for each symbol is too many queries.
            # Use a window function approach or Postgres DISTINCT ON

            sym_list_str = "', '".join(symbols)
            sql = text(
                f"""
                SELECT DISTINCT ON (symbol) symbol, price 
                FROM market_ticks 
                WHERE symbol IN ('{sym_list_str}') 
                  AND timestamp <= :target_time 
                ORDER BY symbol, timestamp DESC
            """
            )

            try:
                result = await session.execute(sql, {"target_time": target_time})
                rows = result.fetchall()
                return {row[0]: float(row[1]) for row in rows}
            except Exception as e:
                logger.error(f"Failed to fetch 24h reference prices: {e}")
                return {}

    async def store_market_candle(self, candle_data: Dict[str, Any]):
        """
        Store OHLCV candle to TimescaleDB hypertable.
        """
        from backend.core.database import AsyncSessionLocal
        from backend.models.market_data import MarketCandle

        async with AsyncSessionLocal() as session:
            candle = MarketCandle(
                symbol=candle_data["symbol"],
                timeframe=candle_data["timeframe"],
                timestamp=(
                    datetime.fromisoformat(candle_data["timestamp"])
                    if isinstance(candle_data["timestamp"], str)
                    else candle_data["timestamp"]
                ),
                open=candle_data["open"],
                high=candle_data["high"],
                low=candle_data["low"],
                close=candle_data["close"],
                volume=candle_data["volume"],
                provider=candle_data.get("provider", "calculated"),
            )
            session.add(candle)
            await session.commit()


# Singleton
_trading_service: Optional[TradingService] = None


def get_trading_service() -> TradingService:
    global _trading_service
    if _trading_service is None:
        _trading_service = TradingService()
    return _trading_service
