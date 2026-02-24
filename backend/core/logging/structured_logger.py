"""
Enterprise Structured Logging voor Paper Trading Pipeline.

Elke log-statement is JSON-parseerbaar voor observability.
"""

import json
import logging
from datetime import UTC, datetime
from typing import Any


class StructuredLogger:
    """
    Enterprise structured logging — elke log is JSON-parseerbaar.

    Usage:
        logger = StructuredLogger("my_service", trading_mode="paper")
        logger.log_trade_event("order_filled", {"symbol": "BTC/EUR", "qty": 0.001})
    """

    def __init__(self, service_name: str, trading_mode: str = "paper"):
        self.service_name = service_name
        self.trading_mode = trading_mode
        self._logger = logging.getLogger(service_name)

    def _create_log_entry(
        self, event_type: str, data: dict[str, Any], level: str = "info"
    ) -> dict[str, Any]:
        """Create a structured log entry."""
        return {
            "timestamp": datetime.now(UTC).isoformat() + "Z",
            "service": self.service_name,
            "trading_mode": self.trading_mode,
            "event_type": event_type,
            "simulated": self.trading_mode == "paper",
            **data,
        }

    def _log(self, level: str, event_type: str, data: dict[str, Any]):
        """Log a structured entry."""
        entry = self._create_log_entry(event_type, data, level)

        # Log als JSON string
        log_method = getattr(self._logger, level.lower(), self._logger.info)
        log_method(json.dumps(entry, default=str))

        return entry

    def log_trade_event(
        self, event_type: str, data: dict[str, Any], level: str = "info"
    ) -> dict[str, Any]:
        """Log een trade event."""
        return self._log(level, event_type, data)

    def log_vedic_event(
        self,
        event_type: str,
        soul_context: dict[str, Any],
        harmony: float | None = None,
        level: str = "info",
    ) -> dict[str, Any]:
        """Log een Vedic cycle event."""
        data = {
            "vedic_event": event_type,
            "rahu_kala": soul_context.get("rahu_kala_active"),
            "market_regime": soul_context.get("market_regime"),
            "trading_gate_open": soul_context.get("trading_gate_open"),
        }

        if harmony is not None:
            data["harmony_score"] = harmony

        return self._log(level, "vedic_cycle", data)

    def log_agent_decision(
        self,
        agent: str,
        element: str,
        decision: dict[str, Any],
        prana: float,
        level: str = "info",
    ) -> dict[str, Any]:
        """Log een agent beslissing."""
        data = {
            "agent": agent,
            "element": element,
            "decision": decision,
            "prana_level": prana,
            "prana_status": "nominal" if prana >= 10 else "depleted",
        }

        return self._log(level, "agent_decision", data)


def get_structured_logger(service_name: str, trading_mode: str = "paper") -> StructuredLogger:
    """Get a structured logger instance."""
    return StructuredLogger(service_name, trading_mode)
