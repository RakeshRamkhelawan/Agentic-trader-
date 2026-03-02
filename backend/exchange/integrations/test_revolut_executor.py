"""
Test RevolutXAdapter with OrderExecutor.

Demonstrates end-to-end order flow:
1. Initialize RevolutXAdapter
2. Connect to Revolut X API
3. Create OrderExecutor with adapter
4. Execute trade via ExecutionPlan
5. Monitor order status

Usage:
    python backend/integrations/test_revolut_executor.py
"""

import asyncio
import logging

from dotenv import load_dotenv

from backend.core.schemas.ooda_types import ExecutionPlan
from backend.execution.order_executor import OrderExecutor
from backend.execution.revolut_x_adapter import RevolutXAdapter
from backend.governance.agent_gatekeeper import AgentGatekeeper, AgentRole

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()


async def test_revolut_executor():
    """Test RevolutXAdapter integration with OrderExecutor."""

    print("\n" + "=" * 60)
    print("REVOLUT X + ORDER EXECUTOR INTEGRATION TEST")
    print("=" * 60 + "\n")

    # Step 1: Initialize Revolut X Adapter
    print("Step 1️⃣: Initializing RevolutXAdapter...")
    adapter = RevolutXAdapter()

    try:
        # Step 2: Connect to Revolut X
        print("\nStep 2️⃣: Connecting to Revolut X API...")
        await adapter.connect()
        print("✅ Connected to Revolut X!")

        # Step 3: Create OrderExecutor with real adapter
        print("\nStep 3️⃣: Creating OrderExecutor with RevolutXAdapter...")

        # Create gatekeeper (will validate EXECUTOR role has TRADE_EXECUTION permission)
        gatekeeper = AgentGatekeeper()

        # Initialize OrderExecutor with Revolut X adapter
        executor = OrderExecutor(
            exchange_adapter=adapter,
            max_slippage_bps=50,  # 0.5% max slippage
            order_timeout=30,  # 30 seconds
            gatekeeper=gatekeeper,
        )
        print("✅ OrderExecutor initialized with RevolutXAdapter")
        print(f"   Exchange: {type(executor.exchange).__name__}")
        print(f"   Max Slippage: {executor.max_slippage_bps} bps")
        print(f"   Order Timeout: {executor.order_timeout}s")

        # Step 4: Create execution plan
        print("\nStep 4️⃣: Creating ExecutionPlan...")
        execution_plan = ExecutionPlan(
            symbol="BTC/USDT",  # OODA format (will be mapped to BTC-USD)
            side="buy",
            order_type="limit",
            quantity=0.0001,  # Very small test order (~$10)
            price=100000.0,  # Well below market (won't fill immediately)
            expected_price=100000.0,  # Expected fill price for slippage calc
            trace_id="test-revolut-executor-001",
            caller_name="test_trader",
            caller_role=AgentRole.EXECUTOR,
        )
        print("✅ ExecutionPlan created:")
        print(f"   Symbol: {execution_plan.symbol}")
        print(f"   Side: {execution_plan.side}")
        print(f"   Type: {execution_plan.order_type}")
        print(f"   Quantity: {execution_plan.quantity} BTC")
        print(f"   Limit Price: ${execution_plan.price:,.0f}")

        # Step 5: Execute trade (COMMENTED OUT - UNCOMMENT TO PLACE REAL ORDER)
        print("\n" + "⚠️ " * 20)
        print("⚠️  REAL ORDER EXECUTION DISABLED")
        print("⚠️  To place a real order on Revolut X:")
        print("⚠️    1. Review the execution plan above")
        print("⚠️    2. Uncomment the execution block in the code")
        print("⚠️    3. Run this script again")
        print("⚠️ " * 20 + "\n")

        # UNCOMMENT BELOW TO PLACE REAL ORDER
        # print("\nStep 5️⃣: Executing trade on Revolut X...")
        # outcome = await executor.execute_trade(execution_plan)
        #
        # print("\n" + "="*60)
        # print("EXECUTION OUTCOME")
        # print("="*60)
        # print(f"Success: {outcome.success}")
        # print(f"Trace ID: {outcome.trace_id}")
        # print(f"Order ID: {outcome.order_id}")
        # print(f"Filled Quantity: {outcome.filled_qty}")
        # print(f"Avg Fill Price: ${outcome.avg_price:,.2f}")
        # print(f"Fee: ${outcome.fee:.2f}")
        # print(f"Execution Latency: {outcome.execution_latency_ms:.2f}ms")
        # if outcome.error:
        #     print(f"Error: {outcome.error}")

        # Step 6: Query active orders
        print("\nStep 6️⃣: Querying active orders...")
        active_orders = await adapter.client.get_active_orders(limit=10)
        print(f"✅ Active orders: {len(active_orders)}")

        if active_orders:
            for i, order in enumerate(active_orders, 1):
                print(f"\n   Order {i}:")
                print(f"   - ID: {order.get('id')}")
                print(f"   - Symbol: {order.get('symbol')}")
                print(f"   - Side: {order.get('order_side')}")
                print(f"   - Quantity: {order.get('qty')}")
                print(f"   - Price: {order.get('price')}")
                print(f"   - Status: {order.get('status')}")
        else:
            print("   No active orders found")

    except Exception as e:
        logger.error("Test failed: %s", e, exc_info=True)
        return False

    finally:
        # Step 7: Cleanup
        print("\nStep 7️⃣: Disconnecting from Revolut X...")
        await adapter.disconnect()
        print("✅ Disconnected")

    print("\n" + "=" * 60)
    print("✅ INTEGRATION TEST COMPLETED")
    print("=" * 60 + "\n")
    return True


