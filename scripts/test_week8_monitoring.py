#!/usr/bin/env python
"""
Week 8 Test Suite - Monitoring & Alerting

Tests:
1. Trading metrics initialization
2. Alert manager functionality
3. MCP monitoring tools
4. Grafana dashboard configs
5. Prometheus alert rules
"""

import asyncio
import json
import logging
import os
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)

sys.path.insert(0, ".")


async def test_trading_metrics():
    """Test trading metrics initialization."""
    print("\n" + "=" * 60)
    print("Test 1: Trading Metrics")
    print("=" * 60)

    from backend.observability.trading_metrics import TradingMetrics

    # Test metrics are defined
    metrics = [
        TradingMetrics.orders_total,
        TradingMetrics.orders_value_eur,
        TradingMetrics.order_latency_seconds,
        TradingMetrics.position_size,
        TradingMetrics.position_value_eur,
        TradingMetrics.realized_pnl_eur,
        TradingMetrics.unrealized_pnl_eur,
        TradingMetrics.exchange_up,
        TradingMetrics.exchange_latency_seconds,
        TradingMetrics.exposure_eur,
        TradingMetrics.daily_volume_eur,
        TradingMetrics.price_discrepancy_pct,
        TradingMetrics.best_bid,
        TradingMetrics.best_ask,
    ]

    print(f"Defined metrics: {len(metrics)}")
    for m in metrics:
        print(f"  - {m._name}: {m._documentation}")

    return len(metrics) > 0


async def test_alert_manager():
    """Test alert manager functionality."""
    print("\n" + "=" * 60)
    print("Test 2: Alert Manager")
    print("=" * 60)

    from backend.observability.trading_metrics import alert_manager

    # Trigger some test alerts
    alert_manager.check_order_latency("bitvavo", 15.0)
    alert_manager.check_price_discrepancy("BTC", 1.5)
    alert_manager.check_exposure("ETH", 60000.0)
    alert_manager.check_exchange_health("revolutx", False)

    # Get active alerts
    alerts = alert_manager.get_active_alerts()
    print(f"Active alerts: {len(alerts)}")

    for alert in alerts:
        print(f"  [{alert['severity'].upper()}] {alert['category']}: {alert['message']}")

    # Test acknowledgment
    if alerts:
        alert_id = alerts[0]["id"]
        success = alert_manager.acknowledge_alert(alert_id)
        print(f"\nAcknowledged alert {alert_id}: {success}")

    # Get alerts by severity
    critical = alert_manager.get_active_alerts("critical")
    print(f"\nCritical alerts: {len(critical)}")

    return len(alerts) > 0


async def test_mcp_monitoring_tools():
    """Test MCP monitoring tools."""
    print("\n" + "=" * 60)
    print("Test 3: MCP Monitoring Tools")
    print("=" * 60)

    import asyncio

    from backend.mcp_broker.server import mcp

    tools = await mcp.list_tools()

    monitoring_tools = [t for t in tools if "monitoring" in t.name]

    print(f"Total tools: {len(tools)}")
    print(f"Monitoring tools: {len(monitoring_tools)}")

    expected = [
        "monitoring__get_metrics",
        "monitoring__get_alerts",
        "monitoring__acknowledge_alert",
        "monitoring__get_health",
        "monitoring__get_performance_summary",
        "monitoring__export_data",
    ]

    print("\nRegistered tools:")
    found = [t.name for t in monitoring_tools]
    for tool in expected:
        status = "OK" if tool in found else "MISSING"
        print(f"  - {tool}: {status}")

    return len(monitoring_tools) == len(expected)


async def test_grafana_dashboards():
    """Test Grafana dashboard configurations."""
    print("\n" + "=" * 60)
    print("Test 4: Grafana Dashboards")
    print("=" * 60)

    dashboards_dir = "infrastructure/grafana/dashboards"

    expected_dashboards = [
        "trading-overview.json",
        "positions-pnl.json",
        "arbitrage-prices.json",
    ]

    found = []
    for dashboard in expected_dashboards:
        path = os.path.join(dashboards_dir, dashboard)
        if os.path.exists(path):
            with open(path, "r") as f:
                content = json.load(f)
                title = content.get("dashboard", {}).get("title", "Unknown")
                panels = len(content.get("dashboard", {}).get("panels", []))
                print(f"  [OK] {dashboard}: {title} ({panels} panels)")
                found.append(dashboard)
        else:
            print(f"  [MISSING] {dashboard}")

    return len(found) == len(expected_dashboards)


