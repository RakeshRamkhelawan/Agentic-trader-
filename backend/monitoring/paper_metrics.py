"""
Prometheus Metrics voor Paper Trading & Vedic Stack.

Deze metrics zijn essentieel voor enterprise observability.
"""

from prometheus_client import Counter, Gauge, Histogram, Info

# ═══════════════════════════════════════════════════════════════════════════
# Paper Trading Metrics
# ═══════════════════════════════════════════════════════════════════════════

PAPER_TRADES_TOTAL = Counter(
    "paper_trades_total",
    "Totaal aantal gesimuleerde trades",
    ["symbol", "side", "agent", "element"],
)

PAPER_TRADE_VALUE = Histogram(
    "paper_trade_value_eur",
    "Waarde van trades in EUR",
    buckets=[10, 50, 100, 500, 1000, 5000, 10000],
)

PAPER_PORTFOLIO_VALUE = Gauge(
    "paper_portfolio_value_eur", "Actuele portfolio waarde in EUR"
)

PAPER_PNL = Gauge("paper_pnl_eur", "Gerealiseerde P&L in EUR")

PAPER_PNL_PERCENTAGE = Gauge(
    "paper_pnl_percentage", "P&L als percentage van startkapitaal"
)

PAPER_CASH_BALANCE = Gauge("paper_cash_balance_eur", "Beschikbaar cash in EUR")

PAPER_POSITIONS_COUNT = Gauge("paper_positions_count", "Aantal open posities")

# ═══════════════════════════════════════════════════════════════════════════
# Vedic Stack Metrics
# ═══════════════════════════════════════════════════════════════════════════

VEDIC_HARMONY_SCORE = Gauge(
    "vedic_harmony_score",
    "Actuele harmony score (0-1)",
)

VEDIC_HARMONY_STATUS = Gauge(
    "vedic_harmony_status", "Harmony status: 0=low, 1=medium, 2=high"
)

VEDIC_PRANA_LEVELS = Gauge(
    "vedic_prana_level", "Prana level per elementaire agent", ["element"]
)

VEDIC_PRANA_STATUS = Gauge(
    "vedic_prana_status", "Prana status: 0=depleted, 1=nominal", ["element"]
)

RAHU_KALA_ACTIVE = Gauge("rahu_kala_active", "1 als Rahu Kala actief is, 0 anders")

MARKET_REGIME = Gauge(
    "vedic_market_regime",
    "Market regime: 0=neutral, 1=expansion, 2=contraction, 3=recovery",
)

CONSCIOUSNESS_LEVEL = Gauge("vedic_consciousness_level", "Consciousness level (0-1)")

TRADING_GATE_OPEN = Gauge(
    "vedic_trading_gate_open", "1 als trading gate open is, 0 als geblokkeerd"
)

# ═══════════════════════════════════════════════════════════════════════════
# Safety & Audit Metrics
# ═══════════════════════════════════════════════════════════════════════════

PAPER_GUARD_INTERCEPTS = Counter(
    "paper_guard_intercepts_total",
    "Aantal keren dat paper_guard een echte exchange call blokkeerde",
    ["function"],
)

SAFETY_VIOLATIONS = Counter(
    "paper_safety_violations_total",
    "Aantal veiligheidsschendingen geprobeerd",
    ["violation_type"],
)

# ═══════════════════════════════════════════════════════════════════════════
# WebSocket Metrics
# ═══════════════════════════════════════════════════════════════════════════

WS_CONNECTED_CLIENTS = Gauge(
    "ws_paper_trading_connected_clients",
    "Aantal actieve WebSocket verbindingen op /ws/paper-trading",
)

WS_MESSAGES_SENT = Counter(
    "ws_messages_sent_total",
    "Totaal aantal WebSocket berichten verstuurd",
    ["channel", "message_type"],
)

WS_CONNECTION_ERRORS = Counter(
    "ws_connection_errors_total", "Aantal WebSocket connectie errors"
)

# ═══════════════════════════════════════════════════════════════════════════
# Performance Metrics
# ═══════════════════════════════════════════════════════════════════════════

AGENT_CYCLE_DURATION = Histogram(
    "agent_cycle_duration_seconds",
    "Duur van een volledige Vedic trading cycle",
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0],
)

AGENT_RESPONSE_TIME = Histogram(
    "agent_response_time_seconds",
    "Response tijd per agent",
    ["agent", "element"],
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1],
)

LLM_CALL_DURATION = Histogram(
    "llm_call_duration_seconds",
    "Duur van LLM calls",
    ["agent"],
    buckets=[0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
)

# ═══════════════════════════════════════════════════════════════════════════
# System Info
# ═══════════════════════════════════════════════════════════════════════════

SYSTEM_INFO = Info("paper_trading_system", "System information")


def set_system_info(version: str, trading_mode: str, environment: str):
    """Set system info metrics."""
    SYSTEM_INFO.info(
        {
            "version": version,
            "trading_mode": trading_mode,
            "environment": environment,
        }
    )


def update_harmony_metrics(harmony_score: float):
    """Update harmony score en status metrics."""
    VEDIC_HARMONY_SCORE.set(harmony_score)

    # Status: 0=low, 1=medium, 2=high
    if harmony_score < 0.3:
        VEDIC_HARMONY_STATUS.set(0)
    elif harmony_score < 0.7:
        VEDIC_HARMONY_STATUS.set(1)
    else:
        VEDIC_HARMONY_STATUS.set(2)


def update_prana_metrics(element: str, prana: float):
    """Update prana metrics voor een element."""
    VEDIC_PRANA_LEVELS.labels(element=element).set(prana)

    # Status: 0=depleted (<10), 1=nominal
    VEDIC_PRANA_STATUS.labels(element=element).set(0 if prana < 10 else 1)


def record_trade(symbol: str, side: str, agent: str, element: str, value: float):
    """Record een trade metric."""
    PAPER_TRADES_TOTAL.labels(
        symbol=symbol, side=side, agent=agent, element=element
    ).inc()

    PAPER_TRADE_VALUE.observe(value)
