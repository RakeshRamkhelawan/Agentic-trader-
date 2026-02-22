# C4 Architecture - Level 4: Code

> Code-level view showing implementation details of critical components

---

## Overview

This level provides detailed code examples and explanations of the most important implementation patterns in the Agentic Trader Platform.

---

## 1. Authentication & Authorization

### JWT Token Validation

**File**: `backend/security/jwt_handler.py`

```python
"""
JWT Token Handler

Implements RS256 token validation using JWKS from Auth0.
Critical for multi-tenant SaaS security.
"""

import jwt
from jwt import PyJWKClient
from fastapi import HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

class JWTHandler:
    def __init__(self, jwks_url: str, audience: str, issuer: str):
        self.jwks_client = PyJWKClient(jwks_url)
        self.audience = audience
        self.issuer = issuer

    async def verify_token(self, credentials: HTTPAuthorizationCredentials) -> dict:
        """
        Verify and decode JWT token.

        Returns:
            dict: Decoded token claims including tenant_id, account_id

        Raises:
            HTTPException: 401 if token is invalid
        """
        token = credentials.credentials

        try:
            # Get signing key from JWKS
            signing_key = self.jwks_client.get_signing_key_from_jwt(token)

            # Verify token
            payload = jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256"],
                audience=self.audience,
                issuer=self.issuer,
            )

            # Extract tenant context for multi-tenancy
            return {
                "sub": payload["sub"],
                "tenant_id": payload.get("https://yourapp.com/tenant_id"),
                "account_id": payload.get("https://yourapp.com/account_id"),
                "permissions": payload.get("permissions", []),
            }

        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token expired")
        except jwt.JWTClaimsError:
            raise HTTPException(status_code=401, detail="Invalid claims")
        except jwt.JWTError:
            raise HTTPException(status_code=401, detail="Invalid token")

# Dependency for FastAPI endpoints
async def get_current_user(credentials: HTTPAuthorizationCredentials = Security(security)):
    """FastAPI dependency to get authenticated user."""
    jwt_handler = JWTHandler(
        jwks_url=f"https://{settings.AUTH0_DOMAIN}/.well-known/jwks.json",
        audience=settings.AUTH0_AUDIENCE,
        issuer=f"https://{settings.AUTH0_DOMAIN}/"
    )
    return await jwt_handler.verify_token(credentials)
```

### Row-Level Security (RLS)

**File**: `backend/security/rls.py`

```python
"""
Row-Level Security Enforcer

Ensures multi-tenant data isolation at database level.
All queries automatically filter by tenant_id.
"""

from sqlalchemy import event
from sqlalchemy.orm import Session

class RLSEnforcer:
    """Enforces RLS policies on database queries."""

    def __init__(self, tenant_id: str, account_id: str):
        self.tenant_id = tenant_id
        self.account_id = account_id

    def apply_to_query(self, query, model_class):
        """
        Apply RLS filter to SQLAlchemy query.

        Usage:
            query = session.query(Order)
            query = rls.apply_to_query(query, Order)
            results = query.all()  # Only returns orders for this tenant
        """
        if hasattr(model_class, 'tenant_id'):
            query = query.filter(model_class.tenant_id == self.tenant_id)

        if hasattr(model_class, 'account_id'):
            query = query.filter(model_class.account_id == self.account_id)

        return query

# SQLAlchemy model base with RLS
from sqlalchemy import Column, String
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class TenantMixin:
    """Mixin to add RLS columns to models."""
    tenant_id = Column(String, nullable=False, index=True)
    account_id = Column(String, nullable=False, index=True)

class Order(Base, TenantMixin):
    __tablename__ = 'orders'

    id = Column(String, primary_key=True)
    symbol = Column(String, nullable=False)
    side = Column(String, nullable=False)  # buy/sell
    amount = Column(String, nullable=False)
    status = Column(String, default='pending')
```

---

## 2. Trading Service

**File**: `backend/services/trading_service.py`

