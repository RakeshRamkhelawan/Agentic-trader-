"""
WebSocket Metrics for Prometheus

Implements ADR-003: WebSocket Reliability & Backpressure
Provides observability into WS layer performance.

Metrics:
- Connection counts and rates
- Message throughput and drops
- Queue depths
- Latency distributions
- Disconnect reasons
"""

from prometheus_client import Counter, Gauge, Histogram


class WSMetrics:
    """Prometheus metrics for WebSocket monitoring."""

    def __init__(self):
        # Connection metrics
        self.connections = Gauge(
            "ws_connections_current", "Number of active WebSocket connections"
        )

        self.connect_rate = Counter(
            "ws_connect_total",
            "Total WebSocket connection attempts",
            ["status"],  # success, failure, rejected
        )

        self.disconnect_reason = Counter(
            "ws_disconnect_total",
            "WebSocket disconnections by reason",
            [
                "reason"
            ],  # client_disconnect, heartbeat_timeout, send_error, auth_failure
        )

        # Message metrics
        self.messages_sent = Counter(
            "ws_messages_sent",
            "Messages sent to clients",
            ["stream", "priority"],  # priority: high, low
        )

        self.messages_dropped = Counter(
            "ws_messages_dropped", "Messages dropped due to backpressure", ["stream"]
        )

        self.messages_received = Counter(
            "ws_messages_received",
            "Messages received from clients",
            ["type"],  # subscribe, unsubscribe, ping, pong, etc.
        )

        # Queue metrics
        self.queue_depth = Gauge(
            "ws_queue_depth",
            "Current queue depth per connection",
            ["connection_id", "tenant_id"],
        )

        self.queue_high_watermark = Gauge(
            "ws_queue_high_watermark", "Maximum queue depth observed"
        )

        # Latency metrics
        self.latency = Histogram(
            "ws_latency_seconds",
            "Message publish to receive latency",
            buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0],
        )

        self.heartbeat_latency = Histogram(
            "ws_heartbeat_latency_seconds",
            "Round-trip heartbeat latency",
            buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1],
        )

        # Channel metrics
        self.channel_subscribers = Gauge(
            "ws_channel_subscribers", "Number of subscribers per channel", ["channel"]
        )

        # Error metrics
        self.errors = Counter(
            "ws_errors_total",
            "WebSocket errors",
            ["type"],  # serialization, send, receive, auth
        )

        self.resync_signals = Counter(
            "ws_resync_signals_total", "Resync signals sent to clients", ["reason"]
        )


# Global metrics instance
ws_metrics = WSMetrics()
