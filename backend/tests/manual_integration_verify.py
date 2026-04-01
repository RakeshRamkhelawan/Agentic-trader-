import asyncio
import logging
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

from backend.core.router_engine import RouterEngine

# Configure logging to stdout
logging.basicConfig(level=logging.INFO)


async def run_integration_manual():
    print("--- Starting Manual Integration Verification ---")

    # Setup mocks
    mock_a = MagicMock()
    mock_a.exchange_id = "bitvavo"
    mock_a.fetch_order_book = AsyncMock(
        return_value={
            "asks": [[50000.0, 1.0]],
            "bids": [[49000.0, 1.0]],
            "timestamp": int(datetime.now().timestamp() * 1000),
        }
    )

    mock_b = MagicMock()
    mock_b.exchange_id = "revolut"
    # Revolut uses dash BTC-EUR
    mock_b.fetch_order_book = AsyncMock(
        return_value={
            "asks": [[49900.0, 1.0]],
            "bids": [[49500.0, 1.0]],
            "timestamp": int(datetime.now().timestamp() * 1000),
        }
    )

    router = RouterEngine([mock_a, mock_b])

    # Test Buy (Lowest Ask)
    print("Verifying Buy route for BTC/EUR...")
    buy_res = await router.get_best_route("BTC/EUR", side="buy")
    if buy_res:
        print(f"BUY Result -> Exchange: {buy_res.exchange_id}, Price: {buy_res.price}")
        assert buy_res.exchange_id == "revolut"
        assert buy_res.price == 49900.0
        # Verification of SymbolNormalizer usage
        mock_b.fetch_order_book.assert_called_with("BTC-EUR")
        print("Success: Buy route verification passed.")
    else:
        print("Failure: No buy route found.")
        exit(1)

    # Test Sell (Highest Bid)
    print("Verifying Sell route for BTC/EUR...")
    sell_res = await router.get_best_route("BTC/EUR", side="sell")
    if sell_res:
        print(
            f"SELL Result -> Exchange: {sell_res.exchange_id}, Price: {sell_res.price}"
        )
        assert sell_res.exchange_id == "revolut"
        assert sell_res.price == 49500.0
        # Verification of SymbolNormalizer usage
        mock_a.fetch_order_book.assert_called_with("BTC/EUR")
        print("Success: Sell route verification passed.")
    else:
        print("Failure: No sell route found.")
        exit(1)

    print("--- INTEGRATION VERIFICATION SUCCESSFUL ---")


if __name__ == "__main__":
    try:
        asyncio.run(run_integration_manual())
    except Exception as e:
        print(f"Error during verification: {e}")
        exit(1)
