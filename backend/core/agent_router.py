"""
Agent Router - Categorizes agents by latency requirements and routes to optimal LLM path.

Agent Categories:
- HOT PATH (Real-time): Risk checks, order validation, execution (< 100ms)
- FAST PATH: UI updates, quick sentiment (< 500ms)
- STANDARD PATH: Analysis, research, reports (> 2s) - USES OLLAMA GPU
- BATCH PATH: Backtesting, bulk analysis - USES OLLAMA GPU
"""

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any

from backend.llm.gateway import LatencyRequirement, LLMGateway, LLMRequest

logger = logging.getLogger(__name__)


class AgentCategory(Enum):
    """Agent execution categories."""

    HOT_PATH = "hot_path"  # Real-time trading decisions
    FAST_PATH = "fast_path"  # Quick responses
    STANDARD_PATH = "standard_path"  # Analysis (Ollama)
    BATCH_PATH = "batch_path"  # Bulk processing (Ollama)


@dataclass
class AgentProfile:
    """Agent routing profile."""

    agent_id: str
    name: str
    category: AgentCategory
    default_latency: LatencyRequirement
    preferred_ollama_model: str | None = None
    can_use_cloud: bool = True
    can_use_local: bool = True
    batch_size: int = 1  # For batch processing


class AgentRouter:
    """
    Routes agent requests to optimal LLM path.

    Design Philosophy:
    - Hot Path: Cloud APIs (consistent low latency)
    - Standard/Batch: Ollama GPU (cost-free, unlimited)
    """

    # Predefined agent profiles
    DEFAULT_PROFILES = {
        # Hot Path Agents - Fast cloud APIs
        "risk_guardian_v1": AgentProfile(
            agent_id="risk_guardian_v1",
            name="Risk Guardian",
            category=AgentCategory.HOT_PATH,
            default_latency=LatencyRequirement.REALTIME,
            can_use_cloud=True,
            can_use_local=False,  # Too slow for risk checks
        ),
        "execution_v1": AgentProfile(
            agent_id="execution_v1",
            name="Execution Agent",
            category=AgentCategory.HOT_PATH,
            default_latency=LatencyRequirement.REALTIME,
            can_use_cloud=True,
            can_use_local=False,
        ),
        # Fast Path Agents - Cloud preferred, local fallback
        "news_v1": AgentProfile(
            agent_id="news_v1",
            name="News Agent",
            category=AgentCategory.FAST_PATH,
            default_latency=LatencyRequirement.FAST,
            can_use_cloud=True,
            can_use_local=True,
        ),
        "macro_v1": AgentProfile(
            agent_id="macro_v1",
            name="Macro Agent",
            category=AgentCategory.FAST_PATH,
            default_latency=LatencyRequirement.FAST,
            can_use_cloud=True,
            can_use_local=True,
        ),
        # Standard Path - Ollama GPU optimal (RTX 4090 8GB)
        "sentiment_v1": AgentProfile(
            agent_id="sentiment_v1",
            name="Sentiment Agent",
            category=AgentCategory.STANDARD_PATH,
            default_latency=LatencyRequirement.STANDARD,
            preferred_ollama_model="deepseek-r1:7b",  # 4.7GB
            can_use_cloud=False,  # Force local for cost savings
            can_use_local=True,
        ),
        "research_v1": AgentProfile(
            agent_id="research_v1",
            name="Research Agent",
            category=AgentCategory.STANDARD_PATH,
            default_latency=LatencyRequirement.STANDARD,
            preferred_ollama_model="deepseek-r1:7b",  # 4.7GB - fits in 8GB VRAM
            can_use_cloud=True,
            can_use_local=True,
        ),
        "valuation_v1": AgentProfile(
            agent_id="valuation_v1",
            name="Valuation Agent",
            category=AgentCategory.STANDARD_PATH,
            default_latency=LatencyRequirement.STANDARD,
            preferred_ollama_model="deepseek-r1:7b",  # 4.7GB
            can_use_cloud=True,
            can_use_local=True,
        ),
        # Batch Path - Ollama GPU, bulk processing (RTX 4090 8GB)
        "asset_discovery_v1": AgentProfile(
            agent_id="asset_discovery_v1",
            name="Asset Discovery",
            category=AgentCategory.BATCH_PATH,
            default_latency=LatencyRequirement.BATCH,
            preferred_ollama_model="phi3:mini",  # 2.2GB - small & fast
            can_use_cloud=False,
            can_use_local=True,
            batch_size=10,
        ),
        "backtest_v1": AgentProfile(
            agent_id="backtest_v1",
            name="Backtest Agent",
            category=AgentCategory.BATCH_PATH,
            default_latency=LatencyRequirement.BATCH,
            preferred_ollama_model="deepseek-r1:7b",  # 4.7GB - fits in 8GB
            can_use_cloud=False,
            can_use_local=True,
            batch_size=50,
        ),
    }

    def __init__(self, llm_gateway: LLMGateway):
        self.gateway = llm_gateway
        self.profiles: dict[str, AgentProfile] = dict(self.DEFAULT_PROFILES)

    def register_agent(self, profile: AgentProfile):
        """Register or update agent profile."""
        self.profiles[profile.agent_id] = profile
        logger.info(f"Registered agent {profile.name} as {profile.category.value}")

    def get_profile(self, agent_id: str) -> AgentProfile | None:
        """Get agent routing profile."""
        return self.profiles.get(agent_id)

    async def route_request(
        self,
        agent_id: str,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.3,
        max_tokens: int = 500,
        json_mode: bool = False,
    ) -> str:
        """
        Route LLM request for agent to optimal path.
        """
        profile = self.get_profile(agent_id)
        if not profile:
            # Default to standard path for unknown agents
            profile = AgentProfile(
                agent_id=agent_id,
                name=agent_id,
                category=AgentCategory.STANDARD_PATH,
                default_latency=LatencyRequirement.STANDARD,
                can_use_cloud=True,
                can_use_local=True,
            )

        # Determine optimal provider based on profile
        force_provider = None
        if not profile.can_use_cloud and profile.can_use_local:
            force_provider = LLMGateway.LLMProvider.OLLAMA_LOCAL
        elif not profile.can_use_local and profile.can_use_cloud:
            # Use cloud (first available)
            force_provider = None  # Let gateway decide

        request = LLMRequest(
            prompt=prompt,
            latency_requirement=profile.default_latency,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            json_mode=json_mode,
        )

        response = await self.gateway.generate(request, force_provider)

        logger.debug(
            f"Agent {agent_id}: {response.provider.value} " f"({response.latency_ms:.0f}ms)"
        )

        return response.content

    async def route_batch(
        self,
        agent_id: str,
        prompts: list[str],
        system_prompt: str | None = None,
    ) -> list[str]:
        """
        Batch route requests (ideal for Ollama GPU batching).
        """
        profile = self.get_profile(agent_id)
        if not profile:
            profile = self.profiles.get("backtest_v1")  # Use batch defaults

        requests = [
            LLMRequest(
                prompt=prompt,
                latency_requirement=profile.default_latency,
                system_prompt=system_prompt,
            )
            for prompt in prompts
        ]

        responses = await self.gateway.batch_generate(
            requests, max_concurrency=profile.batch_size if profile else 4
        )

        results = []
        for resp in responses:
            if isinstance(resp, Exception):
                logger.error(f"Batch request failed: {resp}")
                results.append("")
            else:
                results.append(resp.content)

        return results

    def get_agent_stats(self, agent_id: str) -> dict[str, Any]:
        """Get routing statistics for agent."""
        profile = self.get_profile(agent_id)
        if not profile:
            return {}

        return {
            "agent_id": agent_id,
            "category": profile.category.value,
            "latency_requirement": profile.default_latency.value,
            "can_use_cloud": profile.can_use_cloud,
            "can_use_local": profile.can_use_local,
            "preferred_model": profile.preferred_ollama_model,
        }

    def get_category_summary(self) -> dict[str, list[str]]:
        """Get summary of agents by category."""
        summary = {
            "hot_path": [],
            "fast_path": [],
            "standard_path": [],
            "batch_path": [],
        }
        for profile in self.profiles.values():
            summary[profile.category.value].append(profile.name)
        return summary
