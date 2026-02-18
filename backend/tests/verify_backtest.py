import asyncio
import uuid
from datetime import datetime, timedelta, timezone

from backend.core.database import AsyncSessionLocal
from backend.execution.backtest_engine import BacktestEngine
from backend.execution.paper_exchange import (OrderRequest, OrderStatus,
                                              PaperExchange)
from backend.models.market_data import MarketTick

SYMBOL = "BTC-EUR"
START_TIME = datetime.now(timezone.utc) - timedelta(days=1)
END_TIME = datetime.now(timezone.utc)


async def seed_data():
    print("🌱 Seeding historical data...")
    async with AsyncSessionLocal() as session:
        # Clear existing for test
        # await session.execute(delete(MarketTick).where(MarketTick.symbol == SYMBOL))

        ticks = []
        price = 50000.0
        # Generate 100 ticks over last hour
        for i in range(100):
            t_time = START_TIME + timedelta(minutes=i)
            # Random walk
            price = price * (1 + (0.001 * ((-1) ** i)))

            ticks.append(
                MarketTick(
                    id=uuid.uuid4(),
                    symbol=SYMBOL,
                    timestamp=t_time,
                    price=price,
                    volume=1.5,
                    side="buy",
                )
            )

        session.add_all(ticks)
        await session.commit()
    print("✅ Seeded 100 ticks.")


async def verify_backtest():
    await seed_data()

    print("🚀 Starting Backtest Verification...")

    engine = BacktestEngine(
        START_TIME, START_TIME + timedelta(minutes=100), speed=1000.0
    )  # 1000x speed
    exchange = PaperExchange(engine, initial_balance_eur=100000.0)

    print(f"💰 Initial Balance: {exchange.balances}")

    tick_count = 0
    orders_placed = False

    async for tick in engine.stream_ticks(SYMBOL):
        tick_count += 1

        if tick_count == 10 and not orders_placed:
            print(f"⏱️  Tick {tick_count} @ {tick.last}. Placing BUY order...")

            # Place Order
            req = OrderRequest(
                symbol=SYMBOL, side="buy", qty=1.0, client_order_id="test-order-1"
            )
            result = await exchange.submit_order(req)

            print(f"📝 Order Result: {result.status} @ {result.avg_price}")

            if result.status == OrderStatus.FILLED:
                print("✅ Order Filled!")
                orders_placed = True
            else:
                print(f"❌ Order Failed: {result}")

    print(f"🛑 Backtest Finished. Processed {tick_count} ticks.")
    print(f"💰 Final Balance: {exchange.balances}")

    # Assertions
    assert tick_count > 0, "No ticks processed"
    assert exchange.balances["BTC"] == 1.0, "BTC balance incorrect"
    assert exchange.balances["EUR"] < 100000.0, "EUR balance should decrease"

    print("🎉 Verification PASSED")


if __name__ == "__main__":
    if hasattr(asyncio, "run"):
        asyncio.run(verify_backtest())
    else:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(verify_backtest())
