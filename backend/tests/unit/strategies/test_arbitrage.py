"""
Unit tests for Arbitrage Strategy (Sprint 3).
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from backend.strategies.arbitrage import (
    ArbitrageOpportunity,
    PriceDisparityDetector,
    LatencyArbitrageDetector,
    ArbitrageExecutor,
    ArbitrageStrategy,
)


@pytest.fixture
def sample_prices():
    """Sample price data from multiple exchanges."""
    return {
        "bitvavo": {
            "BTC-EUR": 50000.0,
            "ETH-EUR": 3000.0,
            "BTC-ETH": 16.67,
        },
        "kraken": {
            "BTC-EUR": 50100.0,  # Higher price
            "ETH-EUR": 3005.0,
            "BTC-ETH": 16.65,
        },
        "binance": {
            "BTC-EUR": 49950.0,  # Lower price
            "ETH-EUR": 2998.0,
            "BTC-ETH": 16.68,
        },
    }


@pytest.fixture
def mock_adapters():
    """Mock execution adapters."""
    return {
        "bitvavo": AsyncMock(),
        "kraken": AsyncMock(),
        "binance": AsyncMock(),
    }


class TestPriceDisparityDetector:
    """Test cases for price disparity detection."""

    @pytest.mark.asyncio
    async def test_detect_opportunity(self, sample_prices):
        """Test detecting price disparity."""
        # Use very low profit threshold and fees to detect opportunities
        detector = PriceDisparityDetector(min_profit_pct=0.05, fee_estimate=0.0)

        opportunities = await detector.detect(sample_prices)

        assert len(opportunities) > 0

        # Check first opportunity
        opp = opportunities[0]
        assert opp.type == "disparity"
        assert opp.buy_price < opp.sell_price
        assert opp.profit_pct > 0.05

    @pytest.mark.asyncio
    async def test_no_opportunity_when_prices_aligned(self):
        """Test no opportunity when prices are similar."""
        prices = {
            "ex1": {"BTC": 50000.0},
            "ex2": {"BTC": 50001.0},  # Only 0.002% difference
        }

        detector = PriceDisparityDetector(min_profit_pct=0.1)
        opportunities = await detector.detect(prices)

        assert len(opportunities) == 0


class TestLatencyArbitrageDetector:
    """Test cases for latency arbitrage detection."""

    @pytest.mark.asyncio
    async def test_detect_statistical_outlier(self):
        """Test detecting statistical outliers."""
        detector = LatencyArbitrageDetector()

        # Prices with extreme outlier (>10% difference, many samples for low std)
        prices = {
            "ex1": {"BTC": 50000.0},
            "ex2": {"BTC": 50000.0},
            "ex3": {"BTC": 50000.0},
            "ex4": {"BTC": 50000.0},
            "ex5": {"BTC": 50000.0},
            "ex6": {"BTC": 50000.0},
            "ex7": {"BTC": 50000.0},
            "ex8": {"BTC": 44000.0},  # 12% outlier
        }

        opportunities = await detector.detect(prices)

        # Should detect opportunity involving the outlier
        assert len(opportunities) > 0

        # Verify opportunity properties
        opp = opportunities[0]
        assert opp.type == "latency"
        assert opp.buy_exchange == "ex8"  # Should buy at the low price
        assert opp.profit_pct > 0.05  # At least 0.05% profit


class TestArbitrageExecutor:
    """Test cases for arbitrage execution."""

    @pytest.mark.asyncio
    async def test_execute_opportunity(self, mock_adapters):
        """Test executing arbitrage opportunity."""
        executor = ArbitrageExecutor(mock_adapters)

        opportunity = ArbitrageOpportunity(
            type="disparity",
            buy_exchange="binance",
            sell_exchange="kraken",
            symbol="BTC-EUR",
            buy_price=49950.0,
            sell_price=50100.0,
            quantity=1.0,
            expected_profit=150.0,
            profit_pct=0.3,
            confidence=0.8,
            timestamp=0.0,
        )

        # Mock successful execution - use proper OrderSide enum
        mock_result_binance = MagicMock()
        mock_result_binance.filled_qty = 1.0
        mock_result_binance.avg_price = 49950.0
        mock_adapters["binance"].submit_order = AsyncMock(return_value=mock_result_binance)

        mock_result_kraken = MagicMock()
        mock_result_kraken.filled_qty = 1.0
        mock_result_kraken.avg_price = 50100.0
        mock_adapters["kraken"].submit_order = AsyncMock(return_value=mock_result_kraken)

        success, profit = await executor.execute_opportunity(opportunity)

        assert success is True
        assert profit > 0


class TestArbitrageStrategy:
    """Test cases for main arbitrage strategy."""

    @pytest.mark.asyncio
    async def test_scan_opportunities(self, mock_adapters, sample_prices):
        """Test scanning for opportunities."""
        strategy = ArbitrageStrategy(mock_adapters)

        opportunities = await strategy.scan(sample_prices)

        assert isinstance(opportunities, list)

    def test_get_statistics(self, mock_adapters):
        """Test getting statistics."""
        strategy = ArbitrageStrategy(mock_adapters)

        # Manually set some stats
        strategy.opportunities_found = 100
        strategy.opportunities_executed = 50
        strategy.total_profit = 500.0

        stats = strategy.get_statistics()

        assert stats["opportunities_found"] == 100
        assert stats["opportunities_executed"] == 50
        assert stats["total_profit"] == 500.0
        assert stats["execution_rate"] == 0.5