async def test_mock_executor():
    """Test OrderExecutor with mock adapter (for comparison)."""

    print("\n" + "=" * 60)
    print("MOCK EXECUTOR TEST (NO REAL EXCHANGE)")
    print("=" * 60 + "\n")

    # Create OrderExecutor WITHOUT adapter (uses mock)
    print("Creating OrderExecutor with default mock adapter...")
    executor = OrderExecutor()  # No adapter = mock

    print(f"✅ Executor using: {type(executor.exchange).__name__}")

    # Create test execution plan
    execution_plan = ExecutionPlan(
        symbol="BTC/USDT",
        side="buy",
        order_type="market",
        quantity=0.01,
        expected_price=104000.0,  # Mock expected price
        trace_id="test-mock-executor-001",
        caller_name="test_trader",
        caller_role=AgentRole.EXECUTOR,
    )

    print("\nExecuting trade with mock adapter...")
    outcome = await executor.execute_trade(execution_plan)

    print("\nMock Execution Result:")
    print(f"  Success: {outcome.success}")
    print(f"  Order ID: {outcome.order_id}")
    print(f"  Filled Quantity: {outcome.filled_qty}")
    print(f"  Avg Fill Price: ${outcome.avg_price:,.2f}")
    print(f"  Fee: ${outcome.fee:.2f}")
    if outcome.error:
        print(f"  Error: {outcome.error}")

    print("\n✅ MOCK TEST COMPLETED\n")


if __name__ == "__main__":
    print(
        """
╔════════════════════════════════════════════════════════════════╗
║              REVOLUT X EXECUTOR INTEGRATION TEST               ║
╚════════════════════════════════════════════════════════════════╝

This script tests the integration between:
  • RevolutXAdapter (real Revolut X API)
  • OrderExecutor (OODA Act phase)
  • ExecutionPlan (trade parameters)

Tests will:
  ✓ Connect to Revolut X API
  ✓ Initialize OrderExecutor with real adapter
  ✓ Create execution plan
  ✓ Query active orders

  ⚠️  Real order execution is DISABLED by default
  ⚠️  Uncomment the execution block to place real orders

"""
    )

    asyncio.run(test_revolut_executor())
    asyncio.run(test_mock_executor())
