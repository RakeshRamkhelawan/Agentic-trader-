"""
MCP ToolBroker Module.

Provides tool execution services for agents via the Model Context Protocol (MCP).
"""

from backend.mcp_broker.client import (
    MCPClientWrapper,
    SynchronousMCPClient,
    check_entry_allowed,
    check_exit_needed,
    execute_paper_trade,
    get_client,
    get_elemental_consensus,
    get_position_size,
    get_vedastro_signal,
    close_global_client,
)

__all__ = [
    "MCPClientWrapper",
    "SynchronousMCPClient",
    "get_elemental_consensus",
    "get_position_size",
    "check_entry_allowed",
    "check_exit_needed",
    "get_vedastro_signal",
    "execute_paper_trade",
    "get_client",
    "close_global_client",
]
