import pytest

from backend.governance.agent_gatekeeper import AgentGatekeeper, AgentRole, ToolPermission


def test_agent_gatekeeper_authorize_success():
    gatekeeper = AgentGatekeeper()

    # Trader should have TRADE_EXECUTION
    assert (
        gatekeeper.authorize("Trader", AgentRole.STRATEGIST, ToolPermission.GENERATE_STRATEGY)
        is True
    )
    assert (
        gatekeeper.authorize("Trader", AgentRole.STRATEGIST, ToolPermission.READ_MARKET_DATA)
        is True
    )


def test_agent_gatekeeper_authorize_denied():
    gatekeeper = AgentGatekeeper()

    # DataScout should NOT have TRADE_EXECUTION
    assert (
        gatekeeper.authorize("DataScout", AgentRole.OBSERVER, ToolPermission.TRADE_EXECUTION)
        is False
    )

    # Untrusted should have nothing
    assert (
        gatekeeper.authorize("MaliciousAgent", AgentRole.UNTRUSTED, ToolPermission.READ_MARKET_DATA)
        is False
    )


def test_agent_gatekeeper_require_permission_raises():
    gatekeeper = AgentGatekeeper()

    with pytest.raises(PermissionError) as excinfo:
        gatekeeper.require_permission(
            "DataScout", AgentRole.OBSERVER, ToolPermission.TRADE_EXECUTION
        )

    assert "TRADE_EXECUTION" in str(excinfo.value)


def test_agent_gatekeeper_custom_permissions():
    custom_perms = {AgentRole.UNTRUSTED: {ToolPermission.READ_MARKET_DATA}}
    gatekeeper = AgentGatekeeper(override_permissions=custom_perms)

    assert (
        gatekeeper.authorize(
            "TrustedUntrusted", AgentRole.UNTRUSTED, ToolPermission.READ_MARKET_DATA
        )
        is True
    )
    assert (
        gatekeeper.authorize(
            "TrustedUntrusted", AgentRole.UNTRUSTED, ToolPermission.TRADE_EXECUTION
        )
        is False
    )
