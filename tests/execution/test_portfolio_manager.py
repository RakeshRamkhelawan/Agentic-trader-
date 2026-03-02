"""
Tests for PortfolioManager.

Week 1 of Exchange Integration Refactor.
"""

import pytest
from decimal import Decimal
from datetime import datetime
from unittest.mock import Mock, AsyncMock

from backend.execution.portfolio_manager import (
    PortfolioManager,
    AssetAllocation,
    PortfolioSnapshot
)


class TestPortfolioManager:
    """Test PortfolioManager functionality."""

    @pytest.fixture
    def pm(self):
        """Create PortfolioManager instance."""
        return PortfolioManager()

    @pytest.fixture
    def mock_adapter(self):
        """Create mock exchange adapter."""
        adapter = Mock()
        adapter.connected = True
        return adapter

    def test_register_adapter(self, pm, mock_adapter):
        """Test registering an adapter."""
        pm.register_adapter("test_exchange", mock_adapter)

        assert "test_exchange" in pm._adapters
        assert pm._adapters["test_exchange"] == mock_adapter

    def test_unregister_adapter(self, pm, mock_adapter):
        """Test unregistering an adapter."""
        pm.register_adapter("test_exchange", mock_adapter)
        pm.unregister_adapter("test_exchange")

        assert "test_exchange" not in pm._adapters

    @pytest.mark.asyncio
    async def test_get_portfolio_empty(self, pm):
        """Test getting portfolio with no adapters."""
        portfolio = await pm.get_portfolio()

        assert portfolio.total_value_usd == Decimal("0")
        assert len(portfolio.assets) == 0
        assert len(portfolio.exchanges) == 0

    @pytest.mark.asyncio
    async def test_get_portfolio_with_mock_data(self, pm, mock_adapter):
        """Test getting portfolio with mock data."""
        # Setup mock balance data
        mock_adapter.fetch_balance = AsyncMock(return_value={
            "EUR": {"total": 1000.0, "free": 900.0, "used": 100.0},
            "BTC": {"total": 0.5, "free": 0.5, "used": 0.0}
        })

        pm.register_adapter("test_exchange", mock_adapter)

        portfolio = await pm.get_portfolio()

        assert "test_exchange" in portfolio.exchanges
        assert "EUR" in portfolio.assets
        assert "BTC" in portfolio.assets

        # Check Decimal conversion
        eur_alloc = portfolio.assets["EUR"]
        assert isinstance(eur_alloc.total, Decimal)
        assert eur_alloc.total == Decimal("1000")
        assert eur_alloc.free == Decimal("900")

    def test_to_decimal_conversion(self, pm):
        """Test _to_decimal helper method."""
        # From Decimal
        assert pm._to_decimal(Decimal("10.5")) == Decimal("10.5")

        # From float
        assert pm._to_decimal(10.5) == Decimal("10.5")

        # From int
        assert pm._to_decimal(10) == Decimal("10")

        # From string
        assert pm._to_decimal("10.5") == Decimal("10.5")

    def test_calculate_cash_ratio(self, pm):
        """Test cash ratio calculation."""
        assets = {
            "EUR": AssetAllocation(
                asset="EUR",
                total=Decimal("1000"),
                free=Decimal("1000"),
                used=Decimal("0"),
                value_usd=Decimal("1000")
            ),
            "BTC": AssetAllocation(
                asset="BTC",
                total=Decimal("0.1"),
                free=Decimal("0.1"),
                used=Decimal("0"),
                value_usd=Decimal("4500")
            )
        }

        total = Decimal("5500")
        ratio = pm._calculate_cash_ratio(assets, total)

        # EUR is cash, BTC is not
        # 1000 / 5500 = ~18.18%
        assert ratio is not None
        assert abs(ratio - Decimal("0.1818")) < Decimal("0.01")

    def test_calculate_max_position(self, pm):
        """Test max position calculation."""
        assets = {
            "BTC": AssetAllocation(
                asset="BTC",
                total=Decimal("0.1"),
                free=Decimal("0.1"),
                used=Decimal("0"),
                allocation_pct=Decimal("0.45")
            ),
            "ETH": AssetAllocation(
                asset="ETH",
                total=Decimal("1.0"),
                free=Decimal("1.0"),
                used=Decimal("0"),
                allocation_pct=Decimal("0.30")
            )
        }

        max_pos = pm._calculate_max_position(assets)

        assert max_pos == Decimal("0.45")  # BTC has largest allocation

    def test_get_allocation_report(self, pm):
        """Test allocation report generation."""
        # Create a snapshot first
        snapshot = PortfolioSnapshot(
            timestamp=datetime.utcnow(),
            total_value_usd=Decimal("10000"),
            assets={
                "BTC": AssetAllocation(
                    asset="BTC",
                    total=Decimal("0.1"),
                    free=Decimal("0.1"),
                    used=Decimal("0"),
                    value_usd=Decimal("4500"),
                    allocation_pct=Decimal("0.45")
                ),
                "EUR": AssetAllocation(
                    asset="EUR",
                    total=Decimal("5500"),
                    free=Decimal("5500"),
                    used=Decimal("0"),
                    value_usd=Decimal("5500"),
                    allocation_pct=Decimal("0.55")
                )
            },
            exchanges=["bitvavo"]
        )
        pm._snapshots.append(snapshot)

        report = pm.get_allocation_report()

        assert "PORTFOLIO ALLOCATION REPORT" in report
        assert "BTC" in report
        assert "EUR" in report
        # Values are formatted with commas (5,500.00)
        assert "5,500" in report or "4,500" in report


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