async def test_prometheus_rules():
    """Test Prometheus alert rules."""
    print("\n" + "=" * 60)
    print("Test 5: Prometheus Alert Rules")
    print("=" * 60)

    rules_file = "infrastructure/prometheus/rules/trading_alerts.yml"

    if not os.path.exists(rules_file):
        print(f"  [MISSING] {rules_file}")
        return False

    import yaml

    with open(rules_file, "r") as f:
        rules = yaml.safe_load(f)

    groups = rules.get("groups", [])
    print(f"Rule groups: {len(groups)}")

    total_rules = 0
    for group in groups:
        group_name = group.get("name", "unknown")
        group_rules = group.get("rules", [])
        print(f"\n  Group: {group_name} ({len(group_rules)} rules)")
        total_rules += len(group_rules)

        for rule in group_rules:
            alert_name = rule.get("alert", "unknown")
            severity = rule.get("labels", {}).get("severity", "unknown")
            print(f"    - {alert_name} [{severity}]")

    return total_rules > 0


async def test_metrics_recording():
    """Test recording metrics."""
    print("\n" + "=" * 60)
    print("Test 6: Metrics Recording")
    print("=" * 60)

    from backend.observability.trading_metrics import TradingMetrics

    # Record some test metrics
    TradingMetrics.record_order(
        exchange="bitvavo",
        symbol="BTC",
        side="buy",
        status="filled",
        value_eur=5000.0,
        latency_seconds=0.5,
    )

    TradingMetrics.update_position(
        symbol="BTC",
        exchange="bitvavo",
        size=0.1,
        value_eur=5750.0,
    )

    TradingMetrics.update_pnl(
        symbol="BTC",
        exchange="bitvavo",
        unrealized=250.0,
    )

    TradingMetrics.update_exchange_health(
        exchange="bitvavo",
        is_up=True,
        latency_seconds=0.1,
    )

    TradingMetrics.update_price_metrics(
        symbol="BTC",
        exchange="bitvavo",
        bid=57500.0,
        ask=57550.0,
        discrepancy_pct=0.05,
    )

    print("Recorded test metrics:")
    print("  - Order: bitvavo BTC buy €5,000")
    print("  - Position: 0.1 BTC @ bitvavo")
    print("  - PnL: €250 unrealized")
    print("  - Exchange health: bitvavo UP (100ms)")
    print("  - Price: BTC bid €57,500 / ask €57,550")

    return True


async def main():
    """Run all Week 8 tests."""
    print("=" * 60)
    print("Week 8: Monitoring & Alerting Tests")
    print("=" * 60)

    results = {}

    tests = [
        ("trading_metrics", test_trading_metrics),
        ("alert_manager", test_alert_manager),
        ("mcp_monitoring_tools", test_mcp_monitoring_tools),
        ("grafana_dashboards", test_grafana_dashboards),
        ("prometheus_rules", test_prometheus_rules),
        ("metrics_recording", test_metrics_recording),
    ]

    for test_name, test_func in tests:
        try:
            results[test_name] = await test_func()
        except Exception as e:
            logger.error(f"{test_name} test failed: {e}")
            results[test_name] = False

    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)

    for test_name, passed in results.items():
        status = "PASS" if passed else "FAIL"
        emoji = " " if passed else " "
        print(f"{emoji} {test_name}: {status}")

    all_passed = all(results.values())
    print("\n" + "=" * 60)
    if all_passed:
        print("All Week 8 tests passed! Monitoring system ready.")
        print("\nDashboards available:")
        print("  - Trading Overview")
        print("  - Positions & P&L")
        print("  - Arbitrage & Prices")
        print("\nAlert rules configured:")
        print("  - Exchange health")
        print("  - Order latency")
        print("  - Price discrepancies")
        print("  - Risk limits")
    else:
        print("Some tests failed. Check logs above.")
    print("=" * 60)

    return 0 if all_passed else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