```python
"""
Trading Service

Core business logic for order management and execution.
Implements the trading workflow with risk checks.
"""

from typing import Optional
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession

class TradingService:
    """
    Manages the complete order lifecycle.

    Responsibilities:
    - Order validation
    - Risk checking
    - Exchange execution
    - Order state management
    - Audit logging
    """

    def __init__(
        self,
        db: AsyncSession,
        risk_service: RiskService,
        exchange_client: BitvavoClient,
        event_bus: EventBus,
        audit_logger: AuditLogger
    ):
        self.db = db
        self.risk_service = risk_service
        self.exchange = exchange_client
        self.event_bus = event_bus
        self.audit = audit_logger

    async def create_order(
        self,
        tenant_id: str,
        account_id: str,
        symbol: str,
        side: str,
        amount: Decimal,
        order_type: str = "market",
        price: Optional[Decimal] = None
    ) -> Order:
        """
        Create and execute a new order.

        Workflow:
        1. Validate order parameters
        2. Check risk limits
        3. Execute on exchange
        4. Save to database
        5. Publish event
        6. Log audit trail

        Args:
            tenant_id: Organization identifier
            account_id: User account identifier
            symbol: Trading pair (e.g., "BTC-EUR")
            side: "buy" or "sell"
            amount: Order quantity
            order_type: "market", "limit", "stop"
            price: Limit price (required for limit orders)

        Returns:
            Order: Created order object

        Raises:
            RiskViolationError: If order exceeds risk limits
            ExchangeError: If exchange execution fails
        """
        # 1. Validate
        self._validate_order(symbol, side, amount, order_type, price)

        # 2. Risk check
        risk_check = await self.risk_service.check_order(
            account_id=account_id,
            symbol=symbol,
            side=side,
            amount=amount,
            current_price=await self.exchange.get_price(symbol)
        )

        if not risk_check.approved:
            await self.audit.log_rejected_order(tenant_id, account_id, risk_check.reason)
            raise RiskViolationError(risk_check.reason)

        # 3. Execute on exchange
        try:
            exchange_order = await self.exchange.place_order(
                symbol=symbol,
                side=side,
                amount=str(amount),
                order_type=order_type,
                price=str(price) if price else None
            )
        except ExchangeError as e:
            await self.audit.log_exchange_error(tenant_id, account_id, str(e))
            raise

        # 4. Save to database
        order = Order(
            id=exchange_order['orderId'],
            tenant_id=tenant_id,
            account_id=account_id,
            symbol=symbol,
            side=side,
            amount=str(amount),
            price=str(price) if price else None,
            status=exchange_order['status'],
            exchange_order_id=exchange_order['orderId']
        )

        self.db.add(order)
        await self.db.commit()

        # 5. Publish event for real-time updates
        await self.event_bus.publish("orders", {
            "type": "order_created",
            "tenant_id": tenant_id,
            "account_id": account_id,
            "order": order.to_dict()
        })

        # 6. Audit log
        await self.audit.log_order_created(tenant_id, account_id, order)

        return order

    async def get_orders(
        self,
        tenant_id: str,
        account_id: str,
        status: Optional[str] = None,
        limit: int = 100
    ) -> list[Order]:
        """
        Get orders for account with RLS enforcement.

        Returns only orders belonging to the specified
        tenant and account (row-level security).
        """
        query = self.db.query(Order).filter(
            Order.tenant_id == tenant_id,
            Order.account_id == account_id
        )

        if status:
            query = query.filter(Order.status == status)

        return await query.order_by(Order.created_at.desc()).limit(limit).all()
```

---

## 3. Backtest Engine

**File**: `backend/services/backtest_service.py`

