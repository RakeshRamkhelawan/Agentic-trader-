"""
Smart Order Router for multi-exchange order execution.

Routes orders to optimal venues based on liquidity and pricing.
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple

from backend.execution.broker_interface import ExecutionInterface, OrderResult
from backend.schemas.orders import OrderRequest, OrderSide

logger = logging.getLogger(__name__)


class NoRouteFoundError(Exception):
    """Raised when no adapter is available for the given symbol."""

    pass


@dataclass
class OrderAllocation:
    """Represents allocation of an order to an exchange."""

    exchange: str
    quantity: float
    expected_price: float
    expected_slippage: float = 0.0

    @property
    def expected_cost(self) -> float:
        """Expected total cost including slippage."""
        return self.quantity * self.expected_price * (1 + self.expected_slippage)


@dataclass
class ExchangePricing:
    """Pricing info from an exchange."""

    exchange: str
    bid: float
    ask: float
    available_qty: float
    timestamp: datetime = field(default_factory=datetime.utcnow)


class SmartOrderRouter:
    """
    Routes orders to the best execution venue based on liquidity and pricing.

    Features:
    - Multi-exchange support
    - VWAP-optimized allocation
    - Automatic failover
    - Parallel execution
    """

    def __init__(self, adapters: Optional[Dict[str, ExecutionInterface]] = None):
        """
        Initialize router.

        Args:
            adapters: Optional dict of exchange_name -> adapter
        """
        self.adapters: Dict[str, ExecutionInterface] = adapters or {}
        self.symbol_map: Dict[str, List[str]] = {}  # symbol -> [adapter_names]

    def register_adapter(
        self, name: str, adapter: ExecutionInterface, supported_symbols: List[str]
    ) -> None:
        """
        Register a broker adapter and its supported symbols.

        Args:
            name: Exchange name
            adapter: ExecutionInterface instance
            supported_symbols: List of supported trading pairs
        """
        self.adapters[name] = adapter
        for symbol in supported_symbols:
            if symbol not in self.symbol_map:
                self.symbol_map[symbol] = []
            if name not in self.symbol_map[symbol]:
                self.symbol_map[symbol].append(name)

    async def get_best_prices(self, symbol: str) -> Dict[str, ExchangePricing]:
        """
        Get current prices from all exchanges supporting the symbol.

        Args:
            symbol: Trading pair

        Returns:
            Dict of exchange_name -> pricing info
        """
        exchanges = self.symbol_map.get(symbol, list(self.adapters.keys()))

        if not exchanges:
            return {}

        async def fetch_price(name: str) -> Tuple[str, Optional[ExchangePricing]]:
            try:
                adapter = self.adapters[name]
                ticker = await adapter.get_ticker(symbol)
                return name, ExchangePricing(
                    exchange=name,
                    bid=ticker.get("bid", 0),
                    ask=ticker.get("ask", 0),
                    available_qty=ticker.get("volume", 0) * 0.01,  # Assume 1% available
                )
            except Exception as e:
                logger.warning(f"Failed to get price from {name}: {e}")
                return name, None

        results = await asyncio.gather(*[fetch_price(n) for n in exchanges])
        return {name: pricing for name, pricing in results if pricing}

    def calculate_vwap_routing(
        self, quantity: float, side: OrderSide, prices: Dict[str, ExchangePricing]
    ) -> List[OrderAllocation]:
        """
        Calculate optimal order allocation based on VWAP.

        Allocates order to exchanges proportionally to their liquidity
        and price competitiveness.

        Args:
            quantity: Total order quantity
            side: Buy or Sell
            prices: Dict of exchange pricing

        Returns:
            List of OrderAllocations
        """
        if not prices:
            return []

        # Sort exchanges by price (best first)
        if side == OrderSide.BUY:
            # For buys, lower ask is better
            sorted_exchanges = sorted(prices.items(), key=lambda x: x[1].ask)
        else:
            # For sells, higher bid is better
            sorted_exchanges = sorted(prices.items(), key=lambda x: -x[1].bid)

        allocations = []
        remaining = quantity

        for name, pricing in sorted_exchanges:
            if remaining <= 0:
                break

            # Allocate based on available liquidity
            alloc_qty = min(remaining, pricing.available_qty)

            if alloc_qty > 0:
                price = pricing.ask if side == OrderSide.BUY else pricing.bid

                # Estimate slippage based on order size relative to liquidity
                slippage = (alloc_qty / max(pricing.available_qty, 1)) * 0.001

                allocations.append(
                    OrderAllocation(
                        exchange=name,
                        quantity=alloc_qty,
                        expected_price=price,
                        expected_slippage=slippage,
                    )
                )

                remaining -= alloc_qty

        # If we still have remaining quantity, allocate to first exchange
        if remaining > 0 and sorted_exchanges:
            name, pricing = sorted_exchanges[0]
            price = pricing.ask if side == OrderSide.BUY else pricing.bid
            allocations.append(
                OrderAllocation(
                    exchange=name,
                    quantity=remaining,
                    expected_price=price,
                    expected_slippage=0.002,  # Higher slippage for oversized orders
                )
            )

        return allocations

    async def route_order(
        self, order: OrderRequest, use_vwap: bool = True
    ) -> List[OrderResult]:
        """
        Route order to optimal exchange(s).

        Args:
            order: Order to route
            use_vwap: If True, use VWAP across multiple exchanges

        Returns:
            List of OrderResults from each exchange
        """
        quantity = getattr(order, "quantity", None) or getattr(order, "qty", 0)

        if use_vwap and len(self.adapters) > 1:
            # Get prices from all exchanges
            prices = await self.get_best_prices(order.symbol)

            if not prices:
                raise NoRouteFoundError(
                    f"No execution adapter found for symbol: {order.symbol}"
                )

            # Calculate optimal allocation
            allocations = self.calculate_vwap_routing(quantity, order.side, prices)

            if not allocations:
                raise NoRouteFoundError(f"Could not allocate order for: {order.symbol}")

            # Execute in parallel
            async def execute_allocation(alloc: OrderAllocation) -> OrderResult:
                adapter = self.adapters[alloc.exchange]
                # Create child order with allocated quantity
                child_order = OrderRequest(
                    symbol=order.symbol,
                    side=order.side,
                    order_type=order.order_type,
                    qty=alloc.quantity,
                    limit_price=order.limit_price,
                    stop_price=order.stop_price,
                )
                return await adapter.submit_order(child_order)

            results = await asyncio.gather(
                *[execute_allocation(a) for a in allocations], return_exceptions=True
            )

            # Filter out exceptions
            return [r for r in results if isinstance(r, OrderResult)]

        else:
            # Single exchange routing
            return await self.route_and_execute(order)

    async def route_and_execute(self, order: OrderRequest) -> List[OrderResult]:
        """
        Find best adapter and execute order (single exchange).

        Args:
            order: Order to execute

        Returns:
            List with single OrderResult
        """
        # Find adapters that support this symbol
        adapter_names = self.symbol_map.get(order.symbol)

        if not adapter_names:
            # Try first available adapter
            if self.adapters:
                adapter_name = list(self.adapters.keys())[0]
            else:
                raise NoRouteFoundError(
                    f"No execution adapter found for symbol: {order.symbol}"
                )
        else:
            adapter_name = adapter_names[0]

        adapter = self.adapters[adapter_name]
        result = await adapter.submit_order(order)
        return [result]
