"""
Agent Gatekeeper - Authorization for agent-specific tool access.

Enforces permissions based on AgentRole to prevent unauthorized
service or tool invocation by automated agents.
"""

import logging
from enum import Enum
from typing import Set, Dict, Optional

logger = logging.getLogger(__name__)


class ToolPermission(str, Enum):
    """Permissions for sensitive tools and services."""

    READ_MARKET_DATA = "tool:read_market_data"
    GENERATE_STRATEGY = "tool:generate_strategy"
    ASSESS_RISK = "tool:assess_risk"
    TRADE_EXECUTION = "tool:trade_execution"
    ACCESS_VAULT = "tool:access_vault"


class AgentRole(str, Enum):
    """Roles assigned to agents to define their capabilities."""

    OBSERVER = "observer"
    STRATEGIST = "strategist"
    EXECUTOR = "executor"
    RESEARCHER = "researcher"
    UNTRUSTED = "untrusted"


# Role -> Permissions mapping
ROLE_PERMISSIONS: Dict[AgentRole, Set[ToolPermission]] = {
    AgentRole.OBSERVER: {ToolPermission.READ_MARKET_DATA},
    AgentRole.STRATEGIST: {
        ToolPermission.READ_MARKET_DATA,
        ToolPermission.GENERATE_STRATEGY,
        ToolPermission.ASSESS_RISK,
    },
    AgentRole.EXECUTOR: {
        ToolPermission.READ_MARKET_DATA,
        ToolPermission.TRADE_EXECUTION,
    },
    AgentRole.RESEARCHER: {
        ToolPermission.READ_MARKET_DATA,
        ToolPermission.GENERATE_STRATEGY,
    },
    AgentRole.UNTRUSTED: set(),
}


class AgentGatekeeper:
    """
    Gatekeeper service to authorize agent actions.
    """

    def __init__(
        self,
        override_permissions: Optional[Dict[AgentRole, Set[ToolPermission]]] = None,
    ):
        """
        Initialize AgentGatekeeper.

        Args:
            override_permissions: Optional custom role mapping for testing/overrides.
        """
        self.permissions = override_permissions or ROLE_PERMISSIONS

    def authorize(
        self,
        agent_name: str,
        agent_role: AgentRole,
        required_permission: ToolPermission,
    ) -> bool:
        """
        Authorize an agent to perform a specific action.

        Args:
            agent_name: Name of the agent (for logging)
            agent_role: Role assigned to the agent
            required_permission: The permission required for the action

        Returns:
            bool: True if authorized, False otherwise
        """
        allowed_permissions = self.permissions.get(agent_role, set())

        if required_permission in allowed_permissions:
            logger.debug(
                f"Authorization GRANTED: {agent_name} ({agent_role}) -> {required_permission}"
            )
            return True

        logger.warning(
            f"Authorization DENIED: {agent_name} ({agent_role}) lacks {required_permission}"
        )
        return False

    def require_permission(
        self,
        agent_name: str,
        agent_role: AgentRole,
        required_permission: ToolPermission,
    ):
        """
        Enforce a permission check, raising an exception if unauthorized.

        Args:
            agent_name: Name of the agent
            agent_role: Role assigned to the agent
            required_permission: The permission required for the action

        Raises:
            PermissionError: If authorization fails.
        """
        if not self.authorize(agent_name, agent_role, required_permission):
            raise PermissionError(
                f"Agent '{agent_name}' with role '{agent_role}' is not authorized for {required_permission}"
            )
