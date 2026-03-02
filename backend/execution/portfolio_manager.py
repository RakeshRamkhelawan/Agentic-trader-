"""
Multi-Exchange Portfolio Manager.

Aggregates balances and positions across multiple exchanges.
Refactored from exchange/ to execution/ folder (Week 1).

Changes from original:
- Uses Decimal for all financial values
- Integrates with existing adapters (BitvavoAdapter, RevolutXAdapter)
- Converts to OODA PortfolioState for agent compatibility
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Any

# OODA integration
from backend.core.schemas.ooda_types import PortfolioState

logger = logging.getLogger(__name__)


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

    @property
    def is_cash(self) -> bool:
        """Check if asset is a stablecoin/fiat."""
        cash_assets = {"USD", "USDT", "USDC", "EUR", "BUSD", "DAI"}
        return self.asset in cash_assets


@dataclass
class PortfolioSnapshot:
    """Complete portfolio snapshot."""
    timestamp: datetime
    total_value_usd: Decimal
    assets: dict[str, AssetAllocation]
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

    # Time-weighted returns
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


class PortfolioManager:
    """
    Multi-exchange portfolio manager.

    Aggregates balances from multiple exchange adapters.
    Provides unified view of entire portfolio.

    Example:
        >>> pm = PortfolioManager()
        >>> pm.register_adapter("bitvavo", bitvavo_adapter)
        >>> pm.register_adapter("revolut", revolut_adapter)
        >>> portfolio = await pm.get_portfolio()
        >>> print(f"Total: ${portfolio.total_value_usd}")
    """

    def __init__(self):
        """Initialize portfolio manager."""
        self._adapters: dict[str, Any] = {}
        self._price_cache: dict[str, tuple[Decimal, datetime]] = {}
        self._price_cache_ttl = 60  # seconds

        # Target allocations for rebalancing
        self._target_allocations: dict[str, Decimal] = {}

        # Historical snapshots for performance
        self._snapshots: list[PortfolioSnapshot] = []
        self._max_snapshots = 1000

        # Callbacks
        self._update_callbacks: list[Callable[[PortfolioSnapshot], None]] = []

        logger.info("[PortfolioManager] Initialized")

    def register_adapter(self, name: str, adapter: Any) -> None:
        """
        Register an exchange adapter.

        Args:
            name: Exchange identifier (e.g., "bitvavo")
            adapter: Exchange adapter instance
        """
        self._adapters[name] = adapter
        logger.info(f"[PortfolioManager] Registered adapter: {name}")

    def unregister_adapter(self, name: str) -> None:
        """Unregister an adapter."""
        if name in self._adapters:
            del self._adapters[name]
            logger.info(f"[PortfolioManager] Unregistered adapter: {name}")

    async def get_portfolio(self, include_prices: bool = True) -> PortfolioSnapshot:
        """
        Get complete portfolio snapshot across all exchanges.

        Args:
            include_prices: Whether to fetch current prices for valuation

        Returns:
            PortfolioSnapshot with aggregated data
        """
        timestamp = datetime.utcnow()

        # Aggregate balances from all adapters
        all_balances: dict[str, AssetAllocation] = {}

        for exchange_id, adapter in self._adapters.items():
            # Check if adapter is connected
            is_connected = False
            if hasattr(adapter, 'connected'):
                is_connected = adapter.connected
            elif hasattr(adapter, '_connected'):
                is_connected = adapter._connected
            elif hasattr(adapter, 'exchange'):
                is_connected = adapter.exchange is not None

            if not is_connected:
                logger.debug(f"[PortfolioManager] Adapter {exchange_id} not connected, skipping")
                continue

            try:
                # Get balances from adapter
                balances = await self._get_adapter_balances(adapter)

                for asset, balance_data in balances.items():
                    if asset not in all_balances:
                        all_balances[asset] = AssetAllocation(
                            asset=asset,
                            total=Decimal("0"),
                            free=Decimal("0"),
                            used=Decimal("0"),
                            by_exchange={}
                        )

                    # Update balances
                    all_balances[asset].total += balance_data.get('total', Decimal("0"))
                    all_balances[asset].free += balance_data.get('free', Decimal("0"))
                    all_balances[asset].used += balance_data.get('used', Decimal("0"))
                    all_balances[asset].by_exchange[exchange_id] = balance_data.get('total', Decimal("0"))

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
                    total_value_usd += all_balances[asset].value_usd or Decimal("0")

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
            exchanges=list(self._adapters.keys()),
            cash_ratio=self._calculate_cash_ratio(all_balances, total_value_usd),
            max_position_pct=self._calculate_max_position(all_balances),
            concentration_risk=self._calculate_concentration(all_balances)
        )

        # Store snapshot
        self._snapshots.append(snapshot)
        if len(self._snapshots) > self._max_snapshots:
            self._snapshots = self._snapshots[-self._max_snapshots:]

        return snapshot

    async def _get_adapter_balances(self, adapter: Any) -> dict[str, dict[str, Decimal]]:
        """
        Get balances from an adapter and normalize to Decimal.

        Args:
            adapter: Exchange adapter

        Returns:
            Dict of asset -> {total, free, used}
        """
        balances = {}

        try:
            # Try different balance methods
            if hasattr(adapter, 'fetch_balance'):
                raw_balances = await adapter.fetch_balance()
            elif hasattr(adapter, 'get_balance'):
                raw_balances = await adapter.get_balance()
            else:
                logger.warning("[PortfolioManager] Adapter has no balance method")
                return balances

            # Normalize to Decimal
            for asset, data in raw_balances.items():
                if isinstance(data, dict):
                    total = self._to_decimal(data.get('total', 0))
                    free = self._to_decimal(data.get('free', 0))
                    used = self._to_decimal(data.get('used', 0))

                    if total > 0 or asset in ['EUR', 'USD', 'USDT', 'BTC', 'ETH']:
                        balances[asset] = {
                            'total': total,
                            'free': free,
                            'used': used
                        }
                else:
                    # Simple balance format
                    total = self._to_decimal(data)
                    if total > 0:
                        balances[asset] = {
                            'total': total,
                            'free': total,
                            'used': Decimal('0')
                        }

        except Exception as e:
            logger.error(f"[PortfolioManager] Error fetching balances: {e}")

        return balances

    def _to_decimal(self, value: Any) -> Decimal:
        """Convert value to Decimal safely."""
        if isinstance(value, Decimal):
            return value
        if isinstance(value, (int, float)):
            return Decimal(str(value))
        if isinstance(value, str):
            return Decimal(value)
        return Decimal('0')

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

        # Try each adapter
        for exchange_id, adapter in self._adapters.items():
            if not hasattr(adapter, 'fetch_ticker'):
                continue

            try:
                # Try direct USD pair
                ticker = await adapter.fetch_ticker(f"{asset}/USD")
                if ticker and 'last' in ticker:
                    price = self._to_decimal(ticker['last'])
                    self._price_cache[asset] = (price, datetime.utcnow())
                    return price
            except Exception:
                pass

            try:
                # Try USDT pair
                ticker = await adapter.fetch_ticker(f"{asset}/USDT")
                if ticker and 'last' in ticker:
                    price = self._to_decimal(ticker['last'])
                    self._price_cache[asset] = (price, datetime.utcnow())
                    return price
            except Exception:
                pass

            try:
                # Try EUR pair and convert
                ticker = await adapter.fetch_ticker(f"{asset}/EUR")
                if ticker and 'last' in ticker:
                    # Approximate USD conversion (1 EUR ≈ 1.08 USD)
                    price_eur = self._to_decimal(ticker['last'])
                    price = price_eur * Decimal("1.08")
                    self._price_cache[asset] = (price, datetime.utcnow())
                    return price
            except Exception:
                pass

        logger.warning(f"[PortfolioManager] Could not get price for {asset}")
        return None

    async def get_portfolio_state(self) -> PortfolioState:
        """
        Convert to OODA PortfolioState.

        Returns:
            PortfolioState compatible with FundManagerAgent
        """
        snapshot = await self.get_portfolio()

        return PortfolioState(
            total_equity=float(snapshot.total_value_usd),  # Convert for OODA compat
            available_capital=float(self._get_free_capital(snapshot)),
            total_exposure_pct=float(self._calculate_exposure(snapshot)),
            num_open_positions=len([a for a in snapshot.assets.values() if a.total > 0]),
            timestamp=datetime.utcnow().timestamp()
        )

    def _get_free_capital(self, snapshot: PortfolioSnapshot) -> Decimal:
        """Calculate free capital (cash not in positions)."""
        cash_assets = {"USD", "USDT", "USDC", "EUR", "BUSD"}
        free = Decimal("0")

        for asset, alloc in snapshot.assets.items():
            if asset in cash_assets:
                free += alloc.free

        return free

    def _calculate_exposure(self, snapshot: PortfolioSnapshot) -> Decimal:
        """Calculate total exposure percentage."""
        if snapshot.total_value_usd == 0:
            return Decimal("0")

        non_cash_value = Decimal("0")
        cash_assets = {"USD", "USDT", "USDC", "EUR", "BUSD"}

        for asset, alloc in snapshot.assets.items():
            if asset not in cash_assets and alloc.value_usd:
                non_cash_value += alloc.value_usd

        return non_cash_value / snapshot.total_value_usd

    def _calculate_cash_ratio(
        self,
        assets: dict[str, AssetAllocation],
        total_value: Decimal
    ) -> Decimal | None:
        """Calculate cash/stablecoin ratio."""
        if total_value == 0:
            return None

        cash_assets = {"USD", "USDT", "USDC", "EUR", "BUSD", "DAI"}
        cash_value = sum(
            alloc.value_usd or Decimal("0")
            for asset, alloc in assets.items()
            if asset in cash_assets
        )

        return cash_value / total_value

    def _calculate_max_position(
        self,
        assets: dict[str, AssetAllocation]
    ) -> Decimal | None:
        """Calculate maximum single position percentage."""
        if not assets:
            return None

        max_pct = max(
            (alloc.allocation_pct or Decimal("0"))
            for alloc in assets.values()
        )

        return max_pct

    def _calculate_concentration(
        self,
        assets: dict[str, AssetAllocation]
    ) -> Decimal | None:
        """Calculate portfolio concentration (Herfindahl index)."""
        if not assets:
            return None

        # Herfindahl-Hirschman Index
        hhi = sum(
            (alloc.allocation_pct or Decimal("0")) ** 2
            for alloc in assets.values()
        )

        return hhi

    def set_target_allocation(self, asset: str, target_pct: Decimal) -> None:
        """Set target allocation for an asset."""
        self._target_allocations[asset] = target_pct
        logger.info(f"[PortfolioManager] Target allocation: {asset} = {target_pct:.1%}")

    async def get_rebalance_suggestions(self) -> list[RebalanceSuggestion]:
        """Get portfolio rebalance suggestions."""
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
            current_value = current.value_usd if current else Decimal("0")

            # Calculate difference
            diff_pct = target_pct - current_pct
            diff_value = total_value * diff_pct

            # Determine action
            if abs(diff_pct) < Decimal("0.01"):  # 1% threshold
                action = "hold"
                amount = Decimal("0")
            elif diff_pct > 0:
                action = "buy"
                price = current.price_usd if current and current.price_usd else Decimal("1")
                amount = diff_value / price
            else:
                action = "sell"
                price = current.price_usd if current and current.price_usd else Decimal("1")
                amount = abs(diff_value) / price

            suggestions.append(RebalanceSuggestion(
                asset=asset,
                current_allocation=current_pct,
                target_allocation=target_pct,
                suggested_action=action,
                suggested_amount=amount,
                reason=f"Allocation diff: {diff_pct:.1%}"
            ))

        return suggestions

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
            "-" * 60
        ]

        # Sort by allocation
        sorted_assets = sorted(
            latest.assets.items(),
            key=lambda x: x[1].allocation_pct or Decimal("0"),
            reverse=True
        )

        for asset, alloc in sorted_assets:
            pct = alloc.allocation_pct or Decimal("0")
            value = alloc.value_usd or Decimal("0")
            bar_length = int(float(pct) * 50)  # 50 chars = 100%
            bar = "█" * bar_length + "░" * (50 - bar_length)
            lines.append(f"{asset:6} │{bar}│ {float(pct):>6.1%} (${float(value):>10,.2f})")

        lines.extend([
            "-" * 60,
            f"Cash Ratio: {float(latest.cash_ratio):.1%}" if latest.cash_ratio else "Cash Ratio: N/A",
            f"Max Position: {float(latest.max_position_pct):.1%}" if latest.max_position_pct else "Max Position: N/A",
            "=" * 60
        ])

        return "\n".join(lines)


# Singleton instance
_portfolio_manager: PortfolioManager | None = None


def get_portfolio_manager() -> PortfolioManager:
    """Get or create global portfolio manager."""
    global _portfolio_manager
    if _portfolio_manager is None:
        _portfolio_manager = PortfolioManager()
    return _portfolio_manager
