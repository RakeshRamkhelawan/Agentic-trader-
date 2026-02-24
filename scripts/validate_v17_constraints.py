#!/usr/bin/env python3
"""
Validate V17 Financial Constraints in MCP Tools.

This script validates that all V17 constraints are properly enforced:
- €2,000 max position size
- 60-day failsafe
- 3-loss rule
- Trailing stop logic
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.mcp_broker.tools.elemental_tools import (
    elemental_fire_position_size,
    elemental_earth_entry_check,
    elemental_earth_exit_check,
)


class MockContext:
    """Mock MCP context for testing."""
    def info(self, msg): print(f"  [INFO] {msg}")
    def error(self, msg): print(f"  [ERROR] {msg}")
    def warning(self, msg): print(f"  [WARN] {msg}")


async def test_max_position_constraint():
    """Test €2,000 max position size constraint."""
    print("\n" + "=" * 60)
    print("TEST: Max Position Size Constraint (€2,000)")
    print("=" * 60)

    ctx = MockContext()

    # Test 1: Small portfolio should respect €2k cap
    result = await elemental_fire_position_size(
        symbol="AAPL",
        portfolio_value=1000000.0,  # €1M portfolio
        vedastro_score=90.0,
        dominant_planet="JUPITER",
        price_history=[100.0 + i * 0.5 for i in range(30)],
        ctx=ctx
    )

    position_size = result["position_size_eur"]
    max_allowed = result["max_position_eur"]

    print(f"\nPortfolio: €1,000,000")
    print(f"Position size: €{position_size:.2f}")
    print(f"Max allowed: €{max_allowed:.2f}")

    assert max_allowed == 2000.0, f"Max position should be €2,000, got €{max_allowed}"
    assert position_size <= 2000.0, f"Position size €{position_size} exceeds €2,000 cap!"

    print("[PASS] Position size respects €2,000 cap")

    # Test 2: Position should not exceed 2% of portfolio
    portfolio_value = 50000.0  # €50k
    result = await elemental_fire_position_size(
        symbol="AAPL",
        portfolio_value=portfolio_value,
        vedastro_score=80.0,
        dominant_planet="JUPITER",
        price_history=[100.0 + i * 0.5 for i in range(30)],
        ctx=ctx
    )

    position_pct = result["position_pct"]
    print(f"\nPortfolio: €50,000")
    print(f"Position size: €{result['position_size_eur']:.2f}")
    print(f"Position pct: {position_pct*100:.2f}%")

    assert position_pct <= 0.02, f"Position {position_pct*100}% exceeds 2% portfolio limit!"

    print("[PASS] Position size respects 2% portfolio limit")


async def test_three_loss_rule():
    """Test 3 consecutive losses entry blocking."""
    print("\n" + "=" * 60)
    print("TEST: 3-Loss Rule (Entry Blocking)")
    print("=" * 60)

    ctx = MockContext()

    # Test 1: No losses - should allow entry
    result = await elemental_earth_entry_check(
        symbol="AAPL",
        trade_history=[
            {"symbol": "AAPL", "pnl": 100, "win": True},
            {"symbol": "AAPL", "pnl": 200, "win": True},
        ],
        ctx=ctx
    )

    assert result["can_enter"] is True, "Should allow entry with no losses"
    assert result["consecutive_losses"] == 0
    print("[PASS] Entry allowed with winning history")

    # Test 2: 2 consecutive losses - should allow entry
    result = await elemental_earth_entry_check(
        symbol="AAPL",
        trade_history=[
            {"symbol": "AAPL", "pnl": -100, "win": False},
            {"symbol": "AAPL", "pnl": -200, "win": False},
            {"symbol": "AAPL", "pnl": 100, "win": True},  # Win before losses
        ],
        ctx=ctx
    )

    assert result["can_enter"] is True, "Should allow entry with 2 consecutive losses"
    assert result["consecutive_losses"] == 2
    print("[PASS] Entry allowed with 2 consecutive losses")

    # Test 3: 3 consecutive losses - should BLOCK entry
    result = await elemental_earth_entry_check(
        symbol="AAPL",
        trade_history=[
            {"symbol": "AAPL", "pnl": -100, "win": False},
            {"symbol": "AAPL", "pnl": -200, "win": False},
            {"symbol": "AAPL", "pnl": -150, "win": False},
        ],
        ctx=ctx
    )

    assert result["can_enter"] is False, "Should BLOCK entry with 3 consecutive losses"
    assert result["consecutive_losses"] == 3
    assert result["blocking_reason"] == "3_consecutive_losses"
    print("[PASS] Entry BLOCKED with 3 consecutive losses")


async def test_sixty_day_failsafe():
    """Test 60-day max hold constraint."""
    print("\n" + "=" * 60)
    print("TEST: 60-Day Failsafe (Max Hold)")
    print("=" * 60)

    ctx = MockContext()
    from datetime import datetime, timedelta

    # Test 1: 30 days held - should NOT exit
    entry_date = (datetime.utcnow() - timedelta(days=30)).isoformat()
    current_date = datetime.utcnow().isoformat()

    result = await elemental_earth_exit_check(
        symbol="AAPL",
        entry_date=entry_date,
        current_date=current_date,
        entry_price=100.0,
        current_price=120.0,
        peak_price=130.0,
        ctx=ctx
    )

    assert result["should_exit"] is False, "Should NOT exit after 30 days"
    assert result["days_held"] == 30
    print("[PASS] No exit after 30 days")

    # Test 2: 65 days held - should EXIT (60-day failsafe)
    entry_date = (datetime.utcnow() - timedelta(days=65)).isoformat()

    result = await elemental_earth_exit_check(
        symbol="AAPL",
        entry_date=entry_date,
        current_date=current_date,
        entry_price=100.0,
        current_price=120.0,
        peak_price=130.0,
        ctx=ctx
    )

    assert result["should_exit"] is True, "Should EXIT after 65 days (exceeds 60-day failsafe)"
    assert result["days_held"] == 65
    assert "max_hold_days_60" in result["exit_reasons"]
    print("[PASS] Exit triggered after 65 days (60-day failsafe)")


async def test_trailing_stop():
    """Test trailing stop logic (+40% → -15%)."""
    print("\n" + "=" * 60)
    print("TEST: Trailing Stop (+40% Peak to -15% Drop)")
    print("=" * 60)

    ctx = MockContext()
    from datetime import datetime, timedelta

    entry_date = (datetime.utcnow() - timedelta(days=10)).isoformat()
    current_date = datetime.utcnow().isoformat()

    # Test 1: Peak +40%, current -10% from peak - should NOT exit
    entry_price = 100.0
    peak_price = 140.0  # +40%
    current_price = 126.0  # -10% from peak

    result = await elemental_earth_exit_check(
        symbol="AAPL",
        entry_date=entry_date,
        current_date=current_date,
        entry_price=entry_price,
        current_price=current_price,
        peak_price=peak_price,
        ctx=ctx
    )

    assert result["trailing_stop_active"] is True, "Trailing stop should be active at +40%"
    assert result["should_exit"] is False, "Should NOT exit at -10% from peak"
    print(f"[PASS] Trailing stop active, no exit at -10% from peak (peak was +40%)")

    # Test 2: Peak +40%, current -20% from peak - should EXIT
    current_price = 112.0  # -20% from peak

    result = await elemental_earth_exit_check(
        symbol="AAPL",
        entry_date=entry_date,
        current_date=current_date,
        entry_price=entry_price,
        current_price=current_price,
        peak_price=peak_price,
        ctx=ctx
    )

    assert result["trailing_stop_active"] is True
    assert result["should_exit"] is True, "Should EXIT at -20% from peak (exceeds -15%)"
    assert any("trailing_stop" in reason for reason in result["exit_reasons"])
    print(f"[PASS] Exit triggered at -20% from peak (exceeds -15% trailing stop)")


async def test_commission_and_slippage():
    """Test commission (0.05%) and slippage (0.1%) in execution."""
    print("\n" + "=" * 60)
    print("TEST: Commission & Slippage")
    print("=" * 60)

    from backend.mcp_broker.tools.execution_tools import (
        execution_execute_paper_trade,
        COMMISSION_PCT,
        SLIPPAGE_PCT
    )

    ctx = MockContext()

    symbol = "AAPL"
    action = "BUY"
    quantity = 10.0
    current_price = 150.0

    result = await execution_execute_paper_trade(
        symbol=symbol,
        action=action,
        quantity=quantity,
        current_price=current_price,
        account_id="test_account",
        ctx=ctx
    )

    gross_value = result["gross_value"]
    commission = result["commission"]
    filled_price = result["filled_price"]

    # Calculate expected values
    expected_filled_price = current_price * (1 + SLIPPAGE_PCT)  # BUY = +slippage
    expected_gross = quantity * expected_filled_price
    expected_commission = expected_gross * COMMISSION_PCT

    print(f"\nTrade: BUY {quantity} {symbol} @ ${current_price}")
    print(f"Filled price: ${filled_price:.2f} (expected: ${expected_filled_price:.2f})")
    print(f"Gross value: €{gross_value:.2f}")
    print(f"Commission: €{commission:.4f} (expected: €{expected_commission:.4f})")
    print(f"Commission rate: {COMMISSION_PCT*100:.3f}%")
    print(f"Slippage rate: {SLIPPAGE_PCT*100:.1f}%")

    assert abs(filled_price - expected_filled_price) < 0.01, "Slippage not applied correctly"
    assert abs(commission - expected_commission) < 0.01, "Commission not calculated correctly"

    print("[PASS] Commission and slippage applied correctly")


async def test_max_position_enforcement():
    """Test that trades exceeding €2,000 are rejected."""
    print("\n" + "=" * 60)
    print("TEST: Max Position Enforcement (Rejection)")
    print("=" * 60)

    from backend.mcp_broker.tools.execution_tools import (
        execution_execute_paper_trade,
        MAX_POSITION_EUR
    )

    ctx = MockContext()

    # Try to execute a trade that would exceed €2,000
    symbol = "AAPL"
    action = "BUY"
    quantity = 20.0  # 20 shares @ $150 = $3,000
    current_price = 150.0

    try:
        result = await execution_execute_paper_trade(
            symbol=symbol,
            action=action,
            quantity=quantity,
            current_price=current_price,
            account_id="test_account",
            ctx=ctx
        )
        print(f"❌ FAIL: Trade should have been rejected! Position: €{result['gross_value']:.2f}")
        return False
    except ValueError as e:
        print(f"[PASS] Trade correctly rejected - {e}")
        return True


async def main():
    """Run all V17 constraint validation tests."""
    print("\n" + "=" * 60)
    print("V17 FINANCIAL CONSTRAINTS VALIDATION")
    print("Agentic Trader Platform V18 - MCP Tools")
    print("=" * 60)

    tests = [
        ("Max Position Constraint", test_max_position_constraint),
        ("3-Loss Rule", test_three_loss_rule),
        ("60-Day Failsafe", test_sixty_day_failsafe),
        ("Trailing Stop", test_trailing_stop),
        ("Commission & Slippage", test_commission_and_slippage),
        ("Max Position Enforcement", test_max_position_enforcement),
    ]

    passed = 0
    failed = 0

    for test_name, test_func in tests:
        try:
            await test_func()
            passed += 1
        except AssertionError as e:
            print(f"\n[FAIL] {test_name} - {e}")
            failed += 1
        except Exception as e:
            print(f"\n[ERROR] {test_name} - {e}")
            import traceback
            traceback.print_exc()
            failed += 1

    print("\n" + "=" * 60)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("=" * 60)

    if failed == 0:
        print("\n[SUCCESS] ALL V17 CONSTRAINTS VALIDATED SUCCESSFULLY!")
        return 0
    else:
        print(f"\n[ERROR] {failed} TEST(S) FAILED")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