```python
"""
Backtest Service

Historical simulation engine for strategy validation.
Supports both single-asset and multi-asset backtests.
"""

import pandas as pd
from datetime import datetime, timedelta
from typing import Callable, Optional
from dataclasses import dataclass

@dataclass
class BacktestConfig:
    """Configuration for backtest execution."""
    symbols: list[str]
    start_date: datetime
    end_date: datetime
    initial_capital: float
    position_size_pct: float = 0.1  # 10% per position
    commission_pct: float = 0.0025  # 0.25% per trade
    use_elemental: bool = True
    use_vedastro: bool = True

@dataclass
class BacktestResult:
    """Results from backtest execution."""
    config: BacktestConfig
    trades: pd.DataFrame
    equity_curve: pd.DataFrame
    metrics: dict

    # Performance metrics
    total_return: float
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float
    profit_factor: float

class BacktestService:
    """
    Backtesting engine for trading strategies.

    Implements event-driven backtesting with support for:
    - Historical market data replay
    - Elemental consensus signals
    - VedAstro astrological timing
    - Multi-asset portfolio simulation
    """

    def __init__(
        self,
        market_data_service: MarketDataService,
        elemental_service: ElementalService,
        vedastro_service: VedAstroService,
        cache: CacheClient
    ):
        self.market_data = market_data_service
        self.elemental = elemental_service
        self.vedastro = vedastro_service
        self.cache = cache

    async def run_backtest(
        self,
        config: BacktestConfig,
        strategy: Optional[Callable] = None
    ) -> BacktestResult:
        """
        Execute backtest with given configuration.

        Args:
            config: Backtest parameters
            strategy: Optional custom strategy function

        Returns:
            BacktestResult with trades and metrics
        """
        # Check cache for existing results
        cache_key = self._generate_cache_key(config)
        cached = await self.cache.get(cache_key)
        if cached:
            return BacktestResult(**cached)

        # Fetch historical data
        historical_data = await self._fetch_historical_data(config)

        # Initialize portfolio
        portfolio = Portfolio(
            initial_capital=config.initial_capital,
            symbols=config.symbols
        )

        # Run simulation
        trades = []
        for timestamp, market_snapshot in historical_data.iterrows():
            # Get signals
            signals = await self._generate_signals(
                timestamp=timestamp,
                data=market_snapshot,
                config=config
            )

            # Execute strategy
            if strategy:
                actions = strategy(portfolio, signals, market_snapshot)
            else:
                actions = self._default_strategy(portfolio, signals)

            # Execute trades
            for action in actions:
                trade = await self._execute_trade(
                    portfolio=portfolio,
                    action=action,
                    timestamp=timestamp,
                    price=market_snapshot[action.symbol]['close']
                )
                if trade:
                    trades.append(trade)

        # Calculate metrics
        metrics = self._calculate_metrics(trades, portfolio)

        # Build result
        result = BacktestResult(
            config=config,
            trades=pd.DataFrame(trades),
            equity_curve=portfolio.equity_curve,
            metrics=metrics,
            total_return=metrics['total_return'],
            sharpe_ratio=metrics['sharpe_ratio'],
            max_drawdown=metrics['max_drawdown'],
            win_rate=metrics['win_rate'],
            profit_factor=metrics['profit_factor']
        )

        # Cache results
        await self.cache.set(cache_key, result.__dict__, ttl=3600)

        return result

    async def _generate_signals(
        self,
        timestamp: datetime,
        data: pd.DataFrame,
        config: BacktestConfig
    ) -> dict:
        """Generate trading signals from all sources."""
        signals = {}

        # Technical signals (from data)
        signals['technical'] = self._calculate_technical_signals(data)

        # Elemental consensus
        if config.use_elemental:
            signals['elemental'] = await self.elemental.calculate_consensus(
                timestamp=timestamp,
                symbols=config.symbols
            )

        # VedAstro timing
        if config.use_vedastro:
            signals['vedastro'] = await self.vedastro.get_timings(
                timestamp=timestamp,
                location="Amsterdam"  # Configurable
            )

        return signals

    def _calculate_metrics(
        self,
        trades: list,
        portfolio: Portfolio
    ) -> dict:
        """Calculate performance metrics from trades."""
        if not trades:
            return {
                'total_return': 0.0,
                'sharpe_ratio': 0.0,
                'max_drawdown': 0.0,
                'win_rate': 0.0,
                'profit_factor': 0.0
            }

        trades_df = pd.DataFrame(trades)

        returns = trades_df['profit_loss']
        wins = returns[returns > 0]
        losses = returns[returns < 0]

        return {
            'total_return': (portfolio.current_value / portfolio.initial_capital - 1) * 100,
            'sharpe_ratio': returns.mean() / returns.std() * (252 ** 0.5),  # Annualized
            'max_drawdown': portfolio.max_drawdown,
            'win_rate': len(wins) / len(trades) * 100 if trades else 0,
            'profit_factor': abs(wins.sum() / losses.sum()) if len(losses) > 0 else float('inf')
        }
```

