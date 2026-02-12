
import asyncio
import logging
from unittest.mock import MagicMock, AsyncMock, Mock
import time
import sys

# Mock dependencies BEFORE importing services if needed, but here we can inject mocks
sys.path.append("backend") # Ensure backend is in path
from backend.services.cognitive_orchestrator import CognitiveOrchestrator, AgentMessage
from backend.services.risk_guardian_agent import RiskGuardianAgent
from backend.services.signal_bridge import SignalBridge

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Verification")

async def test_execution_flow():
    logger.info("--- Starting Risk Execution Flow Verification ---")

    # 1. Mock Dependencies
    mock_clickhouse = MagicMock()
    mock_clickhouse.connect = AsyncMock()
    
    # Mock Writers
    mock_market_writer = AsyncMock()
    mock_market_writer.enqueue = AsyncMock()
    
    mock_message_writer = AsyncMock()
    mock_message_writer.enqueue = AsyncMock()
    
    # Mock Redis Publisher for SignalBridge
    # RedisPublisher.publish is async
    mock_redis_publisher = Mock()
    mock_redis_publisher.publish = AsyncMock()
    
    # Setup SignalBridge
    signal_bridge = SignalBridge()
    signal_bridge.set_redis_publisher(mock_redis_publisher)
    
    # 2. Instantiate Orchestrator (it will call _initialize_agents)
    # Orchestrator uses AgentRegistry for configs. We may need to mock it if YAML not found.
    # But let's assume it finds agents or we manually inject them.
    
    logger.info("Initializing Orchestrator...")
    orchestrator = CognitiveOrchestrator(
        clickhouse_client=mock_clickhouse,
        market_writer=mock_market_writer,
        message_writer=mock_message_writer,
        signal_bridge=signal_bridge
    )
    
    # Manually register agents (since we don't start the full loop)
    # Orchestrator registers itself in __init__ -> _initialize_agents
    # We need to ensure RiskGuardian is there.
    # The _initialize_agents might fail if config is missing or cannot load agents.
    # Let's inspect agents dict.
    
    # Spy on RiskGuardian if it exists
    if "risk_guardian_v1" not in orchestrator.agents:
        logger.info("RiskGuardian not in registry, manually adding...")
        orchestrator.agents["risk_guardian_v1"] = RiskGuardianAgent(message_bus=orchestrator.handle_message)
    else:
        logger.info("RiskGuardian found in registry.")

    # 3. Simulate RESEARCH SIGNAL (BULLISH)
    # Orchestrator.handle_message(msg) should handle it
    
    logger.info("STEP 1: Injecting BULLISH SIGNAL from Research Agent...")
    signal_msg = AgentMessage(
        source="research_v1",
        target="orchestrator_v1", # Targeted at orchestrator
        type="SIGNAL",
        payload={
            "signal": "BULLISH_MOMENTUM",
            "symbol": "BTC/USD",
            "price": 50000.0,
            "confidence": "high"
        }
    )
    
    await orchestrator.handle_message(signal_msg)
    
    # Give async tasks time to complete
    await asyncio.sleep(0.5)
    
    # 4. Verify Logic
    
    # Verify Orchestrator Logic:
    # 1. Did it convert Signal to VALIDATE_ORDER? -> RiskGuardian calls message_bus with ORDER_VALIDATION_RESULT.
    # 2. Did Orchestrator log "EXECUTING ORDER"? (We verify via execution side effect if we had one, but here we only check logs manually or mocking).
    # Easier: Check if SignalBridge emitted ORDER_VALIDATION_RESULT?
    # Because process_generic_message calls signal_bridge.emit_from_agent_message on actionable types.
    # ORDER_VALIDATION_RESULT is actionable.
    
    logger.info("STEP 2: Verifying SignalBridge Broadcast...")
    
    if mock_redis_publisher.publish.called:
        logger.info(f"✅ SignalBridge published to Redis! Call count: {mock_redis_publisher.publish.call_count}")
        call_args = mock_redis_publisher.publish.call_args_list
        for i, call in enumerate(call_args):
            event = call[0][0] # First arg inside tuple
            if event['data']['metadata'].get('original_type') == 'ORDER_VALIDATION_RESULT':
                logger.info(f"  Event {i}: FOUND ORDER_VALIDATION_RESULT ✅")
                logger.info(f"    Payload: {event['data']}")
            else:
                logger.info(f"  Event {i}: {event['event_type']} (Type: {event['data']['metadata'].get('original_type')})")
    else:
        logger.error("❌ SignalBridge DID NOT publish to Redis!")
        
    # 5. Verify Message Persistence
    if mock_message_writer.enqueue.called:
        logger.info(f"✅ Message Writer enqueued {mock_message_writer.enqueue.call_count} messages.")
    else:
        logger.error("❌ Message Writer DID NOT enqueue messages!")

if __name__ == "__main__":
    asyncio.run(test_execution_flow())
