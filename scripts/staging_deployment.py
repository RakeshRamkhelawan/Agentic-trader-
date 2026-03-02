"""
Staging Deployment Script for Exchange Integration Refactor.

Week 5: Deploy new components to staging environment.

Usage:
    python scripts/staging_deployment.py --enable-features
    python scripts/staging_deployment.py --verify
    python scripts/staging_deployment.py --rollback
"""

import argparse
import asyncio
import logging
import sys
from datetime import datetime
from typing import Dict, List, Optional

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class StagingDeployment:
    """Manages staging deployment for exchange integration."""

    def __init__(self):
        self.deployment_id = f"staging-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}"
        self.checks_passed = 0
        self.checks_failed = 0

    async def enable_feature_flags(self) -> bool:
        """
        Enable feature flags in staging environment.

        Returns:
            True if all flags enabled successfully
        """
        logger.info("=" * 60)
        logger.info("ENABLING FEATURE FLAGS IN STAGING")
        logger.info("=" * 60)

        try:
            from backend.core.config.feature_flags import feature_flags

            # Enable Week 1 features
            feature_flags.USE_UNIFIED_SCHEMA = True
            logger.info("✅ USE_UNIFIED_SCHEMA enabled")

            feature_flags.USE_PORTFOLIO_MANAGER_AGENT = True
            logger.info("✅ USE_PORTFOLIO_MANAGER_AGENT enabled")

            # Enable Week 2 features
            feature_flags.USE_ENHANCED_RISK_VALIDATOR = True
            logger.info("✅ USE_ENHANCED_RISK_VALIDATOR enabled")

            # Keep Week 3-4 disabled for now
            # feature_flags.USE_REFACTORED_TRIAD_SERVICE = True
            logger.info("⏳ USE_REFACTORED_TRIAD_SERVICE kept disabled")

            logger.info("\nFeature flags configuration:")
            logger.info(feature_flags.model_dump_json(indent=2))

            self.checks_passed += 1
            return True

        except Exception as e:
            logger.error(f"❌ Failed to enable feature flags: {e}")
            self.checks_failed += 1
            return False

    async def verify_exchanges(self) -> bool:
        """
        Verify exchange connectivity in staging.

        Returns:
            True if all exchanges are accessible
        """
        logger.info("\n" + "=" * 60)
        logger.info("VERIFYING EXCHANGE CONNECTIVITY")
        logger.info("=" * 60)

        try:
            from backend.exchange.exchange_factory_v2 import ExchangeFactoryV2

            factory = ExchangeFactoryV2()
            available = factory.get_available_types()

            logger.info(f"Available exchange types: {available}")

            # Try to create adapters (without connecting)
            for exchange_type in available:
                try:
                    adapter = await factory.create_exchange(
                        exchange_type,
                        auto_connect=False
                    )
                    if adapter:
                        logger.info(f"✅ {exchange_type} adapter created successfully")
                    else:
                        logger.warning(f"⚠️  {exchange_type} adapter returned None")
                except Exception as e:
                    logger.error(f"❌ {exchange_type} adapter failed: {e}")
                    self.checks_failed += 1
                    return False

            self.checks_passed += 1
            return True

        except Exception as e:
            logger.error(f"❌ Exchange verification failed: {e}")
            self.checks_failed += 1
            return False

    async def run_integration_tests(self) -> bool:
        """
        Run integration tests in staging.

        Returns:
            True if all tests pass
        """
        logger.info("\n" + "=" * 60)
        logger.info("RUNNING INTEGRATION TESTS")
        logger.info("=" * 60)

        import subprocess

        test_suites = [
            ("Unified Schema", "tests/schemas/test_unified_execution.py"),
            ("Portfolio Manager", "tests/execution/test_portfolio_manager.py"),
            ("Risk Manager", "tests/agents/test_risk_manager_enhanced.py"),
            ("TriadService", "tests/execution/test_triad_service.py"),
            ("OODA Flow", "tests/integration/test_ooda_execution_flow.py"),
            ("Multi-Exchange", "tests/integration/test_multi_exchange_execution.py"),
        ]

        all_passed = True

        for name, test_path in test_suites:
            logger.info(f"\nRunning {name} tests...")
            try:
                result = subprocess.run(
                    ["python", "-m", "pytest", test_path, "-v", "--tb=short"],
                    capture_output=True,
                    text=True,
                    timeout=120
                )

                if result.returncode == 0:
                    logger.info(f"✅ {name} tests passed")
                    self.checks_passed += 1
                else:
                    logger.error(f"❌ {name} tests failed")
                    logger.error(result.stdout[-500:] if len(result.stdout) > 500 else result.stdout)
                    self.checks_failed += 1
                    all_passed = False

            except subprocess.TimeoutExpired:
                logger.error(f"❌ {name} tests timed out")
                self.checks_failed += 1
                all_passed = False
            except Exception as e:
                logger.error(f"❌ {name} tests error: {e}")
                self.checks_failed += 1
                all_passed = False

        return all_passed

    async def verify_metrics(self) -> bool:
        """
        Verify metrics and monitoring are working.

        Returns:
            True if metrics are being collected
        """
        logger.info("\n" + "=" * 60)
        logger.info("VERIFYING METRICS COLLECTION")
        logger.info("=" * 60)

        try:
            # Check that key metrics can be collected
            from backend.agents.risk_manager_agent import RiskManagerAgent

            agent = RiskManagerAgent(use_enhanced_validator=True)
            stats = agent.get_stats()

            logger.info(f"RiskManager stats: {stats}")
            logger.info("✅ Metrics collection working")

            self.checks_passed += 1
            return True

        except Exception as e:
            logger.error(f"❌ Metrics verification failed: {e}")
            self.checks_failed += 1
            return False

    async def rollback(self) -> bool:
        """
        Rollback to legacy components.

        Returns:
            True if rollback successful
        """
        logger.info("\n" + "=" * 60)
        logger.info("ROLLING BACK TO LEGACY COMPONENTS")
        logger.info("=" * 60)

        try:
            from backend.core.config.feature_flags import feature_flags

            # Disable all new features
            feature_flags.USE_UNIFIED_SCHEMA = False
            feature_flags.USE_PORTFOLIO_MANAGER_AGENT = False
            feature_flags.USE_ENHANCED_RISK_VALIDATOR = False
            feature_flags.USE_REFACTORED_TRIAD_SERVICE = False

            logger.info("✅ All feature flags disabled")
            logger.info("✅ System rolled back to legacy components")

            return True

        except Exception as e:
            logger.error(f"❌ Rollback failed: {e}")
            return False

    def generate_report(self) -> str:
        """Generate deployment report."""
        report = f"""
{'=' * 60}
STAGING DEPLOYMENT REPORT
{'=' * 60}
Deployment ID: {self.deployment_id}
Timestamp: {datetime.utcnow().isoformat()}

Results:
  ✅ Passed: {self.checks_passed}
  ❌ Failed: {self.checks_failed}
  📊 Total:  {self.checks_passed + self.checks_failed}

Status: {'✅ SUCCESS' if self.checks_failed == 0 else '❌ FAILED'}

{'=' * 60}
"""
        return report


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Staging Deployment for Exchange Integration"
    )
    parser.add_argument(
        "--enable-features",
        action="store_true",
        help="Enable new feature flags"
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Verify deployment"
    )
    parser.add_argument(
        "--run-tests",
        action="store_true",
        help="Run integration tests"
    )
    parser.add_argument(
        "--rollback",
        action="store_true",
        help="Rollback to legacy"
    )
    parser.add_argument(
        "--full",
        action="store_true",
        help="Full deployment (enable + verify + tests)"
    )

    args = parser.parse_args()

    deployment = StagingDeployment()

    if args.full:
        args.enable_features = True
        args.verify = True
        args.run_tests = True

    success = True

    if args.enable_features:
        success = await deployment.enable_feature_flags() and success

    if args.verify:
        success = await deployment.verify_exchanges() and success
        success = await deployment.verify_metrics() and success

    if args.run_tests:
        success = await deployment.run_integration_tests() and success

    if args.rollback:
        success = await deployment.rollback() and success

    # Print report
    report = deployment.generate_report()
    print(report)

    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