---

## 4. WebSocket Manager

**File**: `backend/api/websocket_manager.py`

```python
"""
WebSocket Connection Manager

Manages real-time connections for live price feeds and order updates.
Implements channel-based pub/sub with multi-tenant isolation.
"""

import asyncio
from typing import Dict, Set, Optional
from fastapi import WebSocket
from dataclasses import dataclass, field

@dataclass
class Connection:
    """Represents a WebSocket connection."""
    websocket: WebSocket
    tenant_id: str
    account_id: str
    subscriptions: Set[str] = field(default_factory=set)
    connected_at: datetime = field(default_factory=datetime.utcnow)
    last_ping: datetime = field(default_factory=datetime.utcnow)

class WebSocketManager:
    """
    Manages WebSocket connections and message routing.

    Features:
    - Multi-tenant channel isolation
    - Automatic heartbeat/ping-pong
    - Broadcast to channel subscribers
    - Connection statistics
    """

    def __init__(self):
        # connection_id -> Connection
        self.connections: Dict[str, Connection] = {}
        # channel -> set of connection_ids
        self.channels: Dict[str, Set[str]] = {}
        self._lock = asyncio.Lock()

    async def connect(
        self,
        websocket: WebSocket,
        connection_id: str,
        tenant_id: str,
        account_id: str
    ) -> None:
        """Accept new WebSocket connection."""
        await websocket.accept()

        async with self._lock:
            self.connections[connection_id] = Connection(
                websocket=websocket,
                tenant_id=tenant_id,
                account_id=account_id
            )

        # Send connection confirmation
        await websocket.send_json({
            "type": "connected",
            "connection_id": connection_id,
            "timestamp": datetime.utcnow().isoformat()
        })

    async def subscribe(self, connection_id: str, channel: str) -> bool:
        """
        Subscribe connection to a channel.

        Channels:
        - ticker.{symbol}: Price updates
        - orderbook.{symbol}: Orderbook depth
        - orders.{account_id}: User's orders
        """
        if connection_id not in self.connections:
            return False

        conn = self.connections[connection_id]

        # Tenant isolation for user-specific channels
        if channel == "orders":
            channel = f"orders.{conn.account_id}"

        async with self._lock:
            conn.subscriptions.add(channel)

            if channel not in self.channels:
                self.channels[channel] = set()
            self.channels[channel].add(connection_id)

        return True

    async def broadcast_to_channel(
        self,
        channel: str,
        message: dict,
        message_type: str = "update"
    ) -> int:
        """
        Broadcast message to all subscribers of a channel.

        Returns:
            int: Number of successful deliveries
        """
        if channel not in self.channels:
            return 0

        full_message = {
            "channel": channel,
            "type": message_type,
            "data": message,
            "timestamp": datetime.utcnow().isoformat()
        }

        subscribers = list(self.channels[channel])
        sent_count = 0

        for conn_id in subscribers:
            if conn_id in self.connections:
                conn = self.connections[conn_id]
                try:
                    await conn.websocket.send_json(full_message)
                    sent_count += 1
                except Exception:
                    # Connection closed, will be cleaned up
                    await self.disconnect(conn_id)

        return sent_count

    async def disconnect(self, connection_id: str) -> None:
        """Clean up disconnected client."""
        async with self._lock:
            if connection_id in self.connections:
                conn = self.connections[connection_id]

                # Remove from all channels
                for channel in conn.subscriptions:
                    if channel in self.channels:
                        self.channels[channel].discard(connection_id)
                        if not self.channels[channel]:
                            del self.channels[channel]

                del self.connections[connection_id]
```

---

## 5. MCP Tool Implementation

**File**: `backend/mcp_server/tools/backtest_tool.py`

