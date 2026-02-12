
import asyncio
import logging
import sys
import os
import json
from unittest.mock import MagicMock

# Add project root to path
sys.path.append(os.getcwd())

from backend.services.cognitive_orchestrator import CognitiveOrchestrator, AgentMessage
from backend.services.execution_gateway import ExecutionGateway

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("verify_execution")

async def main():
    logger.info("--- Starting Execution Flow Verification ---")
    
    # Mock dependencies
    gateway = ExecutionGateway(exchange_id="kraken")
    # For verification, we can let it be in PAPER mode (default)
    
    orchestrator = CognitiveOrchestrator(
        execution_gateway=gateway
    )
    
    # Start Gateway
    await gateway.start()
    
    # 1. Simulate ORDER_VALIDATION_RESULT from RiskGuardian
    # This simulates a scenario where RiskGuardian has approved an order
    order_payload = {
        "symbol": "BTC/USD",
        "side": "buy",
        "quantity": 0.01,
        "price": 50000.0,
        "order_type": "limit"
    }
    
    msg = AgentMessage(
        source="risk_guardian_v1",
        target="orchestrator_v1",
        type="ORDER_VALIDATION_RESULT",
        payload={
             "original_msg_id": "test_msg_id_123",
             "result": {"allowed": True, "reason": "Test Approval"},
             "order": order_payload
        }
    )
    
    logger.info("Injecting ORDER_VALIDATION_RESULT...")
    await orchestrator.handle_message(msg)
    
    # We expect logs in the Orchestrator saying "Sent to Gateway" and ExecutionGateway logs
    logger.info("Check logs above for 'Execution Result'")
    
    await gateway.stop()
    logger.info("Verification Complete.")

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
