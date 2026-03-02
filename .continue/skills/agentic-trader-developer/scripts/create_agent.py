#!/usr/bin/env python3
"""
Create a new Agentic Trader agent from template.

Usage:
    python create_agent.py MyAgent --role STRATEGIST
"""

import argparse
import os
import sys
from pathlib import Path

AGENT_TEMPLATE = '''"""
{agent_name} Agent - {description}
"""

import logging
from typing import Any

from backend.agents.agent_with_tools import AgentWithTools
from backend.governance.agent_gatekeeper import AgentRole

logger = logging.getLogger(__name__)


class {agent_name}Agent(AgentWithTools):
    """
    {description}
    """

    def __init__(
        self,
        agent_name: str = "{agent_lower}",
        tool_broker_url: str | None = None,
        **kwargs
    ):
        super().__init__(
            agent_name=agent_name,
            agent_role=AgentRole.{role},
            tool_broker_url=tool_broker_url,
            **kwargs
        )
        logger.info(f"{{agent_name}} initialized")

    async def analyze(
        self,
        features: dict[str, Any],
        context: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Analyze features and return trading decision.

        Args:
            features: Market data features
            context: Additional context

        Returns:
            Trading decision dict
        """
        # TODO: Implement analysis logic

        # Example: Get VedAstro signal
        # signal = await self.get_vedastro_signal(
        #     features.get("symbol", "BTC"),
        #     features.get("price", 0.0)
        # )

        return {{
            "action": "hold",
            "confidence": 0.5,
            "reason": "Default hold - implement analysis logic"
        }}
'''

TEST_TEMPLATE = '''"""
Tests for {agent_name} Agent.
"""

import pytest

from backend.agents.{agent_lower}_agent import {agent_name}Agent


class Test{agent_name}Agent:
    """Test suite for {agent_name}Agent."""

    @pytest.fixture
    def agent(self):
        return {agent_name}Agent()

    @pytest.mark.asyncio
    async def test_analyze_returns_dict(self, agent):
        """Test that analyze returns a dict."""
        result = await agent.analyze(
            features={{"symbol": "BTC", "price": 45000}},
            context={}
        )

        assert isinstance(result, dict)
        assert "action" in result
        assert "confidence" in result

    @pytest.mark.asyncio
    async def test_default_action_is_hold(self, agent):
        """Test default action is hold."""
        result = await agent.analyze(
            features={{}},
            context={{}},
        )

        assert result["action"] == "hold"
'''


def create_agent(name: str, role: str, description: str):
    """Create agent files from template."""

    agent_lower = name.lower().replace(" ", "_")
    agent_upper = name.title().replace(" ", "")

    # Project root
    root = Path(__file__).parent.parent.parent.parent
    agents_dir = root / "backend" / "agents"
    tests_dir = root / "backend" / "tests" / "unit"

    # Check if agent already exists
    agent_file = agents_dir / f"{agent_lower}_agent.py"
    if agent_file.exists():
        print(f"ERROR: Agent file already exists: {agent_file}")
        sys.exit(1)

    # Create agent file
    agent_content = AGENT_TEMPLATE.format(
        agent_name=agent_upper,
        agent_lower=agent_lower,
        role=role.upper(),
        description=description
    )

    with open(agent_file, "w") as f:
        f.write(agent_content)

    print(f"Created: {agent_file}")

    # Create test file
    test_content = TEST_TEMPLATE.format(
        agent_name=agent_upper,
        agent_lower=agent_lower
    )

    test_file = tests_dir / f"test_{agent_lower}_agent.py"
    with open(test_file, "w") as f:
        f.write(test_content)

    print(f"Created: {test_file}")

    # Update __init__.py
    init_file = agents_dir / "__init__.py"
    with open(init_file, "r") as f:
        content = f.read()

    # Add import
    import_line = f"from backend.agents.{agent_lower}_agent import {agent_upper}Agent"
    if import_line not in content:
        # Find last import line
        lines = content.split("\n")
        import_idx = len(lines)
        for i, line in enumerate(lines):
            if line.startswith("from ") or line.startswith("import "):
                import_idx = i + 1

        lines.insert(import_idx, import_line)

        # Update __all__
        for i, line in enumerate(lines):
            if "__all__" in line:
                # Find closing bracket
                for j in range(i, len(lines)):
                    if "]" in lines[j]:
                        lines[j] = lines[j].replace(
                            "]",
                            f'    "{agent_upper}Agent",\n]'
                        )
                        break
                break

        with open(init_file, "w") as f:
            f.write("\n".join(lines))

        print(f"Updated: {init_file}")

    print(f"\n[SUCCESS] Agent '{agent_upper}Agent' created successfully!")
    print(f"\nNext steps:")
    print(f"  1. Edit {agent_file}")
    print(f"  2. Implement analyze() logic")
    print(f"  3. Run tests: pytest {test_file} -v")


def main():
    parser = argparse.ArgumentParser(
        description="Create a new Agentic Trader agent"
    )
    parser.add_argument(
        "name",
        help="Agent name (e.g., 'MyAgent')"
    )
    parser.add_argument(
        "--role",
        default="STRATEGIST",
        choices=["OBSERVER", "STRATEGIST", "EXECUTOR", "RESEARCHER"],
        help="Agent security role"
    )
    parser.add_argument(
        "--description",
        default="A trading agent",
        help="Agent description"
    )

    args = parser.parse_args()

    create_agent(args.name, args.role, args.description)


if __name__ == "__main__":
    main()
