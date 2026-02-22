"""
Run Enterprise Backtest with Real Database Data
"""

import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from scripts.backtest_enterprise import EnterpriseBacktestEngine
from sqlalchemy import create_engine, text
from datetime import datetime

def fetch_price_data(symbols, start_date, end_date):
    """Fetch OHLCV data from database"""
    db_url = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg2://trader:trading_secure@localhost:5456/trading_db"
    ).replace("+asyncpg", "+psycopg2").replace("postgresql+psycopg2", "postgresql")
    
    engine = create_engine(db_url)
    price_data = {}
    
    with engine.connect() as conn:
        for symbol in symbols:
            result = conn.execute(text("""
                SELECT timestamp, open, high, low, close, volume
                FROM market_candles
                WHERE symbol = :symbol
                  AND timestamp >= :start AND timestamp <= :end
                ORDER BY timestamp ASC
            """), {
                "symbol": symbol,
                "start": start_date,
                "end": end_date
            })
            
            rows = []
            for row in result:
                rows.append({
                    "timestamp": row[0],
                    "open": row[1],
                    "high": row[2],
                    "low": row[3],
                    "close": row[4],
                    "volume": row[5]
                })
            
            if rows:
                price_data[symbol] = rows
                print(f"Loaded {len(rows)} candles for {symbol}")
    
    return price_data

def main():
    # Configuration
    symbols = ["BTC", "ETH", "SOL", "ADA", "DOT", "XRP", "LINK", "DOGE", "LTC", "XLM"]
    start_date = "2020-01-01"
    end_date = "2025-12-31"
    initial_capital = 50000.0
    
    print("=" * 80)
    print("ENTERPRISE BACKTEST - AUDIT COMPLIANT")
    print("=" * 80)
    print(f"Symbols: {symbols}")
    print(f"Period: {start_date} to {end_date}")
    print(f"Initial Capital: ${initial_capital:,.2f}")
    print("=" * 80)
    
    # Fetch data
    print("\nFetching price data from database...")
    price_data = fetch_price_data(symbols, start_date, end_date)
    
    if not price_data:
        print("ERROR: No price data found!")
        return
    
    # Run backtest
    engine = EnterpriseBacktestEngine(
        symbols=list(price_data.keys()),
        start_date=start_date,
        end_date=end_date,
        initial_capital=initial_capital,
        max_position_pct=0.10,  # 10% max per position
        max_drawdown_pct=0.20,   # Stop at 20% drawdown
        risk_per_trade_pct=0.02  # 2% risk per trade
    )
    
    result = engine.run_backtest(price_data)
    
    # Save results
    output_file = f"enterprise_backtest_{result.session_id}.json"
    result.save(output_file)
    print(f"\nResults saved to: {output_file}")
    
    return result

if __name__ == "__main__":
    result = main()
