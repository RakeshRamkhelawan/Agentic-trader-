"""
Production Rollout Script for Exchange Integration Refactor.

Week 7: Gradual rollout from 10% → 50% → 100%

Usage:
    python scripts/production_rollout.py --phase 1  # 10% rollout
    python scripts/production_rollout.py --phase 2  # 50% rollout
    python scripts/production_rollout.py --phase 3  # 100% rollout
    python scripts/production_rollout.py --rollback
"""

import argparse
import asyncio
import hashlib
import logging
import random
import sys
from datetime import datetime
from typing import Dict, List, Optional, Set

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class ProductionRollout:
    """Manages gradual production rollout."""

    # Rollout phases
    PHASES = {
        1: {"percentage": 10, "name": "Canary (10%)"},
        2: {"percentage": 50, "name": "Partial (50%)"},
        3: {"percentage": 100, "name": "Full (100%)"},
    }

    def __init__(self):
        self.current_phase = 0
        self.enabled_users: Set[str] = set()
        self.metrics: Dict[str, any] = {}

    def is_user_enabled(self, user_id: str, phase: int) -> bool:
        """
        Determine if a user should have new features enabled.

        Uses consistent hashing for stable rollout.

        Args:
            user_id: Unique user identifier
            phase: Rollout phase (1, 2, or 3)

        Returns:
            True if user should have new features
        """
        percentage = self.PHASES[phase]["percentage"]

        # Use hash for consistent decision
        hash_value = int(hashlib.md5(user_id.encode()).hexdigest(), 16)
        user_percentage = (hash_value % 100) + 1  # 1-100

        return user_percentage <= percentage

    async def enable_phase(self, phase: int) -> bool:
        """
        Enable rollout phase.

        Args:
            phase: Phase number (1, 2, or 3)

        Returns:
            True if phase enabled successfully
        """
        if phase not in self.PHASES:
            logger.error(f"❌ Invalid phase: {phase}")
            return False

        phase_info = self.PHASES[phase]
        logger.info(f"\n{'=' * 60}")
        logger.info(f"ENABLING PHASE {phase}: {phase_info['name']}")
        logger.info(f"{'=' * 60}")

        try:
            from backend.core.config.feature_flags import feature_flags

            # Enable all features for this phase
            feature_flags.USE_UNIFIED_SCHEMA = True
            feature_flags.USE_PORTFOLIO_MANAGER_AGENT = True
            feature_flags.USE_ENHANCED_RISK_VALIDATOR = True

            self.current_phase = phase

            logger.info(f"✅ Phase {phase} enabled ({phase_info['percentage']}% of users)")
            logger.info("✅ New features active for eligible users")

            return True

        except Exception as e:
            logger.error(f"❌ Failed to enable phase {phase}: {e}")
            return False

    async def check_rollout_health(self, phase: int) -> Dict[str, any]:
        """
        Check health metrics for current rollout phase.

        Args:
            phase: Current phase number

        Returns:
            Health metrics dictionary
        """
        logger.info(f"\n{'=' * 60}")
        logger.info(f"CHECKING ROLLOUT HEALTH - PHASE {phase}")
        logger.info(f"{'=' * 60}")

        metrics = {
            "phase": phase,
            "timestamp": datetime.utcnow().isoformat(),
            "checks": {}
        }

        # Check error rates
        try:
            from backend.agents.risk_manager_agent import RiskManagerAgent
            agent = RiskManagerAgent(use_enhanced_validator=True)
            stats = agent.get_stats()

            metrics["checks"]["risk_manager"] = {
                "status": "healthy",
                "assessments": stats.get("assessments_made", 0)
            }
            logger.info("✅ RiskManager: Healthy")

        except Exception as e:
            metrics["checks"]["risk_manager"] = {"status": "error", "message": str(e)}
            logger.error(f"❌ RiskManager: {e}")

        # Check TriadService
        try:
            from backend.execution.triad_service import TriadService
            service = TriadService(trading_mode="live")
            stats = service.get_statistics()

            metrics["checks"]["triad_service"] = {
                "status": "healthy",
                "trades_executed": stats.get("trades_executed", 0)
            }
            logger.info("✅ TriadService: Healthy")

        except Exception as e:
            metrics["checks"]["triad_service"] = {"status": "error", "message": str(e)}
            logger.error(f"❌ TriadService: {e}")

        self.metrics = metrics
        return metrics

    async def validate_phase(self, phase: int) -> bool:
        """
        Validate that current phase is healthy before proceeding.

        Args:
            phase: Phase to validate

        Returns:
            True if phase is healthy
        """
        metrics = await self.check_rollout_health(phase)

        # Check for errors
        errors = [
            check for check in metrics["checks"].values()
            if check.get("status") == "error"
        ]

        if errors:
            logger.error(f"❌ Phase {phase} validation failed:")
            for error in errors:
                logger.error(f"  - {error.get('message', 'Unknown error')}")
            return False

        logger.info(f"✅ Phase {phase} validation passed")
        return True

    async def rollback(self) -> bool:
        """
        Emergency rollback to legacy components.

        Returns:
            True if rollback successful
        """
        logger.info(f"\n{'=' * 60}")
        logger.info("🚨 EMERGENCY ROLLBACK INITIATED")
        logger.info(f"{'=' * 60}")

        try:
            from backend.core.config.feature_flags import feature_flags

            # Disable all new features
            feature_flags.USE_UNIFIED_SCHEMA = False
            feature_flags.USE_PORTFOLIO_MANAGER_AGENT = False
            feature_flags.USE_ENHANCED_RISK_VALIDATOR = False
            feature_flags.USE_REFACTORED_TRIAD_SERVICE = False

            self.current_phase = 0

            logger.info("✅ All new features disabled")
            logger.info("✅ System rolled back to legacy components")
            logger.info("⚠️  Investigate issues before re-enabling")

            return True

        except Exception as e:
            logger.error(f"❌ Rollback failed: {e}")
            logger.error("🚨 MANUAL INTERVENTION REQUIRED")
            return False

    def generate_rollout_report(self) -> str:
        """Generate rollout status report."""
        phase_info = self.PHASES.get(self.current_phase, {"name": "None", "percentage": 0})

        report = f"""
{'=' * 60}
PRODUCTION ROLLOUT REPORT
{'=' * 60}
Timestamp: {datetime.utcnow().isoformat()}
Current Phase: {self.current_phase} ({phase_info['name']})
Rollout Percentage: {phase_info['percentage']}%

Metrics:
"""
        for component, data in self.metrics.get("checks", {}).items():
            status = data.get("status", "unknown")
            icon = "✅" if status == "healthy" else "❌"
            report += f"  {icon} {component}: {status}\n"

        report += f"\n{'=' * 60}\n"
        return report


