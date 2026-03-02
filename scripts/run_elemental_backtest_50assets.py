"""
Run Elemental Agent Backtest with 50 Assets, 2020-2026
Vedic Intelligence with extended timeframe
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


from sqlalchemy import create_engine, text

from scripts.backtest_elemental import ElementalBacktestEngine


def get_all_symbols(limit=50):
    """Get top N symbols from database by data quality"""
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
        # Get symbols with most data points (better for backtest)
        result = conn.execute(
            text(
                """
            SELECT symbol, COUNT(*) as candle_count
            FROM market_candles
            WHERE timestamp >= '2020-01-01'
            GROUP BY symbol
            ORDER BY candle_count DESC
            LIMIT :limit
        """
            ),
            {"limit": limit},
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
    # Configuration - 50 assets, 2020-2026
    start_date = "2020-01-01"
    end_date = "2026-01-09"  # Extended to 2026 (database limit)
    initial_capital = 100000.0
    num_assets = 50

    print("=" * 80)
    print("ELEMENTAL AGENT BACKTEST - 50 ASSETS | 2020-2026")
    print("=" * 80)
    print(f"Period: {start_date} to {end_date}")
    print(f"Assets: {num_assets} symbols")
    print(f"Initial Capital: ${initial_capital:,.2f}")
    print("\nActive Vedic Agents:")
    print("  [FIRE]   (Agni)    - Risk Guardian")
    print("  [WATER]  (Apas)    - Macro Regime")
    print("  [AIR]    (Vayu)    - Technical Signals")
    print("  [EARTH]  (Prithvi) - Valuation")
    print("  [ETHER]  (Akasha)  - Orchestrator")

    # Get top 50 symbols by data quality
    all_symbols = get_all_symbols(limit=num_assets)

    # V6: No hardcoded exclusions - agents decide organically
    # TSLA and other risky symbols will self-exclude through low agent confidence

    print(f"\nSelected {len(all_symbols)} assets for backtest:")
    print("  V7: Calibrated adaptive - warm-start confidence per asset class")

    # Group by asset type
    crypto = [
        s
        for s in all_symbols
        if s in ["BTC", "ETH", "SOL", "ADA", "DOT", "LINK", "AVAX", "MATIC"]
    ]
    equities = [
        s
        for s in all_symbols
        if s not in crypto
        and not any(
            x in s
            for x in [
                "EEM",
                "EFA",
                "GLD",
                "IWM",
                "QQQ",
                "SPY",
                "TLT",
                "USO",
                "VTI",
                "VIX",
            ]
        )
    ]
    etfs = [
        s
        for s in all_symbols
        if s in ["EEM", "EFA", "GLD", "IWM", "QQQ", "SPY", "TLT", "USO", "VTI"]
    ]

    print(f"  Crypto:   {crypto}")
    print(
        f"  Equities: {equities[:15]}..."
        if len(equities) > 15
        else f"  Equities: {equities}"
    )
    print(f"  ETFs:     {etfs}")

    # Fetch data
    print("\n" + "=" * 80)
    price_data = fetch_price_data(all_symbols, start_date, end_date)

    if not price_data:
        print("ERROR: No price data found!")
        return

    print(f"\nSuccessfully loaded data for {len(price_data)} symbols")

    # Calculate date range in data
    all_dates = set()
    for symbol_data in price_data.values():
        for d in symbol_data:
            all_dates.add(d["timestamp"])
    date_range = sorted(all_dates)
    print(f"Date range: {date_range[0]} to {date_range[-1]}")
    print(f"Total trading days: {len(date_range)}")

    # Run backtest
    print("\n" + "=" * 80)
    print("STARTING ELEMENTAL AGENT BACKTEST")
    print("=" * 80)

    engine = ElementalBacktestEngine(
        symbols=list(price_data.keys()),
        start_date=start_date,
        end_date=end_date,
        initial_capital=initial_capital,
        max_position_pct=0.06,  # Max 6% per position (diversified across 50)
        max_drawdown_pct=0.20,  # Stop at 20% drawdown
        risk_per_trade_pct=0.012,  # 1.2% risk per trade
    )

    result = engine.run_backtest(price_data)

    # Save results
    output_file = f"elemental_backtest_50assets_{result.session_id}.json"
    result.save(output_file)

    # Create summary CSVs
    create_trade_csv(
        result, f"elemental_backtest_50assets_{result.session_id}_trades.csv"
    )
    create_harmony_csv(
        result, f"elemental_backtest_50assets_{result.session_id}_harmony.csv"
    )
    create_symbol_performance_csv(
        result, f"elemental_backtest_50assets_{result.session_id}_symbols.csv"
    )

    print("\n" + "=" * 80)
    print("BACKTEST COMPLETE - FILES GENERATED")
    print("=" * 80)
    print(f"JSON Report:  {output_file}")
    print(f"Trade CSV:    elemental_backtest_50assets_{result.session_id}_trades.csv")
    print(f"Harmony CSV:  elemental_backtest_50assets_{result.session_id}_harmony.csv")
    print(f"Symbols CSV:  elemental_backtest_50assets_{result.session_id}_symbols.csv")
    print("\n[FINAL RESULTS]")
    print(f"  Portfolio Value: ${result.final_value:,.2f}")
    print(f"  Total Return:    {result.total_return_pct:+.2f}%")
    print(f"  Max Drawdown:    {result.max_drawdown_pct:.2f}%")
    print(f"  Sharpe Ratio:    {result.sharpe_ratio:.2f}")
    print(f"  Sortino Ratio:   {result.sortino_ratio:.2f}")
    print(f"  Win Rate:        {result.win_rate_pct:.1f}%")
    print(f"  Avg Harmony:     {result.avg_harmony_score:.3f}")
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


def create_symbol_performance_csv(result, filename):
    """Create CSV with per-symbol performance"""
    import csv

    with open(filename, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["symbol", "trades", "wins", "losses", "win_rate", "total_pnl"])

        # Sort by total PnL
        sorted_symbols = sorted(
            result.symbol_performance.items(),
            key=lambda x: x[1].get("total_pnl", 0),
            reverse=True,
        )

        for symbol, stats in sorted_symbols:
            writer.writerow(
                [
                    symbol,
                    stats.get("trades", 0),
                    stats.get("wins", 0),
                    stats.get("losses", 0),
                    stats.get("win_rate", 0),
                    stats.get("total_pnl", 0),
                ]
            )

    print(f"Symbol performance CSV created: {filename}")


if __name__ == "__main__":
    result = main()
