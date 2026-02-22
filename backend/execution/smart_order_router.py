"""
Smart Order Router for multi-exchange order execution.

Routes orders to optimal venues based on liquidity and pricing.
Includes Circuit Breaker pattern for resilience against exchange downtime.
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Tuple

from backend.execution.broker_interface import ExecutionInterface, OrderResult
from backend.schemas.orders import OrderRequest, OrderSide

logger = logging.getLogger(__name__)


class NoRouteFoundError(Exception):
    """Raised when no adapter is available for the given symbol."""
    pass


class CircuitBreakerState(Enum):
    """Circuit breaker states for exchange health."""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if service recovered


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


@dataclass
class ExchangeCircuitBreaker:
    """
    Circuit breaker state for a single exchange.
    
    In-memory structure for ultra-fast lookups (< 10μs).
    No Redis/network calls in hot path.
    """
    exchange: str
    state: CircuitBreakerState = CircuitBreakerState.CLOSED
    failure_count: int = 0
    success_count: int = 0
    last_failure_time: Optional[float] = None
    half_open_calls: int = 0
    
    # Configuration
    failure_threshold: int = 5          # Failures before opening
    recovery_timeout: float = 30.0      # Seconds before half-open
    half_open_max_calls: int = 3        # Test calls in half-open
    success_threshold: int = 2          # Successes to close
    
    def can_execute(self) -> bool:
        """
        Check if request can be executed.
        Ultra-fast in-memory check (< 10μs).
        """
        if self.state == CircuitBreakerState.CLOSED:
            return True
        
        if self.state == CircuitBreakerState.OPEN:
            # Check if recovery timeout passed
            if self.last_failure_time:
                elapsed = time.time() - self.last_failure_time
                if elapsed >= self.recovery_timeout:
                    logger.info(f"[{self.exchange}] Recovery timeout passed, entering HALF_OPEN")
                    self._transition_to(CircuitBreakerState.HALF_OPEN)
                    return True
            return False
        
        if self.state == CircuitBreakerState.HALF_OPEN:
            if self.half_open_calls < self.half_open_max_calls:
                self.half_open_calls += 1
                return True
            return False
        
        return True
    
    def record_success(self) -> None:
        """Record successful call."""
        if self.state == CircuitBreakerState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.success_threshold:
                logger.info(f"[{self.exchange}] Success threshold reached, closing circuit")
                self._transition_to(CircuitBreakerState.CLOSED)
        else:
            # Reset failure count on success in CLOSED state
            self.failure_count = 0
    
    def record_failure(self) -> None:
        """Record failed call."""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.state == CircuitBreakerState.HALF_OPEN:
            logger.warning(f"[{self.exchange}] Failure in HALF_OPEN, opening circuit")
            self._transition_to(CircuitBreakerState.OPEN)
        elif self.state == CircuitBreakerState.CLOSED:
            if self.failure_count >= self.failure_threshold:
                logger.warning(f"[{self.exchange}] Failure threshold ({self.failure_threshold}) reached, opening circuit")
                self._transition_to(CircuitBreakerState.OPEN)
    
    def _transition_to(self, new_state: CircuitBreakerState) -> None:
        """Transition to new state with logging."""
        old_state = self.state
        self.state = new_state
        logger.warning(f"[{self.exchange}] Circuit transitioned: {old_state.value} -> {new_state.value}")
        
        # Reset counters on transition
        if new_state == CircuitBreakerState.CLOSED:
            self.failure_count = 0
            self.success_count = 0
            self.half_open_calls = 0
        elif new_state == CircuitBreakerState.OPEN:
            self.half_open_calls = 0
            self.success_count = 0
        elif new_state == CircuitBreakerState.HALF_OPEN:
            self.failure_count = 0
            self.half_open_calls = 0
    
    def get_metrics(self) -> Dict:
        """Get circuit breaker metrics."""
        return {
            "exchange": self.exchange,
            "state": self.state.value,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "half_open_calls": self.half_open_calls,
            "last_failure_time": self.last_failure_time,
        }


class SmartOrderRouter:
    """
    Routes orders to the best execution venue based on liquidity and pricing.
    
    Features:
    - Multi-exchange support
    - VWAP-optimized allocation
    - Circuit breaker protection per exchange
    - Automatic failover to healthy exchanges
    - Parallel execution
    """

    def __init__(
        self, 
        adapters: Optional[Dict[str, ExecutionInterface]] = None,
        enable_circuit_breaker: bool = True,
    ):
        """
        Initialize router.
        
        Args:
            adapters: Optional dict of exchange_name -> adapter
            enable_circuit_breaker: If True, enable circuit breaker protection
        """
        self.adapters: Dict[str, ExecutionInterface] = adapters or {}
        self.symbol_map: Dict[str, List[str]] = {}  # symbol -> [adapter_names]
        self.enable_circuit_breaker = enable_circuit_breaker
        
        # Circuit breakers per exchange (in-memory for <10μs lookups)
        self._circuit_breakers: Dict[str, ExchangeCircuitBreaker] = {}

    def register_adapter(
        self, 
        name: str, 
        adapter: ExecutionInterface, 
        supported_symbols: List[str],
        failure_threshold: int = 5,
        recovery_timeout: float = 30.0,
    ) -> None:
        """
        Register a broker adapter and its supported symbols.
        
        Args:
            name: Exchange name
            adapter: ExecutionInterface instance
            supported_symbols: List of supported trading pairs
            failure_threshold: Failures before circuit opens
            recovery_timeout: Seconds before attempting recovery
        """
        self.adapters[name] = adapter
        
        # Initialize circuit breaker for this exchange
        if self.enable_circuit_breaker:
            self._circuit_breakers[name] = ExchangeCircuitBreaker(
                exchange=name,
                failure_threshold=failure_threshold,
                recovery_timeout=recovery_timeout,
            )
        
        for symbol in supported_symbols:
            if symbol not in self.symbol_map:
                self.symbol_map[symbol] = []
            if name not in self.symbol_map[symbol]:
                self.symbol_map[symbol].append(name)
        
        logger.info(f"Registered adapter '{name}' with {len(supported_symbols)} symbols")

    def get_circuit_breaker(self, exchange: str) -> Optional[ExchangeCircuitBreaker]:
        """Get circuit breaker for an exchange."""
        return self._circuit_breakers.get(exchange)

    def get_all_circuit_breaker_metrics(self) -> Dict[str, Dict]:
        """Get metrics for all circuit breakers."""
        return {
            name: cb.get_metrics() 
            for name, cb in self._circuit_breakers.items()
        }

    async def get_best_prices(
        self, 
        symbol: str,
        skip_unhealthy: bool = True,
    ) -> Dict[str, ExchangePricing]:
        """
        Get current prices from all exchanges supporting the symbol.
        
        Args:
            symbol: Trading pair
            skip_unhealthy: If True, skip exchanges with OPEN circuit
        
        Returns:
            Dict of exchange_name -> pricing info
        """
        exchanges = self.symbol_map.get(symbol, list(self.adapters.keys()))
        
        if not exchanges:
            return {}

        async def fetch_price(name: str) -> Tuple[str, Optional[ExchangePricing]]:
            # Check circuit breaker first (ultra-fast in-memory check)
            if skip_unhealthy and self.enable_circuit_breaker:
                cb = self._circuit_breakers.get(name)
                if cb and not cb.can_execute():
                    logger.debug(f"Skipping {name} - circuit is {cb.state.value}")
                    return name, None
            
            try:
                adapter = self.adapters[name]
                ticker = await adapter.get_ticker(symbol)
                
                # Record success for circuit breaker
                if self.enable_circuit_breaker:
                    cb = self._circuit_breakers.get(name)
                    if cb:
                        cb.record_success()
                
                return name, ExchangePricing(
                    exchange=name,
                    bid=ticker.get("bid", 0),
                    ask=ticker.get("ask", 0),
                    available_qty=ticker.get("volume", 0) * 0.01,  # Assume 1% available
                )
            except Exception as e:
                logger.warning(f"Failed to get price from {name}: {e}")
                
                # Record failure for circuit breaker
                if self.enable_circuit_breaker:
                    cb = self._circuit_breakers.get(name)
                    if cb:
                        cb.record_failure()
                
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
        Route order to optimal exchange(s) with circuit breaker protection.
        
        Args:
            order: Order to route
            use_vwap: If True, use VWAP across multiple exchanges
        
        Returns:
            List of OrderResults from each exchange
        """
        quantity = getattr(order, "quantity", None) or getattr(order, "qty", 0)

        if use_vwap and len(self.adapters) > 1:
            # Get prices from all healthy exchanges
            prices = await self.get_best_prices(order.symbol, skip_unhealthy=True)

            if not prices:
                # Try unhealthy exchanges as last resort
                logger.warning("No healthy exchanges, trying all exchanges")
                prices = await self.get_best_prices(order.symbol, skip_unhealthy=False)
                
                if not prices:
                    raise NoRouteFoundError(
                        f"No execution adapter available for symbol: {order.symbol}"
                    )

            # Calculate optimal allocation
            allocations = self.calculate_vwap_routing(quantity, order.side, prices)

            if not allocations:
                raise NoRouteFoundError(f"Could not allocate order for: {order.symbol}")

            # Execute with circuit breaker protection
            async def execute_allocation(alloc: OrderAllocation) -> OrderResult:
                cb = self._circuit_breakers.get(alloc.exchange)
                
                try:
                    adapter = self.adapters[alloc.exchange]
                    child_order = OrderRequest(
                        symbol=order.symbol,
                        side=order.side,
                        order_type=order.order_type,
                        qty=alloc.quantity,
                        limit_price=order.limit_price,
                        stop_price=order.stop_price,
                    )
                    result = await adapter.submit_order(child_order)
                    
                    # Record success
                    if cb:
                        cb.record_success()
                    
                    return result
                    
                except Exception as e:
                    # Record failure
                    if cb:
                        cb.record_failure()
                    raise

            results = await asyncio.gather(
                *[execute_allocation(a) for a in allocations], return_exceptions=True
            )

            # Filter out exceptions
            successful_results = [r for r in results if isinstance(r, OrderResult)]
            
            # Check if we need failover for failed allocations
            failed_exchanges = [
                allocations[i].exchange 
                for i, r in enumerate(results) 
                if isinstance(r, Exception)
            ]
            
            if failed_exchanges:
                logger.warning(f"Failed to execute on exchanges: {failed_exchanges}")
            
            return successful_results

        else:
            # Single exchange routing
            return await self.route_and_execute(order)

    async def route_and_execute(self, order: OrderRequest) -> List[OrderResult]:
        """
        Find best adapter and execute order (single exchange) with failover.
        
        Args:
            order: Order to execute
        
        Returns:
            List with single OrderResult
        """
        # Find adapters that support this symbol, prioritizing healthy ones
        adapter_names = self.symbol_map.get(order.symbol, list(self.adapters.keys()))
        
        # Sort by circuit breaker health (CLOSED first)
        if self.enable_circuit_breaker:
            def health_priority(name: str) -> int:
                cb = self._circuit_breakers.get(name)
                if not cb:
                    return 0
                if cb.state == CircuitBreakerState.CLOSED:
                    return 0
                if cb.state == CircuitBreakerState.HALF_OPEN:
                    return 1
                return 2  # OPEN
            
            adapter_names = sorted(adapter_names, key=health_priority)

        # Try each adapter in order until one succeeds
        last_error = None
        for adapter_name in adapter_names:
            cb = self._circuit_breakers.get(adapter_name)
            
            # Skip if circuit is OPEN (unless it's the last option)
            if cb and cb.state == CircuitBreakerState.OPEN and len(adapter_names) > 1:
                logger.debug(f"Skipping {adapter_name} - circuit OPEN")
                continue
            
            try:
                adapter = self.adapters[adapter_name]
                result = await adapter.submit_order(order)
                
                # Record success
                if cb:
                    cb.record_success()
                
                return [result]
                
            except Exception as e:
                logger.warning(f"Failed to execute on {adapter_name}: {e}")
                last_error = e
                
                # Record failure
                if cb:
                    cb.record_failure()
                
                # Continue to next exchange (failover)
                continue
        
        # All exchanges failed
        raise NoRouteFoundError(
            f"All execution adapters failed for symbol: {order.symbol}. "
            f"Last error: {last_error}"
        )
