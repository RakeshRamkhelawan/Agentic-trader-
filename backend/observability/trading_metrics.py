"""
Trading Metrics Exporter

Comprehensive metrics for live trading monitoring:
- Order execution metrics
- Position tracking
- P&L analytics
- Exchange health
- Risk metrics
"""

import logging
from datetime import datetime
from typing import Any

from prometheus_client import Counter, Gauge, Histogram, Info

logger = logging.getLogger(__name__)


class TradingMetrics:
    """
    Prometheus metrics for live multi-exchange trading.
    """

    # Order metrics
    orders_total = Counter(
        "trading_orders_total",
        "Total orders by exchange, symbol, side, and status",
        ["exchange", "symbol", "side", "status"],
    )

    orders_value_eur = Counter(
        "trading_orders_value_eur_total",
        "Total order value in EUR",
        ["exchange", "symbol", "side"],
    )

    order_latency_seconds = Histogram(
        "trading_order_latency_seconds",
        "Order execution latency",
        ["exchange", "order_type"],
        buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0],
    )

    # Position metrics
    position_size = Gauge(
        "trading_position_size",
        "Current position size by symbol and exchange",
        ["symbol", "exchange"],
    )

    position_value_eur = Gauge(
        "trading_position_value_eur",
        "Current position value in EUR",
        ["symbol", "exchange"],
    )

    # P&L metrics
    realized_pnl_eur = Counter(
        "trading_realized_pnl_eur_total",
        "Realized P&L in EUR",
        ["symbol", "exchange"],
    )

    unrealized_pnl_eur = Gauge(
        "trading_unrealized_pnl_eur",
        "Unrealized P&L in EUR",
        ["symbol", "exchange"],
    )

    # Exchange health
    exchange_up = Gauge(
        "trading_exchange_up",
        "Exchange connectivity status (1=up, 0=down)",
        ["exchange"],
    )

    exchange_latency_seconds = Gauge(
        "trading_exchange_latency_seconds",
        "Exchange API latency",
        ["exchange"],
    )

    # Risk metrics
    exposure_eur = Gauge(
        "trading_exposure_eur",
        "Total exposure by symbol",
        ["symbol"],
    )

    daily_volume_eur = Counter(
        "trading_daily_volume_eur",
        "Daily trading volume in EUR",
        ["symbol"],
    )

    # Price metrics
    price_discrepancy_pct = Gauge(
        "trading_price_discrepancy_pct",
        "Price discrepancy between exchanges",
        ["symbol"],
    )

    best_bid = Gauge(
        "trading_best_bid",
        "Best bid price across exchanges",
        ["symbol", "exchange"],
    )

    best_ask = Gauge(
        "trading_best_ask",
        "Best ask price across exchanges",
        ["symbol", "exchange"],
    )

    # System info
    trading_info = Info(
        "trading_platform",
        "Trading platform information",
    )

    @classmethod
    def record_order(
        cls,
        exchange: str,
        symbol: str,
        side: str,
        status: str,
        value_eur: float,
        latency_seconds: float,
        order_type: str = "market",
    ):
        """Record order execution metrics."""
        cls.orders_total.labels(
            exchange=exchange,
            symbol=symbol,
            side=side,
            status=status,
        ).inc()

        cls.orders_value_eur.labels(
            exchange=exchange,
            symbol=symbol,
            side=side,
        ).inc(value_eur)

        cls.order_latency_seconds.labels(
            exchange=exchange,
            order_type=order_type,
        ).observe(latency_seconds)

    @classmethod
    def update_position(
        cls,
        symbol: str,
        exchange: str,
        size: float,
        value_eur: float,
    ):
        """Update position metrics."""
        cls.position_size.labels(
            symbol=symbol,
            exchange=exchange,
        ).set(size)

        cls.position_value_eur.labels(
            symbol=symbol,
            exchange=exchange,
        ).set(value_eur)

    @classmethod
    def update_pnl(
        cls,
        symbol: str,
        exchange: str,
        realized: float | None = None,
        unrealized: float | None = None,
    ):
        """Update P&L metrics."""
        if realized is not None:
            cls.realized_pnl_eur.labels(
                symbol=symbol,
                exchange=exchange,
            ).inc(realized)

        if unrealized is not None:
            cls.unrealized_pnl_eur.labels(
                symbol=symbol,
                exchange=exchange,
            ).set(unrealized)

    @classmethod
    def update_exchange_health(
        cls,
        exchange: str,
        is_up: bool,
        latency_seconds: float = 0.0,
    ):
        """Update exchange health metrics."""
        cls.exchange_up.labels(exchange=exchange).set(1 if is_up else 0)
        cls.exchange_latency_seconds.labels(exchange=exchange).set(latency_seconds)

    @classmethod
    def update_exposure(
        cls,
        symbol: str,
        exposure_eur: float,
    ):
        """Update exposure metrics."""
        cls.exposure_eur.labels(symbol=symbol).set(exposure_eur)

    @classmethod
    def record_volume(
        cls,
        symbol: str,
        volume_eur: float,
    ):
        """Record trading volume."""
        cls.daily_volume_eur.labels(symbol=symbol).inc(volume_eur)

    @classmethod
    def update_price_metrics(
        cls,
        symbol: str,
        exchange: str,
        bid: float,
        ask: float,
        discrepancy_pct: float = 0.0,
    ):
        """Update price metrics."""
        cls.best_bid.labels(symbol=symbol, exchange=exchange).set(bid)
        cls.best_ask.labels(symbol=symbol, exchange=exchange).set(ask)

        if discrepancy_pct > 0:
            cls.price_discrepancy_pct.labels(symbol=symbol).set(discrepancy_pct)

    @classmethod
    def set_platform_info(cls, version: str, environment: str):
        """Set platform information."""
        cls.trading_info.info(
            {
                "version": version,
                "environment": environment,
                "start_time": datetime.utcnow().isoformat(),
            }
        )


