"""
AgentWithTools - Base class for agents that use MCP ToolBroker.

This integrates with the existing backend/mcp_broker infrastructure.
"""

import logging
import os
from typing import Any

from backend.agents.base_agent import BaseAgent
from backend.governance.agent_gatekeeper import AgentRole

logger = logging.getLogger(__name__)


class ToolBrokerClient:
    """Client for calling tools via the ToolBroker."""

    def __init__(self, http_url: str | None = None):
        self.http_url = http_url or os.getenv("MCP_BROKER_URL", "http://localhost:8001")
        self._http_client: Any = None

    async def _get_http_client(self):
        if self._http_client is None:
            import httpx
            self._http_client = httpx.AsyncClient(timeout=30.0)
        return self._http_client

    async def call_tool(
        self,
        tool_name: str,
        params: dict[str, Any],
        timeout: float = 30.0
    ) -> dict[str, Any]:
        """Call a tool via the ToolBroker."""
        try:
            client = await self._get_http_client()

            response = await client.post(
                f"{self.http_url}/tools/call",
                json={"tool_name": tool_name, "params": params, "timeout": timeout}
            )

            if response.status_code == 200:
                result = response.json()
                if result.get("success"):
                    return result.get("result", {})
                else:
                    raise Exception(f"Tool call failed: {result.get('error')}")
            else:
                raise Exception(f"HTTP {response.status_code}: {response.text}")

        except Exception as e:
            logger.error(f"Tool call failed: {tool_name} - {e}")
            raise

    async def close(self):
        if self._http_client:
            await self._http_client.aclose()


class AgentWithTools(BaseAgent):
    """
    Base agent with ToolBroker integration.

    Extends BaseAgent with the ability to call tools via the ToolBroker.
    """

    def __init__(
        self,
        agent_name: str,
        llm_provider: Any | None = None,
        event_bus: Any | None = None,
        agent_role: AgentRole = AgentRole.STRATEGIST,
        tool_broker_url: str | None = None,
        max_reasoning_history: int = 1000,
        max_event_buffer: int = 10000,
    ):
        super().__init__(
            agent_name=agent_name,
            llm_provider=llm_provider,
            event_bus=event_bus,
            agent_role=agent_role,
            max_reasoning_history=max_reasoning_history,
            max_event_buffer=max_event_buffer,
        )

        self.tool_broker = ToolBrokerClient(http_url=tool_broker_url)
        self._tool_cache: dict[str, Any] = {}

        logger.info(f"{agent_name} initialized with ToolBroker support")

    async def call_tool(
        self,
        tool_name: str,
        params: dict[str, Any],
        cache_result: bool = False,
        timeout: float = 30.0,
    ) -> dict[str, Any]:
        """Call a tool via the ToolBroker."""
        cache_key = f"{tool_name}:{hash(str(params))}"
        if cache_result and cache_key in self._tool_cache:
            return self._tool_cache[cache_key]

        try:
            result = await self.tool_broker.call_tool(tool_name, params, timeout)

            if cache_result:
                self._tool_cache[cache_key] = result

            self.record_activity(success=True)
            return result

        except Exception:
            self.record_activity(success=False)
            raise

    # Convenience methods
    async def get_vedastro_signal(self, symbol: str, current_price: float) -> dict:
        """Get VedAstro trading signal."""
        return await self.call_tool(
            "vedastro__generate_signal",
            {"symbol": symbol, "current_price": current_price}
        )

    async def get_elemental_consensus(self, fire_vote: float, earth_vote: float,
                                     water_vote: float, air_vote: float) -> dict:
        """Get elemental consensus."""
        return await self.call_tool(
            "elemental__ether_consensus",
            {"fire_vote": fire_vote, "earth_vote": earth_vote,
             "water_vote": water_vote, "air_vote": air_vote}
        )

    async def close(self):
        """Close agent and cleanup resources."""
        await self.tool_broker.close()

    async def analyze(self, features: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
        """
        Analyze features and context using available tools.

        This is the main entry point for agent analysis. Subclasses should
        override this method with their specific analysis logic, using
        `call_tool()` to invoke MCP tools.

        Default implementation raises NotImplementedError - must be overridden.

        Args:
            features: Feature data for analysis
            context: Additional context for decision making

        Returns:
            Analysis result dict

        Example:
            async def analyze(self, features, context):
                signal = await self.get_vedastro_signal(
                    features["symbol"], features["price"]
                )
                return {"action": "buy", "confidence": signal["confidence"]}
        """
        raise NotImplementedError(
            "Subclasses must implement analyze(). "
            "Use call_tool() to invoke MCP tools from your analysis."
        )
