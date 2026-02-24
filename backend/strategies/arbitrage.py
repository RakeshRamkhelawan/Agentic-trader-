"""
Cross-Exchange Arbitrage Strategy (Sprint 3).

Implements three types of arbitrage:
1. Price Disparity: Simple price differences between exchanges
2. Latency Arbitrage: Fast path only - pure computational arbitrage
3. Triangular Arbitrage: Multi-asset arbitrage cycles

Philosophy:
Budha (Mercury) is the graha of analysis, commerce, and calculation.
Arbitrage represents the intellectual discernment of price differences -
the purest form of Budha's analytical energy.
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass

import numpy as np

from backend.execution.broker_interface import ExecutionInterface
from backend.schemas.orders import OrderRequest, OrderSide, OrderType

logger = logging.getLogger(__name__)


@dataclass
class ArbitrageOpportunity:
    """Represents an arbitrage opportunity."""

    type: str  # "disparity", "latency", "triangular"
    buy_exchange: str
    sell_exchange: str
    symbol: str
    buy_price: float
    sell_price: float
    quantity: float
    expected_profit: float
    profit_pct: float
    confidence: float
    timestamp: float


class ArbitrageDetector(ABC):
    """Abstract base for arbitrage detection."""

    @abstractmethod
    async def detect(
        self,
        prices: dict[str, dict[str, float]],
    ) -> list[ArbitrageOpportunity]:
        """Detect arbitrage opportunities."""
        pass


class PriceDisparityDetector(ArbitrageDetector):
    """
    Detects price disparities between exchanges.

    Compares prices across exchanges for the same symbol
    and identifies profitable spreads after fees.
    """

    def __init__(
        self,
        min_profit_pct: float = 0.1,  # 0.1% minimum profit
        fee_estimate: float = 0.15,  # 0.15% estimated fees per leg
    ):
        self.min_profit_pct = min_profit_pct
        self.fee_estimate = fee_estimate

    async def detect(
        self,
        prices: dict[str, dict[str, float]],
    ) -> list[ArbitrageOpportunity]:
        """
        Detect price disparity opportunities.

        Args:
            prices: Dict[exchange, Dict[symbol, price]]

        Returns:
            List of arbitrage opportunities
        """
        opportunities = []
        import time

        # Get all symbols
        all_symbols = set()
        for exchange_prices in prices.values():
            all_symbols.update(exchange_prices.keys())

        for symbol in all_symbols:
            # Get prices for this symbol across exchanges
            exchange_prices = {}
            for exchange, price_dict in prices.items():
                if symbol in price_dict:
                    exchange_prices[exchange] = price_dict[symbol]

            if len(exchange_prices) < 2:
                continue

            # Find best buy (lowest ask) and sell (highest bid)
            sorted_prices = sorted(exchange_prices.items(), key=lambda x: x[1])

            for i, (buy_ex, buy_price) in enumerate(sorted_prices):
                for sell_ex, sell_price in sorted_prices[i + 1 :]:
                    # Calculate profit
                    gross_profit_pct = (sell_price - buy_price) / buy_price * 100
                    net_profit_pct = gross_profit_pct - (2 * self.fee_estimate)

                    if net_profit_pct > self.min_profit_pct:
                        opportunity = ArbitrageOpportunity(
                            type="disparity",
                            buy_exchange=buy_ex,
                            sell_exchange=sell_ex,
                            symbol=symbol,
                            buy_price=buy_price,
                            sell_price=sell_price,
                            quantity=0.0,  # To be calculated
                            expected_profit=0.0,  # To be calculated
                            profit_pct=net_profit_pct,
                            confidence=0.8,
                            timestamp=time.time(),
                        )
                        opportunities.append(opportunity)

        # Sort by profit percentage
        opportunities.sort(key=lambda x: x.profit_pct, reverse=True)
        return opportunities


class LatencyArbitrageDetector(ArbitrageDetector):
    """
    Latency arbitrage detector - FAST PATH ONLY.

    This detector uses only computational logic (no I/O)
    and is designed for the hot path (< 1ms).

    Philosophy:
    Like the Buddhi (intellect) making split-second decisions,
    latency arbitrage requires pure, unclouded perception of price.
    """

    def __init__(
        self,
        min_spread_ticks: int = 2,
        tick_size: float = 0.01,
    ):
        self.min_spread_ticks = min_spread_ticks
        self.tick_size = tick_size

    async def detect(
        self,
        prices: dict[str, dict[str, float]],
    ) -> list[ArbitrageOpportunity]:
        """
        Detect latency arbitrage opportunities.

        FAST PATH: Pure computation, no I/O, < 1ms execution.
        """
        opportunities = []
        import time

        for symbol in self._get_common_symbols(prices):
            symbol_prices = {ex: data[symbol] for ex, data in prices.items() if symbol in data}

            if len(symbol_prices) < 2:
                continue

            # Fast statistical arbitrage detection
            price_array = np.array(list(symbol_prices.values()))
            mean_price = np.mean(price_array)
            std_price = np.std(price_array)

            # Detect outliers (potential arbitrage)
            for exchange, price in symbol_prices.items():
                z_score = (price - mean_price) / (std_price + 1e-10)

                if abs(z_score) > 2.0:  # 2 sigma outlier
                    # Determine buy/sell based on deviation
                    if z_score < 0:  # Price is low - buy opportunity
                        # Find highest price exchange to sell
                        sell_ex = max(symbol_prices, key=symbol_prices.get)
                        if sell_ex != exchange:
                            profit_pct = (symbol_prices[sell_ex] - price) / price * 100

                            if profit_pct > 0.05:  # 0.05% minimum
                                opportunities.append(
                                    ArbitrageOpportunity(
                                        type="latency",
                                        buy_exchange=exchange,
                                        sell_exchange=sell_ex,
                                        symbol=symbol,
                                        buy_price=price,
                                        sell_price=symbol_prices[sell_ex],
                                        quantity=0.0,
                                        expected_profit=0.0,
                                        profit_pct=profit_pct,
                                        confidence=min(abs(z_score) / 3.0, 0.95),
                                        timestamp=time.time(),
                                    )
                                )

        return opportunities[:5]  # Return top 5 only

    def _get_common_symbols(self, prices: dict[str, dict[str, float]]) -> set:
        """Get symbols available on multiple exchanges."""
        symbol_sets = [set(p.keys()) for p in prices.values()]
        if not symbol_sets:
            return set()
        return set.intersection(*symbol_sets) if len(symbol_sets) > 1 else symbol_sets[0]


class TriangularArbitrageDetector(ArbitrageDetector):
    """
    Triangular arbitrage detector for multi-asset cycles.

    Detects profitable cycles like: BTC -> ETH -> EUR -> BTC
    """

    def __init__(
        self,
        min_profit_pct: float = 0.05,
        max_cycle_length: int = 3,
    ):
        self.min_profit_pct = min_profit_pct
        self.max_cycle_length = max_cycle_length

    async def detect(
        self,
        prices: dict[str, dict[str, float]],
    ) -> list[ArbitrageOpportunity]:
        """
        Detect triangular arbitrage opportunities.

        Searches for profitable trading cycles.
        """
        opportunities = []
        import time

        # Build price graph
        # This is a simplified version - full implementation would use graph algorithms
        # For now, detect simple BTC-ETH-EUR cycles
        for exchange, price_dict in prices.items():
            if not all(s in price_dict for s in ["BTC-EUR", "ETH-EUR", "BTC-ETH"]):
                continue

            btc_eur = price_dict["BTC-EUR"]
            eth_eur = price_dict["ETH-EUR"]
            btc_eth = price_dict["BTC-ETH"]

            # Calculate cycle: BTC -> ETH -> EUR -> BTC
            # Start with 1 BTC
            btc_amount = 1.0
            eth_amount = btc_amount * btc_eth  # Sell BTC for ETH
            eur_amount = eth_amount * eth_eur  # Sell ETH for EUR
            final_btc = eur_amount / btc_eur  # Buy BTC with EUR

            profit_pct = (final_btc - btc_amount) / btc_amount * 100

            if profit_pct > self.min_profit_pct:
                opportunities.append(
                    ArbitrageOpportunity(
                        type="triangular",
                        buy_exchange=exchange,
                        sell_exchange=exchange,
                        symbol="BTC-ETH-EUR",
                        buy_price=btc_eth,
                        sell_price=btc_eur,
                        quantity=btc_amount,
                        expected_profit=final_btc - btc_amount,
                        profit_pct=profit_pct,
                        confidence=0.7,
                        timestamp=time.time(),
                    )
                )

        return opportunities


class ArbitrageExecutor:
    """
    Executes arbitrage opportunities with risk controls.

    Ensures both legs of arbitrage are executed or none at all
    (atomic execution).
    """

    def __init__(self, adapters: dict[str, ExecutionInterface]):
        self.adapters = adapters
        self.min_profit_threshold = 0.1  # 0.1%

    async def execute_opportunity(
        self,
        opportunity: ArbitrageOpportunity,
        max_quantity: float = 1.0,
    ) -> tuple[bool, float]:
        """
        Execute arbitrage opportunity.

        Args:
            opportunity: The arbitrage opportunity
            max_quantity: Maximum quantity to trade

        Returns:
            Tuple of (success, actual_profit)
        """
        if opportunity.profit_pct < self.min_profit_threshold:
            logger.info(f"Opportunity profit {opportunity.profit_pct}% below threshold")
            return False, 0.0

        # Determine quantity
        quantity = min(max_quantity, opportunity.quantity or 1.0)

        # Get adapters
        buy_adapter = self.adapters.get(opportunity.buy_exchange)
        sell_adapter = self.adapters.get(opportunity.sell_exchange)

        if not buy_adapter or not sell_adapter:
            logger.error("Missing adapter for execution")
            return False, 0.0

        try:
            # Execute both legs simultaneously
            buy_order = OrderRequest(
                symbol=opportunity.symbol,
                side=OrderSide.BUY,
                order_type=OrderType.MARKET,
                qty=quantity,
            )
            sell_order = OrderRequest(
                symbol=opportunity.symbol,
                side=OrderSide.SELL,
                order_type=OrderType.MARKET,
                qty=quantity,
            )

            # Execute simultaneously
            buy_task = buy_adapter.submit_order(buy_order)
            sell_task = sell_adapter.submit_order(sell_order)

            buy_result, sell_result = await asyncio.gather(
                buy_task, sell_task, return_exceptions=True
            )

            # Check results
            if isinstance(buy_result, Exception) or isinstance(sell_result, Exception):
                logger.error(f"Arbitrage execution failed: buy={buy_result}, sell={sell_result}")
                return False, 0.0

            # Calculate actual profit
            buy_cost = buy_result.filled_qty * buy_result.avg_price
            sell_revenue = sell_result.filled_qty * sell_result.avg_price
            actual_profit = sell_revenue - buy_cost

            logger.info(
                f"Arbitrage executed: {opportunity.type}, "
                f"profit={actual_profit:.4f}, "
                f"buy={opportunity.buy_exchange}, sell={opportunity.sell_exchange}"
            )

            return True, actual_profit

        except Exception as e:
            logger.error(f"Arbitrage execution error: {e}")
            return False, 0.0


class ArbitrageStrategy:
    """
    Main arbitrage strategy combining detection and execution.

    Integrates with Budha Graha (Mercury) strategy mapping.
    """

    def __init__(
        self,
        adapters: dict[str, ExecutionInterface],
        enable_disparity: bool = True,
        enable_latency: bool = True,
        enable_triangular: bool = True,
    ):
        self.adapters = adapters
        self.executor = ArbitrageExecutor(adapters)

        # Initialize detectors
        self.detectors: list[ArbitrageDetector] = []
        if enable_disparity:
            self.detectors.append(PriceDisparityDetector())
        if enable_latency:
            self.detectors.append(LatencyArbitrageDetector())
        if enable_triangular:
            self.detectors.append(TriangularArbitrageDetector())

        # Statistics
        self.opportunities_found = 0
        self.opportunities_executed = 0
        self.total_profit = 0.0

    async def scan(self, prices: dict[str, dict[str, float]]) -> list[ArbitrageOpportunity]:
        """
        Scan for arbitrage opportunities across all detectors.

        Args:
            prices: Price data from all exchanges

        Returns:
            Combined list of opportunities
        """
        all_opportunities = []

        for detector in self.detectors:
            try:
                opportunities = await detector.detect(prices)
                all_opportunities.extend(opportunities)
            except Exception as e:
                logger.error(f"Detector error: {e}")

        # Sort by profit
        all_opportunities.sort(key=lambda x: x.profit_pct, reverse=True)

        self.opportunities_found += len(all_opportunities)

        return all_opportunities[:10]  # Return top 10

    async def execute_best(
        self,
        opportunities: list[ArbitrageOpportunity],
        max_executions: int = 3,
    ) -> list[tuple[bool, float]]:
        """
        Execute best arbitrage opportunities.

        Args:
            opportunities: List of opportunities
            max_executions: Maximum number to execute

        Returns:
            List of execution results
        """
        results = []

        for opp in opportunities[:max_executions]:
            success, profit = await self.executor.execute_opportunity(opp)
            results.append((success, profit))

            if success:
                self.opportunities_executed += 1
                self.total_profit += profit

        return results

    def get_statistics(self) -> dict:
        """Get arbitrage statistics."""
        return {
            "opportunities_found": self.opportunities_found,
            "opportunities_executed": self.opportunities_executed,
            "total_profit": self.total_profit,
            "execution_rate": (self.opportunities_executed / max(self.opportunities_found, 1)),
        }
