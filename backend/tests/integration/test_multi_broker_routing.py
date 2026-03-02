import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from backend.schemas.agent_messages import AgentMessage
from backend.services.cognitive_orchestrator import CognitiveOrchestrator
from backend.services.execution_gateway import ExecutionGateway
from backend.services.risk_guardian import RiskGuardian


@pytest.mark.asyncio
async def test_multi_broker_routing():
    """
    Verify that CognitiveOrchestrator routes signals to the correct exchange
    via ExecutionGateway based on the 'exchange_id' in the signal payload.
    """
    # 1. Setup ExecutionGateway with mocked exchanges
    gateway = ExecutionGateway(default_exchange_id="kraken")
    gateway.dry_run = (
        True  # Force dry run to avoid real keys check in execute_order (though we mock exchanges)
    )

    # Mock exchanges in the registry
    mock_bybit = AsyncMock()
    mock_bybit.create_order.return_value = {"id": "bybit_123", "status": "closed"}

    mock_revolut = AsyncMock()
    mock_revolut.submit_order.return_value = MagicMock(
        order_id="rev_123", status=MagicMock(value="closed"), filled_qty=1.0, raw_response={}
    )

    gateway.exchanges["bybit"] = mock_bybit
    gateway.exchanges["revolut"] = mock_revolut

    # 2. Setup Orchestrator with mocked RiskGuardian
    orchestrator = CognitiveOrchestrator(tenant_id="test_tenant")
    orchestrator.execution_gateway = gateway

    # Mock Risk Guardian to auto-approve
    mock_risk = AsyncMock()

    async def risk_handler(msg: AgentMessage):
        if msg.type == "VALIDATE_ORDER":
            # Auto-approve
            result_msg = AgentMessage(
                source="risk_guardian_v1",
                target="orchestrator_v1",
                type="ORDER_VALIDATION_RESULT",
                payload={
                    "result": {"allowed": True, "reason": "Test Approval"},
                    "original_msg_id": msg.id,
                    "order": msg.payload[
                        "order"
                    ],  # Echo back the order details including exchange_id
                },
                tenant_id="test_tenant",
            )
            await orchestrator.handle_message(result_msg)

    mock_risk.handle_message = risk_handler
    orchestrator.agents["risk_guardian_v1"] = mock_risk

    # 3. Test Bybit Routing
    signal_bybit = AgentMessage(
        source="research_v1",
        target="orchestrator_v1",
        type="SIGNAL",
        payload={
            "signal": "BULLISH_MOMENTUM",
            "symbol": "BTC/USD",
            "price": 50000.0,
            "exchange_id": "bybit",
        },
        tenant_id="test_tenant",
    )

    # We need to spy on gateway.execute_order or just check the mock_bybit call?
    # Since execute_order calls the mock exchange, checking mock exchange is better.
    # But wait, execute_order mocks internal logic if dry_run=True.
    # Let's check execute_order logic.
    # If dry_run is True, it returns a mock dict AND DOES NOT CALL the exchange.
    # So we must set dry_run=False to verifying routing to actual exchange object?
    # BUT if we set dry_run=False, execute_order checks for keys/killswitch/initialized.
    # We manually injected exchanges into gateway.exchanges, so initialization check should pass.
    # Kill switch is in settings.

    # Let's force dry_run=False for the gateway instance for this test
    gateway.dry_run = False
    gateway.settings.KILL_SWITCH = False

    await orchestrator.handle_message(signal_bybit)

    # Allow some time for async processing if needed (handle_message is async but calls sub-handlers awaitedly?
    # Yes, process_generic -> risk -> orchestrator -> gateway is a chain.
    # But wait, orchestrator.handle_message calls process_generic which calls risk.handle_message (awaited).
    # Risk mock calls orchestrator.handle_message (awaited) which calls process_generic for VALIDATION_RESULT.
    # So it should be synchronous chain in this test setup.

    mock_bybit.create_order.assert_called_once()
    assert mock_bybit.create_order.call_args[1]["symbol"] == "BTC/USD"

    # 4. Test Revolut Routing
    signal_revolut = AgentMessage(
        source="research_v1",
        target="orchestrator_v1",
        type="SIGNAL",
        payload={
            "signal": "BEARISH_MOMENTUM",
            "symbol": "ETH/USD",
            "price": 3000.0,
            "exchange_id": "revolut",
        },
        tenant_id="test_tenant",
    )

    await orchestrator.handle_message(signal_revolut)

    mock_revolut.submit_order.assert_called_once()
    # Check symbol mapping logic in execute_order
    # rev_symbol = symbol.replace("/", "-") -> "ETH-USD"
    assert mock_revolut.submit_order.call_args[0][0].symbol == "ETH-USD"


if __name__ == "__main__":
    # Allow running directly
    asyncio.run(test_multi_broker_routing())
