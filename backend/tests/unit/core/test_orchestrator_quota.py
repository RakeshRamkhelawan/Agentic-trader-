from unittest.mock import AsyncMock, MagicMock

import pytest

from backend.core.auth.context import clear_context, set_current_tenant
from backend.core.exceptions import QuotaExceededError
from backend.llm.usage_tracker import UsageTracker
from backend.schemas.agent_messages import AgentMessage
from backend.services.cognitive_orchestrator import CognitiveOrchestrator


@pytest.fixture
def mock_usage_tracker():
    tracker = MagicMock(spec=UsageTracker)
    tracker.get_daily_usage = AsyncMock(return_value=5.0)  # Default $5 usage
    return tracker


@pytest.fixture
def orchestrator(mock_usage_tracker):
    orch = CognitiveOrchestrator(usage_tracker=mock_usage_tracker)
    # Mock internal components to avoid side effects
    orch.intent_monitor = MagicMock()
    orch.guna_quantifier = MagicMock()
    orch.agent_registry = MagicMock()
    orch.agent_registry.profiles = {}

    # Mock handlers that might be called
    orch.intent_monitor.monitor_balance = MagicMock()
    orch.guna_quantifier.quantify_text = MagicMock(
        return_value=MagicMock(sattva=0.1, rajas=0.1, tamas=0.1)
    )

    return orch


@pytest.fixture(autouse=True)
def clear_tenant_context():
    """Ensure context is cleared before and after each test."""
    clear_context()
    yield
    clear_context()


@pytest.mark.asyncio
async def test_quota_within_limits(orchestrator, mock_usage_tracker):
    """Test that processing proceeds when usage is within limits."""
    # Usage $5, Quota $10 (default in code)
    mock_usage_tracker.get_daily_usage.return_value = 5.0

    message = AgentMessage(
        source="user", target="research_v1", type="QUERY", payload={"text": "Hello"}
    )

    # Set tenant context
    set_current_tenant("tenant-123")

    await orchestrator.handle_message(message)

    # Verify usage check was called
    mock_usage_tracker.get_daily_usage.assert_called_once_with("tenant-123")


@pytest.mark.asyncio
async def test_quota_exceeded(orchestrator, mock_usage_tracker):
    """Test that QuotaExceededError is raised when usage exceeds quota."""
    # Usage $12, Quota $10
    mock_usage_tracker.get_daily_usage.return_value = 12.0

    message = AgentMessage(
        source="user", target="research_v1", type="QUERY", payload={"text": "Hello"}
    )

    set_current_tenant("tenant-123")

    with pytest.raises(QuotaExceededError) as exc:
        await orchestrator.handle_message(message)

    assert "Daily LLM budget exceeded" in str(exc.value)
    assert exc.value.status_code == 429
    assert exc.value.details["usage"] == 12.0


@pytest.mark.asyncio
async def test_quota_check_fails_open(orchestrator, mock_usage_tracker):
    """Test that system fails open (allows request) if tracker fails."""
    mock_usage_tracker.get_daily_usage.side_effect = Exception("DB Error")

    message = AgentMessage(
        source="user", target="research_v1", type="QUERY", payload={"text": "Hello"}
    )

    set_current_tenant("tenant-123")

    # Should NOT raise exception
    await orchestrator.handle_message(message)


@pytest.mark.asyncio
async def test_skip_quota_no_tenant(orchestrator, mock_usage_tracker):
    """Test that quota check is skipped if no tenant ID is found (system task)."""
    message = AgentMessage(
        source="system",
        target="research_v1",
        # Use a valid message type for system ticks
        type="TIMER_TICK_1MIN",
        payload={},
    )

    # No tenant context set (default None)

    await orchestrator.handle_message(message)

    mock_usage_tracker.get_daily_usage.assert_not_called()
