"""
Multi-Exchange Portfolio Manager.

Aggregates balances and positions across multiple exchanges,
providing a unified view of the entire portfolio.

Architecture:
    ┌─────────────────────────────────────────────────────────────┐
    │                  PortfolioManager                           │
    │                ─────────────────                            │
    │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
    │  │  Balance    │  │  Position   │  │  Performance│         │
    │  │ Aggregator  │  │  Tracker    │  │  Calculator │         │
    │  └─────────────┘  └─────────────┘  └─────────────┘         │
    └─────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ↓                     ↓                     ↓
   ┌──────────┐        ┌──────────┐        ┌──────────┐
   │ Bitvavo  │        │ Revolut  │        │  Other   │
   │Balances  │        │Balances  │        │Balances  │
   └──────────┘        └──────────┘        └──────────┘
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal

from backend.exchange.base_exchange import BaseExchange, Position, Symbol

logger = logging.getLogger(__name__)


# =============================================================================
# Data Classes
# =============================================================================


@dataclass
class AssetAllocation:
    """Asset allocation across exchanges."""

    asset: str
    total: Decimal
    free: Decimal
    used: Decimal
    by_exchange: dict[str, Decimal] = field(default_factory=dict)
    price_usd: Decimal | None = None
    value_usd: Decimal | None = None
    allocation_pct: Decimal | None = None


@dataclass
class PortfolioSnapshot:
    """Complete portfolio snapshot."""

    timestamp: datetime
    total_value_usd: Decimal
    assets: dict[str, AssetAllocation]
    positions: list[Position]
    exchanges: list[str]

    # Risk metrics
    cash_ratio: Decimal | None = None
    max_position_pct: Decimal | None = None
    concentration_risk: Decimal | None = None


@dataclass
class PerformanceMetrics:
    """Portfolio performance metrics."""

    total_pnl: Decimal
    realized_pnl: Decimal
    unrealized_pnl: Decimal
    roi_pct: Decimal
    sharpe_ratio: Decimal | None = None
    max_drawdown: Decimal | None = None
    win_rate: Decimal | None = None

    # Time-weighted
    daily_return: Decimal | None = None
    weekly_return: Decimal | None = None
    monthly_return: Decimal | None = None


@dataclass
class RebalanceSuggestion:
    """Portfolio rebalance suggestion."""

    asset: str
    current_allocation: Decimal
    target_allocation: Decimal
    suggested_action: str  # "buy", "sell", "hold"
    suggested_amount: Decimal
    reason: str


# =============================================================================
# Portfolio Manager
# =============================================================================


class PortfolioManager:
    """
    Multi-exchange portfolio management.

    Features:
    - Aggregate balances across exchanges
    - Track positions and P&L
    - Calculate performance metrics
    - Rebalance suggestions
    - Risk monitoring

    Example:
        >>> pm = PortfolioManager()
        >>> pm.register_exchange("bitvavo", bitvavo)
        >>> pm.register_exchange("revolut", revolut)
        >>>
        >>> # Get unified portfolio view
        >>> portfolio = await pm.get_portfolio()
        >>> print(f"Total Value: ${portfolio.total_value_usd}")
        >>>
        >>> # Check allocations
        >>> for asset, alloc in portfolio.assets.items():
        ...     print(f"{asset}: {alloc.allocation_pct:.1%}")
    """

    def __init__(self):
        """Initialize portfolio manager."""
        self._exchanges: dict[str, BaseExchange] = {}
        self._price_cache: dict[str, tuple[Decimal, datetime]] = {}
        self._price_cache_ttl = 60  # seconds

        # Target allocations for rebalancing
        self._target_allocations: dict[str, Decimal] = {}

        # Historical snapshots for performance calculation
        self._snapshots: list[PortfolioSnapshot] = []
        self._max_snapshots = 1000

        # Callbacks
        self._update_callbacks: list[Callable[[PortfolioSnapshot], None]] = []

        logger.info("[PortfolioManager] Initialized")

    # -------------------------------------------------------------------------
    # Exchange Management
    # -------------------------------------------------------------------------

    def register_exchange(self, exchange_id: str, exchange: BaseExchange) -> None:
        """Register an exchange for portfolio tracking."""
        self._exchanges[exchange_id] = exchange
        logger.info(f"[PortfolioManager] Registered exchange: {exchange_id}")

    def unregister_exchange(self, exchange_id: str) -> None:
        """Unregister an exchange."""
        if exchange_id in self._exchanges:
            del self._exchanges[exchange_id]
            logger.info(f"[PortfolioManager] Unregistered exchange: {exchange_id}")

    # -------------------------------------------------------------------------
    # Portfolio Aggregation
    # -------------------------------------------------------------------------

    async def get_portfolio(self, include_prices: bool = True) -> PortfolioSnapshot:
        """
        Get complete portfolio snapshot across all exchanges.

        Args:
            include_prices: Whether to fetch current prices for valuation

        Returns:
            Portfolio snapshot
        """
        timestamp = datetime.utcnow()

        # Aggregate balances from all exchanges
        all_balances: dict[str, AssetAllocation] = {}
        all_positions: list[Position] = []

        for exchange_id, exchange in self._exchanges.items():
            if not exchange.connected:
                continue

            try:
                # Get balances
                balances = await exchange.get_all_balances()
                for asset, balance in balances.items():
                    if balance.total == 0:
                        continue

                    if asset not in all_balances:
                        all_balances[asset] = AssetAllocation(
                            asset=asset,
                            total=Decimal("0"),
                            free=Decimal("0"),
                            used=Decimal("0"),
                            by_exchange={},
                        )

                    all_balances[asset].total += balance.total
                    all_balances[asset].free += balance.free
                    all_balances[asset].used += balance.used
                    all_balances[asset].by_exchange[exchange_id] = balance.total

                # Get positions (for margin/futures)
                positions = await exchange.get_positions()
                for pos in positions:
                    pos.exchange_id = exchange_id
                    all_positions.append(pos)

            except Exception as e:
                logger.error(f"[PortfolioManager] Failed to get data from {exchange_id}: {e}")

        # Calculate USD values
        total_value_usd = Decimal("0")

        if include_prices:
            for asset in all_balances:
                price = await self._get_asset_price_usd(asset)
                if price:
                    all_balances[asset].price_usd = price
                    all_balances[asset].value_usd = all_balances[asset].total * price
                    total_value_usd += all_balances[asset].value_usd or 0

        # Calculate allocations
        if total_value_usd > 0:
            for asset in all_balances:
                if all_balances[asset].value_usd:
                    all_balances[asset].allocation_pct = (
                        all_balances[asset].value_usd / total_value_usd
                    )

        # Create snapshot
        snapshot = PortfolioSnapshot(
            timestamp=timestamp,
            total_value_usd=total_value_usd,
            assets=all_balances,
            positions=all_positions,
            exchanges=list(self._exchanges.keys()),
            cash_ratio=self._calculate_cash_ratio(all_balances, total_value_usd),
            max_position_pct=self._calculate_max_position(all_balances),
            concentration_risk=self._calculate_concentration(all_balances),
        )

        # Store snapshot
        self._snapshots.append(snapshot)
        if len(self._snapshots) > self._max_snapshots:
            self._snapshots = self._snapshots[-self._max_snapshots :]

        return snapshot

    async def get_balance(self, asset: str) -> AssetAllocation | None:
        """Get allocation for a specific asset."""
        portfolio = await self.get_portfolio()
        return portfolio.assets.get(asset)

    async def get_total_value_usd(self) -> Decimal:
        """Get total portfolio value in USD."""
        portfolio = await self.get_portfolio()
        return portfolio.total_value_usd

    # -------------------------------------------------------------------------
    # Price Fetching
    # -------------------------------------------------------------------------

    async def _get_asset_price_usd(self, asset: str) -> Decimal | None:
        """
        Get USD price for an asset.

        Tries multiple exchanges and caches results.
        """
        # Check cache
        if asset in self._price_cache:
            price, timestamp = self._price_cache[asset]
            if (datetime.utcnow() - timestamp).seconds < self._price_cache_ttl:
                return price

        # Try each exchange
        for exchange_id, exchange in self._exchanges.items():
            if not exchange.connected:
                continue

            try:
                # Try direct USD pair
                symbol = Symbol(asset, "USD")
                ticker = await exchange.get_ticker(symbol)
                if ticker:
                    self._price_cache[asset] = (ticker.last, datetime.utcnow())
                    return ticker.last
            except Exception:
                pass

            try:
                # Try USDT pair
                symbol = Symbol(asset, "USDT")
                ticker = await exchange.get_ticker(symbol)
                if ticker:
                    self._price_cache[asset] = (ticker.last, datetime.utcnow())
                    return ticker.last
            except Exception:
                pass

            try:
                # Try EUR pair and convert
                symbol = Symbol(asset, "EUR")
                ticker = await exchange.get_ticker(symbol)
                if ticker:
                    # Approximate USD conversion (1 EUR ≈ 1.08 USD)
                    usd_price = ticker.last * Decimal("1.08")
                    self._price_cache[asset] = (usd_price, datetime.utcnow())
                    return usd_price
            except Exception:
                pass

        logger.warning(f"[PortfolioManager] Could not get price for {asset}")
        return None

    # -------------------------------------------------------------------------
    # Performance Calculation
    # -------------------------------------------------------------------------

    def get_performance(self, days: int = 30) -> PerformanceMetrics:
        """
        Calculate portfolio performance metrics.

        Args:
            days: Number of days to calculate performance for

        Returns:
            Performance metrics
        """
        if len(self._snapshots) < 2:
            return PerformanceMetrics(
                total_pnl=Decimal("0"),
                realized_pnl=Decimal("0"),
                unrealized_pnl=Decimal("0"),
                roi_pct=Decimal("0"),
            )

        # Get snapshots from period
        cutoff = datetime.utcnow() - timedelta(days=days)
        period_snapshots = [s for s in self._snapshots if s.timestamp >= cutoff]

        if len(period_snapshots) < 2:
            period_snapshots = self._snapshots[-2:]  # Use last 2 available

        start_value = period_snapshots[0].total_value_usd
        end_value = period_snapshots[-1].total_value_usd

        total_pnl = end_value - start_value
        roi_pct = (total_pnl / start_value * 100) if start_value > 0 else Decimal("0")

        # Calculate returns
        values = [s.total_value_usd for s in period_snapshots]
        returns = [
            (values[i] - values[i - 1]) / values[i - 1]
            for i in range(1, len(values))
            if values[i - 1] > 0
        ]

        # Sharpe ratio (simplified, assuming risk-free rate = 0)
        if returns:
            import statistics

            avg_return = sum(returns) / len(returns)
            try:
                std_return = statistics.stdev(returns)
                sharpe = (avg_return / std_return) if std_return > 0 else None
            except statistics.StatisticsError:
                sharpe = None
        else:
            sharpe = None

        # Max drawdown
        max_dd = self._calculate_max_drawdown(values)

        return PerformanceMetrics(
            total_pnl=total_pnl,
            realized_pnl=Decimal("0"),  # Would need trade history
            unrealized_pnl=total_pnl,
            roi_pct=roi_pct,
            sharpe_ratio=Decimal(str(sharpe)) if sharpe else None,
            max_drawdown=Decimal(str(max_dd)) if max_dd else None,
        )

    # -------------------------------------------------------------------------
    # Rebalancing
    # -------------------------------------------------------------------------

    def set_target_allocation(self, asset: str, target_pct: Decimal) -> None:
        """Set target allocation for an asset."""
        self._target_allocations[asset] = target_pct
        logger.info(f"[PortfolioManager] Target allocation set: {asset} = {target_pct:.1%}")

    def clear_target_allocations(self) -> None:
        """Clear all target allocations."""
        self._target_allocations = {}

    async def get_rebalance_suggestions(self) -> list[RebalanceSuggestion]:
        """
        Get portfolio rebalance suggestions.

        Returns:
            List of rebalance suggestions
        """
        if not self._target_allocations:
            return []

        portfolio = await self.get_portfolio()
        suggestions = []

        total_value = portfolio.total_value_usd
        if total_value == 0:
            return []

        for asset, target_pct in self._target_allocations.items():
            current = portfolio.assets.get(asset)
            current_pct = current.allocation_pct if current else Decimal("0")
            current.value_usd if current else Decimal("0")

            # Calculate difference
            diff_pct = target_pct - current_pct
            diff_value = total_value * diff_pct

            # Determine action
            if abs(diff_pct) < Decimal("0.01"):  # 1% threshold
                action = "hold"
                amount = Decimal("0")
            elif diff_pct > 0:
                action = "buy"
                amount = diff_value / (
                    current.price_usd if current and current.price_usd else Decimal("1")
                )
            else:
                action = "sell"
                amount = abs(diff_value) / (
                    current.price_usd if current and current.price_usd else Decimal("1")
                )

            suggestions.append(
                RebalanceSuggestion(
                    asset=asset,
                    current_allocation=current_pct,
                    target_allocation=target_pct,
                    suggested_action=action,
                    suggested_amount=amount,
                    reason=f"Allocation diff: {diff_pct:.1%}",
                )
            )

        return suggestions

    # -------------------------------------------------------------------------
    # Risk Metrics
    # -------------------------------------------------------------------------

    def _calculate_cash_ratio(
        self, assets: dict[str, AssetAllocation], total_value: Decimal
    ) -> Decimal | None:
        """Calculate cash/stablecoin ratio."""
        if total_value == 0:
            return None

        cash_assets = {"USD", "USDT", "USDC", "EUR", "BUSD"}
        cash_value = sum(
            alloc.value_usd or 0 for asset, alloc in assets.items() if asset in cash_assets
        )

        return cash_value / total_value

    def _calculate_max_position(self, assets: dict[str, AssetAllocation]) -> Decimal | None:
        """Calculate maximum single position percentage."""
        if not assets:
            return None

        max_pct = max((alloc.allocation_pct or 0) for alloc in assets.values())

        return max_pct

    def _calculate_concentration(self, assets: dict[str, AssetAllocation]) -> Decimal | None:
        """Calculate portfolio concentration (Herfindahl index)."""
        if not assets:
            return None

        # Herfindahl-Hirschman Index
        hhi = sum((alloc.allocation_pct or 0) ** 2 for alloc in assets.values())

        return hhi

    def _calculate_max_drawdown(self, values: list[Decimal]) -> float | None:
        """Calculate maximum drawdown from value series."""
        if len(values) < 2:
            return None

        peak = values[0]
        max_dd = Decimal("0")

        for value in values:
            if value > peak:
                peak = value

            drawdown = (peak - value) / peak if peak > 0 else Decimal("0")
            if drawdown > max_dd:
                max_dd = drawdown

        return float(max_dd)

    # -------------------------------------------------------------------------
    # Event Handling
    # -------------------------------------------------------------------------

    def register_update_callback(self, callback: Callable[[PortfolioSnapshot], None]) -> None:
        """Register callback for portfolio updates."""
        self._update_callbacks.append(callback)

    async def notify_update(self) -> None:
        """Notify all callbacks of portfolio update."""
        portfolio = await self.get_portfolio()

        for callback in self._update_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(portfolio)
                else:
                    callback(portfolio)
            except Exception as e:
                logger.error(f"[PortfolioManager] Callback error: {e}")

    # -------------------------------------------------------------------------
    # Reporting
    # -------------------------------------------------------------------------

    def get_allocation_report(self) -> str:
        """Generate allocation report string."""
        if not self._snapshots:
            return "No portfolio data available"

        latest = self._snapshots[-1]

        lines = [
            "=" * 60,
            "PORTFOLIO ALLOCATION REPORT",
            f"Generated: {latest.timestamp.strftime('%Y-%m-%d %H:%M:%S')} UTC",
            "=" * 60,
            f"\nTotal Value: ${latest.total_value_usd:,.2f}",
            f"Exchanges: {', '.join(latest.exchanges)}",
            "\nAsset Allocation:",
            "-" * 60,
        ]

        # Sort by allocation
        sorted_assets = sorted(
            latest.assets.items(), key=lambda x: x[1].allocation_pct or 0, reverse=True
        )

        for asset, alloc in sorted_assets:
            pct = alloc.allocation_pct or Decimal("0")
            value = alloc.value_usd or Decimal("0")
            bar_length = int(pct * 50)  # 50 chars = 100%
            bar = "█" * bar_length + "░" * (50 - bar_length)
            lines.append(f"{asset:6} │{bar}│ {pct:>6.1%} (${value:>10,.2f})")

        lines.extend(
            [
                "-" * 60,
                f"Cash Ratio: {latest.cash_ratio:.1%}" if latest.cash_ratio else "Cash Ratio: N/A",
                (
                    f"Max Position: {latest.max_position_pct:.1%}"
                    if latest.max_position_pct
                    else "Max Position: N/A"
                ),
                "=" * 60,
            ]
        )

        return "\n".join(lines)

    def __repr__(self) -> str:
        return (
            f"PortfolioManager(exchanges={len(self._exchanges)}, snapshots={len(self._snapshots)})"
        )


# Import needed for calculations
from datetime import timedelta
