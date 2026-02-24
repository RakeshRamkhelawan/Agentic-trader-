"""MCP Tools for Agentic Trader Platform."""

from .elemental_tools import (
    elemental_fire_position_size,
    elemental_earth_entry_check,
    elemental_earth_exit_check,
    elemental_water_regime_check,
    elemental_ether_consensus,
)
from .vedastro_tools import (
    vedastro_generate_signal,
    vedastro_get_dasha,
    vedastro_get_transits,
)
from .data_tools import (
    data_get_historical_prices,
    data_get_portfolio_status,
    data_get_market_regime,
)
from .execution_tools import (
    execution_execute_paper_trade,
    execution_get_open_positions,
    execution_close_position,
    execution_get_trade_history,
)

__all__ = [
    # Elemental tools
    "elemental_fire_position_size",
    "elemental_earth_entry_check",
    "elemental_earth_exit_check",
    "elemental_water_regime_check",
    "elemental_ether_consensus",
    # VedAstro tools
    "vedastro_generate_signal",
    "vedastro_get_dasha",
    "vedastro_get_transits",
    # Data tools
    "data_get_historical_prices",
    "data_get_portfolio_status",
    "data_get_market_regime",
    # Execution tools
    "execution_execute_paper_trade",
    "execution_get_open_positions",
    "execution_close_position",
    "execution_get_trade_history",
]
