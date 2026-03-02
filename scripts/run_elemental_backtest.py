"""
Run Elemental Agent Backtest with Full Asset Universe
Integrates Vedic intelligence into trading decisions
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


from sqlalchemy import create_engine, text

from scripts.backtest_elemental import ElementalBacktestEngine


def get_all_symbols():
    """Get all available symbols from database"""
    db_url = (
        os.getenv(
            "DATABASE_URL",
            "postgresql+psycopg2://trader:trading_secure@localhost:5456/trading_db",
        )
        .replace("+asyncpg", "+psycopg2")
        .replace("postgresql+psycopg2", "postgresql")
    )

    engine = create_engine(db_url)

    with engine.connect() as conn:
        result = conn.execute(
            text(
                """
            SELECT DISTINCT symbol FROM market_candles
            WHERE timestamp >= '2020-01-01'
            ORDER BY symbol
        """
            )
        )
        symbols = [row[0] for row in result]

    return symbols


def fetch_price_data(symbols, start_date, end_date):
    """Fetch OHLCV data from database"""
    db_url = (
        os.getenv(
            "DATABASE_URL",
            "postgresql+psycopg2://trader:trading_secure@localhost:5456/trading_db",
        )
        .replace("+asyncpg", "+psycopg2")
        .replace("postgresql+psycopg2", "postgresql")
    )

    engine = create_engine(db_url)
    price_data = {}

    print(f"\nFetching data for {len(symbols)} symbols...")

    with engine.connect() as conn:
        for i, symbol in enumerate(symbols, 1):
            result = conn.execute(
                text(
                    """
                SELECT timestamp, open, high, low, close, volume
                FROM market_candles
                WHERE symbol = :symbol
                  AND timestamp >= :start
                  AND timestamp <= :end
                ORDER BY timestamp ASC
            """
                ),
                {"symbol": symbol, "start": start_date, "end": end_date},
            )

            rows = []
            for row in result:
                rows.append(
                    {
                        "timestamp": row[0],
                        "open": row[1],
                        "high": row[2],
                        "low": row[3],
                        "close": row[4],
                        "volume": row[5],
                    }
                )

            if rows:
                price_data[symbol] = rows
                print(f"  [{i}/{len(symbols)}] {symbol}: {len(rows)} candles")

    return price_data


def main():
    # Configuration
    start_date = "2020-01-01"
    end_date = "2025-12-31"
    initial_capital = 100000.0

    print("=" * 80)
    print("ELEMENTAL AGENT BACKTEST - VEDIC INTELLIGENCE")
    print("=" * 80)
    print(f"Period: {start_date} to {end_date}")
    print(f"Initial Capital: ${initial_capital:,.2f}")
    print("\nActive Agents:")
    print("  FIRE   (Agni)    - Risk Guardian")
    print("  WATER  (Apas)    - Macro Regime")
    print("  AIR    (Vayu)    - Technical Signals")
    print("  EARTH  (Prithvi) - Valuation")
    print("  ETHER  (Akasha)  - Orchestrator")

    # Get all available symbols
    all_symbols = get_all_symbols()
    print(f"\nAvailable symbols in database: {len(all_symbols)}")

    # Use all available symbols
    symbols = all_symbols[:57]  # We have 57 total
    print(f"Running backtest with {len(symbols)} assets")
    print(f"Assets: {', '.join(symbols[:10])}... (and {len(symbols)-10} more)")

    # Fetch data
    print("\n" + "=" * 80)
    price_data = fetch_price_data(symbols, start_date, end_date)

    if not price_data:
        print("ERROR: No price data found!")
        return

    print(f"\nSuccessfully loaded data for {len(price_data)} symbols")

    # Run backtest
    print("\n" + "=" * 80)
    print("STARTING ELEMENTAL AGENT BACKTEST")
    print("=" * 80)

    engine = ElementalBacktestEngine(
        symbols=list(price_data.keys()),
        start_date=start_date,
        end_date=end_date,
        initial_capital=initial_capital,
        max_position_pct=0.08,  # Max 8% per position
        max_drawdown_pct=0.20,  # Stop at 20% drawdown
        risk_per_trade_pct=0.015,  # 1.5% risk per trade
    )

    result = engine.run_backtest(price_data)

    # Save results
    output_file = f"elemental_backtest_{result.session_id}.json"
    result.save(output_file)

    # Also create summary CSV
    create_trade_csv(result, f"elemental_backtest_{result.session_id}_trades.csv")

    # Create harmony curve CSV
    create_harmony_csv(result, f"elemental_backtest_{result.session_id}_harmony.csv")

    print("\n" + "=" * 80)
    print("BACKTEST COMPLETE - FILES GENERATED")
    print("=" * 80)
    print(f"JSON Report:  {output_file}")
    print(f"Trade CSV:    elemental_backtest_{result.session_id}_trades.csv")
    print(f"Harmony CSV:  elemental_backtest_{result.session_id}_harmony.csv")
    print(f"\nFinal Value:  ${result.final_value:,.2f}")
    print(f"Return:       {result.total_return_pct:+.2f}%")
    print(f"Max DD:       {result.max_drawdown_pct:.2f}%")
    print(f"Sharpe:       {result.sharpe_ratio:.2f}")
    print(f"Sortino:      {result.sortino_ratio:.2f}")
    print(f"Harmony:      {result.avg_harmony_score:.3f}")
    print("=" * 80)

    return result


def create_trade_csv(result, filename):
    """Create CSV file with all trades for Excel analysis"""
    import csv

    with open(filename, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "trade_id",
                "timestamp",
                "symbol",
                "action",
                "quantity",
                "price",
                "value",
                "realized_pnl",
                "realized_pnl_pct",
                "is_winner",
                "is_loser",
                "harmony_score",
                "dominant_planet",
                "fire_decision",
                "ether_decision",
                "portfolio_value_before",
                "portfolio_value_after",
            ]
        )

        for trade in result.trades:
            writer.writerow(
                [
                    trade["trade_id"],
                    trade["timestamp"],
                    trade["symbol"],
                    trade["action"],
                    trade["quantity"],
                    trade["price"],
                    trade["value"],
                    trade.get("realized_pnl", ""),
                    trade.get("realized_pnl_pct", ""),
                    trade.get("is_winner", ""),
                    trade.get("is_loser", ""),
                    trade.get("harmony_score", ""),
                    trade.get("dominant_planet", ""),
                    trade.get("fire_decision", ""),
                    trade.get("ether_decision", ""),
                    trade["portfolio_value_before"],
                    trade["portfolio_value_after"],
                ]
            )

    print(f"Trade CSV created: {filename}")


def create_harmony_csv(result, filename):
    """Create CSV with harmony scores over time"""
    import csv

    with open(filename, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(
            ["timestamp", "symbol", "harmony", "decision", "action", "planet"]
        )

        for entry in result.harmony_curve:
            writer.writerow(
                [
                    entry.get("timestamp", ""),
                    entry.get("symbol", ""),
                    entry.get("harmony", ""),
                    entry.get("decision", ""),
                    entry.get("action", ""),
                    entry.get("planet", ""),
                ]
            )

    print(f"Harmony CSV created: {filename}")


if __name__ == "__main__":
    result = main()
