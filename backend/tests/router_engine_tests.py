from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest

from backend.core.router_engine import RouterEngine


class TestRouterEngine:
    @pytest.fixture
    def mock_broker_a(self):
        broker = MagicMock()
        broker.exchange_id = "bitvavo"
        broker.fetch_order_book = AsyncMock()
        return broker

    @pytest.fixture
    def mock_broker_b(self):
        broker = MagicMock()
        broker.exchange_id = "revolut"
        broker.fetch_order_book = AsyncMock()
        return broker

    @pytest.mark.asyncio
    async def test_find_best_ask(self, mock_broker_a, mock_broker_b):
        """Should find the lowest ask across multiple brokers."""
        # Broker A: Ask 50000
        mock_broker_a.fetch_order_book.return_value = {
            "asks": [[50000, 1.0]],
            "bids": [[49000, 1.0]],
            "timestamp": int(datetime.now().timestamp() * 1000),
        }
        # Broker B: Ask 49900 (Better)
        mock_broker_b.fetch_order_book.return_value = {
            "asks": [[49900, 1.0]],
            "bids": [[49100, 1.0]],
            "timestamp": int(datetime.now().timestamp() * 1000),
        }

        router = RouterEngine([mock_broker_a, mock_broker_b])
        result = await router.get_best_route("BTC/EUR", side="buy")

        assert result.exchange_id == "revolut"
        assert result.price == 49900
        assert result.normalized_symbol == "BTC/EUR"

    @pytest.mark.asyncio
    async def test_find_best_bid(self, mock_broker_a, mock_broker_b):
        """Should find the highest bid across multiple brokers."""
        # Broker A: Bid 49000
        mock_broker_a.fetch_order_book.return_value = {
            "asks": [[51000, 1.0]],
            "bids": [[49000, 1.0]],
            "timestamp": int(datetime.now().timestamp() * 1000),
        }
        # Broker B: Bid 49500 (Better)
        mock_broker_b.fetch_order_book.return_value = {
            "asks": [[51000, 1.0]],
            "bids": [[49500, 1.0]],
            "timestamp": int(datetime.now().timestamp() * 1000),
        }

        router = RouterEngine([mock_broker_a, mock_broker_b])
        result = await router.get_best_route("BTC/EUR", side="sell")

        assert result.exchange_id == "revolut"
        assert result.price == 49500

    @pytest.mark.asyncio
    async def test_stale_data_handling(self, mock_broker_a, mock_broker_b):
        """Should ignore stale data if beyond threshold."""
        # Broker A: Fresh but expensive
        mock_broker_a.fetch_order_book.return_value = {
            "asks": [[55000, 1.0]],
            "bids": [[54000, 1.0]],
            "timestamp": int(datetime.now().timestamp() * 1000),
        }
        # Broker B: Cheap but 1 hour old (stale)
        stale_ts = int((datetime.now() - timedelta(hours=1)).timestamp() * 1000)
        mock_broker_b.fetch_order_book.return_value = {
            "asks": [[45000, 1.0]],
            "bids": [[44000, 1.0]],
            "timestamp": stale_ts,
        }

        router = RouterEngine([mock_broker_a, mock_broker_b])
        result = await router.get_best_route("BTC/EUR", side="buy")

        # Should pick A because B is stale
        assert result.exchange_id == "bitvavo"
        assert result.price == 55000

    @pytest.mark.asyncio
    async def test_symbol_normalization_per_exchange(self, mock_broker_a, mock_broker_b):
        """Should use correctly normalized symbols for each exchange query."""
        router = RouterEngine([mock_broker_a, mock_broker_b])
        await router.get_best_route("BTC/EUR")

        # Bitvavo uses slash
        mock_broker_a.fetch_order_book.assert_called_with("BTC/EUR")
        # Revolut uses dash
        mock_broker_b.fetch_order_book.assert_called_with("BTC-EUR")
