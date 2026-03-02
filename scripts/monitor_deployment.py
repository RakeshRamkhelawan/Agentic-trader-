"""
Deployment Monitoring Script.

Week 5: Monitor staging and production deployments.

Usage:
    python scripts/monitor_deployment.py --staging
    python scripts/monitor_deployment.py --production
    python scripts/monitor_deployment.py --check-health
"""

import argparse
import asyncio
import logging
import sys
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class DeploymentMonitor:
    """Monitors deployment health and metrics."""

    # Thresholds for alerting
    THRESHOLDS = {
        "error_rate": 0.05,  # 5% error rate
        "latency_p95": 100,   # 100ms P95 latency
        "risk_latency": 50,   # 50ms risk assessment
        "trade_success": 0.95,  # 95% trade success rate
    }

    def __init__(self, environment: str = "staging"):
        self.environment = environment
        self.metrics: Dict[str, Any] = {}
        self.alerts: List[str] = []
        self.checks_passed = 0
        self.checks_failed = 0

    async def check_health(self) -> bool:
        """
        Check system health.

        Returns:
            True if system is healthy
        """
        logger.info(f"\n{'=' * 60}")
        logger.info(f"HEALTH CHECK - {self.environment.upper()}")
        logger.info(f"{'=' * 60}")

        health_checks = [
            ("Feature Flags", self._check_feature_flags),
            ("Risk Manager", self._check_risk_manager),
            ("Portfolio Manager", self._check_portfolio_manager),
            ("TriadService", self._check_triad_service),
            ("Exchanges", self._check_exchanges),
        ]

        all_healthy = True

        for name, check_func in health_checks:
            try:
                healthy = await check_func()
                if healthy:
                    logger.info(f"✅ {name}: Healthy")
                    self.checks_passed += 1
                else:
                    logger.warning(f"⚠️  {name}: Unhealthy")
                    self.alerts.append(f"{name} is unhealthy")
                    self.checks_failed += 1
                    all_healthy = False
            except Exception as e:
                logger.error(f"❌ {name}: Error - {e}")
                self.alerts.append(f"{name} check failed: {e}")
                self.checks_failed += 1
                all_healthy = False

        return all_healthy

    async def _check_feature_flags(self) -> bool:
        """Check feature flags are properly configured."""
        from backend.core.config.feature_flags import feature_flags

        # In staging, new features should be enabled
        if self.environment == "staging":
            return (
                feature_flags.USE_UNIFIED_SCHEMA and
                feature_flags.USE_PORTFOLIO_MANAGER_AGENT and
                feature_flags.USE_ENHANCED_RISK_VALIDATOR
            )

        # In production, check based on rollout phase
        return True

    async def _check_risk_manager(self) -> bool:
        """Check RiskManager is functioning."""
        from backend.agents.risk_manager_agent import RiskManagerAgent
        from backend.core.schemas.ooda_types import TradeProposal

        agent = RiskManagerAgent(use_enhanced_validator=True)

        # Test risk assessment
        proposal = TradeProposal(
            symbol="BTC/EUR",
            side="buy",
            size=0.01,
            entry_price=45000,
            stop_loss=40000,
            take_profit=50000,
            rationale="Health check",
            strategy_id="health_check",
            confidence=0.8
        )

        start = time.time()
        assessment = await agent.assess_risk(
            proposal=proposal,
            current_regime="bull",
            current_position_size=0.0
        )
        latency = (time.time() - start) * 1000

        # Store metric
        self.metrics["risk_latency_ms"] = latency

        # Check latency threshold
        if latency > self.THRESHOLDS["risk_latency"]:
            self.alerts.append(f"Risk assessment latency {latency:.1f}ms exceeds threshold")

        return assessment is not None and latency < 100

    async def _check_portfolio_manager(self) -> bool:
        """Check PortfolioManager is functioning."""
        from backend.execution.portfolio_manager import PortfolioManager

        pm = PortfolioManager()

        # Check that it can be initialized
        return pm is not None

    async def _check_triad_service(self) -> bool:
        """Check TriadService is functioning."""
        from backend.execution.triad_service import TriadService

        service = TriadService(trading_mode="paper")

        # Check stats collection
        stats = service.get_statistics()

        return stats is not None and "trading_mode" in stats

    async def _check_exchanges(self) -> bool:
        """Check exchange adapters are available."""
        from backend.exchange.exchange_factory_v2 import ExchangeFactoryV2

        factory = ExchangeFactoryV2()
        available = factory.get_available_types()

        return len(available) >= 2  # At least Bitvavo and Revolut

    async def collect_metrics(self) -> Dict[str, Any]:
        """
        Collect deployment metrics.

        Returns:
            Dictionary of metrics
        """
        logger.info(f"\n{'=' * 60}")
        logger.info(f"COLLECTING METRICS - {self.environment.upper()}")
        logger.info(f"{'=' * 60}")

        metrics = {
            "timestamp": datetime.utcnow().isoformat(),
            "environment": self.environment,
        }

        try:
            # Collect RiskManager metrics
            from backend.agents.risk_manager_agent import RiskManagerAgent
            agent = RiskManagerAgent(use_enhanced_validator=True)
            metrics["risk_manager"] = agent.get_stats()

            # Collect TriadService metrics
            from backend.execution.triad_service import TriadService
            service = TriadService(trading_mode="paper")
            metrics["triad_service"] = service.get_statistics()

            logger.info("✅ Metrics collected successfully")

        except Exception as e:
            logger.error(f"❌ Failed to collect metrics: {e}")

        self.metrics.update(metrics)
        return metrics

    def check_thresholds(self) -> List[str]:
        """
        Check if metrics exceed thresholds.

        Returns:
            List of alert messages
        """
        alerts = []

        # Check risk latency
        risk_latency = self.metrics.get("risk_latency_ms", 0)
        if risk_latency > self.THRESHOLDS["risk_latency"]:
            alerts.append(
                f"ALERT: Risk assessment latency {risk_latency:.1f}ms exceeds "
                f"threshold {self.THRESHOLDS['risk_latency']}ms"
            )

        return alerts

    def generate_report(self) -> str:
        """Generate monitoring report."""
        report = f"""
{'=' * 60}
DEPLOYMENT MONITORING REPORT
{'=' * 60}
Environment: {self.environment}
Timestamp: {datetime.utcnow().isoformat()}

Health Checks:
  ✅ Passed: {self.checks_passed}
  ❌ Failed: {self.checks_failed}

Metrics:
"""
        for key, value in self.metrics.items():
            if key not in ["timestamp", "environment"]:
                report += f"  {key}: {value}\n"

        if self.alerts:
            report += f"\n⚠️  Alerts ({len(self.alerts)}):\n"
            for alert in self.alerts:
                report += f"  - {alert}\n"
        else:
            report += "\n✅ No alerts\n"

        report += f"\n{'=' * 60}\n"

        return report

    async def continuous_monitor(self, interval: int = 60):
        """
        Continuously monitor deployment.

        Args:
            interval: Seconds between checks
        """
        logger.info(f"Starting continuous monitoring ({interval}s interval)...")

        while True:
            await self.check_health()
            await self.collect_metrics()

            # Print status
            status = "✅ HEALTHY" if not self.alerts else f"⚠️  {len(self.alerts)} ALERTS"
            logger.info(f"Status: {status}")

            await asyncio.sleep(interval)


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Deployment Monitoring"
    )
    parser.add_argument(
        "--staging",
        action="store_true",
        help="Monitor staging environment"
    )
    parser.add_argument(
        "--production",
        action="store_true",
        help="Monitor production environment"
    )
    parser.add_argument(
        "--check-health",
        action="store_true",
        help="Run health check once"
    )
    parser.add_argument(
        "--collect-metrics",
        action="store_true",
        help="Collect metrics once"
    )
    parser.add_argument(
        "--continuous",
        action="store_true",
        help="Continuous monitoring"
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=60,
        help="Monitoring interval in seconds"
    )

    args = parser.parse_args()

    # Determine environment
    environment = "production" if args.production else "staging"

    monitor = DeploymentMonitor(environment=environment)

    if args.check_health:
        healthy = await monitor.check_health()
        print(monitor.generate_report())
        sys.exit(0 if healthy else 1)

    elif args.collect_metrics:
        await monitor.collect_metrics()
        print(monitor.generate_report())

    elif args.continuous:
        await monitor.continuous_monitor(interval=args.interval)

    else:
        # Default: run health check and collect metrics
        await monitor.check_health()
        await monitor.collect_metrics()
        print(monitor.generate_report())


if __name__ == "__main__":
    asyncio.run(main())