class AlertManager:
    """
    Simple alert manager for trading alerts.
    """

    ALERT_THRESHOLDS = {
        "max_order_latency": 10.0,  # seconds
        "max_price_discrepancy": 1.0,  # percent
        "max_exposure": 50000.0,  # EUR
        "exchange_down_timeout": 60.0,  # seconds
    }

    def __init__(self):
        self._alerts: list[dict[str, Any]] = []
        self._alert_history: list[dict[str, Any]] = []

    def check_order_latency(self, exchange: str, latency_seconds: float):
        """Check if order latency exceeds threshold."""
        if latency_seconds > self.ALERT_THRESHOLDS["max_order_latency"]:
            self._trigger_alert(
                severity="warning",
                category="performance",
                message=f"High order latency on {exchange}: {latency_seconds:.2f}s",
                data={"exchange": exchange, "latency": latency_seconds},
            )

    def check_price_discrepancy(self, symbol: str, discrepancy_pct: float):
        """Check if price discrepancy exceeds threshold."""
        if discrepancy_pct > self.ALERT_THRESHOLDS["max_price_discrepancy"]:
            self._trigger_alert(
                severity="warning",
                category="arbitrage",
                message=f"High price discrepancy for {symbol}: {discrepancy_pct:.2f}%",
                data={"symbol": symbol, "discrepancy_pct": discrepancy_pct},
            )

    def check_exposure(self, symbol: str, exposure_eur: float):
        """Check if exposure exceeds threshold."""
        if exposure_eur > self.ALERT_THRESHOLDS["max_exposure"]:
            self._trigger_alert(
                severity="critical",
                category="risk",
                message=f"High exposure for {symbol}: €{exposure_eur:,.2f}",
                data={"symbol": symbol, "exposure_eur": exposure_eur},
            )

    def check_exchange_health(self, exchange: str, is_up: bool):
        """Check exchange health status."""
        if not is_up:
            self._trigger_alert(
                severity="critical",
                category="exchange",
                message=f"Exchange {exchange} is down",
                data={"exchange": exchange},
            )

    def _trigger_alert(
        self,
        severity: str,
        category: str,
        message: str,
        data: dict[str, Any],
    ):
        """Trigger an alert."""
        alert = {
            "id": f"{category}_{datetime.utcnow().timestamp()}",
            "severity": severity,
            "category": category,
            "message": message,
            "data": data,
            "timestamp": datetime.utcnow().isoformat(),
            "acknowledged": False,
        }

        self._alerts.append(alert)
        self._alert_history.append(alert)

        logger.warning(f"[ALERT] {severity.upper()}: {message}")

    def get_active_alerts(self, severity: str | None = None) -> list[dict[str, Any]]:
        """Get active alerts, optionally filtered by severity."""
        if severity:
            return [a for a in self._alerts if a["severity"] == severity and not a["acknowledged"]]
        return [a for a in self._alerts if not a["acknowledged"]]

    def acknowledge_alert(self, alert_id: str) -> bool:
        """Acknowledge an alert."""
        for alert in self._alerts:
            if alert["id"] == alert_id:
                alert["acknowledged"] = True
                return True
        return False

    def clear_acknowledged(self):
        """Clear acknowledged alerts."""
        self._alerts = [a for a in self._alerts if not a["acknowledged"]]


# Global instances
trading_metrics = TradingMetrics
alert_manager = AlertManager()
