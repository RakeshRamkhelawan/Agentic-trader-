import asyncio
import argparse
from datetime import datetime, timedelta, timezone
import sys
import os

# Ensure backend modules are found
sys.path.append(os.getcwd())

from backend.execution.backtest_engine import BacktestEngine
from backend.execution.paper_exchange import PaperExchange, OrderRequest, OrderStatus
from backend.services.performance_analytics import PerformanceAnalytics


async def run_backtest(symbol: str, days: int, speed: float):
    print(f"🚀 Starting Backtest for {symbol} ({days} days) @ {speed}x speed")

    end_time = datetime.now(timezone.utc)
    start_time = end_time - timedelta(days=days)

    engine = BacktestEngine(start_time, end_time, speed=speed)
    exchange = PaperExchange(engine, initial_balance_eur=10000.0)

    # Store equity curve
    equity_curve = []
    trades = []

    # Simple Strategy: Buy if price drops 1%, Sell if price rises 1%
    # This assumes we have a strategy interface, but here we hardcode for the runner demo
    last_price = None
    position = 0.0
    entry_price = 0.0

    print("⏳ Streaming ticks...", flush=True)
    tick_count = 0

    async for tick in engine.stream_ticks(symbol):
        tick_count += 1
        current_equity = exchange.balances["EUR"] + (
            exchange.balances["BTC"] * tick.last
        )
        equity_curve.append(current_equity)

        if tick_count % 10 == 0:
            print(f"Propagating tick {tick_count}: {tick.last:.2f}", flush=True)

        if last_price is None:
            last_price = tick.last
            continue

        change = (tick.last - last_price) / last_price

        # Simple Mean Reversion logic (Relaxed for test data volatility)
        if change < -0.0005 and position == 0:  # Drop 0.05%, Buy
            # Buy 0.1 BTC
            req = OrderRequest(
                symbol=symbol, side="buy", qty=0.1, client_order_id=f"B-{tick_count}"
            )
            res = await exchange.submit_order(req)
            if res.status == OrderStatus.FILLED:
                position += res.filled_qty
                entry_price = res.avg_price
                print(f"🟢 BUY  @ {res.avg_price:.2f}", flush=True)

        elif position > 0 and tick.last > entry_price * 1.0005:  # Rise 0.05%, Sell
            # Sell Position
            req = OrderRequest(
                symbol=symbol,
                side="sell",
                qty=position,
                client_order_id=f"S-{tick_count}",
            )
            res = await exchange.submit_order(req)
            if res.status == OrderStatus.FILLED:
                pnl = (res.avg_price - entry_price) * res.filled_qty
                trades.append({"pnl": pnl, "time": tick.timestamp})
                position = 0.0
                print(f"🔴 SELL @ {res.avg_price:.2f} | PnL: {pnl:.2f}")

        last_price = tick.last

    print(f"🛑 Backtest Complete. Processed {tick_count} ticks.")

    # Analyze
    analytics = PerformanceAnalytics()
    metrics = analytics.calculate_metrics(equity_curve, trades)

    print("\n📊 Performance Report:")
    print(f"Total Return: {metrics.total_return*100:.2f}%")
    print(f"Sharpe Ratio: {metrics.sharpe_ratio:.2f}")
    print(f"Max Drawdown: {metrics.max_drawdown*100:.2f}%")
    print(f"Win Rate:     {metrics.win_rate*100:.2f}%")
    print(f"Trades:       {metrics.trade_count}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Agentic Backtest")
    parser.add_argument("--symbol", type=str, default="BTC-EUR")
    parser.add_argument("--days", type=int, default=1)
    parser.add_argument("--speed", type=float, default=1000.0)

    args = parser.parse_args()

    if hasattr(asyncio, "run"):
        asyncio.run(run_backtest(args.symbol, args.days, args.speed))
    else:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(run_backtest(args.symbol, args.days, args.speed))
