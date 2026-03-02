from fastapi.testclient import TestClient
from datetime import datetime, timedelta
import sys
import os
import asyncio

# Add project root to path
sys.path.append(os.getcwd())

from backend.api.main import app, token_validator
from backend.core.auth.models import TokenPayload

# Mock Auth (Async)
async def mock_validate_token(token):
    return TokenPayload(
        sub="test-user",
        tenant_id="tenant-dev",
        roles=[],
        exp=9999999999
    )

token_validator.validate_token = mock_validate_token

client = TestClient(app)

def test_run_backtest():
    start_date = (datetime.now() - timedelta(days=30)).isoformat()
    end_date = datetime.now().isoformat()

    headers = {"Authorization": "Bearer mock-token"}

    payload = {
        "strategy_name": "MovingAverage",
        "symbols": ["BTC/USD"],
        "start_date": start_date,
        "end_date": end_date,
        "initial_capital": 10000.0,
        "timeframe": "1d"
    }

    print(f"Testing Backtest API with payload: {payload}")

    response = client.post("/api/v1/backtest/run", json=payload, headers=headers)

    if response.status_code != 200:
        print(f"Request failed: {response.status_code}")
        print(response.json())
        sys.exit(1)

    data = response.json()
    metrics = data.get("metrics")
    equity_curve = data.get("equity_curve")
    trades = data.get("trades")

    print("\n--- Backtest Results ---")
    print(f"Total Return: {metrics['total_return']*100:.2f}%")
    print(f"CAGR: {metrics['cagr']*100:.2f}%")
    print(f"Sharpe Ratio: {metrics['sharpe_ratio']:.2f}")
    print(f"Max Drawdown: {metrics['max_drawdown']*100:.2f}%")
    print(f"Total Trades: {metrics.get('total_trades', len(trades))}")
    print(f"Final Equity: {equity_curve[-1]['equity']:.2f}")

    assert metrics['total_return'] is not None
    assert len(equity_curve) > 0

    print("\nSUCCESS: Backtest API Verified!")

if __name__ == "__main__":
    test_run_backtest()