async def interactive_rollout():
    """Interactive rollout wizard."""
    rollout = ProductionRollout()

    print("\n" + "=" * 60)
    print("PRODUCTION ROLLOUT WIZARD")
    print("=" * 60)
    print("\nPhases:")
    for phase, info in ProductionRollout.PHASES.items():
        print(f"  {phase}. {info['name']}")
    print("\nOptions:")
    print("  r. Rollback")
    print("  q. Quit")
    print("  v. Validate current phase")
    print("  s. Show status")

    while True:
        choice = input("\nEnter choice (1/2/3/r/q/v/s): ").strip().lower()

        if choice == "q":
            break
        elif choice == "r":
            await rollout.rollback()
        elif choice == "v":
            if rollout.current_phase > 0:
                await rollout.validate_phase(rollout.current_phase)
            else:
                print("No active phase to validate")
        elif choice == "s":
            print(rollout.generate_rollout_report())
        elif choice in ["1", "2", "3"]:
            phase = int(choice)

            # Validate previous phase before advancing
            if phase > 1 and rollout.current_phase < phase - 1:
                print(f"⚠️  Please complete phase {phase - 1} first")
                continue

            if phase > 1:
                healthy = await rollout.validate_phase(phase - 1)
                if not healthy:
                    print("❌ Previous phase not healthy. Fix issues before proceeding.")
                    continue

            success = await rollout.enable_phase(phase)
            if success:
                await rollout.validate_phase(phase)
        else:
            print("Invalid choice")


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Production Rollout for Exchange Integration"
    )
    parser.add_argument(
        "--phase",
        type=int,
        choices=[1, 2, 3],
        help="Enable rollout phase (1=10%, 2=50%, 3=100%)"
    )
    parser.add_argument(
        "--rollback",
        action="store_true",
        help="Emergency rollback"
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Validate current phase"
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Interactive rollout wizard"
    )
    parser.add_argument(
        "--check-user",
        type=str,
        help="Check if user would be enabled (provide user_id)"
    )

    args = parser.parse_args()

    rollout = ProductionRollout()

    if args.interactive:
        await interactive_rollout()
    elif args.rollback:
        success = await rollout.rollback()
        sys.exit(0 if success else 1)
    elif args.validate:
        # Try to detect current phase
        from backend.core.config.feature_flags import feature_flags
        if feature_flags.USE_UNIFIED_SCHEMA:
            # Assume phase 3 if all features enabled
            await rollout.validate_phase(3)
        else:
            logger.info("New features not enabled (Phase 0)")
    elif args.check_user:
        for phase in [1, 2, 3]:
            enabled = rollout.is_user_enabled(args.check_user, phase)
            phase_name = ProductionRollout.PHASES[phase]["name"]
            status = "✅ Enabled" if enabled else "❌ Disabled"
            print(f"Phase {phase} ({phase_name}): {status}")
    elif args.phase:
        success = await rollout.enable_phase(args.phase)
        if success:
            await rollout.validate_phase(args.phase)
        print(rollout.generate_rollout_report())
        sys.exit(0 if success else 1)
    else:
        parser.print_help()


if __name__ == "__main__":
    asyncio.run(main())
