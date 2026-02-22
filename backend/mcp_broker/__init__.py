"""
MCP Broker - Model Context Protocol integration for Agentic Trader.

Provides:
- MCP Server with 16 registered tools
- MCP Client for tool invocation
- Backtest engines (standard and optimized)
- Resilience patterns (circuit breaker, retry)
- Performance optimizations (caching, batching, parallel)
"""

from backend.mcp_broker.server import mcp
from backend.mcp_broker.client import (
    MCPClientWrapper,
    SynchronousMCPClient,
    get_elemental_consensus,
    get_position_size,
    check_entry_allowed,
    check_exit_needed,
    get_vedastro_signal,
    execute_paper_trade
)

# Optional imports - only if performance module is available
try:
    from backend.mcp_broker.backtest_engine_v18 import (
        BacktestConfig,
        BacktestEngineV18,
        run_backtest_v18
    )
    from backend.mcp_broker.backtest_engine_v18_optimized import (
        OptimizedBacktestConfig,
        OptimizedBacktestEngineV18,
        run_optimized_backtest
    )
    from backend.mcp_broker.elemental_manager_v18 import (
        ElementalAgentManagerV18,
        get_elemental_manager_v18
    )
    V18_AVAILABLE = True
except ImportError:
    V18_AVAILABLE = False

__version__ = "18.1.0"

__all__ = [
    # Server
    "mcp",

    # Client
    "MCPClientWrapper",
    "SynchronousMCPClient",
    "get_elemental_consensus",
    "get_position_size",
    "check_entry_allowed",
    "check_exit_needed",
    "get_vedastro_signal",
    "execute_paper_trade",
]

# Conditionally add V18 exports
if V18_AVAILABLE:
    __all__.extend([
        # Backtest Engines
        "BacktestConfig",
        "BacktestEngineV18",
        "run_backtest_v18",
        "OptimizedBacktestConfig",
        "OptimizedBacktestEngineV18",
        "run_optimized_backtest",

        # Elemental Manager
        "ElementalAgentManagerV18",
        "get_elemental_manager_v18",
    ])
