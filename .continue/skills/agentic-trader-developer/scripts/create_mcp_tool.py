#!/usr/bin/env python3
"""
Create a new MCP tool for the Agentic Trader platform.

Usage:
    python create_mcp_tool.py my_tool --category data
"""

import argparse
import os
import sys
from pathlib import Path

TOOL_TEMPLATE = '''"""
{tool_name} MCP Tool.
"""

import logging
from typing import Any

from backend.mcp_broker.resilience import circuit_breaker, retry

logger = logging.getLogger(__name__)


@circuit_breaker(failure_threshold=5, timeout_seconds=30)
@retry(max_attempts=3)
async def {tool_func}(
    param1: str,
    param2: float,
    ctx=None
) -> dict[str, Any]:
    """
    Brief description of what this tool does.

    Args:
        param1: Description of param1
        param2: Description of param2
        ctx: MCP context for logging

    Returns:
        Dictionary with results
    """
    if ctx:
        ctx.info(f"Processing {{param1}} with {{param2}}")

    try:
        # TODO: Implement tool logic
        result = {{"processed": param1, "value": param2}}

        return {{
            "success": True,
            "result": result,
        }}
    except Exception as e:
        logger.error(f"{tool_name} failed: {{e}}")
        return {{
            "success": False,
            "error": str(e),
        }}
'''

SERVER_REGISTRATION = '''
# Add to backend/mcp_broker/server.py:

from backend.mcp_broker.tools.{tool_file} import {tool_func}

@mcp.tool(name="{category}__{tool_name}")
async def {tool_func}_wrapper(
    param1: str,
    param2: float,
    ctx: Context = None
) -> dict:
    """Wrapper for {tool_name} tool."""
    return await {tool_func}(param1, param2, ctx)
'''


def create_tool(name: str, category: str):
    """Create MCP tool files."""

    tool_lower = name.lower().replace(" ", "_")
    tool_upper = name.title().replace(" ", "")
    tool_func = f"{tool_lower}_tool"

    # Project root
    root = Path(__file__).parent.parent.parent.parent
    tools_dir = root / "backend" / "mcp_broker" / "tools"

    # Create or append to category file
    tool_file = tools_dir / f"{category}_tools.py"

    tool_content = TOOL_TEMPLATE.format(
        tool_name=tool_upper,
        tool_func=tool_func
    )

    if tool_file.exists():
        # Append to existing file
        with open(tool_file, "a") as f:
            f.write("\n\n")
            f.write(tool_content)
        print(f"Appended to: {tool_file}")
    else:
        # Create new file
        with open(tool_file, "w") as f:
            f.write(tool_content)
        print(f"Created: {tool_file}")

    # Print registration code
    print("\n" + "="*60)
    print("Add this to backend/mcp_broker/server.py:")
    print("="*60)
    print(SERVER_REGISTRATION.format(
        tool_file=f"{category}_tools",
        tool_func=tool_func,
        tool_name=tool_lower,
        category=category
    ))

    print("\n" + "="*60)
    print("Usage from AgentWithTools:")
    print("="*60)
    print(f'''
result = await self.call_tool(
    "{category}__{tool_name}",
    {{"param1": "value", "param2": 0.5}}
)
''')


def main():
    parser = argparse.ArgumentParser(
        description="Create a new MCP tool"
    )
    parser.add_argument(
        "name",
        help="Tool name (e.g., 'get_price')"
    )
    parser.add_argument(
        "--category",
        default="data",
        choices=["data", "elemental", "execution", "vedastro", "external"],
        help="Tool category"
    )

    args = parser.parse_args()

    create_tool(args.name, args.category)


if __name__ == "__main__":
    main()
