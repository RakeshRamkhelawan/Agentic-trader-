"""
Monitoring MCP Tools.

Metrics, alerts, and platform health monitoring.
"""

import logging
from typing import Any

from backend.mcp_broker.resilience import circuit_breaker

logger = logging.getLogger(__name__)


@circuit_breaker(failure_threshold=5, timeout_seconds=10)
async def monitoring_get_metrics(ctx=None) -> dict[str, Any]:
    """
    Get current trading metrics summary.

    Args:
        ctx: MCP context

    Returns:
        Metrics summary
    """
    if ctx:
        ctx.info("Fetching trading metrics")

    try:

        # Note: This is a simplified summary - in production, you'd query Prometheus
        metrics = {
            "timestamp": datetime.utcnow().isoformat(),
            "orders": {
                "total_count": "See Prometheus: trading_orders_total",
                "by_status": {
                    "filled": "Query: sum(trading_orders_total{status='filled'})",
                    "pending": "Query: sum(trading_orders_total{status='pending'})",
                    "cancelled": "Query: sum(trading_orders_total{status='cancelled'})",
                },
            },
            "exchanges": {
                "bitvavo": {
                    "status": "Query: trading_exchange_up{exchange='bitvavo'}",
                    "latency": "Query: trading_exchange_latency_seconds{exchange='bitvavo'}",
                },
                "revolutx": {
                    "status": "Query: trading_exchange_up{exchange='revolutx'}",
                    "latency": "Query: trading_exchange_latency_seconds{exchange='revolutx'}",
                },
            },
            "prometheus_url": "http://localhost:9090",
            "grafana_url": "http://localhost:3000",
        }

        return {
            "success": True,
            "metrics": metrics,
            "note": "Full metrics available in Prometheus/Grafana",
        }

    except Exception as e:
        logger.error(f"Metrics fetch failed: {e}")
        return {"success": False, "error": str(e)}


@circuit_breaker(failure_threshold=3, timeout_seconds=10)
async def monitoring_get_alerts(severity: str | None = None, ctx=None) -> dict[str, Any]:
    """
    Get active alerts.

    Args:
        severity: Filter by severity (critical, warning, info)
        ctx: MCP context

    Returns:
        Active alerts
    """
    if ctx:
        ctx.info(f"Fetching alerts (severity: {severity or 'all'})")

    try:
        from backend.observability.trading_metrics import alert_manager

        alerts = alert_manager.get_active_alerts(severity)

        return {
            "success": True,
            "alerts": alerts,
            "count": len(alerts),
            "severities": {
                "critical": len([a for a in alerts if a["severity"] == "critical"]),
                "warning": len([a for a in alerts if a["severity"] == "warning"]),
                "info": len([a for a in alerts if a["severity"] == "info"]),
            },
        }

    except Exception as e:
        logger.error(f"Alerts fetch failed: {e}")
        return {"success": False, "error": str(e)}


@circuit_breaker(failure_threshold=3, timeout_seconds=10)
async def monitoring_acknowledge_alert(alert_id: str, ctx=None) -> dict[str, Any]:
    """
    Acknowledge an alert.

    Args:
        alert_id: Alert ID to acknowledge
        ctx: MCP context

    Returns:
        Acknowledgment result
    """
    if ctx:
        ctx.info(f"Acknowledging alert: {alert_id}")

    try:
        from backend.observability.trading_metrics import alert_manager

        success = alert_manager.acknowledge_alert(alert_id)

        if success:
            return {
                "success": True,
                "alert_id": alert_id,
                "status": "acknowledged",
            }
        else:
            return {
                "success": False,
                "alert_id": alert_id,
                "error": "Alert not found or already acknowledged",
            }

    except Exception as e:
        logger.error(f"Alert acknowledgment failed: {e}")
        return {"success": False, "error": str(e)}


@circuit_breaker(failure_threshold=5, timeout_seconds=10)
async def monitoring_get_health(ctx=None) -> dict[str, Any]:
    """
    Get comprehensive platform health status.

    Args:
        ctx: MCP context

    Returns:
        Health status of all components
    """
    if ctx:
        ctx.info("Checking platform health")

    try:
        health = {
            "timestamp": datetime.utcnow().isoformat(),
            "components": {},
        }

        # Check exchanges
        from backend.execution.live_multi_exchange_trading import (
            get_live_trading_service,
        )

        trading = await get_live_trading_service()
        stats = trading.get_stats()

        health["components"]["exchanges"] = {
            "status": "healthy" if len(stats["active_exchanges"]) >= 1 else "degraded",
            "active": stats["active_exchanges"],
            "count": len(stats["active_exchanges"]),
        }

        # Check MCP broker
        from backend.mcp_broker.server import mcp

        tools = await mcp.list_tools()
        health["components"]["mcp_broker"] = {
            "status": "healthy",
            "registered_tools": len(tools),
        }

        # Overall status
        all_healthy = all(
            c["status"] in ["healthy", "ok"]
            for c in health["components"].values()
        )
        health["overall_status"] = "healthy" if all_healthy else "degraded"

        return {
            "success": True,
            "health": health,
        }

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "overall_status": "unhealthy",
        }


@circuit_breaker(failure_threshold=3, timeout_seconds=10)
async def monitoring_get_performance_summary(ctx=None) -> dict[str, Any]:
    """
    Get trading performance summary.

    Args:
        ctx: MCP context

    Returns:
        Performance metrics
    """
    if ctx:
        ctx.info("Generating performance summary")

    try:
        from backend.execution.live_multi_exchange_trading import (
            get_live_trading_service,
        )

        trading = await get_live_trading_service()
        stats = trading.get_stats()

        summary = {
            "timestamp": datetime.utcnow().isoformat(),
            "trading_stats": stats,
            "metrics": {
                "total_orders": stats.get("total_orders", 0),
                "open_orders": stats.get("open_orders", 0),
                "tracked_positions": stats.get("tracked_positions", 0),
            },
            "risk_limits": stats.get("risk_limits", {}),
        }

        return {
            "success": True,
            "summary": summary,
        }

    except Exception as e:
        logger.error(f"Performance summary failed: {e}")
        return {"success": False, "error": str(e)}


@circuit_breaker(failure_threshold=3, timeout_seconds=10)
async def monitoring_export_data(
    start_date: str,
    end_date: str,
    format: str = "json",
    ctx=None,
) -> dict[str, Any]:
    """
    Export trading data for analysis.

    Args:
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        format: Export format (json, csv)
        ctx: MCP context

    Returns:
        Export result
    """
    if ctx:
        ctx.info(f"Exporting data from {start_date} to {end_date}")

    # Placeholder - real implementation would query database
    return {
        "success": True,
        "export": {
            "start_date": start_date,
            "end_date": end_date,
            "format": format,
            "status": "generated",
            "note": "Data export is a placeholder - implement with actual database queries",
        },
    }


from datetime import datetime