```python
"""
MCP Backtest Tool

Exposes backtesting functionality to Claude Desktop via MCP protocol.
Allows AI assistant to run strategy simulations.
"""

from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Literal

# MCP Server instance
mcp = FastMCP("agentic-trader")

class BacktestInput(BaseModel):
    """Input parameters for backtest execution."""
    symbols: list[str] = Field(
        description="Trading pairs to backtest (e.g., ['BTC-EUR', 'ETH-EUR'])"
    )
    start_date: str = Field(
        description="Start date in ISO format (YYYY-MM-DD)"
    )
    end_date: str = Field(
        description="End date in ISO format (YYYY-MM-DD)"
    )
    initial_capital: float = Field(
        default=10000.0,
        description="Initial portfolio capital in EUR"
    )
    strategy: Literal["elemental", "technical", "combined"] = Field(
        default="elemental",
        description="Trading strategy to use"
    )

class BacktestOutput(BaseModel):
    """Results from backtest execution."""
    total_return: float
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float
    total_trades: int
    summary: str

@mcp.tool()
async def run_backtest(params: BacktestInput) -> BacktestOutput:
    """
    Run historical backtest of trading strategy.

    This tool simulates trading over historical data to validate
    strategy performance before deploying with real capital.

    Args:
        params: Backtest configuration

    Returns:
        Performance metrics and trade summary

    Example:
        "Run a backtest for BTC-EUR from January to March 2024"
        → run_backtest(
            symbols=["BTC-EUR"],
            start_date="2024-01-01",
            end_date="2024-03-31"
          )
    """
    # Import service (direct import, no HTTP overhead)
    from backend.services.backtest_service import BacktestService, BacktestConfig

    # Parse dates
    start = datetime.fromisoformat(params.start_date)
    end = datetime.fromisoformat(params.end_date)

    # Create config
    config = BacktestConfig(
        symbols=params.symbols,
        start_date=start,
        end_date=end,
        initial_capital=params.initial_capital,
        use_elemental=params.strategy in ["elemental", "combined"]
    )

    # Execute backtest
    service = BacktestService(...)  # Dependencies injected
    result = await service.run_backtest(config)

    # Format output for AI consumption
    return BacktestOutput(
        total_return=result.total_return,
        sharpe_ratio=result.sharpe_ratio,
        max_drawdown=result.max_drawdown,
        win_rate=result.win_rate,
        total_trades=len(result.trades),
        summary=format_backtest_summary(result)
    )

def format_backtest_summary(result: BacktestResult) -> str:
    """Format results as human-readable summary."""
    return f"""
Backtest Results ({result.config.start_date.date()} to {result.config.end_date.date()})

Strategy: {'Elemental' if result.config.use_elemental else 'Technical'}
Symbols: {', '.join(result.config.symbols)}

Performance:
- Total Return: {result.total_return:+.2f}%
- Sharpe Ratio: {result.sharpe_ratio:.2f}
- Max Drawdown: {result.max_drawdown:.2f}%
- Win Rate: {result.win_rate:.1f}%
- Total Trades: {len(result.trades)}

{generate_recommendation(result)}
"""

def generate_recommendation(result: BacktestResult) -> str:
    """Generate AI recommendation based on results."""
    if result.sharpe_ratio > 1.5 and result.max_drawdown < 20:
        return "✅ Strategy shows strong risk-adjusted returns. Suitable for live deployment."
    elif result.sharpe_ratio > 1.0:
        return "⚠️ Strategy is viable but consider position sizing to limit drawdowns."
    else:
        return "❌ Strategy underperforms. Consider parameter optimization or different approach."
```

---

## Code Organization Summary

```
backend/
├── api/                     # HTTP/WebSocket endpoints
├── services/                # Business logic
├── core/                    # Shared infrastructure
├── adapters/                # External integrations
├── security/                # Auth, RLS, audit
└── mcp_server/              # AI tool interface

Frontend:
├── src/
│   ├── components/          # React components
│   ├── hooks/               # Custom hooks (useWebSocket)
│   ├── services/            # API clients
│   └── store/               # State management
```

---

## Related Documentation

- [Level 3: Component](./03_COMPONENT.md)
- [Architecture Decision Records](../../adr/)
- [Engineering Onboarding](../../engineering/DEVELOPMENT.md)
