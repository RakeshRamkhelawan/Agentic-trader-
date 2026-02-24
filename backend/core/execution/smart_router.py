from pydantic import BaseModel


class RoutingDecision(BaseModel):
    selected_exchange_id: str
    price: float
    fee_tier: str
    split_ratio: float = 1.0  # 1.0 = 100% to this exchange


class SmartRouter:
    """
    Selects the best venue for execution based on price, liquidity (mocked), and fees.
    """

    def __init__(self):
        # Mock available exchanges with base fees
        self.exchanges = {
            "kraken": {"maker_fee": 0.0016, "taker_fee": 0.0026},
            "binance": {"maker_fee": 0.0010, "taker_fee": 0.0010},
            "coinbase": {"maker_fee": 0.0040, "taker_fee": 0.0060},
        }

    async def get_best_route(self, asset: str, side: str, amount: float) -> RoutingDecision:
        """
        Simulate checking multiple exchanges for the best price.
        In a real system, this would fetch Order Books via CCXT/WebSocket.
        """

        # Mock prices (slightly different to force routing logic)
        # Base price 50000
        mock_prices = {
            "kraken": 50000.0,
            "binance": 50010.0,  # Higher ask (bad for buy)
            "coinbase": 49990.0,  # Lower ask (good for buy)
        }

        best_exchange = None
        best_price = float("inf") if side == "buy" else float("-inf")

        for exchange_id, price in mock_prices.items():
            # Adjust price for fees (simplified)
            # Buy: Effective Price = Price * (1 + fee)
            # Sell: Effective Price = Price * (1 - fee)

            fee = self.exchanges[exchange_id]["taker_fee"]  # Assume taker

            if side == "buy":
                effective_price = price * (1 + fee)
                if effective_price < best_price:
                    best_price = effective_price
                    best_exchange = exchange_id
            else:  # sell
                effective_price = price * (1 - fee)
                if effective_price > best_price:
                    best_price = effective_price
                    best_exchange = exchange_id

        return RoutingDecision(
            selected_exchange_id=best_exchange or "kraken",  # Fallback
            price=mock_prices.get(best_exchange, 0.0),
            fee_tier="taker",
        )
