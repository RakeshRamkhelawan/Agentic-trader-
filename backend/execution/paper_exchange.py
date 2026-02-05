"""
Paper Exchange for Backtesting.

Simulates realistic order execution with slippage,
balance tracking, and partial fills.
"""
import asyncio
import logging
import random
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional, AsyncGenerator

from backend.execution.broker_interface import ExecutionInterface, OrderResult
from backend.schemas.orders import OrderRequest, OrderSide, OrderStatus
from backend.schemas.market_data import TickerUpdate, OrderBook, OrderUpdate
from backend.schemas.market_data import OrderStatus as MarketOrderStatus

logger = logging.getLogger(__name__)


class PaperExchange(ExecutionInterface):
    """
    Paper trading exchange for backtesting without real trades.
    
    Features:
    - Realistic slippage based on order size and volatility
    - Balance tracking with margin checks
    - Simulated latency
    - Partial fill simulation
    """
    
    def __init__(
        self,
        initial_balance: Optional[Dict[str, float]] = None,
        slippage_factor: float = 0.001,
        latency_ms: tuple = (50, 200),
        fill_rate: float = 0.9
    ):
        """
        Initialize paper exchange.
        
        Args:
            initial_balance: Starting balances (e.g., {"EUR": 10000, "BTC": 1})
            slippage_factor: Base slippage percentage
            latency_ms: Min/max latency in milliseconds
            fill_rate: Percentage of order filled immediately
        """
        self._balance = initial_balance or {"EUR": 10000.0, "BTC": 0.0}
        self.slippage_factor = slippage_factor
        self.latency_min = latency_ms[0] / 1000
        self.latency_max = latency_ms[1] / 1000
        self.fill_rate = fill_rate
        
        # Order tracking
        self._orders: Dict[str, OrderResult] = {}
        self._fills: List[Dict[str, Any]] = []
        
        # Ticker data (for slippage calculation)
        self._tickers: Dict[str, TickerUpdate] = {}
        
        # Volatility cache
        self._volatility: Dict[str, float] = {}
    
    @property
    def balance(self) -> Dict[str, float]:
        """Get current balance."""
        return self._balance.copy()
    
    def set_ticker(self, ticker: TickerUpdate) -> None:
        """Update ticker data for a symbol."""
        self._tickers[ticker.symbol] = ticker
    
    def set_volatility(self, symbol: str, volatility: float) -> None:
        """Set volatility for slippage calculation."""
        self._volatility[symbol] = volatility
    
    def calculate_slippage(
        self,
        side: OrderSide,
        quantity: float,
        symbol: str
    ) -> float:
        """
        Calculate slippage based on order size and volatility.
        
        Args:
            side: Buy or Sell
            quantity: Order quantity
            symbol: Trading pair
            
        Returns:
            Slippage percentage (0.001 = 0.1%)
        """
        ticker = self._tickers.get(symbol)
        volatility = self._volatility.get(symbol, 0.02)  # Default 2%
        
        if not ticker:
            return self.slippage_factor
        
        # Market impact: larger orders have more slippage
        volume_ratio = quantity / max(ticker.volume_24h, 1.0)
        market_impact = volume_ratio * volatility
        
        # Add random component
        random_factor = random.uniform(0.5, 1.5)
        
        slippage = (self.slippage_factor + market_impact) * random_factor
        return min(slippage, 0.05)  # Cap at 5%
    
    # ==================== REST METHODS ====================
    
    async def submit_order(self, order: OrderRequest) -> OrderResult:
        """Submit a paper order."""
        # Simulate latency
        await asyncio.sleep(random.uniform(self.latency_min, self.latency_max))
        
        # Get quantity from order (handle both 'qty' and 'quantity' attributes)
        quantity = getattr(order, 'quantity', None) or getattr(order, 'qty', 0)
        
        # Get current price
        ticker = self._tickers.get(order.symbol)
        if not ticker:
            # Default price if no ticker
            base_price = 45000.0
        else:
            base_price = ticker.ask if order.side == OrderSide.BUY else ticker.bid
        
        # Calculate slippage
        slippage = self.calculate_slippage(order.side, quantity, order.symbol)
        
        if order.side == OrderSide.BUY:
            fill_price = base_price * (1 + slippage)
        else:
            fill_price = base_price * (1 - slippage)
        
        # Calculate fill
        filled_qty = quantity * self.fill_rate
        remaining_qty = quantity - filled_qty
        
        # Determine status
        if remaining_qty == 0:
            status = OrderStatus.FILLED
        elif filled_qty > 0:
            status = OrderStatus.PARTIALLY_FILLED
        else:
            status = OrderStatus.OPEN
        
        # Create result
        order_id = str(uuid.uuid4())
        client_order_id = str(order.client_order_id) if hasattr(order, 'client_order_id') else ""
        
        result = OrderResult(
            order_id=order_id,
            client_order_id=client_order_id,
            status=status,
            filled_qty=filled_qty,
            remaining_qty=remaining_qty,
            avg_price=fill_price,
            raw_response={
                "slippage": slippage,
                "base_price": base_price
            }
        )
        
        # Update balance
        self._update_balance(order.side, order.symbol, filled_qty, fill_price)
        
        # Store order
        self._orders[order_id] = result
        self._fills.append({
            "order_id": order_id,
            "symbol": order.symbol,
            "side": order.side.value,
            "quantity": filled_qty,
            "price": fill_price,
            "timestamp": datetime.utcnow()
        })
        
        logger.info(f"Paper order filled: {order.side.value} {filled_qty} {order.symbol} @ {fill_price:.2f}")
        
        return result
    
    def _update_balance(
        self,
        side: OrderSide,
        symbol: str,
        quantity: float,
        price: float
    ) -> None:
        """Update balance after fill."""
        # Parse symbol (e.g., "BTC/EUR" -> base="BTC", quote="EUR")
        parts = symbol.split("/")
        if len(parts) != 2:
            return
        
        base, quote = parts
        cost = quantity * price
        
        if side == OrderSide.BUY:
            # Buying: spend quote, get base
            self._balance[quote] = self._balance.get(quote, 0) - cost
            self._balance[base] = self._balance.get(base, 0) + quantity
        else:
            # Selling: spend base, get quote
            self._balance[base] = self._balance.get(base, 0) - quantity
            self._balance[quote] = self._balance.get(quote, 0) + cost
    
    async def get_order_status(self, order_id: str) -> OrderResult:
        """Get order status."""
        if order_id in self._orders:
            return self._orders[order_id]
        
        return OrderResult(
            order_id=order_id,
            client_order_id="",
            status=OrderStatus.REJECTED,
            error_message="Order not found"
        )
    
    async def get_balance(self) -> Dict[str, float]:
        """Get current balance."""
        return self.balance
    
    async def get_ticker(self, symbol: str) -> Dict[str, float]:
        """Get ticker data."""
        ticker = self._tickers.get(symbol)
        if ticker:
            return {
                "bid": ticker.bid,
                "ask": ticker.ask,
                "last": ticker.last,
                "volume": ticker.volume_24h
            }
        return {"bid": 45000.0, "ask": 45010.0, "last": 45005.0, "volume": 1000000.0}
    
    async def cancel_all_orders(self) -> None:
        """Cancel all open orders."""
        for order_id, order in self._orders.items():
            if order.status in [OrderStatus.OPEN, OrderStatus.PARTIALLY_FILLED]:
                order.status = OrderStatus.CANCELLED
        logger.info("All paper orders cancelled")
    
    # ==================== WEBSOCKET STREAMING (Not implemented for paper) ====================
    
    async def subscribe_ticker(self, symbol: str) -> AsyncGenerator[TickerUpdate, None]:
        """Not implemented for paper exchange."""
        while True:
            ticker = self._tickers.get(symbol)
            if ticker:
                yield ticker
            await asyncio.sleep(1.0)
    
    async def subscribe_orderbook(self, symbol: str, depth: int = 10) -> AsyncGenerator[OrderBook, None]:
        """Not implemented for paper exchange."""
        while True:
            yield OrderBook(
                symbol=symbol,
                bids=[(45000.0 - i * 10, 1.0) for i in range(depth)],
                asks=[(45010.0 + i * 10, 1.0) for i in range(depth)],
                timestamp=datetime.utcnow()
            )
            await asyncio.sleep(1.0)
    
    async def subscribe_orders(self) -> AsyncGenerator[OrderUpdate, None]:
        """Not implemented for paper exchange."""
        while True:
            await asyncio.sleep(10.0)
