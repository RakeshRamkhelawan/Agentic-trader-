
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from backend.services.cognitive_orchestrator import CognitiveOrchestrator
from backend.schemas.agent_messages import AgentMessage
from backend.core.auth.context import get_current_tenant_optional

@pytest.mark.asyncio
async def test_orchestrator_propagates_tenant_context_from_message():
    # Setup
    mock_registry = MagicMock()
    mock_quantifier = MagicMock()
    mock_tracker = MagicMock()
    
    # Mock vector
    mock_vector = MagicMock()
    mock_vector.to_dict.return_value = {"sattva": 0.3, "rajas": 0.3, "tamas": 0.4}
    mock_vector.sattva = 0.3; mock_vector.rajas = 0.3; mock_vector.tamas = 0.4
    mock_quantifier.quantify_text.return_value = mock_vector
    
    orchestrator = CognitiveOrchestrator(
        agent_registry=mock_registry,
        guna_quantifier=mock_quantifier,
        usage_tracker=mock_tracker
    )
    
    # Mock _check_quota to verify context
    orchestrator._check_quota = AsyncMock()
    
    # Message with tenant_id
    msg = AgentMessage(
        source="agent-A",
        target="agent-B",
        type="SIGNAL",
        payload={"text": "hello"},
        tenant_id="tenant-TEST-123"
    )
    
    # Spy on internal context check
    # We define a side effect for _check_quota that checks the global context var
    async def check_quota_side_effect(tid):
        # At this point, context var should be set
        current = get_current_tenant_optional()
        assert current == "tenant-TEST-123", f"Context was {current}, expected tenant-TEST-123"
        return
        
    orchestrator._check_quota.side_effect = check_quota_side_effect
    
    # Act
    await orchestrator.handle_message(msg)
    
    # Assert
    orchestrator._check_quota.assert_called_once_with("tenant-TEST-123")

@pytest.mark.asyncio
async def test_orchestrator_uses_existing_context_if_message_has_none():
    # Setup
    mock_registry = MagicMock()
    mock_quantifier = MagicMock()
    mock_vector = MagicMock()
    mock_vector.to_dict.return_value = {"sattva": 0.3, "rajas": 0.3, "tamas": 0.4}
    mock_vector.sattva = 0.3; mock_vector.rajas = 0.3; mock_vector.tamas = 0.4
    mock_quantifier.quantify_text.return_value = mock_vector
    
    orchestrator = CognitiveOrchestrator(
        agent_registry=mock_registry,
        guna_quantifier=mock_quantifier
    )
    orchestrator._check_quota = AsyncMock()
    
    msg = AgentMessage(
        source="agent-A",
        target="agent-B",
        type="SIGNAL",
        payload={"text": "hello"},
        tenant_id=None # No tenant in message
    )
    
    # Set context directly
    from backend.core.auth.context import set_current_tenant, clear_context
    set_current_tenant("existing-tenant")
    
    try:
         await orchestrator.handle_message(msg)
    finally:
         clear_context()
         
    # Assert
    orchestrator._check_quota.assert_called_once_with("existing-tenant")
         
    # Assert
    # Logic: effective_tenant = msg.tenant_id or get_current_context()
    # It should use "existing-tenant"
    orchestrator._check_quota.assert_called_once_with("existing-tenant")
